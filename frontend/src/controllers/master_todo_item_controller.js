/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ["todoItemForm", "itemTitle", "listId", "listContainer", "itemEditTitle", "itemEditModal",
    "itemEditSelectTask", "itemEditSelectProject", "itemEditDescription", "itemDescriptionShow", "itemDueDate"];

  initialize() {
    this.listType = this.data.get("listType");
    this.pageType = this.data.get("pageType");
    this.today_date = this.data.get("todayDate");
    this.PLAN = 'plan';
    this.WORK = 'work';
    this.DAY = 'day';
    this.editingItemId = null;
    console.log("Init of list type " + this.listType);
    let that = this;
    $(this.itemTitleTarget).keyup(function (evt) {
      if (evt.keyCode === 13) {
        if (that.pageType === 'plan') {
          that.createPlanItem(evt);
        } else {
          that.createWorkItem(evt);
        }
      }
    });

    this.$listSelect = $(this.itemEditSelectProjectTarget);
    this.$projectListSelect = $(this.itemEditSelectTaskTarget);
    this.$projectListSelect.select2();
    this.$listSelect.select2();
    this.$listSelect.on('change', this.changeItemProject(this));
  }

  changeItemProject(ctx) {
    return function (evt) {
      let projectId = this.value;
      let that = ctx;
      if (Number.parseInt(projectId) !== 0) {
        that.getProjectLists(projectId, function (result) {
          that.createListOptions(result.lists);
        }, function (err) {
          console.log("Could not load project task lists");
        });
      } else {
        that.createListOptions([]);
      }
    };
  }

  showEditDescription() {
    let $descriptionShow = $(this.itemDescriptionShowTarget);
    let $descriptionEdit = $(this.itemEditDescriptionTarget);
    $descriptionShow.html($descriptionEdit.val());
    $descriptionEdit.toggle();
    $descriptionShow.toggle();
  }


  setSelects(data) {
    this.$listSelect.val(data.itemProjectId);
    this.$listSelect.trigger('change');

    this.$projectListSelect.val(data.itemProjectListId);
    this.$projectListSelect.trigger('change');
  }

  fillModal(data) {
    this.editingItemId = data.itemId;
    this.itemEditTitleTarget.value = data.itemTitle;
    this.itemDueDateTarget.value = data.itemDueDate || moment().format(MOMENT_DATE_FORMAT);
    this.setSelects(data);

    $(this.itemEditDescriptionTarget).show();
    $(this.itemDescriptionShowTarget).hide();
    let that = this;
    this.getItemDetails(data.itemId, function (response) {
      let description = response.item.description;
      that.itemEditDescriptionTarget.value = description;
      if (response.item.description) {
        $(that.itemEditDescriptionTarget).hide();
        $(that.itemDescriptionShowTarget).html(description);
        $(that.itemDescriptionShowTarget).show();
      }
    }, function (err) {
      that.itemEditDescriptionTarget.value = "Error getting item description";
      console.log(err);
    });

    if (data.itemProjectListId) {
      this.getProjectLists(data.itemProjectId, function (response) {
        that.createListOptions(response.lists);
        that.$projectListSelect.val(data.itemProjectListId);
        that.$projectListSelect.trigger('change');
      }, function (err) {
        console.log(err);
      });
    } else {
      this.$projectListSelect.find('option').remove().end().append("<option value='0'>None</option>");
      this.$projectListSelect.trigger('change');
    }
  }

  getItemDetails(itemId, successClb, errorClb) {
    let url = `${BASE_URL}/master/todo/item/${itemId}`;
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

  itemEdit(evt) {
    let $row = $(evt.target).closest('li');
    let itemId = $row.data('itemId');
    let projectId = $row.data('projectId');
    let projectListId = $row.data('projectListId');
    let dueDate = $row.data('dueDate');
    let title = $row.find('.item-title').text();
    this.fillModal({
      'itemId': itemId,
      'itemTitle': title,
      'itemProjectId': projectId,
      'itemProjectListId': projectListId,
      'itemDueDate': dueDate
    });
    $(this.itemEditModalTarget).modal('show');
  }

  removeItemRow() {
    if (this.pageType === this.WORK) {
      $('li.item-' + this.editingItemId).closest('list-item-container').remove();
    } else {
      $('li.item-' + this.editingItemId).remove();
    }
  }

  updateItemViewRow() {
    let projectId = this.$listSelect.val();
    let projectName = this.$listSelect.find('option:selected').text();
    let projectListId = this.$projectListSelect.val();
    let itemId = this.editingItemId;
    let $item = $('.item-' + itemId);
    let newTitle = this.itemEditTitleTarget.value;
    $item.find('.item-title').text(newTitle);
    $item.data("projectId", projectId);
    $item.data("projectListId", projectListId);

    if (projectName === 'None') {
      $item.find('.item-text').find(".badge").remove();
    } else {
      let $existingProject = $item.find(".item-text").find(".badge");
      if ($existingProject.length > 0) {
        $existingProject.text(projectName);
      } else {
        $item.find(".item-text").append(" <span class=\"badge badge-warning item-project\">" + projectName + "</span>");
      }
    }
  }

  saveEditItem(evt) {
    let projectListId = this.$projectListSelect.val();
    let data = {
      'project_list_id': projectListId,
      'title': this.itemEditTitleTarget.value,
      'description': this.itemEditDescriptionTarget.value,
      'dueDate': this.itemDueDateTarget.value
    };
    let itemId = this.editingItemId;
    let url = `${BASE_URL}/master/todo/item/${itemId}`;
    let that = this;
    $.ajax({
      url: url,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      method: 'PUT',
      success: function (rez) {
        if (that.listType === that.DAY) {
          that.updateItemViewRow();
        } else {
          if (moment(data.dueDate) > moment(that.today_date)) {
            that.removeItemRow();
          } else {
            that.updateItemViewRow();
          }
        }
        $(that.itemEditModalTarget).modal('hide');
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  deleteItem(evt) {
    if (confirm("Are you sure you want to remove this task?")) {
      let that = this;
      $.ajax({
        url: BASE_URL + '/todos/item/' + that.editingItemId,
        method: 'DELETE',
        headers: {'X-CSRFToken': getCsrf()},
        success: function (rez) {
          window.location = '/projects';
        }
      });
    }
  }

  toggleNewItem() {
    this.todoItemFormTarget.classList.toggle("hidden");
    $(this.itemTitleTarget).focus();
  }


  createCheckRow(newItem) {
    return '<div class="item-container" data-item-id="' + newItem.id + '">\n' +
      '                  <div class="form-check">\n' +
      '                    <label class="form-check-label">\n' +
      '                      <input data-item-id="' + newItem.id + '"\n' +
      '                             data-saction="master-todo-item#complete"\n' +
      '                             class="form-check-input" type="checkbox"\n' +
      '                             value="">\n' +
      '                      <span class="form-check-sign">\n' +
      '                          <span class="check"></span>\n' +
      '                      </span>\n' +
      '                    </label>\n' +
      '                  </div>\n' +
      '                  <li class="item-table-row item-' + newItem.id + '" data-item-id="' + newItem.id + '"\n' +
      '                      data-list-id="' + newItem.listId + '" data-item-index="' + newItem.index + '">\n' +
      '                    <div class="item-text">\n' +
      '                      <span class="item-title">' + newItem.title + '</span>' +
      '                    </div>\n' +
      '                    <div class="item-actions">\n' +
      '                      <span class="clickable action-play text-success" data-saction="click->pomodoro-master#pickTask">\n' +
      '                        <i class="fas fa-play-circle"></i>\n' +
      '                      </span>\n' +
      '                      <span class="clickable" data-saction="click->master-todo-item#itemEdit">\n' +
      '                        <i class="fas fa-edit"></i>\n' +
      '                      </span>\n' +
      '                    </div>\n' +
      '                  </li>\n' +
      '                </div>';
  }

  createMoveableRow(newItem) {
    return '<li class="item-table-row item-' + newItem.id + '" data-item-id="' + newItem.id + '"' +
      ' data-item-index="' + newItem.index + '" data-list-date="' + newItem.listDate + '" >' +
      '<div>' +
      '<span class="item-text"><span class="item-title">' + newItem.title +
      ' </span> </span>' +
      '</div>' +
      '<div class="item-actions">\n' +
      '<span class="clickable action-play text-danger" data-saction="click->master-todo-item#deletePlanItem"><i class="fas fa-times"></i></span>\n' +
      '<span class="clickable" data-saction="click->master-todo-item#itemEdit">\n' +
      '  <i class="fas fa-edit"></i>\n' +
      ' </span>\n' +
      '</div>' +
      '</li>';
  }



  createWorkItem(evt) {
    let listId = this.listIdTarget.value;
    let csrfEl = document.getElementsByName("csrfmiddlewaretoken")[0];
    let csrf = csrfEl.value;
    let title = this.itemTitleTarget.value;
    let that = this;
    let $tableWork = $(this.listContainerTarget).find("ul.work-list");
    let lastIndex = Number($tableWork.find('tr').last().data('itemIndex') || 0) + 1;
    let data = {
      title: title,
      listId: listId,
      index: lastIndex
    };
    $.post({
      url: BASE_URL + '/master/todo/item/',
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': csrf},
      success: function (response) {
        let row = that.createCheckRow(response.item);
        $tableWork.append(row);
        $(evt.target).closest(".item-form").find(".item-input").val("");
        $(evt.target).closest(".item-form").find(".item-input").focus();
      },
      error: function (err) {
        console.log("some error");
        console.log(err);
      }
    });
  }

  createPlanItem(evt) {
    let listId = this.listIdTarget.value;
    let csrfEl = document.getElementsByName("csrfmiddlewaretoken")[0];
    let csrf = csrfEl.value;
    let title = this.itemTitleTarget.value;
    let $tablePlan = $(this.listContainerTarget).find('ul.sortable');
    let lastIndex = Number($tablePlan.find('li').last().data('itemIndex') || 0) + 1;
    let that = this;
    $.post({
      url: BASE_URL + '/master/todo/item/',
      data: JSON.stringify({
        title: title,
        listId: listId,
        index: lastIndex,
        listType: this.listType
      }),
      headers: {'X-CSRFToken': csrf},
      success: function (response) {
        let row = that.createMoveableRow(response.item);
        $tablePlan.append(row);
        $(evt.target).closest(".item-form").find(".item-input").val("");
        $(evt.target).closest(".item-form").find(".item-input").focus();
      },
      error: function (err) {
        console.log("some error");
        console.log(err);
      }
    });
  }

  complete(evt) {
    evt.preventDefault();
    evt.stopPropagation();
    let isCompleted = evt.target.checked;
    if (isCompleted) {
      this.completeIt(evt.target);
    } else {
      this.uncompleteIt(evt.target);
    }
  }

  completeIt(target) {
    let $container = $(target).closest('.item-container');
    let itemId = $container.data('itemId');
    $.post({
      url: BASE_URL + '/master/todo/complete/' + itemId,
      data: JSON.stringify({
        completed: true
      }),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        let tableCompleted = $container.closest(".personal-list-do").find("ul.table-completed");
        tableCompleted.append($container);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  uncompleteIt(target) {
    let $container = $(target).closest('.item-container');
    let itemId = $container.data('itemId');
    $.post({
      url: BASE_URL + '/master/todo/complete/' + itemId,
      data: JSON.stringify({
        completed: false
      }),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        let tableActive = $(target).closest(".personal-list-do").find("ul.work-list");
        tableActive.append($container);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  deleteWorkItem(evt) {
    evt.preventDefault();
    let $parentRow = $(evt.target).closest('tr');
    let itemId = $parentRow.data('itemId');
    let that = this;
    this.deleteMasterItem(itemId, function (rez) {
        $parentRow.remove();
      },
      function (err) {
        console.log("failed to delete item");
      }
    );
  }


  deletePlanItem(evt) {
    evt.preventDefault();
    let $parentRow = $(evt.target).closest('li');
    let itemId = $parentRow.data('itemId');
    this.deleteMasterItem(itemId, function (rez) {
        $parentRow.remove();
        if (rez.project_item_id) {
          let $projectRow = $('.project-item-' + rez.project_item_id);
          $projectRow.removeClass('added-row');
          $projectRow.addClass('review-list-row');
          $projectRow.find(".item-icon").html("<i class=\"material-icons btn-transfer-todo bg-success\">keyboard_arrow_right</i>");
        }
      },
      function (err) {
        console.log("failed to delete item");
      }
    );
  }

  deleteModalItem() {
    let that = this;
    this.deleteMasterItem(this.editingItemId, function () {
      $('li.item-' + that.editingItemId).remove();
      $(that.itemEditModalTarget).modal('hide');
    }, function (err) {
      console.log("Error deleting item");
      console.log(err);
    });
  }

  postponeModalItem(evt) {
    let that = this;
    let projectListId = this.$projectListSelect.val();
    let data = {
      'project_list_id': projectListId,
      'title': this.itemEditTitleTarget.value,
      'description': this.itemEditDescriptionTarget.value,
      'due': this.itemDueDateTarget.value
    };
    let itemId = this.editingItemId;
    let url = `${BASE_URL}/master/todo/item/${itemId}`;
    $.ajax({
      url: url,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      method: 'PUT',
      success: function (rez) {
        $('li.item-' + that.editingItemId).remove();
        $(that.itemEditModalTarget).modal('hide');
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  showDatepicker() {
    let dueDatepicker = $(this.itemDueDateTarget);
    if (dueDatepicker.hasClass('on')) {
      dueDatepicker.data("DateTimePicker").show();
    } else {
      let startDate;
      if (this.itemDueDateTarget.value !== 'None') {
        startDate = moment(this.itemDueDateTarget.value);
      } else {
        startDate = moment();
      }
      $('.due-datepicker').datetimepicker({
        format: 'MM/DD/YYYY',
        icons: datepickerIcons,
        defaultDate: startDate
      });
      $('.due-datepicker').data("DateTimePicker").show();
      dueDatepicker.addClass('on');
    }
  }

  deleteMasterItem(itemId, successFunc, errorFunc) {
    $.ajax({
      url: BASE_URL + '/master/todo/item/' + itemId,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: successFunc,
      error: errorFunc,
    });
  }

  createListOptions(lists) {
    let $container = this.$projectListSelect;
    $container.find('option').remove();
    if (lists.length) {
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
}
