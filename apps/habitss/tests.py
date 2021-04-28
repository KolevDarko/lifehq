from datetime import datetime

from account.models import Account
from dateutil.parser import parser, parse
from django.test import TestCase
from django_common.auth_backends import User

from apps.base.models import Profile
from apps.habitss.models import HabitAction, Habit
from apps.habitss.views import HabitStruct


class TestHabitStruct(TestCase):

    def _create_profile(self):
        user = User(email='kolevdarko.work@gmail.com', username='kolevdarko')
        user.set_password("testpass")
        user.pk = 1
        user.save()
        account = Account(user_id=1)
        account.pk = 1
        account.save()
        self.profile = Profile(name='Dare', account_id=1)
        self.profile.save()

    def _create_habit(self):
        self._create_profile()
        habit = Habit(name="TEst ht", user=self.profile)
        habit.save()
        return habit

    def _create_habit_actions(self, habit, action_dates):
        results = []
        for a_date in action_dates:
            ha = HabitAction(habit=habit, action_date=parse(a_date).date())
            results.append(ha)
        return results

    def test_fill_actions(self):
        habit = self._create_habit()
        actions = self._create_habit_actions(habit, ['2019-05-29', '2019-05-31'])
        week_actions = HabitStruct.fill_actions(action_list=actions)
        self.validate_wed_fri(week_actions)

        new_actions = self._create_habit_actions(habit, ['2019-05-27', '2019-06-02'])
        week_actions = HabitStruct.fill_actions(new_actions)
        self.validate_mon_sun(week_actions)

        new_actions = self._create_habit_actions(habit, ['2019-05-30'])
        week_actions = HabitStruct.fill_actions(new_actions)
        self.validate_thu(week_actions)

    def validate_wed_fri(self, week_actions):
        self.assertEqual(7, len(week_actions))
        self.assertFalse(week_actions[0])
        self.assertFalse(week_actions[1])
        self.assertTrue(week_actions[2])
        self.assertFalse(week_actions[3])
        self.assertTrue(week_actions[4])
        self.assertFalse(week_actions[5])
        self.assertFalse(week_actions[6])

    def validate_mon_sun(self, week_actions):
        self.assertEqual(7, len(week_actions))
        self.assertTrue(week_actions[0])
        self.assertEqual(week_actions[0].action_date, datetime(2019, 5, 27).date())
        self.assertFalse(week_actions[1])
        self.assertFalse(week_actions[2])
        self.assertFalse(week_actions[3])
        self.assertFalse(week_actions[4])
        self.assertFalse(week_actions[5])
        self.assertTrue(week_actions[6])
        self.assertEqual(week_actions[6].action_date, datetime(2019, 6, 2).date())

    def validate_thu(self, week_actions):
        self.assertEqual(7, len(week_actions))
        self.assertFalse(week_actions[0])
        self.assertFalse(week_actions[1])
        self.assertFalse(week_actions[2])

        self.assertTrue(week_actions[3])
        self.assertEqual(week_actions[3].action_date, datetime(2019, 5, 30).date())

        self.assertFalse(week_actions[4])
        self.assertFalse(week_actions[5])
        self.assertFalse(week_actions[6])
