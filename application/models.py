# coding=utf-8

__author__ = 'cage'


from google.appengine.ext import ndb
import webapp2_extras.appengine.auth.models as auth_models
import application.settings as settings

class User(auth_models.User):
  account_enabled = ndb.BooleanProperty(default=False)
  report_enabled = ndb.BooleanProperty(default=False)
  description = ndb.TextProperty(default='')

class Site(ndb.Model):
  VERSION = 1
  baseurl = ndb.StringProperty(default=None)
  name = ndb.StringProperty()
  article_per_page = ndb.IntegerProperty()
  admin_article_per_page = ndb.IntegerProperty()
  feed_url = ndb.StringProperty()
  disqus_shortname = ndb.StringProperty()

def InitSiteDate():
  global g_site

  # Site
  g_site = Site(id='default')
  g_site.baseurl = settings.BASIC_SITE_URL
  g_site.name = settings.SITE_NAME

  g_site.put()

  return g_site


def global_init(forceUpdate=False):
  global g_site
  try:
    if g_site:
      return g_site

  except:
    pass

  g_site = Site.get_by_id('default')
  if not g_site or forceUpdate:
    g_site = InitSiteDate()

  return g_site

try:
  g_site = global_init(forceUpdate=True)

except:
  pass
