# Generated by Django 2.0 on 2019-05-09 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0072_onboardevents_sales_canceled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workcycle',
            name='blocker_answer',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name='workcycle',
            name='how_startanswer',
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name='workcycle',
            name='what_answer',
            field=models.CharField(max_length=150),
        ),
    ]
