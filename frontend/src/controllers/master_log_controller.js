/*jshint esversion: 6 */
// eslint-disable-next-line import/no-unresolved
import { Controller } from "stimulus";

export default class extends Controller {

  initialize(){
    this.proejctId = 0;
    this.logStart = 0;
    this.logEnd = 0;
  }

  selectProject(evt){
    this.projectId = evt.target.value;
    console.log("Selected project " + this.projectId);
  }

  startLog(evt){
    let data = {
      action: "start",
      projectId: this.projectId
    };
    let saveUrl = BASE_URL + "/projects/log";
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        console.log("Log started");
      },
      error: function(err){
        console.log(err);
      }
    });
  }

  endLog(evt){
    let data = {
      action: "end",
      projectId: this.projectId
    };
    let saveUrl = BASE_URL + "/projects/log";
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function(response){
        console.log("Log ended");
      },
      error: function(err){
        console.log(err);
      }
    });
  }
}
