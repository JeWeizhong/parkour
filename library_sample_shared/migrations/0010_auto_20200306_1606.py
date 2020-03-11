# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-06 15:06
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_sample_shared', '0009_auto_20200220_1547'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indextype',
            name='index_length',
            field=models.CharField(choices=[('6', '6'), ('8', '8'), ('10', '10'), ('12', '12'), ('14', '14'), ('16', '16'), ('18', '18'), ('20', '20'), ('22', '22'), ('24', '24')], default='8', max_length=2, verbose_name='Index Length'),
        ),
    ]
