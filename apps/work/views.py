from dateutil.parser import parse
from django.shortcuts import render

# Create your views here.
from django.template.loader import render_to_string
from django.views import View

from apps.base.models import ProjectTodoItem, WorkCycleGroup
from apps.base.views import CustomLoginRequiredMixin, JsonResponse
from apps.work.models import TrackWorkedDay
from mastermind.utils import calc_week_start


class TrackTodoItemManual(CustomLoginRequiredMixin, View):

    def post(self, request, item_id):
        data = self.parse_json_body()
        minutes_worked = int(data['manualMinutes'])
        hours_worked = int(data['manualHours'])
        total_minutes = minutes_worked + 60 * hours_worked
        manual_date = parse(data['manualDate']).date()
        project_id = data['manualProjectId'] or None
        task_list_id = data['manualTaskListId'] or None
        if manual_date == self.profile_today:
            ProjectTodoItem.update_minutes_worked(item_id, total_minutes)
        else:
            if project_id == '0':
                TrackWorkedDay.add_manual(self.my_profile.id, item_id, manual_date, total_minutes)
            else:
                TrackWorkedDay.add_manual(self.my_profile.id, item_id, manual_date, total_minutes, project_id, task_list_id)
        ProjectTodoItem.set_in_progress(item_id)
        return JsonResponse({})


class TrackTodoItem(CustomLoginRequiredMixin, View):

    def post(self, request, item_id):
        data = self.parse_json_body()
        minutes_worked = data['minutes_worked']
        ProjectTodoItem.update_minutes_worked(item_id, minutes_worked)
        return JsonResponse({})

    def put(self, request, item_id):
        data = self.parse_json_body()
        track_minutes = int(data['trackMinutes'])
        track_hours = int(data['trackHours'])
        total_minutes = track_minutes + 60 * track_hours
        track_date = parse(data['trackDate']).date()
        project_id = data.get('projectId', None)
        if project_id == '0':
            project_id = None

        if track_date == self.profile_today:
            ProjectTodoItem.update_minutes_worked(item_id, total_minutes)
        else:
            TrackWorkedDay.update_track(self.my_profile.id, project_id, item_id, track_date, total_minutes)
        return JsonResponse({})


class PersonalTasks(CustomLoginRequiredMixin, View):

    def get(self, request):
        profile = self.my_profile
        week_start = calc_week_start(profile.utc_offset)
        personal_tasks = ProjectTodoItem.get_personal_tasks_for_stats(profile, week_start)
        results = [task.to_dict() for task in personal_tasks]
        return JsonResponse({'tasks': results})


class PomodoroSetupPartial(CustomLoginRequiredMixin, View):

    def past_sessions(self, groups):
        results = []
        for g in groups:
            shortName = g.question_what[:30]
            item = {
                'id': g.id,
                'name': "{}-{}".format(shortName, g.created_at.strftime("%b %d, %-I%p"))
            }
            results.append(item)
        return results

    def prepare_context(self):
        profile = self.my_profile
        groups = WorkCycleGroup.get_past_sessions(profile)
        pastSessions = self.past_sessions(groups)
        return {'my_user': profile, 'pastSessions': pastSessions}

    def get(self, request):
        ctx = self.prepare_context()
        card_html = render_to_string('work/partials/pomodoro-setup-card.html', ctx)
        return JsonResponse({'content': card_html})
