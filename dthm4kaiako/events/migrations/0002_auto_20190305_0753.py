# Generated by Django 2.1.5 on 2019-03-04 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='url_label',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]