from collections import Counter, OrderedDict
import datetime

from django.db.models import Sum, Q
from django.http import HttpResponse
from django.views.generic import ListView

import xlwt

from .models import ApacheLog
from .forms import SearchForm


class IndexView(ListView):

    paginate_by = 50
    model = ApacheLog
    context_object_name = 'log'
    template_name = 'parser_log/index.html'
    criteria = None

    def get_queryset(self):
        self.criteria = self.request.GET.get('search')
        if self.criteria:
            queryset_log = ApacheLog.objects.filter(
                Q(ip__icontains=self.criteria)
                | Q(date__icontains=self.criteria)
                | Q(method__icontains=self.criteria)
                | Q(url__icontains=self.criteria))
        else:
            queryset_log = ApacheLog.objects.all()
        return queryset_log

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        context['criteria'] = self.criteria
        # queryset без пагинациии
        query_log = self.get_queryset()

        # Сначала я неправильно понял задачу и выводил итоги по странице
        # query_log = context['log']

        # количество записей
        context['count_records'] = query_log.count()

        # количество переданных байт
        sum_resp = query_log.aggregate(Sum('resp_size'))
        context['sum_responce'] = sum_resp

        # уникальные ip
        list_ip = query_log.values_list('ip')
        sum_unique_ip = len(set(list_ip))
        context['sum_unique_ip'] = sum_unique_ip

        new_d = OrderedDict(reversed(sorted(Counter(list_ip).items(), key=lambda x: x[1])))
        unique_ip = [(k[0], v) for k, v in new_d.items()][0:11]
        context['unique_ip'] = unique_ip

        # информация по http-методам
        sum_method = [(k[0], v) for k, v in Counter(query_log.values_list('method')).items()]
        context['sum_method'] = sum_method

        # поисковая форма
        form = SearchForm()
        context['form'] = form
        return context


def export_xls(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="log.xls"'
    criteria = request.GET.get('criteria')
    # если был использован поиск
    if criteria:
        queryset_log = ApacheLog.objects.filter(
            Q(ip__icontains=criteria)
            | Q(date__icontains=criteria)
            | Q(method__icontains=criteria)
            | Q(url__icontains=criteria))

    else:
        queryset_log = ApacheLog.objects.all()

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Log')

    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['id', 'IP', 'Date', 'Method', 'URL', 'Response code', 'Response size']

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    font_style = xlwt.XFStyle()

    for row in queryset_log:
        # нужно в цикле по списку полей, только траблы с datetime Python
        row_num += 1
        col = 0
        ws.write(row_num, col, row.pk, font_style)
        col += 1
        ws.write(row_num, col, row.ip, font_style)
        col += 1
        date = datetime.datetime.strftime(row.date, '%a, %d %b %Y %H:%M:%S')
        ws.write(row_num, col, date, font_style)
        col += 1
        ws.write(row_num, col, row.method, font_style)
        col += 1
        ws.write(row_num, col, row.url, font_style)
        col += 1
        ws.write(row_num, col, row.id_resp, font_style)
        col += 1
        ws.write(row_num, col, row.resp_size, font_style)

    wb.save(response)
    return response

