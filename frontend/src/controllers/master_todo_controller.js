/*jshint esversion: 6 */
// eslint-disable-next-line import/no-unresolved
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['reviewContainer', 'projectSelector', 'personalListsContainer'];

  initialize() {
    let $projectSelector = $(this.projectSelectorTarget);
    this.projectName = $projectSelector.children("option:selected").text();
    this.projectId = $projectSelector.val();
    $(".selectpicker").selectpicker();
    this.initSortable();
    if (FIRST_TODAY === "true") {
      FIRST_TODAY = "false";
      $('.alert-info-mine').removeClass('hidden');
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': false,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "These three lists hold all your tasks for the day.",
            element: ".intro-step-1"
          },
          {
            intro: 'Choose from your projects and transfer tasks to the daily lists',
            element: '.intro-step-2'
          },
          {
            intro: 'You can reorder the tasks and move them between lists with drag & drop',
            element: '.planing-personal-cards .personal-list-container tbody.important-list td.sortable-icon:first-child'
          },
          {
            intro: 'When finished, go to the Work tab to start working',
            element: '.intro-step-4'
          },
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
  }


  initSortable() {
    let that = this;
    $('.sortable').sortable({
      connectWith: ".sortable",
      placeholder: "placeholder",
      update: function(event, ui){
        let targetListId = $(event.target).data('listId');
        let newIndex = that.calcNewIndex(ui.item);
        let postData = {
          index: newIndex,
          itemId: ui.item.data("itemId"),
          newListId: targetListId,
          listType: 'personal'
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

  reloadProjectList(projectId, targetElement) {
    $.get({
      url: BASE_URL + "/master/todo/reload/" + projectId,
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        targetElement.html(response);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  selectProject(evt) {
    this.projectId = this.projectSelectorTarget.value;
    this.projectName = $(this.projectSelectorTarget).children("option:selected").text();
    this.reloadProjectList(this.projectId, $(this.reviewContainerTarget));
  }

  createMoveableRow(newItem) {
    return '<li class="item-table-row item-' + newItem.id + '" data-item-id="' + newItem.id + '"' +
      '                      data-project-id="' + this.projectId + '" data-project-list-id="' + newItem.projectListId + '"' +
      ' data-item-index="' + newItem.index + '" data-list-id="'+ newItem.listId +'" >' +
      '<span class="item-text"><span data-saction="click->master-todo-item#itemEdit" class="item-title">' + newItem.title +
      ' </span> <span class="badge badge-warning item-project"> ' + this.projectName + '</span> </span></li>';
  }

  indexFromList($targetList) {
    if ($targetList.find('ul li').length)
      return Number($targetList.find('ul li').last().data('itemIndex')) + 1;
    else
      return 1;
  }

  calcNewItemDestination() {
    let newIndex, newList, $targetTable;
    let $urgentList = $('.personal-list-plan.secondary-list');
    if ($urgentList.find('ul li').length < 3) {
      newIndex = this.indexFromList($urgentList);
      newList = $urgentList.data('listId');
      $targetTable = $urgentList;
    } else {
      let $importantList = $('.personal-list-plan.important-list');
      if ($importantList.find('ul li').length < 3) {
        newIndex = this.indexFromList($importantList);
        newList = $importantList.data('listId');
        $targetTable = $importantList;
      } else {
        let $extraList = $('.personal-list-plan.extra-list');
        newIndex = this.indexFromList($extraList);
        newList = $extraList.data('listId');
        $targetTable = $extraList;
      }
    }
    return {
      'index': newIndex,
      'list': newList,
      'targetTable': $targetTable
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
      projectListId: $projectRow.data('listId'),
      index: newItemData.index,
      personalListId: newItemData.list,
    };
    $.post({
      url: BASE_URL + "/master/todo/transfer",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(data),
      success: function (response) {
        let mRow = that.createMoveableRow(response.item);
        let $targetTable = newItemData.targetTable.find('ul');
        $targetTable.append(mRow);
        $projectRow.addClass("added-row");
        $projectRow.removeClass("review-list-row");
        $projectRow.find(".item-icon").html("Added");
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  syncWeekPlanner(evt){
    evt.preventDefault();
    let that = this;
    $(this.personalListsContainerTarget).css('opacity', '0.6');
    $.post({
      url: BASE_URL + "/master/todo/sync",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify({}),
      success: function(response){
        $(that.personalListsContainerTarget).html(response.content).css('opacity', '1');
        that.initSortable();
      },
      error: function(err){
        console.log(err);
      }
    });
  }
}
