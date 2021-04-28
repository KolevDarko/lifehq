/*jshint esversion: 6 */
import {Controller} from "stimulus";

export default class extends Controller {
  static targets = ['tagsContainer', 'editName', 'editDeadline', 'editDeadlineEnabled', 'name', 'deadline', 'fileUploadForm', 'resourcesRow',
    'chosenFile', 'resSize', 'resName', 'resCreatedOn', 'resFileUrl', 'resIcon', 'resId', 'usageQuota', 'uploadProgress', 'uploadCompleted',
    'resourcesControls', 'pagesControls', 'pagesTab', 'uploadsTab', 'uploadErrors'];

  initialize() {
    this.PAGES = "PAGES";
    this.UPLOADS = "UPLOADS";
    this.resourcesState = this.PAGES;

    if (FIRST_PROJECT === "true") {
      let intro = introJs();
      intro.setOptions({
        'showProgress': true,
        'scrollToElement': true,
        'showStepNumbers': false,
        'tooltipPosition': 'auto',
        'showBullets': false,
        steps: [
          {
            intro: "Define all project tasks in TO-DOs, separated into task lists.",
            element: ".intro-step-1"
          },
          {
            intro: 'Schedule holds milestones, deadlines and all other events.',
            element: '.intro-step-2'
          },
          {
            intro: 'Resources hold all documents relevant to the project.',
            element: '.intro-step-3'
          },
          {
            intro: 'Create pages or upload your own files',
            element: '.intro-step-3-1'
          },
          {
            intro: 'Project without a deadline is just a dream ;)',
            element: '.intro-step-4'
          },

        ]
      });
      intro.oncomplete(function(){
        MyTrack('tour-project-completed');
      });
      intro.onexit(function(){
        let currentStep = intro._currentStep;
        MyTrack('tour-project-exit', {exitStep: currentStep});
      });
      intro.start();
    }
    this.projectId = this.data.get("projid");
    let myDatepicker = $('.datepicker');
    let projectDeadline;
    if (myDatepicker[0].dataset.projectDeadline) {
      projectDeadline = moment(myDatepicker[0].dataset.projectDeadline);
      this.toggleDeadline();
      $(this.editDeadlineEnabledTarget).prop('checked', true);
    }else{
      projectDeadline = '';
    }

    myDatepicker.datetimepicker({
      format: 'MM/DD/YYYY',
      defaultDate: projectDeadline
    });

    $('#fileUpload').change(function () {
    });
  }

  connect() {
    let that = this;
    this.initialTags = $(this.tagsContainerTarget).val().split(',');

    $('#projectTagsInput').on('beforeItemAdd', function (event) {
      let tag = event.item;
      if (that.initialTags.indexOf(tag) !== -1) {
        return;
      }
      if (!event.options || !event.options.preventPost) {
        let fullUrl = BASE_URL + "/projects/" + that.projectId + '/tag';
        let data = {
          'tag': tag
        };
        $.post({
          url: fullUrl,
          data: JSON.stringify(data),
          headers: {'X-CSRFToken': getCsrf()},
          success: function (response) {
            return;
          },
          error: function (err) {
            console.log(err);
            $('#projectTagsInput').tagsinput('remove', tag, {preventPost: true});
            //  todo show err notification
          }
        });
      }
    });

    $('#projectTagsInput').on('beforeItemRemove', function (event) {
      var tag = event.item;
      // Do some processing here

      if (!event.options || !event.options.preventPost) {
        let fullUrl = BASE_URL + "/projects/" + that.projectId + '/tag/delete';
        let data = {
          'tag': tag
        };
        $.post({
          url: fullUrl,
          data: JSON.stringify(data),
          headers: {'X-CSRFToken': getCsrf()},
          success: function (response) {
            return;
          },
          error: function (err) {
            console.log(err);
            $('#projectTagsInput').tagsinput('add', tag, {preventPost: true});
            //  todo show err notification
          }
        });
      }
    });

    $(this.fileUploadFormTarget).submit(this.uploadFile);
  }

  updateView(newData) {
    if (newData.projectName)
      $(this.nameTarget).text(newData.projectName);
    if (newData.projectDeadlineEnabled){
      if (newData.projectDeadline) {
        let HUMAN_FORMAT = "MMM D, YYYY";
        let newDeadline = "Deadline " + moment(newData.projectDeadline).format(HUMAN_FORMAT);
        $(this.deadlineTarget).text(newDeadline);
      }
    }else{
        $(this.deadlineTarget).text('');
    }
  }

  updateProject() {
    let postData = {};

    if (this.editNameTarget.value)
      postData.projectName = this.editNameTarget.value;

    if (this.editDeadlineTarget.value)
      postData.projectDeadline = this.editDeadlineTarget.value;

    if ($(this.editDeadlineEnabledTarget).prop('checked'))
      postData.projectDeadlineEnabled = this.editDeadlineEnabledTarget.value;

    if (!postData)
      return;

    let that = this;
    $.ajax({
      url: BASE_URL + '/projects/' + that.projectId,
      method: 'PUT',
      data: JSON.stringify(postData),
      headers: {'X-CSRFToken': getCsrf()},
      success: function (rez) {
        that.updateView(postData);
        $('#projectEditModal').modal('hide');
      }
    });
  }

  deleteProject() {
    if (confirm("Are you sure you want to delete this project?")) {
      let that = this;
      $.ajax({
        url: BASE_URL + '/projects/' + that.projectId,
        method: 'DELETE',
        headers: {'X-CSRFToken': getCsrf()},
        success: function (rez) {
          window.location = '/projects';
        }
      });
    }
  }

  loadPages(evt) {
    evt.preventDefault();
    if (this.resourcesState === this.PAGES) {
      return;
    }
    let $container = $(this.resourcesRowTarget);
    let url = `${BASE_URL}/projects/${this.projectId}/page/view`;
    let that = this;
    $.get({
      url: url,
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        $(that.resourcesControlsTarget).hide();
        $(that.pagesControlsTarget).show();
        $(that.pagesTabTarget).addClass('active');
        $(that.uploadsTabTarget).removeClass('active');
        $container.html(response);
        that.resourcesState = that.PAGES;
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  loadResources(evt) {
    evt.preventDefault();
    if (this.resourcesState === this.UPLOADS) {
      return;
    }
    let $container = $(this.resourcesRowTarget);
    let url = `${BASE_URL}/projects/${this.projectId}/resource/view`;
    let that = this;
    $.get({
      url: url,
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        $(that.resourcesControlsTarget).show();
        $(that.pagesControlsTarget).hide();
        $(that.pagesTabTarget).removeClass('active');
        $(that.uploadsTabTarget).addClass('active');
        $container.html(response);
        that.resourcesState = that.UPLOADS;
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  createFileCard(fileData) {
    let newCard = "<div class=\"col-md-3\">\n" +
      "                        <div class=\"card main-card\" data-resource-id='" + fileData.id + "'>\n" +
      " <a href=\" " + fileData.file_url + " \" target=\"_blank\">\n" +
      "                              <div class=\"card-body card-resource\">\n" +
      "                                  <div class=\"card-title\">" + fileData.title + "</div>\n" +
      "                                  <div class=\"card-resource-img card-description\">\n" +
      fileData.description +
      "                                  </div>\n" +
      "                              </div>\n" +
      "                            </a>\n" +
      "                            <div class=\"card-footer link-text\">\n" +
      "                              <a href=\"#\" data-saction=\"project#resourceDetails\">Details</a>\n" +
      "                            </div>" +
      "                            </div>" +
      "                            </div>";


    $(this.resourcesRowTarget).append(newCard);
  }

  uploadFile(event) {
    event.preventDefault();
    $(this.uploadProgressTarget).removeClass('hidden');
    $(this.uploadCompletedTarget).addClass('hidden');
    var data = new FormData($('form').get(0));
    if (!data) return;
    var the_form = $('form');
    let that = this;
    $.ajax({
      url: the_form.attr('action'),
      type: the_form.attr('method'),
      data: data,
      cache: false,
      processData: false,
      contentType: false,
      success: function (response) {
        $(that.uploadProgressTarget).addClass('hidden');
        if (response.error) {
          //  todo show error, form is invalid
          console.log("Err uploading file");
          console.log(response.error);
          $(that.uploadErrorsTarget).html("Error: " + response.error);
        } else {
          $(that.uploadCompletedTarget).removeClass('hidden');
          that.createFileCard(response);
          $(that.usageQuotaTarget).html(response.quota);
        }
      },
      error: function (err) {
        console.log("Err uploading file");
        console.log(err);
        $(that.uploadErrorsTarget).html("Error: " + response.error);
        // todo show error to contact support
      }
    });
    return false;
  }

  resourceDetails(evt) {
    evt.preventDefault();
    let resourceId = $(evt.target).closest('.card.main-card').data('resourceId');
    let url = `${BASE_URL}/projects/${this.projectId}/resource/${resourceId}`;
    let that = this;
    $.get({
      url: url,
      success: function (response) {
        console.log(response);
        $(that.resNameTarget).html(response.name);
        $(that.resSizeTarget).html(response.file_size);
        $(that.resCreatedOnTarget).html(response.created);
        $(that.resFileUrlTarget).attr("href", response.file_url);
        that.resIdTarget.value = response.id;
        $(that.resIconTarget).html(response.resIconElement);
        $('#resourceModal').modal('show');
      },
      error: function (err) {
        console.log(err.responseText);
      }
    });
  }

  deleteResource(evt) {
    evt.preventDefault();
    if (confirm("Are you sure you want to delete this file?")) {
      let resourceId = this.resIdTarget.value;
      let url = `${BASE_URL}/projects/${this.projectId}/resource/${resourceId}`;
      let that = this;
      $.ajax({
        url: url,
        method: 'DELETE',
        headers: {'X-CSRFToken': getCsrf()},
        success: function (rez) {
          $('#resourceModal').modal('hide');
          $('.resource-card-'+resourceId).hide("slow").html("");
        },
        error: function (err) {
          console.log(err);
        }
      });
    }
  }

  getSortUrl(sortBy) {
    if(this.resourcesState === this.PAGES){
      return `${BASE_URL}/projects/${this.projectId}/page/sorted?sort=${sortBy}`;
    }else{
      return `${BASE_URL}/projects/${this.projectId}/resource/sorted?sort=${sortBy}`;
    }
  }

  changeSort(evt) {
    let sortBy = evt.target.value;
    let url = this.getSortUrl(sortBy);
    let $container = $(this.resourcesRowTarget);
    $.get({
      url: url,
      headers: {'X-CSRFToken': getCsrf()},
      success: function (response) {
        $container.html(response);
      },
      error: function (err) {
        console.log(err);
      }
    });
  }

  fileChanged(e) {
    console.log("File has changed");
    let fileName = e.target.value.split('\\').pop();
    $(this.chosenFileTarget).html(fileName);
  }

  toggleDeadline(){
    $(this.editDeadlineTarget).toggle();
  }

}
