/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['cycleCount', 'workDuration', 'breakDuration', 'inputQ1', 'inputQ2', 'timer', 'timerInfo', 'cycleChild',
    'startBtn', 'cycleInfo', 'nextBtn', 'nextBtnInfo', 'pauseBtn', 'selectGroup', 'projectSelect', 'reviewAccomplished', 'reviewEnergy', 'reviewText',
    'timerProjectTitle', 'timerTaskTitle', 'timerTaskDescription', 'timerTaskWorked', 'assignPomodoroTime'];


  initialize() {
    this.finishSequence = false;
    this.scroller = 0;
    this.firstCycle = true;
    this.activeCycleIndex = 0;
    this.cycleIdList = [];
    this.allReviewData = [];
    this.breakCounter = 0;
    this.timerCounter = 0;
    this.cyclesPassed = 0;
    this.workPaused = false;
    this.breakPaused = false;
    $('.selectpicker').selectpicker();
    this.autoPlay = false;
    this.nextAction = 'break';

    this.childControllers = {};
    this.stateStatus = 'ready';
    this.stateType = 'ready';

    if (FIRST_WORK === "true") {
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': false,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "This is where Work gets done. Select your task by clicking the green play button and track the time worked.",
            element: ".intro-step-1"
          },
          {
            intro: 'Use regular timer or Advanced pomodoro sessions',
            element: '.intro-step-2'
          },
          {
            intro: "When finished, check your weekly and daily work output here.",
            element: ".work-intro-step-6"
          }
        ]
      });
      intro.start();
      intro.oncomplete(function () {
        MyTrack('tour-master-completed');
      });
      intro.onexit(function () {
        let currentStep = intro._currentStep;
        MyTrack('tour-master-exit', {exitStep: currentStep});
      });
    }

    window.onbeforeunload = this.createCheckExit();

    this.workingTaskId = localStorage.getItem("workingTaskId");

    if (this.workingTaskId) {
      this.activateTimer(this.workingTaskId);
    }
  }

  resetAll(evt) {
    if (evt) {
      evt.preventDefault();
    }
    clearInterval(this.workHandle);
    clearInterval(this.breakHandle);
    this.scroller = 0;
    this.firstCycle = true;
    this.finishSequence = false;
    this.breakTime = false;
    this.workTime = false;
    this.breakCounter = 0;
    this.timerCounter = 0;
    this.cyclesPassed = 0;
    this.workPaused = false;
    this.breakPaused = false;
    $('.scrollable-container').animate({scrollLeft: this.scroller}, 200);
    $(this.cycleInfoTarget).html("Next: Cycle 1");
    this.enableStartBtn();
    this.controlButtons('disable');
    POMODORO_RUNNING = false;
    this.allReviewData = [];
    this.cycleIdList = [];
    this.finishSequence = false;
    this.scroller = 0;
    this.firstCycle = true;
    this.activeCycleIndex = 0;
    this.autoPlay = false;
    this.nextAction = 'break';
    this.childControllers = {};
    this.stateStatus = 'ready';
    this.stateType = 'ready';
  }

  trackingEnded(newMinutes){
    this.prevMinutesWorked = newMinutes;
    localStorage.setItem("workingTaskMinutes", newMinutes);
    $(this.timerTaskWorkedTarget).html(this.calcTimeWorked(newMinutes));
    this.timerStatus = null;
    localStorage.removeItem("timerStatus");
  }

  activateTimer(workingTaskId) {
    let $taskRow = $('.item-' + workingTaskId);
    if ($taskRow.length > 0){
      this.activateTask($taskRow);
      this.timerStatus = localStorage.getItem("timerStatus");
      if (this.timerStatus) {
        $('.start-timer-btn').hide();
        $('.stop-timer-btn').show();
      }
    }else{
      this.workingTaskId = null;
      localStorage.removeItem("workingTaskId");
    }
  }

  createCheckExit() {
    return function () {
      if (POMODORO_RUNNING) {
        return "Pomodoro is running, are you sure you want to leave, you will lose your running cycle";
      }
    };
  }

  disableStartBtn() {
    $(this.startBtnTarget).animate({'hidden': true}, 200);
  }

  enableStartBtn() {
    $(this.startBtnTarget).animate({'hidden': false}, 200);
  }

  switchPauseBtn(makeResume) {
    if (makeResume) {
      $(this.pauseBtnTarget).html("Resume").removeClass("btn-danger").addClass("btn-success");
    } else {
      $(this.pauseBtnTarget).html("Pause").removeClass("btn-success").addClass("btn-danger");
    }
  }

  addFiveMins() {
    if (this.isStateType('work')) {
      if (this.isState("running_work")) {
        this.thisWorkDuration += 300;
        this.thisWorkDurationTime = moment().startOf('day').add(this.thisWorkDuration, 's');
      } else {
        this.thisWorkDuration = 300;
        this.thisWorkDurationTime = moment().startOf('day').add(this.thisWorkDuration, 's');
        this.startWorkInterval();
      }
    } else {
      this.thisBreakDuration += 300;
      this.thisBreakDurationTime = moment().startOf('day').add(this.thisBreakDuration, 's');
    }
  }

  openGroup(evt) {
    let groupId = this.selectGroupTarget.value;
    let that = this;
    $.get({
      url: BASE_URL + "/master/pomodoro/open/" + groupId,
      success: function (response) {
        $('#pomodoroCyclesContainer').html(response.content);
        that.cycleGroupId = response.cycleGroupId;
        that.cycleIdList = response.cycleIdList;

        that.cyclesPassed = response.cyclesPassed;
        that.activeCycleIndex = response.activeCycleId;
        that.allReviewData = response.cycleReviewData;
        $('.scrollable-container').scrollLeft(0);
        that.scrollRight(that.activeCycleIndex);
        if (FIRST_WORK === "true") {
          that.startSecondTour();
        }
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  saveAll(evt, callback) {
    let that = this;
    let cyclesData = [];
    this.cycleChildTargets.forEach(function (cycleTarget) {
      let cycleController = that.application.getControllerForElementAndIdentifier(cycleTarget, "pomodoro-cycle");
      that.childControllers[cycleController.cycleId] = cycleController;
      let newData = cycleController.getIfUpdated();
      if (newData.data) {
        cyclesData.push(newData);
      }
    });
    if (cyclesData) {
      let saveData = {
        'cyclesData': cyclesData,
        'cycleGroupId': this.cycleGroupId
      };
      $.post({
        url: BASE_URL + "/master/pomodoro/save",
        data: JSON.stringify(saveData),
        headers: {'X-CSRFToken': getCsrf()},
        success: function (response) {
          if (callback) {
            callback();
          }
        },
        error: function (err) {
          console.log(err);
        }
      });
    }
  }

  controlButtons(action) {
    if (action === 'disable') {
      $('.pomodoro-controls').find('button').prop('disabled', true);
      return;
    }
    if (action === 'enable') {
      $('.pomodoro-controls').find('button').prop('disabled', false);
    }
  }

  saveAndStart(evt) {
    POMODORO_RUNNING = true;
    MyTrack('pomodoro-start');
    let that = this;
    this.saveAll(0, function () {
      that.disableStartBtn();
      that.startCycle(evt);
      that.controlButtons('enable');
    });
  }

  generateCycles() {
    MyTrack('pomodoro-generate');
    let data = {
      cycleCount: this.cycleCountTarget.value,
      workDuration: this.workDurationTarget.value,
      breakDuration: this.breakDurationTarget.value,
      questionWhat: this.inputQ1Target.value,
      questionHow: this.inputQ2Target.value,
      projectId: this.projectSelectTarget.value
    };
    let saveUrl = BASE_URL + "/master/pomodoro/generate";
    let that = this;
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        $('#pomodoroCyclesContainer').html(response.content);
        that.cycleGroupId = response.cycleGroupId;
        that.cycleIdList = response.cycleIdList;
        that.activeCycleId = that.cycleIdList[0];
        that.activeCycleIndex = 0;
        if (FIRST_WORK === "true") {
          that.startSecondTour();
        }
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  startSecondTour() {
    let intro = introJs();
    intro.setOptions({
      'showProgress': true,
      'scrollToElement': false,
      'showStepNumbers': false,
      'tooltipPosition': 'auto',
      'showBullets': false,
      steps: [
        {
          intro: "Decide what you will work on and think how you're going to start. This will jumpstart your productivity.",
          element: '.intro-step-2-1'
        },
        {
          intro: "Control your session from here.",
          element: ".intro-step-2-2"
        },
        {
          intro: "When ready click Start.",
          element: '.intro-step-2-3'
        },
      ]
    });
    intro.start();
    intro.oncomplete(function () {
      MyTrack('tour-pomodoro-completed');
    });
    intro.onexit(function () {
      let currentStep = intro._currentStep;
      MyTrack('tour-pomodoro-exit', {exitStep: currentStep});
    });
  }

  toggleAutoPlay(evt) {
    this.autoPlay = evt.target.checked;
  }

  pausePomodoroTimer(){
    this.switchPauseBtn(true);
      if (this.isState("running_work")) {
        clearInterval(this.workHandle);
        this.stateStatus = 'paused_work';
      }
      if (this.isState('running_break')) {
        clearInterval(this.breakHandle);
        this.stateStatus = 'paused_break';
      }
  }

  pauseResumeCycle() {
    if (this.stateStatus.startsWith('paused')) {
      this.switchPauseBtn(false);

      if (this.isState('paused_break')) {
        this.startBreak();
        return;
      }

      if (this.isState('paused_work')) {
        this.startCycle();
        return;
      }
    } else {
      this.pausePomodoroTimer();
    }
  }

  stopBreak() {
    clearInterval(this.breakHandle);
  }

  stopWork() {
    clearInterval(this.workHandle);
  }

  gatherReviewData(){
    let data = {
      done: this.reviewAccomplishedTarget.value,
      energy: this.reviewEnergyTarget.value,
      review: this.reviewTextTarget.value,
      timeWorked: this.timerCounter
    };
    if(this.assignPomodoroTimeTarget.value){
      data.taskId = this.workingTaskId;
    }
    this.allReviewData.push(data);

    if(this.finishSequence || this.cyclesCount === this.cyclesPassed){
      data.finishSession = true;
    }

    return data;
  }

  getActiveCycleId(){
    let cycleIdValue = this.cycleIdList[this.activeCycleIndex];
    if(!cycleIdValue){
      cycleIdValue = this.cycleIdList[this.activeCycleIndex-1];
    }
    return cycleIdValue;
  }

  saveReview() {
    let data = this.gatherReviewData();
    let cycleIdValue = this.getActiveCycleId();

    let that = this;
    $.post({
      url: BASE_URL + "/master/pomodoro/single/" + cycleIdValue,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        $('#reviewModal').modal('hide');
        that.updateChildControllerData(cycleIdValue, data);
        that.reviewSaved();
      },
      error: function (err) {
        $(that.reviewErrorTarget).html("Error saving cycle data, contact support at darko@lifehqapp.com");
        console.log(err);
      }
    });
  }

  updateChildControllerData(cycleId, data) {
    this.childControllers[cycleId].updateReviewData(data);
  }

  reviewSaved() {
    this.stopWork();
    if (this.timerCounter !== 0) {
      this.cyclesPassed += 1;
    }
    this.timerCounter = 0;
    if(this.finishSequence){
      POMODORO_RUNNING = false;
      this.showSummary();
      return;
    }
    if (this.cyclesCount === this.cyclesPassed) {
      this.notifyMe("All Cycles finished. Take a longer break.");
      POMODORO_RUNNING = false;
      this.showSummary();
      return;
    }
    this.startBreak();
  }

  calcEnergyScores(energy) {
    let height, color;
    if (energy === 'low') {
      height = 10;
      color = "red";
    }
    if (energy === 'medium') {
      height = 40;
      color = "orange";
    }
    if (energy === 'high') {
      height = 80;
      color = "green";
    }
    return {height: height, color: color};
  }

  calcTargetHtml(target, index, baseLeft){
    let resultHtml = "";
    let left = baseLeft + 15 + index * 80;
    if(target === 'no'){
       resultHtml = "<div class=\"target\" style=\"left: "+ left +";color:red\">" +
      "                    <i class=\"fas fa-times\"></i>\n" +
      "                </div>";
    }
    if(target === 'half'){
      resultHtml = "<div class=\"target half\" style=\"left:"+ (left+5) +";\">-</div>";
    }
    if(target === 'yes'){
      resultHtml = "<div class=\"target\" style=\"left:"+ left +";color:green;\">" +
      "                    <i class=\"fas fa-check\"></i>" +
      "                </div>";
    }
    return resultHtml;
  }

  showSummary() {
    $('body').removeClass('modal-open');
    $('.modal-backdrop').remove();
    let headersHtml = "";
    let energyHtml = "";
    let targetsHtml = "";
    let i = 0, baseLeft = 116;
    let that = this;
    this.allReviewData.forEach(function(data){
      headersHtml += "<div class='review-header' style='left:"+(baseLeft + i * 80)+"'>Cycle " + (i+1) + "</div>";
      let energy = that.calcEnergyScores(data.energy);
      energyHtml += " <div class=\"vertical-bar\" style='height:"+energy.height+";background-color:"+energy.color+";left:"+(baseLeft + i * 80)+"'></div>";
      targetsHtml += that.calcTargetHtml(data.done, i, baseLeft);
      i += 1;
    });
    let fullHtml = "<div class=\"card review-pomodoro\">\n" +
      "    <div class=\"card-header\">Review session</div>\n" +
      "    <div class=\"card-body\">\n" +
      "        <div class=\"row\">\n" +
      "            <div class=\"col-md-8\">\n" +
                        headersHtml +
      "            </div>\n" +
      "        </div>\n" +
      "        <div class=\"row\">\n" +
      "            <div class=\"col-md-8\">\n" +
      "                <div class=\"stats-container\">" +
      "                <div class=\"chart-title\" style='bottom: 30px;'>Energy</div>" +
                        energyHtml +
      "                </div>\n" +
      "            </div>\n" +
      "        </div>\n" +
      "        <div class=\"row\">\n" +
      "         <div class=\"col-md-8\">\n" +
      "            <div class='targets-container'> " +
      "            <div class=\"chart-title\">Targets</div>\n" +
                        targetsHtml +
      "            </div>" +
      "            </div>" +
      "        </div>\n" +
      "        <div class='row'> " +
      "         <div class='col-md-6'>" +
      "           <div class=\"row\">\n" +
      "                  <button data-saction='pomodoro-master#showPomodoroSetup' class='btn btn-outline-primary'>New session</button>" +
      "    </div>\n" +
      "</div>";
    $('#pomodoroCyclesContainer').html(fullHtml);
  }

  showPomodoroSetup(){
    let fullUrl = BASE_URL + '/work/pomodoro/setup';
    let that = this;
    $.get({
      url: fullUrl,
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        $('#pomodoroCyclesContainer').html(response.content);
        that.resetAll();
        $('.selectpicker').selectpicker();
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  initNextBtn() {
    if (this.isStateType('work')) {
      $(this.nextBtnTarget).html("Review & Start Break");
      return;
    }
    if (this.isStateType('break')) {
      $(this.nextBtnTarget).html("Start Next Cycle");
      return;
    }
  }

  reviewShowActiveItemTitle(){
      let activeItemTitle = $('li.task-active').find('.item-title').text().slice(0, 20) + "...";
      $('#reviewModal .chosenTaskTitle').html(activeItemTitle);
  }

  nextCycle() {
    this.finishSequence = false;
    $(this.nextBtnInfoTarget).hide();
    this.breakCounter = 0;
    this.switchPauseBtn(false);

    if (this.isStateType('work')) {
      this.reviewShowActiveItemTitle();
      $('#reviewModal').modal('show');
    } else if (this.isStateType('break')) {
      this.timerCounter = 0;
      this.stopBreak();
      this.activeCycleIndex += 1;
      this.startCycle();
    }
  }

  breakStatus(currentTime, totalTime) {
    return "Break time: " + currentTime.format('mm:ss') + " / " + totalTime.format('mm:ss');
  }

  startBreak() {
    this.stateStatus = 'running_break';
    this.stateType = 'break';
    this.breakStartTime = moment().startOf('day').add(this.breakCounter, 's');
    this.thisBreakDuration = this.breakDuration;
    this.initNextBtn();
    let that = this;
    that.thisBreakDurationTime = moment().startOf('day').add(that.thisBreakDuration, 's');
    $(that.timerInfoTarget).html(that.breakStatus(that.breakStartTime, that.thisBreakDurationTime));
    $(this.cycleInfoTarget).html("Running: Break " + (this.cyclesPassed));
    if (this.isState('paused_break')) {
      this.notifyMe("Resuming Break");
    } else {
      this.scrollRight();
    }
    this.breakHandle = setInterval(function () {
      that.breakCounter += 1;
      that.breakStartTime.add(1, 's');
      let progressStyle = (100 * that.breakCounter / that.thisBreakDuration) + "%";
      $(that.timerTarget).css("width", progressStyle);
      $(that.timerInfoTarget).html(that.breakStatus(that.breakStartTime, that.thisBreakDurationTime));
      if (that.breakCounter === that.thisBreakDuration) {
        clearInterval(that.breakHandle);
        that.breakCounter = 0;
        this.stateStatus = "finished_break";
        if (that.autoPlay) {
          that.startCycle();
        } else {
          $(that.nextBtnInfoTarget).show();
        }
      }
    }, 1000);
  }

  isState(someState) {
    return this.stateStatus === someState;
  }

  isStateType(someState) {
    return this.stateType === someState;
  }

  isLast() {
    let thisOne = this.cyclesPassed + 1;
    return this.cyclesCount === thisOne;
  }

  initAndNotifyCycle(evt) {
    if (this.firstCycle) {
      this.workDuration = parseInt(evt.target.dataset.duration);
      this.breakDuration = parseInt(evt.target.dataset.break);
      this.cyclesCount = parseInt(evt.target.dataset.cycleCount);
      console.log("Work: " + this.workDuration);
      console.log("Break: " + this.breakDuration);
      this.firstCycle = false;
    } else if (this.isState('paused_work')) {
      this.notifyMe("Resuming Cycle " + (this.cyclesPassed + 1));
    } else {
      let msg = "";
      if (this.isLast()) {
        msg = "Starting Work on last Cycle " + (this.cyclesPassed + 1) + " finish strong!";
      } else {
        msg = "Starting Work on Cycle " + (this.cyclesPassed + 1);
      }
      this.notifyMe(msg);
    }
    $(this.cycleInfoTarget).html("Running: Cycle " + (this.cyclesPassed + 1));
  }

  workStatus(currentTime, totalTime) {
    return "Work time: " + currentTime.format('mm:ss') + " / " + totalTime.format('mm:ss');
  }

  startCycle(evt) {
    this.stateStatus = 'running_work';
    this.stateType = 'work';
    this.workStartTime = moment().startOf('day').add(this.timerCounter, 's');
    this.initAndNotifyCycle(evt);
    this.initNextBtn("work");
    let that = this;
    $(that.timerInfoTarget).html("Work time: " + that.workStartTime.format('mm:ss'));
    this.thisWorkDuration = this.workDuration;
    this.thisWorkDurationTime = moment().startOf('day').add(this.thisWorkDuration, 's');
    $(this.timerInfoTarget).html(this.workStatus(this.workStartTime, this.thisWorkDurationTime));

    this.startWorkInterval();
    this.allowNotifications();
  }

  startWorkInterval() {
    let that = this;
    this.workHandle = setInterval(function () {
      that.timerCounter += 1;
      that.workStartTime.add(1, 's');
      let progressStyle = (100 * that.timerCounter / that.thisWorkDuration) + "%";
      $(that.timerTarget).css("width", progressStyle);
      $(that.timerInfoTarget).html(that.workStatus(that.workStartTime, that.thisWorkDurationTime));
      if (that.timerCounter === Math.floor(that.thisWorkDuration / 2)) {
        that.notifyMe("Cycle " + that.cyclesPassed + " Half way there");
      }
      if (that.timerCounter >= that.thisWorkDuration) {
        that.timerCounter = 0;
        that.cyclesPassed += 1;
        clearInterval(that.workHandle);
        that.stateStatus = "finished_work";
        if (that.cyclesPassed === that.cyclesCount) {
          that.notifyMe("All Cycles finished. Take a longer break.");
          POMODORO_RUNNING = false;
          return;
        }
        that.notifyMe("Work cycle finished, take a break");
        if (that.autoPlay) {
          that.startBreak();
        } else {
          $(that.nextBtnInfoTarget).show();
        }
      }
    }, 1000);
  }


  scrollRight(howMuch) {
    let cardWidth = $('.card.cycle-list').outerWidth();
    if (Number.isInteger(howMuch)) {
      this.scroller = $('.scrollable-container').scrollLeft() + cardWidth * howMuch + 5;
    } else {
      this.scroller = $('.scrollable-container').scrollLeft() + cardWidth + 5;
    }
    $('.scrollable-container').animate({scrollLeft: this.scroller}, 200);
  }

  scrollLeft() {
    this.scroller = $('.scrollable-container').scrollLeft();
    if (this.scroller > 0) {
      let cardWidth = $('.card.cycle-list').outerWidth();
      this.scroller = $('.scrollable-container').scrollLeft() - (cardWidth + 5);
      $('.scrollable-container').animate({scrollLeft: this.scroller}, 200);
    }
  }

  finishSession(evt) {
    evt.preventDefault();
    this.finishSequence = true;
    this.pausePomodoroTimer();
    this.reviewShowActiveItemTitle();
    $('#reviewModal .btnSaveReview').text('Finish Session');
    $('#reviewModal').modal('show');
  }

  notifyMe(message) {
    var notification = new Notification(message);
  }

  allowNotifications() {
    if (Notification.permission === "granted") {
      return;
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission().then(function (permission) {
        // If the user accepts, let's create a notification
        if (permission === "granted") {
          console.log("granted");
        }
      });
    }
  }

  pickTask(evt) {
    if (this.timerStatus){
      return;
    }
    let $row = $(evt.target).parents('li');
    this.activateTask($row);
  }

  switchIcons($row){
    $('.task-active .action-play').html('<i class="fas fa-play-circle"></i>');
    $('.task-active').removeClass('task-active');
    $row.find('.action-play').html('<i class="fas fa-circle"></i>');
    $row.addClass('task-active');
  }

  activateTask($row) {
    this.switchIcons($row);
    let itemId = $row.data('itemId');
    this.workingTaskId = itemId;

    let projectTitle = $row.find('.item-project').html() || "None";

    let that = this;
    this.getItemDetails(itemId, function (response) {
      let minutesWorked = parseInt(response.item.minutes_worked_today);
      localStorage.setItem("workingTaskId", itemId);
      localStorage.setItem("workingTaskMinutes", minutesWorked);
      $('#pick-task-info').hide();
      that.fillTaskInfo(response.item, projectTitle);
    }, function (err){
      console.log("Error getting item details ");
      console.log(err);
    });
  }

  fillTaskInfo(item, projectTitle) {
    let taskDescription = item.description;
    let taskTitle = item.title;
    this.prevMinutesWorked = parseInt(item.minutes_worked_today);

    $(this.timerProjectTitleTarget).html(projectTitle);
    $(this.timerTaskTitleTarget).html(taskTitle);
    $(this.timerTaskDescriptionTarget).html(taskDescription);
    $(this.timerTaskWorkedTarget).html(this.calcTimeWorked(this.prevMinutesWorked));
  }



  calcTimeWorked(minutesWorked){
    let hours = Math.floor(minutesWorked / 60);
    let minutes = minutesWorked - (hours * 60);
    let response = "";
    if (hours > 0) {
      response += hours + "h ";
    }
    if (minutes > 0) {
      response += minutes + "m";
    }
    return response;
  }

  getItemDetails(itemId, successClb, errorClb) {
    let url = `${BASE_URL}/master/todo/item/${itemId}`;
    $.get({
      url: url,
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        successClb(response);
      },
      error: function (err) {
        errorClb(err);
      }
    });
  }

}
