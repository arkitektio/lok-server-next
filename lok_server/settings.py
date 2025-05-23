"""
Django settings for kreature project.

Generated by 'django-admin startproject' using Django 4.2.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import os
from pathlib import Path

from omegaconf import OmegaConf

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
FAKTS_PROTOCOL_VERSION = "0.1.0"
DEPLOYMENT_NAME = conf.deployment.name
DEPLOYMENT_DESCRIPTION = conf.deployment.get("description", "A Basic Arkitekt Deployment")
# Application definition


USER_DEFINED_BACKEND_NAME = "user_defined"


INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_probes",
    "pak",
    "authapp",
    "guardian",
    "komment",
    "channels",
    "fakts",
    "karakter",
]

FAKTS_LAYERS = [
    {
        "NAME": "Web Layer",
        "DESCRIPTION": "The default web layer",
        "KIND": "WEB",
        "IDENTIFIER": "web",
        "GET_PROBE": "https://google.com",
    },
    {
        "NAME": "Johannes Tailscale",
        "DESCRIPTION": "The Johannes tailscale",
        "KIND": "TAILSCALE",
        "IDENTIFIER": "tailscale",
        "DNS_PROBE": "jhnnsrs-lab",
    },
]


FAKTS_BACKENDS = [
    {
        "NAME": "contrib.backends.docker_backend.DockerBackend",
        "BUILDERS": [
            "arkitekt.lok",
            "arkitekt.generic",
            "arkitekt.rekuest",
            "arkitekt.s3",
            "livekitio.livekit",
            "ollama.ollama",
        ],
        "DEFAULT_BUILDER": "arkitekt.generic",
    },
    {
        "NAME": "contrib.backends.config_backend.ConfigBackend",
    },
]


ACCOUNT_EMAIL_VERIFICATION = "none"  # we don't have an smpt server by default

# Authentikate section

AUTH_USER_MODEL = "karakter.User"


AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]

SUPERUSERS = [
    {
        "USERNAME": conf.django.admin.username,
        "EMAIL": "fake@fake.com",
        "PASSWORD": conf.django.admin.password,
    }
]

SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # because we are going to be run behind a reverse proxy


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# S3_PUBLIC_DOMAIN = f"{conf.s3.public.host}:{conf.s3.public.port}"  # TODO: FIx
AWS_ACCESS_KEY_ID = conf.s3.access_key
AWS_SECRET_ACCESS_KEY = conf.s3.secret_key
AWS_S3_ENDPOINT_URL = f"{conf.s3.protocol}://{conf.s3.host}:{conf.s3.port}"
# AWS_S3_PUBLIC_ENDPOINT_URL = (
#    f"{conf.minio.public.protocol}://{conf.minio.public.host}:{conf.minio.public.port}"
# )
AWS_S3_URL_PROTOCOL = f"{conf.s3.protocol}:"
AWS_S3_FILE_OVERWRITE = False
AWS_QUERYSTRING_EXPIRE = 3600
AWS_S3_REGION_NAME = conf.s3.get("region", "us-east-1")

MEDIA_BUCKET = conf.s3.buckets.media

AWS_STORAGE_BUCKET_NAME = conf.s3.buckets.media
AWS_DEFAULT_ACL = "private"
AWS_S3_USE_SSL = True
AWS_S3_SECURE_URLS = False

CHANNEL_LAYERS = {
    "default": {
        # This example app uses the Redis channel layer implementation channels_redis
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [(conf.redis.host, conf.redis.port)], "prefix": "mikro"},
    },
}

CORS_ALLOW_ALL_ORIGINS = True


ROOT_URLCONF = "lok_server.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
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

INITIAL_MESSAGE_TEMPLATE = [
    {
        "title": "Welcome {user.name} :) This will be fun",
        "description": "It will be fun setting this up for you",
        "unique": "initial_message",
    }
]


WSGI_APPLICATION = "lok_server.wsgi.application"
ASGI_APPLICATION = "lok_server.asgi.application"


REDEEM_TOKENS = conf.get("redeem_tokens", [])


CA_FILE = conf.get("ca_file", "/certs/ca.crt")


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
    "IMITATE_PERMISSION": "kante.imitate",
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

PRIVATE_KEY = conf.private_key

AUTHENTIKATE = {
    "ISSUERS": [
        {
            "iss": "lok",
            "kind": "rsa",
            "public_key": conf.lok.get("public_key", None),
        }
    ],
    "STATIC_TOKENS": conf.lok.get("static_tokens", {}),
}


OAUTH2_PROVIDER = {
    "OIDC_ENABLED": True,
    "OIDC_RSA_PRIVATE_KEY": conf.private_key,
    "SCOPES": {
        "openid": "OpenID Connect scope",
        **conf.scopes,
        # ... any other scopes that you use
    },
    "ACCESS_TOKEN_EXPIRE_SECONDS": conf.token_expire_seconds or 60 * 60 * 24,  # TOkens are valid for 24 Hours
    "OAUTH2_VALIDATOR_CLASS": "karakter.oauth2.validator.CustomOAuth2Validator",
    "OAUTH2_SERVER_CLASS": "karakter.oauth2.server.JWTServer",
    "ALLOWED_REDIRECT_URI_SCHEMES": conf.get(
        "allowed_redirect_uri_schemes",
        [
            "http",
            "https",
            "tauri",
            "arkitekt",
            "exp",
            "orkestrator",
            "doks",
            "kranken",
        ],
    ),
    "PKCE_REQUIRED": False,  # to allow no challenges
}

OAUTH2_JWT = {
    "PRIVATE_KEY": conf.private_key,
    "PUBLIC_KEY": conf.public_key,
    "KEY_TYPE": conf.get("key_type", "RS256"),
    "ISSUER": "herre",
}

STRAWBERRY_DJANGO = {
    "TYPE_DESCRIPTION_FROM_MODEL_DOCSTRING": True,
    "FIELD_DESCRIPTION_FROM_HELP_TEXT": True,
    "USE_DEPRECATED_FILTERS": True,
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


# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

CSRF_TRUSTED_ORIGINS = conf.get("csrf_trusted_origins", ["http://localhost", "https://localhost"])
MY_SCRIPT_NAME = conf.get("force_script_name", "lok")
STATIC_URL = MY_SCRIPT_NAME.lstrip("/") + "/" + "static/"


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


ENSURED_APPS = []

ENSURED_USERS = OmegaConf.to_object(conf.users)

SYSTEM_MESSAGES = conf.get(
    "system_messages",
    [
        {
            "title": "Welcome to Lok",
            "message": "Now that you are here, you can start creating your own compositions",
        }
    ],
)

STATIC_ROOT = os.path.join(BASE_DIR, "static")

SOCIALACCOUNT_PROVIDERS = {
    "github": {
        # For each provider, you can choose whether or not the
        # email address(es) retrieved from the provider are to be
        # interpreted as verified.
        "VERIFIED_EMAIL": True
    },
    "orcid": {
        "SCOPE": [
            "openid",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
        },
    },
}


MY_SCRIPT_NAME = conf.get("force_script_name", "lok")
