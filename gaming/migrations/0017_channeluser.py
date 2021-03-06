# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-28 01:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0016_auto_20161127_1039'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChannelUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gaming.Channel')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='gaming.DiscordUser')),
            ],
            options={
                'verbose_name': 'Channel User',
                'verbose_name_plural': 'Channel Users',
            },
        ),
    ]
