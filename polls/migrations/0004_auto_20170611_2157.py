# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-11 21:57
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('polls', '0003_choice_idinpoll'),
    ]

    operations = [
        migrations.AlterField(
            model_name='poll',
            name='created',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]