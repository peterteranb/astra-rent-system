"""Funciones de ayuda para las pruebas.

Diferencia con conftest.py:
    conftest.py tiene fixtures, que solo existen DENTRO de una prueba.
    Aqui hay funciones normales, que se importan y se pueden usar en cualquier
    lugar, por ejemplo para crear constantes al inicio de un archivo de pruebas.
"""
from datetime import datetime

from django.utils import timezone

from rentals.models import Equipment, Rental, StatusChange


def local_datetime(year, month, day, hour, minute=0):
    """Crea una fecha y hora CON zona horaria de La Paz (America/La_Paz).

    Ejemplo: local_datetime(2026, 10, 9, 18) -> 09/10/2026 18:00 en Bolivia.

    Por que hace falta: el proyecto usa USE_TZ = True, asi que todas las fechas
    llevan zona horaria. timezone.make_aware() le pone la zona de TIME_ZONE
    (settings.py). Sin esto, las comparaciones con 18:00 y 09:00 fallarian.
    """
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def foto_de_la_base():
    """Copia independiente de lo que cambian las operaciones: rentas, equipos e historial."""
    rentas = list(
        Rental.objects.order_by("pk").values(
            "pk",
            "client_id",
            "equipment_id",
            "start_datetime",
            "end_datetime",
            "picked_up_at",
            "returned_at",
            "cancelled_at",
            "return_note",
            "registered_by_id",
        )
    )
    equipos = list(Equipment.objects.order_by("pk").values("pk", "inventory_id", "status"))
    historial = list(
        StatusChange.objects.order_by("pk").values(
            "pk", "equipment_id", "old_status", "new_status", "changed_by_id", "changed_at", "comment"
        )
    )
    return rentas, equipos, historial
