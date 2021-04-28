/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ["eventForm", "startTime", "endTime", "startDate", "endDate", "title", "description", "eventsDetails", "eventEnd", "formTitle", "saveButton", "deleteButton", "toggleEndBox"];

  eventFilter(start, end) {
    return function(eventObj){
      return event.start >= start && event.start <= end;
    };
  }

  rowEl(value, klass){
    let rez = $('<div/>', {
      'html': value,
      'class': klass
    }).wrap("<p/>").parent().html();
    return rez;
  }

  createRow(event, container, allDay, eventStart, eventEnd) {
    let dateInfo = '';
    if (eventStart && eventEnd) {
      eventStart = moment(eventStart);
      eventEnd = moment(eventEnd);
      dateInfo = 'Starts: ' + eventStart.format('hh:mm a') + ' - Ends: ' + eventEnd.format('hh:mm a');
    }
    if (allDay) {
      dateInfo = 'Ongoing';
    }
    if(eventStart && !eventEnd){
      eventStart = moment(eventStart);
      dateInfo = 'Starts at ' + eventStart.format('hh:mm a');
    }
    if(eventEnd && !eventStart) {
      eventEnd = moment(eventEnd);
      dateInfo = 'Ends at ' + eventEnd.format('hh:mm a');
    }

    let rezEl = '<div class="row schedule-event" data-saction="click->project-schedule#showEditForm" data-event-pos="'+ event.eventPos +'"> '+
                  '<div class="col-md-6 schedule-event__content" >'+
                    '<div class="schedule-event__title">'+ event.title+
                    '</div>'+
                    '<div class="schedule-event__description">'+event.description+
                    '</div>'+
                    '<div class="schedule-event__dates">'+dateInfo+
                    '</div>'+
                  '</div>'+
                '</div>';

    $(rezEl).appendTo(container);
  }

  updateControlLabels(){
    this.formTitleTarget.innerText = "Edit event";
    this.saveButtonTarget.innerText = "Update event";
    this.deleteButtonTarget.classList.remove('hidden');
    this.eventFormTarget.classList.remove("hidden");
  }

  updateControlValues(event){
    this.titleTarget.value = event.title;
    this.descriptionTarget.value = event.description;
    let startDate = moment(event.start);
    $(this.startDateTarget).data("DateTimePicker").date(startDate);
    $(this.startTimeTarget).data("DateTimePicker").date(startDate);
    if (event.end){
      let endDate = moment(event.end);
      $(this.endDateTarget).data("DateTimePicker").date(endDate);
      $(this.endTimeTarget).data("DateTimePicker").date(endDate);
      $(this.toggleEndBoxTarget).prop('checked', true);
      this.eventEndTarget.classList.remove("hidden");
      this.hasEnd = true;
    }else{
      $(this.toggleEndBoxTarget).prop('checked', false);
      this.eventEndTarget.classList.add("hidden");
      this.hasEnd = false;
    }

  }

  showEditForm(evt) {
    evt.preventDefault();
    let $target = $(evt.target).closest('.row.schedule-event');
    let fEvents = this.$calendar.fullCalendar('clientEvents');
    let event = fEvents[$target.data('eventPos')];
    this.eventId = event.id;
    this.editingEvent = true;
    this.updateControlLabels(event);
    this.updateControlValues(event);
    window.location = "#formAnchor";
  }

  labelsCreate() {
    this.formTitleTarget.innerText = "New event";
    this.saveButtonTarget.innerText = "Create event";
    this.deleteButtonTarget.classList.add('hidden');
    this.eventFormTarget.classList.remove("hidden");
  }

  controlsEmpty() {
    this.titleTarget.value = '';
    this.descriptionTarget.value = '';
    let startDate = moment().add(1, 'hours');
    startDate.set('minute', 0);
    $(this.startDateTarget).data("DateTimePicker").date(startDate);
    $(this.startTimeTarget).data("DateTimePicker").date(startDate);
    $(this.toggleEndBoxTarget).prop('checked', false);
    this.eventEndTarget.classList.add("hidden");
    startDate.add(1, 'hours');
    $(this.endDateTarget).data("DateTimePicker").date(startDate);
    $(this.endTimeTarget).data("DateTimePicker").date(startDate);
  }

  showCreateForm(evt){
    evt.preventDefault();
    this.eventId = null;
    this.editingEvent = false;
    this.labelsCreate();
    this.controlsEmpty();
  }

  initialize() {
    this.hasEnd = false;
    this.projectId = this.data.get("projid");

    this.editingEvent = false;
    this.eventId = null;

    this.$calendar = $('#fullProjectCalendar');

    let today = new Date();
    let y = today.getFullYear();
    let m = today.getMonth();
    let d = today.getDate();
    let that = this;
    this.$calendar.fullCalendar({
      viewRender: function (view, element) {
        // We make sure that we activate the perfect scrollbar when the view isn't on Month
        if (view.name !== 'month') {
          $(element).find('.fc-scroller').perfectScrollbar();
        }
      },
      // timezone: 'local',
      timezone: 'local',
      header: {
        left: 'title',
        center: 'month',
        right: 'prev,next,today'
      },
      defaultDate: today,
      selectable: true,
      selectHelper: true,
      views: {
        month: { // name of view
          titleFormat: 'MMMM YYYY'
          // other view-specific options here
        },
        week: {
          titleFormat: " MMMM D YYYY"
        },
        day: {
          titleFormat: 'D MMM, YYYY'
        }
      },

      eventRender: function (eventObj, $el) {
        // $el.popover({
        //   title: eventObj.title,
        //   content: "from " + eventObj.start.format("h:mm a") + " to " + eventObj.end.format('h:mm a'),
        //   trigger: 'click',
        //   placement: 'top',
        //   container: 'body'
        // });
      },

      select: function (start, end) {
        //make start and end into local timezone
        let tzOffset = new Date().getTimezoneOffset();
        // start.add(tzOffset, 's');
        // end.add(tzOffset, 's');
        let fEvents = that.$calendar.fullCalendar('clientEvents');
        let container = $(that.eventsDetailsTarget);
        container.html('<h2 class="schedule-event__day"> '+ start.format('ddd, MMMM Do')+'</h2>');
        let groupedByDay = {};
        start = start.valueOf() + tzOffset*60000;
        end = end.valueOf() + tzOffset*60000;
        for(let i = 0; i < fEvents.length; i++){
            let ev = fEvents[i];
            ev.eventPos = i;
            ev.start = ev.start.valueOf();
            if (ev.end)
              ev.end = ev.end.valueOf();

            if (ev.start < start && ev.end && ev.end > end){ //ongoing
              that.createRow(ev, container, true);
              continue;
            }
            if (ev.start >= start && (ev.end && ev.end < end)){ //contained
              that.createRow(ev, container, false, ev.start, ev.end);
              continue;
            }
            if (ev.start >= start && ev.start < end && (ev.end && ev.end > end || !ev.end && ev.start < end)){ //beginning
              that.createRow(ev, container, false, ev.start, false);
              continue;
            }
            if (ev.start < start && ev.end >= start && ev.end < end) { // ending
              that.createRow(ev, container, false, false, ev.end);
            }
        }
        window.location = "#dayDetails";
      },
      editable: false,
      eventLimit: true,
      // color classes: [ event-blue | event-azure | event-green | event-orange | event-red ]
      events: BASE_URL + '/projects/' + this.projectId + '/event',
    });

    let startTime = moment().add(1, 'hours');
    startTime.set('minute', 0);

    $('.datepicker').datetimepicker({
      format: 'MM/DD/YYYY',
      icons: datepickerIcons,
      defaultDate: startTime
    });

    $(this.startTimeTarget).datetimepicker({
      format: 'h:mm A',
      icons: datepickerIcons,
      stepping: 15,
      defaultDate: startTime
    });

    startTime.add(1, 'hours');

    this.endTimePicker =  $(this.endTimeTarget).datetimepicker({
      format: 'h:mm A',    //use this format if you want the 12hours timpiecker with AM/PM toggle
      icons: datepickerIcons,
      stepping: 15,
      defaultDate: startTime
    });
  }

  toggleEnd(){
    this.eventEndTarget.classList.toggle("hidden");
    this.hasEnd = !this.hasEnd;
  }

  toggleEventForm(evt) {
    evt.preventDefault();
    this.eventFormTarget.classList.toggle("hidden");
  }

  createFullDate(_dateTarget, _timeTarget){
    let dateRes = $(_dateTarget).data("DateTimePicker").date();
    let timeRes = $(_timeTarget).data("DateTimePicker").date();
    dateRes.hours(timeRes.hours());
    dateRes.minutes(timeRes.minutes());
    return dateRes;
  }

  createEvent(evt) {
    let startDate = this.createFullDate(this.startDateTarget, this.startTimeTarget);
    let postData = {
      title : this.titleTarget.value,
      description: this.descriptionTarget.value,
      start: startDate.format(),
    };
    if(this.hasEnd){
      postData.end = this.createFullDate(this.endDateTarget, this.endTimeTarget).format();
    }
    let that = this;
    let url = BASE_URL + '/projects/' + this.projectId + '/event';
    if(this.eventId){
      url += "/" + this.eventId;
    }
    $.post({
      url: url,
      data: JSON.stringify(postData),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        // that.$calendar.fullCalendar('renderEvent', postData, true);
        that.$calendar.fullCalendar('refetchEvents');
        window.scrollTo(0,document.body.scrollHeight);
        that.eventFormTarget.classList.toggle("hidden");
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  deleteEvent(evt) {
    evt.preventDefault();
    if (confirm("Are you sure you want to delete this event?")) {
      let that=this;
      $.ajax({
        method: 'DELETE',
        url: BASE_URL + '/projects/' + this.projectId + '/event/' + this.eventId,
        headers: {'X-CSRFToken': getCsrf()},
        success: function (rez) {
          // that.$calendar.fullCalendar('renderEvent', postData, true);
          that.$calendar.fullCalendar('refetchEvents');
          that.eventFormTarget.classList.add("hidden");
        },
        error: function (err) {
          console.log(err);
        }
      });
    }
  }
}
