from django.contrib import admin
from .models import Profile, Project, OnboardEvents


class ProfileAdmin(admin.ModelAdmin):
    search_fields = ['account__user__email']


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ['name']

class OnboardAdmin(admin.ModelAdmin):
    search_fields = ['user__account__user__email']

admin.site.register(Profile, ProfileAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(OnboardEvents, OnboardAdmin)
