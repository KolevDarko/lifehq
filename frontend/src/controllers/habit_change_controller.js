/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ['habitName'];

  initialize(){
    this.habitId = this.data.get("habitId");
    this.habitSchedule = this.data.get("schedule");
  }

  showEditHabit(){
    this.fillHabitModal();
  }

  fillHabitModal(){
    this.habitModal = $("#newHabitModal");
    this.habitModal.find(".card-title").text("Edit Habit");
    this.habitModal.find('.btn-success').text("Save");
    this.habitModal.find("#habitTitle").val(this.habitNameTarget.innerText);
    this.habitModal.find("#editHabitId").val(this.habitId);
    this.fillCheckboxes();
    this.habitModal.modal('show');
  }

  fillCheckboxes(){
    for(var i = 0; i < this.habitSchedule.length; i++){
      let theCheckbox = $('.check-'+i);
      if(parseInt(this.habitSchedule[i])){
        theCheckbox.prop('checked', true);
      }else{
        theCheckbox.prop('checked', false);
      }
    }
  }

  showArchiveHabit(){
    let fullTitle = "Are you sure you want to archive habit: <span style='font-weight:bold'>" +
      this.habitNameTarget.innerText + "</span> ?";
    $('#archiveHabitTitle').html(fullTitle);
    $('#archiveHabitId').val(this.habitId);
    $('#archiveHabitModal').modal('show');
    $('#editHabitId').val(this.habitId);
  }

}
