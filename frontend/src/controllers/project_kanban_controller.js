/*jshint esversion: 6 */
// eslint-disable-next-line import/no-unresolved
import {Controller} from "stimulus";
import {Calendar} from "@fullcalendar/core/main";
import interaction from "@fullcalendar/interaction";
import dayGrid from "@fullcalendar/daygrid";
import timeGrid from "@fullcalendar/timegrid";

export default class extends Controller {
  static targets = ["itemTitle", "itemEditTitle", "itemEditModal",
    "itemEditSelectList", "itemEditDescription", "itemDescriptionShow", "newListInput", "newListContainer"];

  connect() {
    console.log("Initializing project kanban");
    this.projectId = this.data.get("projectId");
    this.initSortable();
    this.$listSelect = $(this.itemEditSelectListTarget);
    this.$listSelect.select2();
  }

  showEditDescription() {
    let $descriptionShow = $(this.itemDescriptionShowTarget);
    let $descriptionEdit = $(this.itemEditDescriptionTarget);
    $descriptionShow.html($descriptionEdit.val());
    $descriptionEdit.toggle();
    $descriptionShow.toggle();
  }


  setSelects(data) {
    this.$listSelect.val(data.listId);
    this.$listSelect.trigger('change');
  }

  fillModal(data) {
    this.editingItemId = data.itemId;
    this.itemEditTitleTarget.value = data.itemTitle;
    this.setSelects(data);

    $(this.itemEditDescriptionTarget).show();
    $(this.itemDescriptionShowTarget).hide();
    let that = this;
    this.getItemDetails(data.itemId, function (response) {
      let description = response.item.description;
      that.itemEditDescriptionTarget.value = description;
      if (description) {
        $(that.itemEditDescriptionTarget).hide();
        $(that.itemDescriptionShowTarget).html(description);
        $(that.itemDescriptionShowTarget).show();
      }
    }, function (err) {
      that.itemEditDescriptionTarget.value = "Error getting item description";
      console.log(err);
    });
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
    let projectListId = $row.data('projectListId');
    let title = $row.find('.item-title').text();
    this.fillModal({
      'itemId': itemId,
      'itemTitle': title,
      'listId': projectListId,
    });
    $(this.itemEditModalTarget).modal('show');
  }

  updateItemViewRow() {
    let projectListId = this.$listSelect.val();
    let listName = this.$listSelect.find('option:selected').text();
    let itemId = this.editingItemId;
    let $item = $('.item-' + itemId);
    let newTitle = this.itemEditTitleTarget.value;
    $item.find('.item-title').text(newTitle);
    $item.data("projectListId", projectListId);
    let $existingList = $item.find('.badge');
    $existingList.text(listName);
  }

  saveEditItem(evt) {
    let projectListId = this.$listSelect.val();
    let data = {
      'project_list_id': projectListId,
      'title': this.itemEditTitleTarget.value,
      'description': this.itemEditDescriptionTarget.value
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
        that.updateItemViewRow();
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

  initSortable() {
    let that = this;
    $('.sortable').sortable({
      connectWith: ".sortable",
      placeholder: "placeholder",
      update: function (event, ui) {
        let targetListId = $(event.target).data('listId');
        let itemListId = ui.item.data("listId");
        if (targetListId === itemListId) {
          console.log("Not reordering " + targetListId);
          return;
        } else {
          console.log("Am reordering at " + targetListId);
        }
        let postData = {
          itemId: ui.item.data("itemId"),
          newListId: targetListId,
          listType: 'day'
        };
        console.log(postData);
        that.reorder(postData);
      }
    });

    $('.modal-kanban-list').sortable({
      items: "li:not(.ui-state-disabled)",
      placeholder: "placeholder",
      update: function (event, ui) {
        let listId = ui.item.data("listId");
        let newIndex = that.calcNewIndex(ui.item);
        let postData = {
          listId: listId,
          newIndex: newIndex
        };
        console.log(postData);
        that.reorderList(postData);
      }
    });
  }

  calcNewIndex($item) {
    let prevIndex = Number($item.prev().data('listIndex') || 0);
    let newIndex;
    if ($item.next().length) {
      let nextIndex = Number($item.next().data('listIndex'));
      newIndex = (prevIndex + nextIndex) / 2;
    } else {
      newIndex = prevIndex + 1;
    }
    return newIndex;
  }

  reorder(postData) {
    $.post({
      url: BASE_URL + "/todos/kanban/reorder/item",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(postData),
      success: function (response) {
        console.log("Reordered kanban item");
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  reorderList(postData) {
    $.ajax({
      method: 'PUT',
      url: BASE_URL + "/todos/kanban/list",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(postData),
      success: function (response) {
        console.log("Reordered kanban list");
      },
      error: function (err) {
        console.log(err);
      }
    });
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
      'listId': this.$activeDay.data('listId')
    };
  }

  saveNewList() {
    let kanbanListsNum = $(this.newListInputTarget).data('listsNum');
    let postData = {
      listName: this.newListInputTarget.value,
      listsNum: kanbanListsNum,
      projectId: this.projectId
    };
    $.post({
      url: BASE_URL + "/todos/kanban/list",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(postData),
      success: function (response) {
        location.reload();
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  showRenameList(evt) {
    let $cardContainer = $(evt.target).closest('.kanban-list');
    $cardContainer.find(".header-display").hide();
    $cardContainer.find(".header-edit").show();
    $cardContainer.find('.title-input').focus();
  }

  saveRename(evt) {
    let $cardContainer = $(evt.target).closest('.kanban-list');
    let editUrl = BASE_URL + "/todos/kanban/list";
    let postData = {
      listId: $cardContainer.data('listPk'),
      name: $cardContainer.find('input').val()
    };
    $.ajax({
      method: 'put',
      headers: {'X-CSRFToken': getCsrf()},
      url: editUrl,
      data: JSON.stringify(postData),
      success: function (response) {
        $cardContainer.find(".header-edit").hide();
        $cardContainer.find(".header-text").text(postData.name);
        $cardContainer.find(".header-display").show();
      },
      error: function (err) {
        console.log(err);
      }
    });
  }
}
