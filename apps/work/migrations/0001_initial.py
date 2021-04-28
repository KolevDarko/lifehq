# Generated by Django 2.1.5 on 2019-07-04 04:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0080_auto_20190703_0643'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrackWorkedDay',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('track_date', models.DateField()),
                ('minutes_worked', models.IntegerField()),
                ('project', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='profile_tracks', to='base.Project')),
                ('task', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_item_tracks', to='base.ProjectTodoItem')),
                ('task_list', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='project_list_tracks', to='base.ProjectTodoList')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_tracks', to='base.Profile')),
            ],
        ),
    ]
