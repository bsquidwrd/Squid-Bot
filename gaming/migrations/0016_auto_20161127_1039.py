# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-27 18:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0015_channel_warning_sent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='expire_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
