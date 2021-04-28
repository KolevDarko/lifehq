import datetime
import hashlib

import pytz
from account.hooks import AccountDefaultHookSet
from account.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

HUMAN_FORMAT = '%b %d, %Y - %H:%M'
HUMAN_FORMAT_DATE = '%b %d, %Y'
SHORT_DATE_FORMAT = '%b %d'


def delta_from_offset(str_offset):
    negative = False
    minutes = 0
    if '.' in str_offset:
        parts = str_offset.split('.')
        if parts[0].startswith('-'):
            hours = int(parts[0][1:])
            negative = True
        else:
            hours = int(parts[0])
        if parts[1] == '3':
            minutes = 30
    else:
        if str_offset.startswith('-'):
            hours = int(str_offset[1:])
            negative = True
        else:
            hours = int(str_offset)
    if negative:
        hours = -hours
        minutes = -minutes
    return datetime.timedelta(hours=hours, minutes=minutes)


def user_time_now(str_offset):
    utc_now = datetime.datetime.utcnow()
    if str_offset:
        offset_delta = delta_from_offset(str_offset)
        return utc_now + offset_delta
    else:
        return utc_now


def calc_week_start(str_offset):
    today = user_time_now(str_offset).date()
    delta_to_week_start = datetime.timedelta(days=(today.isoweekday() - 1))
    week_start = today - delta_to_week_start
    return week_start

def calc_week_range(str_offset):
    week_start = calc_week_start(str_offset)
    week_end = week_start + datetime.timedelta(days=6)
    return week_start, week_end

def calc_month_start(str_offset):
    today = user_time_now(str_offset).date()
    return datetime.datetime(today.year, today.month, 1).date()


class MyAccountHookset(AccountDefaultHookSet):

    def send_invitation_email(self, to, ctx):
        subject = render_to_string("account/email/invite_user_subject.txt", ctx)
        message = render_to_string("account/email/invite_user.html", ctx)
        plain_message = strip_tags(message)
        mail.send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, to, html_message=message)

    def send_confirmation_email(self, to, ctx):
        subject = render_to_string("account/email/email_confirmation_subject.txt", ctx)
        subject = "".join(subject.splitlines())  # remove superfluous line breaks
        html_message = render_to_string("account/email/email_confirmation_message.html", ctx)
        plain_message = strip_tags(html_message)
        mail.send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, to, html_message=html_message)

    def send_password_change_email(self, to, ctx):
        subject = render_to_string("account/email/password_change_subject.txt", ctx)
        subject = "".join(subject.splitlines())
        message = render_to_string("account/email/password_change.html", ctx)
        plain_message = strip_tags(message)
        mail.send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, to, html_message=message)

    def send_password_reset_email(self, to, ctx):
        subject = render_to_string("account/email/password_reset_subject.txt", ctx)
        subject = "".join(subject.splitlines())
        message = render_to_string("account/email/password_reset.html", ctx)
        plain_message = strip_tags(message)
        mail.send_mail(subject, plain_message, settings.DEFAULT_FROM_EMAIL, to, html_message=message)


def bytes_to_human(bytes_num):
    kb_mul = 1e-3
    mb_mul = 1e-6
    kb_size = bytes_num * kb_mul
    if kb_size > 1000:
        mb_size = bytes_num * mb_mul
        return "{} MB".format(round(mb_size, 2))
    else:
        return "{} KB".format(int(kb_size))


def bytes_to_mb(bytes_num):
    mb_mul = 1e-6
    return bytes_num * mb_mul


def filename_for_storage(profile_id, filename, timestamp=None):
    if not timestamp:
        timestamp = int(datetime.datetime.utcnow().timestamp())
    extension = filename.split('.')[-1]
    raw_unique_filename = "{}/{}/{}".format(timestamp, profile_id, filename)
    hash = hashlib.sha1()
    hash.update(raw_unique_filename.encode())
    hashed_unique = hash.hexdigest()
    full = "{}.{}".format(hashed_unique, extension)
    return full
