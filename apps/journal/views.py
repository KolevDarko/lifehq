import json

from account.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from django.urls import reverse
from django.views import View

from apps.base.views import CustomLoginRequiredMixin
from apps.common.analytics_client import AnalyticsManager, JOURNAL
from apps.common.views import MyJsonResponse
from apps.journal.models import JournalEntry, Journal, JournalTemplate
from mastermind.utils import user_time_now

JsonResponse = MyJsonResponse

class CreateJournalEntry(CustomLoginRequiredMixin, View):

    def get(self, request, entry_type):
        print("we out here")
        if entry_type not in JournalEntry.JOURNAL_TYPES:
            return HttpResponse(status=401, content="Entry type invalid")
        profile = self.profile(request)
        user_journal = Journal.objects.get(user=profile)
        user_date = user_time_now(profile.utc_offset).date()
        the_entry = JournalEntry.create_from_template(entry_type, user_journal.id, user_date_now=user_date)
        self.update_daily_success('journals', todo=1)
        return redirect('journal-entry', entry_id=the_entry.id)


class JournalIds(CustomLoginRequiredMixin, View):

    def get(self, request):
        journal = Journal.objects.get(user=self.profile(request))
        all_entries = journal.entries.order_by('id')
        ids = [e.id for e in all_entries]
        return JsonResponse({'ids': ids})


class JournalHome(CustomLoginRequiredMixin, View):

    def get(self, request, entry_id=None):
        profile = self.profile(request)
        journal = Journal.objects.get(user=profile)
        all_entries = journal.entries.order_by('-id')

        review_entry = JournalEntry()
        last_id = 0
        if all_entries:
            review_entry = all_entries[0]
            last_id = review_entry.id
        if entry_id:
            the_entry = JournalEntry.get_by_id(entry_id, self.profile(request))
        else:
            if all_entries:
                the_entry = all_entries[0]
            else:
                the_entry = JournalEntry()
        first_journal = ''
        if profile.first_journal:
            first_journal = 'true'
            profile.first_journal = False
            profile.save()
        return render(request, "journal/journal_home.html",
                      {'journal': journal, 'all_entries': all_entries, 'the_entry': the_entry,
                       'review_entry': review_entry, 'last_id': last_id, 'active_journal': True,
                       'first_journal': first_journal})

    def post(self, request, entry_id=None):
        if entry_id:
            entry = self.update(request, entry_id)
        else:
            entry = self.create(request)
        return redirect('journal-entry', entry_id=entry.id)

    def update(self, request, entry_id):
        entry = JournalEntry.objects.get(pk=entry_id)
        data = request.POST
        if 'journalEntryContent' in data:
            entry.content = data['journalEntryContent']
        if 'title' in data:
            entry.title = data['title']
        entry.save()
        return entry

    def create(self, request):
        entry = JournalEntry()
        entry.save()
        entry.title = "Day {}".format(entry.id)
        entry.save()
        return entry

class JournalEntryJson(CustomLoginRequiredMixin, View):

    def get(self, request, entry_id):
        entry = JournalEntry.objects.filter(pk=entry_id, journal__user=self.profile(request)).first()
        return JsonResponse({"title": entry.title, "content": entry.content})

    def post(self, request, entry_id):
        data = json.loads(request.body.decode())
        the_entry = JournalEntry.get_by_id(entry_id, self.profile(request))
        if 'content' in data:
            the_entry.content = data['content']
            the_entry.done = True
            self.update_daily_success('journals', done=1)
        if 'title' in data:
            the_entry.title = data['title']
        the_entry.save()
        AnalyticsManager.record(self.user_id, JOURNAL)
        return JsonResponse({"success": True})

    def delete(self, request, entry_id):
        the_entry = JournalEntry.get_by_id(entry_id, self.profile(request))
        if not the_entry.done:
            self.update_daily_success('journals', todo=-1)
        the_entry.delete()
        journal_home = reverse('journal')
        return JsonResponse({"success": True, "location": journal_home})


class Schedule(LoginRequiredMixin, View):

    def parse_checkbox(self, data, key):
        if data.get(key):
            return True
        else:
            return False

    def post(self, request, journal_id):
        data = json.loads(request.body.decode())
        journal = Journal.objects.get(pk=journal_id)
        journal.day = self.parse_checkbox(data, 'day')
        journal.week = self.parse_checkbox(data, 'week')
        journal.month = self.parse_checkbox(data, 'month')
        journal.quarter = self.parse_checkbox(data, 'quarter')
        journal.year = self.parse_checkbox(data, 'year')
        journal.save()
        return JsonResponse({'success': True})


class JournalTemplates(CustomLoginRequiredMixin, View):

    def get(self, request, journal_id):
        profile = self.profile(request)
        journal = Journal.objects.get(pk=journal_id, user=profile)
        templates_map = {}
        for _temp in journal.templates.all():
            templates_map[_temp.template_type] = _temp.content
        first_journal_template = ""
        if profile.first_journal_template:
            first_journal_template = "true"
            profile.first_journal_template = False
            profile.save()

        return render(request, "journal/journal_templates.html", {'templates': templates_map, 'journal': journal,
                                                                  'active_journal': True,
                                                                  'first_journal_template': first_journal_template})

    def group_templates(self, journal_id):
        results = {}
        journalTemplates = JournalTemplate.objects.filter(journal_id=journal_id)
        for journal_template in journalTemplates:
            this_template_type = JournalTemplate.TEMPLATE_TYPES_LIST[int(journal_template.template_type)]
            results[this_template_type] = journal_template
        return results

    def post(self, request, journal_id):
        post_data = json.loads(request.body.decode())
        db_templates = self.group_templates(journal_id)
        for template_type, new_content in post_data.items():
            if template_type in db_templates:
                db_template = db_templates[template_type]
                db_template.content = new_content
            else:
                db_template = JournalTemplate(
                    journal_id=journal_id,
                    template_type=JournalTemplate.TEMPLATE_TYPES_MAP[template_type],
                    content=new_content
                )
            db_template.save()
        return JsonResponse({'success': True})
