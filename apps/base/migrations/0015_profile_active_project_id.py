# Generated by Django 2.0 on 2018-10-08 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_auto_20181007_1841'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='active_project_id',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
