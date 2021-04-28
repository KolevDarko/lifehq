/*jshint esversion: 6 */
// eslint-disable-next-line import/no-unresolved
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['container', 'linkWork', 'linkPlan', 'linkPlanWeek', 'linkStats', 'filterProjectSelect'];

  connect() {
    this.pageLoaded = null;
    if (window.location.hash) {
      let hash = window.location.hash.substr(1);
      if (hash) {
        this.loadPage(hash);
        return;
      }
    }
    let choice = localStorage.getItem('workChoice') || 'plan-week';
    this.loadPage(choice);
  }

  loadPage(pageName) {
    if (pageName === 'work') {
      this._loadWork();
      return;
    }
    if (pageName === 'plan') {
      this._loadPlan();
      return;
    }
    if (pageName === 'stats') {
      this._loadStats();
      return;
    }
    if (pageName === 'plan-week') {
      this._loadPlanWeek();
    }
  }


  filterProjectStats() {
    let chosenProjectId = $(this.filterProjectStatsTarget).val();
  }

  filterProject(evt) {
    evt.preventDefault();
    let chosenProjectId = $(this.filterProjectSelectTarget).val();
    $('#workSelectedProject').val(chosenProjectId);
    if (chosenProjectId === "all") {
      $("table.active-table tr").show();
    } else {
      let projectIdSelector = "tr[data-project-id='" + chosenProjectId + "']";
      let toHideSelector = $("table.active-table tr").not(projectIdSelector);
      toHideSelector.hide();
      $("tbody " + projectIdSelector).show();
    }
  }

  _activateTab(pageName){
    this.pageLoaded = pageName;
    localStorage.setItem('workChoice', pageName);
    $('ul li a').removeClass('active');
    let targets = {
      'work': this.linkWorkTarget,
      'plan': this.linkPlanTarget,
      'plan-week': this.linkPlanWeekTarget,
      'stats': this.linkStatsTarget
    };
    $(targets[pageName]).addClass('active');
  }

  loadPlan(evt) {
    if (this.pageLoaded === 'plan') {
      return;
    }
    if (POMODORO_RUNNING) {
      if (confirm("Pomodoro is running, are you sure you want to leave?")) {
        POMODORO_RUNNING = false;
        this._loadPlan();
      } else {
        evt.preventDefault();
      }
    } else {
      this._loadPlan();
    }
  }

  _loadPlan() {
    this._activateTab('plan');
    let that = this;
    $(that.containerTarget).html(spinnerHtml());
    $.get({
      url: BASE_URL + '/master/partial/plan',
      success: function (response) {
        $(that.containerTarget).html(response.content);
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  _loadPlanWeek(evt) {
    this._activateTab('plan-week');
    let that = this;
    $(that.containerTarget).html(spinnerHtml());
    $.get({
      url: BASE_URL + '/master/partial/plan-week',
      success: function (response) {
        $(that.containerTarget).html(response.content);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  _loadWork(evt) {
    this._activateTab('work');
    let that = this;
    $(that.containerTarget).html(spinnerHtml());
    $.get({
      url: BASE_URL + '/master/partial/work',
      success: function (response) {
        $(that.containerTarget).html(response.content);
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

  navigateTab(evt){
    let pageName = $(evt.target).data('pageType');
    if(this.pageLoaded === pageName){
      return;
    }
    if(POMODORO_RUNNING) {
      evt.preventDefault();
      evt.stopPropagation();
      if (confirm("Pomodoro is running, are you sure you want to leave?")) {
        POMODORO_RUNNING = false;
        this.loadPage(pageName);
      }
    }else{
      this.loadPage(pageName);
    }
  }

  loadStats(evt) {
    if (this.pageLoaded === 'stats') {
      return;
    }
    if (POMODORO_RUNNING) {
      if (confirm("Pomodoro is running, are you sure you want to leave?")) {
        POMODORO_RUNNING = false;
        this._loadStats();
      }
    } else {
      this._loadStats();
    }
  }

  _loadStats() {
    this._activateTab('stats');
    let that = this;
    let fullUrl = BASE_URL + '/master/partial/stats';
    $.get({
      url: fullUrl,
      success: function (response) {
        $(that.containerTarget).html(response.content);
      },
      error: function (error) {
        console.log(error);
      }
    });
  }
}
