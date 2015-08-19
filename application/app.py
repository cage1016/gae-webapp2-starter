# -*- coding:utf-8 -*-

import webapp2

from application.controllers.base import *
from application.controllers.error_handler import *

# from settings import decorator
from secrets import SESSION_KEY

# webapp2 config
app_config = {
  'webapp2_extras.sessions': {
    'secret_key': SESSION_KEY
  },
  'webapp2_extras.auth': {
    'user_model': User
  }
}


class MainHandler(BaseRequestHandler):
  def get(self):
    self.render('index.html')


class Webapp2HandlerAdapter(webapp2.BaseHandlerAdapter):
  """Wrapper for error handlers,
  Passes the extra parameter "exception" into the get method.
  """

  def __call__(self, request, response, exception):
    return self.handler(request, response).get(exception)


routes = [
  ('/', MainHandler),

  ('/oauth2callback', OAuth2CallbackHandler),
  ('/logout', LogOutHandler),
]

router = webapp2.WSGIApplication(routes, config=app_config, debug=True)

router.error_handlers[404] = Webapp2HandlerAdapter(Handle404)
router.error_handlers[403] = Webapp2HandlerAdapter(Handle403)
router.error_handlers[500] = Webapp2HandlerAdapter(Handle500)
