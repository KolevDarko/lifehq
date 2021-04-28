# Generated by Django 2.1.5 on 2019-10-15 05:19

from django.db import migrations

def fill_todo_item_profile(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    ProjectTodoItem = apps.get_model('base', 'ProjectTodoItem')
    for todoItem in ProjectTodoItem.objects.all():
        itemProfile = None
        if todoItem.personal_list:
            itemProfile = todoItem.personal_list.user
        elif todoItem.day_list:
            itemProfile = todoItem.day_list.user
        elif todoItem.project_list:
            itemProfile = todoItem.project_list.project.user
        else:
            print("Item {} has no attachments".format(todoItem.id))
        if itemProfile:
            todoItem.user = itemProfile
            todoItem.save()

def empty_stub(apps, schema_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('base', '0089_projecttodoitem_user'),
    ]

    operations = [
        migrations.RunPython(fill_todo_item_profile, empty_stub),
    ]
