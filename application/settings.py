# -*- coding: utf-8 -*-

__author__ = 'cage'

import os
import logging

if os.environ.get('SERVER_SOFTWARE', '').startswith('Development'):
  DEBUG = True
else:
  DEBUG = False

logging.info("Starting application in DEBUG mode: %s", DEBUG)

CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secret.json')

WEB_CLIENT_ID = '<web-client-id>'

DEVELOPER_KEY = '<developer=key>'

SERVICE_ACCOUNT_EMAIL = '<service-account-email>'

SITE_NAME = '<site-name>'
BASIC_SITE_URL = '<basic-site-url>'
SITE_OWNER = '<site-owner>'

ADMINS = [
  # email list
]