# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-06-03 08:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0018_auto_20170601_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='needthreerecord',
            name='num_sd_diff',
            field=models.FloatField(default=0),
        ),
    ]
