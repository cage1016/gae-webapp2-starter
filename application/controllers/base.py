# -*- coding:utf-8 -*-

__author__ = 'cage'

import os
import webapp2
import pickle
import httplib2
import logging

from webapp2_extras import sessions, jinja2
from jinja2.runtime import TemplateNotFound
from application.utils import to_json_encodable

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.clientsecrets import loadfile
from google.appengine.api import urlfetch


from application.models import *
import application.settings as settings


def jinja2_date_filter(date, fmt=None):
  if fmt:
    return date.strftime(fmt)
  else:
    return date.strftime('%Y-%m')


# oauth
# Set deadline of urlfetch in order to prevent 5 second timeout
urlfetch.set_default_fetch_deadline(45)

# Load client secrets from 'client_secrets.json' file.
client_type, client_info = loadfile(settings.CLIENT_SECRETS)
FLOW = flow_from_clientsecrets(
  settings.CLIENT_SECRETS,
  scope=['https://www.googleapis.com/auth/userinfo.email',
         'https://www.googleapis.com/auth/devstorage.read_write'],
  redirect_uri=client_info['redirect_uris'][0], )
FLOW.params.update({'access_type': 'offline'})
FLOW.params.update({'approval_prompt': 'force'})


class BaseRequestHandler(webapp2.RequestHandler):
  def dispatch(self):
    """Get a session store for this request."""
    self.session_store = sessions.get_store(request=self.request)
    try:
      # Dispatch the request.
      webapp2.RequestHandler.dispatch(self)
    finally:
      # Save all sessions.
      self.session_store.save_sessions(self.response)

  @webapp2.cached_property
  def session(self):
    """Return a session using key from the configuration."""
    return self.session_store.get_session()

  def CreateLogInUrl(self, state=''):
    """Return an oauth authorization url if user needs authorization.
    Args:
      state: string, state parameter of oauth2 request url.
    """
    login_url = None
    if 'credential' not in self.session:
      # Create OAuth2 authentication url with given state parameter.
      FLOW.params.update({'state': state})
      login_url = FLOW.step1_get_authorize_url()
    return login_url

  @webapp2.cached_property
  def logged_in(self):
    """Returns true if a user is currently logged in, false otherwise"""
    return 'credential' in self.session

  @webapp2.cached_property
  def jinja2(self):
    """Returns a Jinja2 renderer cached in the app registry"""

    j = jinja2.get_jinja2(app=self.app)
    j.environment.filters['date'] = jinja2_date_filter
    return j

  @webapp2.cached_property
  def user(self):
    user = None
    if 'user' in self.session:
      user = self.session['user']
    return user

  @webapp2.cached_property
  def site(self):
    site = Site.get_by_id('default')
    return site

  def render(self, template_name, **template_vars):
    # Pass name of current page
    state = ''
    if template_name != 'index.html':
      state = os.path.splitext(template_name)[0]
    template_vars['state'] = state

    # Pass login url
    if state != '403':
      template_vars['login_url'] = self.CreateLogInUrl(state)

    if type(self.request.route_args) == dict:
      if self.request.route_args['exception']:
        template_vars['exception'] = self.request.route_args.get('exception').message

    values = {
      'upath_info': self.request.upath_info,
      'url_for': self.uri_for,
      'site': self.site,
      'user': self.user
    }

    # Add manually supplied template values
    values.update(template_vars)

    # read the template or 404.html
    try:
      self.response.write(self.jinja2.render_template(template_name, **values))
    except TemplateNotFound:
      self.abort(404)

  def LogOut(self):
    """Unsubscribe and delete credential in session data."""
    if 'credential' in self.session:
      del self.session['credential']
    if 'user' in self.session:
      del self.session['user']


class OAuth2CallbackHandler(BaseRequestHandler):
  """Request handling class for /oauth2callback."""

  def get(self):
    """GET request handling method.
    Receive authentication code from user with GET['code'].
    Save credential if code exchange is successful.
    Redirect to previous page user visited.
    """
    if 'code' in self.request.GET:
      try:
        credential = FLOW.step2_exchange(self.request.GET.get('code'))
      except FlowExchangeError:
        pass
      else:
        # Retrieve basic information about the user
        http = httplib2.Http()
        http = credential.authorize(http)
        users_service = build('oauth2', 'v2', http=http)
        user_document = users_service.userinfo().get().execute()

        # custom
        logging.debug('Got user data: %s', user_document)

        auth_id = 'google:%s' % user_document['email']

        logging.debug('Looking for a user with id %s', auth_id)
        user = User.get_by_id(auth_id)
        _attrs = user_document

        if user:
          logging.debug('Found existing user to log in')
          # Existing users might've changed their profile data so we update our
          # local model anyway. This might result in quite inefficient usage
          # of the Datastore, but we do this anyway for demo purposes.
          #
          # In a real app you could compare _attrs with user's properties fetched
          # from the datastore and update local user in case something's changed.
          user.populate(**_attrs)
          user.put()

          self.session['user'] = to_json_encodable(user)
          self.session['credential'] = pickle.dumps(credential)

        else:
          logging.debug('Creating a brand new user')

          # add is admin to user model by settings.ADMINS list
          if _attrs.get('email') in settings.ADMINS:
            _attrs.update(is_admin=True, account_enabled=True, report_enabled=True)
          else:
            _attrs.update(is_admin=False)

          user = User.get_or_insert(auth_id)
          if user:
            user.populate(**_attrs)
            user.put()

          self.session['user'] = to_json_encodable(user)
          self.session['credential'] = pickle.dumps(credential)

    self.redirect('/' + (self.request.GET.get('state') or ''))


class LogOutHandler(BaseRequestHandler):
  """Request handling class for /logout."""

  def get(self):
    """GET request handling method.
    Delete credential from session data.
    Redirect to previous page user visited.
    """
    self.LogOut()
    self.redirect('/' + (self.request.GET.get('state') or ''))
