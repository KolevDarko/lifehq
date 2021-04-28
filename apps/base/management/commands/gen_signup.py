import uuid

from django.core.management import BaseCommand

from apps.base.models import SignupToken


class Command(BaseCommand):
    help = "Creates a signup token that stands by itself"

    def add_arguments(self, parser):
        parser.add_argument('token')

    def handle(self, *args, **options):
        new_token = options['token']
        SignupToken.objects.create(token=new_token)
        self.stdout.write("Created token {}".format(new_token))
