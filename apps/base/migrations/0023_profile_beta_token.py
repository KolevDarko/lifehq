# Generated by Django 2.0 on 2018-11-16 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0022_auto_20181113_0712'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='beta_token',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
