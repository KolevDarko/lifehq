const path = require("path")
var BundleTracker = require('webpack-bundle-tracker')

module.exports = {
  context: __dirname,

  entry: {
    bundle: "./frontend/src/index.js"
  },

  output: {
    filename: "[name].js",
    path: path.resolve("./frontend/bundles")
  },

  devtool: "source-map",

  plugins: [
    new BundleTracker({filename: './webpack-stats.json'})
  ],

  module: {
    rules: [
      {
        test: /\.js$/,
        exclude: [
          /node_modules/
        ],
        use: [
          { loader: "babel-loader" }
        ]
      }
    ]
  }
}
