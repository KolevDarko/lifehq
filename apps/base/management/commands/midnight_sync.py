import datetime
import logging
import traceback

from dateutil.relativedelta import relativedelta
from django.core.management import BaseCommand

from apps.base.models import Profile
from apps.habitss.models import Habit, HabitStatus
from apps.journal.models import JournalEntry
from mastermind.utils import user_time_now, calc_week_start

logger = logging.getLogger('crons')

class MidnightCron:

    @staticmethod
    def last_day_of_month(now_date):
        last = now_date + relativedelta(months=1) - datetime.timedelta(now_date.day)
        return last.day

    @classmethod
    def create_journals(cls, profile, profile_time):
        journal = profile.journal_set.first()
        journal_date = profile_time.date()
        if journal.day:
            day_entry = JournalEntry.create_from_template(JournalEntry.DAY, journal.id, user_date_now=journal_date)
            logger.info("Day journal for {}".format(profile.account.user.email))

        if journal.week and profile_time.isoweekday() == 7:
            week_entry = JournalEntry.create_from_template(JournalEntry.WEEK, journal.id, user_date_now=journal_date)
            logger.info("Week journal for {}".format(profile.account.user.email))

        if journal.month and profile_time.day == 1:
            month_entry = JournalEntry.create_from_template(JournalEntry.MONTH, journal.id, user_date_now=journal_date)
            logger.info("Month journal for {}".format(profile.account.user.email))

        if journal.year and profile_time.month == 1 and profile_time.day == 1:
            year_entry = JournalEntry.create_from_template(JournalEntry.YEAR, journal.id, user_date_now=journal_date)
            logger.info("Year journal for {}".format(profile.account.user.email))

    @classmethod
    def create_habit_actions(cls, profile):
        user_habits = Habit.objects.filter(user=profile, status=HabitStatus.ACTIVE).order_by('id').all()
        week_start = calc_week_start(profile.utc_offset)
        for habit in user_habits:
            habit.create_week_actions(_week_start=week_start)

    @classmethod
    def do_sync(cls):
        logger.info("Running MidnightCron")
        cls.iterate_profiles_and_gen_stuff()

    @classmethod
    def iterate_profiles_and_gen_stuff(cls):
        for profile in Profile.objects.all():
            email = profile.account.user.email
            if not profile.is_plan_valid():
                logger.info("Skipping profile {}".format(email))
                continue
            try:
                profile_time = user_time_now(profile.utc_offset)
                if profile_time.hour == 0:
                    logger.info("It is midnight now for {}".format(email))
                    cls.create_journals(profile, profile_time)
                    if profile_time.isoweekday() == 1:
                        cls.create_habit_actions(profile)
            except Exception:
                logger.exception("Problem in midnight cron for {}".format(email))
                logger.exception(traceback.format_exc())


class Command(BaseCommand):
    help = "Sync journals & habits"

    def handle(self, *args, **options):
        MidnightCron.do_sync()
