from django.db import models

# Create your models here.

# class ApacheLogManager(models.Manager):
#     def with_counts(self):
#         from django.db import connection
#         cursor = connection.cursor()
#         cursor.execute("""
#             SELECT p.id, p.question, p.poll_date, COUNT(*)
#             FROM polls_opinionpoll p, polls_response r
#             WHERE p.id = r.poll_id
#             GROUP BY p.id, p.question, p.poll_date
#             ORDER BY p.poll_date DESC""")
#         result_list = []
#         for row in cursor.fetchall():
#             p = self.model(id=row[0], question=row[1], poll_date=row[2])
#             p.num_responses = row[3]
#             result_list.append(p)
#         return result_list


class ApacheLog (models.Model):

    ip = models.GenericIPAddressField(verbose_name='IP')
    date = models.DateTimeField(verbose_name='дата запроса')
    method = models.TextField(verbose_name='HTTP - метод', max_length=25, blank=True, default='')
    url = models.URLField(verbose_name='URL', default='')
    id_resp = models.IntegerField(verbose_name='код ответа', blank=True, default=0)
    resp_size = models.IntegerField(verbose_name='размер ответа', blank=True, default=0)

    # def __str__(self):
    #     return 'IP - ' + self.ip + ', date - ' + self.date \
    #            + ', url - ' + self.url + ', response code - ' + self.id_resp