# Generated by Django 2.0 on 2019-02-14 07:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0061_profile_plan_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paymentevent',
            name='receipt_url',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='cancel_url',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='update_url',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
