# Generated by Django 2.1.5 on 2019-09-23 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0086_projecttodoitemstate_item_state'),
    ]

    operations = [
        migrations.AddField(
            model_name='onboardevents',
            name='daily_mission',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='onboardevents',
            name='daily_mission_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
