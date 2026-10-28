"""Configuración de Django del proyecto; los datos secretos y lo que cambia por servidor se leen de .env."""
import os
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_list(name, default=""):
    """Lee de .env una lista separada por comas, por ejemplo «localhost,127.0.0.1»."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# DEBUG es False salvo que .env diga DEBUG=True: un servidor nunca queda en modo desarrollo por olvido.
DEBUG = os.environ.get("DEBUG", "False") == "True"
SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY and not DEBUG:
    raise ImproperlyConfigured("Falta SECRET_KEY en .env: es obligatoria con DEBUG=False.")
SECRET_KEY = SECRET_KEY or "django-insecure-solo-para-desarrollo"

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")
CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")

# USE_HTTPS=True solo detrás de HTTPS: con HTTP estas opciones impiden iniciar sesión.
USE_HTTPS = os.environ.get("USE_HTTPS", "False") == "True"
SESSION_COOKIE_SECURE = USE_HTTPS
CSRF_COOKIE_SECURE = USE_HTTPS
SECURE_SSL_REDIRECT = USE_HTTPS
SECURE_HSTS_SECONDS = 31536000 if USE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = USE_HTTPS
SECURE_HSTS_PRELOAD = USE_HTTPS

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "rentals",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # whitenoise sirve /static/ con gunicorn, sin un servidor web aparte.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Las plantillas de todo el proyecto están en /templates, en un solo lugar.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "rentals.context_processors.staff_roles",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "astra_rent"),
        "USER": os.environ.get("DB_USER", "astra"),
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    # ENT-84: además, al menos una mayúscula y un número.
    {"NAME": "accounts.validators.UppercaseAndDigitValidator"},
]

LANGUAGE_CODE = "es"
# Las reglas comparan horas de reloj de Bolivia (18:00, 09:00, 12:00).
TIME_ZONE = "America/La_Paz"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
# collectstatic junta aquí los estáticos; whitenoise los sirve comprimidos y con un nombre por versión.
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

AUTH_USER_MODEL = "accounts.User"
# ModelBackend va primero: con él entran las cuentas activas y su sesión deja de valer si se desactivan.
# El segundo solo reconoce una cuenta desactivada con su contraseña correcta, para decirle por qué no entra (ENT-79).
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "django.contrib.auth.backends.AllowAllUsersModelBackend",
]

# Reglas del negocio que el cliente puede cambiar sin tocar el código.
# ENT-71: el precio por día es el 5 % del valor del equipo.
DAILY_RATE = Decimal("0.05")
# ENT-74: reparación cobra el 20 % del valor y baja, el 100 %.
REPAIR_CHARGE_RATE = Decimal("0.20")
RETIRE_CHARGE_RATE = Decimal("1.00")
# ENT-83: 3 letras, guion y 5 números, por ejemplo MES-00001.
INVENTORY_ID_FORMAT = r"^[A-Z]{3}-[0-9]{5}$"

# Log de negocio (RC-05): cada operación del logger «rentals» va a la consola y a logs/negocio.log.
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "business": {
            "format": "{asctime} | {levelname:<7} | {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "business"},
        "business_file": {
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "negocio.log",
            "encoding": "utf-8",
            "formatter": "business",
            "delay": True,
        },
    },
    "loggers": {
        "rentals": {"handlers": ["console", "business_file"], "level": "INFO"},
    },
}

# Correo (ENT-85) con MAILERS de Django 6.1: consola por defecto y Gmail si .env trae
# la cuenta y su contraseña de aplicación.
gmail_user = os.environ.get("EMAIL_HOST_USER", "")
gmail_app_password = os.environ.get("EMAIL_HOST_PASSWORD", "")
if gmail_user and gmail_app_password:
    MAILERS = {
        "default": {
            "BACKEND": "django.core.mail.backends.smtp.EmailBackend",
            "OPTIONS": {
                "host": "smtp.gmail.com",
                "port": 587,
                "username": gmail_user,
                "password": gmail_app_password,
                "use_tls": True,
                "timeout": 10,
            },
        },
    }
    DEFAULT_FROM_EMAIL = f"SergioCorp <{gmail_user}>"
else:
    MAILERS = {"default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"}}
    DEFAULT_FROM_EMAIL = "SergioCorp <no-responder@sergiocorp.local>"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
