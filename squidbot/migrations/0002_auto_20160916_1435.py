# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-09-16 21:35
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('squidbot', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='discorduser',
            options={'verbose_name': 'Discord User', 'verbose_name_plural': 'Discord Users'},
        ),
        migrations.AlterModelOptions(
            name='game',
            options={'verbose_name': 'Game', 'verbose_name_plural': 'Games'},
        ),
        migrations.AlterModelOptions(
            name='gamesearch',
            options={'verbose_name': 'Game Search', 'verbose_name_plural': 'Game Searches'},
        ),
        migrations.AlterModelOptions(
            name='gameuser',
            options={'verbose_name': 'Game User', 'verbose_name_plural': 'Game Users'},
        ),
        migrations.AlterModelOptions(
            name='role',
            options={'verbose_name': 'Role', 'verbose_name_plural': 'Roles'},
        ),
        migrations.AlterModelOptions(
            name='server',
            options={'verbose_name': 'Server', 'verbose_name_plural': 'Servers'},
        ),
        migrations.RemoveField(
            model_name='game',
            name='count',
        ),
    ]
