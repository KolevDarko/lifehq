# Generated by Django 2.0 on 2019-03-09 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0066_auto_20190219_1653'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='plan_end_time',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='plan_start_time',
            field=models.DateField(blank=True, null=True),
        ),
    ]
