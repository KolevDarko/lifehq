/*jshint esversion: 6 */
// eslint-disable-next-line import/no-unresolved
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['filterProjectSelect', 'todaySessions', 'weekTime', 'weekSessions', 'todayCycles', 'weekCycles', 'weekAvgTime', 'weekAvgSessions', 'weekAvgCycles', 'errorBox', 'timeVal', 'timeName', 'timeValShow', 'timeNameShow',
  'manAddSelectProject', 'manAddSelectTaskList', 'tasksContainer', 'manualDay', 'manualMinutes', 'manualHours',
    'trackEditDate', 'trackEditMinutes', 'trackEditHours', 'trackEditTitle'];

  connect() {
    let $projectStatsSelector = $(this.filterProjectSelectTarget);
    this.mainProjectId = $projectStatsSelector.val();
    $projectStatsSelector.select2();
    $projectStatsSelector.on('change', this.filterProjectGen());
    $('.selectpicker').selectpicker();
    this.$projectListSelect = $(this.manAddSelectTaskListTarget);
    this.$tasksContainer = $(this.tasksContainerTarget);
    this.manualTaskId = 0;
    let that = this;
    if(this.mainProjectId === '0'){
      this.getPersonalTasks(function(result){
        that.clearTasksTable();
        that.$projectListSelect.find('option').remove();
        that.createTasks(result.tasks);
      }, function (err){
        console.log("Could not load personal tasks");
      });
    }
  }

  initialize() {
    let manualAddDatepicker = $('.datepicker');
    manualAddDatepicker.datetimepicker({
      format: 'MM/DD/YYYY',
      defaultDate: moment()
    });
  }

  showEditTrackModal(evt){
    let trackItem = $(evt.target);
    let trackDate = trackItem.data('trackDate');
    let timeWorked = this.toHoursMins(trackItem.data('trackMinutes'));
    let $parentRow = trackItem.parent('tr');
    let editTaskTitle = $parentRow.find('td.task-title').text();
    this.editItemId = $parentRow.data('itemId');
    this.editItemDate = trackDate;
    this.fillEditTrackModal(editTaskTitle, timeWorked, trackDate);
    $('#trackEditModal').modal('show');
  }

  toHoursMins(totalMinutes) {
    let value = parseInt(totalMinutes);
    let hours = Math.floor(value / 60);
    let minutes = value % 60;
    return {
      hours: hours,
      minutes: minutes
    };
  }

  fillEditTrackModal(editTaskTitle, timeWorked, trackDate){
    $(this.trackEditTitleTarget).text(editTaskTitle);
    this.trackEditMinutesTarget.value = timeWorked.minutes;
    this.trackEditHoursTarget.value = timeWorked.hours;
    $(this.trackEditDateTarget).text(trackDate);
  }

  saveEditTrack(){
    let fullUrl = `${BASE_URL}/work/todos/item/track/${this.editItemId}`;
    let postData = {
      trackMinutes: this.trackEditMinutesTarget.value,
      trackHours: this.trackEditHoursTarget.value,
      trackDate: this.editItemDate,
      projectId: this.mainProjectId
    };
    let that = this;
    $.ajax({
      method: 'PUT',
      url: fullUrl,
      data: JSON.stringify(postData),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(){
        that.reloadTracks();
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  reloadTracks() {
    let that = this;
    let chosenProjectId = $(that.filterProjectSelectTarget).val();
    let fullUrl = `${BASE_URL}/master/partial/stats/${chosenProjectId}`;
    $.get({
      url: fullUrl,
      success: function (response) {
        that.fillData(response);
        that.hideModalsCompletely();
      },
      error: function (err) {
        console.log(err.responseText);
      }
    });
  }

  clearTasksTable(){
    this.$tasksContainer.find('li').remove();
  }

  hookupManualTasksClicks(){
    let lis = $(this.tasksContainerTarget).find('li');
    let that = this;
    lis.click(function(evt){
      let $target = $(evt.target);
      that.manualTaskId = $target.data('id');
      lis.removeClass('active');
      $target.addClass('active');
      console.log("Just clicked " + $target.text());
    });
  }

  saveManualAdd(){
    let fullUrl = `${BASE_URL}/work/todos/item/track/${this.manualTaskId}/manual`;
    let selProjectId = this.manAddSelectProjectTarget.value;
    let selTaskListId = this.manAddSelectTaskListTarget.value;
    let postData = {
      'manualMinutes': this.manualMinutesTarget.value,
      'manualHours': this.manualHoursTarget.value,
      'manualDate': this.manualDayTarget.value,
      'manualTaskListId': selTaskListId,
      'manualProjectId': selProjectId
    };
    let that = this;
    $.post({
      url: fullUrl,
      data: JSON.stringify(postData),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(){
        that.reloadTracks();
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  filterProjectGen() {
    let that = this;
    return function changeCallback() {
      let chosenProjectId = $(that.filterProjectSelectTarget).val();
      let fullUrl = `${BASE_URL}/master/partial/stats/${chosenProjectId}`;
      $.get({
        url: fullUrl,
        success: function (response) {
          that.fillData(response);
          that.mainProjectId = chosenProjectId;
        },
        error: function (err) {
          console.log(err.responseText);
        }
      });
    };
  }

  fillData(fullResponse) {
    $('#master-container').html(fullResponse.content);
  }

  setRowData(name, stats) {
    let targetNames = [`${name}TimeTarget`, `${name}SessionsTarget`, `${name}CyclesTarget`];
    for (let i = 0; i < 3; i++) {
      $(this[targetNames[i]]).text(stats[i]);
    }
  }

  editTimeTarget() {
    $(".display-track-target").hide();
    $(".edit-track-target").show();
  }

  saveTimeTarget() {
    let postData = {
      timeTargetVal: this.timeValTarget.value,
      timeTargetName: this.timeNameTarget.value
    };
    let that = this;
    $.ajax({
      url: BASE_URL + '/projects/' + this.mainProjectId,
      method: 'PUT',
      data: JSON.stringify(postData),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        that.updateTrackView(postData);
        $(".edit-track-target").hide();
        $(".display-track-target").show();
      }
    });
  }

  updateTrackView() {
    $(this.timeValShowTarget).text(this.timeValTarget.value + ' h /');
    let newTypeName = $(this.timeNameTarget).find('option:selected').text();
    $(this.timeNameShowTarget).text(newTypeName);
  }

  showManualAddPopup(){
    $('#manualAddModal').modal('show');
  }

  hideManualAddPopup(){
    $('#manualAddModal').modal('hide');
  }

  hideEditModal(){
    $('#trackEditModal').modal('hide');
  }

  hideModalsCompletely(){
    this.hideEditModal();
    this.hideManualAddPopup();
    $('body').removeClass('modal-open');
    $('.modal-backdrop').remove();
  }

  changeManualAddProject(evt) {
    let projectId = evt.target.value;
    let that = this;
    if (Number.parseInt(projectId) !== 0) {
      this.getProjectLists(projectId, function (result) {
        that.createListOptions(result.lists);
        that.clearTasksTable();
      }, function (err) {
        console.log("Could not load project task lists");
      });
    } else {
      this.getPersonalTasks(function(result){
        that.clearTasksTable();
        that.$projectListSelect.find('option').remove();
        that.createTasks(result.tasks);
      }, function (err){
        console.log("Could not load personal tasks");
      });
    }
  }

  changeItemList(evt) {
    let taskListId = evt.target.value;
    let that = this;
    if (Number.parseInt(taskListId) !== 0) {
      this.getProjectListTasks(taskListId, function (result) {
        that.createTasks(result.tasks);
      }, function (err) {
        console.log("Could not load tasks");
      });
    } else {
      if (Number.parseInt(taskListId) === -1) {
        this.getPersonalTasks(function (result) {
          that.clearTasksTable();
          that.$projectListSelect.find('option').remove();
          that.createTasks(result.tasks);
        }, function (err) {
          console.log("Could not load personal tasks");
        });
      }
    }
  }

  createTasks(tasks){
    let $container = $(this.tasksContainerTarget);
    $container.find('li').remove();
    if (tasks.length){
      tasks.forEach(function (task) {
        let row = "<li data-id=\"" + task.id + "\">" + task.title + "</li>\n";
        $container.append(row);
      });
    }else{
      let row = "<li data-id='0'>No tasks</li>\n";
      $container.append(row);
    }
    this.hookupManualTasksClicks();
  }

  getPersonalTasks(successClb, errorClb) {
    let url = `${BASE_URL}/work/todos/personal`;
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

  getProjectLists(projectId, successClb, errorClb) {
    let url = `${BASE_URL}/projects/${projectId}/lists`;
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

  getProjectListTasks(listId, successClb, errorClb) {
    let url = `${BASE_URL}/todos/list/${listId}/items`;
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

  createListOptions(lists) {
    let $container = this.$projectListSelect;
    $container.find('option').remove();
    if (lists.length) {
      let row = "<option value='0'>None</option>\n";
      $container.append(row);
      lists.forEach(function (list) {
        let row = "<option value=\"" + list.id + "\">" + list.title + "</option>\n";
        $container.append(row);
      });
    } else {
      let row = "<option value='0'>None</option>\n";
      $container.append(row);
    }
    $container.selectpicker('refresh');
  }

}
