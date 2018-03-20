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

    ip = models.TextField(max_length=100)
    date = models.DateTimeField()
    method = models.TextField(max_length=10)
    url = models.TextField(max_length=256)
    id_resp = models.IntegerField()
    resp_size = models.IntegerField()

    def __str__(self):
        return 'IP - ' + self.ip + ', date - ' + self.date \
               + ', url - ' + self.url + ', response code - ' + self.id_resp