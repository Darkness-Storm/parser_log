# Generated by Django 2.0.3 on 2018-03-18 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ApacheLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip', models.TextField(max_length=100)),
                ('date', models.DateTimeField()),
                ('method', models.TextField(max_length=10)),
                ('url', models.TextField(max_length=256)),
                ('id_err', models.IntegerField()),
                ('resp_size', models.IntegerField()),
            ],
        ),
    ]
