/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ["deleteModal", "pageContent", "showTitleBox", "pageTitleShow", "editTitleBox", "pageTitleEdit"];

  initialize() {
    this.projectId = this.data.get("projid");
    this.pageId = null;
    if (this.data.get("pageid") !== "None") {
      this.pageId = this.data.get("pageid");
    }
    let that = this;
    addEventListener("trix-attachment-add", function(event) {
      if (event.attachment.file) {
        that.uploadFileAttachment(event.attachment);
      }
    });

    addEventListener("trix-attachment-remove", function(event){
      var attachment = event.attachment;
      var data = attachment.getAttributes();
      if(!data.url) {
        console.log("file was not saved");
        return false;
      }
      let deleteUrl = `${BASE_URL}/projects/${that.projectId}/page/${that.pageId}/image/${data.id}`;
      $.ajax({
        url: deleteUrl,
        type: "DELETE",
        headers: { 'X-CSRFToken': getCsrf()},
      });
    });

    $('#trix-toolbar-1 .trix-button--icon-attach-files').click(function(evt){
      that.btnUploadFile();
    });
    $('form.ays-warning').areYouSure({'message': 'Are you sure you want to leave? You have unsaved changes.'});
    $('trix-editor').on('trix-change', function(){
      $('form.ays-warning').addClass('dirty');
    });
  }


  btnUploadFile(){
      var trix = document.querySelector("trix-editor");
      var fileInput = document.createElement("input");

      fileInput.setAttribute("type", "file");

      fileInput.addEventListener("change", function(event) {
        var files = this.files;
        var results = [];
        var filesCounter = files.length;

        for (var i = 0; i < filesCounter; i++) {
          results.push(trix.editor.insertFile(files[i]));
        }
        return results;
      });
      fileInput.click();
  }

  uploadFileAttachment(attachment){
    this.uploadFile(attachment.file, setProgress, setAttributes);

    function setProgress(progress) {
      attachment.setUploadProgress(progress);
    }

    function setAttributes(attributes) {
      attachment.setAttributes(attributes);
    }
  }

  uploadFile(file, progressCallback, successCallback) {
    var key = this.createStorageKey(file);
    var formData = this.createFormData(key, file);
    var xhr = new XMLHttpRequest();
    var saveUrl = BASE_URL + '/projects/' + this.projectId + '/page/' + this.pageId + '/image';
    xhr.open("POST", saveUrl, true);

    xhr.upload.addEventListener("progress", function(event) {
      var progress = event.loaded / event.total * 100;
      progressCallback(progress);
    });

    xhr.addEventListener("load", function(event) {
      if (xhr.status === 200) {
        var response = JSON.parse(xhr.response);
        var attributes = {
          url: response.url,
          href: response.url + "&content-disposition=attachment",
          id: response.id
        };
        successCallback(attributes);
      }else{
        console.log(xhr);
        console.log(event);
        console.log('finished');
      }
    });
    xhr.send(formData);
  }

  createStorageKey(file) {
    var date = new Date();
    var day = date.toISOString().slice(0,10);
    var name = date.getTime() + "-" + file.name;
    return [ "tmp", day, name ].join("/");
  }

  createFormData(key, file) {
    var data = new FormData();
    data.append("key", key);
    data.append("file", file);
    data.append("Content-Type", file.type);
    data.append("csrfmiddlewaretoken", getCsrf());
    return data;
  }

  editPageTitle(evt) {
    evt.preventDefault();
    $(this.showTitleBoxTarget).hide();
    $(this.editTitleBoxTarget).show();
    $(this.pageTitleEditTarget).focus();
  }

  savePageTitle(evt) {
    if (this.pageTitleEditTarget.value.toString() === this.pageTitleShowTarget.innerHTML.toString()) {
      $(this.editTitleBoxTarget).hide();
      $(this.showTitleBoxTarget).show();
      return;
    }
    this.savePage(evt, true);
  }


  savePage(evt, onlyTitle) {
    let data = {};
    if (onlyTitle) {
      data.title = this.pageTitleEditTarget.value;
    } else {
      data = {
        'title': this.pageTitleEditTarget.value,
        'content': this.pageContentTarget.value
      };
    }
    let saveUrl = '';
    if (this.pageId) {
      saveUrl = BASE_URL + '/projects/' + this.projectId + '/page/' + this.pageId;
    } else {
      saveUrl = BASE_URL + '/projects/' + this.projectId + '/page';
    }

    let that = this;
    $.post({
      url: saveUrl,
      data: JSON.stringify(data),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        that.pageId = response.id;
        if (onlyTitle) {
          $(that.editTitleBoxTarget).hide();
          $(that.pageTitleShowTarget).html(data.title);
          $(that.showTitleBoxTarget).show();
        } else {
          showSuccessNotification("Page saved");
          $('form.ays-warning').removeClass('dirty');
        }
      }
    });
  }

  deletePage(evt) {
    let pageId = evt.target.dataset.pageId;
    let projectId = evt.target.dataset.projectId;
    $('form.ays-warning').removeClass('dirty');
    $.ajax({
      url: BASE_URL + '/projects/' + projectId + '/page/' + pageId,
      type: 'DELETE',
      headers: {'X-CSRFToken': getCsrf()},
      success: function (result) {
        let projectUrl = BASE_URL + '/projects/' + projectId;
        window.location = projectUrl;
      },
      error: function (err) {
        //  todo show notification
        console.log(err);
      }
    });
  }

}
