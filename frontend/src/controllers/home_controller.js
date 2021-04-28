/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ['newProjectForm', 'newNotebookForm', 'projectContainer', 'projectDeadline'];

  toggleProjectForm(event){
    event.preventDefault();
    this.newProjectFormTarget.classList.toggle("hidden");
  }

  toggleNotebookForm(event){
    event.preventDefault();
    this.newNotebookFormTarget.classList.toggle("hidden");
  }

  initialize(){
    if(PROFILE_FIRST_LOGIN === "true"){
      this.startProductTour();
      this.setTimezone();
    }
    let startTime = moment().add(7, 'days');
    startTime.set('minute', 0);

    $('.datepicker').datetimepicker({
      format: 'MM/DD/YYYY',
      // icons: datepickerIcons,
      defaultDate: startTime
    });
  }
  setTimezone(){
    let localTime = moment().format();
    $.post({
      url: BASE_URL + '/set-timezone/',
      data: JSON.stringify({'datetime': localTime}),
      headers: { 'X-CSRFToken': getCsrf()},
      success: function(response){},
      error: function(error){
        console.log(error);
      }
    });
  }
  startProductTour(){
    let tour = introJs();
    tour.setOption('showProgress', true);
    tour.setOption('scrollToElement', true);
    tour.setOption('showStepNumbers', false);
    tour.setOption('tooltipPosition', 'auto');
    tour.setOption('showBullets', false);
    tour.setOption('steps', [
      {
        element: ".intro-step-1",
        intro: "Before you shut this down! <br>This Intro project explains how everything works and fits together. <br> The rest of the intro takes 34 seconds. (press Enter to move forward)",
        position: 'right'
      },
      {
        element: '.intro-step-1-2',
        intro: "Win every day! This shows your combined score from your Work, Habits and Journals for today.",
        position: 'below'
      },
      {
        element: ".intro-step-2",
        intro: "Use the Journal to define your goals, review your actions and keep yourself in check."
      },
      {
        element: ".intro-step-3",
        intro: "In the Year journal define your giant goals. Then use the Month and Week journals to split them into smaller chunks."
      },
      {
        element: ".intro-step-4",
        intro: "Easy access to the journals for today. Don't worry, they all have templates.",
        // intro: "Use the Daily Journal to prep for the day and keep yourself aligned with your goals day to day."
      },
      {
        element: ".intro-step-5",
        intro: "Create a project for every goal you have. Projects store tasks, schedule and resources.",
        position: 'right'
      },
      {
        element: ".intro-step-6",
        intro: "The master list with work for today. This is where you crush it. This alone will 10x your productivity."
      },
      {
        element: ".intro-step-7",
        intro: "Congrats! You've completed one important task already."
      },
      {
        element: ".intro-step-8",
        intro: "Track multiple habits at once with our consistency chain in the habits module."
      },
      {
        element: ".intro-step-9",
        intro: "Write lecture notes, book summaries, best practices and repeating checklists. Or browse our knowledge library (coming soon) and learn something new.",
        position: 'right'
      },
    ]);
    tour.oncomplete(function(){
        MyTrack('tour-home-completed');
      });
    tour.onexit(function(){
        let currentStep = tour._currentStep;
        MyTrack('tour-home-exit', {exitStep: currentStep});
      });
    tour.start();
  }

  tagFilter(evt) {
    let tagName = evt.target.value;
    this.reloadProjectList(tagName, $(this.projectContainerTarget));
  }

  reloadProjectList(tagName, targetElement) {
    let fullUrl = BASE_URL + "/projects/filter?tagName=" + tagName;
    $.get({
      url: fullUrl,
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        targetElement.html(response);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  toggleDeadline(){
    $(this.projectDeadlineTarget).toggle();
  }

}
