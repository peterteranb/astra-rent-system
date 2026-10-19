"""Errores que se lanzan cuando una operación se rechaza; su mensaje es la causa para el usuario (RC-01)."""


class OperationRejectedError(Exception):
    """Base de todos los rechazos: la operación no guardó nada. Las vistas atrapan esta."""


class InvalidPeriodError(OperationRejectedError):
    """Las fechas, los horarios o la duración del periodo pedido rompen una regla."""


class EquipmentNotAvailableError(OperationRejectedError):
    """El equipo no está «Disponible» o ya tiene otra renta en esas fechas (RF-01)."""


class RentalStateError(OperationRejectedError):
    """La renta no está en el estado que pide la operación: cancelada, entregada, vencida o devuelta."""


class IncompleteReturnError(OperationRejectedError):
    """A la devolución le falta la observación de cómo llegó el equipo (RF-08)."""


class InvalidStatusChangeError(OperationRejectedError):
    """El cambio de estado del equipo no se permite: está de baja, ya tiene ese estado o no es un resultado de revisión."""
