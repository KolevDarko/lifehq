from django.core.management import BaseCommand

from apps.base.models import Profile, PersonalTodoList
from apps.base.views import create_day_lists


class Command(BaseCommand):
    help = "Create day lists for all profiles that dont have them"

    def handle(self, *args, **options):
        for profile in Profile.objects.all():
            if PersonalTodoList.profile_has_day_lists(profile):
                self.stdout.write("Profile {} already has day lists".format(profile.id))
            else:
                create_day_lists(profile)
                self.stdout.write("Created day lists for {}".format(profile.id))
