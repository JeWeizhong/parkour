# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-03-10 10:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library_sample_shared', '0013_auto_20200310_1108'),
    ]

    operations = [
        migrations.AlterField(
            model_name='indexi5',
            name='index',
            field=models.CharField(max_length=25, verbose_name='Index'),
        ),
        migrations.AlterField(
            model_name='indexi7',
            name='index',
            field=models.CharField(max_length=25, verbose_name='Index'),
        ),
    ]
