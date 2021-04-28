/*jshint esversion: 6 */
// eslint-disable-next-line import/no-unresolved
import {Controller} from "stimulus";
import {Calendar} from "@fullcalendar/core/main";
import interaction from "@fullcalendar/interaction";
import dayGrid from "@fullcalendar/daygrid";
import timeGrid from "@fullcalendar/timegrid";

export default class extends Controller {
  static targets = ['reviewContainer', 'projectSelector', 'calendarContainer'];

  initialize() {
    let $projectSelector = $(this.projectSelectorTarget);
    $projectSelector.select2();
    $projectSelector.on('change', this.selectProject(this));
    this.projectName = $projectSelector.children("option:selected").text();
    this.projectId = $projectSelector.val();
    this.$activeDay = $('.day-card').first();
    this.initSortable();
    console.log("Initializing plan week ctrl");
    if(FIRST_WEEK_PLAN === "true"){
      FIRST_WEEK_PLAN = "false";
      $('.alert-info-mine').removeClass('hidden');
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': true,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "Plan your tasks for every day of the week.",
            element: ".intro-step-1"
          },
          {
            intro: 'Choose tasks from your projects and add them to the active day.',
            element: '.intro-step-2'
          },
          {
            intro: "Click the bulls-eye button so project tasks go into that day.",
            element: ".intro-step-3"
          },
          {
            intro: "Create new tasks here and drag & drop between days.",
            element: ".intro-step-4-1"
          },
        ]
      });
      intro.start();
    }
  }


  initSortable() {
    let that = this;
    $('.sortable').sortable({
      connectWith: ".sortable",
      placeholder: "placeholder",
      update: function(event, ui){
        let targetListDate = $(event.target).data('listDate');
        let newIndex = that.calcNewIndex(ui.item);
        let postData = {
          index: newIndex,
          itemId: ui.item.data("itemId"),
          newListId: targetListDate,
          listType: 'day'
        };
        console.log(postData);
        that.reorder(postData);
      },
    });
  }

  calcNewIndex($item) {
    let prevIndex = Number($item.prev().data('itemIndex') || 0);
    let newIndex;
    if ($item.next().length) {
      let nextIndex = Number($item.next().data('itemIndex'));
      newIndex = (prevIndex + nextIndex) / 2;
    } else {
      newIndex = prevIndex + 1;
    }
    return newIndex;
  }

  reorder(postData) {
    $.post({
      url: BASE_URL + "/master/todo/reorder",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(postData),
      success: function (response) {
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  scrollRight() {
    let cardWidth = $('.scrollable-container .card').outerWidth();
    this.scroller = $('.scrollable-container').scrollLeft() + cardWidth + 5;
    $('.scrollable-container').animate({scrollLeft: this.scroller}, 200);
  }

  scrollLeft() {
    this.scroller = $('.scrollable-container').scrollLeft();
    if (this.scroller > 0) {
      let cardWidth = $('.scrollable-container .card').outerWidth();
      this.scroller = $('.scrollable-container').scrollLeft() - (cardWidth + 5);
      $('.scrollable-container').animate({scrollLeft: this.scroller}, 200);
    }
  }

  connect() {
    let that = this;
    $(".selectpicker").selectpicker();
  }

  reloadProjectList(projectId, targetElement) {
    let that = this;
    $.get({
      url: BASE_URL + "/master/todo/reload/week/" + projectId,
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        targetElement.html(response);
        that.initSortable();
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  selectProject(ctx) {
    return function () {
      ctx.projectId = ctx.projectSelectorTarget.value;
      ctx.projectName = $(ctx.projectSelectorTarget).children("option:selected").text();
      ctx.reloadProjectList(ctx.projectId, $(ctx.reviewContainerTarget));
    };
  }

  createMoveableRow(newItem) {
    return '<li class="item-table-row item-' + newItem.id + '" data-item-id="' + newItem.id + '"' +
      '                      data-project-id="' + this.projectId + '" data-project-list-id="' + newItem.projectListId + '"' +
      ' data-item-index="' + newItem.index + '" data-list-date="' + newItem.listDate + '" >' +
      '<div>' +
      '<span class="item-text"><span data-saction="click->master-todo-item#itemEdit" class="item-title">' + newItem.title +
      ' </span> <span class="badge badge-warning item-project"> ' + this.projectName + '</span> </span>' +
      '</div>' +

      '<div class="item-actions">\n' +
      '<span class="clickable action-play text-danger" data-saction="click->master-todo-item#deletePlanItem"><i class="fas fa-times"></i></span>\n' +
      '<span class="clickable" data-saction="click->master-todo-item#itemEdit">\n' +
      '  <i class="fas fa-edit"></i>\n' +
      ' </span>\n' +
      '</div>' +
      '</li>';
  }

  indexFromList($targetDay) {
    let listRows = $targetDay.find('ul li.item-table-row');
    if (listRows.length)
      return Number(listRows.last().data('itemIndex')) + 1;
    else
      return 1;
  }

  calcNewItemDestination() {
    let newIndex = this.indexFromList(this.$activeDay);
    let targetDay = this.$activeDay;
    return {
      'index': newIndex,
      'targetDay': targetDay,
      'listDate': this.$activeDay.data('listDate')
    };
  }

  copyItem(evt) {
    if ($(evt.target).closest('tr').hasClass('added-row')) {
      console.log("Already added");
      return;
    }
    let $projectRow = $(evt.target).closest('tr');
    let that = this;
    let newItemData = this.calcNewItemDestination();
    let data = {
      itemId: $projectRow.data('itemId'),
      index: newItemData.index,
      listDate: newItemData.listDate,
      projectListId: $projectRow.data('listId'),
      projectId: this.projectId
    };
    $.post({
      url: BASE_URL + "/master/todo/transfer-week",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(data),
      success: function (response) {
        let mRow = that.createMoveableRow(response.item);
        let $destinationDay = newItemData.targetDay.find('ul');
        $destinationDay.append(mRow);
        $projectRow.addClass("added-row");
        $projectRow.removeClass("review-list-row");
        $projectRow.find(".item-icon").html("Added");
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  selectDay(evt) {
    this._backToNormalPrev();
    this._activateNewDay(evt);
  }

  _backToNormalPrev() {
    $('.day-card.active').removeClass('active');
  }

  _activateNewDay(evt){
    let $selectedDay = $(evt.target).closest('.day-card');
    $selectedDay.addClass("active");
    this.$activeDay = $selectedDay;
  }

}
