# Generated by Django 2.0 on 2019-05-10 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0072_onboardevents_sales_canceled'),
    ]

    operations = [
        migrations.AddField(
            model_name='projecttodoitem',
            name='planned',
            field=models.DateField(blank=True, null=True),
        ),
    ]
