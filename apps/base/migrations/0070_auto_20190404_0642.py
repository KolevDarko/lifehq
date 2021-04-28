# Generated by Django 2.0 on 2019-04-04 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0069_onboardevents_onboard_finished'),
    ]

    operations = [
        migrations.AddField(
            model_name='onboardevents',
            name='discount_1',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='onboardevents',
            name='discount_1_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='onboardevents',
            name='discount_2',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AddField(
            model_name='onboardevents',
            name='discount_2_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
