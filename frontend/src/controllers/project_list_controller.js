/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['newForm', 'deadline', 'projectContainer', 'projectDeadline'];

  toggleForm(event) {
    if(event)
      event.preventDefault();
    this.newFormTarget.classList.toggle("hidden");
  }

  initialize() {
    let startTime = moment().add(7, 'days');
    startTime.set('minute', 0);

    if (window.location.hash) {
      let hash = window.location.hash.substr(1);
      if (hash === "new") {
        this.toggleForm();
      }
    }

    $('.datepicker').datetimepicker({
      format: 'MM/DD/YYYY',
      icons: datepickerIcons,
      defaultDate: startTime
    });
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
