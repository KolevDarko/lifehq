# Generated by Django 2.0 on 2018-11-01 07:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0019_profile_first_journal_template'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='has_default_data',
            field=models.BooleanField(default=False),
        ),
    ]