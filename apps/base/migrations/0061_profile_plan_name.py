# Generated by Django 2.0 on 2019-02-14 06:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0060_paymentevent'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='plan_name',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
