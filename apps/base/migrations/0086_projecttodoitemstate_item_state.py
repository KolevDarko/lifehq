# Generated by Django 2.1.5 on 2019-08-21 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0085_projecttodoitemstate'),
    ]

    operations = [
        migrations.AddField(
            model_name='projecttodoitemstate',
            name='item_state',
            field=models.IntegerField(default=1),
            preserve_default=False,
        ),
    ]
