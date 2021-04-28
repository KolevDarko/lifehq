# Generated by Django 2.0 on 2018-05-25 09:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0006_auto_20180521_0534'),
    ]

    operations = [
        migrations.AddField(
            model_name='projecttodolist',
            name='archived',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='projectpage',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pages', to='base.Project'),
        ),
    ]