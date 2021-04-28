/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {

  static targets = ["newHabitTitle", "habitModal", "container", "actionRow", "editHabitName", "editHabitId",
    "archiveHabitId", "schedule", "habitError"];


  connect() {
    this.$container = $(this.containerTarget);
    let that = this;
    $(this.newHabitTitleTarget).keyup(function (evt) {
      if (evt.keyCode === 13) {
        that.createHabit(evt);
      }
    });
  }

  initialize() {
    if (FIRST_HABIT === "true") {
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': false,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "Mark your completed habits every day and create the green success chain. Then it's easy, just don't break the chain.",
            element: ".intro-step-1"
          },
          {
            intro: 'The squares have 3 states: yes, no and half, click to toggle.',
            element: '.intro-step-2'
          },
          {
            intro: 'Review your success across all habits and aim to improve every day.',
            element: '.intro-step-3'
          },
          {
            intro: 'The system analyses your weekly average and offers intelligent advice',
            element: '.intro-step-4'
          },

        ]
      });
      intro.oncomplete(function () {
        MyTrack('tour-habit-completed');
      });
      intro.onexit(function () {
        let currentStep = intro._currentStep;
        MyTrack('tour-habit-exit', {exitStep: currentStep});
      });
      intro.start();
    }
  }

  showNewHabit(evt) {
    this.habitModal = $("#newHabitModal");
    this.habitModal.find(".card-title").text("New Habit");
    this.habitModal.find('.btn-success').text("Create");
    $(this.newHabitTitleTarget).val("");
    $(this.editHabitIdTarget).val("");
    this.fillAllCheckboxes();
    this.habitModal.modal('show');
  }

  fillAllCheckboxes() {
    for (let i = 0; i <= 6; i++) {
      let theCheckbox = $('.check-' + i);
      theCheckbox.prop('checked', true);
    }
  }


  addHabitRow(habitStruct, todayWeekday) {
    let habitName = habitStruct.habit.name;
    let habitId = habitStruct.habit.id;
    let habitActions = habitStruct.action_list;
    let newRow = "<tr data-controller='habit-change' data-habit-change-habit-id=" + habitId + " data-habit-change-schedule=" + habitStruct.habit.schedule + " class='habit-row habit-"+habitId+"'>\n" +
      "<td><div class='habit-name habit-name-" + habitId + "' " +
      " data-target='habit-change.habitName'>" + habitName + "</div></td>\n";
    for (let i = 0; i < habitActions.length; i++) {
      let hAction = habitActions[i];
      let thisWeekday = i + 1;
      let cell;
      if (hAction.id === null) {
        cell = '<td class="habit-status today box-"' + thisWeekday + '></td>';
      } else {
        if (thisWeekday === todayWeekday) {
          cell = "<td class=\"habit-status today box-" + thisWeekday + " \">\n";
        } else {
          cell = "<td class=\"habit-status box-" + thisWeekday + "\">\n";
        }
        cell += "<div data-controller=\"habit-action\" data-target=\"habit-action.box\"\n" +
          "     data-habit-action-status=\"0\"\n" +
          "     data-habit-action-id=\"" + hAction.id + "\"\n" +
          "     data-saction=\"click->habit-action#switch\"></div>\n" +
          "    </td>";
      }
      newRow += cell;
    }

    newRow += "<td class=\"td-actions text-right\">\n" +
      "<button data-saction=\"habit-change#showEditHabit\" title=\"edit\" type=\"button\" rel=\"tooltip\" class=\"btn btn-success\">\n" +
      "    <i class=\"material-icons\">edit</i>\n" +
      "</button>\n" +
      "<button data-saction=\"habit-change#showArchiveHabit\" title=\"archive\" type=\"button\" rel=\"tooltip\" class=\"btn btn-danger\">\n" +
      "    <i class=\"material-icons\">close</i>\n" +
      "</button>\n" +
      "</td></tr>";
    return newRow;
  }

  getSchedule() {
    let fullSchedule = "";
    this.scheduleTargets.forEach(function (item) {
      if (item.checked) {
        fullSchedule += "1";
      } else {
        fullSchedule += "0";
      }
    });
    console.log("Full schedule is " + fullSchedule);
    return fullSchedule;
  }

  showError(errMsg) {
    $(this.habitErrorTarget).text(errMsg);
  }

  createHabit(evt) {
    evt.preventDefault();
    if (!this.newHabitTitleTarget.value) {
      this.showError("Habit name is required");
      return;
    }
    let scheduleEncoded = this.getSchedule();
    if (scheduleEncoded === "0000000") {
      this.showError("Schedule cannot be empty");
      return;
    }

    if (this.editHabitIdTarget.value) {
      this.updateHabit(scheduleEncoded);
    } else {
      this.createNewHabit(scheduleEncoded);
    }
  }

  createNewHabit(scheduleEncoded) {
    debugger;
    let data = {
      name: this.newHabitTitleTarget.value,
      schedule: scheduleEncoded
    };
    let saveUrl = BASE_URL + '/habits/habit';
    let that = this;
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        let newRow = that.addHabitRow(response.habit_struct, response.weekday);
        $(that.actionRowTarget).before(newRow);
        $(that.habitModalTarget).modal('hide');
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  updateHabit(newSchedule) {
    debugger;
    let data = {
      id: this.editHabitIdTarget.value,
      name: this.newHabitTitleTarget.value,
      schedule: newSchedule
    };
    let saveUrl = BASE_URL + '/habits/habit';
    let csrfToken = getCsrf();
    let that = this;
    console.log("Working with token " + csrfToken);
    $.ajax({
      type: 'PUT',
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': csrfToken},
      success: function (response) {
        let hStruct = response.habit_struct;
        let habit = response.habit_struct.habit;
        $(that.habitModalTarget).modal('hide');
        $('.habit-name-' + habit.id).text(habit.name);
        if(hStruct.action_list){
          let newRow = that.addHabitRow(hStruct, response.weekday);
          let existingRow = '.habit-'+habit.id;
          $(existingRow).replaceWith(newRow);
        }
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  archiveHabit(evt) {
    evt.preventDefault();
    let data = {
      id: this.archiveHabitIdTarget.value,
    };
    let saveUrl = BASE_URL + '/habits/habit';
    $.ajax({
      type: 'DELETE',
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        $('#archiveHabitModal').modal('hide');
        $('.habit-name-' + data.id).closest('tr').hide("slow").html("");
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

}
