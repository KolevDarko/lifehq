import datetime
import logging

from django.core.management import BaseCommand

from apps.base.models import ProjectTodoItem, Profile
from apps.habitss.models import HabitAction, HabitActionStatus
from apps.journal.models import JournalEntry
from apps.work.models import KarmaPoints
from mastermind.utils import user_time_now

logger = logging.getLogger('crons')

class Command(BaseCommand):
    help = "Store karma points for the last days"

    def add_arguments(self, parser):
        parser.add_argument('--days')

    def calc_habit_points(self, profile, calc_date):
        finished, not_finished = HabitAction.get_habit_actions_by_date_by_profile(calc_date, profile)
        final_score = 0
        for habit_action in finished:
            if habit_action.status == HabitActionStatus.YES:
                final_score += 1
            elif habit_action.status == HabitActionStatus.HALF:
                final_score += 0.5
        return final_score

    def calc_journal_points(self, profile, calc_date):
        completed_entries = JournalEntry.get_done_entries_by_day_by_user(calc_date, profile)
        return completed_entries.count()

    def calc_karma(self, profile, calc_date):
        completed_tasks = ProjectTodoItem.get_completed_tasks_by_user_by_date(profile, calc_date)
        task_points = completed_tasks.count()
        habit_points = self.calc_habit_points(profile, calc_date)
        journal_points = self.calc_journal_points(profile, calc_date)
        total_points = task_points + habit_points + journal_points
        KarmaPoints.store_points(profile, calc_date, task_points, habit_points, journal_points, total_points)

    def is_midnight(self, profile_time):
        return profile_time.hour == 0

    def handle(self, *args, **options):
        days_back = -1
        if options.get('days'):
            days_back = int(options['days'])
        print("Calcing karma for {} days".format(days_back))

        for profile in Profile.objects.all():
            if profile.is_plan_valid():
                if days_back == -1:
                    profile_time = user_time_now(profile.utc_offset)
                    if self.is_midnight(profile_time):
                        calc_datetime = profile_time - datetime.timedelta(days=1)
                        print("Calcing karma for {} for {}".format(profile.id, calc_datetime.isoformat()))
                        self.calc_karma(profile, calc_datetime.date())
                else:
                    profile_today = user_time_now(profile.utc_offset)
                    for i in range(1, days_back):
                        calc_datetime = profile_today - datetime.timedelta(days=i)
                        print("Calcing karma for {} for {}".format(profile.id, calc_datetime.isoformat()))
                        self.calc_karma(profile, calc_datetime.date())
