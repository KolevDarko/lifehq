import datetime
import random

from django.db import models
from django.db.models import Sum

from apps.base.models import Profile, Project, ProjectTodoItem, ProjectTodoList


class TrackWorkedDay(models.Model):

    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='user_tracks')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='profile_tracks', null=True)
    task_list = models.ForeignKey(ProjectTodoList, on_delete=models.CASCADE, related_name='project_list_tracks', null=True)
    task = models.ForeignKey(ProjectTodoItem, on_delete=models.CASCADE, related_name='project_item_tracks')
    track_date = models.DateField()
    minutes_worked = models.IntegerField()

    @classmethod
    def get_by_project(cls, project_id, from_):
        return cls.objects.filter(project_id=project_id, track_date__gte=from_).order_by('track_date')

    @classmethod
    def get_personal(cls, user_id, from_):
        return cls.objects.filter(user_id=user_id, project=None, track_date__gte=from_).order_by('track_date')

    @classmethod
    def get_sum_by_project(cls, project_id, from_):
        worked_sum = cls.objects.filter(project_id=project_id, track_date__gte=from_).aggregate(Sum('minutes_worked'))
        return worked_sum['minutes_worked__sum'] or 0

    @classmethod
    def insert_mock_data(cls, user_id, project_id, start_date):
        project_tasks = ProjectTodoItem.objects.filter(project_list__project_id=project_id)
        for task in project_tasks:
            track_date = start_date
            for i in range(6):
                track = cls(user_id=user_id, project_id=project_id, task_id=task.id, track_date=track_date)
                track.minutes_worked = random.randint(10, 100)
                track.save()
                track_date = track_date + datetime.timedelta(days=1)

    @classmethod
    def add_manual(cls, user_id, task_id, manual_date, manual_minutes, project_id=None, task_list_id=None):
        new_track = cls(
            user_id=user_id,
            minutes_worked=manual_minutes,
            track_date=manual_date,
            task_id=task_id,
            project_id=project_id,
            task_list_id=task_list_id
        )
        new_track.save()
        return new_track

    @classmethod
    def update_track(cls, user_id, project_id, item_id, track_date, track_minutes):
        obj, created = cls.objects.update_or_create(task_id=item_id, track_date=track_date,
                                                      defaults={'minutes_worked': track_minutes,
                                                                'user_id': user_id,
                                                                'project_id': project_id,
                                                                'task_id': item_id,
                                                                'track_date': track_date})

class KarmaPoints(models.Model):

    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='user_karma_points')
    points_date = models.DateField(unique=True)
    task_points = models.FloatField()
    habit_points = models.FloatField()
    journal_points = models.FloatField()
    total_points = models.FloatField()
    # todo add constraint meta

    @classmethod
    def store_points(cls, _user, _date, _task_points, _habit_points, _journal_points, _total_points):
        created, obj = cls.objects.update_or_create(user=_user, points_date=_date,
                                     defaults={
                                         'task_points': _task_points,
                                         'habit_points': _habit_points,
                                         'journal_points': _journal_points,
                                         'total_points': _total_points
                                     })
        print(created)
