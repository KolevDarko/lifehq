"""urlconf for the base application"""

from account.views import ChangePasswordView, PasswordResetView, PasswordResetTokenView, LogoutView, DeleteView
from django.conf.urls import url

from .views import HomeView, Projects, ProjectPageView, TodosPage, ProjectSchedulePage, ProjectTodoItemView, \
    CompleteTodoItem, \
    ReorderTodoItemProject, ReloadTodoList, SignupView, LoginView, ProjectEventView, MasterTodo, \
    ReloadProjectTodoListsPreview, \
    TransferItemToMaster, ReloadProjectTodoLists, DeleteProjectTodoItem, \
    ArchiveDeleteProjectTodoList, CompleteMasterItem, MySettingsView, TodosArchivedPage, \
    ProjectLogView, ProjectPageImageView, ConfirmEmailView, TokenWall, ProjectsTagFiltered, \
    ProjectTagView, ProjectTagDelete, RemindersView, SetTimezoneView, GeneratePomodoroCycles, SavePomodoroCycles, \
    OpenPomodoroGroup, MasterPartialPlan, MasterPartialWork, ProjectResourceView, ProjectResourceSorted, \
    ProjectResourceHtmlView, ProjectPageHtmlView, ProjectPageSorted, MasterTodoItem, ProjectTodoLists, \
    ReorderTodoItemMaster, MasterPartialStats, ProjectStatsData, paddle_webhook, Billing, BillingStatus, \
    test_error, \
    SinglePomodoroCycle, DaySuccessDetails, UnsubscribeOnboarding, PrivacyPolicy, UnsubscribeSales, \
    MasterPartialPlanWeek, TransferItemToMasterWeek, ReloadProjectTodoListsPreviewWeek, SyncMasterWeek, \
    ProjectTodoListItems, TodosKanbanPage, ProjectKanbanItem, ProjectKanbanList

urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),

    url(r"^unsub/onboard/(?P<onboard_id>\w+)$", UnsubscribeOnboarding.as_view()),
    url(r"^unsub/sales/(?P<onboard_id>\w+)$", UnsubscribeSales.as_view()),
    url(r"^paddle/webhook/$", paddle_webhook),
    url(r"^test/error/$", test_error),
    url(r"^billing/$", Billing.as_view(), name='billing'),
    url(r"^billing-status/$", BillingStatus.as_view(), name='billing-status'),
    url(r"^validate-token/$", TokenWall.as_view(), name="validate-token"),
    url(r"^policy/$", PrivacyPolicy.as_view(), name="privacy-policy"),
    url(r"^signup/$", SignupView.as_view(), name="account_signup"),
    url(r"^login/$", LoginView.as_view(), name="account_login"),
    url(r"^logout/$", LogoutView.as_view(), name="account_logout"),
    url(r"^confirm_email/(?P<key>\w+)/$", ConfirmEmailView.as_view(), name="account_confirm_email"),
    url(r"^password/$", ChangePasswordView.as_view(), name="account_password"),
    url(r"^password/reset/$", PasswordResetView.as_view(), name="account_password_reset"),
    url(r"^password/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$", PasswordResetTokenView.as_view(), name="account_password_reset_token"),
    url(r"^settings/$", MySettingsView.as_view(), name="account_settings"),
    url(r"^reminders/$", RemindersView.as_view(), name="reminders"),
    url(r"^delete/$", DeleteView.as_view(), name="account_delete"),
    url(r"^set-timezone/$", SetTimezoneView.as_view(), name="set_timezone"),

    url(r"^todos/list/reload/(?P<list_id>\w+)$", ReloadTodoList.as_view()),
    url(r"^todos/list/archive/(?P<list_id>\w+)$", ArchiveDeleteProjectTodoList.as_view()),
    url(r"^todos/list/(?P<list_id>\w+)/items$", ProjectTodoListItems.as_view()),
    url(r"^todos/item/reorder$", ReorderTodoItemProject.as_view()),
    url(r"^todos/item/complete/(?P<item_id>\w+)$", CompleteTodoItem.as_view()),
    url(r"^todos/item/delete/(?P<item_id>\w+)$", DeleteProjectTodoItem.as_view()),
    url(r"^todos/kanban/reorder/item$", ProjectKanbanItem.as_view(), name='project-kanban-item'),
    url(r"^todos/kanban/list$", ProjectKanbanList.as_view(), name='project-kanban-list'),
    url(r"^events/item/complete/(?P<item_id>\w+)$", CompleteTodoItem.as_view()),
    url(r"^projects/(?P<project_id>\w+)/todos/(?P<list_id>\w+)/item$", ProjectTodoItemView.as_view(), name='todo-item'),
    url(r"^projects/(?P<project_id>\w+)/todos/reload$", ReloadProjectTodoLists.as_view(), name='todos-reload'),
    url(r"^projects/(?P<project_id>\w+)/todos$", TodosPage.as_view(), name='todos'),
    url(r"^projects/(?P<project_id>\w+)/todos/kanban$", TodosKanbanPage.as_view(), name='todos-kanban'),
    url(r"^projects/(?P<project_id>\w+)/todos/archived$", TodosArchivedPage.as_view(), name='todos-archived'),
    url(r"^projects/(?P<project_id>\w+)/schedule$", ProjectSchedulePage.as_view(), name='schedule'),
    url(r"^projects/(?P<project_id>\w+)/event$", ProjectEventView.as_view(), name='project-event'),
    url(r"^projects/(?P<project_id>\w+)/event/(?P<event_id>\w+)$", ProjectEventView.as_view(), name='project-event-edit'),
    url(r"^projects/(?P<project_id>\w+)/page/(?P<page_id>\w+)/image$", ProjectPageImageView.as_view(), name='project-page-image'),
    url(r"^projects/(?P<project_id>\w+)/page/(?P<page_id>\w+)/image/(?P<image_id>\w+)$", ProjectPageImageView.as_view(), name='project-page-image'),
    url(r"^projects/(?P<project_id>\w+)/page/view$", ProjectPageHtmlView.as_view(), name='project-page-view'),
    url(r"^projects/(?P<project_id>\w+)/page/(?P<page_id>\w+)$", ProjectPageView.as_view(), name='new-page'),
    url(r"^projects/(?P<project_id>\w+)/page/sorted$", ProjectPageSorted.as_view(), name='project-page-sort'),
    url(r"^projects/(?P<project_id>\w+)/page$", ProjectPageView.as_view(), name='new-page'),
    url(r"^projects/(?P<project_id>\w+)/tag/delete$", ProjectTagDelete.as_view(), name='project-tag-delete'),
    url(r"^projects/(?P<project_id>\w+)/tag$", ProjectTagView.as_view(), name='project-tag'),
    url(r"^projects/(?P<project_id>\w+)/resource/sorted$", ProjectResourceSorted.as_view(), name='project-resource-sort'),
    url(r"^projects/(?P<project_id>\w+)/resource/view$", ProjectResourceHtmlView.as_view(), name='project-resource-view'),
    url(r"^projects/(?P<project_id>\w+)/resource/(?P<resource_id>\w+)$", ProjectResourceView.as_view(), name='project-single-resource'),
    url(r"^projects/(?P<project_id>\w+)/resource$", ProjectResourceView.as_view(), name='project-resource'),
    url(r"^projects/(?P<project_id>\w+)/lists$", ProjectTodoLists.as_view(), name='project-todo-lists'),
    url(r"^projects/log$", ProjectLogView.as_view(), name='project-log'),
    url(r"^projects/(?P<project_id>\w+)$", Projects.as_view(), name='project_view'),
    url(r"^projects/filter", ProjectsTagFiltered.as_view(), name='project-tag-filtered'),
    url(r"^projects/", Projects.as_view(), name='project'),

    url(r"^master/todo/item/(?P<item_id>\w+)$", MasterTodoItem.as_view()),
    url(r"^master/todo/item/", MasterTodoItem.as_view()),

    url(r"^master/todo/complete/(?P<item_id>\w+)$", CompleteMasterItem.as_view()),
    url(r"^master/todo/transfer$", TransferItemToMaster.as_view()),
    url(r"^master/todo/transfer-week$", TransferItemToMasterWeek.as_view()),
    url(r"^master/todo/reorder$", ReorderTodoItemMaster.as_view()),
    url(r"^master/todo/sync$", SyncMasterWeek.as_view()),
    url(r"^master/todo/reload/week/(?P<project_id>\w+)$", ReloadProjectTodoListsPreviewWeek.as_view()),
    url(r"^master/todo/reload/(?P<project_id>\w+)$", ReloadProjectTodoListsPreview.as_view()),
    url(r"^master/todo", MasterTodo.as_view(), name='master-todo'),
    url(r"^master/pomodoro/generate", GeneratePomodoroCycles.as_view(), name='pomodoro-gen'),
    url(r"^master/pomodoro/single/(?P<cycle_id>\w+)$", SinglePomodoroCycle.as_view(), name='pomodoro-single'),
    url(r"^master/pomodoro/save", SavePomodoroCycles.as_view(), name='pomodoro-save'),
    url(r"^master/pomodoro/open/(?P<group_id>\w+)$", OpenPomodoroGroup.as_view(), name='pomodoro-open'),
    url(r"^master/partial/plan-week", MasterPartialPlanWeek.as_view(), name='master-partial-plan-week'),
    url(r"^master/partial/plan", MasterPartialPlan.as_view(), name='master-partial-plan'),
    url(r"^master/partial/work", MasterPartialWork.as_view(), name='master-partial-work'),
    url(r"^master/partial/stats/(?P<project_id>\w+)$", MasterPartialStats.as_view(), name='master-partial-stats'),
    url(r"^master/partial/stats$", MasterPartialStats.as_view(), name='master-partial-stats'),
    url(r"^master/stats/data/(?P<project_id>\w+)$", ProjectStatsData.as_view(), name='master-stats-data'),
    url(r"^success/day", DaySuccessDetails.as_view(), name='success-day'),
]
