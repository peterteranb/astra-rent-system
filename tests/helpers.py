"""Funciones de ayuda para las pruebas: fechas en hora de La Paz y una foto de la base para los rechazos."""
from datetime import datetime, timedelta

from django.utils import timezone

from rentals.models import Equipment, Rental, StatusChange


def local_datetime(year, month, day, hour, minute=0):
    """Crea una fecha y hora con la zona de La Paz, por ejemplo local_datetime(2026, 10, 9, 18) -> 09/10/2026 18:00."""
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def dentro_de(dias, hora, minuto=0):
    """Crea la fecha y hora de La Paz que cae dias después de hoy, a esa hora.

    Hace falta porque una reserva vence a las 12:00 del día siguiente: con una
    fecha fija que ya pasó, la reserva ya no ocuparía el equipo.
    """
    dia = timezone.localdate() + timedelta(days=dias)
    return local_datetime(dia.year, dia.month, dia.day, hora, minuto)


def foto_de_la_base():
    """Copia de todo lo que cambian las operaciones: rentas, equipos e historial."""
    rentas = list(Rental.objects.order_by("pk").values())
    equipos = list(Equipment.objects.order_by("pk").values())
    historial = list(StatusChange.objects.order_by("pk").values())
    return rentas, equipos, historial
