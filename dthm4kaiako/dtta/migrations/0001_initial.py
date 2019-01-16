# Generated by Django 2.1.5 on 2019-01-16 23:45

from django.db import migrations, models
import markdownx.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='NewsArticle',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('datetime', models.DateTimeField()),
                ('content', markdownx.models.MarkdownxField()),
            ],
        ),
    ]
