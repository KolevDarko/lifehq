import os
from .base import *  # noqa

DEBUG = False
print("Using production settings")
# DATABASE SETTINGS
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'lifehqdb',
        'USER': 'lifehqdb',
        'PASSWORD': 'cdeVFRdarko!@#123',
        'HOST': 'localhost',
        'PORT': '',
    },
}
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# CACHES = {
#     "default": {
#         "BACKEND": 'django.core.cache.backends.memcached.MemcachedCache',
#         'LOCATION': '127.0.0.1:11211',
#     }
# }

# IMPORTANT!:
# You must keep this secret, you can store it in an
# environment variable and set it with:
# https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/#secret-key
SECRET_KEY = os.environ.get('LFHQ_SECRET', 'environment123variable')

# WSGI SETTINGS
# https://docs.djangoproject.com/en/1.10/ref/settings/#wsgi-application
WSGI_APPLICATION = 'mastermind.wsgi.application'

# NOTIFICATIONS
# A tuple that lists people who get code error notifications.
# https://docs.djangoproject.com/en/1.10/ref/settings/#admins
ADMINS = (
         ('Darko Admin', 'darko@lifehqapp.com'),
)
MANAGERS = ADMINS

# DJANGO-COMPRESSOR SETTINGS
STATICFILES_FINDERS = STATICFILES_FINDERS + (
    'compressor.finders.CompressorFinder',
)

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

LOG_DIRECTORY = "/home/darko/logs"

try:
    from local_settings import * # noqa
except ImportError:
    pass

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="https://9526d90129a84a509a58817612b02be7@sentry.io/1451711",
    integrations=[DjangoIntegration()]
)
