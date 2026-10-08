from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class EquipmentStatus(models.TextChoices):
    AVAILABLE = 'AVAILABLE', 'Disponible'
    IN_REVISION = 'IN_REVISION', 'En Revisión'
    MAINTENANCE = 'MAINTENANCE', 'En Mantenimiento'


class Equipment(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=EquipmentStatus.choices,
        default=EquipmentStatus.AVAILABLE
    )

    def is_available_for_rent(self) -> bool:
        """Satisface PRE-RF-04: si está en revisión o mantenimiento no se puede rentar."""
        return self.status == EquipmentStatus.AVAILABLE

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class RentalStatus(models.TextChoices):
    CONFIRMED = 'CONFIRMED', 'Confirmada'
    CANCELLED = 'CANCELLED', 'Cancelada'
    COMPLETED = 'COMPLETED', 'Completada'


class Rental(models.Model):
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rentals'
    )
    equipment = models.ForeignKey(
        Equipment,
        on_delete=models.CASCADE,
        related_name='rentals'
    )
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=RentalStatus.choices,
        default=RentalStatus.CONFIRMED
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.start_datetime and self.end_datetime:
            if self.start_datetime >= self.end_datetime:
                raise ValidationError("La fecha de retiro debe ser anterior a la fecha de devolución.")

    def __str__(self):
        return f"Renta #{self.id} - {self.equipment.name} por {self.client.username}"