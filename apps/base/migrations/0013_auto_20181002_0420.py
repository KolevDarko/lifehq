# Generated by Django 2.0 on 2018-10-02 04:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0012_project_project_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='first_habit',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_journal',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_knowledge',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_proj_resource',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_proj_schedule',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_proj_tasks',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_project',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='first_today',
            field=models.BooleanField(default=True),
        ),
    ]
