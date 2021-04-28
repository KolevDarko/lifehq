from django.conf.urls import url

from .views import HabitsHome, HabitView, HabitActionView, HabitsReset

urlpatterns = [
    url(r'^$', HabitsHome.as_view(), name='habits-home'),
    url(r'habit$', HabitView.as_view(), name='habits-habit'),
    url(r'action$', HabitActionView.as_view(), name='habits-action'),
    url(r'reset-week$', HabitsReset.as_view(), name='habits-reset'),

    # url(r'entry/create/(?P<entry_type>[a-z]+)$', CreateJournalEntry.as_view(), name='journal-create'),
]
