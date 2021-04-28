/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ["templateTitle", "templateContent", "newTemplateBox", "templatesHeaderList"];

  initialize(){
    this.i = 0;
    this.templateId = this.data.get("templateId");
    this.$headerList = $(this.templatesHeaderListTarget);
    this.isNew = false;

    this.trix = document.querySelector("trix-editor").editor;
    if(FIRST_NOTE_TEMPLATE === "true"){
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': true,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "Switch between templates. First three are on the house.",
            element: ".intro-step-1"
          },
          {
            intro: 'Create your own.',
            element: '.intro-step-2'
          },
          {
            intro: "Save & Delete are here.",
            element: '.intro-step-3'
          },
        ]
      });
      intro.oncomplete(function(){
        MyTrack('tour-note-template-completed');
      });
      intro.onexit(function(){
        let currentStep = intro._currentStep;
        MyTrack('tour-note-template-exit', {exitStep: currentStep});
      });
      intro.start();
    }
    $('form.ays-warning').areYouSure({'message': 'Are you sure you want to leave? You have unsaved changes.'});
    $('trix-editor').on('trix-change', function(){
      $('form.ays-warning').addClass('dirty');
    });
  }

  scrollRight() {
    this.i += 200;
    $('.note-templates-container').animate({scrollLeft: this.i}, 300);
    console.log("Scroll to " + this.i);
  }

  scrollLeft() {
    if(this.i > 0) {
      this.i -= 200;
      $('.note-templates-container').animate({scrollLeft: this.i}, 300);
    }
  }

  clearAllSelections() {
    $('.header-list .header-list__item').removeClass("header-list__item--active");
  }

  selectTemplate(evt) {
    //todo show sweet alert about not saved changes
    evt.preventDefault();
    let $parent = $(evt.target).closest(".header-list__parent");
    if($('form.ays-warning').hasClass('dirty')){
      if(confirm("You will lose your changes if you navigate without saving this template?")){
        this._selectTemplate($parent);
      }
    }else{
      this._selectTemplate($parent);
    }
  }

  clearTrix(){
    this.trix.setSelectedRange([0, this.trix.getDocument().getLength()]);
    this.trix.deleteInDirection("forward");
  }

  reinitEditor(content){
    this.clearTrix();
    this.trix.insertHTML(content);
  }

  _selectTemplate($parent){
    this.templateId = $parent.data("templateId");
    this.clearAllSelections();
    $parent.find(".header-list__item").addClass("header-list__item--active");
    let that = this;
    $.get({
      url: BASE_URL + '/notebook/templates/ajax/' + this.templateId,
      success: function(response){
        that.reinitEditor(response.content);
        that.templateTitleTarget.value = response.title;
        $('form.ays-warning').removeClass('dirty');
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  newTemplate(evt){
    this.clearAllSelections();
    this.reinitEditor('New template content');
    this.templateTitleTarget.value = "New template";
    this.templateTitleTarget.focus();
    this.templateId = 0;
    if(!this.isNew) {
      $('.note-templates-container').prepend("<a data-target='note-template.newTemplateBox' class=\"header-list__parent\" href=\"#\" data-saction=\"note-template#selectTemplate\">" +
        "<div class=\"header-list__item card header-list__item--active\">\n" +
        "                    <div class=\"card-body\">\n" +
        "                        <div class=\"card-title\">New template</div>\n" +
        "                    </div>\n" +
        "                    </div></a>");
      this.isNew = true;
    }
  }

  saveTemplate(evt) {
    let templateId = this.templateId;
    let postData = {
        title: this.templateTitleTarget.value,
        content: this.templateContentTarget.value
      };
    let that = this;
    $.post({
      url: BASE_URL + '/notebook/templates/ajax/'+templateId,
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(postData),
      success: function(result) {
        $('.header-list__item--active .card-title').html(postData.title);
        if(that.isNew){
          $(that.newTemplateBoxTarget).find('.card-title').html(postData.title);
          $(that.newTemplateBoxTarget).data('template-id', result.id);
        }
        $('form.ays-warning').trigger('reinitialize.areYouSure');
        showSuccessNotification("Note template saved");
      },
      error: function (err) {
        //todo show err notification
        console.log(err);
      }
    });
  }

  deleteTemplate(evt){
    let templateId = this.templateId;
    let that = this;
    $.ajax({
      url: BASE_URL + '/notebook/templates/ajax/' + templateId,
      type: 'delete',
      headers: {'X-CSRFToken': getCsrf()},
      success: function (result) {
        that.$headerList.find(".header-list__item--active").remove();
        let $parent = that.$headerList.find(".header-list__parent:first");
        that._selectTemplate($parent);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }
}
