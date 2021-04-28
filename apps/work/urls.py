from .views import TrackTodoItemManual, TrackTodoItem, PersonalTasks, PomodoroSetupPartial
from django.conf.urls import url

urlpatterns = [
    url(r"^todos/item/track/(?P<item_id>\w+)/manual$", TrackTodoItemManual.as_view()),
    url(r"^todos/item/track/(?P<item_id>\w+)$", TrackTodoItem.as_view()),
    url(r"^todos/personal$", PersonalTasks.as_view()),
    url(r"^pomodoro/setup$", PomodoroSetupPartial.as_view()),
]
