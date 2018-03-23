import re

#
# m = re.match(r"(?P<method>([A-Z]]+)) (?P<url>\/(.*)\s+) (?P<version>[A-Z]+\/(\d+)\.(\d+))", "GET /index.php?option=com_content&view=article&id=46&Itemid=54 HTTP/1.1")
s = '194.232.72.121 - - [24/Jul/2017:16:24:42 +0200] "GET /images/phocagallery/almhuette/thumbs/phoca_thumb_l_almhuette_raith_007.jpg HTTP/1.1" 200 87330 "http://www.almhuette-raith.at/index.php?option=com_phocagallery&view=category&id=1&Itemid=53" "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0" "-"'
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

# lexeme types
WSP, QUOTED_STRING, DATE, RAW, NO_DATA = range(5) # ENUM

RULES = [
    ('\s+', WSP),
    ('-|"-"', NO_DATA),
    ('"([^"]+)"', QUOTED_STRING),
    ('\[([^\]]+)\]', DATE),
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