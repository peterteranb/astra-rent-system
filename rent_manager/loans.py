"""Business rules for equipment loans (PB-01).

The functions receive the inventory and the recorded loans as arguments.
They do no input/output and no storage, so a future interface or database
can use them without changes.
"""
from dataclasses import dataclass

class EquipmentNotFoundError(Exception):
    """Raised when an inventory number is not in the inventory."""

class EquipmentNotAvailableError(Exception):
    """Raised when a unit already has an active loan."""

@dataclass
class Equipment:
    inventory_id: str
    serial_number: str
    description: str


@dataclass
class Loan:
    inventory_id: str
    borrower_name: str


def is_available(
    inventory: dict[str, Equipment], loans: list[Loan], inventory_id: str
) -> bool:
    """Return True if the unit is registered and has no active loan.

    Does not modify the inventory or the loans.
    """
    if inventory_id not in inventory:
        return False
    return not any(loan.inventory_id == inventory_id for loan in loans)


def register_loan(
    inventory: dict[str, Equipment],
    loans: list[Loan],
    inventory_id: str,
    borrower_name: str,
) -> Loan:
    """Record a loan of one unit and return it.

    Raises EquipmentNotFoundError if the unit is not registered and
    EquipmentNotAvailableError if it already has an active loan.
    In both cases the loans list is left unchanged.
    """
    if inventory_id not in inventory:
        raise EquipmentNotFoundError(f"Equipment {inventory_id} is not registered.")
    if not is_available(inventory, loans, inventory_id):
        raise EquipmentNotAvailableError(f"Equipment {inventory_id} is already on loan.")

    new_loan = Loan(inventory_id=inventory_id, borrower_name=borrower_name)
    loans.append(new_loan)
    return new_loan