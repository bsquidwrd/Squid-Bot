# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-30 06:47
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0005_auto_20161029_2324'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='channel',
            name='expire_date',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now, null=True),
        ),
        migrations.AlterField(
            model_name='gamesearch',
            name='created_date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='gamesearch',
            name='expire_date',
            field=models.DateTimeField(default=datetime.datetime.now),
        ),
    ]