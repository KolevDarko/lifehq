import datetime

from dateutil.parser import parse
from django.core.management import BaseCommand

from apps.base.models import Profile


class Command(BaseCommand):
    help = "Sets trial start and trial end to every profile that doesn't have it, and sets subscription to my-trial," \
           "and marks existing users as beta users for special treatment"

    def add_arguments(self, parser):
        parser.add_argument('trial_start_iso')
        parser.add_argument('duration')

    def handle(self, *args, **options):
        start_iso_str = options['trial_start_iso']
        trial_duration = int(options['duration'])
        trial_start = parse(start_iso_str)
        trial_end = trial_start + datetime.timedelta(days=trial_duration)
        for profile in Profile.objects.all():
            if not (profile.plan_start_time or profile.plan_end_time or profile.trial_start_time):
                profile.trial_start_time = trial_start
                profile.trial_end_time = trial_end
                profile.subscription_status = Profile.MY_TRIAL
                profile.profile_type = Profile.BETA_USER
                profile.save()
                self.stdout.write("Started trial for {}".format(profile.name))
