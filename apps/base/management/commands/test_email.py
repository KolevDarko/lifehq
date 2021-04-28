from django.core import mail
from django.core.management import BaseCommand


class Command(BaseCommand):
    help = "Sends test email"

    def add_arguments(self, parser):
        parser.add_argument('to')
        parser.add_argument('subject')

    def handle(self, *args, **options):
        subject = options["subject"]
        to = options["to"]
        content = "TEst content"
        mail.send_mail(subject, content, "darko@email.lifehqapp.com", [to])
        self.stdout.write("Sent email executed")
