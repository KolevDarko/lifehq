import datetime

# Create your models here.
from django.db import models
from django.db.models import CharField, TextField, DateField, BooleanField, ForeignKey

from apps.base.models import Profile
from apps.common.models import HashedModel


class Journal(HashedModel):

    day = BooleanField(default=True)
    week = BooleanField(default=True)
    month = BooleanField(default=True)
    quarter = BooleanField(default=False)
    year = BooleanField(default=True)
    user = ForeignKey(Profile, on_delete=models.CASCADE)

    @classmethod
    def get_user_journal(cls, user_id):
        return cls.objects.get(user_id=user_id)

    def get_review_journal(self, is_enabled, entry_type, container):
        if is_enabled:
            last_entry = self.entries.filter(entry_type=JournalEntry.JOURNAL_TYPES[entry_type]).order_by('-id').first()
            if last_entry:
                container.append(last_entry)

    def get_last_for_review(self):
        review_journals = list()
        self.get_review_journal(self.week, JournalEntry.WEEK, review_journals)
        self.get_review_journal(self.month, JournalEntry.MONTH, review_journals)
        self.get_review_journal(self.year, JournalEntry.YEAR, review_journals)
        return review_journals

    def get_todays(self, user_today):
        return self.entries.filter(created_on__gte=user_today)


class JournalEntry(HashedModel):

    DAY = 'day'
    WEEK = 'week'
    MONTH = 'month'
    YEAR = 'year'
    JOURNAL_TYPES = {
        DAY: 0,
        WEEK: 1,
        MONTH: 2,
        YEAR: 3
    }

    JOURNAL_TYPES_REV_MAP = {
        '0': DAY,
        '1': WEEK,
        '2': MONTH,
        '3': YEAR
    }
    title = CharField(max_length=200)
    content = TextField()
    done = BooleanField(default=False)

    entry_type = CharField(max_length=20)
    created_on = DateField(default=datetime.date.today)
    journal = ForeignKey(Journal, on_delete=models.CASCADE, related_name='entries')

    @classmethod
    def get_by_id(cls, model_id, user):
        return cls.objects.filter(id=model_id, journal__user=user).first()

    @property
    def name(self):
        return self.JOURNAL_TYPES_REV_MAP[self.entry_type].capitalize()

    @classmethod
    def get_done_entries_by_day_by_user(cls, _date, _user):
        return cls.objects.filter(created_on=_date, journal__user=_user, done=True)

    @classmethod
    def create_from_template(cls, str_entry_type, journal_id, title='', user_date_now=None):
        obj = JournalEntry()
        entry_type = cls.JOURNAL_TYPES[str_entry_type]
        obj.entry_type = entry_type
        obj.journal_id = journal_id
        template_content = JournalTemplate.get_content(journal_id, entry_type)
        obj.content = template_content
        if user_date_now:
            date_now = user_date_now
        else:
            date_now = datetime.date.today()
        if title:
            obj.title = title
        else:
            obj.title = str(str_entry_type).capitalize() + " - " + date_now.strftime("%a, %b %d")
        obj.created_on = date_now
        obj.save()
        return obj

class JournalTemplate(HashedModel):

    TEMPLATE_TYPES_MAP = {
        'day': '0',
        'week': '1',
        'month': '2',
        'year': '3',
    }
    TEMPLATE_TYPES_LIST = ['day', 'week', 'month', 'year']
    TEMPLATE_CHOICES = [(str(i), _type) for i, _type in enumerate(['day', 'week', 'month', 'year'])]

    template_type = CharField(max_length=20, choices=TEMPLATE_CHOICES)
    content = TextField()
    journal = ForeignKey(Journal, on_delete=models.CASCADE, related_name='templates')

    @classmethod
    def get_content(cls, journal_id, entry_type):
        j_template = cls.objects.filter(journal_id=journal_id, template_type=entry_type).first()
        if j_template:
            return j_template.content
        else:
            return ''

    @classmethod
    def copy_templates(cls, template_journal, new_journal):
        for default_template in template_journal.templates.all():
            new_template = JournalTemplate(
                journal=new_journal,
                template_type=default_template.template_type,
                content=default_template.content
            )
            new_template.save()

    @classmethod
    def empty_templates(cls, new_journal):
        for template_type in cls.TEMPLATE_TYPES_LIST:
            new_template = JournalTemplate(
                journal=new_journal,
                template_type=template_type
            )
            new_template.save()

