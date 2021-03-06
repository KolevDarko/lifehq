# Generated by Django 2.0 on 2019-01-30 15:56

from django.db import migrations
import hashid_field.field


class Migration(migrations.Migration):

    dependencies = [
        ('habitss', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='habit',
            name='id',
            field=hashid_field.field.HashidAutoField(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', min_length=7, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='habitaction',
            name='id',
            field=hashid_field.field.HashidAutoField(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', min_length=7, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='habitparent',
            name='id',
            field=hashid_field.field.HashidAutoField(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890', min_length=7, primary_key=True, serialize=False),
        ),
    ]
