import { Application } from "stimulus";
import { definitionsFromContext } from "stimulus/webpack-helpers";

const application = Application.start(document.documentElement, {
 controllerAttribute: "data-controller",
  actionAttribute: "data-saction",
  targetAttribute: "data-target"
});
const context = require.context("./controllers", true, /\.js$/);
application.load(definitionsFromContext(context));
