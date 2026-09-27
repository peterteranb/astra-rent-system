from dataclasses import dataclass

@dataclass
class Equipment:
    inventory_id: str
    serial_number: str
    description: str


@dataclass
class Loan:
    inventory_id: str
    borrower_name: str

# Receives an Equipment dictionary, a list of loans, and an inventory_id
def is_available(
    inventory: dict[str, Equipment], loans: list[Loan], inventory_id: str
) -> bool:
    # Check if the device exists
    if inventory_id not in inventory:
        return False

    # The equipment is available if it is NOT on the list of active loans
    return not any(loan.inventory_id == inventory_id for loan in loans)

# Receives an Equipment dictionary, a list of loans, inventory_id, and borrower_name (fictitious name)
def register_loan(
    inventory: dict[str, Equipment],
    loans: list[Loan],
    inventory_id: str,
    borrower_name: str,
):
    # is_available will return un mensaje
    if not is_available(inventory, loans, inventory_id):
        return f"{inventory_id} is not available"

    # Create and record the new loan
    new_loan = Loan(inventory_id=inventory_id, borrower_name=borrower_name)
    loans.append(new_loan)
    return new_loan