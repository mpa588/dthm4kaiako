# Generated by Django 2.1.5 on 2019-04-11 21:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bitfit', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='questiontypefunctiontestcase',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='testcases', to='bitfit.QuestionTypeFunction'),
        ),
        migrations.AlterField(
            model_name='questiontypeprogramtestcase',
            name='question',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='testcases', to='bitfit.QuestionTypeProgram'),
        ),
    ]
