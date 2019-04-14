# Generated by Django 2.1.5 on 2019-04-14 07:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bitfit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attempt',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('datetime', models.DateTimeField(auto_now_add=True)),
                ('user_code', models.TextField()),
                ('passed_tests', models.BooleanField(default=False)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitfit.Profile')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bitfit.Question')),
            ],
        ),
    ]