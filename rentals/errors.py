"""Errores que se lanzan cuando una operación se rechaza; su mensaje es la causa para el usuario (RC-04)."""


class OperationRejectedError(Exception):
    """Base de todos los rechazos: la operación no guardó nada. Las vistas atrapan esta."""


class RejectedWithCausesError(OperationRejectedError):
    """Rechazo con varias causas a la vez, para que la persona corrija todo de una sola vez."""

    def __init__(self, title, causes):
        """Guarda el título («No se creó la cuenta:») y la lista de causas."""
        super().__init__(f"{title} {' '.join(causes)}")
        self.title = title
        self.causes = causes


class InvalidPeriodError(OperationRejectedError):
    """Las fechas, los horarios o la duración del periodo pedido rompen una regla."""


class EquipmentNotAvailableError(OperationRejectedError):
    """El equipo no está «Disponible» o ya tiene otra renta en esas fechas (RF-01)."""


class RentalStateError(OperationRejectedError):
    """La renta no está en el estado que pide la operación: cancelada, entregada, vencida, devuelta o ya pagada."""


class PaymentRequiredError(OperationRejectedError):
    """Se quiere entregar una renta con el pago pendiente sin cobrarlo (ENT-68)."""


class DebtPendingError(OperationRejectedError):
    """El cliente tiene una deuda pendiente y no puede crear rentas (ENT-77)."""


class DeadlinePassedError(OperationRejectedError):
    """El cliente quiere cancelar o modificar a menos de 24 h del recojo (ENT-80)."""


class InvalidModificationError(OperationRejectedError):
    """Las fechas nuevas de una reserva no tienen la misma cantidad de días (ENT-81)."""


class IncompleteReturnError(OperationRejectedError):
    """A la devolución le falta la observación de cómo llegó el equipo."""


class InvalidStatusChangeError(OperationRejectedError):
    """El cambio de estado del equipo no se permite: está de baja, ya tiene ese estado o no es un resultado de revisión."""


class DebtStateError(OperationRejectedError):
    """La deuda ya se pagó."""


class EquipmentRegistrationError(RejectedWithCausesError):
    """Los datos de un equipo nuevo rompen una o más reglas (ENT-83)."""


class RegistrationRejectedError(RejectedWithCausesError):
    """Los datos de una cuenta nueva rompen una o más reglas (ENT-84)."""
