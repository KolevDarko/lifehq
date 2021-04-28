# To be run every hour and 5 minutes
# I think it's 5 * ***
import logging
import traceback

from django.core.management import BaseCommand

from apps.base.models import PersonalTodoList, Profile
from mastermind.utils import user_time_now

logger = logging.getLogger('crons')


class WeekPlannerSyncCron:

    @classmethod
    def do_sync(cls):
        logger.info("Running Week planner sync")
        cls.iterate_profiles_and_sync_planners()

    @classmethod
    def iterate_profiles_and_sync_planners(cls):
        for profile in Profile.objects.all():
            email = profile.account.user.email
            try:
                profile_time = user_time_now(profile.utc_offset)
                if profile_time.hour == 0:
                    logger.info("It is midnight now for {}".format(email))
                    synced_tasks = PersonalTodoList.sync_week_planner_today(profile)
                    logger.info("Synced {} tasks for {}".format(synced_tasks, email))
            except Exception:
                logger.exception("Problem in week planner sync for {}".format(email))
                logger.exception(traceback.format_exc())


class Command(BaseCommand):
    help = "Syncs week tasks today"

    def handle(self, *args, **options):
        WeekPlannerSyncCron.do_sync()
