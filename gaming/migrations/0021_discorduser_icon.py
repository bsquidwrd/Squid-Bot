# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-12-10 05:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0020_auto_20161204_0049'),
    ]

    operations = [
        migrations.AddField(
            model_name='discorduser',
            name='icon',
            field=models.CharField(blank=True, max_length=4000, null=True),
        ),
    ]
