# Generated by Django 2.0 on 2019-01-23 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0044_projectpageimage_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectpageimage',
            name='file_size',
            field=models.FloatField(default=10),
            preserve_default=False,
        ),
    ]