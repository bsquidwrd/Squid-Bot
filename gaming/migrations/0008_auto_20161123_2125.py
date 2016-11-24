# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-24 05:25
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0007_auto_20161029_2354'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='game',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='gaming.Game'),
        ),
        migrations.AddField(
            model_name='channel',
            name='game_channel',
            field=models.BooleanField(default=False),
        ),
    ]
