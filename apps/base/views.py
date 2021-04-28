"""Views for the base app"""
import datetime
import json
import random
from collections import namedtuple
import account.forms
import account.views
import requests
from account.conf import settings
from account.mixins import LoginRequiredMixin
from account.models import Account
from account.signals import user_signed_up, email_confirmed
from dateutil.parser import parse
from django import urls
from django.contrib import messages
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.db import IntegrityError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render as django_render
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from apps.base import forms
from apps.base.models import Project, ProjectPage, Profile, ProjectEvent, ProjectTodoItem, ProjectTodoList, \
    PersonalTodoList, ProjectLog, ProjectPageImage, SignupToken, ProjectTag, WorkCycleGroup, \
    WorkCycle, ProjectResource, PaymentEvent, OnboardEvents, ProjectTodoItemState
from apps.common.analytics_client import AnalyticsManager, PROJECT, PROJECT_TODO_LIST, PROJECT_TASK, MASTER_TASK, \
    POMODORO_SESSION, POMODORO_CYCLE, PAYMENTS
from apps.common.constants import EMAIL_FROM
from apps.common.views import MyJsonResponse
from apps.habitss.models import HabitAction, Habit, HabitActionStatus
from apps.journal.models import Journal, JournalEntry, JournalTemplate
from apps.notebooks.models import Notebook, NoteTemplate, Note, DefaultNoteTemplate
from apps.work.models import TrackWorkedDay
from mastermind import utils
from mastermind.settings.base import GOOGLE_CAPTCHA_SECRET
from mastermind.utils import calc_week_start, user_time_now, HUMAN_FORMAT, calc_month_start, calc_week_range, \
    SHORT_DATE_FORMAT


def render(request, template_name, context=None):
    if not context:
        context = {}
    for field in ['active_home', 'active_journal', 'active_projects', 'active_today', 'active_consistency',
                  'active_knowledge']:
        if field not in context:
            context[field] = ""

    return django_render(request, template_name, context)


BETA_TOKEN = 'beta-token'

import logging

logger = logging.getLogger('django')

JsonResponse = MyJsonResponse



def copy_journal_templates(new_journal):
    try:
        template_user = Profile.get_template_user()
    except Profile.DoesNotExist:
        JournalTemplate.empty_templates(new_journal)
        return
    template_journal = Journal.objects.get(user=template_user)
    JournalTemplate.copy_templates(template_journal, new_journal)


def create_journal_entries(new_journal):
    JournalEntry.create_from_template('day', new_journal.id)
    JournalEntry.create_from_template('week', new_journal.id)
    JournalEntry.create_from_template('month', new_journal.id)
    JournalEntry.create_from_template('year', new_journal.id)


def create_journal(profile):
    new_journal = Journal(user=profile)
    new_journal.save()
    copy_journal_templates(new_journal)
    create_journal_entries(new_journal)


def create_day_lists(profile):
    PersonalTodoList.objects.create(title="Monday", user_id=profile.id, priority=PersonalTodoList.DAY_LIST_PRIORITY)
    PersonalTodoList.objects.create(title="Tuesday", user_id=profile.id, priority=PersonalTodoList.DAY_LIST_PRIORITY)
    PersonalTodoList.objects.create(title="Wednesday", user_id=profile.id, priority=PersonalTodoList.DAY_LIST_PRIORITY)
    PersonalTodoList.objects.create(title="Thursday", user_id=profile.id, priority=PersonalTodoList.DAY_LIST_PRIORITY)
    PersonalTodoList.objects.create(title="Friday", user_id=profile.id, priority=PersonalTodoList.DAY_LIST_PRIORITY)
    PersonalTodoList.objects.create(title="Saturday", user_id=profile.id, priority=PersonalTodoList.DAY_LIST_PRIORITY)
    PersonalTodoList.objects.create(title="Sunday", user_id=profile.id, priority=PersonalTodoList.DAY_LIST_PRIORITY)


def create_personal_lists(profile):
    primary = PersonalTodoList(title="Important", priority=1, user_id=profile.id)
    primary.save()
    secondary = PersonalTodoList(title="Urgent", priority=2, user_id=profile.id)
    secondary.save()
    other = PersonalTodoList(title="Extra", priority=3, user_id=profile.id)
    other.save()
    first_todo = ProjectTodoItem(personal_list=primary, title="Smart decision: Sign up at LifeHQ",
                                 personal_list_order=1, user_id=profile.id)
    first_todo.complete_now()
    second_todo = ProjectTodoItem(personal_list=primary, title="Set up my personal productivity system",
                                  personal_list_order=2, user_id=profile.id)
    second_todo.save()
    create_day_lists(profile)


def create_default_habit(profile):
    Habit.create_habit_with_actions(profile, 'Be Awesome', past_action_default=True)
    Habit.create_habit_with_actions(profile, 'Maintain high productivity', past_action_default=True)


def create_intro_project(profile):
    try:
        intro_project = Project.objects.get(project_type="template-intro")
    except Project.DoesNotExist:
        return
    one_week = datetime.datetime.today() + datetime.timedelta(days=7)
    new_project = Project(name=intro_project.name, description=intro_project.description,
                          deadline=one_week, user=profile)
    new_project.save()
    new_project.add_event(start_date=one_week, title="Deadline")

    intro_project.duplicate(new_project)


def create_default_note_templates(profile):
    for default_t in DefaultNoteTemplate.objects.all():
        my_template = NoteTemplate(title=default_t.title, content=default_t.content, user=profile)
        my_template.save()


def create_onboarding_record(profile):
    OnboardEvents.objects.create(user=profile)


def create_default_data(profile):
    create_default_habit(profile)
    create_intro_project(profile)
    create_personal_lists(profile)
    create_default_note_templates(profile)
    create_journal(profile)
    create_onboarding_record(profile)
    profile.has_default_data = True
    profile.save()


def create_profile_with_trial(account, profile_name):
    trial_start = datetime.datetime.utcnow().date()
    trial_end = trial_start + datetime.timedelta(days=Profile.TRIAL_DURATION)
    profile = Profile(name=profile_name, account=account,
                      trial_start_time=trial_start,
                      trial_end_time=trial_end)
    profile.save()


def create_profile_after_signup(sender, **kwargs):
    profile_name = kwargs['form'].data['name']
    try:
        create_profile_with_trial(kwargs['user'].account, profile_name)
    except IntegrityError:
        return


def create_default_data_after_email_confirmation(sender, **kwargs):
    user_email = kwargs['email_address'].email
    user = User.objects.get(email=user_email)
    profile = user.account.profile
    if not profile.has_default_data:
        create_default_data(profile)


user_signed_up.connect(create_profile_after_signup)
email_confirmed.connect(create_default_data_after_email_confirmation)


def create_profile_with_data(account, name, beta_token=''):
    trial_start = datetime.datetime.utcnow().date()
    trial_end = trial_start + datetime.timedelta(days=Profile.TRIAL_DURATION)
    profile = Profile(name=name, account=account, beta_token=beta_token,
                      trial_start_time=trial_start,
                      trial_end_time=trial_end)
    profile.save()
    create_default_data(profile)


def create_account_profile(*args, **kwargs):
    user = kwargs['user']
    if not hasattr(user, 'account'):
        user.account = Account.create(user=user, create_email=False)
    if not hasattr(user.account, 'profile'):
        profile_name = user.username
        if BETA_TOKEN in kwargs['request'].session:
            create_profile_with_data(user.account, profile_name, beta_token=kwargs['request'].session[BETA_TOKEN])
        else:
            create_profile_with_data(user.account, profile_name)


class CustomLoginRequiredMixin(LoginRequiredMixin):

    @staticmethod
    def profile(request):
        return request.user.account.profile

    def parse_json_body(self):
        return json.loads(self.request.body.decode("utf-8"))

    def update_daily_success(self, task_type='work', todo=0, done=0):
        if not self.request.session.get('success_data'):
            return
        all_success_data = self.request.session['success_data']
        data = all_success_data[task_type]
        if todo != 0:
            data['todo'] += todo
        else:
            data['done'] += done
        if data['todo'] == 0:
            score = 0
        else:
            score = round((data['done'] / data['todo'] * 100), 2)
        rev_score = 100 - score
        data['score'] = score
        data['rev_score'] = rev_score
        total_score, rev_total_score = self.recalc_total_score(all_success_data)
        all_success_data['total_score'] = total_score
        all_success_data['rev_total_score'] = rev_total_score
        self.request.session['success_data'] = all_success_data

    def recalc_total_score(self, all_success_data):
        all_scores = [all_success_data['work']['score'], all_success_data['habits']['score'],
                      all_success_data['journals']['score']]
        total = sum(all_scores)
        avg_score = round((total / len(all_scores)), 2)
        rev_avg_score = 100 - avg_score
        return avg_score, rev_avg_score

    @property
    def my_profile(self):
        return self.request.user.account.profile

    @property
    def user_email(self):
        return self.request.user.email

    @property
    def user_id(self):
        return self.request.user.id

    @property
    def profile_today(self):
        return user_time_now(self.my_profile.utc_offset).date()

    @property
    def profile_now(self):
        return user_time_now(self.my_profile.utc_offset)


ITEMS_HOMEPAGE_SECTION = 4


def profile(request):
    return request.user.account.profile


import logging

base_logger = logging.getLogger(__name__)


class DayStatsMixin:
    Score = namedtuple('Score', ['score', 'rev_score', 'todo', 'done'])

    Empty_100 = Score(score=100, rev_score=0, todo=0, done=0)

    @staticmethod
    def score_dict(score):
        return {
            'score': score.score,
            'rev_score': score.rev_score,
            'todo': score.todo,
            'done': score.done
        }

    @staticmethod
    def calc_journal_score(todays_journals):
        if todays_journals.count() == 0:
            return DayStatsMixin.Empty_100
        count_done = len([j for j in todays_journals if j.done])
        done = int((count_done / len(todays_journals)) * 100)
        return DayStatsMixin.Score(score=done, rev_score=(100 - done), todo=todays_journals.count(), done=count_done)

    @staticmethod
    def calc_habits_score(habit_actions):
        score = 0
        count = habit_actions.count()
        if not count:
            return DayStatsMixin.Empty_100
        for action in habit_actions:
            if action.status == HabitActionStatus.YES:
                score += 1
            elif action.status == HabitActionStatus.HALF:
                score += 0.5
        done = int((score / count) * 100)
        return DayStatsMixin.Score(score=done, rev_score=(100 - done), todo=count, done=score)

    @staticmethod
    def calc_task_score(todo_today, completed_today):
        # todo, archive completed from previous days and then get all of this in one query
        # the query will filter just by user, but will also check completed_on date here
        done_today = completed_today.count()
        total = todo_today.count() + done_today
        if total == 0:
            return DayStatsMixin.Empty_100
        perc_done = int((done_today / total) * 100)
        return DayStatsMixin.Score(score=perc_done, rev_score=(100 - perc_done), todo=total, done=done_today)


class DaySuccessDetails(CustomLoginRequiredMixin, DayStatsMixin, View):

    def get(self, request):
        journals_score = self.get_journal_score()
        habits_score = self.get_habit_score()
        work_score = self.get_work_score()
        all_scores = [journals_score.score, habits_score.score, work_score.score]
        total = sum(all_scores)
        avg_score = round((total / len(all_scores)), 2)
        rev_avg_score = 100 - avg_score
        success_data = {
            'total_score': avg_score,
            'rev_total_score': rev_avg_score,
            'journals': self.score_dict(journals_score),
            'habits': self.score_dict(habits_score),
            'work': self.score_dict(work_score),
            'valid': True,
            'date': self.profile_today.isoformat()
        }
        request.session['success_data'] = success_data
        return JsonResponse(success_data)

    def get_journal_score(self):
        user_journal = Journal.get_user_journal(self.my_profile)
        todays = user_journal.get_todays(self.profile_today)
        journal_score = self.calc_journal_score(todays)
        return journal_score

    def get_work_score(self):
        todo_today, completed_today = ProjectTodoItem.personal_todos_today(self.my_profile, self.profile_today)
        work_score = self.calc_task_score(todo_today, completed_today)
        return work_score

    def get_habit_score(self):
        habit_actions = HabitAction.get_active_with_habit_name(self.my_profile, self.profile_today)
        habit_score = self.calc_habits_score(habit_actions)
        return habit_score


class HomeView(CustomLoginRequiredMixin, DayStatsMixin, View):

    def habit_actions_today(self):
        profile = self.my_profile
        user_today = user_time_now(profile.utc_offset)
        return HabitAction.get_active_with_habit_name(profile, user_today)

    def full_journal_info(self, journal):
        user_today = user_time_now(self.my_profile.utc_offset).date()
        logger.info("Getting user journals for {}".format(user_today.isoformat()))
        towrite_journals = journal.get_todays(user_today)
        review_journals = journal.get_last_for_review()
        journal_score = self.calc_journal_score(towrite_journals)
        return towrite_journals, review_journals, journal_score

    def get(self, request):
        profile = request.user.account.profile
        FIRST_LOGIN = ""

        all_projects = Project.objects.filter(user=profile)

        user_journal = Journal.objects.get(user=profile)
        towrite_journals, review_journals, journal_score = self.full_journal_info(user_journal)

        total_notebooks = Notebook.objects.filter(user=profile).count()
        total_notes = Note.objects.filter(notebook__user=profile).count()

        recent_notes = Note.objects.filter(notebook__user=profile).order_by("-updated_on")[:3]
        notes_classes = {
            0: 'col-md-12',
            1: 'col-md-12',
            2: 'col-md-6',
            3: 'col-md-4'
        }
        recent_notes_class = notes_classes[len(recent_notes)]

        profiles_today = user_time_now(profile.utc_offset).date()
        todo_today, completed_today = ProjectTodoItem.personal_todos_today(profile, profiles_today)
        task_score = self.calc_task_score(todo_today, completed_today)

        home_tasks = todo_today[:3]
        remaining_tasks = todo_today.count() - 3
        total_todos = todo_today.count()
        habit_actions = self.habit_actions_today()
        if not habit_actions.count():
            habits_are_empty = True
            habits_to_show = []
        else:
            habits_are_empty = False
            habits_to_show = habit_actions[:6]

        habit_score = self.calc_habits_score(habit_actions)
        user_tags = ProjectTag.user_tags(self.profile(request))

        done_today = None
        if profile.first_login:
            FIRST_LOGIN = "true"
            profile.first_login = False
            done_today = completed_today.first()
            profile.save()

        return render(request, 'base/home.html',
                      {'projects': all_projects, 'towrite_journals': towrite_journals,
                       'review_journals': review_journals,
                       'total_notebooks': total_notebooks, 'total_notes': total_notes, 'recent_notes': recent_notes,
                       'home_tasks': home_tasks, 'habit_actions': habits_to_show, 'habit_score': habit_score.score,
                       'active_home': True, 'habits_are_empty': habits_are_empty, 'journal_score': journal_score.score,
                       "first_login": FIRST_LOGIN, 'recent_notes_class': recent_notes_class, 'tags': user_tags,
                       'rev_habit_score': habit_score.rev_score, 'rev_journal_score': journal_score.rev_score,
                       'task_score': task_score.score, 'rev_task_score': task_score.rev_score,
                       'remaining_tasks': remaining_tasks,
                       'total_todos': total_todos, 'done_today': done_today})


class LoginView(account.views.LoginView):
    form_class = account.forms.LoginEmailForm

    def valid_token_in_url(self, full_url):
        try:
            parts = full_url.split("?")
            if len(parts) >= 2:
                params = parts[1].split("=")
                if len(params) == 2 and params[0] == 'token':
                    token = params[1]
                    try:
                        signup_obj = SignupToken.objects.get(token=token)
                        if signup_obj.valid:
                            return True
                        else:
                            return False
                    except SignupToken.DoesNotExist:
                        return False
                else:
                    return False
        except Exception:
            return False


class TokenWall(View):

    def get(self, request):
        return render(request, "base/token_wall.html", {})

    def post(self, request):
        signup_token = request.POST.get("token")
        next = request.GET.get("next")
        try:
            signup_obj = SignupToken.objects.get(token=signup_token)
            if signup_obj.valid:
                request.session[BETA_TOKEN] = signup_token
                if next == 'login':
                    the_url = urls.reverse('account_login')
                    full_url = "{}?token={}".format(the_url, signup_token)
                    return redirect(full_url)
                else:
                    the_url = urls.reverse('account_signup')
                    full_url = "{}?token={}".format(the_url, signup_token)
                    return redirect(full_url)
            else:
                return render(request, "base/token_wall.html", {'invalid_code': True})
        except SignupToken.DoesNotExist:
            return render(request, "base/token_wall.html", {'invalid_code': True})


class PrivacyPolicy(View):
    def get(self, request):
        return redirect("http://lifehqapp.com/Privacy_Policy.html")


class SignupView(account.views.SignupView):
    form_class = forms.SignupForm

    def token_wall(self):
        return redirect('validate-token')

    def valid_token_in_url(self, full_url):
        try:
            parts = full_url.split("?")
            if len(parts) >= 2:
                params = parts[1].split("=")
                if len(params) == 2 and params[0] == 'token':
                    token = params[1]
                    try:
                        signup_obj = SignupToken.objects.get(token=token)
                        if signup_obj.valid:
                            return True
                        else:
                            return False
                    except SignupToken.DoesNotExist:
                        return False
                else:
                    return False
        except Exception:
            return False

    # todo, only for private beta
    # def get(self, *args, **kwargs):
    #     request = args[0]
    #     signup_token = request.GET.get('token')
    #     if request.session.get(BETA_TOKEN):
    #         return super(SignupView, self).get(*args, **kwargs)
    #     if signup_token:
    #         try:
    #             signup_obj = SignupToken.objects.get(token=signup_token)
    #             if signup_obj.valid:
    #                 return super(SignupView, self).get(*args, **kwargs)
    #             else:
    #                 return self.token_wall()
    #         except SignupToken.DoesNotExist:
    #             return self.token_wall()
    #     elif request.META.get('HTTP_REFERER'):
    #         referrer = request.META.get('HTTP_REFERER')
    #         if self.valid_token_in_url(referrer):
    #             return super(SignupView, self).get(*args, **kwargs)
    #         else:
    #             return self.token_wall()
    #     else:
    #         return self.token_wall()

    def check_recaptcha(self, value):
        logger.info("Got recaptcha value {}".format(value))
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        api_secret = GOOGLE_CAPTCHA_SECRET
        data = {
            'secret': api_secret,
            'response': value
        }
        response = requests.post(verify_url, data=data)
        response = response.json()
        logger.info(response)
        if response['success'] == True and response['hostname'] == settings.MY_HOSTNAME:
            return True
        else:
            return False

    def post(self, request, **kwargs):
        logger.info("we are doing register")
        if request.user.is_authenticated:
            raise Http404()
        if not self.is_open():
            return self.closed()
        recaptcha_valid = self.check_recaptcha(request.POST.get('g-recaptcha-response'))
        form = self.get_form()
        # if form.is_valid() and recaptcha_valid:
        if form.is_valid():
            return self.form_valid(form)
        else:
            if not recaptcha_valid:
                form.add_error(None, "Invalid 'Not Robot field' Are you sure you're not a robot? ")
            return self.form_invalid(form)

    def create_user(self, form, commit=True, **kwargs):
        if BETA_TOKEN in self.request.session:
            form.cleaned_data[BETA_TOKEN] = self.request.session[BETA_TOKEN]
        form.cleaned_data['username'] = form.cleaned_data['email']
        return super(SignupView, self).create_user(form, commit=False, **kwargs)


class ConfirmEmailView(account.views.ConfirmEmailView):

    def get(self, *args, **kwargs):
        self.object = confirmation = self.get_object()
        confirmation.confirm()
        self.after_confirmation(confirmation)
        if settings.ACCOUNT_EMAIL_CONFIRMATION_AUTO_LOGIN:
            self.user = self.login_user(confirmation.email_address.user)
        else:
            self.user = self.request.user
        redirect_url = self.get_redirect_url()
        if not redirect_url:
            ctx = self.get_context_data()
            return self.render_to_response(ctx)
        if self.messages.get("email_confirmed"):
            messages.add_message(
                self.request,
                self.messages["email_confirmed"]["level"],
                "You have successfully confirmed your account at {}. You can now login with your credentials".format(
                    confirmation.email_address.email
                )
            )
        return redirect(redirect_url)


class ProjectLogView(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        profile = self.profile(request)
        action = data['action']
        if action == "start":
            project = Project.objects.get(pk=int(data['projectId']), user=profile)
            project.log_start = datetime.datetime.utcnow()
            project.save()
            profile.active_project_id = project.id
            profile.save()
        elif action == "end":
            project = Project.objects.get(pk=profile.active_project_id)
            project_log = ProjectLog(project=project, start=project.log_start, end=datetime.datetime.utcnow())
            project_log.save()
            profile.active_project_id = None
            profile.save()
        return JsonResponse({'success': True})


class Projects(CustomLoginRequiredMixin, View):

    def combined_resources(self, project):
        pages = project.pages.all()
        uploaded_resources = project.resources.all()
        all = list()
        all.extend([p for p in pages])
        all.extend([u for u in uploaded_resources])
        all.sort(key=lambda obj: obj.updated_on)
        return all

    def get(self, request, project_id=None):
        profile = self.profile(request)
        if project_id:
            project = Project.objects.get(pk=project_id, user=profile)
            todo_lists = []
            for db_list in project.todo_lists.filter(archived=False).order_by("id")[:5]:
                list_struct = TodoListStruct(db_list)
                todo_lists.append(list_struct)
            events = project.events.filter(start__gte=datetime.datetime.now())[:3]
            first_project = ""
            if profile.first_project:
                first_project = "true"
                profile.first_project = False
                profile.save()

            this_project_tags = []
            for tag in project.project_tags.all():
                this_project_tags.append(tag.name)
            tags_joined = ",".join(this_project_tags)
            # upload_form = forms.ProjectResourceForm()
            # resources = self.combined_resources(project)
            # human_quota = utils.bytes_to_human(profile.total_upload_quota)
            return render(request, "base/project_view.html", {"project": project, 'todo_lists': todo_lists,
                                                              'events': events, 'active_projects': True,
                                                              'first_project': first_project, 'tagsJoined': tags_joined,
                                                              'sortOptions': ProjectResource.SORT_CRITERIA,
                                                              })
        else:
            all_projects = Project.objects.filter(user=self.profile(request))
            user_tags = ProjectTag.user_tags(self.profile(request))
            return render(request, "base/project_list.html",
                          {'projects': all_projects, 'active_projects': True, 'tags': list(user_tags)})

    def put(self, request, project_id):
        data = json.loads(request.body.decode())
        project = Project.objects.get(pk=project_id, user=self.profile(request))
        if 'projectName' in data:
            name = data.get('projectName')
            project.name = name
        if 'projectDeadlineEnabled' in data:
            if data['projectDeadlineEnabled'] == 'on':
                if 'projectDeadline' in data:
                    deadline = parse(data['projectDeadline'])
                    project.deadline = deadline
        else:
            project.deadline = None
        if 'timeTargetVal' in data:
            time_target_val = float(data['timeTargetVal'])
            time_target_type = data['timeTargetName']
            project.time_target_duration = time_target_val
            project.time_target_type = time_target_type
        project.save()
        return JsonResponse({'name': project.name, 'deadline': project.deadline})

    def post(self, request):
        name = request.POST['projectName']
        description = request.POST['projectDesc']
        raw_tags = request.POST['projectTags']
        profile = request.user.account.profile
        new_project = Project(name=name, description=description, user=profile)
        new_project.save()
        deadline_enabled = request.POST.get('deadlineEnabled', '')
        if deadline_enabled == 'on':
            deadline = request.POST['projectDeadline']
            deadline_date = parse(deadline)
            new_project.deadline = deadline_date
            new_project.save()
            new_project.add_event(start_date=deadline_date, title="Deadline")
            new_project.add_tags(raw_tags.split(' '))
        else:
            deadline = None
        AnalyticsManager.record(self.user_id, PROJECT)
        return redirect('project_view', new_project.id)

    def delete(self, request, project_id):
        project = Project.objects.get(pk=project_id, user=self.profile(request))
        if project:
            project.delete()
        return JsonResponse({})


class ProjectsTagFiltered(CustomLoginRequiredMixin, View):

    def get(self, request):
        tag_name = request.GET['tagName']
        if tag_name.lower() == "all":
            projects = Project.objects.filter(user=self.profile(request))
        else:
            all_project_tags = ProjectTag.objects.filter(name=tag_name, user=self.profile(request))
            projects = [t.project for t in all_project_tags]
        return render(request, "base/project_list_filtered.html", {'projects': projects})


class ProjectTagDelete(CustomLoginRequiredMixin, View):

    def post(self, request, project_id):
        data = json.loads(request.body.decode('utf-8'))
        tagName = data['tag']
        removed = ProjectTag.objects.filter(name=tagName, user=self.profile(request), project_id=project_id).delete()
        print(removed)
        return JsonResponse({'success': True})


class ProjectTagView(CustomLoginRequiredMixin, View):

    def post(self, request, project_id):
        data = json.loads(request.body.decode('utf-8'))
        if data.get('tag'):
            tagName = data['tag'].lower()
            try:
                ProjectTag.objects.create(name=tagName, user=self.profile(request), project_id=project_id)
            except IntegrityError:
                pass
        return JsonResponse({'success': True})


class ProjectPageImageView(CustomLoginRequiredMixin, View):
    MB2 = 2000000

    def create_db_image(self, image_file, profile_id, page_id):
        page = ProjectPage.objects.get(pk=page_id)
        db_image = ProjectPageImage()
        filename = utils.filename_for_storage(profile_id, image_file.name)
        image_file.name = filename
        db_image.image = image_file
        db_image.name = filename
        db_image.file_size = image_file.size
        db_image.page = page
        db_image.save()
        return db_image

    def post(self, request, project_id, page_id):
        image_file = request.FILES['file']
        profile = self.profile(request)

        if image_file.size >= self.MB2:
            error = "Image size must be lower than 2MB."
            return JsonResponse({"success": False, "error": error})
        if profile.upload_limit_exceeds(image_file.size):
            return JsonResponse({'success': False, 'error': "Upload limit of 1GB exceeded"})

        original_name = image_file.name
        profile.update_uploads_quota(image_file.size)
        db_image = self.create_db_image(image_file, profile.id, page_id)

        return JsonResponse({'url': db_image.image.url, 'id': db_image.id, 'name': original_name})

    def delete(self, request, project_id, page_id, image_id):
        db_image = ProjectPageImage.objects.get(page_id=page_id, id=image_id)
        db_image.delete()
        return HttpResponse('')


class ProjectPageHtmlView(CustomLoginRequiredMixin, View):

    def get(self, request, project_id):
        profile = self.profile(request)
        project = Project.get_personal_project(profile, project_id)
        return render(request, "base/partials/project_pages.html", {
            'project': project, 'pages': project.pages.all
        })


class ProjectPageView(CustomLoginRequiredMixin, View):
    funny_titles = [
        "Taking Over The World (Plan C)",
        "10 best ways to walk in circles",
        "Let's do all the things",
        "All our tips are belong to you"
    ]

    def get(self, request, project_id, page_id=None):
        project = Project.objects.get(pk=project_id)
        page = ProjectPage()
        example_page_title = random.choice(self.funny_titles)
        if page_id:
            page = ProjectPage.objects.get(pk=page_id)

        return render(request, 'base/page_view.html', {'project': project, 'page': page,
                                                       'example_page_title': example_page_title,
                                                       'active_projects': True})

    def post(self, request, project_id, page_id=None):
        project = Project.objects.get(pk=project_id, user=self.profile(request))
        if page_id:
            page = ProjectPage.objects.get(pk=page_id)
        else:
            page = ProjectPage()
        data = json.loads(request.body.decode('utf-8'))
        if 'title' in data:
            page.title = strip_tags(data['title'])
        if 'content' in data:
            page.content = data['content']
        page.project = project
        page.save()
        return JsonResponse({'id': page.id, 'title': page.title})

    def delete(self, request, project_id, page_id):
        page = ProjectPage.objects.get(pk=page_id)
        page.delete()
        return JsonResponse({})


class ProjectResourceHtmlView(CustomLoginRequiredMixin, View):

    def get(self, request, project_id):
        profile = self.profile(request)
        project = Project.get_personal_project(profile, project_id)
        return render(request, "base/partials/project_resources.html", {
            'storage_quota': utils.bytes_to_human(profile.total_upload_quota),
            'resources': project.resources.all()
        })


class ProjectResourceView(CustomLoginRequiredMixin, View):

    def extract_extension(self, filename):
        parts = filename.split('.')
        if len(parts) >= 2:
            return parts[-1]
        else:
            return ''

    def post(self, request, project_id, resource_id=None):
        project = Project.get_personal_project(self.profile(request), project_id)
        form = forms.ProjectResourceForm(request.POST, request.FILES)
        if form.is_valid():
            the_file = request.FILES['the_file']
            profile = self.profile(request)
            filesize_in_mb = utils.bytes_to_mb(the_file.size)

            if filesize_in_mb > ProjectResource.MAX_FILE_SIZE_MB:
                return JsonResponse({'error': "You can't upload files bigger than 20MB"})
            if profile.upload_limit_exceeds(the_file.size):
                return JsonResponse({'error': "Upload limit of 1GB exceeded."})

            original_name = the_file.name
            ts_now = int(datetime.datetime.utcnow().timestamp())
            filename = utils.filename_for_storage(profile.id, the_file.name, ts_now)
            the_file.name = filename
            resource = ProjectResource(the_file=the_file, display_name=original_name, name=filename,
                                       extension=self.extract_extension(filename), file_size=the_file.size,
                                       project_id=project_id)
            resource.save()
            total_quota = profile.update_uploads_quota(resource.file_size)
            response_dict = {
                'id': resource.id,
                'title': resource.get_title(),
                'quota': utils.bytes_to_human(total_quota),
                'file_url': resource.file_url,
                'description': resource.get_description()
            }
            return JsonResponse(response_dict)
        else:
            return JsonResponse({'error': form.errors})

    def get(self, request, project_id, resource_id=None):
        resource = ProjectResource.objects.get(project_id=project_id, id=resource_id)
        resource_dict = resource.to_dict()
        resource_dict['resIconElement'] = resource.get_description()
        return JsonResponse(resource_dict)

    def delete(self, request, project_id, resource_id):
        project = Project.get_personal_project(self.profile(request), project_id)
        resource = ProjectResource.objects.get(project=project, id=resource_id)
        resource_size = resource.file_size
        resource.delete()
        profile = self.profile(request)
        profile.update_uploads_quota(-resource_size)
        return JsonResponse({'success': True})


class ProjectResourceSorted(CustomLoginRequiredMixin, View):

    def sorted_resources(self, criteria, project_id):
        return ProjectResource.get_sorted(criteria, project_id=project_id)

    def get(self, request, project_id):
        project = Project.objects.get(user=self.profile(request), id=project_id)
        criteria = request.GET['sort']
        sorted_resources = self.sorted_resources(criteria, project.id)
        return render(request, "base/partials/project_resources.html",
                      {'resources': sorted_resources, 'project': project})


class ProjectPageSorted(CustomLoginRequiredMixin, View):

    def sorted_pages(self, criteria, project_id):
        return ProjectPage.get_sorted(criteria, project_id=project_id)

    def get(self, request, project_id):
        project = Project.objects.get(user=self.profile(request), id=project_id)
        criteria = request.GET['sort']
        sorted_pages = self.sorted_pages(criteria, project.id)
        return render(request, "base/partials/project_pages.html",
                      {'pages': sorted_pages, 'project': project})


class TodoListStruct:
    def __init__(self, todo_list=None, extras=None, completed_date_filter=None, personal_list=False, day_list=False,
                 no_completed=False):
        self.todo = list()
        self.done = list()
        if todo_list:
            self.id = todo_list.id
            self.title = todo_list.title
            self.extract_items(todo_list, completed_date_filter, personal_list, day_list=day_list,
                               no_completed=no_completed)
            self.priority = todo_list.priority
            self.extras = extras
            self.total_count = len(self.todo) + len(self.done)
            self.done_count = len(self.done)
            if self.total_count == 0:
                self.percent_done = 0
            else:
                self.percent_done = int((self.done_count / self.total_count) * 100)

    def extract_items(self, todo_list, completed_date_filter=None, personal_list=False, day_list=False,
                      no_completed=False):
        raw_todos = {}
        if personal_list:
            items_queryset = todo_list.personal_todos.all().order_by('personal_list_order')
        elif day_list:
            items_queryset = todo_list.day_todos.all().order_by('day_list_order')
        else:
            items_queryset = todo_list.todos.all().order_by('project_list_order')
        for item in items_queryset:
            if personal_list or day_list:
                if item.project_list:
                    item.project_list_id = item.project_list_id
                    item.project_id = item.project_list.project_id
                    item.project_name = item.project_list.project.name
                else:
                    item.project_list_id = ""

            if item.completed:
                if no_completed:
                    continue
                if completed_date_filter:
                    if item.completed_on.date() == completed_date_filter:
                        self.done.append(item)
                else:
                    self.done.append(item)
            else:
                self.todo.append(item)


class TodosArchivedPage(CustomLoginRequiredMixin, View):
    def get(self, request, project_id):
        project = Project.objects.get(pk=project_id, user=self.profile(request))
        all_lists = []
        for todo_list in project.todo_lists.filter(archived=True).order_by("-id"):
            list_struct = TodoListStruct(todo_list)
            all_lists.append(list_struct)
        return render(request, 'base/todos_archived_view.html',
                      {'project': project, 'all_todo_lists': all_lists, 'active_projects': True})


class ProjectKanbanItem(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        itemId = data['itemId']
        newKanbanStatus = data.get('newListId')
        todoItem = get_object_or_404(ProjectTodoItem, pk=itemId)
        todoItem.update_kanban_status(newKanbanStatus)
        return JsonResponse({})


class TodosKanbanPage(CustomLoginRequiredMixin, View):

    def get(self, request, project_id):
        project_states = ProjectTodoItemState.get_by_project(project_id)
        if not project_states:
            project_states = ProjectTodoItemState.create_defaults(project_id)
        self.tasks_status_grouped = ProjectTodoItem.status_grouped_by_project(project_id, project_states)
        all_kanban_lists = list()
        for project_todo_state in project_states:
            all_kanban_lists.append(self.create_struct(project_todo_state))
        kanban_list_count = len(all_kanban_lists)
        kanban_list_width = self.calc_list_width(kanban_list_count)
        project = Project.objects.get(pk=project_id, user=self.my_profile)
        return render(request, 'base/todos_kanban_view.html',
                      {'kanban_list_width': kanban_list_width, 'kanban_states_num': kanban_list_count, 'all_kanban_states': all_kanban_lists,
                       'project': project})


    @staticmethod
    def calc_list_width(list_count):
        return round(100 / list_count, 2)

    def create_struct(self, todo_item_state):
        list_struct = TodoListStruct()
        list_struct.title = todo_item_state.name
        list_struct.id = todo_item_state.item_state
        list_struct.extras = {'pk': todo_item_state.id}
        list_struct.todo = self.tasks_status_grouped[todo_item_state.item_state]
        return list_struct


class ProjectKanbanList(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        list_name = data['listName']
        lists_num = data['listsNum']
        project_id = data['projectId']
        if lists_num < 5:
            new_list_state = lists_num
            new_list = ProjectTodoItemState.create_new(project_id=project_id, list_state=new_list_state, name=list_name)
            response = JsonResponse({'success': True, 'list': {'id': new_list.id}})
        else:
            response = JsonResponse({'success': False, 'error': 'Kanban list limit reached'})
            response.status_code = 400
        return response

    def put(self, request):
        data = json.loads(request.body.decode('utf-8'))
        list_id = data['listId']
        new_name = data['name']
        ProjectTodoItemState.update_by_id(list_id, name=new_name)
        return JsonResponse({})


class TodosPage(CustomLoginRequiredMixin, View):
    def get(self, request, project_id):
        profile = self.profile(request)
        project = Project.objects.get(pk=project_id, user=profile)
        all_lists = []
        for todo_list in project.todo_lists.filter(archived=False).order_by("-id"):
            list_struct = TodoListStruct(todo_list)
            all_lists.append(list_struct)
        return render(request, 'base/todos_view.html',
                      {'project': project, 'all_todo_lists': all_lists, 'active_projects': True, 'my_user': profile})

    def post(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        todoList = ProjectTodoList()
        data = json.loads(request.body.decode('utf-8'))
        todoList.title = data['title']
        todoList.project = project
        todoList.save()
        AnalyticsManager.record(self.user_id, PROJECT_TODO_LIST)
        return JsonResponse({'success': True, 'listId': todoList.id})


class ProjectTodoItemView(CustomLoginRequiredMixin, View):

    def post(self, request, project_id, list_id):
        item = ProjectTodoItem()
        data = json.loads(request.body.decode('utf-8'))
        item.title = data['title']
        item.project_list_id = list_id
        item.project_list_order = data['index']
        item.user = self.my_profile
        item.save()
        AnalyticsManager.record(self.user_id, PROJECT_TASK)
        return JsonResponse({'success': True, 'item': item.to_dict(extras={'project_id': project_id})})


class CompleteTodoItem(CustomLoginRequiredMixin, View):
    def post(self, request, item_id):
        item = ProjectTodoItem.objects.get(pk=item_id)
        data = json.loads(request.body.decode('utf-8'))
        if data['completed']:
            item.complete_now(completed_time=self.profile_now)
        else:
            item.completed = False
            item.save()
        return JsonResponse({'success': True})


class ReorderTodoItemProject(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        itemId = data['itemId']
        newIndex = data.get('index')
        newListId = data.get('newListId')
        todoItem = get_object_or_404(ProjectTodoItem, pk=itemId)
        if newIndex:
            todoItem.project_list_order = newIndex
        if newListId:
            todoItem.project_list_id = newListId
        todoItem.save()
        return JsonResponse({})


class ReorderTodoItemMaster(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        itemId = data['itemId']
        newIndex = data['index']
        newListId = data['newListId']
        listType = data.get('listType')
        todoItem = get_object_or_404(ProjectTodoItem, pk=itemId)
        if newListId:
            if listType == 'day':
                newListDate = parse(newListId)
                todoItem.due_date = newListDate
            else:
                todoItem.personal_list_id = newListId
                todoItem.personal_list_order = newIndex
        todoItem.save()
        return JsonResponse({})


class DeleteProjectTodoItem(CustomLoginRequiredMixin, View):

    def delete(self, request, item_id):
        item = ProjectTodoItem.objects.get(pk=item_id)
        item.delete()
        return JsonResponse({'success': True})


class ProjectSchedulePage(CustomLoginRequiredMixin, View):
    def get(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        return render(request, 'base/schedule_view.html', {'project': project, 'active_projects': True})


class ReloadTodoList(CustomLoginRequiredMixin, View):
    def get(self, request, list_id):
        todo_list = ProjectTodoList.objects.get(pk=list_id)
        list_struct = TodoListStruct(todo_list)
        return render(request, 'base/partials/todo_list_partial.html', {'list_struct': list_struct})


class ReloadProjectTodoListsPreview(CustomLoginRequiredMixin, View):
    def get(self, request, project_id):
        project_list_structs = []
        try:
            project = Project.objects.get(pk=project_id)
            for project_list in project.todo_lists.filter(archived=False):
                project_list_structs.append(TodoListStruct(project_list))
        except Project.DoesNotExist:
            pass
        return render(request, 'base/partials/project_todo_lists_master.html',
                      {'project_lists': project_list_structs, })


class ReloadProjectTodoListsPreviewWeek(CustomLoginRequiredMixin, View):
    def get(self, request, project_id):
        project_list_structs = []
        try:
            project = Project.objects.get(pk=project_id)
            for project_list in project.todo_lists.filter(archived=False):
                project_list_structs.append(TodoListStruct(project_list))
        except Project.DoesNotExist:
            pass
        return render(request, 'base/partials/project_todo_lists_master_week_partial.html',
                      {'project_lists': project_list_structs, })


class ReloadProjectTodoLists(CustomLoginRequiredMixin, View):
    def get(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        all_lists = []
        for todo_list in project.todo_lists.filter(archived=False).order_by("-id"):
            list_struct = TodoListStruct(todo_list)
            all_lists.append(list_struct)
        return render(request, 'base/partials/project_todo_lists_partial.html',
                      {'project': project, 'all_todo_lists': all_lists, 'my_user': self.profile(request)})


class ArchiveDeleteProjectTodoList(CustomLoginRequiredMixin, View):

    def post(self, request, list_id):
        profile = self.profile(request)
        list = ProjectTodoList.objects.get(pk=list_id, project__user=profile)
        list.archived = True
        list.save()
        return JsonResponse({})

    def delete(self, request, list_id):
        profile = self.profile(request)
        list = ProjectTodoList.objects.get(pk=list_id, project__user=profile)
        list.delete()
        return JsonResponse({})

    def put(self, request, list_id):
        profile = self.profile(request)
        list = ProjectTodoList.objects.get(pk=list_id, project__user=profile)
        data = json.loads(request.body.decode("utf-8"))
        if data.get("name"):
            list.title = data["name"]
            list.save()
        return JsonResponse({})


class ProjectTodoListItems(CustomLoginRequiredMixin, View):

    def get(self, request, list_id):
        list_tasks = ProjectTodoList.get_tasks_for_list(list_id)
        results = [task.to_dict() for task in list_tasks]
        return JsonResponse({'tasks': results})


class ProjectEventView(CustomLoginRequiredMixin, View):

    def get(self, request, project_id):
        project_events = ProjectEvent.objects.filter(project_id=project_id).all().order_by('start')
        json_events = [event.to_json() for event in project_events]
        return JsonResponse(json_events, safe=False)

    def post(self, request, project_id, event_id=None):
        project = Project.objects.get(pk=project_id, user=self.profile(request))
        data = json.loads(request.body.decode('utf-8'))
        if event_id:
            event = ProjectEvent.objects.get(id=event_id, project=project)
        else:
            event = ProjectEvent(project=project)

        event.title = data['title']
        event.description = data['description']
        event.start = parse(data['start'])
        if 'end' in data:
            event.end = parse(data['end'])
        event.save()
        return JsonResponse(event.to_json())

    def delete(self, request, project_id, event_id):
        event = ProjectEvent.objects.get(id=event_id, project__user=self.profile(request))
        event.delete()
        return JsonResponse({})


class PersonalListExtractorMixin():

    @staticmethod
    def extract_personal_lists(_lists, users_today):
        important_list = None
        urgent_list = None
        extra_list = None
        for _list in _lists:
            if _list.priority == 1:
                important_list = TodoListStruct(_list, extras={'class': 'important-list'},
                                                completed_date_filter=users_today, personal_list=True)
            elif _list.priority == 2:
                urgent_list = TodoListStruct(_list, extras={'class': 'secondary-list'},
                                             completed_date_filter=users_today, personal_list=True)
            elif _list.priority == 3:
                extra_list = TodoListStruct(_list, extras={'class': 'extra-list'}, completed_date_filter=users_today,
                                            personal_list=True)
        return urgent_list, important_list, extra_list

    @staticmethod
    def extract_day_lists(_lists, users_today):
        results = list()
        for _list in _lists:
            day_struct = TodoListStruct(_list, completed_date_filter=users_today, day_list=True, no_completed=True)
            results.append(day_struct)
        return results


class MasterTodo(CustomLoginRequiredMixin, View):

    def set_first_flags(self, profile):
        first_today = ''
        first_work = ''
        first_work_stats = ''
        first_week_plan = ''
        if profile.first_today:
            first_today = 'true'
            profile.first_today = False
        if profile.first_work:
            first_work = 'true'
            profile.first_work = False
        if profile.first_work_stats:
            first_work_stats = 'true'
            profile.first_work_stats = False
        if profile.first_week_plan:
            profile.first_week_plan = False
            first_week_plan = 'true'
        profile.save()
        return first_today, first_work, first_work_stats, first_week_plan

    def get(self, request):
        profile = self.profile(request)
        first_today, first_work, first_work_stats, first_week_plan = self.set_first_flags(profile)

        return render(request, 'base/master_todo_view.html', {'active_today': True, 'first_work': first_work,
                                                              'first_work_stats': first_work_stats,
                                                              'first_today': first_today,
                                                              'first_week_plan': first_week_plan
                                                              })


class PomodoroStatsMixin:

    def today_stats(self, profile):
        users_today = user_time_now(profile.utc_offset).date()
        todays_sessions = WorkCycleGroup.get_users_day(profile, day_start=users_today)
        return self._calc_stats(todays_sessions)

    def week_stats(self, profile):
        week_start = calc_week_start(profile.utc_offset)
        week_sessions = WorkCycleGroup.get_users_week(profile, week_start=week_start)
        return self._calc_stats(week_sessions)

    def get_all_pomodoro_stats(self):
        today_stats = self.today_stats(profile)
        week_stats = self.week_stats(profile)
        week_avgs = self.calc_week_averages(profile.utc_offset, week_stats)

    def minutes_to_human(self, total_minutes):
        hours = total_minutes // 60
        remaining_minutes = round((total_minutes % 60), 2)
        return "{}h {}min".format(hours, remaining_minutes)

    def _calc_stats(self, sessions):
        sessions_count = sessions.count()
        total_minutes = 0
        cycles_count = 0
        for session in sessions:
            total_minutes += session.total_work_duration()
            cycles_count += session.cycles_num
        total_time = self.minutes_to_human(total_minutes)
        return self.Stat(total_time, sessions_count, cycles_count, total_minutes)

    def calc_week_averages(self, utc_offset, week_stats):
        days = user_time_now(utc_offset).date().isoweekday()
        avg_time_minutes = round(week_stats.total_minutes / days, 2)
        return self.Stat(
            total_time=self.minutes_to_human(avg_time_minutes),
            sessions_count=round(week_stats.sessions_count / days, 2),
            cycles_count=round(week_stats.cycles_count / days, 2),
            total_minutes=avg_time_minutes
        )

    def today_stats(self, project_id, profile):
        users_today = user_time_now(profile.utc_offset).date()
        if project_id == 'all':
            todays_sessions = WorkCycleGroup.get_users_day(profile, day_start=users_today)
        else:
            todays_sessions = WorkCycleGroup.get_projects_day(project_id, day_start=users_today)
        return self._calc_stats(todays_sessions)

    def week_stats(self, project_id, profile):
        week_start = calc_week_start(profile.utc_offset)
        if project_id == 'all':
            week_sessions = WorkCycleGroup.get_users_week(profile, week_start=week_start)
        else:
            week_sessions = WorkCycleGroup.get_projects_week(project_id, week_start=week_start)
        return self._calc_stats(week_sessions)


class StatsDataMixin:
    Stat = namedtuple('Stat', ['total_time', 'sessions_count', 'cycles_count', 'total_minutes'])

    class TaskTrackTime:
        def __init__(self, task):
            self.task = task
            self.tracks_dict = dict()
            self.full_tracks_list = list()

        def add_track_to_dict(self, track):
            self.tracks_dict[track.track_date] = track

        def fill_week(self, week_start):
            day_date = week_start
            for i in range(7):
                if day_date in self.tracks_dict:
                    self.full_tracks_list.append(self.tracks_dict[day_date])
                else:
                    self.full_tracks_list.append(self.empty_track(track_date=day_date))
                day_date += datetime.timedelta(days=1)

        def empty_track(self, track_date):
            return TrackWorkedDay(minutes_worked=0, track_date=track_date)

    def calc_personal_worked_today(self, profile):
        total_minutes_today = ProjectTodoItem.personal_tasks_worked_today_sum(profile)
        return self.format_h_min(total_minutes_today)

    def calc_project_worked_today(self, project, utc_offset):
        total_minutes_today = ProjectTodoItem.project_tasks_worked_today_sum(project)

        if project.time_target_type == '0':  # Day
            return self.format_h_min(total_minutes_today)

        elif project.time_target_type == '1':  # week
            profile_week_start = calc_week_start(utc_offset)
            total_minutes = total_minutes_today + self.history_total_worked(project.id, profile_week_start)
            return self.format_h_min(total_minutes)

        elif project.time_target_type == '2':
            profile_month_start = calc_month_start(utc_offset)
            total_minutes = total_minutes_today + self.history_total_worked(project.id, profile_month_start)
            return self.format_h_min(total_minutes)

    def format_h_min(self, total_minutes):
        if total_minutes == 0:
            return "0h 0min"
        else:
            hours_worked = total_minutes // 60
            mins_worked = total_minutes % 60
            return "{}h {}min".format(hours_worked, mins_worked)

    def history_total_worked(self, project_id, profile_week_start):
        return TrackWorkedDay.get_sum_by_project(project_id, from_=profile_week_start)

    @classmethod
    def group_by_task(cls, all_tracks):
        grouped = dict()
        for track in all_tracks:
            if track.task_id not in grouped:
                task = ProjectTodoItem.get_by_id(track.task_id)
                grouped[track.task_id] = cls.TaskTrackTime(task)
            grouped[track.task_id].add_track_to_dict(track)
        return grouped

    @staticmethod
    def fill_missing_days(grouped_tracks, week_start):
        results = list()
        for task_tracks_obj in grouped_tracks.values():
            task_tracks_obj.fill_week(week_start)
            results.append(task_tracks_obj)
        return results


class ProjectStatsData(CustomLoginRequiredMixin, View, StatsDataMixin):

    # def get(self, request, project_id):
    #     profile = self.profile(request)
    #     today_stats = self.today_stats(project_id, profile)
    #     week_stats = self.week_stats(project_id, profile)
    #     week_avgs = self.calc_week_averages(profile.utc_offset, week_stats)
    #     return JsonResponse({'today_stats': today_stats,
    #                          'week_stats': week_stats,
    #                          'week_avgs': week_avgs
    #                          })

    def get(self, request, project_id):
        pass


class MasterPartialStats(CustomLoginRequiredMixin, View, StatsDataMixin):

    def get(self, request, project_id=None):
        profile = self.my_profile
        profile_week_start = calc_week_start(profile.utc_offset)
        if project_id:
            if project_id == '0':
                active_project = None
            else:
                active_project = Project.get_by_id(project_id)
        else:
            active_project = profile.projects.first()

        if active_project:
            project_time_target_name, project_time_target_val = self.project_time_targets(active_project)
            project_time_target_duration = active_project.time_target_duration
            all_worked_this_week = self.combine_project_archive_with_today(profile, active_project, profile_week_start)
            today_worked_total = self.calc_project_worked_today(active_project, profile.utc_offset)
        else:
            project_time_target_name, project_time_target_val = self.blank_project_time_target()
            project_time_target_duration = None
            all_worked_this_week = self.combine_personal_archive_with_today(profile, profile_week_start)
            today_worked_total = self.calc_personal_worked_today(active_project)

        tracks_grouped = self.group_by_task(all_worked_this_week)
        complete_week_tracks = self.fill_missing_days(tracks_grouped, profile_week_start)
        week_days = self.gen_week_days(profile_week_start)
        all_target_options = Project.TIME_TARGET_CHOICES

        rendered_response = render_to_string('base/master_todo_stats.html', {
            'user_projects': profile.projects.all,
            'my_user': profile, 'week_days': week_days,
            'active_project': active_project, 'project_time_target_type': project_time_target_name,
            'project_time_target_val': project_time_target_val, 'all_target_options': all_target_options,
            'project_time_target_duration': project_time_target_duration,
            'today_stats': 0, 'week_stats': 0, 'week_avgs': 0,
            'tracks_grouped': complete_week_tracks, 'project_worked_total': today_worked_total
        })
        return JsonResponse({'content': rendered_response})

    def gen_week_days(self, week_start):
        days = list()
        day_date = week_start
        names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for i in range(7):
            full_name = '{} ({})'.format(names[i], day_date.strftime('%b %d'))
            days.append(full_name)
            day_date += datetime.timedelta(days=1)
        return days

    def combine_personal_archive_with_today(self, profile, profile_week_start):
        tracks_worked_this_week = list(TrackWorkedDay.get_personal(profile.id, profile_week_start))
        today_worked_into_tracks = self.today_worked_personal(profile)
        tracks_worked_this_week.extend(today_worked_into_tracks)
        return tracks_worked_this_week

    def combine_project_archive_with_today(self, profile, active_project, profile_week_start):
        tracks_worked_this_week = list(TrackWorkedDay.get_by_project(active_project.id, profile_week_start))
        today_worked_into_tracks = self.today_worked_project(profile, active_project)
        tracks_worked_this_week.extend(today_worked_into_tracks)
        return tracks_worked_this_week

    def today_worked_project(self, profile, project):
        results = list()
        tasks_worked_today = ProjectTodoItem.project_tasks_worked_today(project)
        profile_today = user_time_now(profile.utc_offset).date()
        for task in tasks_worked_today:
            track = TrackWorkedDay(user=profile,
                                   project=project,
                                   task_list_id=task.project_list_id,
                                   task=task,
                                   track_date=profile_today,
                                   minutes_worked=task.minutes_worked_today
                                   )
            results.append(track)
        return results

    def today_worked_personal(self, profile):
        results = list()
        personal_worked_today = ProjectTodoItem.personal_tasks_worked_today(profile)
        profile_today = user_time_now(profile.utc_offset).date()
        for task in personal_worked_today:
            track = TrackWorkedDay(user=profile,
                                   project=None,
                                   task=task,
                                   track_date=profile_today,
                                   minutes_worked=task.minutes_worked_today)
            results.append(track)
        return results

    def blank_project_time_target(self):
        project_time_target_name = Project.TIME_TARGET_CHOICES[0][1].capitalize()
        project_time_target_val = "0"
        return project_time_target_name, project_time_target_val

    def project_time_targets(self, active_project):
        if active_project.time_target_type:
            project_time_target_name = str(
                Project.TIME_TARGET_CHOICES[int(active_project.time_target_type)][1]).capitalize()
            project_time_target_val = active_project.time_target_type
        else:
            project_time_target_name, project_time_target_val = self.blank_project_time_target()
        return project_time_target_name, project_time_target_val


class MasterPartialWork(CustomLoginRequiredMixin, View, PersonalListExtractorMixin):

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

    def get(self, request):
        profile = request.user.account.profile
        _lists = PersonalTodoList.objects.filter(user=profile).order_by('priority')
        urgent_list, important_list, extra_list = self.extract_personal_lists(_lists, self.profile_today)
        personal_lists = [urgent_list, important_list, extra_list]
        groups = WorkCycleGroup.get_past_sessions(profile)
        pastSessions = self.past_sessions(groups)
        rendered_response = render_to_string('base/master_todo_work.html', {
            'my_user': profile, 'personal_lists': personal_lists, 'pastSessions': pastSessions,
            'today_date': self.profile_today
        })
        return JsonResponse({'content': rendered_response})


class MasterPartialPlanWeek(CustomLoginRequiredMixin, View, PersonalListExtractorMixin):

    def weekdays(self):
        DAY = "%A"
        user_today = self.profile_today
        user_monday = user_today - datetime.timedelta(days=user_today.weekday())
        all_days = []
        all_days.append({
            'name': user_monday.strftime(DAY),
            'isodate': user_monday.isoformat()
        })
        for i in range(1, 7):
            next_day = user_monday + datetime.timedelta(days=i)
            all_days.append({
                'name': next_day.strftime(DAY),
                'isodate': next_day.isoformat()
            })
        return all_days

    def get(self, request):
        profile = request.user.account.profile
        latest_project = Project.objects.filter(user=profile).order_by("-id").first()
        project_lists = list()
        if latest_project:
            project_lists = MasterPartialPlan.convert_lists_to_structs(latest_project.todo_lists.filter(archived=False))
        all_projects = profile.projects.all
        this_week_tasks = ProjectTodoItem.this_week_tasks(profile, self.profile_today)
        profile_date = user_time_now(profile.utc_offset).date()
        master_tasks = ProjectTodoItem.get_active_master_tasks(profile)
        all_week_tasks = this_week_tasks
        tasks_grouped = self.group_by_day(all_week_tasks, master_tasks, profile_date)
        days_structs = self.create_day_lists(tasks_grouped, profile_date)
        rendered_response = render_to_string('base/master_todo_plan_week.html',
                                             {'my_user': profile, 'all_projects': all_projects,
                                              'project': latest_project,
                                              'project_lists': project_lists,
                                              'latest_project': latest_project,
                                              'days_structs': days_structs,
                                              'today_date': self.profile_today
                                              })
        return JsonResponse({'content': rendered_response})

    @staticmethod
    def create_day_lists(tasks_grouped, today):
        DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        results = []
        iterday = today
        for i in range(7):
            weekday = iterday.isoweekday()
            day_list = TodoListStruct()
            day_list.todo = tasks_grouped[i]
            day_list.human_date = iterday.strftime(SHORT_DATE_FORMAT)
            day_list.isodate = iterday.isoformat()
            day_list.title = DAY_NAMES[weekday-1]
            results.append(day_list)
            iterday += datetime.timedelta(days=1)
            i += 1
        return results

    @staticmethod
    def group_by_day(week_tasks, master_tasks, user_today):
        day_lists = [ [], [], [], [], [], [], [] ]
        week_start = user_today
        week_end = week_start + datetime.timedelta(days=6)
        task_i = 0
        day_i = 0
        while week_start <= week_end:
            while task_i < len(week_tasks) and week_tasks[task_i].due_date.date() == week_start:
                day_lists[day_i].append(week_tasks[task_i])
                task_i += 1
            day_i += 1
            week_start += datetime.timedelta(days=1)
        today_list = day_lists[0]
        today_list.extend(master_tasks.all())
        return day_lists

class MasterPartialPlan(CustomLoginRequiredMixin, View, PersonalListExtractorMixin):

    def get(self, request):
        profile = request.user.account.profile
        personal_lists = self.profile_personal_lists(profile)

        latest_project = Project.objects.filter(user=profile).order_by("-id").first()
        project_lists = list()
        if latest_project:
            project_lists = self.convert_lists_to_structs(latest_project.todo_lists.filter(archived=False))

        all_projects = profile.projects.all
        rendered_response = render_to_string('base/master_todo_plan.html',
                                             {'my_user': profile, 'personal_lists': personal_lists,
                                              'all_projects': all_projects,
                                              'project': latest_project,
                                              'project_lists': project_lists,
                                              'latest_project': latest_project,
                                                'today_date': self.profile_today
                                              })
        return JsonResponse({'content': rendered_response})

    def profile_personal_lists(self, profile):
        _lists = PersonalTodoList.objects.filter(user=profile).order_by('priority')
        users_today = user_time_now(profile.utc_offset).date()
        urgent_list, important_list, extra_list = self.extract_personal_lists(_lists, users_today)
        personal_lists = [urgent_list, important_list, extra_list]
        return personal_lists

    @staticmethod
    def check_tasks_present(important, secondary, extra):
        return important.done or important.todo or secondary.done or secondary.todo or extra.done or extra.todo

    def post(self, request, project_id):
        project = Project.objects.get(pk=project_id)
        todoList = ProjectTodoList()
        data = json.loads(request.body.decode('utf-8'))
        todoList.title = data['title']
        todoList.project = project
        todoList.save()
        # todoList.refresh_from_db()
        return JsonResponse({'success': True, 'listId': todoList.id})

    @staticmethod
    def convert_lists_to_structs(_lists):
        result_structs = []
        for p_list in _lists:
            list_struct = TodoListStruct(p_list)
            result_structs.append(list_struct)
        return result_structs


class SyncMasterWeek(MasterPartialPlan):

    def get(self, request):
        return JsonResponse({})

    def post(self, request):
        synced_tasks = PersonalTodoList.sync_week_planner_today(self.my_profile)
        personal_lists = self.profile_personal_lists(self.my_profile)
        rendered_response = render_to_string("base/partials/personal_lists_partial.html",
                                             {'personal_lists': personal_lists, 'today_date': self.profile_today})
        return JsonResponse({'content': rendered_response})

class MasterTodoItem(CustomLoginRequiredMixin, View):

    def get(self, request, item_id):
        todo_item = ProjectTodoItem.objects.get(pk=item_id)
        return JsonResponse({'item': todo_item.to_dict(full=True)})

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        title = data['title']
        item_index = data['index']
        list_type = data.get('listType')
        if list_type == 'day':
            list_date = data['listId']
            item = ProjectTodoItem(title=title, due_date=parse(list_date))
        else:
            list_id = data['listId']
            item = ProjectTodoItem(title=title, personal_list_id=list_id, personal_list_order=item_index)
        if data.get('description'):
            item.description = data['description']
        item.user = self.my_profile
        item.save()
        self.update_daily_success(task_type='work', todo=1)
        AnalyticsManager.record(self.user_id, MASTER_TASK)
        item_response = {
            'title': item.title,
            'id': item.id,
            'index': item_index
        }
        if list_type == 'day':
            item_response['listDate'] = list_date

        return JsonResponse({'success': True, 'item': item_response})

    def update_project_list_and_order(self, item, new_project_list_id):
        if not new_project_list_id or new_project_list_id == '0':
            item.project_list_id = None
        elif item.project_list_id != new_project_list_id:
            item.project_list_id = new_project_list_id
            last_item_new_list = ProjectTodoItem.last_active_from_list(new_project_list_id)
            if last_item_new_list:
                item.project_list_order = last_item_new_list.project_list_order + 1
            else:
                item.project_list_order = 1

    def put(self, request, item_id):
        item = get_object_or_404(ProjectTodoItem, pk=item_id)
        data = json.loads(request.body.decode('utf-8'))
        if 'project_list_id' in data:
            self.update_project_list_and_order(item, data['project_list_id'])
        if 'title' in data:
            item.title = data['title']
        if data.get('description'):
            item.description = data['description']
        if data.get('dueDate'):
            item.due_date = parse(data['dueDate'])
            if item.due_date.date() > self.profile_today:
                item.personal_list = None
                item.personal_list_order = None
                item.added_to_master = False
        item.save()
        return JsonResponse({'item': item.to_dict()})

    def delete(self, request, item_id):
        item = ProjectTodoItem.objects.get(pk=item_id)
        project_item_id = 0
        if item.project_list:
            item.added_to_master = False
            item.personal_list = None
            item.day_list = None
            project_item_id = item.id
            item.save()
        else:
            item.delete()
        self.update_daily_success('work', todo=-1)
        return JsonResponse({'success': True, 'project_item_id': project_item_id})


class CompleteMasterItem(CustomLoginRequiredMixin, View):
    def post(self, request, item_id):
        personal_item = ProjectTodoItem.objects.get(pk=item_id)
        data = json.loads(request.body.decode('utf-8'))
        if data['completed']:
            personal_item.complete_now(self.profile_now)
        else:
            personal_item.completed = False
            personal_item.save()
        self.update_daily_success('work', done=1)
        return JsonResponse({'success': True})


class TransferItemToMasterWeek(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))

        itemId = data['itemId']
        dayListDate = data['listDate']
        projectId = data['projectId']
        projectListId = data['projectListId']

        dayIndex = data.get('index')

        if not dayIndex:
            dayIndex = 1

        project_item = ProjectTodoItem.objects.get(pk=itemId)
        project_item.day_list_order = float(dayIndex)
        project_item.due_date = parse(dayListDate)
        project_item.user = self.my_profile
        project_item.save()
        AnalyticsManager.record(self.user_id, MASTER_TASK)
        response_item = {
            'id': itemId,
            'listDate': dayListDate,
            'index': dayIndex,
            'title': project_item.title,
            'projectId': projectId,
            'projectListId': projectListId
        }
        return JsonResponse({"success": True, 'item': response_item})


class TransferItemToMaster(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        itemId = data['itemId']
        personalListId = data['personalListId']
        projectListId = data['projectListId']
        personalIndex = data['index']
        project_item = self.update_project_item(itemId, personalIndex, personalListId)
        self.update_daily_success('work', todo=1)
        AnalyticsManager.record(self.user_id, MASTER_TASK)
        item_response = {
            'id': itemId,
            'listId': project_item.personal_list_id,
            'title': project_item.title,
            'index': personalIndex,
            'projectListId': projectListId
        }
        return JsonResponse({"success": True, "item": item_response})

    def update_project_item(self, itemId, personalIndex, personalListId):
        project_item = ProjectTodoItem.objects.get(pk=itemId)
        project_item.personal_list_id = personalListId
        project_item.personal_list_order = float(personalIndex)
        project_item.added_to_master = True
        project_item.save()
        return project_item


class TransferBetweenMasterLists(CustomLoginRequiredMixin, View):
    def post(self, request):
        data = json.loads(request.body.decode('utf-8'))
        itemId = data['itemId']
        index = data['index']
        oldListId = data['listId']
        newListType = data['listType']
        item = ProjectTodoItem.objects.get(pk=itemId)
        new_list = self.get_new_list(request.user.account.profile, newListType)
        if item.personal_list_id == new_list.id:
            #     same list reorder
            new_list.change_order(item.id, index)
        else:
            self.add_to_new_list(new_list, item, index)

        return JsonResponse({'success': True})

    def get_new_list(self, profile, listType):
        new_list_priority = PersonalTodoList.PRIORITIES[listType]
        new_list = PersonalTodoList.objects.filter(priority=new_list_priority, user=profile).get()
        return new_list

    def add_to_new_list(self, new_list, item, index):
        item.personal_list = new_list
        item.personal_list_order = index
        item.save()


class MySettingsView(CustomLoginRequiredMixin, account.views.SettingsView):

    def reminder_data(self, user_reminder, default_reminder):
        if user_reminder:
            return user_reminder, True
        else:
            return default_reminder, False

    def utc_offset_list(self):
        offsets = [
            ('-12', "UTC-12:00"),
            ('-11', "UTC-11:00"),
            ('-10', "UTC-10:00"),
            ('-9.3', "UTC-09:30"),
            ('-9', "UTC-09:00"),
            ('-8', "UTC-08:00"),
            ('-7', "UTC-07:00"),
            ('-6', "UTC-06:00"),
            ('-5', "UTC-05:00"),
            ('-4', "UTC-04:00"),
            ('-3.3', "UTC-03:30"),
            ('-3', "UTC-03:00"),
            ('-2', "UTC-02:00"),
            ('-1', "UTC-01:00"),
            ('0', "UTC+00:00"),
            ('1', "UTC+01:00"),
            ('2', "UTC+02:00"),
            ('3', "UTC+03:00"),
            ('3.3', "UTC+03:30"),
            ('4', "UTC+04:00"),
            ('4.3', "UTC+04:30"),
            ('5', "UTC+05:00"),
            ('5.3', "UTC+05:30"),
            ('6', "UTC+06:00"),
            ('6.3', "UTC+06:30"),
            ('7', "UTC+07:00"),
            ('8', "UTC+08:00"),
            ('9', "UTC+09:00"),
            ('9.3', "UTC+09:30"),
            ('10', "UTC+10:00"),
            ('10.3', "UTC+10:30"),
            ('11', "UTC+11:00"),
            ('12', "UTC+12:00"),
            ('13', "UTC+13:00"),
            ('14', "UTC+14:00"),
        ]
        return offsets

    def get_context_data(self, **kwargs):
        ctx = super(MySettingsView, self).get_context_data(**kwargs)
        user = self.profile(self.request)
        morning_reminder, morning_enabled = self.reminder_data(user.morning_reminder, Profile.DEFAULT_MORNING_REMINDER)
        midday_reminder, midday_enabled = self.reminder_data(user.midday_reminder, Profile.DEFAULT_MIDDAY_REMINDER)
        evening_reminder, evening_enabled = self.reminder_data(user.evening_reminder, Profile.DEFAULT_EVENING_REMINDER)
        ctx.update({
            'morning_reminder': morning_reminder,
            'midday_reminder': midday_reminder,
            'evening_reminder': evening_reminder,
            'morning_enabled': morning_enabled,
            'midday_enabled': midday_enabled,
            'evening_enabled': evening_enabled,
            'utc_offset_list': self.utc_offset_list()
        })
        if user.utc_offset != None:
            user_offset = user.utc_offset
        else:
            user_offset = '0'
        ctx.update({
            'user_offset': user_offset
        })
        return ctx

    def form_valid(self, form):
        self.update_settings(form)
        if self.messages.get("settings_updated"):
            messages.add_message(
                self.request,
                self.messages["settings_updated"]["level"],
                self.messages["settings_updated"]["text"]
            )
        return redirect(self.get_success_url())


class RemindersView(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        profile = self.profile(request)
        profile.update_reminder(data['morningEnabled'], 'morning', data.get('morning'))
        profile.update_reminder(data['middayEnabled'], 'midday', data.get('midday'))
        profile.update_reminder(data['eveningEnabled'], 'evening', data.get('evening'))
        profile.utc_offset = str(data['utcOffset'])
        profile.save()

        return JsonResponse({"success": True})


class SetTimezoneView(CustomLoginRequiredMixin, View):

    def post(self, request):
        profile = self.profile(request)
        data = json.loads(request.body.decode("utf-8"))
        local_date = parse(data['datetime'])
        seconds_offset = local_date.utcoffset().seconds
        hours_offset = str(int(seconds_offset / 3600))
        if seconds_offset % 3600:
            hours_offset += ".3"
        profile.utc_offset = hours_offset
        profile.save()
        return JsonResponse({'timezone': hours_offset})


class GeneratePomodoroCycles(CustomLoginRequiredMixin, View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        project_id = None
        if 'projectId' in data and data['projectId'] != '0':
            project_id = data['projectId']

        cycle_group = WorkCycleGroup(
            cycles_num=int(data['cycleCount']),
            work_duration=int(data['workDuration']),
            break_duration=int(data['breakDuration']),
            question_what=data['questionWhat'],
            question_how=data['questionHow'],
            project_id=project_id,
            user=self.profile(request)
        )
        cycle_group.save()
        new_cycles = []
        for i in range(cycle_group.cycles_num):
            cycle = WorkCycle(cycle_group_id=cycle_group.id)
            cycle.save()
            new_cycles.append(cycle)
        ctx = cycle_group.html_context(cycles=new_cycles)
        AnalyticsManager.record(self.user_id, POMODORO_SESSION)
        return JsonResponse({
            'content': render_to_string("base/partials/pomodoro_cycle_card.html", ctx),
            'cycleGroupId': cycle_group.id,
            'cycleIdList': [c.id for c in new_cycles]
        })


class OpenPomodoroGroup(CustomLoginRequiredMixin, View):

    def get(self, request, group_id):
        cycle_group = WorkCycleGroup.objects.get(pk=group_id)
        ctx = cycle_group.html_context()
        cycleReviewData = list()
        cyclesPassed = 0
        for cycle in ctx['cycles']:
            cycleReviewData.append(cycle.review_dict())
            if cycle.finished:
                cyclesPassed += 1
        return JsonResponse({
            'content': render_to_string("base/partials/pomodoro_cycle_card.html", ctx),
            'cycleGroupId': cycle_group.id,
            'cycleIdList': list(cycle_group.cycles_ids()),
            'activeCycleId': ctx['active_cycle_id'],
            'cycleReviewData': cycleReviewData,
            'cyclesPassed': cyclesPassed
        })


class SinglePomodoroCycle(CustomLoginRequiredMixin, View):

    def post(self, request, cycle_id):
        data = json.loads(request.body.decode("utf-8"))
        try:
            cycle = WorkCycle.by_id(cycle_id)
            cycle.update_review(data)
            AnalyticsManager.record(self.user_id, POMODORO_CYCLE)
            if data.get('taskId') and data.get('timeWorked'):
                ProjectTodoItem.add_minutes_worked(data['taskId'], int(data['timeWorked']))
            if data.get('finishSession'):
                cycle.cycle_group.finish()
        except WorkCycle.DoesNotExist:
            pass
        return JsonResponse({})


class SavePomodoroCycles(CustomLoginRequiredMixin, View):

    def post(self, request):
        all_data = json.loads(request.body.decode("utf-8"))
        for cycle_data in all_data['cyclesData']:
            if cycle_data['data']:
                cycle = WorkCycle.by_id(cycle_data['id'])
                cycle.update_from(cycle_data['data'])
        return JsonResponse({})


class ProjectTodoLists(CustomLoginRequiredMixin, View):

    def get(self, request, project_id):
        project = get_object_or_404(Project, id=project_id)
        project_lists = [list.to_dict() for list in project.todo_lists.filter(archived=False).order_by('-id')]
        return JsonResponse({'lists': project_lists})


class Billing(CustomLoginRequiredMixin, View):

    def normal_page(self, request):
        return render(request, 'base/billing.html', {'plan_trial': False,
                                                     'month_plan_id': Profile.MONTH_PLAN_ID,
                                                     'year_plan_id': Profile.YEAR_PLAN_ID})

    def get(self, request):
        if self.my_profile.is_trial():
            return self.handle_trial(request)
        else:
            return self.handle_paying(request)

    def handle_trial(self, request):
        trial_end_time = self.my_profile.trial_end_time
        if not trial_end_time:
            return self.normal_page(request)
        else:
            plan_status_msg, status_class = self.trial_status_message(trial_end_time)
            return render(request, 'base/billing.html', {
                'plan_status': plan_status_msg,
                'status_class': status_class,
                'month_plan_id': Profile.MONTH_PLAN_ID,
                'year_plan_id': Profile.YEAR_PLAN_ID})

    def trial_status_message(self, trial_end_time):
        today = datetime.datetime.today().date()
        if trial_end_time < today:
            return "Your free trial has expired, pick a plan to continue using LifeHQ.", "text-danger"
        else:
            trial_remaining = trial_end_time - today
            return "Your free trial ends in {} days.".format(trial_remaining), "color--success"

    def handle_paying(self, request):
        plan_end_time = self.my_profile.plan_end_time
        if plan_end_time:
            end_time_formatted = plan_end_time.strftime(HUMAN_FORMAT)
            plan_status_msg = "Your plan ends on {}.".format(end_time_formatted)
            status_class = "text-danger"
        else:
            plan_status_msg = "Your plan is active."
            status_class = "color--success"
        return render(request, 'base/billing.html', {
            'plan_status': plan_status_msg,
            'status_class': status_class,
            'month_plan_id': Profile.MONTH_PLAN_ID,
            'year_plan_id': Profile.YEAR_PLAN_ID})


class BillingStatus(CustomLoginRequiredMixin, View):

    def get(self, request):
        receipts = PaymentEvent.profile_receipts(self.my_profile)
        return render(request, 'base/billing-status.html', {"profile": self.my_profile, "receipts": receipts})


from libs.paddle_billing import verify_signature


def invalidate_billing_cache(profile_id):
    cache.set("billing:{}".format(profile_id), None)


def send_payment_welcome(profile_id, email_to):
    logger.info("Welcoming new user {}".format(email_to))
    subject = "Your special offer and a warm welcome from LifeHQ"
    message = render_to_string("onboarding/payment-welcome.html", {})
    plain_message = strip_tags(message)
    to = [email_to]
    mail.send_mail(subject, plain_message, EMAIL_FROM, to, html_message=message)


@csrf_exempt
def test_error(request):
    b = 5 / 0
    return HttpResponse()


@csrf_exempt
def paddle_webhook(request):
    logger.info("Webhook paddle")
    webhook_data = {}
    for parameter, value in request.POST.items():
        logger.info("{}={}".format(parameter, value))
        webhook_data[parameter] = value
    logger.info("Now let's verify the signature")
    if verify_signature(logger, webhook_data):
        logger.info("Signature is verified, event: {}".format(webhook_data['alert_name']))
        profile_id = webhook_data['passthrough']
        invalidate_billing_cache(profile_id)
        try:
            profile = Profile.objects.get(pk=profile_id)
            profile.update_payment_status(webhook_data)
            event = webhook_data['alert_name']
            if event == 'subscription_created':
                AnalyticsManager.record(profile_id, PAYMENTS)
                send_payment_welcome(profile.id, profile.account.user.email)
        except Profile.DoesNotExist:
            logger.info("It was an old profile with id {}".format(profile_id))
            pass
    return HttpResponse()


class UnsubscribeOnboarding(View):

    def get(self, request, onboard_id):
        onboard = OnboardEvents.objects.get(pk=onboard_id)
        onboard.onboard_canceled = True
        onboard.save()
        return render(request, "base/onboard-canceled.html")


class UnsubscribeSales(View):

    def get(self, request, onboard_id):
        onboard = OnboardEvents.objects.get(pk=onboard_id)
        onboard.sales_canceled = True
        onboard.save()
        return render(request, "base/sales-canceled.html")
