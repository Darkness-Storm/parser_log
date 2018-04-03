from collections import Counter, OrderedDict
import datetime
import xlwt

from django.db.models import Sum, Q, Count
from django.http import HttpResponse
from django.views.generic import ListView

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

        # количество записей
        context['count_records'] = query_log.count()

        # количество переданных байт
        sum_resp = query_log.aggregate(Sum('resp_size'))
        context['sum_responce'] = sum_resp

        # общее количество уникальных ip
        sum_unique_ip = query_log.aggregate(sum_ip=Count('ip', distinct=True))
        context['sum_unique_ip'] = sum_unique_ip

        # агрегация уникальных ip
        unique_ip = query_log.values('ip').annotate(count_ip=Count('ip')).order_by('count_ip').reverse()[0:11]
        context['unique_ip'] = unique_ip

        # информация по http-методам
        sum_method = query_log.values('method').annotate(sum_method=Count('method')).order_by('sum_method').reverse()
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

