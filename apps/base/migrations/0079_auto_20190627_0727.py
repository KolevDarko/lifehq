# Generated by Django 2.1.5 on 2019-06-27 07:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0078_projecttodoitem_seconds_worked_today'),
    ]

    operations = [
        migrations.RenameField(
            model_name='projecttodoitem',
            old_name='seconds_worked_today',
            new_name='minutes_worked_today',
        ),
    ]
