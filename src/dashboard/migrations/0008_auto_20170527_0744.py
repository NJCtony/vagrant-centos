# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-27 07:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_auto_20170527_0741'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderdifference',
            name='soldtoname',
            field=models.CharField(default=None, max_length=64),
        ),
    ]