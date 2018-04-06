import logging
import requests
import datetime
import os.path
import re

from django.core.management.base import BaseCommand

from parser_log.models import ApacheLog


WSP, REQUEST, QUOTED_STRING, DATE, RAW1, RAW, NO_DATA, IP = range(8) # ENUM


RULES = [
    ('\s+', WSP),
    ('-|"-"', NO_DATA),
    ('[0-9]{1,3}(\.[0-9]{1,3}){3}', IP),
    ('"(([A-Z]+)\s(\/|[htps://].*)\s([A-Z]+\/(\d)\.(\d)))"', REQUEST),
    ('"([^"]+)"', QUOTED_STRING),
    ('\[([^\]]+)\]', DATE),
    ('([0-9]+)\s([0-9]+)|-', RAW1),
    ('([^\s]+)', RAW),
]


class Command(BaseCommand):
    help = """Accepts a link or a local path to a log file of a certain format, 
    downloads it, parses it and writes it to DB."""
    size_file = 0
    path_file = ''
    list_log = []  # list for bulk save Apache Log objects
    count_str = 0
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

    def line_handling(self, line):
        self.count_str += 1
        self.size_record += len(line)
        log = self.parse_line(line)
        if log.date or log.ip:
            self.list_log.append(log)
            per = self.get_percent(self.size_record)
            if per > self.percent:
                self.percent = per
                self.stdout.write('Complete - '
                                  + str(self.percent)
                                  + '%. Parsed ' + str(
                    self.count_str) + ' rows.'
                                  , ending='\r')
                ApacheLog.objects.bulk_create(self.list_log)
                self.list_log.clear()

    def download(self):
        r = requests.get(self.path_file, stream=True)
        # The size of the uploaded file from 'headers'
        self.size_file = int(r.headers.get('Content-Length'))

        self.stdout.write('Start download, parsing and writing to DB.')
        for line in r.iter_lines(chunk_size=512, decode_unicode=True):
            self.line_handling(line)

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

            for line in file:
                self.line_handling(line)

    def parse_line(self, line):
        # accepts a string
        # returns the object model Log

        try:
            tokens = self.lex(line)
        except Exception:
            logging.exception("Error in line '%s'", line)
            return None

        log = ApacheLog()
        for re_match, token_type in tokens:
            if token_type == WSP:
                # spaces are ignored
                continue
            elif token_type == NO_DATA:
                # NO_DATA are ignored
                continue
            elif token_type == RAW1:
                log.id_resp = re_match.group(1)
                log.resp_size = re_match.group(2)
                continue
            elif token_type == RAW:
                continue
            elif token_type == QUOTED_STRING:
                # quoted string is ignored
                continue
            elif token_type == REQUEST:
                    log.method = re_match.group(2)
                    log.url = re_match.group(3)
            elif token_type == DATE:
                log.date = datetime.datetime.strptime(re_match.group(1),
                                                   "%d/%b/%Y:%H:%M:%S %z")
            elif token_type == IP:
                log.ip = re_match.group(0)
            else:
                raise SyntaxError("Unknown token", token_type, re_match)
        return log

