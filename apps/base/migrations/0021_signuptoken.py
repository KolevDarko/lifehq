# Generated by Django 2.0 on 2018-11-12 16:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0020_profile_has_default_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignupToken',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=200)),
                ('used', models.BooleanField(default=False)),
            ],
        ),
    ]
