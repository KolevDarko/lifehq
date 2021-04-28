/*jshint esversion: 6 */
// eslint-disable-next-line import/no-unresolved
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ["todoListForm", "listTitle", "itemTitle", "listId"];

  connect(){
    let that = this;
    $(this.listTitleTarget).keyup(function (evt){
       if (evt.keyCode == 13) {
         that.submitListForm(evt);
       }
     });
    $("body").click(function(){
      $('.dropdown-menu').removeClass("show");
    });

    $(".my-drop").click(function(evt){
      evt.stopPropagation();
      let $parent = $(this).parent();
      let $menu =  $parent.find('.dropdown-menu');
      let hasClass = $menu.hasClass("show");
      $menu.toggleClass("show");
    });
  }

  toggleNewList(){
    this.todoListFormTarget.classList.toggle("hidden");
  }

  toggleNewListAndFocus(){
    this.toggleNewList();
    $(this.listTitleTarget).focus();
  }

  submitListForm(){
    let projectId = this.data.get("projid");
    let csrfEl = document.getElementsByName("csrfmiddlewaretoken")[0];
    let csrf = csrfEl.value;
    let title = this.listTitleTarget.value;
    let that = this;
    $.post({
      url: BASE_URL + '/projects/'+projectId+'/todos',
      data: JSON.stringify({
        title: title,
        projectId: projectId
      }),
      headers: {'X-CSRFToken': csrf},
      success: function(rez){
        that.todoListFormTarget.classList.add("hidden");
        that.listTitleTarget.value = '';
        let targetElement = $('.todo-list-container');
        that.reloadAllLists(projectId, targetElement);
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
