# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-22 11:01
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Orders',
            new_name='OrderSnapshot',
        ),
    ]
