 document.addEventListener('trix-initialize', function(e) {
   var trix = e.target;
   var toolBar = trix.toolbarElement;

   // Creation of the button
   var button = document.createElement("button");
   button.setAttribute("type", "button");
   button.setAttribute("class", "trix-button trix-button--icon trix-button--icon-attach-files");
   button.setAttribute("data-trix-action", "x-attach");
   button.setAttribute("title", "Attach a file");
   button.setAttribute("tabindex", "-1");
   button.innerText = "Attach a file";

   // Attachment of the button to the toolBar
   toolBar.querySelector('.trix-button-group.trix-button-group--block-tools').appendChild(button);
 });
