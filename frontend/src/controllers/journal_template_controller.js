/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ["success", "loader", "save", "dayContent", "weekContent", "monthContent", "quarterContent", "yearContent", "editorHiddenInput"];
  initialize(){
    this.shownTemplate = 'year';
    this.templatesContent = {
      'day': this.dayContentTarget.innerHTML,
      'week': this.weekContentTarget.innerHTML,
      'month': this.monthContentTarget.innerHTML,
      'year': this.yearContentTarget.innerHTML,
    };
    if(FIRST_JOURNAL_TEMPLATE === "true"){
      this.showIntroTour();
    }
    $('form.ays-warning').areYouSure({'message': 'Are you sure you want to leave? You have unsaved changes.'});
    this.trix = document.querySelector("trix-editor").editor;
    $('trix-editor').on('trix-change', function(){
      $('form.ays-warning').addClass('dirty');
    });
  }

  showIntroTour() {
    let intro = introJs();
    intro.setOptions({
      'showProgress': true,
      'scrollToElement': false,
      'showStepNumbers': false,
      'tooltipPosition': 'auto',
      'showBullets': false,
      steps: [
        {
          intro: "Staring at a blank page is the main reason people aren't consistent with their journals.",
          element: ".intro-step-1"
        },
        {
          intro: "So we've set up journal templates centered around achieving your goals.",
          element: '.intro-step-2'
        },
        {
          intro: 'Start by writing your major goals in the Year journal and then split them into smaller chunks ' +
          'in the Month, Week and Day journals.',
          element: '.intro-step-3'
        },
      ]
    });
    intro.oncomplete(function () {
      MyTrack('tour-journal-template-completed');
    });
    intro.onexit(function () {
      let currentStep = intro._currentStep;
      MyTrack('tour-journal-template-exit', {exitStep: currentStep});
    });
    intro.start();
  }

  clearTrix(){
    this.trix.setSelectedRange([0, this.trix.getDocument().getLength()]);
    this.trix.deleteInDirection("forward");
  }

  reinitEditor(content){
    this.clearTrix();
    this.trix.insertHTML(content);
  }


  showContent(template_type){
   this.templatesContent[this.shownTemplate] = this.editorHiddenInputTarget.value;
   this.shownTemplate = template_type;
   let content = this.templatesContent[template_type];
   this.reinitEditor(content);
   this.shownTemplate = template_type;
  }

  showDay(evt){
    evt.preventDefault();
    this.showContent('day');
  }

  showWeek(evt){
    evt.preventDefault();
    this.showContent('week');
  }

  showMonth(evt){
    evt.preventDefault();
    this.showContent('month');
  }

  showYear(evt){
    evt.preventDefault();
    this.showContent('year');
  }

  saveTemplate(evt) {
    $(this.loaderTarget).removeClass('hidden');
    $(this.successTarget).addClass('hidden');
    let that = this;
    this.templatesContent[this.shownTemplate] = this.editorHiddenInputTarget.value;
    $.post({
      url: BASE_URL + '/journal/templates/' + evt.target.dataset.journalId,
      data: JSON.stringify({
          'day': this.templatesContent.day,
          'week': this.templatesContent.week,
          'month': this.templatesContent.month,
          'quarter': this.templatesContent.quarter,
          'year': this.templatesContent.year,
      }),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        $(that.loaderTarget).addClass('hidden');
        $(that.successTarget).removeClass('hidden');
        $('form.ays-warning').removeClass('dirty');
      }
    });
  }
}
