# Generated by Django 2.0 on 2019-01-16 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0040_auto_20190111_1658'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='total_upload_quota',
            field=models.FloatField(default=0.0),
        ),
    ]
