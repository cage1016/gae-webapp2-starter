var router = require('router');

// Add routes to initialize code based on the page the user is on.
new router()
  .match(location.pathname);