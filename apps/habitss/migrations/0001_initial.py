# Generated by Django 2.0 on 2018-08-07 18:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0007_auto_20180525_0906'),
    ]

    operations = [
        migrations.CreateModel(
            name='Habit',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('status', models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name='HabitAction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_date', models.DateField()),
                ('status', models.CharField(default='0', max_length=10)),
                ('habit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='habitss.Habit')),
            ],
        ),
        migrations.CreateModel(
            name='HabitParent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.AddField(
            model_name='habit',
            name='habit_parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='habitss.HabitParent'),
        ),
        migrations.AddField(
            model_name='habit',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Profile'),
        ),
    ]