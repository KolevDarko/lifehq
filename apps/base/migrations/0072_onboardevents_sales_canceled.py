# Generated by Django 2.0 on 2019-04-19 07:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0071_auto_20190418_0446'),
    ]

    operations = [
        migrations.AddField(
            model_name='onboardevents',
            name='sales_canceled',
            field=models.BooleanField(default=False),
        ),
    ]
