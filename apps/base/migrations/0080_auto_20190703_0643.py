# Generated by Django 2.1.5 on 2019-07-03 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0079_auto_20190627_0727'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='time_target_duration',
            field=models.IntegerField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='project',
            name='time_target_type',
            field=models.CharField(blank=True, choices=[('0', 'day'), ('1', 'week'), ('2', 'month'), ('3', 'year')], default=None, max_length=20, null=True),
        ),
    ]
