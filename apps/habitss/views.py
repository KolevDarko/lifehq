import json

import datetime
import logging

from django.shortcuts import render, redirect
from django.views import View

from apps.base.views import CustomLoginRequiredMixin
from apps.common.analytics_client import AnalyticsManager, HABIT, HABIT_ACTION
from apps.habitss.models import Habit, HabitStatus, HabitAction, HabitActionStatus
from mastermind.utils import calc_week_start, user_time_now, SHORT_DATE_FORMAT

from apps.common.views import MyJsonResponse
JsonResponse = MyJsonResponse

logger = logging.getLogger('django')


class HabitStruct:

    def __init__(self, habit=None, action_list=None):
        self.habit = habit
        self.action_list = self.fill_actions(action_list)
        self.name_len = len(self.habit.name)

    @staticmethod
    def fill_actions(action_list):
        week_actions = []
        a_i = 0
        i = 0
        if len(action_list) == 0:
            return week_actions
        while i < 7:
            try:
                action = action_list[a_i]
                while action.action_date.weekday() > i:
                    i += 1
                    week_actions.append(False)
                week_actions.append(action)
                a_i += 1
            except IndexError:
                week_actions.append(False)
            i += 1
        return week_actions

    def to_json(self):
        return {
            'habit': {
                'id': self.habit.id,
                'name': self.habit.name,
                'schedule': self.habit.schedule
            },
            'action_list': [self.action_json(ac) for ac in self.action_list]
        }

    def action_json(self, habit_action):
        if habit_action:
            return {'id': habit_action.id}
        else:
            return {'id': None}

class HabitsHome(CustomLoginRequiredMixin, View):

    def calc_day_data(self, week_start):
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        results = list()
        for day_name in names:
            elem = {
                'name': day_name,
                'shortDate': week_start.strftime(SHORT_DATE_FORMAT)
            }
            results.append(elem)
            week_start = week_start + datetime.timedelta(days=1)
        return results

    def create_all_week_actions(self, active_habits, str_offset):
        week_start = calc_week_start(str_offset)
        for habit in active_habits:
            habit.create_week_actions(_week_start=week_start)

    @staticmethod
    def group_habit_data(active_habits, active_actions):
        """
        Returns list of Habit struct objects
        """
        grouped = {}
        for h_action in active_actions:
            if h_action.habit_id not in grouped:
                grouped[h_action.habit_id] = []
            grouped[h_action.habit_id].append(h_action)
        results = []
        for habit in active_habits:
            h_struct = HabitStruct(habit=habit, action_list=grouped[habit.id])
            results.append(h_struct)
        return results

    def get(self, request):
        profile = self.profile(request)
        user_habits = Habit.objects.filter(user=self.profile(request), status=HabitStatus.ACTIVE).order_by('id').all()
        week_start = calc_week_start(profile.utc_offset)
        habit_actions = HabitAction.objects.filter(habit__user=profile,
                                                   habit__status=HabitStatus.ACTIVE, action_date__gte=week_start).order_by('action_date')
        if not habit_actions.count():
            self.create_all_week_actions(user_habits, profile.utc_offset)
            habit_actions = HabitAction.objects.filter(habit__user=profile,
                                                       habit__status=HabitStatus.ACTIVE,
                                                       action_date__gte=week_start).order_by('action_date')

        habit_structs = self.group_habit_data(user_habits, habit_actions)
        success_stats, today_score, week_score = Habit.calc_stats(habit_actions, profile)
        day_data = self.calc_day_data(week_start)
        today = self.profile_today
        first_habit = ""
        if profile.first_habit:
            first_habit = "true"
            profile.first_habit = False
            profile.save()
        week_score *= 100
        today_score *= 100

        if week_score <= 50:
            habit_advice = "Week score below 50%, push yourself to keep up or cancel your least important habit"
            advice_class = "text-danger"
        elif week_score < 90:
            habit_advice = "You are doing great, keep it up"
            advice_class = "text-info"
        else:
            habit_advice = "Success rate over 90%. Congrats!!!. When you feel ready, archive one of your most successful habits and replace it with new one."
            advice_class = "text-success"

        all_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        return render(request, "habitss/habits_home.html", {'habit_structs': habit_structs,
                                                            'stats': success_stats, 'today_score': today_score,
                                                            'week_score': week_score, 'day_data': day_data,
                                                            'active_consistency': True, 'today': today,
                                                            'first_habit': first_habit, 'habit_advice': habit_advice,
                                                            'advice_class': advice_class, 'schedule_days': all_days})


class HabitsReset(CustomLoginRequiredMixin, View):

    def post(self, request):
        active_habits = Habit.objects.filter(user=self.profile(request), status=HabitStatus.ACTIVE).all()
        profile = self.profile(request)
        week_start = calc_week_start(profile.utc_offset)
        for habit in active_habits:
            habit.create_week_actions(_week_start=week_start)
        return redirect('habits-home')


class HabitView(CustomLoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body.decode())
        habit_name = data['name']
        habit_schedule = data['schedule']
        profile = self.profile(request)
        new_habit = Habit(user=profile, name=habit_name, status=HabitStatus.ACTIVE, schedule=habit_schedule)
        new_habit.save()
        new_actions = new_habit.create_week_actions(profile_utc_offset=self.my_profile.utc_offset)
        self.update_daily_success('habits', todo=1)
        AnalyticsManager.record(self.user_id, HABIT)
        today = self.profile_today
        weekday = today.isoweekday()
        habit_struct = HabitStruct(new_habit, new_actions)
        return JsonResponse({'weekday': weekday, 'habit_struct': habit_struct.to_json()})

    def put(self, request):
        data = json.loads(request.body.decode())
        new_name = data['name']
        habit_id = data['id']
        new_schedule = data['schedule']
        habit = Habit.objects.get(user=self.profile(request), id=habit_id)
        habit.name = new_name
        new_actions = []
        if habit.schedule != new_schedule:
            self.clear_old_actions(habit)
            habit.schedule = new_schedule
            new_actions = habit.create_week_actions(profile_utc_offset=self.my_profile.utc_offset)
        habit.save()
        habit_struct = HabitStruct(habit, new_actions)
        weekday = self.profile_today.isoweekday()
        return JsonResponse({'weekday': weekday, 'habit_struct': habit_struct.to_json()})

    def clear_old_actions(self, habit):
        week_start = calc_week_start(self.my_profile.utc_offset)
        deleted_actions = habit.actions.filter(action_date__gte=week_start).delete()
        logger.info("Removed {} actions".format(deleted_actions))

    def delete(self, request):
        body = json.loads(request.body.decode())
        habit_id = body['id']
        Habit.objects.filter(user=self.profile(request), id=habit_id).update(status=HabitStatus.INACTIVE)
        self.update_daily_success('habits', todo=-1)
        return JsonResponse({'success': True})

class HabitActionView(CustomLoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body.decode())
        action_id = data['actionId']
        new_status = data['status']
        habit_action = HabitAction.objects.get(pk=action_id)
        habit_action.status = new_status
        habit_action.save()
        if habit_action.action_date == self.profile_today:
            self.update_habits_success(new_status)
        AnalyticsManager.record(self.user_id, HABIT_ACTION)
        return JsonResponse({'success': True})

    def update_habits_success(self, new_status):
        if str(new_status) == HabitActionStatus.YES:
            self.update_daily_success('habits', done=1)
        elif str(new_status) == HabitActionStatus.HALF:
            self.update_daily_success('habits', done=-0.5)
        elif str(new_status) == HabitActionStatus.NO:
            self.update_daily_success('habits', done=-0.5)
