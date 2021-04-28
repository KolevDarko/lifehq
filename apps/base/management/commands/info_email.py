import datetime

from django.core import mail
from django.core.management import BaseCommand
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from apps.common.constants import EMAIL_FROM


class Command(BaseCommand):
    help = "How many new trials in last 24h"

    def add_arguments(self, parser):
        parser.add_argument('--days')

    def handle(self, *args, **options):
        days_ago = 1
        if 'days' in options:
            days_ago = int(options['days'])
        yesterday_now = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        new_users = User.objects.filter(date_joined__gte=yesterday_now)
        self.send_the_email(new_users, days_ago)

    def send_the_email(self, new_users, days):
        subject = "New Subscribers at LifeHQ"
        message = render_to_string("admin_info.html", {'days': days, 'new_users_count': new_users.count(), 'new_users': new_users})
        plain_message = strip_tags(message)
        to = ['darko@lifehqapp.com']
        mail.send_mail(subject, plain_message, EMAIL_FROM, to, html_message=message)
