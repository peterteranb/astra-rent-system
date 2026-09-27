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
    Loan,
    is_available,
    register_loan,
)


# ---------- Edge Cases & Input Integrity ----------

def test_borrower_name_with_whitespace_and_special_characters():
    """Verify registration with empty string or whitespace borrower names."""
    inventory = {
        "INV-001": Equipment("INV-001", "SN-100", "Projector"),
    }
    loans = []

    result = register_loan(inventory, loans, "INV-001", "  Andrew O'Connor-Smith  ")
    assert isinstance(result, Loan)
    assert result.borrower_name == "  Andrew O'Connor-Smith  "


def test_inventory_keys_case_sensitivity():
    """Verify that inventory lookup handles case sensitivity properly."""
    inventory = {
        "INV-001": Equipment("INV-001", "SN-100", "Projector"),
    }
    loans = []

    # Lowercase lookup should fail if inventory keys are uppercase
    assert is_available(inventory, loans, "inv-001") is False
    result = register_loan(inventory, loans, "inv-001", "Andrew")
    assert result == "inv-001 is not available"


def test_loan_mutation_isolation():
    """Ensure returning a mutated/copied loan list doesn't break original state without side effects."""
    inventory = {
        "INV-001": Equipment("INV-001", "SN-100", "Projector"),
        "INV-002": Equipment("INV-002", "SN-200", "Laptop"),
    }
    loans = []

    loan1 = register_loan(inventory, loans, "INV-001", "Andrew")
    assert len(loans) == 1

    # Modify loan object attribute in-place
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


# ---------- Batch/Stress Operations ----------

def test_register_multiple_loans_until_inventory_exhausted():
    """Test full inventory depletion workflow."""
    inventory = {
        f"INV-00{i}": Equipment(f"INV-00{i}", f"SN-{i}", f"Item {i}")
        for i in range(1, 5)
    }
    loans = []

    # Borrow all items
    for item_id in inventory.keys():
        res = register_loan(inventory, loans, item_id, "Andrew")
        assert isinstance(res, Loan)

    assert len(loans) == 4

    # Confirm none are available anymore
    for item_id in inventory.keys():
        assert is_available(inventory, loans, item_id) is False