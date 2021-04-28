from django.core.management import BaseCommand
from django.contrib.auth.models import User

from apps.base.models import Profile
from apps.common.analytics_client import AnalyticsManager


class Command(BaseCommand):
    help = "Analyze user activity data"

    def add_arguments(self, parser):
        parser.add_argument('points')

    def handle(self, *args, **options):
        points = int(options['points'])
        results, power_users = AnalyticsManager.analize_all(points)
        self.stdout.write("Power users {}".format(power_users))
        for user_id, user_data in results.items():
            only_id = user_id.split(":")[1]
            try:
                user = User.objects.get(pk=only_id)
                profile = Profile.objects.get(account__user_id=only_id)
                if profile.is_plan_valid():
                    if profile.subscription_status == profile.MY_TRIAL:
                        if profile.trial_end_time:
                            plan_info = "Trial ending: {}".format(profile.trial_end_time.isoformat())
                        else:
                            plan_info = "No trial end time for"
                    else:
                        plan_info = "Plan valid no trial"
                else:
                    plan_info = "Plan invalid: {}".format(profile.trial_end_time.isoformat())
            except User.DoesNotExist:
                self.stdout.write("User {} does not exist".format(only_id))
                continue
            self.stdout.write("{} {} {}: {}".format(user_id, user.email, plan_info, user_data))
