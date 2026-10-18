"""Use case: maintenance reviews a returned unit and sets its new status."""
from .errors import InvalidStatusChangeError
from .history import change_status
from .statuses import EquipmentStatus

# The client agreed (review flow of 17/10): from review or repair a unit goes
# to available, to repair or to retired, and a retired unit never comes back.
# Not agreed: whether the source status must be "in review" or "in repair".
REVIEW_RESULTS = (
    EquipmentStatus.AVAILABLE,
    EquipmentStatus.IN_REPAIR,
    EquipmentStatus.RETIRED,
)


def review_equipment(equipment, staff_user, new_status, comment=""):
    """Set the new status of a reviewed unit, keep the change in its history and return it.

    Raises InvalidStatusChangeError if new_status is not a result of a review
    or the unit is retired; then nothing changes.
    """
    check_review_result(equipment, new_status)
    return change_status(equipment, new_status, staff_user, comment)


def check_review_result(equipment, new_status):
    """Raise InvalidStatusChangeError if new_status is not available, in repair or retired."""
    if new_status not in REVIEW_RESULTS:
        raise InvalidStatusChangeError(
            f"El equipo {equipment.inventory_id} solo puede pasar a disponible, en reparación o baja."
        )