# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-10-02 21:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('privatechannel', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='privatechannel.DiscordUser'),
            preserve_default=False,
        ),
    ]
