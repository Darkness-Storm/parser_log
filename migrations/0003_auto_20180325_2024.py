# Generated by Django 2.0.3 on 2018-03-25 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parser_log', '0002_auto_20180319_0937'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apachelog',
            name='id_resp',
            field=models.IntegerField(blank=True),
        ),
        migrations.AlterField(
            model_name='apachelog',
            name='resp_size',
            field=models.IntegerField(blank=True),
        ),
    ]
