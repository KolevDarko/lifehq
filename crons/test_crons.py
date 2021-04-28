import datetime

import pytz
from django.template.loader import render_to_string
from django.test import TestCase

from apps.base.models import Profile, OnboardEvents
from crons.Crons import RemindersCron, MidnightCron, OnboardingCron
from mastermind.utils import user_time_now


def get_profile(email):
    return Profile.objects.get(account__user__email='kolevdarko.work@gmail.com')

class MorningReminderTest():

    @staticmethod
    def test_morning_render():
        profile = Profile.objects.get(account__user__email='kolevdarko.work@gmail.com')
        print("Profile is {} ".format(profile))
        context = RemindersCron.prepare_morning_context(profile)
        message = render_to_string("reminders/morning.html", context)
        with open('/Users/darko/dev/django-new/mastermind/morning-out.html', 'w') as f:
            f.write(message)

    @staticmethod
    def test_evening_render():
        profile = Profile.objects.get(account__user__email='kolevdarko.work@gmail.com')
        print("Profile is {} ".format(profile))
        context = RemindersCron.prepare_evening_context(profile)
        message = render_to_string("reminders/evening.html", context)
        with open('/Users/darko/dev/django-new/mastermind/evening-out.html', 'w') as f:
            f.write(message)

    @staticmethod
    def test_midday_render():
        profile = Profile.objects.get(account__user__email='kolevdarko.work@gmail.com')
        print("Profile is {} ".format(profile))
        context = RemindersCron.prepare_midday_context(profile)
        message = render_to_string("reminders/midday.html", context)
        with open('/Users/darko/dev/django-new/mastermind/midday-out.html', 'w') as f:
            f.write(message)


class MidnightCronTest(TestCase):

    def test_gen_stuff(self):
        MidnightCron.iterate_profiles_and_gen_stuff()


class OnboardCronTest(TestCase):

    fixtures = ['users.json', 'accounts.json', 'profile.json']

    def setUp(self):
        self.me = get_profile('kolevdarko.work@gmail.com')
        self.onboard = OnboardEvents.objects.create(user=self.me)
        super(OnboardCronTest, self).setUp()

    def test_onboard_user_regular(self):
        self.user_now = pytz.utc.localize(datetime.datetime(2019, 3, 22, 19, 20))
        OnboardingCron.onboard_user(self.onboard, self.user_now)
        self.onboard.refresh_from_db()
        self.should_be_journal(self.user_now)

        same_day_later = self.user_now+datetime.timedelta(hours=10)
        OnboardingCron.onboard_user(self.onboard, same_day_later)
        self.assertIsNone(self.onboard.next_to_send(same_day_later))

        next_day = self.user_now + datetime.timedelta(hours=24)
        OnboardingCron.onboard_user(self.onboard, next_day)
        self.should_be_project(next_day)

        next_day = next_day + datetime.timedelta(hours=24)
        OnboardingCron.onboard_user(self.onboard, next_day)
        self.should_be_plan(next_day)

        next_day = next_day + datetime.timedelta(hours=24)
        OnboardingCron.onboard_user(self.onboard, next_day)
        self.should_be_work(next_day)

        next_day = next_day + datetime.timedelta(hours=24)
        OnboardingCron.onboard_user(self.onboard, next_day)
        self.should_be_habits(next_day)

    def test_onboard_user_from_project(self):
        self.user_now = pytz.utc.localize(datetime.datetime(2019, 3, 22, 19, 20))
        self.onboard.project = ":user"
        self.onboard.project_date = self.user_now - datetime.timedelta(hours=10)
        OnboardingCron.onboard_user(self.onboard, self.user_now)
        self.onboard.refresh_from_db()
        next_day = self.user_now
        self.should_be_plan(next_day)

        next_day = next_day + datetime.timedelta(hours=24)
        OnboardingCron.onboard_user(self.onboard, next_day)
        self.should_be_work(next_day)

        next_day = next_day + datetime.timedelta(hours=24)
        OnboardingCron.onboard_user(self.onboard, next_day)
        self.should_be_journal(next_day)

        next_day = next_day + datetime.timedelta(hours=24)
        OnboardingCron.onboard_user(self.onboard, next_day)
        self.should_be_habits(next_day)

    def should_be_journal(self, sent_at):
        self.assertEqual(self.onboard.journal, ":email")
        self.assertEqual(self.onboard.journal_date, sent_at)
        self.assertEqual(self.onboard.last_sent, sent_at)

    def should_be_project(self, sent_at):
        self.assertIsNotNone(self.onboard.journal)
        self.assertEqual(self.onboard.project, ":email")
        self.assertEqual(self.onboard.project_date, sent_at)
        self.assertEqual(self.onboard.last_sent, sent_at)
        self.assertNotEqual(self.onboard.journal_date, sent_at)
        self.assertIsNone(self.onboard.work)
        self.assertIsNone(self.onboard.plan)
        self.assertIsNone(self.onboard.habits)

    def should_be_plan(self, sent_at):
        self.assertIsNotNone(self.onboard.project)
        self.assertEqual(self.onboard.plan, ":email")
        self.assertEqual(self.onboard.plan_date, sent_at)
        self.assertEqual(self.onboard.last_sent, sent_at)
        self.assertNotEqual(self.onboard.journal_date, sent_at)
        self.assertNotEqual(self.onboard.project_date, sent_at)
        self.assertIsNone(self.onboard.work)
        self.assertIsNone(self.onboard.habits)

    def should_be_work(self, sent_at):
        self.assertEqual(self.onboard.work, ":email")
        self.assertEqual(self.onboard.work_date, sent_at)
        self.assertEqual(self.onboard.last_sent, sent_at)
        self.assertIsNone(self.onboard.habits)

    def should_be_habits(self, sent_at):
        self.assertEqual(self.onboard.habits, ":email")
        self.assertEqual(self.onboard.habits_date, sent_at)
        self.assertEqual(self.onboard.last_sent, sent_at)
