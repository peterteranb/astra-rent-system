from rent_manager import (
    is_available,
    register_loan,
    Equipment,
    Loan
)


# ---------- Tests: is_available ----------

def test_equipment_not_in_inventory():
    # Equipment id does not exist in the inventory at all -> not available
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
        "INV-002": Equipment("INV-002", "SN-67890", "Microfono"),
    }
    loans = []
    assert is_available(inventory, loans, "INV-999") is False


def test_equipment_exists_with_no_loans_is_available():
    # Equipment exists and there are no loans at all -> available
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
        "INV-002": Equipment("INV-002", "SN-67890", "Microfono"),
    }
    loans = []
    assert is_available(inventory, loans, "INV-001") is True


def test_equipment_with_active_loan_is_not_available():
    # Equipment exists but has an active loan -> not available
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
        "INV-002": Equipment("INV-002", "SN-67890", "Microfono"),
    }
    loans = [Loan(inventory_id="INV-001", borrower_name="Juan Perez")]
    assert is_available(inventory, loans, "INV-001") is False


def test_loan_of_other_equipment_does_not_affect_availability():
    # An active loan exists, but for a different equipment id (INV-002),
    # so INV-001 must remain available while INV-002 does not
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
        "INV-002": Equipment("INV-002", "SN-67890", "Microfono"),
    }
    loans = [Loan(inventory_id="INV-002", borrower_name="Ana Gomez")]
    assert is_available(inventory, loans, "INV-001") is True
    assert is_available(inventory, loans, "INV-002") is False


def test_multiple_loans_none_for_the_checked_equipment():
    # Several loans exist, but none of them reference the checked equipment id
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
        "INV-002": Equipment("INV-002", "SN-67890", "Microfono"),
    }
    loans = [
        Loan(inventory_id="INV-002", borrower_name="Ana Gomez"),
        Loan(inventory_id="INV-002", borrower_name="Luis Rojas"),
    ]
    assert is_available(inventory, loans, "INV-001") is True


def test_empty_inventory_equipment_not_found():
    # Inventory is completely empty -> any equipment id is "not found" -> not available
    inventory = {}
    loans = []
    assert is_available(inventory, loans, "INV-001") is False


def test_empty_loans_list_existing_equipment():
    # Loans list is empty, equipment exists -> available
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    }
    loans = []
    assert is_available(inventory, loans, "INV-001") is True


# ---------- Tests: register_loan ----------

def test_register_loan_succeeds_when_available():
    # Equipment is available -> register_loan must return a Loan object
    # with the correct inventory_id and borrower_name
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    }
    loans = []
    result = register_loan(inventory, loans, "INV-001", "Juan Perez")

    assert isinstance(result, Loan)
    assert result.inventory_id == "INV-001"
    assert result.borrower_name == "Juan Perez"


def test_successful_loan_is_added_to_loans_list():
    # After a successful register_loan, the new Loan must appear in the loans list
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    }
    loans = []
    register_loan(inventory, loans, "INV-001", "Juan Perez")

    assert len(loans) == 1
    assert loans[0].inventory_id == "INV-001"
    assert loans[0].borrower_name == "Juan Perez"


def test_register_loan_rejected_when_equipment_already_loaned():
    # Equipment is already loaned out -> second register_loan must fail
    # and must NOT add a second loan to the list
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    }
    loans = []
    register_loan(inventory, loans, "INV-001", "Juan Perez")
    result = register_loan(inventory, loans, "INV-001", "Ana Gomez")

    assert result == "INV-001 is not available"
    assert len(loans) == 1


def test_register_loan_rejected_when_equipment_not_in_inventory():
    # Equipment id does not exist in the inventory -> register_loan must fail
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    }
    loans = []
    result = register_loan(inventory, loans, "INV-999", "Juan Perez")

    assert result == "INV-999 is not available"
    assert len(loans) == 0


def test_two_different_equipment_can_be_loaned_independently():
    # Two different equipment ids can each be loaned successfully,
    # loans list must end up with both entries
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
        "INV-002": Equipment("INV-002", "SN-67890", "Microfono"),
    }
    loans = []
    result_1 = register_loan(inventory, loans, "INV-001", "Juan Perez")
    result_2 = register_loan(inventory, loans, "INV-002", "Ana Gomez")

    assert isinstance(result_1, Loan)
    assert isinstance(result_2, Loan)
    assert len(loans) == 2


def test_same_equipment_cannot_be_loaned_twice_in_a_row():
    # Same borrower trying to loan the same equipment they already have
    # must also be rejected (equipment is still unavailable)
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    }
    loans = []
    register_loan(inventory, loans, "INV-001", "Juan Perez")
    result = register_loan(inventory, loans, "INV-001", "Juan Perez")

    assert result == "INV-001 is not available"
    assert len(loans) == 1


def test_equipment_available_again_after_loan_is_removed():
    # Simulates the equipment being returned (its loan removed from the list),
    # after which it should be possible to register a new loan for it
    inventory = {
        "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    }
    loans = []
    register_loan(inventory, loans, "INV-001", "Juan Perez")
    loans.clear()  # simulates returning the equipment

    result = register_loan(inventory, loans, "INV-001", "Ana Gomez")
    assert isinstance(result, Loan)
    assert len(loans) == 1
