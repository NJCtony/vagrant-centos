# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-17 06:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0030_auto_20170617_0642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='clm_code',
            field=models.CharField(default='', max_length=16),
        ),
    ]
