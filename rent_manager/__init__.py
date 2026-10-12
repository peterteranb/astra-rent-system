# Iteration 1 baseline, frozen. Replaced by the rentals app. Kept so its tests stay as regression baseline.
from .loans import (
    Equipment,
    EquipmentNotAvailableError,
    EquipmentNotFoundError,
    Loan,
    is_available,
    register_loan,
)