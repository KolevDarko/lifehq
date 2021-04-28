from django.db import models
from django.utils import timezone

from apps.base.models import Profile
from apps.common.models import HashedModel


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

class Notebook(TimestampedModel):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=200)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)


class Note(TimestampedModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name='notes')


class NoteImage(HashedModel):
    image = models.ImageField(upload_to='note_images')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    note = models.ForeignKey(Note, on_delete=models.CASCADE, related_name='images')


class NoteTemplate(HashedModel):
    title = models.CharField(max_length=200)
    content = models.TextField()
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)


class DefaultNoteTemplate(HashedModel):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=20)
    content = models.TextField()

    @classmethod
    def get_templates_dict(cls):
        response = {}
        for note_template in DefaultNoteTemplate.objects.all():
            response[note_template.slug] = note_template
        return response
