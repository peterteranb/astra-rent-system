# Possible future tests
#===========================================================================================================================
# Dataclass Verification:
# Tests direct creation and field integrity for both Equipment and Loan dataclasses
# Case Sensitivity & Null Handling:
# Tests how is_available handles lowercase matches (inv-001 vs INV-001), empty strings "", and None
# Inventory Immutability:
# Verifies that registering a loan modifies the loans list without accidentally mutating or deleting entries from inventory
# Single Borrower / Multiple Items:
# Ensures a single user (e.g., Andrew) can check out several items at once without triggering false unavailability flags

import pytest
from rent_manager.loans import (
    Equipment,
    EquipmentNotAvailableError,
    EquipmentNotFoundError,
    Loan,
    is_available,
    register_loan,
)


# ---------- Pending client decisions (skipped until agreed) ----------

@pytest.mark.skip(reason="Pending client decision: which borrower names are valid?")
def test_borrower_name_with_whitespace_and_special_characters():
    """Verify registration with whitespace and special characters in borrower names."""
    inventory = {
        "INV-001": Equipment("INV-001", "SN-100", "Projector"),
    }
    loans = []

    result = register_loan(inventory, loans, "INV-001", "  Andrew O'Connor-Smith  ")
    assert isinstance(result, Loan)
    assert result.borrower_name == "  Andrew O'Connor-Smith  "

@pytest.mark.skip(reason="Pending client decision: are inventory numbers case-sensitive?")
def test_inventory_keys_case_sensitivity():
    """Verify that inventory lookup handles case sensitivity properly."""
    inventory = {
        "INV-001": Equipment("INV-001", "SN-100", "Projector"),
    }
    loans = []

    assert is_available(inventory, loans, "inv-001") is False
    with pytest.raises(EquipmentNotFoundError):
        register_loan(inventory, loans, "inv-001", "Andrew")

@pytest.mark.skip(reason="Pending decision: can a registered loan be modified? P01 asks to keep history")
def test_loan_mutation_isolation():
    """Check whether a registered loan can be modified after it is recorded."""
    inventory = {
        "INV-001": Equipment("INV-001", "SN-100", "Projector"),
        "INV-002": Equipment("INV-002", "SN-200", "Laptop"),
    }
    loans = []

    loan1 = register_loan(inventory, loans, "INV-001", "Andrew")
    assert len(loans) == 1

    loan1.borrower_name = "Andrew Modified"
    assert loans[0].borrower_name == "Andrew Modified"


# ---------- Dataclass & State Verification ----------

def test_equipment_dataclass_equality_and_repr():
    """Check dataclass behaviors for Equipment and Loan models."""
    eq1 = Equipment("INV-001", "SN-100", "Projector")
    eq2 = Equipment("INV-001", "SN-100", "Projector")

    assert eq1 == eq2
    assert repr(eq1) == "Equipment(inventory_id='INV-001', serial_number='SN-100', description='Projector')"


def test_loan_dataclass_equality():
    """Check dataclass behaviors for Loan model."""
    loan1 = Loan(inventory_id="INV-001", borrower_name="Andrew")
    loan2 = Loan(inventory_id="INV-001", borrower_name="Andrew")

    assert loan1 == loan2


# ---------- Batch Operations ----------

def test_register_multiple_loans_until_inventory_exhausted():
    """Test full inventory depletion workflow, one borrower per unit."""
    inventory = {
        f"INV-00{i}": Equipment(f"INV-00{i}", f"SN-{i}", f"Item {i}")
        for i in range(1, 5)
    }
    loans = []
    borrowers = ["Ana", "Juan", "Luis", "Marta"]

    for item_id, borrower in zip(inventory, borrowers):
        res = register_loan(inventory, loans, item_id, borrower)
        assert isinstance(res, Loan)

    assert len(loans) == 4

    for item_id in inventory:
        assert is_available(inventory, loans, item_id) is False


# ---------- Inventory Immutability ----------

def test_inventory_immutability_on_loan_registration():
    """Verify that registering a loan does NOT mutate or delete entries from the inventory."""
    inventory = {
        "INV-001": Equipment("INV-001", "SN-100", "Projector"),
        "INV-002": Equipment("INV-002", "SN-200", "Laptop"),
    }
    loans = []

    # Store shallow copy / initial state of the inventory for comparison
    inventory_keys_before = set(inventory.keys())
    inv_001_before = Equipment("INV-001", "SN-100", "Projector")

    # Register a loan
    result = register_loan(inventory, loans, "INV-001", "Andrew")

    # Assert loan creation succeeded
    assert isinstance(result, Loan)
    assert len(loans) == 1

    # Assert inventory keys and length were not modified or deleted
    assert set(inventory.keys()) == inventory_keys_before
    assert len(inventory) == 2

    # Assert specific equipment object inside inventory was not mutated
    assert inventory["INV-001"] == inv_001_before
    assert inventory["INV-001"].inventory_id == "INV-001"
    assert inventory["INV-001"].serial_number == "SN-100"
    assert inventory["INV-001"].description == "Projector"