import json

from django.shortcuts import render, redirect
from django.utils.html import strip_tags
from django.views import View

from apps.base.views import CustomLoginRequiredMixin
from apps.common.views import MyJsonResponse
from apps.notebooks.models import Notebook, Note, NoteTemplate, NoteImage, DefaultNoteTemplate
from mastermind.settings.base import MAX_IMAGE_SIZE

JsonResponse = MyJsonResponse

class NotebookPage(CustomLoginRequiredMixin, View):
    def get(self, request, notebook_id=None, note_id=None):
        user_notebooks = Notebook.objects.filter(user=self.profile(request)).order_by('-created_on')
        note_templates = NoteTemplate.objects.filter(user=self.profile(request))
        sidebar_active = True
        notebook = Notebook()
        no_notebooks = False
        if notebook_id:
            sidebar_active = False
            notebook = Notebook.objects.get(pk=notebook_id)
        elif user_notebooks.count():
            notebook = user_notebooks[0]
            sidebar_active = False
        else:
            no_notebooks = True
        if note_id:
            note = Note.objects.get(pk=note_id)
        elif notebook.notes:
            note = notebook.notes.last()
        else:
            note = Note()
        profile = self.profile(request)
        first_note = ""
        if profile.first_note:
            profile.first_note = False
            first_note = "true"
            profile.save()

        return render(request, 'notebooks/notebook_view.html', {'notebook': notebook, 'all_notebooks': user_notebooks,
                                                                'sidebar_active': sidebar_active, 'the_note': note,
                                                                'note_templates': note_templates,
                                                                "active_knowledge": True, 'no_notebooks': no_notebooks,
                                                                'first_note': first_note})

    def post(self, request):
        data = request.POST
        notebook = Notebook(title=data['notebookTitle'], description=data.get('notebookDesc', ''),
                            user=request.user.account.profile)
        notebook.save()
        return redirect('notebook-page', notebook_id=notebook.id)


class NotebookPageAjax(CustomLoginRequiredMixin, View):
    def post(self, request, notebook_id):
        data = json.loads(request.body.decode())
        notebook = Notebook.objects.filter(user=self.profile(request), pk=notebook_id).first()
        if notebook:
            notebook.title = str(data['title']).strip()
            notebook.save()
        return JsonResponse({"success": True})

    def delete(self, request, notebook_id):
        notebook = Notebook.objects.filter(pk=notebook_id, user=self.profile(request)).first()
        if notebook:
            notebook.delete()
        return JsonResponse({'success': True})

class NotePageImage(CustomLoginRequiredMixin, View):
    def post(self, request, notebook_id, note_id):
        image_file = request.FILES['file']
        if image_file.size >= MAX_IMAGE_SIZE:
            error = "Image size must be lower than 2MB."
            return JsonResponse({"success": False, "error": error})
        note = Note.objects.get(pk=note_id)
        db_image = NoteImage.objects.create(image=image_file, note=note)
        return JsonResponse({'url': db_image.image.url, 'success': True})

class NotePage(CustomLoginRequiredMixin, View):
    funny_titles = [
        "Take Over The World (Plan B)",
        "10 best ways to write titles",
        "Best Practices: Swimming",
        "Checklist: Going to Australia"
    ]

    def get(self, request, notebook_id, note_id=None):
        if note_id:
            note = Note.objects.get(pk=note_id)
        else:
            note = Note.objects.filter(notebook_id=notebook_id).order_by('-id').first()
        return JsonResponse({'title': note.title, 'content': note.content})

    def post(self, request, notebook_id, note_id=None):
        notebook = Notebook.objects.get(pk=notebook_id)
        if note_id:
            note = Note.objects.get(pk=note_id)
        else:
            note = Note()
        data = json.loads(request.body.decode())
        if 'title' in data:
            note.title = data['title']
        if 'content' in data:
            note.content = data['content']
        note.notebook = notebook
        note.save()
        return JsonResponse({'id': note.id, 'title': strip_tags(note.title)})

    def delete(self, request, notebook_id, note_id):
        note = Note.objects.get(pk=note_id)
        note.delete()
        return JsonResponse({'success': True})


class NoteFromTemplateAjax(CustomLoginRequiredMixin, View):

    def get(self, request, notebook_id, template_id):
        chosen_template = NoteTemplate.objects.get(user=request.user.account.profile, pk=template_id)
        title = chosen_template.title + " Title"
        return JsonResponse({'title': title, 'content': chosen_template.content})


class NoteFromDefaultTemplate(CustomLoginRequiredMixin, View):
    def get(self, request, template_id):
        slug_map = {
            '0': 'book-summary',
            '1': 'best-practices',
            '2': 'checklist'
        }
        template_slug = slug_map[template_id]
        chosen_template = DefaultNoteTemplate.objects.get(slug=template_slug)
        title = chosen_template.title + " Title"
        content = chosen_template.content
        profile = self.profile(request)
        new_notebook = Notebook(title=chosen_template.title + " Notebook", user=profile)
        new_notebook.save()
        new_note = Note(title=title, content=content, notebook=new_notebook)
        new_note.save()
        return redirect('notebook-page', notebook_id=new_notebook.id, note_id=new_note.id)


class NoteTemplatesView(CustomLoginRequiredMixin, View):

    def get(self, request, template_id=None):
        note_templates = NoteTemplate.objects.filter(user=request.user.account.profile)
        if template_id:
            chosen_template = NoteTemplate.objects.get(pk=template_id)
        else:
            all_templates = NoteTemplate.objects.filter(user=request.user.account.profile)
            if all_templates.count():
                chosen_template = all_templates.first()
            else:
                chosen_template = NoteTemplate()

        profile = self.profile(request)
        first_note_template = ''
        if profile.first_note_template:
            first_note_template = 'true'
            profile.first_note_template = False
            profile.save()
        return render(request, 'notebooks/note_templates.html',
                      {'chosen_template': chosen_template, 'note_templates': note_templates,
                       'first_note_template': first_note_template})


class NoteTemplateAjax(CustomLoginRequiredMixin, View):
    def get(self, request, template_id=None):
        note_template = NoteTemplate.objects.get(pk=template_id, user=self.profile(request))
        return JsonResponse({'content': note_template.content, 'title': note_template.title})

    def post(self, request, template_id=None):
        data = json.loads(request.body.decode())
        if template_id and template_id != '0':
            the_template = NoteTemplate.objects.get(pk=template_id)
        else:
            the_template = NoteTemplate(user=request.user.account.profile)
        the_template.title = data['title']
        the_template.content = data['content']
        the_template.save()
        return JsonResponse({'success': True, 'id': the_template.id})

    def delete(self, request, template_id):
        t = NoteTemplate.objects.get(pk=template_id)
        t.delete()
        return JsonResponse({"success": True})
