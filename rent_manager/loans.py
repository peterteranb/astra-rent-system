from dataclasses import dataclass

# Equipment(inventory_id, serial_number, description)
# Loan(inventory_id, borrower_name)
#
# funciones
# is_available(inventory, loans, inventory_id) -> bool
# register_loan(inventory, loans, inventory_id, borrower_name) -> Loan
#
#
# inventory: diccionario
# inventory_id -> Equipment
# loans: lista de Loan(todos activos en esta iteración)
# errores: EquipmentNotAvailableError, EquipmentNotFoundError

@dataclass
class Equipment:
    inventory_id: str
    serial_number: str
    description: str


@dataclass
class Loan:
    inventory_id: str
    borrower_name: str

# recibe diccionario de Equipment, lista de loans y inventory_id
def is_available(
    inventory: dict[str, Equipment], loans: list[Loan], inventory_id: str
) -> bool:
    # Verificar si el equipo existe
    if inventory_id not in inventory:
        return False

    # El equipo está disponible si NO se encuentra en la lista de préstamos activos
    return not any(loan.inventory_id == inventory_id for loan in loans)

# recibe diccionario de Equipment, lista de loans, inventory_id y borrower_name(nombre ficticio)
def register_loan(
    inventory: dict[str, Equipment],
    loans: list[Loan],
    inventory_id: str,
    borrower_name: str,
):
    # is_available lanzara false
    if not is_available(inventory, loans, inventory_id):
        return f"{inventory_id} is not available"

    # Crear y registrar el nuevo préstamo
    new_loan = Loan(inventory_id=inventory_id, borrower_name=borrower_name)
    loans.append(new_loan)
    return new_loan

inventory = {
    "INV-001": Equipment("INV-001", "SN-12345", "Parlante"),
    "INV-002": Equipment("INV-002", "SN-67890", "Microfono"),
}

# loans = [
#     Loan(inventory_id="INV-001", borrower_name="Alice")
# ]
#
# # 1. Consultar disponibilidad
# print(is_available(inventory, loans, "INV-001"))  # Output: False
# print(is_available(inventory, loans, "INV-002"))  # Output: True
#
# # 2. Registrar un préstamo exitoso
# new_loan = register_loan(inventory, loans, "INV-002", "Bob")
# print(f"Préstamo registrado a: {new_loan.borrower_name}")
# print(is_available(inventory, loans, "INV-002"))  # Output: False