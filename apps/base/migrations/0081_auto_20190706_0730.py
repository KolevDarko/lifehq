# Generated by Django 2.1.5 on 2019-07-06 07:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0080_auto_20190703_0643'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='time_target_duration',
            field=models.FloatField(blank=True, default=None, null=True),
        ),
    ]
