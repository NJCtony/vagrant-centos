# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-27 05:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_auto_20170527_0515'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderdifference',
            name='aler_description',
        ),
        migrations.AddField(
            model_name='orderdifference',
            name='alert_description',
            field=models.CharField(default='', max_length=64),
        ),
    ]
