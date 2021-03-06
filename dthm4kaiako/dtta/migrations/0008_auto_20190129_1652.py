# Generated by Django 2.1.5 on 2019-01-29 03:52

import autoslug.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dtta', '0007_relatedlink_order_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='newsarticle',
            name='slug',
            field=autoslug.fields.AutoSlugField(always_update=True, editable=False, null=True, populate_from='title'),
        ),
        migrations.AddField(
            model_name='page',
            name='slug',
            field=autoslug.fields.AutoSlugField(always_update=True, editable=False, null=True, populate_from='title'),
        ),
    ]
