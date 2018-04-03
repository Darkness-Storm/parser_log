import datetime
import re

#
# m = re.match(r"(?P<method>([A-Z]]+)) (?P<url>\/(.*)\s+) (?P<version>[A-Z]+\/(\d+)\.(\d+))", "GET /index.php?option=com_content&view=article&id=46&Itemid=54 HTTP/1.1")
# s = '194.232.72.121 - - [24/Jul/2017:16:24:42 +0200] "GET /images/phocagallery/almhuette/thumbs/phoca_thumb_l_almhuette_raith_007.jpg HTTP/1.1" 200 87330 "http://www.almhuette-raith.at/index.php?option=com_phocagallery&view=category&id=1&Itemid=53" "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" "-"'
# s = '95.213.184.116 - - [19/Dec/2015:05:28:29 +0100] "GET http://almhuette-raith.at/ HTTP/1.1" 200 10479 "-" "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13" "-"'
# m1 = re.match(r"([A-Z]]+)\s\/(.+?)\s(\/.+?)", "GET /index.php?option=com_content&view=article&id=46&Itemid=54 HTTP/1.1")
# m2 = re.search(r'\s\/(.*)\s+', "GET /index.php?option=com_content&view=article&id=46&Itemid=54 HTTP/1.1")
# m3 = re.match(r"([A-Z]+)", "GET /index.php?option=com_content&view=article&id=46&Itemid=54 HTTP/1.1")
# m4 = re.search(r'([A-Z]+)\s+\/(.+?)\s', "GET /index.php?option=com_content&view=article&id=46&Itemid=54 HTTP/1.1")
m5 = re.search(r'[A-Z]+\s(\/.+)\s([A-Z]+\/(\d)\.(\d))', s)
# m5 = re.search(r'([^\s]+)', s)
# m6 = re.search(r'\[([^\]]+)\]', s)
m = re.search(r'[1-9]{1,3}\.[1-9]{1,3}', s)
m = re.search(r'[0-9]{1,3}(\.[0-9]{1,3}){3}', s)
m = re.search(r'[0-9]+\s[0-9]+', s)
m = re.search(r'([A-Z]+)\s(\/|[htps://].*)\s([A-Z]+\/(\d)\.(\d))', s)
# lexeme types
WSP, QUOTED_STRING, DATE, RAW1, RAW, NO_DATA, IP = range(7) # ENUM

RULES = [
    ('\s+', WSP),
    ('-|"-"', NO_DATA),
    ('[0-9]{1,3}(\.[0-9]{1,3}){3}', IP),
    ('"([^"]+)"', QUOTED_STRING),
    ('\[([^\]]+)\]', DATE),
    ('([0-9]+)\s([0-9]+)', RAW1),
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

lexer = Lexer(RULES)
s = '77.117.192.65 - - [10/Jan/2018:15:04:41 +0100] "GET / HTTP/1.1" 200 10479 "-" "\"Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1\"" "-"'
list_rez = []
tokens = lexer(s)
for re_match, token_type in tokens:
    if token_type == WSP:
        # пробелы игнорируем
        continue
    elif token_type == NO_DATA:
        # NO_DATA игнорируем
        continue
    elif token_type == RAW1:
        list_rez.append(re_match.group(0))
        list_rez.append(re_match.group(2))
    elif token_type == RAW:
        resp = re.match(r'([0-9]+)', re_match.group(0))
        if resp:
            list_rez.append(re_match.group(1))
    elif token_type == QUOTED_STRING:
        un_escape = re.match(r'([A-Z]+)\s(\/|[htps://].*)\s([A-Z]+\/(\d)\.(\d))',
                             re_match.group(1))
        if un_escape:
            list_rez.append(un_escape.group(1))
            list_rez.append(un_escape.group(2))
        else:
            continue
    elif token_type == DATE:
        list_rez.append(datetime.datetime.strptime(re_match.group(1),
                                              "%d/%b/%Y:%H:%M:%S %z"))  # парсим дату
    elif token_type == IP:
        list_rez.append(re_match.group(0))
    else:
        raise SyntaxError("Unknown token", token_type, re_match)

print(list_rez)


def Lexer1(rules):
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