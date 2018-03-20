import requests
import datetime
import os.path

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
    size_file = 0
    path_file = 'access.log'

    def add_arguments(self, parser):
        parser.add_argument('url', nargs='*', type=str)

    def handle(self, *args, **options):
        url = options.get('url')[0]
        self.download(url)
        self.parse_log()

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

    def percent(self, size_record):
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

