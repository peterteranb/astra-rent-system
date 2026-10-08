from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Equipment, EquipmentStatus, Rental


def create_rental(*, client, equipment_id: int, start_datetime, end_datetime) -> Rental:
    """
    Registra una renta validando:
    1. PRE-RF-04: El equipo no está en revisión ni en mantenimiento.
    2. PRE-RF-01: No existe solapamiento con otra renta confirmada.
    """
    with transaction.atomic():
        equipment = Equipment.objects.select_for_update().get(pk=equipment_id)

        # Regla PRE-RF-04
        if equipment.status != EquipmentStatus.AVAILABLE:
            raise ValidationError("El equipo está en revisión o mantenimiento y no se puede rentar.")

        # Regla PRE-RF-01: Detección de traslapes en el rango de tiempo
        overlapping_rentals = Rental.objects.filter(
            equipment=equipment,
            start_datetime__lt=end_datetime,
            end_datetime__gt=start_datetime
        )

        if overlapping_rentals.exists():
            raise ValidationError("El equipo no está disponible.")

        rental = Rental(
            client=client,
            equipment=equipment,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
        rental.full_clean()
        rental.save()
        return rental