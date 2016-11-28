# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-30 06:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0006_auto_20161029_2347'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='channel',
            name='expire_date',
            field=models.DateTimeField(blank=True, default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='gamesearch',
            name='created_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='gamesearch',
            name='expire_date',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]