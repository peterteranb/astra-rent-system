"""Funciones de ayuda para las pruebas.

Diferencia con conftest.py:
    conftest.py tiene fixtures, que solo existen DENTRO de una prueba.
    Aqui hay funciones normales, que se importan y se pueden usar en cualquier
    lugar, por ejemplo para crear constantes al inicio de un archivo de pruebas.
"""
from datetime import datetime

from django.utils import timezone


def local_datetime(year, month, day, hour, minute=0):
    """Crea una fecha y hora CON zona horaria de La Paz (America/La_Paz).

    Ejemplo: local_datetime(2026, 10, 9, 18) -> 09/10/2026 18:00 en Bolivia.

    Por que hace falta: el proyecto usa USE_TZ = True, asi que todas las fechas
    llevan zona horaria. timezone.make_aware() le pone la zona de TIME_ZONE
    (settings.py). Sin esto, las comparaciones con 18:00 y 09:00 fallarian.
    """
    return timezone.make_aware(datetime(year, month, day, hour, minute))
