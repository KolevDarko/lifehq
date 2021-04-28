/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets=["notebookSidebar", "notebookForm", "notebookEditForm", "noteListContainer", "templateModal", "editTitle", "noteContent", "showTitleBox", "noteTitleShow", "editTitleBox", "noteTitleEdit"];

  initialize(){
    this.trix = document.querySelector("trix-editor").editor;

    this.$sidebarNotes = $(this.noteListContainerTarget);
    this.notebookId = this.data.get("notebookid");
    this.noteId = this.data.get("noteid");
    this.$delNotebookTarget = null;
    this.editNotebookId = null;

    var that = this;
    $('form.ays-warning').areYouSure({'message': 'Are you sure you want to leave? You have unsaved changes.'});

    if (this.notebookId && FIRST_NOTE === "true"){
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': false,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "Create blank note or choose from template.",
            element: ".intro-step-1"
          },
          {
            intro: 'Manage your note templates here. We added a few to get your started.',
            element: '.intro-step-2'
          },
        ]
      });
      intro.oncomplete(function () {
        MyTrack('tour-notebook-completed');
      });
      intro.onexit(function () {
        let currentStep = intro._currentStep;
        MyTrack('tour-notebook-exit', {exitStep: currentStep});
      });
      intro.start();
    }
    $('trix-editor').on('trix-change', function(){
      $('form.ays-warning').addClass('dirty');
    });
  }

  editNoteTitle(){
    $(this.showTitleBoxTarget).hide();
    $(this.editTitleBoxTarget).show();
  }

  saveNoteTitle(evt){
    evt.preventDefault();
    let data = {
      'title': this.noteTitleEditTarget.value
    };
    let that = this;
    $.ajax({
      url: BASE_URL + '/notebook/'+ this.notebookId +'/ajax/note/' + this.noteId,
      type: 'post',
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(data),
      success: function(response){
        $(that.editTitleBoxTarget).hide();
        $(that.noteTitleShowTarget).html(data.title);
        $(that.showTitleBoxTarget).show();
        if(that.noteId){
          that.$sidebarNotes.find(".active p.wrap").html(data.title);
        }
      },
      error: function(jqXHR, textStatus, errorThrown) {
        console.log(jqXHR);
      }
    });

  }

  clearTrix(){
    this.trix.setSelectedRange([0, this.trix.getDocument().getLength()]);
    this.trix.deleteInDirection("forward");
  }

  reinitEditor(content){
    this.clearTrix();
    this.trix.insertHTML(content);
  }

  toggleNotebookSidebar(evt){
    evt.preventDefault();
    $(this.notebookSidebarTarget).toggleClass("active");
    $(this.notebookSidebarTarget).toggleClass("mobile-active");
  }

  clearActiveNote(){
    this.$sidebarNotes.find('li').removeClass('active');
  }

  showNote(evt){
    evt.preventDefault();
    this.clearActiveNote();
    let $realTarget = $(evt.target).closest("a.nav-link");
    this._showNote($realTarget);
  }

  _showNote($realTarget){
    this.noteId = $realTarget.data('noteId');
    let that = this;
    $.get({
      url: BASE_URL + '/notebook/'+ this.notebookId +'/ajax/note/' + this.noteId,
      success: function(response) {
        that.reinitEditor(response.content);
        $(that.noteTitleShowTarget).html(response.title);
        $(that.noteTitleEditTarget).val(response.title);
        $realTarget.parent().addClass('active');
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  toggleNotebookForm(){
    $(this.notebookFormTarget).toggleClass('hidden');
  }

  showNotebookEditForm(){
    $(this.notebookEditFormTarget).show();
  }

  hideNotebookEditForm(){
    $(this.notebookEditFormTarget).hide();
  }

  updateNotebook(){
    let data = {
      'title': this.editTitleTarget.value
    };
    let saveUrl = BASE_URL + '/notebook/ajax/'+ this.editNotebookId;
    let that = this;
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        $('p.notebook-title-' + that.editNotebookId).text(data.title);
        that.hideNotebookEditForm();
      }
    });
  }

  noteSaved(newNote){
    let newNoteRow = "<li class=\"nav-item active\">\n" +
      "                            <a class=\"nav-link\" href=\"#\" data-saction=\"notebook#showNote\" data-note-id=\""+newNote.id+"\">\n" +
      "                                <i class=\"fa fa-file\"></i>\n" +
      "                                <p class='wrap'> "+ newNote.title +"\n" +
      "                                </p>\n" +
      "                            </a>\n" +
      "                        </li>";
    this.$sidebarNotes.append(newNoteRow);
  }

  saveNote(){
    let data = {
      'title': this.noteTitleEditTarget.value,
      'content': this.noteContentTarget.value,
    };
    let saveUrl = BASE_URL + '/notebook/'+ this.notebookId +'/ajax/note/' + (this.noteId || '');
    let that = this;
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        showSuccessNotification("Note successfully saved");
        $('form.ays-warning').trigger('reinitialize.areYouSure');
        if(that.noteId){
          that.$sidebarNotes.find(".active p.wrap").html(data.title);
          return;
        }
        that.noteId = response.id;
        that.noteSaved({
          'id': response.id,
          'title': response.title
        });
      }
    });
  }

  deleteNote() {
    if (!this.noteId) {
      return;
    }
    let deleteUrl = BASE_URL + '/notebook/' + this.notebookId + '/ajax/note/' + this.noteId;
    let that = this;
    $.ajax({
      url: deleteUrl,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        showDeleteNotification("Note was removed")
        $('#sidebarNotes').find('li.active').remove();
        $('#noteDeleteModal').modal('hide');
        let newSelection = $('#sidebarNotes').find('li:first');
        if (newSelection.length){
          newSelection.addClass('active');
          that._showNote(newSelection.find('a.nav-link'));
        }
      },
    });
  }

  blankNote(){
    this.clearActiveNote();
    let funTitle = "New note title";
    let content = "Take over the world - Plan B";
    this.noteTitleShowTarget.innerText = funTitle;
    this.noteTitleEditTarget.value = funTitle;
    this.reinitEditor(content);
    this.noteId = null;
  }

  noteFromTemplate(evt){
    evt.preventDefault();
    this.clearActiveNote();
    let $realTarget = $(evt.target).closest('a');
    let templateId = $realTarget.data('templateId');
    let that = this;
    let fullUrl = BASE_URL + '/notebook/'+ this.notebookId +'/ajax/note/template/' + templateId;
    $.get({
      url: fullUrl,
      success: function(response) {
        that.noteTitleEditTarget.value = response.title;
        that.noteTitleShowTarget.innerHTML = response.title;
        that.reinitEditor(response.content);
        $(that.templateModalTarget).modal('hide');
        that.noteId = null;
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  modalDeleteNote(evt){
    let title = this.noteTitleEditTarget.value;
    $('#noteDeleteModal').find('.dialog-note-name').text(title);
    $('#noteDeleteModal').modal({
      backdrop: false
    });
  }

  modalDeleteNotebook(evt){
    this.$delNotebookTarget = $(evt.currentTarget);
    $('#notebookDeleteModal').modal({
      backdrop: false
    });
  }

  editNotebook(evt){
    this.editNotebookId = evt.currentTarget.dataset["notebookId"];
    this.editTitleTarget.value = $('p.notebook-title-'+this.editNotebookId).text();
    this.showNotebookEditForm();
  }

  deleteNotebook(){
    if (!this.$delNotebookTarget) {
      return;
    }
    let delNotebookId = this.$delNotebookTarget.data('notebookId');
    let deleteUrl = BASE_URL + '/notebook/ajax/' + delNotebookId;
    let that = this;
    $.ajax({
      url: deleteUrl,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        $('#notebookDeleteModal').modal('hide');
        that.$delNotebookTarget.closest('li.nav-item').remove();
        showDeleteNotification("Notebook was deleted");
      },
    });
  }
}
