/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ["showEntryContainer", "showEntry", "showEntryTitle", "latestEntry", "day", "week", "month", "quarter", "year", "theEntryContent", "theEntryTitle", "journalForm", "splitBtn", "singleBtn", "autoSaveInfo", "saveProgress", "showTitleBox", "journalTitleShow", "editTitleBox", "journalTitleEdit"];

  initialize() {
    this.mainId = this.data.get("entryId");
    this.isSplitView = 2;
    this.trix = document.querySelector("trix-editor").editor;
    $('form.ays-warning').areYouSure({'message': 'Are you sure you want to leave? You have unsaved changes.'});
    if (window.location.hash) {
      let hash = window.location.hash.substr(1);
      if (hash === 'review') {
        this.splitView();
      }
    }
    this.journalIds = [];
    let that = this;
    $.get({
      url: BASE_URL + '/journal/ids',
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        that.journalIds = response.ids;
        that.maxIndex = response.ids.length - 1;
        that.index = that.maxIndex;
      }
    });
    if (FIRST_JOURNAL === "true") {
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': false,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "Create any of the 4 types of journals here.",
            element: ".intro-step-1"
          },
          {
            intro: 'Toggle between split and full view. People say it\'s cool. Try it.',
            element: '.intro-step-2'
          },
          {
            intro: 'Manage your templates and journal schedule here.',
            element: '.intro-step-3'
          },
        ]
      });
      intro.oncomplete(function(){
        MyTrack('tour-journal-completed');
      });
      intro.onexit(function(){
        let currentStep = intro._currentStep;
        MyTrack('tour-journal-exit', {exitStep: currentStep});
      });
      intro.start();
    }
    this.textChanged = false;
    $('trix-editor').on('trix-change', function(){
      $('form.ays-warning').addClass('dirty');
      that.textChanged = true;
    });
    this.setupAutosave();
  }

  setupAutosave(){
    let that = this;
    this.autoSaveInterval = setInterval(function(){
      if(that.textChanged){
        that.saveJournal();
      }
    }, 30000);
  }

  splitView(evt) {
    if(evt){
      evt.preventDefault();
    }

    let targetElement = $(this.showEntryContainerTarget);
    //1 loaded and shown
    //2 loaded and hidden
    //0 not loaded
    let journalForm = $(this.journalFormTarget);
    if (this.isSplitView === 1) {
      targetElement.addClass("hidden");
      journalForm.removeClass("col-md-6");
      journalForm.addClass("col-md-12");
      $(this.splitBtnTarget).removeClass("hidden");
      $(this.singleBtnTarget).addClass("hidden");
      this.isSplitView = 2;
      return;
    } else {
      if (this.isSplitView === 2) {
        targetElement.removeClass("hidden");
        journalForm.removeClass("col-md-12");
        journalForm.addClass("col-md-6");
        $(this.splitBtnTarget).addClass("hidden");
        $(this.singleBtnTarget).removeClass("hidden");
        this.isSplitView = 1;
        return;
      }
    }

  }

  makeRequest(journalId) {
    let entryUrl = BASE_URL + '/journal/entry/ajax/' + journalId;
    console.log("Fetching " + entryUrl);
    let that = this;
    $.get({
      url: entryUrl,
      success: function (entry) {
        $(that.showEntryTarget).html(entry.content);
        $(that.showEntryTitleTarget).html(entry.title);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  showNext(evt) {
    evt.preventDefault();
    if (this.index === this.maxIndex) {
      return;
    }
    this.index += 1;
    this.makeRequest(this.journalIds[this.index]);
  }

  showPrev(evt) {
    evt.preventDefault();
    if (this.index === 0) {
      return;
    }
    this.index -= 1;
    this.makeRequest(this.journalIds[this.index]);
  }

  saveJournal() {
    let body = {
      'title': this.journalTitleEditTarget.value,
      'content': this.theEntryContentTarget.value
    };
    let that = this;
    $(this.saveProgressTarget).removeClass('hidden');
    $.post({
      url: BASE_URL + '/journal/entry/ajax/' + this.mainId,
      data: JSON.stringify(body),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        console.log("saved");
        $(that.saveProgressTarget).addClass('hidden');
        $(that.autoSaveInfoTarget).html('Autosaved at ' + moment().format('HH:mm:ss'));
        $(that.autoSaveInfoTarget).removeClass('hidden');
        $('form.ays-warning').trigger('reinitialize.areYouSure');
        that.textChanged = false;
        $('.sidebar-wrapper ul.nav li.active p span').remove();
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  editJournalTitle(evt){
    evt.preventDefault();
    $(this.showTitleBoxTarget).hide();
    $(this.editTitleBoxTarget).show();
    $(this.journalTitleEditTarget).focus();
  }

  saveJournalTitle(evt){
    evt.preventDefault();
    let data = {
      'title': this.journalTitleEditTarget.value
    };
    let that = this;
    $.ajax({
      url: BASE_URL + '/journal/entry/ajax/'+ this.mainId,
      type: 'post',
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(data),
      success: function(response){
        $(that.editTitleBoxTarget).hide();
        $(that.journalTitleShowTarget).html(data.title);
        $(that.showTitleBoxTarget).show();
        that.$sidebarNotes.find(".active p.wrap").html(data.title);
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

  saveSchedule(evt) {
    $.post({
      url: BASE_URL + '/journal/schedule/' + evt.target.dataset.journalId,
      data: JSON.stringify({
        'day': this.dayTarget.checked,
        'week': this.weekTarget.checked,
        'month': this.monthTarget.checked,
        'year': this.yearTarget.checked,
      }),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        $('#scheduleModal').modal('hide');
      }
    });
  }

  modalDeleteJournal(evt) {
    evt.preventDefault();
    let title = this.journalTitleEditTarget.value;
    $('#journalDeleteModal').find('.dialog-note-name').text(title);
    $('#journalDeleteModal').modal({
      backdrop: false
    });
  }

  deleteJournal() {
    let deleteUrl = BASE_URL + '/journal/entry/ajax/' + this.mainId;
    $.ajax({
      url: deleteUrl,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        window.location = rez.location;
      },
    });
  }
}
