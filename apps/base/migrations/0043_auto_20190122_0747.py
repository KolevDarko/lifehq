# Generated by Django 2.0 on 2019-01-22 07:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0042_auto_20190116_0634'),
    ]

    operations = [
        migrations.AlterField(
            model_name='projectresource',
            name='the_file',
            field=models.FileField(upload_to=''),
        ),
    ]