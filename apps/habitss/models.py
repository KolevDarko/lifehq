
import datetime
from collections import OrderedDict

from dateutil.parser import parse
from django.db import models
from django.db.models import F

from apps.base.models import Profile
from apps.common.models import HashedModel
from mastermind.utils import user_time_now, calc_week_start


class HabitStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    ALL = [ACTIVE, INACTIVE]


class HabitActionStatus:

    EMPTY = "0"
    YES = "1"
    HALF = "2"
    NO = "3"

    ALL = [EMPTY, YES, HALF, NO]


class HabitParent(HashedModel):
    name = models.CharField(max_length=200)


class Habit(HashedModel):
    name = models.CharField(max_length=200)
    status = models.CharField(max_length=10)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    habit_parent = models.ForeignKey(HabitParent, null=True, blank=True, on_delete=models.SET_NULL)
    schedule = models.CharField(max_length=10, default="1111111")

    def create_week_actions(self, profile_utc_offset=None, _week_start=None, past_action_default=None):
        """
        :param profile_utc_offset: if there is _week_start and not past_action_default this is not necessary
        :param _week_start: when the week starts for the user
        :param past_action_default: Should it fill past days
        :return:
        """
        new_actions = list()
        action_map = {
            0: HabitActionStatus.YES,
            1: HabitActionStatus.HALF,
            2: HabitActionStatus.NO,
        }
        if not _week_start:
            week_start = calc_week_start(profile_utc_offset)
        else:
            week_start = _week_start

        today = None
        if past_action_default:
            today = user_time_now(profile_utc_offset).date()

        toggle = 0
        for i in self.schedule:
            if past_action_default:
                if week_start < today:
                    status_index = toggle % 3
                    h_action = HabitAction.objects.create(habit=self, action_date=week_start, status=action_map[status_index])
                    toggle += 1
                elif week_start == today:
                    h_action = HabitAction.objects.create(habit=self, action_date=week_start, status=HabitActionStatus.YES)
                else:
                    h_action = HabitAction.objects.create(habit=self, action_date=week_start)
            else:
                if i == "1":
                    h_action = HabitAction.objects.create(habit=self, action_date=week_start)
                else:
                    h_action = None

            week_start += datetime.timedelta(days=1)
            if h_action:
                new_actions.append(h_action)
        return new_actions

    @staticmethod
    def create_habit_with_actions(profile, habit_name, past_action_default=False):
        new_habit = Habit(user=profile, name=habit_name, status=HabitStatus.ACTIVE)
        new_habit.save()
        new_habit.create_week_actions(profile_utc_offset=profile.utc_offset, past_action_default=past_action_default)

    @staticmethod
    def empty_stats(light):
        stats = {}
        if light:
            days = ["M", "T", "W", "T", "F", "S", "S"]
            spacing_coef = 35
        else:
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            spacing_coef = 80
        i = 0
        for day in days:
            score = 0
            stats[i] = {
                "height": score * 100 + 10,
                "score_height": score * 100 + 50,
                "left": i * spacing_coef,
                "day": day,
                "score": int(score * 100),
                "color": "indianred"
            }
            i += 1
        return stats

    @staticmethod
    def calc_stats(h_actions, profile, light=False):
        sums = {}
        counters = {}
        today_date = user_time_now(profile.utc_offset).date()
        today_key = today_date.isoformat()
        if not len(h_actions):
            return Habit.empty_stats(light), 0, 0

        for action in h_actions:
            date_key = action.action_date.isoformat()
            if date_key not in counters:
                sums[date_key] = 0
                counters[date_key] = 0
            if action.status == HabitActionStatus.YES:
                sums[date_key] += 1
            elif action.status == HabitActionStatus.HALF:
                sums[date_key] += 0.5
            counters[date_key] += 1
        stats = OrderedDict()
        if light:
            days = ["M", "T", "W", "T", "F", "S", "S"]
            spacing_coef = 35
        else:
            days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            spacing_coef = 80
        i = 0
        today_score = 0
        week_score_sum = 0
        week_score_count = 0
        sorted_keys = list(counters.keys())
        sorted_keys.sort()
        today = datetime.datetime.today().date()
        for key in sorted_keys:
            count = counters[key]
            score = sums[key] / count
            stats[key] = {
                "height": score * 100 + 10,
                "score_height": score * 100 + 50,
                "left": i * spacing_coef,
                "day": days[i],
                "score": int(score * 100),
                "iso_date": key
            }
            if key == today_key:
                today_score = score
                before_today = False
                stats[key]["today"] = True
            key_date = parse(key).date()
            if key_date <= today:
                week_score_sum += score
                week_score_count += 1

            i += 1
            if score < .2:
                color = "indianred"
            elif score <= .5:
                color = "orange"
            elif score <= .75:
                color = "lightgreen"
            else:
                color = "green"
            stats[key]["color"] = color
        if week_score_count == 0:
            week_score = 0
        else:
            week_score = week_score_sum / week_score_count
        return stats, today_score, week_score

class HabitAction(HashedModel):
    action_date = models.DateField()
    status = models.CharField(max_length=10, default=HabitActionStatus.EMPTY)
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE, related_name="actions")

    @classmethod
    def get_habits_today(cls, date_now, profile):
        todays_actions = cls.objects.filter(action_date=date_now, habit__user=profile)
        finished = []
        not_finished = []
        for action in todays_actions:
            if action.status in [HabitActionStatus.EMPTY, HabitActionStatus.NO]:
                not_finished.append(action.habit)
            else:
                finished.append(action.habit)

        return finished, not_finished

    @classmethod
    def get_habit_actions_by_date_by_profile(cls, action_date, profile):
        todays_actions = cls.objects.filter(action_date=action_date, habit__user=profile)
        finished = []
        not_finished = []
        for action in todays_actions:
            if action.status in [HabitActionStatus.EMPTY, HabitActionStatus.NO]:
                not_finished.append(action)
            else:
                finished.append(action)

        return finished, not_finished

    @classmethod
    def get_active_with_habit_name(cls, profile, today):
        return HabitAction.objects.filter(habit__user=profile,
                                                   habit__status=HabitStatus.ACTIVE, action_date=today).annotate(habit_name=F('habit__name'))

