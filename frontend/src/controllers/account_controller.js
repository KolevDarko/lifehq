/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ['newProjectForm', 'newNotebookForm'];


  toggleProjectForm(){
    event.preventDefault();
    this.newProjectFormTarget.classList.toggle("hidden");
  }

  toggleNotebookForm(){
    event.preventDefault();
    this.newNotebookFormTarget.classList.toggle("hidden");
  }

}
