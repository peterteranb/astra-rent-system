"""Funciones de ayuda para las pruebas: fechas en hora de La Paz, una hora fija y una foto de la base para los rechazos."""
from datetime import datetime, timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.utils import timezone

from rentals.models import Debt, Equipment, Rental, StatusChange


def local_datetime(year, month, day, hour, minute=0):
    """Crea una fecha y hora con la zona de La Paz, por ejemplo local_datetime(2026, 10, 9, 18) -> 09/10/2026 18:00."""
    return timezone.make_aware(datetime(year, month, day, hour, minute))


def dentro_de(dias, hora, minuto=0):
    """Crea la fecha y hora de La Paz que cae dias después de hoy, a esa hora.

    Hace falta porque una reserva vence a la medianoche de su día de inicio: con
    una fecha fija que ya pasó, la reserva ya no ocuparía el equipo.
    """
    dia = timezone.localdate() + timedelta(days=dias)
    return local_datetime(dia.year, dia.month, dia.day, hora, minuto)


def con_la_hora(momento):
    """Hace que timezone.now() devuelva momento dentro de un bloque with, para probar horas exactas."""
    return mock.patch("django.utils.timezone.now", return_value=momento)


def foto_de_la_base():
    """Copia de todo lo que cambian las operaciones: usuarios, rentas, equipos, deudas e historial."""
    # last_login cambia al iniciar sesión, no con una operación del negocio.
    campos = [campo.attname for campo in get_user_model()._meta.concrete_fields if campo.name != "last_login"]
    usuarios = list(get_user_model().objects.order_by("pk").values(*campos))
    rentas = list(Rental.objects.order_by("pk").values())
    equipos = list(Equipment.objects.order_by("pk").values())
    deudas = list(Debt.objects.order_by("pk").values())
    historial = list(StatusChange.objects.order_by("pk").values())
    return usuarios, rentas, equipos, deudas, historial
