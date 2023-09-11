"""
Django settings for kreature project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path
from omegaconf import OmegaConf
import os


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
conf = OmegaConf.load(os.path.join(BASE_DIR, "config.yaml"))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-ltup=qzfv_bs+20ma(fd^1bsp_)5=!u#8$me3nmk4e6*woqb)r"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

COMPOSITIONS_DIR = os.path.join(BASE_DIR, "compositions")
DEPLOYMENT_NAME = conf.deployment.name
# Application definition

INSTALLED_APPS = [
    "daphne",
    "corsheaders",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "oauth2_provider",
    "ekke",
    "guardian",
    "komment",
    "channels",
    "fakts",
    "karakter",
]

# Authentikate section

AUTH_USER_MODEL = "karakter.User"


AUTHENTICATION_BACKENDS = [
    "oauth2_provider.backends.OAuth2Backend",
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CHANNEL_LAYERS = {
    "default": {
        # This example app uses the Redis channel layer implementation channels_redis
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(conf.redis.host, conf.redis.port)], "prefix": "mikro"},
    },
}

CORS_ALLOW_ALL_ORIGINS = True


ROOT_URLCONF = "lok.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "lok.wsgi.application"
ASGI_APPLICATION = "lok.asgi.application"


EKKE = {
    "PUBLIC_KEY": conf.lok.get("public_key", None),
    "PUBLIC_KEY_PEM_FILE": conf.lok.get("public_key_pem_file", None),
    "KEY_TYPE": conf.lok.get("key_type", "RS256"),
    "AUTHORIZATION_HEADERS": [
        "Authorization",
        "X-Auth-Token",
        "AUTHORIZATION",
        "authorization",
    ],
    "IMITATE_PERMISSION": "ekke.imitate",
    "ALLOW_IMITATE": True,
}
# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": conf.db.engine,
        "NAME": conf.db.db_name,
        "USER": conf.db.username,
        "PASSWORD": conf.db.password,
        "HOST": conf.db.host,
        "PORT": conf.db.port,
    }
}


# Unomment and re run
OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2_provider.Application"
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = "oauth2_provider.AccessToken"
OAUTH2_PROVIDER_REFRESH_TOKEN_MODEL = "oauth2_provider.RefreshToken"
OAUTH2_PROVIDER_ID_TOKEN_MODEL = "oauth2_provider.IDtoken"

OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    "OIDC_RSA_PRIVATE_KEY": conf.private_key,
    "SCOPES": {
        "openid": "OpenID Connect scope",
        **conf.scopes
        # ... any other scopes that you use
    },
    "ACCESS_TOKEN_EXPIRE_SECONDS": conf.token_expire_seconds
    or 60 * 60 * 24,  # TOkens are valid for 24 Hours
    "OAUTH2_VALIDATOR_CLASS": "karakter.oauth2.validator.CustomOAuth2Validator",
    "OAUTH2_SERVER_CLASS": "karakter.oauth2.server.JWTServer",
    "ALLOWED_REDIRECT_URI_SCHEMES": [
        "http",
        "https",
        "tauri",
        "arkitekt",
        "exp",
        "orkestrator",
        "doks",
        "kranken",
    ],
}

OAUTH2_JWT = {
    "PRIVATE_KEY": conf.private_key,
    "PUBLIC_KEY": conf.public_key,
    "KEY_TYPE": conf.get("key_type", "RS256"),
    "ISSUER": "herre",
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            # exact format is not important, this is the minimum information
            "format": "%(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "rich.logging.RichHandler",
            "formatter": "console",
            "rich_tracebacks": True,
        },
    },
    "loggers": {
        # root logger
        "": {
            "level": "INFO",
            "handlers": ["console"],
        },
        "oauthlib": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "delt": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "oauth2_provider": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

LOGIN_URL = "login"
LOGOUT_URL = "logout"

ENSURED_APPS = OmegaConf.to_object(conf.apps)

ENSURED_USERS = OmegaConf.to_object(conf.users)
