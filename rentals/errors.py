"""Domain errors raised when an operation is rejected.

The message of each error is written for the user, in Spanish, and
names the cause of the rejection (PRE-RC-01).
"""


class OperationRejectedError(Exception):
    """Base class: the operation was not saved. The views catch this one."""


class EquipmentNotAvailableError(OperationRejectedError):
    """The unit is not "available" or already has an overlapping rental (E1)."""


class InvalidPeriodError(OperationRejectedError):
    """The return is not after the pickup, or the rental is too long."""


class OutsideRentalHoursError(OperationRejectedError):
    """The pickup or return time is outside the allowed window (ENT-19)."""


class AlreadyPickedUpError(OperationRejectedError):
    """The unit of the rental was already picked up."""


class ReservationExpiredError(OperationRejectedError):
    """The reservation was not picked up before the pickup deadline."""


class AlreadyReturnedError(OperationRejectedError):
    """The unit of the rental was already returned."""


class IncompleteReturnError(OperationRejectedError):
    """The return lacks something needed to register it."""


class RentalCancelledError(OperationRejectedError):
    """The rental was cancelled."""


class RentalNotCancellableError(OperationRejectedError):
    """The rental is no longer a reservation, so it cannot be cancelled."""


class InvalidStatusChangeError(OperationRejectedError):
    """The unit is retired, and a retirement is final."""
