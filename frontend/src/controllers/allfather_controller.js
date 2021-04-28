/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {

  static targets = ['displayTimer', 'displayTimerBtn', 'displayTimerIcon', 'pomCtrl'];

  connect() {
    // Timer has three states, running, paused and stopped(inactive), running and paused will be stored in localStorage,
    // missing localStorage var means it's inactive
    this.TIMER_FORMAT = "HH:mm:ss";
    this.timerHandle = null;
    this.timerCounter = parseInt(localStorage.getItem('timerCounter') || 0);
    this.timerStatus = localStorage.getItem("timerStatus");
    if (!this.timerStatus) {
      return;
    }else{
      $(this.displayTimerBtnTarget).show();
      this.showElapsedTime();
    }
    if (this.timerRunning()) {
      this.runTimer();
      this.continueCounting();
    }
  }

  showElapsedTime(){
    this.workStartTime = moment().startOf('day').add(this.timerCounter, 's');
    $(this.displayTimerTarget).html(this.workStartTime.format(this.TIMER_FORMAT));
  }

  showTimer(shouldShow) {
    if (shouldShow) {
      $(this.displayTimerBtnTarget).show();
    } else {
      $(this.displayTimerBtnTarget).hide();
    }
  }

  timerRunning() {
    return this.timerStatus === "running";
  }

  timerPaused() {
    return this.timerStatus === "paused";
  }

  pauseTimer() {
    this.updateStatus("paused");
    $(this.displayTimerBtnTarget).removeClass("running");
    $(this.displayTimerIconTarget).removeClass('fa-pause');
    $(this.displayTimerIconTarget).addClass('fa-play');
  }

  runTimer() {
    this.updateStatus("running");
    $(this.displayTimerBtnTarget).addClass("running");
    $(this.displayTimerIconTarget).removeClass('fa-play');
    $(this.displayTimerIconTarget).addClass('fa-pause');
  }

  updateStatus(newState) {
    if (!newState) {
      this.timerStatus = null;
      localStorage.removeItem("timerStatus");
    } else {
      this.timerStatus = newState;
      localStorage.setItem("timerStatus", newState);
    }
  }

  pauseResume(evt) {
    if (this.timerRunning()) {
      clearInterval(this.timerHandle);
      this.pauseTimer();
    } else {
      this.continueCounting();
      this.runTimer();
    }
  }

  workingTaskId() {
    return localStorage.getItem('workingTaskId');
  }

  workingTaskMinutes() {
    return localStorage.getItem('workingTaskMinutes');
  }

  showStopBtn(){
    $('.start-timer-btn').hide();
    $('.stop-timer-btn').show();
  }

  getPomodoroCtrl(){
    return this.application.getControllerForElementAndIdentifier(this.pomCtrlTarget, "pomodoro-master");
  }

  notifyPomodoroCtrl(taskId){
    let pomodoroController = this.getPomodoroCtrl();
    pomodoroController.activateTimer(taskId);
  }

  scrollToTop(){
    window.scrollTo(0, 0);
  }

  taskStartTimer(evt) {
    let taskId = this.workingTaskId();
    let prevMinutesWorked = this.workingTaskMinutes();
    if (taskId) {
      this.showStopBtn();
      this.startCounting(prevMinutesWorked);
      this.notifyPomodoroCtrl(taskId);
      this.scrollToTop();
    } else {
      $('#pick-task-info').addClass("text-danger");
    }
  }

  clearUpTimer() {
    // this.timerCounter = 0;
    // this.updateCounter(0);
    this.updateStatus(false);
    this.showTimer(false);
    $('.action-play').removeClass('disabled');
  }

  showStartBtn(){
    $('.start-timer-btn').show();
    $('.stop-timer-btn').hide();
  }

  updateWorkedTime(minutesWorked){
    let pomCtrl = this.getPomodoroCtrl();
    pomCtrl.trackingEnded(minutesWorked);
  }

  stopTimer(evt) {
    clearInterval(this.timerHandle);
    let that = this;
    let minutesWorked = Math.round(this.timerCounter / 60);
    this.storeTimeWorked(minutesWorked,function (success) {
      // todo show success notification and show minutes worked
      that.updateWorkedTime(minutesWorked);
      that.clearUpTimer();
      that.showStartBtn();
    }, function (error) {
      // todo show error notification and suggest contacting me
      that.clearUpTimer();
    });
  }

  storeTimeWorked(minutesWorked, successClb, errorClb) {
    let postData = {
      minutes_worked: minutesWorked
    };
    let taskId = this.workingTaskId();
    $.post({
      url: BASE_URL + '/work/todos/item/track/' + taskId,
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(postData),
      success: successClb,
      error: errorClb
    });
  }

  disableOthers() {
    $('.item-table-row .action-play .fa-play-circle').parent().addClass('disabled');
  }

  startCounting(startingMinutes) {
    this.disableOthers();
    let that = this;
    this.runTimer();
    this.showTimer(true);
    if(startingMinutes){
      this.timerCounter = startingMinutes * 60;
      this.workStartTime = moment().startOf('day').add(this.timerCounter, 's');
      $(that.displayTimerTarget).html(this.workStartTime.format(this.TIMER_FORMAT));
    }else{
      this.timerCounter = 0;
      this.workStartTime = moment().startOf('day');
      $(that.displayTimerTarget).html('00:00:00');
    }

    this.timerHandle = setInterval(function () {
      that.timerCounter += 1;
      that.workStartTime.add(1, 's');
      $(that.displayTimerTarget).html(that.workStartTime.format(that.TIMER_FORMAT));
      that.updateCounter(that.timerCounter);
    }, 1000);
  }

  updateCounter(seconds) {
    localStorage.setItem("timerCounter", seconds);
  }

  continueCounting() {
    this.disableOthers();
    this.runTimer();
    this.showTimer(true);
    this.workStartTime = moment().startOf('day').add(this.timerCounter, 's');
    let that = this;
    this.timerHandle = setInterval(function () {
      that.timerCounter += 1;
      that.workStartTime.add(1, 's');
      $(that.displayTimerTarget).html(that.workStartTime.format(that.TIMER_FORMAT));
      that.updateCounter(that.timerCounter);
    }, 1000);
  }

}
