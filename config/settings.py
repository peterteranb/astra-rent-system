"""Configuración de Django del proyecto; los datos secretos se leen del archivo .env."""
import os
from decimal import Decimal
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Los valores por defecto sirven solo para desarrollo; en un servidor real
# se ponen en .env una clave secreta propia y DEBUG=False.
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-solo-para-desarrollo")
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = []

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

AUTH_USER_MODEL = "accounts.User"

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
