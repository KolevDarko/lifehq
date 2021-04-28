import datetime
import logging
import traceback

import boto3
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django_cron import CronJobBase, Schedule

from apps.base.models import Profile, PersonalTodoList, ProjectResource, ProjectPageImage
from apps.base.views import PersonalListExtractorMixin
from apps.common.constants import EMAIL_FROM
from apps.habitss.models import Habit, HabitStatus, HabitAction
from apps.journal.models import JournalEntry, Journal
from mastermind.utils import user_time_now, calc_week_start

logger = logging.getLogger('crons')


class RemindersCron(CronJobBase):
    RUN_EVERY_MINS = 20

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'lifehq.RemindersCron'

    @staticmethod
    def last_day_of_month(now_date: datetime.datetime):
        last = now_date + relativedelta(months=1) - datetime.timedelta(now_date.day)
        return last.day

    @classmethod
    def send_email(cls, ctx, to, period):
        subject = "{} reminder from LifeHQ".format(period)
        subject = "".join(subject.splitlines())
        message = render_to_string("reminders/{}.html".format(str(period).lower()), ctx)
        plain_message = strip_tags(message)
        mail.send_mail(subject, plain_message, EMAIL_FROM, to, html_message=message)
        logger.info("Sent email to {}".format(to[0]))

    def it_is_time(self, profile_time_now, reminder_time_str):
        reminder_time = parse(reminder_time_str)
        return reminder_time <= profile_time_now <= (reminder_time + datetime.timedelta(minutes=19))

    @classmethod
    def journal_messages(cls, journal, profile_time):
        journal_messages = []
        if journal.day:
            message = "Write your daily journal."
            journal_messages.append(message)
        if journal.week and profile_time.isoweekday() == 7:
            message = "Write the week journal! Review the past week and plan the next one."
            journal_messages.append(message)
        if journal.month and profile_time.day == cls.last_day_of_month(profile_time):
            message = "Another month has passed! Write month journal." \
                      "Review the past month and plan the next one."
            journal_messages.append(message)
        if journal.year and profile_time.month == 1 and profile_time.day == 1:
            message = "Happy New Year! Let's make the next one even better. Plan your giant goals in your year journal."
            journal_messages.append(message)
        return journal_messages

    @classmethod
    def send_morning_email(cls, profile, email):
        context = cls.prepare_morning_context(profile)
        cls.send_email(context, [email], 'Morning')

    @classmethod
    def prepare_morning_context(cls, profile):
        _lists = PersonalTodoList.objects.filter(user=profile).order_by('priority')
        users_today = user_time_now(profile.utc_offset).date()
        urgent_list, important_list, extra_list = PersonalListExtractorMixin.extract_personal_lists(_lists, users_today)
        user_habits = Habit.objects.filter(user=profile, status=HabitStatus.ACTIVE).order_by('id').all()
        base_url = "https://{0}".format(
            settings.MY_HOSTNAME
        )

        journal_message = "Get your mindset right for the day."
        context = {
            'name': profile.name or 'friend',
            'journal_link': '{}{}'.format(base_url, '/journal/'),
            'journal_message': journal_message,
            'important': important_list,
            'important_count': len(important_list.todo),
            'urgent': urgent_list,
            'urgent_count': len(urgent_list.todo),
            'habits': user_habits,
            'todos_link': '{}{}'.format(base_url, '/master/todo/'),
            'habits_link': '{}{}'.format(base_url, '/habits/'),
        }
        return context

    @classmethod
    def send_evening_email(cls, profile, email):
        context = cls.prepare_evening_context(profile)
        cls.send_email(context, [email], 'Evening')

    @classmethod
    def prepare_evening_context(cls, profile):
        _lists = PersonalTodoList.objects.filter(user=profile).order_by('priority')
        users_today = user_time_now(profile.utc_offset).date()
        urgent_list, important_list, extra_list = PersonalListExtractorMixin.extract_personal_lists(_lists, users_today)

        profile_time = user_time_now(profile.utc_offset)
        finished, not_finished = HabitAction.get_habits_today(profile_time.date(), profile)

        base_url = "https://{0}".format(
            settings.MY_HOSTNAME
        )
        journal = Journal.objects.get(user=profile)
        journal_messages = cls.journal_messages(journal, profile_time)
        context = {
            'name': profile.name or 'friend',
            'journal_link': '{}{}'.format(base_url, '/journal/'),
            'journal_messages': journal_messages,
            'journal_messages_count': len(journal_messages),
            'important': important_list,
            'urgent': urgent_list,
            'finished_habits': finished,
            'not_finished_habits': not_finished,
            'finished_habits_count': len(finished),
            'total_habits_count': len(finished) + len(not_finished),
            'todos_link': '{}{}'.format(base_url, '/master/todo/'),
            'habits_link': '{}{}'.format(base_url, '/habits/'),
            'plan_link': '{}{}'.format(base_url, '/master/todo#plan'),
        }
        return context

    @classmethod
    def prepare_midday_context(cls, profile):
        _lists = PersonalTodoList.objects.filter(user=profile).order_by('priority')
        users_today = user_time_now(profile.utc_offset).date()
        urgent_list, important_list, extra_list = PersonalListExtractorMixin.extract_personal_lists(_lists, users_today)

        profile_time = user_time_now(profile.utc_offset)
        finished, not_finished = HabitAction.get_habits_today(profile_time.date(), profile)

        base_url = "https://{0}".format(
            settings.MY_HOSTNAME
        )
        context = {
            'name': profile.name or 'friend',
            'important': important_list,
            'urgent': urgent_list,
            'finished_habits': finished,
            'not_finished_habits': not_finished,
            'finished_habits_count': len(finished),
            'total_habits_count': len(finished) + len(not_finished),
            'todos_link': '{}{}'.format(base_url, '/master/todo/'),
            'habits_link': '{}{}'.format(base_url, '/habits/'),
        }
        return context

    @classmethod
    def send_midday_email(cls, profile, email):
        context = cls.prepare_midday_context(profile)
        cls.send_email(context, [email], 'Midday')

    def do(self):
        logger.info("Running all reminders cron")
        for profile in Profile.objects.all():
            try:
                logger.info("Parsting user {}".format(profile.account.user.email))
                if not profile.is_plan_valid():
                    logger.info("Profile plan has expired, no reminders")
                    continue
                email = profile.account.user.email
                if profile.account.user.is_staff:
                    logger.info("Skipping admin {}".format(email))
                    continue
                profile_time = user_time_now(profile.utc_offset)
                morning_reminder = profile.get_morning_reminder()
                if morning_reminder and self.it_is_time(profile_time, morning_reminder):
                    self.send_morning_email(profile, email)
                    logger.info("Morning email to {}".format(email))

                midday_reminder = profile.get_midday_reminder()
                if midday_reminder and self.it_is_time(profile_time, midday_reminder):
                    self.send_midday_email(profile, email)
                    logger.info("Midday email to {}".format(email))

                evening_reminder = profile.get_evening_reminder()
                if evening_reminder and self.it_is_time(profile_time, evening_reminder):
                    self.send_evening_email(profile, email)
                    logger.info("Evening email to {}".format(email))

            except Exception:
                logger.exception("Error for {}".format(profile.account.user.email))
                logger.exception(traceback.format_exc())


class AwsResourceCleanupCron(CronJobBase):
    RUN_EVERY_MINS = 3600

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'lifehq.AwsResourceCleanupCron'

    @staticmethod
    def is_resource(object_key):
        try:
            ProjectResource.objects.get(name=object_key)
            return True
        except ProjectResource.DoesNotExist:
            return False

    @staticmethod
    def is_image(object_key):
        try:
            ProjectPageImage.objects.get(name=object_key)
            return True
        except ProjectPageImage.DoesNotExist:
            return False


    @staticmethod
    def cleanup_aws_objects():
        BUCKET_NAME = 'lifehq-bucket-1'
        s3_resource = boto3.resource('s3')
        my_bucket = s3_resource.Bucket(BUCKET_NAME)
        for object in my_bucket.objects.all():
            object_key = object.key
            is_resource = AwsResourceCleanupCron.is_resource(object_key)
            is_image = AwsResourceCleanupCron.is_image(object_key)
            if not(is_resource or is_image):
                print("About to delete {}".format(object_key))
                object.delete()


    @staticmethod
    def update_profile_usages():
        for profile in Profile.objects.all():
            usage = 0.0
            for project in profile.projects.all():
                for proj_resource in project.resources.all():
                    usage += proj_resource.file_size
                for page in project.pages.all():
                    for pageImage in page.images.all():
                        usage += pageImage.file_size
            profile.total_upload_quota = usage
            profile.save()

    def do(self):
        print("Running AWS Cleanup")
        self.cleanup_aws_objects()
        self.update_profile_usages()
