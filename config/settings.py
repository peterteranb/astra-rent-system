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

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"
