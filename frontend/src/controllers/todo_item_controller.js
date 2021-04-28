/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ["todoItemForm", "itemTitle", "listContainer", "listName", "editNameInput", "listId",
  "itemEditTitle", "itemEditModal", "itemEditSelectTask", "itemEditSelectProject", "sortableTable", "itemEditDescription",
  "itemDescriptionShow", "itemDueDate"];

  connect(){
    this.projectId = this.data.get('projid');
    this.listId = this.data.get("listId");
    this.$listSelect = $(this.itemEditSelectProjectTarget);
    this.$projectListSelect = $(this.itemEditSelectTaskTarget);
    this.initSelects();
    let that = this;
    this.initSortable();
     $(this.itemTitleTarget).keyup(function (evt){
       if (evt.keyCode === 13) {
         that.createNewItem(evt);
       }
     });
     this.NOT_SCHEDULED = '';
  }

  initSelects(){
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
          listType: 'day'
        };
        console.log(postData);
        that.reorder(postData);
      },
    });
  }

  toggleNewItem(){
    this.todoItemFormTarget.classList.toggle("hidden");
    $(this.itemTitleTarget).focus();
  }

  reloadList(listId, targetElement){
    let url = BASE_URL + "/todos/list/reload/"+listId;
    $.get({
      url: url,
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        targetElement.html(response);
      },
      error: function(err){
        console.log("Error reloading list");
        console.log(err);
      }
    });
  }

  deleteItem(evt){
    evt.preventDefault();
    let $parentRow = $(evt.target).closest('tr');
    let itemId = $parentRow.data('itemId');
    $.ajax({
      url: BASE_URL + '/todos/item/delete/' + itemId,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: function(rez){
        $parentRow.remove();
      },
      error:function (err) {
        console.log("failed to delete item");
      }
    });
  }

  deleteProjectItem(itemId, successClb, errorClb){
    $.ajax({
      url: BASE_URL + '/todos/item/delete/' + itemId,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: successClb,
      error: errorClb
    });
  }

  deleteModalItem() {
    let that = this;
    this.deleteProjectItem(this.editingItemId, function (response) {
      $('li.item-' + that.editingItemId).remove();
      $(that.itemEditModalTarget).modal('hide');
    }, function (err) {
      console.log("Error deleting item");
      console.log(err);
    });
  }

  createItemRow(item) {
    return '<li class="item-table-row item-'+item.id+'" data-item-id="'+item.id+'"\n' +
      '                    data-list-id="'+item.project_list_id+'" data-item-index="'+ item.project_list_order +'" data-project-id="'+item.project_id+'">\n' +
      '                                                                <span class="form-check">\n' +
      '                                                                    <label class="form-check-label">\n' +
      '                                                                        <input data-item-id="'+item.id+'"\n' +
      '                                                                               data-saction="todo-item#complete"\n' +
      '                                                                               class="form-check-input" type="checkbox"\n' +
      '                                                                               value="">\n' +
      '                                                                        <span class="form-check-sign">\n' +
      '                                                <span class="check"></span>\n' +
      '                                            </span>\n' +
      '                                                                    </label>\n' +
      '                                                                </span>\n' +
      '                                                                <span class="item-text"><span class="item-title">'+item.title+'</span>\n' +
      '                                                                </span>' +
      '                                                               <span class="clickable" data-saction="click->todo-item#itemEdit">\n' +
      '                                                                  <i class="fas fa-edit"></i>\n' +
      '                                                               </span>' +
      '                                                            </li>';
  }

  createNewItem(evt){
    let listId = this.listId;
    let projectId = this.data.get("projid");
    console.log("List is "+listId);
    let csrfEl = document.getElementsByName("csrfmiddlewaretoken")[0];
    let csrf = csrfEl.value;
    let title = this.itemTitleTarget.value;
    let $tableTasks = $(this.sortableTableTarget);
    let lastIndex = Number($tableTasks.find('li').last().data('itemIndex') || 0) + 1;
    let that = this;
    $.post({
      url: BASE_URL + '/projects/'+projectId+'/todos/'+listId+'/item',
      data: JSON.stringify({
        title: title,
        index: lastIndex
      }),
      headers: {'X-CSRFToken': csrf},
      success: function(response){
        let $parentCard = $(evt.target).closest(".todo-list-card");
        $parentCard.find('.todo-list-card__info-text').remove();
        let $parent = $parentCard.find("ul.sortable");
        let newRow = that.createItemRow(response.item);
        $parent.append(newRow);
        $(evt.target).closest(".item-form").find(".item-input").val("");
        $(evt.target).closest(".item-form").find(".item-input").focus();
      },
      error: function(err){
        console.log("some error");
        console.log(err);
      }
    });
  }

  complete(evt){
    let itemId = evt.target.dataset.itemId;
    let isCompleted = evt.target.checked;
    $.post({
      url: BASE_URL + '/todos/item/complete/'+itemId,
      data: JSON.stringify({
        completed: isCompleted
      }),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(rez){
        let $rowEl = $(evt.target).closest("li");
        let $textEl = $rowEl.find(".item-text");
        let tableCompleted = $(evt.target).closest(".todo-list-card").find(".table-completed");
        if (isCompleted) {
          $textEl.addClass("item-completed");
          $rowEl.find(".form-check-input").attr("disabled", true);
          tableCompleted.append($rowEl);
        } else {
          $textEl.removeClass("item-completed");
        }
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  archiveList(evt){
    let listId = this.listId;
    let projectId = this.data.get("projid");
    let url = BASE_URL + '/todos/list/archive/' + listId;
    let that = this;
    $.post({
      url: url,
      data: '',
      headers: {'X-CSRFToken': getCsrf()},
      success: function(){
        $('#archiveListModal-'+that.listId).modal('hide');
        that.reloadAllLists(that.projectId, $('div.todo-list-container'));
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  deleteList(evt){
    let listId = this.listId;
    let projectId = this.data.get("projid");
    let url = BASE_URL + '/todos/list/archive/' + listId;
    $(this.listContainerTarget).remove();
    let that = this;
    $.ajax({
      url: url,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: function(err){
        $('#deleteListModal-'+that.listId).modal('hide');
        that.reloadAllLists(that.projectId, $('div.todo-list-container'));
      }
    });
  }

  calcNewIndex($item){
    let prevIndex = Number($item.prev().data('itemIndex') || 0);
    let newIndex;
    if ($item.next().length) {
      let nextIndex = Number($item.next().data('itemIndex'));
      newIndex = (prevIndex + nextIndex) / 2;
    }else {
      newIndex = prevIndex + 1;
    }
    return newIndex;
  }

  reorder(postData) {
    $.post({
      url: BASE_URL + "/todos/item/reorder",
      headers: {'X-CSRFToken': getCsrf()},
      data: JSON.stringify(postData),
      success: function (response) {
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  showEditList(){
    let listName = this.listNameTarget.innerText;
    $('#editListModal').modal('show');
    $('#editListInput').val(listName);
    $('#editListId').val(this.listId);
  }

  saveListName(evt){
    evt.preventDefault();
    let data = {
      name: this.editNameInputTarget.value
    };
    let listId = this.listId;
    let url = BASE_URL + '/todos/list/archive/' + listId;
    let that = this;
    $.ajax({
      type: 'PUT',
      url: url,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        that.listNameTarget.innerText = data.name;
        $('#editListModal-'+listId).modal('hide');
      },
      error: function(err){
        console.log(err);
      }
    });
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

  showDatepicker() {
    let dueDatepicker = $(this.itemDueDateTarget);
    if (dueDatepicker.hasClass('on')) {
      dueDatepicker.data("DateTimePicker").show();
    } else {
      let startDate;
      if (this.itemDueDateTarget.value !== this.NOT_SCHEDULED) {
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

  fillModal(data) {
    this.editingItemId = data.itemId;
    this.itemEditTitleTarget.value = data.itemTitle;
    this.itemDueDateTarget.value = data.itemDueDate || this.NOT_SCHEDULED;
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

  itemEdit(evt){
    let that = this;
    let $row = $(evt.target).closest('li');
    let itemId = $row.data('itemId');
    let projectListId = $row.data('projectListId');
    let title = $row.find('.item-title').text();
    let dueDate = $row.data('dueDate');
    this.fillModal({
      'itemId': itemId,
      'itemTitle': title,
      'itemProjectId': that.projectId,
      'itemProjectListId': projectListId,
      'itemDueDate': dueDate
    });
    $(this.itemEditModalTarget).modal('show');
  }

  getProjectLists(projectId, successClb, errorClb){
    let url = `${BASE_URL}/projects/${projectId}/lists`;
    $.get({
      url: url,
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        successClb(response);
      },
      error: function(err){
        errorClb(err);
      }
    });
  }

  createListOptions(lists){
    let $container = this.$projectListSelect;
    $container.find('option').remove();
    lists.forEach(function(list){
      let row = "<option value=\""+list.id+"\">"+list.title+"</option>\n";
      $container.append(row);
    });
    $container.trigger('change');
  }

  saveEditItem(evt){
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
      success: function(rez){
        $(that.itemEditModalTarget).modal('hide');
        $('body').removeClass('modal-open');
        $('.modal-backdrop').remove();
        if(that.$listSelect.val() !== that.projectId){
          $('li.item-'+that.editingItemId).remove();
        }else {
          that.reloadAllLists(that.projectId, $('div.todo-list-container'));
        }
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  reloadAllLists(projectId, targetElement) {
    let url = BASE_URL + "/projects/"+projectId+"/todos/reload";
    $.get({
      url: url,
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        targetElement.html(response);
      },
      error: function(err){
        console.log("Error reloading project list section");
        console.log(err);
      }
    });
  }
}
