# Generated by Django 2.0 on 2018-11-13 07:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0021_signuptoken'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='signuptoken',
            name='used',
        ),
        migrations.AddField(
            model_name='signuptoken',
            name='valid',
            field=models.BooleanField(default=True),
        ),
    ]