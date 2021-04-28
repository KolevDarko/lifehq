# Generated by Django 2.0 on 2018-09-10 18:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journaltemplate',
            name='template_type',
            field=models.CharField(choices=[('0', 'day'), ('1', 'week'), ('2', 'month'), ('3', 'year')], max_length=20),
        ),
    ]
