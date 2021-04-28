/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ['header', 'dropdown', 'headerArrow', 'workTitle', 'workScore', 'revWorkScore', 'habitsTitle', 'habitsScore', 'revHabitsScore', 'journalsTitle', 'journalsScore', 'revJournalsScore', 'totalScore', 'revTotalScore'];

  initialize() {
    this.detailsHidden = true;
    this.arrows = {
      true: '<i class="fas fa-sort-down"></i>',
      false: '<i class="fas fa-sort-up"></i>'
    };
    if (this.data.get("sessionValid") === "False"){
      this.getWinningData();
    }
  }

  toggleDropdown(){
    $(this.dropdownTarget).toggle(600);
    this.switchArrow();
  }
  
  switchArrow(){
    this.detailsHidden = !this.detailsHidden;
    $(this.headerArrowTarget).html(this.arrows[this.detailsHidden]);
  }

  makeTitle(name, done, todo){
    return `${name} ${done}/${todo}`;
  }

  updateTitles(result){
    $(this.workTitleTarget).html(this.makeTitle('Work', result.work.done, result.work.todo));
    $(this.habitsTitleTarget).html(this.makeTitle('Habits', result.habits.done, result.habits.todo));
    $(this.journalsTitleTarget).html(this.makeTitle('Journals', result.journals.done, result.journals.todo));
  }

  updateProgressBars(result){
    $(this.workScoreTarget).css({'width': result.work.score+'%'});
    $(this.revWorkScoreTarget).css({'width': result.work.rev_score+'%'});
    $(this.journalsScoreTarget).css({'width': result.journals.score+'%'});
    $(this.revJournalsScoreTarget).css({'width': result.journals.rev_score+'%'});
    $(this.habitsScoreTarget).css({'width': result.habits.score+'%'});
    $(this.revHabitsScoreTarget).css({'width': result.habits.rev_score+'%'});
    $(this.totalScoreTarget).css({'width': result.total_score+'%'});
    $(this.revTotalScoreTarget).css({'width': result.rev_total_score+'%'});
  }

  getWinningData(){
    let that = this;
    $.get({
      url: BASE_URL + '/success/day',
      success: function(result){
        console.log(result);
        that.updateTitles(result);
        that.updateProgressBars(result);
      },
      error: function(err){
        console.log(err);
      }
    });
  }
}
