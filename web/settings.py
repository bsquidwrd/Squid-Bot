"""
Django settings for web project.

Generated by 'django-admin startproject' using Django 1.10.1.

For more information on this file, see
https://docs.djangoproject.com/en/1.10/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.10/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.10/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SQUID_BOT_DJANGO_SECRET', None)

# SECURITY WARNING: don't run with debug turned on in production!
debug_mode = os.getenv('SQUID_BOT_DEBUG_MODE', 'true')
if debug_mode.lower() == 'false':
    DEBUG = False
else:
    DEBUG = True

# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
if DEBUG or 'TRAVIS' in os.environ:
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [
        '127.0.0.1',
        'localhost',
        'bsquid.io',
    ]

if 'TRAVIS' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql_psycopg2',
            'NAME':     'travisci',
            'USER':     'postgres',
            'PASSWORD': '',
            'HOST':     'localhost',
            'PORT':     '',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('SQUID_BOT_DATABASE_ENGINE', 'django.db.backends.sqlite3'),
            'NAME': os.getenv('SQUID_BOT_DATABASE_NAME', 'squidbot.db'),
            'HOST': os.getenv('SQUID_BOT_DATABASE_HOST', None),
            'USER': os.getenv('SQUID_BOT_DATABASE_USERNAME', None),
            'PASSWORD': os.getenv('SQUID_BOT_DATABASE_PASSWORD', None),
            'PORT': os.getenv('SQUID_BOT_DATABASE_PORT', None)
        }
    }


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp-relay.gmail.com'
EMAIL_HOST_USER = 'noreply@bsquidwrd.com'
EMAIL_HOST_PASSWORD = os.getenv('SQUID_BOT_EMAIL_PASSWORD', None)
EMAIL_PORT = '587'
EMAIL_USE_TLS = True
SERVER_EMAIL = 'Squid Bot <noreply@bsquidwrd.com>'
DEFAULT_FROM_EMAIL = SERVER_EMAIL

# Used for sending emails
EMAIL_SUBJECT_PREFIX = '[Squid Bot] '

ADMINS = ('bsquidwrd <squidbot@bsquidwrd.com>',)

APPEND_SLASH = True

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'gaming',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates"),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

WSGI_APPLICATION = 'web.wsgi.application'


# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/

# STATIC_ROOT =
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)
STATIC_URL = '/static/'

############################
# Begin my custom settings #
############################

LOGIN_REDIRECT_URL = '/'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'offline'
        }
    }
}

from django.contrib.messages import constants as message_constants
MESSAGE_TAGS = {
    message_constants.DEBUG: 'debug',
    message_constants.INFO: 'info',
    message_constants.SUCCESS: 'success',
    message_constants.WARNING: 'warning',
    message_constants.ERROR: 'danger',
}

##########################
# End my custom settings #
##########################
