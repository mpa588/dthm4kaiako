# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-28 20:06
from __future__ import unicode_literals

import autoslug.fields
from django.db import migrations
import events.models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0030_series_subtitle'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=True, populate_from=events.models.EventBase.create_slug, unique=True),
        ),
        migrations.AlterField(
            model_name='thirdpartyevent',
            name='slug',
            field=autoslug.fields.AutoSlugField(editable=True, populate_from=events.models.EventBase.create_slug, unique=True),
        ),
    ]