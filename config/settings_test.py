"""Configuración para correr las pruebas: la misma del proyecto con un hash de contraseñas rápido."""
from .settings import *  # noqa: F401,F403

# Solo afecta a las pruebas: el hash real tarda unos 0,3 s por usuario creado
# y MD5 es instantáneo. Las contraseñas de la base real siguen con el hash seguro.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
