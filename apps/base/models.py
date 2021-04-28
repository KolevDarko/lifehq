"""Base models"""
import datetime
from time import strftime

from account.models import Account
from dateutil.parser import parse
from django.db import models
from django.db.models import CharField, ForeignKey, TextField, BooleanField, OneToOneField, DateTimeField, \
    IntegerField, DateField, ImageField, FloatField, F, Model, Sum, Q
from django.utils import timezone

from apps.common.models import HashedModel
from mastermind import utils
from mastermind.utils import user_time_now, calc_week_range


class TimestampedModel(HashedModel):
    created_on = models.DateTimeField(editable=False)
    updated_on = models.DateTimeField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_on = timezone.now()
        self.updated_on = timezone.now()
        return super(TimestampedModel, self).save(*args, **kwargs)


class Profile(HashedModel):
    """
    Profile_type is used so I can have a template user from where I get default journal templates and other stuff
    so far profile_type can be profile and template
    """
    DEFAULT_MORNING_REMINDER = "07:00"
    DEFAULT_MIDDAY_REMINDER = "12:00"
    DEFAULT_EVENING_REMINDER = "21:00"

    BETA_USER = 'beta_user'
    NORMAL_USER = 'normal_user'
    TEMPLATE_USER = 'template_user'
    MY_TRIAL = 'my-trial'
    TRIAL_DURATION = 30

    # PLAN_IDS = { Test plans
    #     '551918': 'Monthly Plan',
    #     '551944': 'Year Plan',
    #     '552153': 'Daily Plan'
    # }

    # THE FREE MONTHLY ONE
    # MONTH_PLAN_ID = '551918'


    # REAl ONES
    MONTH_PLAN_ID = '557037'
    YEAR_PLAN_ID = '557038'

    PLAN_IDS = {
        MONTH_PLAN_ID: 'Monthly Plan',
        YEAR_PLAN_ID: 'Year Plan',
    }


    UPLOAD_LIMIT_MB = 1024
    # UPLOAD_LIMIT_MB = 300

    name = CharField(max_length=200)
    profile_type = CharField(max_length=30, default=NORMAL_USER)
    account = OneToOneField(Account, on_delete=models.CASCADE, related_name='profile')
    first_login = BooleanField(default=True)
    first_habit = BooleanField(default=True)
    first_journal = BooleanField(default=True)
    first_journal_template = BooleanField(default=True)
    first_note = BooleanField(default=True)
    first_note_template = BooleanField(default=True)
    first_today = BooleanField(default=True)
    first_project = BooleanField(default=True)
    first_proj_tasks = BooleanField(default=True)
    first_proj_schedule = BooleanField(default=True)
    first_proj_resource = BooleanField(default=True)
    first_work = BooleanField(default=True)
    first_work_stats = BooleanField(default=True)
    first_week_plan = BooleanField(default=True)
    has_default_data = BooleanField(default=False)

    active_project_id = IntegerField(blank=True, null=True)
    beta_token = CharField(blank=True, null=True, max_length=20)

    morning_reminder = CharField(max_length=20, default='')
    midday_reminder = CharField(max_length=20, default='')
    evening_reminder = CharField(max_length=20, default=DEFAULT_EVENING_REMINDER)

    utc_offset = CharField(blank=True, null=True, max_length=20)
    total_upload_quota = FloatField(default=0.0) #in bytes
    passive = BooleanField(default=False)

    # billing
    # https: // paddle.com / docs / subscription - update - cancel - pages /
    subscription_status = CharField(max_length=20, default=MY_TRIAL)

    subscription_id = CharField(blank=True, null=True, max_length=20)
    subscription_plan_id = CharField(blank=True, null=True, max_length=20)
    plan_name = CharField(blank=True, null=True, max_length=20)
    next_bill_date = DateField(blank=True, null=True)
    cancel_url = CharField(blank=True, null=True, max_length=600)
    update_url = CharField(blank=True, null=True, max_length=600)
    subscription_last_event = DateTimeField(blank=True, null=True)
    cancellation_effective_date = DateField(blank=True, null=True)
    plan_start_time = DateField(blank=True, null=True)
    plan_end_time = DateField(blank=True, null=True)

    trial_start_time = DateField(blank=True, null=True)
    trial_end_time = DateField(blank=True, null=True)


    @classmethod
    def get_template_user(cls):
        return cls.objects.get(profile_type=cls.TEMPLATE_USER)

    def is_trial(self):
        return self.subscription_status == self.MY_TRIAL

    def is_plan_valid(self):
        users_today = user_time_now(self.utc_offset)
        if self.is_trial():
            if self.trial_end_time:
                return self.trial_end_time >= users_today.date()
            else:
                # to be investigated
                return True
        else:
            if not self.plan_end_time:
                return True
            else:
                return self.plan_end_time >= users_today.date()

    def update_payment_status(self, payment_data):
        event = payment_data['alert_name']
        if event == 'subscription_created':
            self.subscription_status = payment_data['status']
            self.subscription_id = payment_data['subscription_id']
            self.subscription_plan_id = payment_data['subscription_plan_id']
            self.next_bill_date = parse(payment_data['next_bill_date'])
            self.update_url = payment_data['update_url']
            self.cancel_url = payment_data['cancel_url']
            self.subscription_last_event = parse(payment_data['event_time'])
            self.plan_name = self.PLAN_IDS[str(self.subscription_plan_id)]
            self.plan_start_time = datetime.datetime.utcnow()
            self.plan_end_time = None
            self.save()
            PaymentEvent.objects.create(
                profile_id=self.id,
                subscription_id=self.subscription_id,
                event_type='subscription',
                event_subtype='subscription_created',
                subscription_status=self.subscription_status,
                subscription_plan_id=self.subscription_plan_id,
                event_date=self.subscription_last_event,
                next_bill_date=self.next_bill_date,
            )
        elif event == 'subscription_updated':
            self.subscription_status = payment_data['status']
            self.subscription_plan_id = payment_data['subscription_plan_id']
            self.next_bill_date = parse(payment_data['next_bill_date'])
            self.subscription_last_event = parse(payment_data['event_time'])
            self.save()
            PaymentEvent.objects.create(
                profile_id=self.id,
                subscription_id=self.subscription_id,
                event_type='subscription',
                event_subtype='subscription_updated',
                subscription_status=self.subscription_status,
                subscription_plan_id=self.subscription_plan_id,
                event_date=self.subscription_last_event,
                next_bill_date=self.next_bill_date,
            )
        elif event == 'subscription_cancelled':
            self.subscription_last_event = parse(payment_data['event_time'])
            self.cancellation_effective_date = payment_data['cancellation_effective_date']
            self.plan_end_time = payment_data['cancellation_effective_date']
            self.subscription_status = payment_data['status']
            self.save()
            PaymentEvent.objects.create(
                profile_id=self.id,
                subscription_id=self.subscription_id,
                event_type='subscription',
                event_subtype='subscription_deleted',
                subscription_status=self.subscription_status,
                subscription_plan_id=self.subscription_plan_id,
                event_date=self.subscription_last_event,
            )
        elif event == 'subscription_payment_succeeded':
            self.next_bill_date = parse(payment_data['next_bill_date'])
            self.subscription_status = payment_data['status']
            self.subscription_last_event = parse(payment_data['event_time'])
            self.save()
            PaymentEvent.objects.create(
                profile_id=self.id,
                subscription_id=self.subscription_id,
                event_type='payment',
                event_subtype='payment_succeeded',
                subscription_status=self.subscription_status,
                subscription_plan_id=self.subscription_plan_id,
                event_date=self.subscription_last_event,
                next_bill_date=self.next_bill_date,
                receipt_url=payment_data['receipt_url'],
                plan_name=payment_data['plan_name'],
                amount=payment_data['sale_gross']
            )
        elif event == 'subscription_payment_failed':
            self.subscription_status = payment_data['status']
            self.subscription_last_event = parse(payment_data['event_time'])
            if payment_data.get('hard_failure'):
                self.plan_end_time = datetime.datetime.utcnow()
            self.save()
            PaymentEvent.objects.create(
                profile_id=self.id,
                subscription_id=self.subscription_id,
                event_type='payment',
                event_subtype='payment_failed',
                subscription_status=self.subscription_status,
                subscription_plan_id=self.subscription_plan_id,
                event_date=self.subscription_last_event,
                next_bill_date=parse(payment_data['next_retry_date']),
                receipt_url=payment_data['receipt_url'],
            )
        elif event == 'subscription_payment_refund':
            self.subscription_last_event = parse(payment_data['event_time'])
            self.plan_end_time = datetime.datetime.utcnow()
            self.save()
            PaymentEvent.objects.create(
                profile_id=self.id,
                subscription_id=self.subscription_id,
                event_type='payment',
                event_subtype='payment_refund',
                subscription_plan_id=self.subscription_plan_id,
                event_date=self.subscription_last_event,
                receipt_url=payment_data['receipt_url'],
                amount=payment_data['amount']
            )
        #     should suggest to them to update their card
        #     todo could send email to user when refunded and failed payment

    def update_reminder(self, reminder_enabled, key, new_value):
        if reminder_enabled:
            setattr(self, "{}_reminder".format(key), new_value)
        else:
            setattr(self, "{}_reminder".format(key), '')

    def get_morning_reminder(self):
        if self.morning_reminder == None:
            return self.DEFAULT_MORNING_REMINDER
        else:
            return self.morning_reminder

    def get_midday_reminder(self):
        if self.midday_reminder == None:
            return ''
        else:
            return self.midday_reminder

    def get_evening_reminder(self):
        if self.evening_reminder == None:
            return self.DEFAULT_EVENING_REMINDER
        else:
            return self.evening_reminder

    def get_utc_offset(self):
        if self.utc_offset:
            return self.utc_offset
        else:
            return '0'

    def update_uploads_quota(self, new_size):
        self.total_upload_quota = F('total_upload_quota') + new_size
        self.save()
        self.refresh_from_db()
        return self.total_upload_quota

    def upload_limit_exceeds(self, size_in_bytes):
        return utils.bytes_to_mb(self.total_upload_quota + size_in_bytes) > self.UPLOAD_LIMIT_MB

class PaymentEvent(Model):
    profile = ForeignKey(Profile, on_delete=models.CASCADE, related_name='payment_events')

    event_type = CharField(max_length=30)
    event_subtype = CharField(max_length=30)
    event_date = DateTimeField(blank=True, null=True)
    subscription_id = CharField(blank=True, null=True, max_length=20)
    subscription_plan_id = CharField(blank=True, null=True, max_length=20)
    subscription_status = CharField(blank=True, null=True, max_length=20)
    next_bill_date = DateField(blank=True, null=True)
    cancellation_effective_date = DateField(blank=True, null=True)

    payment_method = CharField(blank=True, null=True, max_length=20)
    plan_name = CharField(blank=True, null=True, max_length=30)
    receipt_url = CharField(blank=True, null=True, max_length=400)
    amount = FloatField(blank=True, null=True)

    @classmethod
    def profile_receipts(cls, profile):
        return cls.objects.filter(profile=profile, event_subtype='payment_succeeded').order_by("-id")

class SignupToken(HashedModel):

    token = CharField(max_length=200)
    valid = BooleanField(default=True)

class Project(HashedModel):
    """
    Project Type is used to detect the templates, for now the intro template
    """
    HUMAN_FORMAT = "%b %d, %Y"
    TIME_TARGET_TYPES = ['daily', 'weekly', 'monthly']
    TIME_TARGET_CHOICES = [(str(i), _type) for i, _type in enumerate(['day', 'week', 'month', 'year'])]

    name = CharField(max_length=200)
    description = CharField(max_length=200)
    deadline = DateField(null=True, blank=True)
    user = ForeignKey(Profile, on_delete=models.CASCADE, related_name='projects')

    project_type = CharField(max_length=50, default='normal')
    log_start = DateTimeField(null=True, blank=True, default=None)

    time_target_duration = FloatField(null=True, blank=True, default=None)
    time_target_type = CharField(max_length=20, choices=TIME_TARGET_CHOICES, null=True, blank=True, default=None)

    @classmethod
    def get_personal_project(cls, profile, project_id):
        return cls.objects.get(user=profile, id=project_id)

    @classmethod
    def get_by_id(cls, project_id):
        return cls.objects.get(pk=project_id)

    def add_tags(self, raw_tags):
        for raw_name in raw_tags:
            tag_name = str(raw_name).lower()
            ProjectTag.objects.create(name=tag_name, project=self, user=self.user)

    def deadline_str(self):
        if self.deadline:
            return strftime(self.HUMAN_FORMAT, self.deadline.timetuple())
        else:
            return ''

    def add_event(self, start_date=None, end_date=None, title=None, description=''):
        event = ProjectEvent(title=title, description=description)
        event.start = start_date
        if end_date:
            event.end = end_date
        event.project = self
        event.save()

    def copy_pages(self, new_project):
        for page in self.pages.all():
            page.project = new_project
            page.pk = None
            page.save()

    def copy_events(self, new_project):
        for event in self.events.all():
            event.project = new_project
            event.pk = None
            event.save()

    def copy_tasks(self, new_project):
        for todo_list in self.todo_lists.all():
            new_list = ProjectTodoList(title=todo_list.title, project=new_project)
            new_list.save()
            i=1
            for task in todo_list.todos.all():
                task.pk = None
                task.project_list = new_list
                task.project_list_order = i
                task.save()
                i += 1

    def duplicate(self, new_project):
        self.copy_pages(new_project)
        self.copy_events(new_project)
        self.copy_tasks(new_project)


class ProjectTodoItemState(Model):

    name = CharField(max_length=30)
    project = ForeignKey(Project, db_index=True, on_delete=models.CASCADE, related_name='project_todo_states')
    order = FloatField()
    item_state = IntegerField()

    @classmethod
    def update_index(cls, list_id, new_index):
        cls.objects.filter(pk=list_id).update(order=new_index)

    @classmethod
    def update_by_id(cls, list_id, **kwargs):
        cls.objects.filter(pk=list_id).update(**kwargs)

    @classmethod
    def get_by_project(cls, project_id):
        return cls.objects.filter(project_id=project_id).order_by('order').all()

    @classmethod
    def create_defaults(cls, project_id):
        todo = cls.objects.create(name="To do", project_id=project_id, order=1, item_state=0)
        doing = cls.objects.create(name="In progress", project_id=project_id, order=2, item_state=1)
        done = cls.objects.create(name="Done", project_id=project_id, order=5, item_state=5)
        return [todo, doing, done]

    @classmethod
    def create_new(cls, project_id, name, list_state, order=None):
        new_list = cls(project_id=project_id, name=name, item_state=list_state)
        new_list.order = order or list_state
        new_list.save()
        return new_list

class ProjectTag(HashedModel):

    name = CharField(max_length=30, db_index=True)
    user = ForeignKey(Profile, on_delete=models.CASCADE, related_name='user_project_tags')
    project = ForeignKey(Project, db_index=True, on_delete=models.CASCADE, related_name='project_tags')

    class Meta:
        unique_together = ('name', 'project',)

    @classmethod
    def user_tags(cls, profile):
        tags_set = set([t.name for t in cls.objects.filter(user=profile).all()])
        return list(tags_set)

class SortableMixin:

    SORT_CRITERIA = [
        (1, 'Age (New-Old)'),
        (2, 'Age (Old-New)'),
        (3, 'Name (A-Z)'),
        (4, 'Name (Z-A)'),
    ]

    CRITERIA_MAP = {
        '1': '-created_on',
        '2': 'created_on',
        '3': 'name',
        '4': '-name'
    }

    @classmethod
    def get_sorted(cls, criteria, **kwargs):
        sort_criteria = cls.CRITERIA_MAP[criteria]
        return cls.objects.filter(**kwargs).order_by(sort_criteria)

class ProjectPage(TimestampedModel, SortableMixin):

    CRITERIA_MAP = {
        '1': '-created_on',
        '2': 'created_on',
        '3': 'title',
        '4': '-title'
    }

    title = CharField(max_length=200)
    content = TextField()
    project = ForeignKey(Project, on_delete=models.CASCADE, related_name='pages')

    def get_title(self):
        return self.title

    def get_description(self):
        return self.content[:50]

    def get_type(self):
        return 'project-page'

class ProjectPageImage(HashedModel):
    image = ImageField(upload_to='project_images')
    name = CharField(max_length=128)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.FloatField()
    page = models.ForeignKey(ProjectPage, on_delete=models.CASCADE, related_name='images')


def update_filename(resource, filename):
    return utils.filename_for_storage(resource.project.user_id, filename)


class ProjectResource(TimestampedModel, SortableMixin):

    MAX_FILE_SIZE_MB = 20

    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    the_file = models.FileField()
    extension = models.CharField(max_length=10)
    file_size = models.FloatField()
    project = ForeignKey(Project, on_delete=models.CASCADE, related_name='resources')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generated_url = None


    def to_dict(self):
        return {
            'id': self.id,
            'name': self.display_name,
            'file_url': self.file_url,
            'extension': self.extension,
            'file_size': self.human_size(),
            'created': self.created_on.strftime(utils.HUMAN_FORMAT)
        }

    def is_image(self):
        return self.extension in ['jpg', 'jpeg', 'gif', 'png', 'tif', 'tiff', 'bmp']

    @property
    def file_url(self):
        if not self.generated_url:
            self.generated_url = self.the_file.url
        return self.generated_url

    @classmethod
    def get_by_project(cls, project_id):
        return cls.objects.filter(project_id=project_id)

    def get_title(self):
        return self.display_name

    def get_description(self):
        if self.is_image():
            description = "<img class=\"card-image\" src=\"{}\">".format(self.file_url)
        else:
            description = "<i class=\"fas fa-file\"></i>"
        return description

    def human_size(self):
        kb_mul =  1e-3
        mb_mul =  1e-6
        kb_size = self.file_size * kb_mul
        if kb_size > 1000:
            mb_size = self.file_size * mb_mul
            return "{} MB".format(round(mb_size, 2))
        else:
            return "{} KB".format(int(kb_size))

    def get_type(self):
        return 'project-resource'

class TodoList(HashedModel):
    """
    itemsOrder is a string used for keeping order of
    """
    title = CharField(max_length=500)
    itemsOrder = CharField(max_length=1000)

    class Meta:
        abstract = True

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title
        }

    def change_order(self, itemId, n_index):
        order_list = self.itemsOrder.split(",")
        itemId = str(itemId)
        try:
            order_list.remove(itemId)
        except ValueError:
            pass
        order_list.insert(n_index, itemId)
        self.itemsOrder = ",".join(order_list)
        self.save()

    def remove_from_order(self, itemId):
        order_list = self.itemsOrder.split(",")
        try:
            order_list.remove(str(itemId))
            self.itemsOrder = ",".join(order_list)
            self.save()
        except ValueError:
            pass

    def remove_todo(self, item):
        self.remove_from_order(item.id)
        item.delete()


class ProjectTodoList(TodoList):
    priority = IntegerField(blank=True, null=True)
    project = ForeignKey(Project, on_delete=models.CASCADE, related_name='todo_lists')
    archived = BooleanField(default=False)

    @classmethod
    def get_tasks_for_list(cls, list_id):
        return cls.objects.get(pk=list_id).todos.all()


class PersonalTodoList(TodoList):

    IMPORTANT = 1
    URGENT = 2
    EXTRA = 3

    PRIORITIES_MAP = {
        1: 'important-list',
        2: 'secondary-list',
        3: 'extra-list'
    }

    PRIORITIES = {
        'important-list': 1,
        'secondary-list': 2,
        'extra-list': 3
    }

    DAY_LIST_PRIORITY = 7

    priority = IntegerField(blank=True, null=True)
    user = ForeignKey(Profile, on_delete=models.CASCADE, related_name='todo_lists')

    @classmethod
    def get_important_list(cls, profile):
        return cls.objects.get(user=profile, priority=cls.IMPORTANT)

    @classmethod
    def get_today_list(cls, profile):
        DAY = "%A"
        users_today = user_time_now(profile.utc_offset)
        day_name = users_today.strftime(DAY)
        return cls.objects.filter(user=profile, priority=cls.DAY_LIST_PRIORITY, title=day_name).first()


    @classmethod
    def sync_week_planner_today(cls, profile):
        important_list = cls.get_important_list(profile)
        today_tasks = ProjectTodoItem.get_profile_today_tasks(profile)
        synced_count = 0
        if today_tasks.count():
            last_important_todo = important_list.personal_todos.filter(completed=False).order_by('-personal_list_order').first()
            if last_important_todo:
                last_index = last_important_todo.personal_list_order
            else:
                last_index = 0
            for todo in today_tasks:
                if not todo.personal_list_id:
                    todo.personal_list_id = important_list
                    last_index += 1
                    todo.personal_list_order = last_index
                    todo.added_to_master = True
                    todo.save()
                    synced_count += 1
            return synced_count
        else:
            return -1

    @classmethod
    def profile_has_day_lists(cls, profile):
        return cls.objects.filter(user=profile, priority=cls.DAY_LIST_PRIORITY).count() > 0

    @classmethod
    def get_week_lists(cls, profile):
        return cls.objects.filter(user=profile, priority=PersonalTodoList.DAY_LIST_PRIORITY).order_by('id')

class TodoItem(HashedModel):
    title = CharField(max_length=300)
    completed = BooleanField(default=False)
    completed_on = DateTimeField(blank=True, null=True)
    description = CharField(max_length=500, default='')
    minutes_worked_today = IntegerField(default=0)
    created_on = DateTimeField(auto_now_add=True)
    due_date = DateTimeField(null=True, blank=True)
    user = ForeignKey(Profile, on_delete=models.CASCADE, related_name='profile_todos', blank=True, null=True)
    # priority, weight, important, urgent

    class Meta:
        abstract = True

    def to_dict(self, full=False):
        response = {
            'id': self.id,
            'title': self.title,
            'completed': self.completed,
            'completed_on': self.completed_on,
            'minutes_worked_today': self.minutes_worked_today
        }
        if full:
            response['description'] = self.description
        return response

    @classmethod
    def get_by_id(cls, the_id):
        return cls.objects.filter(pk=the_id).first()

class ProjectTodoItem(TodoItem):
    TODO = 0
    DOING = 1
    DONE = 5
    """
    Status:
        0 - to do
        1 - doing
        5 - done
    Priority:
        0 - low
        1 - normal
        2 - high
    """

    project_list = ForeignKey(ProjectTodoList, on_delete=models.CASCADE, related_name='todos', null=True)
    personal_list = ForeignKey(PersonalTodoList, on_delete=models.SET_NULL, related_name='personal_todos', null=True)
    day_list = ForeignKey(PersonalTodoList, on_delete=models.SET_NULL, related_name='day_todos', null=True)

    project_list_order = FloatField(null=True)
    personal_list_order = FloatField(null=True)
    day_list_order = FloatField(null=True)

    added_to_master = BooleanField(default=False)
    planned = DateField(null=True, blank=True)

    priority = IntegerField(default=1)
    status = IntegerField(default=0)

    @classmethod
    def get_completed_tasks_by_user_by_date(cls, profile, completed_date):
        return ProjectTodoItem.objects.filter(user=profile, completed=True, completed_on__contains=completed_date)

    @classmethod
    def this_week_tasks(cls, profile, week_start):
        week_end = week_start + datetime.timedelta(days=6)
        return cls.objects.filter(user=profile, due_date__gte=week_start, due_date__lte=week_end, completed=False)\
            .annotate(project_name=F('project_list__project__name'), project_id=F('project_list__project__id')) \
            .order_by('due_date')

    @classmethod
    def get_active_master_tasks(cls, profile):
        return cls.objects.filter(user=profile, personal_list_id__gt=0, completed=False) \
        .annotate(project_name=F('project_list__project__name'), project_id=F('project_list__project__id')) \
        .order_by('due_date')

    @classmethod
    def get_profile_today_tasks(cls, profile):
        profile_today = user_time_now(profile.utc_offset).date()
        today_datetime = datetime.datetime.combine(profile_today, datetime.time())
        return cls.objects.filter(user=profile, due_date=today_datetime, completed=False)

    def to_dict(self, extras=None, full=False):
        response = super(ProjectTodoItem, self).to_dict(full)
        response['project_list_id'] = self.project_list_id
        response['personal_list_id'] = self.personal_list_id
        response['project_list_order'] = self.project_list_order
        response['personal_list_order'] = self.personal_list_order
        if extras:
            for key, value in extras.items():
                response[key] = value
        return response

    def update_kanban_status(self, new_status):
        self.status = int(new_status)
        if new_status == self.DONE:
            self.complete_now()
        elif new_status != self.DONE and self.completed:
            self.completed = False
            self.completed_on = None
        self.save()

    @classmethod
    def set_in_progress(cls, item_id):
        cls.objects.filter(pk=item_id).update(status=cls.DOING)

    @classmethod
    def get_by_project(cls, project_id):
        # todo, in cron transfer archived to different table, takes up space for nothing
        return cls.objects.filter(project_list__project_id=project_id, project_list__archived=False)

    @classmethod
    def get_by_project_with_list_name(cls, project_id):
        return cls.objects.filter(project_list__project_id=project_id, project_list__archived=False).annotate(list_name=F('project_list__title'))

    @classmethod
    def status_grouped_by_project(cls, project_id, task_states):
        project_tasks = cls.get_by_project_with_list_name(project_id)
        grouped = dict()
        for task_state in task_states:
            grouped[task_state.item_state] = list()
        for task in project_tasks:
            if task.completed:
                grouped[cls.DONE].append(task)
            else:
                grouped[task.status].append(task)
        return grouped

    @classmethod
    def last_active_from_list(cls, project_list_id):
        return cls.objects.filter(project_list_id=project_list_id, completed=False).order_by('-project_list_order').first()

    @classmethod
    def personal_todos_today(cls, profile, profiles_today):
        todos = cls.objects.filter(personal_list__isnull=False, personal_list__user=profile, completed=False)
        completed_today = cls.objects.filter(personal_list__isnull=False, personal_list__user=profile, completed=True, completed_on__gte=profiles_today)
        return todos, completed_today

    @classmethod
    def update_minutes_worked(cls, item_id, total_minutes_worked):
        cls.objects.filter(pk=item_id).update(minutes_worked_today=total_minutes_worked, status=cls.DOING)

    @classmethod
    def add_minutes_worked(cls, item_id, more_minutes_worked):
        cls.objects.filter(pk=item_id).update(minutes_worked_today=F('minutes_worked_today') + more_minutes_worked)

    @classmethod
    def tasks_worked_today(cls, profile):
        project_tasks = cls.objects.filter(minutes_worked_today__gt=0, project_list__project__user=profile)
        personal_tasks = cls.objects.filter(minutes_worked_today__gt=0, project_list=None, personal_list__user=profile)
        return project_tasks, personal_tasks

    @classmethod
    def project_tasks_worked_today(cls, project):
        return cls.objects.filter(minutes_worked_today__gt=0, project_list__project=project)

    @classmethod
    def project_tasks_worked_today_sum(cls, project):
        total_worked = cls.objects.filter(minutes_worked_today__gt=0, project_list__project=project).aggregate(Sum('minutes_worked_today'))
        return total_worked['minutes_worked_today__sum'] or 0

    @classmethod
    def personal_tasks_worked_today(cls, profile):
        return cls.objects.filter(minutes_worked_today__gt=0, project_list=None, personal_list__user=profile)

    @classmethod
    def personal_tasks_worked_today_sum(cls, profile):
        total_worked = cls.objects.filter(minutes_worked_today__gt=0, project_list=None, personal_list__user=profile).aggregate(Sum('minutes_worked_today'))
        return total_worked['minutes_worked_today__sum'] or 0

    @classmethod
    def get_personal_tasks_for_stats(cls, profile, since):
        return cls.objects.filter(Q(completed_on=None) | Q(completed_on__gte=since), project_list=None, personal_list__user=profile)

    def complete_now(self, completed_time=None):
        self.completed = True
        if completed_time:
            self.completed_on = completed_time
        else:
            self.completed_on = datetime.datetime.utcnow()
        self.status = self.DONE
        self.save()


class CalendarEvent(HashedModel):
    title = CharField(max_length=200)
    description = CharField(max_length=400, default='')
    start = DateTimeField()
    end = DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True


class ProjectEvent(CalendarEvent):
    project = ForeignKey(Project, on_delete=models.CASCADE, related_name='events')

    def to_json(self):
        response = {
            'title': self.title,
            'description': self.description,
            'start': self.start,
            'type': 'project',
            'id': self.id,
            'project_id': self.project_id
        }
        if self.end:
            response['end'] = self.end
        return response


class ProjectLog(HashedModel):
    project = ForeignKey(Project, on_delete=models.CASCADE, related_name='logs')
    start = DateTimeField()
    end = DateTimeField()


class WorkCycleGroup(HashedModel):

    cycles_num = IntegerField()
    work_duration = CharField(max_length=10)
    break_duration = CharField(max_length=10)
    question_what = CharField(max_length=300)
    question_how = CharField(max_length=300)
    user = ForeignKey(Profile, on_delete=models.CASCADE, related_name='cycle_groups')
    created_at = DateTimeField(auto_now_add=True)
    project = ForeignKey(Project, related_name='project_groups', blank=True, null=True, on_delete=models.SET_NULL)
    finished = BooleanField(default=False)

    def html_context(self, cycles=None):
        response = {
            "workDuration": int(self.work_duration) * 60,
            "breakDuration": int(self.break_duration) * 60,
            "cyclesCount": self.cycles_num,
            "workMin": self.work_duration,
            "breakMin": self.break_duration,
            "objective": self.question_what
        }
        if cycles:
            response['cycles'] = cycles
        else:
            response['cycles'] = [c for c in self.cycles.all().order_by('id')]
        response['active_cycle_id'] = self.active_cycle_index(response['cycles'])
        return response

    @staticmethod
    def active_cycle_index(cycles):
        ind = 0
        for cycle in cycles:
            if not cycle.finished:
                return ind
            else:
                ind += 1
        return ind

    def finish(self):
        self.finished = True
        self.save()

    def cycles_ids(self):
        return self.cycles.values_list('pk', flat=True)

    @classmethod
    def get_past_sessions(cls, profile):
        return cls.objects.filter(user=profile, finished=False).order_by('-created_at')

    @classmethod
    def get_users_day(cls, profile, day_start):
        day_end = day_start + datetime.timedelta(days=1)
        return cls.objects.filter(user=profile, created_at__gte=day_start, created_at__lt=day_end)

    @classmethod
    def get_users_week(cls, profile, week_start):
        week_end = week_start + datetime.timedelta(days=7)
        return cls.objects.filter(user=profile, created_at__gte=week_start, created_at__lt=week_end)

    @classmethod
    def get_projects_day(cls, project_id, day_start):
        day_end = day_start + datetime.timedelta(days=1)
        return cls.objects.filter(project_id=project_id, created_at__gte=day_start, created_at__lt=day_end)

    @classmethod
    def get_projects_week(cls, project_id, week_start):
        week_end = week_start + datetime.timedelta(days=7)
        return cls.objects.filter(project_id=project_id, created_at__gte=week_start, created_at__lt=week_end)


    def total_work_duration(self):
        return int(self.work_duration) * self.cycles_num

class GetterMixin:

    @classmethod
    def by_id(cls, id):
        return cls.objects.get(pk=id)


class WorkCycle(HashedModel, GetterMixin):

    REV_SUCCESS_MAP = {
        2: 'yes',
        1: 'half',
        0: 'no'
    }

    REV_ENERGY_MAP = {
        2: 'high',
        1: 'medium',
        0: 'low'
    }

    SUCCESS_MAP = {
        'yes': 2,
        'half': 1,
        'no': 0
    }
    ENERGY_MAP = {
        'high': 2,
        'medium': 1,
        'low': 0
    }
    FIELDS_MAP = {
        'whatAnswer': 'what_answer',
        'howStartAnswer': 'how_startanswer',
        'blockerAnswer': 'blocker_answer',
        'reviewAnswer': 'review_answer',
        'finishedAnswer': 'success'
    }

    cycle_group = ForeignKey(WorkCycleGroup, on_delete=models.CASCADE, related_name='cycles')
    what_answer = CharField(max_length=150)
    how_startanswer = CharField(max_length=150)
    blocker_answer = CharField(max_length=150)
    review_answer = CharField(max_length=200)
    success = IntegerField(blank=True, null=True)
    energy = IntegerField(blank=True, null=True)
    finished = BooleanField(default=False)

    def update_from(self, new_data):
        for field, value in new_data.items():
            setattr(self, self.FIELDS_MAP[field], value)
        self.save()

    def update_review(self, data):
        energy = self.ENERGY_MAP[data['energy']]
        success = self.SUCCESS_MAP[data['done']]
        self.success = success
        self.energy = energy
        self.review_answer = data['review']
        self.finished = True
        self.save()

    @property
    def energy_human(self):
        return self.REV_ENERGY_MAP.get(self.energy, "")

    @property
    def success_human(self):
        return self.REV_SUCCESS_MAP.get(self.success, "")

    def review_dict(self):
        return {
            'done': self.REV_SUCCESS_MAP.get(self.success),
            'energy': self.REV_ENERGY_MAP.get(self.energy),
            'finished': self.finished
        }

class OnboardEvents(HashedModel):

    """
    Char fields will have values :user or :email depending on who created the event
    If it is email, when user really creates it I'll append user coming out as :email:user
    So possible values are:  :user, :email, :email:user
    Date fields record when the even happened
    """

    ONBOARD_SEND_TIME = 14

    user = ForeignKey(Profile, on_delete=models.CASCADE, related_name='onboard_events')
    journal = CharField(max_length=20, blank=True, null=True)
    journal_date = DateTimeField(blank=True, null=True)

    project = CharField(max_length=20, blank=True, null=True)
    project_date = DateTimeField(blank=True, null=True)

    plan = CharField(max_length=20, blank=True, null=True)
    plan_date = DateTimeField(blank=True, null=True)

    work = CharField(max_length=20, blank=True, null=True)
    work_date = DateTimeField(blank=True, null=True)

    habits = CharField(max_length=20, blank=True, null=True)
    habits_date = DateTimeField(blank=True, null=True)

    daily_mission = CharField(max_length=20, blank=True, null=True)
    daily_mission_date = DateTimeField(blank=True, null=True)

    discount_1 = CharField(max_length=20, blank=True, null=True)
    discount_1_date = DateTimeField(blank=True, null=True)

    discount_2 = CharField(max_length=20, blank=True, null=True)
    discount_2_date = DateTimeField(blank=True, null=True)

    last_sent = DateTimeField(blank=True, null=True)
    onboard_canceled = BooleanField(default=False)
    sales_canceled = BooleanField(default=False)
    signup_date = DateTimeField(default=datetime.datetime.utcnow)
    onboard_finished = BooleanField(default=False)

    @classmethod
    def sale_to_send(cls, user_joined, trial_end_date, user_now, profile_type):
        if user_now.hour != cls.ONBOARD_SEND_TIME:
            return None
        now_date = user_now.date()
        joined_date = user_joined.date()
        if profile_type == Profile.BETA_USER:
            if now_date - joined_date == datetime.timedelta(days=10):
                return "discount_beta"
            elif trial_end_date - now_date == datetime.timedelta(days=5):
                return "beta_trial_expires_1"
            elif trial_end_date - now_date == datetime.timedelta(days=2):
                return "beta_trial_expires_2"
        else:
            if now_date - joined_date == datetime.timedelta(days=10):
                return "discount_1"
            elif now_date - joined_date == datetime.timedelta(days=12):
                return "discount_2"
            elif trial_end_date - now_date == datetime.timedelta(days=5):
                return "trial_expires_1"
            elif trial_end_date - now_date == datetime.timedelta(days=2):
                return "trial_expires_2"
            else:
                return None

    def too_early(self, last_sent, now_date):
        return now_date - last_sent < datetime.timedelta(days=2)

    def next_to_send(self, user_now):
        if self.last_sent and self.too_early(self.last_sent.date(), user_now.date()):
            return None
        if user_now.hour < self.ONBOARD_SEND_TIME:
            return None

        if not self.project:
            return "project"
        elif not self.plan:
            return "plan"
        elif not self.work:
            return "work"
        elif not self.journal:
            return "journal"
        elif not self.habits:
            return "habits"
        # elif not self.daily_mission:
        #     return "daily_mission"
        self.onboard_finished = True
        return None

    def record_sending(self, type_sent, user_now, profile_type=None):
        self.last_sent = user_now
        beta_fields_map = {
            "discount_beta": "discount_1",
            "beta_trial_expires_1": "trial_expires_1",
            "beta_trial_expires_2": "trial_expires_2"
        }
        if profile_type == Profile.BETA_USER:
            beta_type_sent = beta_fields_map[type_sent]
            setattr(self, beta_type_sent, ":email")
            date_field = "{}_date".format(beta_type_sent)
            setattr(self, date_field, user_now)
        else:
            setattr(self, type_sent, ":email")
            date_field = "{}_date".format(type_sent)
            setattr(self, date_field, user_now)
        self.save()

