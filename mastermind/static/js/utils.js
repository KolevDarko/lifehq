$('#sidebarCollapse').on('click', function () {
  $('.sidebar.main-sidebar').toggleClass('mobile-active');
});

function getCsrf() {
  let csrfEl = document.getElementsByName("csrfmiddlewaretoken")[0];
  return csrfEl.value;
}

var POMODORO_RUNNING = false;

function MyTrack(event_name, extras) {
  // if (USER_EMAIL !== 'kolevdarko@gmail.com' && USER_EMAIL !== 'kolevdarko.work@gmail.com') {
  //   mixpanel.track(USER_EMAIL, event_name, extras);
  // }
}

var MOMENT_DATE_FORMAT = "MM/DD/Y";

var datepickerIcons = {
  time: "fa fa-clock-o",
  date: "fa fa-calendar",
  up: "fa fa-chevron-up",
  down: "fa fa-chevron-down",
  previous: 'fa fa-chevron-left',
  next: 'fa fa-chevron-right',
  today: 'fa fa-screenshot',
  clear: 'fa fa-trash',
  close: 'fa fa-remove'
};

//notifications
function showNotification(msg, color, icon, duration) {
  if (!duration) {
    duration = 3000;
  }
  $.notify({
    icon: icon,
    message: msg

  }, {
    type: color,
    timer: duration,
    placement: {
      from: 'top',
      align: 'right'
    }
  });
}

function showSuccessNotification(msg) {
  showNotification(msg, "success", "notifications");
}

function showDeleteNotification(msg) {
  showNotification(msg, "danger", "notifications", 2000);
}

function showFailureNotification(msg) {
  showNotification(msg, "danger", "error");
}

function spinnerHtml(){
  return "<div class=\"cssload-loader\">\n" +
    "\t<div class=\"cssload-inner cssload-one\"></div>\n" +
    "\t<div class=\"cssload-inner cssload-two\"></div>\n" +
    "\t<div class=\"cssload-inner cssload-three\"></div>\n" +
    "</div>";
}
