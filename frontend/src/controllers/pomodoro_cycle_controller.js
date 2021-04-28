/*jshint esversion: 6 */
import { Controller } from "stimulus";

export default class extends Controller {
  static targets = ['whatAnswer', 'howStartAnswer', 'blockerAnswer', 'reviewAccomplishedInfo','reviewEnergyInfo','reviewTakeawayInfo', 'reviewFinished'];

  initialize() {
    this._whatAnswer = this.whatAnswerTarget.value;
    this._howStartAnswer = this.howStartAnswerTarget.value;
    this._blockerAnswer = this.blockerAnswerTarget.value;
    this.cycleId = this.data.get("cycleId");
  }

  getFieldValue(targetVal, storageName){
    let storageVal = this[storageName];
    if(targetVal !== storageVal){
      this[storageName] = targetVal;
      return targetVal;

    }
  }

  getIfUpdated(){
    let that = this;
    let response = {
      'id': this.cycleId,
      'data': {}
    };
    let targets = ['whatAnswer', 'howStartAnswer', 'blockerAnswer'];
    targets.forEach(function(key){
      let targetName = key+'Target';
      let newVal = that.getFieldValue(that[targetName].value, '_'+key);
      if (newVal){
        response.data[key] = newVal;
      }
    });
    return response;
  }

  getCycleData(){
    this._whatAnswer = this.whatAnswerTarget.value;
    this._howStartAnswer = this.howStartAnswerTarget.value;
    this._blockerAnswer = this.blockerAnswerTarget.value;
    return {
      'whatAnswer': this.whatAnswerTarget.value,
      'howStartAnswer': this.howStartAnswerTarget.value,
      'blockerAnswer': this.blockerAnswerTarget.value,
    };
  }

  updateReviewData(data){
    $(this.reviewFinishedTarget).html("<span class='text-success'>Yes</span>");
    $(this.reviewAccomplishedInfoTarget).html(data.done);
    $(this.reviewEnergyInfoTarget).html(data.energy);
    $(this.reviewTakeawayInfoTarget).html(data.review);
  }
}
