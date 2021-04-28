/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['morning', 'midday', 'evening', 'morningEnabled', 'middayEnabled', 'eveningEnabled', 'morningInfo', 'middayInfo', 'eveningInfo', 'utcOffset', 'remindersUpdated'];

  initialize() {
    let morningTime = moment(this.morningTarget.value, 'HH:mm');
    let middayTime = moment(this.middayTarget.value, 'HH:mm');
    let eveningTime = moment(this.eveningTarget.value, 'HH:mm');

    $(this.morningTarget).datetimepicker({
      format: 'HH:mm',
      stepping: 30,
      icons: datepickerIcons,
      defaultDate: morningTime
    });

    $(this.middayTarget).datetimepicker({
      format: 'HH:mm',
      icons: datepickerIcons,
      stepping: 30,
      defaultDate: middayTime
    });

    $(this.eveningTarget).datetimepicker({
      format: 'HH:mm',
      icons: datepickerIcons,
      stepping: 30,
      defaultDate: eveningTime
    });
  }

  morningToggle(){
    let texts = {
      true: "On",
      false: "Off"
    };
    this.morningTarget.disabled = !this.morningEnabledTarget.checked;
    $(this.morningInfoTarget).text(texts[this.morningEnabledTarget.checked]);
  }
  middayToggle(){
    let texts = {
      true: "On",
      false: "Off"
    };
    this.middayTarget.disabled = !this.middayEnabledTarget.checked;
    $(this.middayInfoTarget).text(texts[this.middayEnabledTarget.checked]);
  }
  eveningToggle(){
    let texts = {
      true: "On",
      false: "Off"
    };
    this.eveningTarget.disabled = !this.eveningEnabledTarget.checked;
    $(this.eveningInfoTarget).text(texts[this.eveningEnabledTarget.checked]);
  }

  saveReminders(){
    let postData = {
      morningEnabled: this.morningEnabledTarget.checked,
      middayEnabled: this.middayEnabledTarget.checked,
      eveningEnabled: this.eveningEnabledTarget.checked,
      morning: this.morningTarget.value,
      midday: this.middayTarget.value,
      evening: this.eveningTarget.value,
      utcOffset: this.utcOffsetTarget.value
    };
    let that = this;
    $.post({
      url: BASE_URL + '/reminders/',
      data: JSON.stringify(postData),
      headers: { 'X-CSRFToken': getCsrf()},
      success: function (response) {
        let el = $(that.remindersUpdatedTarget);
        el.text("Reminders updated");
        el.addClass('mt-5 success-box');
      },
      error: function (error) {
        console.log(error);
      }
    });
  }

}
