"""
Project main settings file. These settings are common to the project
if you need to override something do it in local.pt
"""

from sys import path

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

# PATHS
# Path containing the django project
from mastermind import account_utils

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path.append(BASE_DIR)
# Path of the top level directory.
# This directory contains the django project, apps, libs, etc...
PROJECT_ROOT = os.path.dirname(BASE_DIR)

PROJECT_CONTAINER = os.path.dirname(PROJECT_ROOT)

# Add apps and libs to the PROJECT_ROOT
path.append(os.path.join(PROJECT_ROOT, "apps"))
path.append(os.path.join(PROJECT_ROOT, "libs"))

# SITE SETTINGS
# https://docs.djangoproject.com/en/2.0/ref/settings/#site-id
SITE_ID = 1

# https://docs.djangoproject.com/en/2.0/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "167.99.132.42", "beta.lifehqapp.com", "my.lifehqapp.com"]

MY_HOSTNAME = 'my.lifehqapp.com'

DEFAULT_FROM_EMAIL = 'Darko from LifeHQ <darko@lifehqapp.com>'

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = ''  #Paste CLient Key
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = '' #Paste Secret Key

SOCIAL_AUTH_TWITTER_KEY = ''
SOCIAL_AUTH_TWITTER_SECRET = ''

SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

SOCIAL_AUTH_FACEBOOK_KEY = ''
SOCIAL_AUTH_FACEBOOK_SECRET = ''

SOCIAL_AUTH_REDIRECT_IS_HTTPS = True

GOOGLE_CAPTCHA_SECRET = ''

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.user.create_user',
    'apps.base.views.create_account_profile',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'social_core.pipeline.social_auth.associate_by_email',
)

AUTHENTICATION_BACKENDS = [

    'social_core.backends.open_id.OpenIdAuth',  # for Google authentication
    'social_core.backends.google.GoogleOpenId',  # for Google authentication
    'social_core.backends.google.GoogleOAuth2',  # for Google authentication
    'social_core.backends.github.GithubOAuth2',  # for Github authentication
    'social_core.backends.twitter.TwitterOAuth',  # for Twitter authentication
    "account.auth_backends.EmailAuthenticationBackend",
]

# https://docs.djangoproject.com/en/2.0/ref/settings/#installed-apps
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'django.contrib.syndication',
    'django.contrib.staticfiles',
    'account',
    'webpack_loader',
    # Third party apps
    'compressor',
    'social_django',
    'django_cron',
    'django_s3_storage',
    'djcelery_email',
    # Local apps
    'apps.base',
    'apps.journal',
    'apps.notebooks',
    'apps.habitss',
    'apps.work',
]
WEBPACK_LOADER = {
    'DEFAULT': {
        'BUNDLE_DIR_NAME': 'bundles/',
        'STATS_FILE': os.path.join(PROJECT_ROOT, 'webpack-stats.json'),
    }
}
# https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#using-argon2-with-django
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.BCryptPasswordHasher',
]

# DEBUG SETTINGS
# https://docs.djangoproject.com/en/2.0/ref/settings/#debug
DEBUG = True

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'

ACCOUNT_EMAIL_CONFIRMATION_AUTO_LOGIN = True
ACCOUNT_EMAIL_CONFIRMATION_REQUIRED = True
ACCOUNT_EMAIL_CONFIRMATION_EMAIL = True
ACCOUNT_EMAIL_UNIQUE = True
ACCOUNT_OPEN_SIGNUP = True
ACCOUNT_REMEMBER_ME_EXPIRY = 60 * 60 * 24 * 30
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30
ACCOUNT_HOOKSET = 'mastermind.utils.MyAccountHookset'
ACCOUNT_DELETION_EXPUNGE_HOURS = 24
ACCOUNT_DELETION_EXPUNGE_CALLBACK = account_utils.expunge_account
ACCOUNT_DELETION_MARK_CALLBACK = account_utils.deactivate_account

HASHID_FIELD_SALT = os.environ.get('SALT')
HASHID_FIELD_ALLOW_INT_LOOKUP = True
# for AWS S3 storage
DEFAULT_FILE_STORAGE = 'django_s3_storage.storage.S3Storage'
# The AWS region to connect to.
AWS_REGION = "us-west-1"

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_KEY')

AWS_S3_BUCKET_NAME = os.environ.get('AWS_BUCKET_NAME')
AWS_S3_BUCKET_AUTH = False

MAX_UPLOAD_SIZE = 1

CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
# CELERY_RESULT_BACKEND = 'redis://localhost:6379'
# CELERY_ACCEPT_CONTENT = ['application/json']
# CELERY_RESULT_SERIALIZER = 'json'
# CELERY_TASK_SERIALIZER = 'json'
CELERY_EMAIL_TASK_CONFIG = {
    'queue' : 'emailing'
}

# https://docs.djangoproject.com/en/2.0/ref/settings/#internal-ips
INTERNAL_IPS = ('127.0.0.1')

# LOCALE SETTINGS
# Local time zone for this installation.
# https://docs.djangoproject.com/en/2.0/ref/settings/#time-zone
TIME_ZONE = 'UTC'

# https://docs.djangoproject.com/en/2.0/ref/settings/#language-code
LANGUAGE_CODE = 'en-us'

# https://docs.djangoproject.com/en/2.0/ref/settings/#use-i18n
USE_I18N = True

# https://docs.djangoproject.com/en/2.0/ref/settings/#use-l10n
USE_L10N = False

# https://docs.djangoproject.com/en/2.0/ref/settings/#use-tz
USE_TZ = True


# MEDIA AND STATIC SETTINGS
# Absolute filesystem path to the directory that will hold user-uploaded files.
# https://docs.djangoproject.com/en/2.0/ref/settings/#media-root
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'public/media')

# URL that handles the media served from MEDIA_ROOT. Use a trailing slash.
# https://docs.djangoproject.com/en/2.0/ref/settings/#media-url
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# https://docs.djangoproject.com/en/2.0/ref/settings/#static-root
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'public/static')

# URL prefix for static files.
# https://docs.djangoproject.com/en/2.0/ref/settings/#static-url
STATIC_URL = '/static/'

# Additional locations of static files
# https://docs.djangoproject.com/en/2.0/ref/settings/#staticfiles-dirs
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'static'),
    os.path.join(PROJECT_ROOT, 'frontend'),
)
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)
# TEMPLATE SETTINGS
# https://docs.djangoproject.com/en/2.0/ref/settings/#templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'account.context_processors.account',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
                'apps.base.context_processors.my_extra_info_processor',  # Custom
            ],
            'libraries':{
                'my_template_tags': 'apps.work.template_tags.my_template_tags'
            },
            "debug": False
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'development.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}

SESSION_ENGINE = 'redis_sessions.session'

SESSION_REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 0,
    'password': '',
    'prefix': 'session',
    'socket_timeout': 1,
    'retry_on_timeout': False
    }

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/0",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# URL SETTINGS
# https://docs.djangoproject.com/en/2.0/ref/settings/#root-urlconf.
ROOT_URLCONF = 'mastermind.urls'

# MIDDLEWARE SETTINGS
# See: https://docs.djangoproject.com/en/2.0/ref/settings/#middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'account.middleware.LocaleMiddleware',
    'account.middleware.TimezoneMiddleware',
    'apps.base.middleware.TrialCheckMiddleware',
]

CRON_CLASSES = [
    "crons.Crons.AwsResourceCleanupCron",
    "crons.Crons.RemindersCron",
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda r: False,  # disables it
}
# LOGGING
# https://docs.djangoproject.com/en/2.0/topics/logging/
# LOG_DIRECTORY = "/home/darko/logs"
# LOG_DIRECTORY = "/Users/darko/logs"
LOG_DIRECTORY = os.path.join(PROJECT_CONTAINER, 'logs/')

LOGGING = {
    'version': 1,
    'formatters': {
      'console': {
          'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
      }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console'
        },
        'cron_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}cron.log".format(LOG_DIRECTORY),
            'maxBytes': 1048576,
            "backupCount": 10,
            'level': 'DEBUG',
            'formatter': 'console'
        },
        'onboard_handler': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': "{}onboard.log".format(LOG_DIRECTORY),
            'maxBytes': 1048576,
            "backupCount": 10,
            'level': 'DEBUG',
            'formatter': 'console'
        }
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        },
        'crons': {
            'handlers': ['cron_handler'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.template': {
            'handlers': ['console'],
            'level': 'CRITICAL',
        },
        'onboarding': {
            'handlers': ['onboard_handler'],
            'level': 'DEBUG',
            'propagate': False
        }
    },
}

EMAIL_BACKEND = 'djcelery_email.backends.CeleryEmailBackend'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = 'smtp.mailgun.org'
EMAIL_HOST_USER = os.environ.get('MAILGUN_USER')
EMAIL_HOST_PASSWORD = os.environ.get('MAILGUN_PASS')

# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = 'darko@lifehqapp.com'
# EMAIL_HOST_PASSWORD = os.environ.get('GMAIL_PASS', '')

MAX_IMAGE_SIZE = 2000000
