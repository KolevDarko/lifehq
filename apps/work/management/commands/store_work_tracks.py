import datetime

from django.core.management import BaseCommand

from apps.base.models import Profile, ProjectTodoItem
from apps.work.models import TrackWorkedDay
from mastermind.utils import user_time_now


class Command(BaseCommand):
    help = "Store worked today minutes into db"

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            if profile.is_plan_valid():
                profile_time = user_time_now(profile.utc_offset)
                if profile_time.hour == 0:
                    for project in profile.projects.all():
                        self.store_project_tasks(profile, project)
                    self.store_personal_tasks(profile)

    def store_project_tasks(self, profile, project):
        project_tasks_worked = ProjectTodoItem.project_tasks_worked_today(project)
        profile_now = user_time_now(profile.utc_offset)
        profile_yesterday = (profile_now - datetime.timedelta(days=1)).date()
        for task in project_tasks_worked:
            record = TrackWorkedDay(user=profile,
                                    project=project,
                                    task_list=task.project_list,
                                    task=task,
                                    track_date=profile_yesterday,
                                    minutes_worked=task.minutes_worked_today
                                    )
            record.save()
            task.minutes_worked_today = 0
            task.save()

    def store_personal_tasks(self, profile):
        personal_tasks_worked = ProjectTodoItem.personal_tasks_worked_today(profile)
        profile_now = user_time_now(profile.utc_offset)
        profile_yesterday = (profile_now - datetime.timedelta(days=1)).date()
        for task in personal_tasks_worked:
            record = TrackWorkedDay(user=profile,
                                    task=task,
                                    track_date=profile_yesterday,
                                    minutes_worked=task.minutes_worked_today
                                    )
            record.save()
            task.minutes_worked_today = 0
            task.save()
