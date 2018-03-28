import logging

import requests
import datetime
import os.path
import re

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from parser_log.models import ApacheLog


MONTH_NAME = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12,
}


class Command(BaseCommand):
    help = """Accepts a link to a log file of a certain format, downloads it, 
    parses it and writes it to DB."""
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
        self.prepared = [(re.compile(regexp), token_type) for regexp, token_type in RULES]

    def add_arguments(self, parser):
        parser.add_argument('url', nargs='+', type=str)

        parser.add_argument('--file',
                            action='store_true',
                            dest='file',
                            default=False,
                            help='parses it and writes it to DB from a local file')

    def handle(self, *args, **options):
        self.path_file = options.get('url')[0]
        if options['file']:
            self.parse_log_re()
            print('парсинг из локального файла')
        else:
            self.download_re()
            print('парсинг из удаленного файла')
#        self.parse_log_re()

    def download(self, url):
        r = requests.get(url, stream=True)
        "Размер загружаемого файла из headers"
        self.size_file = int(r.headers.get('Content-Length'))
        percent = 0
        with open(self.path_file, 'wb') as fd:
            self.stdout.write('Start download.')
            for chunk in r.iter_content(chunk_size=1024):
                fd.write(chunk)
                size_file = os.path.getsize(fd.name)
                per = self.percent(size_file)
                if per > percent:
                    percent = per
                    self.stdout.write('Complete - '
                                      + str(percent)
                                      + '%'
                                      , ending='\r' )

        self.stdout.write('Complete. Downloading - '
                          + str(self.size_file/1024/1024)
                          + 'Mb')

    def download_re1(self, url):
        r = requests.get(url, stream=True)
        # Размер загружаемого файла из headers
        self.size_file = int(r.headers.get('Content-Length'))

        self.stdout.write('Start download, parsing and writing to DB.')
        for line in r.iter_lines(chunk_size=512, decode_unicode=True):
            self.count_str += 1
            # self.size_record += len(line) #.encode('utf-8'))
            if self.count_str > 885000:
                log = self.parse_line(line, self.count_str)
                print(str(self.count_str) + ', ' + str(log.ip)
                      + ', ' + str(log.date) + ', ' + str(log.method)
                      + ', ' + log.url + ', ' + str(log.id_resp)
                      + ',' + str(log.resp_size))
                log.save()
                if self.count_str > 891603:
                    break

    def download_re(self):
        r = requests.get(self.path_file, stream=True)
        # Размер загружаемого файла из headers
        self.size_file = int(r.headers.get('Content-Length'))

        self.stdout.write('Start download, parsing and writing to DB.')
        for line in r.iter_lines(chunk_size=512, decode_unicode=True):
            self.count_str += 1
            self.size_record += len(line) #.encode('utf-8'))
            log = self.parse_line(line, self.count_str)
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

    def parse_log(self):
        """Парсинг скачанного файла"""

        # с настройками в True ругался на формат даты
        settings.USE_TZ = False
        with open(self.path_file, 'r') as file:
            self.stdout.write('Start parsing and writing to DB.')
            #количество обработанных строк
            count_str = 0
            #размер обработанных строк в байтах
            size_record = 0
            self.size_file = os.path.getsize(self.path_file)
            # список для для массового сохранения объектов ApacheLog
            list_log = []

            for s in file:
                count_str += 1
                size_record += len(s.encode('utf-8'))
                r = s.split(' ')
                try:
                    ip = r[0]
                    date = self.parse_date(r[3][1:])
                    method = r[5][1:]
                    #В логе в есть места, где вместо метода 'POST' или 'GET'
                    #адовая ерунда с окончанием 'POST' или 'GET'"""
                    if method.endswith('POST') and len(method) > 4:
                        method = 'POST'
                    elif method.endswith('GET') and len(method) > 3:
                        method = 'GET'
                    url = r[10][1:-2]
                    resp = int(r[8])
                    try:
                        size = int(r[9])
                    except:
                        size = 0
                    log = ApacheLog(ip=ip
                                    , date=date
                                    , method=method
                                    , url=url
                                    , resp_size=size
                                    , id_resp=resp)
                    list_log.append(log)
                except IndexError:
                    continue
                if str(count_str).endswith('000'):
                    # Пишем по тысяче строк
                    ApacheLog.objects.bulk_create(list_log)
                    list_log.clear()
                    self.stdout.write('Parsed ' + str(count_str)
                                      + ' rows. Complete '
                                      + str(self.percent(size_record))
                                      + '%', ending='\r')
            self.stdout.write('Parsed ' + str(count_str) + ' rows' + ' '*20)
            settings.USE_TZ = True

    def parse_date(self, string_date):
        """Преобразовываем строку даты из лога в Python datetime"""
        l = string_date.split('/')
        day = int(l[0])
        month = MONTH_NAME.get(l[1])
        l1 = l[2].split(':')
        year = int(l1[0])
        hour = int(l1[1])
        min = int(l1[2])
        sec = int(l1[3])
        full_date = datetime.datetime(year, month, day, hour, min, sec)
        return full_date

    def lex(self, line):
        ll = len(line) # длина строки лога - чтобы знать, когда остановиться
        i = 0          # текущая позиция анализатора
        while i < ll:
            for pattern, token_type in self.prepared:  # пробуем регулярные выражения по очереди
                match = pattern.match(line, i)    # проверяем соответствует ли регулярное выражение строке с позиции i
                if match is None:                 # если нет - пробуем следующую регулярку
                    continue
                i = match.end()                   # передвигаем позицию анализатора до индекса, соответствующего концу совпадения
                yield (match, token_type)         # возвращаем найденный токен
                break                             # начинаем анализировать остаток строки с новым значением сдвига i
            # по хорошему, в этом месте нужно кидать ошибку SyntaxError(line, i) в случае, если ни один из шаблонов не совпал

    def parse_log_re(self):

        self.size_file = os.path.getsize(self.path_file)
        with open(self.path_file, 'r') as file:
            self.stdout.write('Start parsing and writing to DB.')

            for s in file:
                self.count_str += 1
                self.size_record += len(s.encode('utf-8'))
                log = self.parse_line(s, self.count_str)
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

    def parse_line(self, line, row_number):
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
#                resp = re.match(r'([0-9]+)', re_match.group(0))
#                if resp:
#                    log.id_resp = re_match.group(1)
                continue
            elif token_type == QUOTED_STRING:
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


def Lexer(rules):
    # предварительно компилируем регулярные выражения для ускорения работы
    prepared = [(re.compile(regexp), token_type) for regexp, token_type in rules]

    def lex(line):
        ll = len(line) # длина строки лога - чтобы знать, когда остановиться
        i = 0          # текущая позиция анализатора
        while i < ll:
            for pattern, token_type in prepared:  # пробуем регулярные выражения по очереди
                match = pattern.match(line, i)    # проверяем соответствует ли регулярное выражение строке с позиции i
                if match is None:                 # если нет - пробуем следующую регулярку
                    continue
                i = match.end()                   # передвигаем позицию анализатора до индекса, соответствующего концу совпадения
                yield (match, token_type)         # возвращаем найденный токен
                break                             # начинаем анализировать остаток строки с новым значением сдвига i
            # по хорошему, в этом месте нужно кидать ошибку SyntaxError(line, i) в случае, если ни один из шаблонов не совпал
    return lex

# lexer = Lexer(RULES)
# s= '109.169.248.247 - - [12/Dec/2015:18:25:11 +0100] "POST /administrator/index.php HTTP/1.1" 200 4494 "http://almhuette-raith.at/administrator/" "Mozilla/5.0 (Windows NT 6.0; rv:34.0) Gecko/20100101 Firefox/34.0" "-"'
# x = lexer(s)
# print(x)