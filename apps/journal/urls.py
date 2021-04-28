from django.conf.urls import url

from .views import JournalHome, JournalEntryJson, Schedule, JournalTemplates, CreateJournalEntry, JournalIds

urlpatterns = [
    url(r'^$', JournalHome.as_view(), name='journal'),
    url(r'entry/create/(?P<entry_type>\w+)$', CreateJournalEntry.as_view(), name='journal-create'),
    url(r'entry/(?P<entry_id>\w+)$', JournalHome.as_view(), name='journal-entry'),
    url(r'entry$', JournalHome.as_view(), name='journal-entry'),
    url(r'entry/ajax/(?P<entry_id>\w+)$', JournalEntryJson.as_view(), name='entry-ajax'),
    url(r'schedule/(?P<journal_id>\w+)$', Schedule.as_view(), name='save-schedule'),
    url(r'templates/(?P<journal_id>\w+)$', JournalTemplates.as_view(), name='journal-templates'),
    url(r'ids$', JournalIds.as_view(), name='journal-ids'),
]
