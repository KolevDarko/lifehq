# Generated by Django 2.0 on 2019-05-19 06:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0075_merge_20190519_0634'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='personaltodoitem',
            name='todo_list',
        ),
        migrations.AddField(
            model_name='projecttodoitem',
            name='day_list_order',
            field=models.FloatField(null=True),
        ),
        migrations.DeleteModel(
            name='PersonalTodoItem',
        ),
    ]