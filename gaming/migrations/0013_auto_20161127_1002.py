# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2016-11-27 18:02
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gaming', '0012_auto_20161127_0946'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='message_id',
            field=models.TextField(),
        ),
    ]
