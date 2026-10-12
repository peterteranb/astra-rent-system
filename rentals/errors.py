"""Domain errors raised when a rental request is rejected.

The message of each error is written for the client, in Spanish, and
names the cause of the rejection (PRE-RC-01).
"""


class RentalRejectedError(Exception):
    """Base class: the rental was not saved. The view catches this one."""


class EquipmentNotAvailableError(RentalRejectedError):
    """The unit is not "available" or already has an overlapping rental (E1)."""


class InvalidPeriodError(RentalRejectedError):
    """The return is not after the pickup, or the rental is too long."""


class OutsideRentalHoursError(RentalRejectedError):
    """The pickup or return time is outside the allowed window (ENT-19)."""
