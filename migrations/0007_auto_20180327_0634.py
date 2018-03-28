# Generated by Django 2.0.3 on 2018-03-27 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parser_log', '0006_auto_20180327_0623'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apachelog',
            name='date',
            field=models.DateTimeField(verbose_name='дата запроса'),
        ),
        migrations.AlterField(
            model_name='apachelog',
            name='ip',
            field=models.GenericIPAddressField(verbose_name='IP'),
        ),
    ]
