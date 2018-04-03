import logging

import requests
import datetime
import os.path
import re

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from parser_log.models import ApacheLog


WSP, QUOTED_STRING, DATE, RAW1, RAW, NO_DATA, IP = range(7) # ENUM


RULES = [
    ('\s+', WSP),
    ('-|"-"', NO_DATA),
    ('[0-9]{1,3}(\.[0-9]{1,3}){3}', IP),
    ('"([^"]+)"', QUOTED_STRING),
    ('\[([^\]]+)\]', DATE),
    ('([0-9]+)\s([0-9]+)|-', RAW1),
    ('([^\s]+)', RAW),
]


class Command(BaseCommand):
    help = """Accepts a link or a local path to a log file of a certain format, 
    downloads it, parses it and writes it to DB."""

    # размер обрабатываемого файла
    size_file = 0

    path_file = ''
    # список для для массового сохранения объектов ApacheLog
    list_log = []
    # количество обработанных строк
    count_str = 0
    # размер обработанных строк в байтах
    size_record = 0
    percent = 0

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        # предварительно скомпилируем регулярные выражения для ускорения работы
        self.prepared = [(re.compile(regexp), token_type) for regexp, token_type in RULES]

    def add_arguments(self, parser):
        parser.add_argument('path_file', nargs='*', type=str,
                            help='a link or a local path to a log file')

        parser.add_argument('--file',
                            action='store_true',
                            dest='file',
                            default=False,
                            help='parses it and writes it to DB from a local file')

    def handle(self, *args, **options):
        self.path_file = options.get('path_file')[0]
        if options['file']:
            self.parse_log()
        else:
            self.download()

    def download(self):
        r = requests.get(self.path_file, stream=True)
        # Размер загружаемого файла из headers
        self.size_file = int(r.headers.get('Content-Length'))

        self.stdout.write('Start download, parsing and writing to DB.')
        for line in r.iter_lines(chunk_size=512, decode_unicode=True):
            self.count_str += 1
            self.size_record += len(line) #.encode('utf-8'))
            log = self.parse_line(line)
            if log.date or log.ip:
                self.list_log.append(log)
                per = self.get_percent(self.size_record)
                if per > self.percent:
                    self.percent = per
                    ApacheLog.objects.bulk_create(self.list_log)
                    self.list_log.clear()
                    self.stdout.write('Complete - '
                                      + str(self.percent)
                                      + '%. Parsed ' + str(self.count_str) + ' rows.'
                                      , ending='\r')

    def get_percent(self, size_record):
        try:
            return int(size_record/self.size_file*100)
        except ZeroDivisionError:
            pass

    def lex(self, line):
        """
        try regular expressions in turn

        :param line: string that is parsed
        :return: generator
        """

        ll = len(line)
        i = 0
        while i < ll:
            for pattern, token_type in self.prepared:
                match = pattern.match(line, i)
                if match is None:
                    continue
                i = match.end()
                yield (match, token_type)
                break
            # for good, need to throw error Syntax Error(line, i)
            # if none of the templates do not match

    def parse_log(self):

        self.size_file = os.path.getsize(self.path_file)
        with open(self.path_file, 'r') as file:
            self.stdout.write('Start parsing and writing to DB.')

            for s in file:
                self.count_str += 1
                self.size_record += len(s.encode('utf-8'))
                log = self.parse_line(s)
                if log.date or log.ip:
                    self.list_log.append(log)
                    per = self.get_percent(self.size_record)
                    if per > self.percent:
                        self.percent = per
                        self.stdout.write('Complete - '
                                            + str(self.percent)
                                            + '%. Parsed ' + str(self.count_str) + ' rows.'
                                            , ending='\r')
                        ApacheLog.objects.bulk_create(self.list_log)
                        self.list_log.clear()

    def parse_line(self, line):
        # принимает строку, возвращает объект модели Лог
        # или None если битая строка

        try:
            tokens = self.lex(line)
        except Exception:
            logging.exception("Error in line '%s'", line)
            return None

        log = ApacheLog()
        for re_match, token_type in tokens:
            if token_type == WSP:
                # пробелы игнорируем
                continue
            elif token_type == NO_DATA:
                # NO_DATA игнорируем
                continue
            elif token_type == RAW1:
                log.id_resp = re_match.group(1)
                log.resp_size = re_match.group(2)
                continue
            elif token_type == RAW:
                continue
            elif token_type == QUOTED_STRING:
                # проверяем соответствие строки нашему шаблону -
                # метод - зарпрос - версия протокола
                un_escape = re.match(r'([A-Z]+)\s(\/|[htps://].*)\s([A-Z]+\/(\d)\.(\d))',
                                    re_match.group(1))
                if un_escape:
                    log.method = un_escape.group(1)
                    log.url = un_escape.group(2)
                else:
                    continue
            elif token_type == DATE:
                log.date = datetime.datetime.strptime(re_match.group(1),
                                                   "%d/%b/%Y:%H:%M:%S %z")  # парсим дату
            elif token_type == IP:
                log.ip = re_match.group(0)
            else:
                raise SyntaxError("Unknown token", token_type, re_match)
        return log

