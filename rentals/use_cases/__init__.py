"""Casos de uso: cada función hace una operación completa (valida, bloquea, guarda, escribe el log y avisa).

CU → archivo
- CU-01, CU-02: accounts/registration.py · CU-17: accounts/account.py
- CU-03: catalog.py
- CU-04: renting.py (crear la renta) y payments.py (el QR)
- CU-05, CU-16: renting.py
- CU-06, CU-07: reservation_changes.py
- CU-08, CU-09: handover.py
- CU-10: review.py
- CU-11: debts.py
- CU-12: inventory.py
- CU-13: equipment_status.py · CU-14: el admin de Django (rentals/admin.py)
- CU-15: dashboard.py

Las dependencias van en un solo sentido: equipment_status -> reservation_changes -> renting -> debts.
"""
