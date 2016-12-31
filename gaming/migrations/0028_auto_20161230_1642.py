# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-31 00:42
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0027_auto_20161230_1608'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quote',
            name='users',
        ),
        migrations.AddField(
            model_name='quote',
            name='quote_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='quote',
            name='user',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='gaming.DiscordUser'),
            preserve_default=False,
        ),
    ]
