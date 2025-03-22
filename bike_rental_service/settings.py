"""
Django settings for bike_rental_service project.

"""
from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-az9pgog(mk+kib7o!xsz4xz+ls!nb)jot+ev&r5w829#t0_2u='

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
CORS_ALLOW_ALL_ORIGINS = True  # For API access from frontend

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'jazzmin', #template for custom dashboard
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # local apps
    'users',
    'bikes',
    'bookings',
    'testimonials',
    'payment',
    'admin_panel',

    #third party package
    'rest_framework',
    'corsheaders',
    'rest_framework.authtoken',
    'django_filters',
    'paypal.standard.ipn',
    'drf_yasg',  # Added for Swagger documentation

]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'bike_rental_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'bike_rental_service.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'bike_rental_service',  # Replace with the database name provided by Render
        'USER': 'sudip',  # Replace with the database user provided by Render
        'PASSWORD': 'tRLI1KykmnP5kEJSzuHzJsEb64v96Ppr',  # Replace with the password provided by Render
        'HOST': 'dpg-cven2i56l47c73afrk60-a',  # Replace with the host provided by Render
        'PORT': '5432',  # Default port for PostgreSQL
    }
}



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

#custom user
AUTH_USER_MODEL = 'users.User'

# global authentications and permissions
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',

    ],

    # Throttling configuration
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '500/day',  # Limits unauthenticated users to 50 requests/day for browsing
        'user': '1000/day',  # Limits authenticated users to 100 requests/day for general actions
        'register': '10/hour',  # Limits registration attempts to 5/hour to prevent mass account creation
        'login': '20/hour',  # Limits login attempts to 10/hour to prevent brute-force
        'bookings': '10/hour',  # Limits booking creation to 10/hour to prevent spam
        'payments': '5/minute',  # Limits payment attempts to 5/minute to allow transactions but prevent abuse
        'testimonials': '5/hour',  # Limits testimonial submissions to 5/hour to prevent spam
        'admin_contact_messages': '100/day', # Limits contact message to 100/day
    },

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 6,  # Default for bike list and other views
    'PAGE_SIZE_QUERY_PARAM': 'page_size',  # Allow overriding page size via query parameter
    'MAX_PAGE_SIZE': 100,  # Set a reasonable maximum

    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ]
}


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
print("MEDIA_ROOT:", MEDIA_ROOT)

# payment-related settings at the bottom of settings.py

# PayPal (already present)
PAYPAL_RECEIVER_EMAIL = os.getenv('PAYPAL_RECEIVER_EMAIL', 'sb-6imge37854947@business.example.com')
PAYPAL_TEST = os.getenv('PAYPAL_TEST', 'True') == 'True'

# eSewa
ESEWA_PRODUCT_CODE = os.getenv('ESEWA_PRODUCT_CODE', 'EPAYTEST')  # Test code for development
ESEWA_SECRET_KEY = os.getenv('ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')  # Test secret for UAT
ESEWA_GATEWAY_URL = os.getenv('ESEWA_GATEWAY_URL', 'https://rc-epay.esewa.com.np/api/epay/main/v2/form')  # Test URL
ESEWA_VERIFY_URL = os.getenv('ESEWA_VERIFY_URL', 'https://rc-epay.esewa.com.np/api/epay/transaction/status')  # Test verification URL


LOGIN_URL = '/login/'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}


# Email settings for Gmail SMTP
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'easymotoservices@gmail.com'
EMAIL_HOST_PASSWORD = 'bilx ibog esrb kipp'  # App Password
DEFAULT_FROM_EMAIL = 'easymotoservices@gmail.com'
EMAIL_TIMEOUT = 10  # timeout to prevent hanging
EMAIL_USE_SSL = False  # we're using TLS on port 587