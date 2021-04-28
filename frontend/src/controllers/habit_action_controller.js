/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['box'];
  contents = {
    0: {
      text: "",
      klas: "empty"
    },
    1: {
      text: "<i class=\"fas fa-check\">",
      klas: "yes"
    },
    2: {
      text: "-",
      klas: "half"
    },
    3: {
      text: "<i class=\"fas fa-times\">",
      klas: "no"
    },
  };

  values = [0, 1, 2, 3];

  values_map = {
    '0': 0,
    '1': 1,
    '2': 0.5,
    '3': 0
  };

  updateText() {
    let data = this.contents[this.status];
    this.$box.html(data.text);
    this.$box.removeClass();
    this.$box.addClass(data.klas);
  }

  connect() {
    this.status = parseInt(this.data.get("status"));
    this.actionId = this.data.get("id");
    this.$box = $(this.boxTarget);
    this.updateText();
  }

  barColor(score) {
    if (score < 20)
      return "indianred";

    if (score <= 50)
      return "orange";

    if (score <= 75)
      return "lightgreen";

    return "green";
  }

  updateChartView(dayScore, position){
    let newPercent = dayScore * 100;
    let chartPercentHeight = newPercent + 50;
    let $myChartPercent = $('div.habits-stats').find('.bar-percent-'+position);
    $myChartPercent.css('bottom', chartPercentHeight + 'px');
    $myChartPercent.text(newPercent.toFixed(2)+'%');

    let chartHeight = dayScore * 100 + 10;
    let $myChartBar = $('div.habits-stats').find('.chart-bar-'+position);
    let newColor = this.barColor(newPercent);
    $myChartBar.animate({
      'height': chartHeight
    }, 500);
    $myChartBar.css({'background-color': newColor});
  }

  updateChart(){
    let $parentRow = this.$box.closest('.habit-row');
    let position = $parentRow.find('td').index(this.$box.parent());
    let $cousins = $('.habit-full-container').find('td.box-'+position);
    let totalScore = 0;
    let that = this;
    let allScores = [];
    this.$box.data('habitActionStatus', this.status);
    $cousins.each(function(){
      let scoreId = $(this).children().first().data('habitActionStatus');
      if(scoreId !== undefined){
        let thisScore = that.values_map[scoreId];
        totalScore += thisScore;
        allScores.push(thisScore);
      }
    });
    let dayScore = totalScore / allScores.length;
    this.updateChartView(dayScore, position);
  }

  switch() {
    this.status = (this.status + 1) % 4;
    let data = {
      status: this.status,
      actionId: this.actionId,
    };
    let saveUrl = BASE_URL + "/habits/action";
    let that = this;
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        that.updateText();
        that.updateChart();
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

}
