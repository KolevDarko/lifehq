# Generated by Django 2.1.5 on 2019-07-28 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0083_workcyclegroup_finished'),
    ]

    operations = [
        migrations.AddField(
            model_name='projecttodoitem',
            name='priority',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='projecttodoitem',
            name='status',
            field=models.IntegerField(default=0),
        ),
    ]