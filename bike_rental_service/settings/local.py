
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
import sys
if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'bike_rental_service',
            'USER': 'sudip',
            'PASSWORD': 'sudip@123',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' 

# Disable WhiteNoise in development (optional, but good for debugging static files)
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
