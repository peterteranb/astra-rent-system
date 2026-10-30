"""Configuración para correr las pruebas: la misma del proyecto con ajustes que solo sirven para probar."""
import os

# Las pruebas no necesitan la clave secreta real: así corren igual en GitHub Actions, sin .env.
os.environ.setdefault("SECRET_KEY", "clave-solo-para-las-pruebas")

from .settings import *  # noqa: E402,F401,F403
from .settings import LOGGING, STORAGES  # noqa: E402

# Solo afecta a las pruebas: el hash real tarda unos 0,3 s por usuario creado
# y MD5 es instantáneo. Las contraseñas de la base real siguen con el hash seguro.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Las pruebas leen mail.outbox apenas termina la operación: sin hilo, el correo ya está ahí.
EMAIL_IN_BACKGROUND = False

# Las pruebas no escriben en logs/negocio.log: ese archivo es el de la demo.
LOGGING["loggers"]["rentals"]["handlers"] = ["console"]

# Las pruebas no corren collectstatic: los estáticos se sirven sin el manifiesto de whitenoise.
STORAGES = {
    **STORAGES,
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

# Sin collectstatic no existe staticfiles/: whitenoise busca los archivos en cada petición y no avisa.
WHITENOISE_AUTOREFRESH = True
