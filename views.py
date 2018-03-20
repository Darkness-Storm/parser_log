from collections import Counter, OrderedDict

from django.db.models import Sum, Q
from django.views.generic import ListView

from .models import ApacheLog
from .forms import SearchForm



class IndexView(ListView):

    paginate_by = 50
    model = ApacheLog
    context_object_name = 'log'
    template_name = 'parser_log/index.html'

    def get_queryset(self):
        criteria = self.request.GET.get('search')
        if criteria:
            return ApacheLog.objects.filter(
                Q(ip__icontains=criteria)
                | Q(date__icontains=criteria)
                | Q(method__icontains=criteria)
                | Q(url__icontains=criteria))
        else:
             return ApacheLog.objects.all()

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        # queryset без пагинациии
        query_log = self.get_queryset()

        # Сначала я неправильно понял задачу и выводил итоги по странице
        #query_log = context['log']

        #количество записей
        context['count_records'] = query_log.count()

        # количество переданных байт
        sum_resp = query_log.aggregate(Sum('resp_size'))
        context['sum_responce'] = sum_resp

        #уникальные ip
        list_ip = query_log.values_list('ip')
        sum_unique_ip = len(set(list_ip))
        context['sum_unique_ip'] = sum_unique_ip

        new_d = OrderedDict(reversed(sorted(Counter(list_ip).items(), key=lambda x: x[1])))
        unique_ip = [(k[0], v) for k, v in new_d.items()][0:11]
        context['unique_ip'] = unique_ip

        #информация по http-методам
        sum_method = [(k[0], v) for k, v in Counter(query_log.values_list('method')).items()]
        context['sum_method'] = sum_method

        #поисковая форма
        form = SearchForm()
        context['form'] = form
        return context

