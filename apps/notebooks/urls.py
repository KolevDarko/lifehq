"""urlconf for the base application"""

from django.conf.urls import url

from apps.notebooks.views import NotebookPage, NotePage, NoteTemplatesView, NoteFromTemplateAjax, NoteTemplateAjax, \
    NotebookPageAjax, NotePageImage, NoteFromDefaultTemplate

urlpatterns = [
    url(r'(?P<notebook_id>\w+)/ajax/note/(?P<note_id>\w+)/image$', NotePageImage.as_view(), name='note-page-image'),
    url(r'(?P<notebook_id>\w+)/ajax/note/(?P<note_id>\w+)$', NotePage.as_view(), name='note-page'),
    url(r'(?P<notebook_id>\w+)/ajax/note/?$', NotePage.as_view(), name='note-page'),
    url(r'(?P<notebook_id>\w+)/ajax/note/template/(?P<template_id>\w+)$', NoteFromTemplateAjax.as_view(), name='ajax-note-from-template'),
    url(r'note/template/(?P<template_id>\w+)$', NoteFromDefaultTemplate.as_view(), name='note-from-default'),

    url(r'templates/(?P<template_id>\w+)$', NoteTemplatesView.as_view(), name='note-templates'),
    url(r'templates$', NoteTemplatesView.as_view(), name='note-templates'),
    url(r'templates/ajax/(?P<template_id>\w+)$', NoteTemplateAjax.as_view(), name='note-template-ajax'),
    url(r'templates/ajax/?$', NoteTemplateAjax.as_view(), name='note-template-ajax'),

    url(r'ajax/(?P<notebook_id>\w+)$', NotebookPageAjax.as_view(), name='notebook-ajax'),
    url(r'(?P<notebook_id>\w+)/note/(?P<note_id>\w+)$', NotebookPage.as_view(), name='notebook-page'),
    url(r'(?P<notebook_id>\w+)$', NotebookPage.as_view(), name='notebook-page'),
    url(r'$', NotebookPage.as_view(), name='notebook-page'),

]
