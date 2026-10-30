"""Configuración para correr las pruebas: la misma del proyecto con ajustes que solo sirven para probar."""
import os

# Las pruebas no necesitan la clave secreta real: así corren igual en GitHub Actions, sin .env.
os.environ.setdefault("SECRET_KEY", "clave-solo-para-las-pruebas")

from .settings import *
from .settings import LOGGING, STORAGES

# Solo en las pruebas: el hash real tarda unos 0,3 s por usuario y MD5 es instantáneo.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Las pruebas leen mail.outbox apenas termina la operación: sin hilo, el correo ya está ahí.
EMAIL_IN_BACKGROUND = False

# Sin handlers propios las líneas suben al logger raíz, donde caplog las lee: logs/negocio.log es de la demo.
LOGGING["loggers"]["rentals"]["handlers"] = []
LOGGING["loggers"]["rentals"]["propagate"] = True

# Las pruebas no corren collectstatic: los estáticos se sirven sin el manifiesto de whitenoise.
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Sin collectstatic no existe staticfiles/: whitenoise busca los archivos en cada petición y no avisa.
WHITENOISE_AUTOREFRESH = True
