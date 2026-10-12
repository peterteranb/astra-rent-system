"""Load the demo data: tables, chairs and two clients.

Safe to run many times: it creates what is missing and resets the demo
units and passwords to their initial values. It never deletes rentals.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from rentals.models import Equipment, EquipmentStatus

DEMO_PASSWORD = "demo1234"

# Catalog is only tables and chairs for now (ENT-07).
# EQ-06 starts "in review" so the demo can show a rejected request (E1).
DEMO_EQUIPMENT = [
    ("EQ-01", "SN-T-001", "Mesa plegable 1,80 m", EquipmentStatus.AVAILABLE),
    ("EQ-02", "SN-T-002", "Mesa plegable 1,80 m", EquipmentStatus.AVAILABLE),
    ("EQ-03", "SN-T-003", "Mesa redonda 1,20 m", EquipmentStatus.AVAILABLE),
    ("EQ-04", "SN-C-001", "Silla plegable blanca", EquipmentStatus.AVAILABLE),
    ("EQ-05", "SN-C-002", "Silla plegable blanca", EquipmentStatus.AVAILABLE),
    ("EQ-06", "SN-C-003", "Silla Tiffany dorada", EquipmentStatus.IN_REVIEW),
]

# Usernames c01 and c02 stand for clients C-01 and C-02 of the documents.
DEMO_CLIENTS = ["c01", "c02"]


class Command(BaseCommand):
    help = "Create the demo equipment and the demo clients c01 and c02."

    def handle(self, *args, **options):
        self.create_equipment()
        self.create_clients()
        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    def create_equipment(self):
        for inventory_id, serial_number, description, status in DEMO_EQUIPMENT:
            # update_or_create keeps one row per inventory_id and puts the
            # demo values back if someone changed them in /admin.
            Equipment.objects.update_or_create(
                inventory_id=inventory_id,
                defaults={
                    "serial_number": serial_number,
                    "description": description,
                    "status": status,
                },
            )
            self.stdout.write(f"Equipment {inventory_id} ready.")

    def create_clients(self):
        User = get_user_model()
        for username in DEMO_CLIENTS:
            user, _created = User.objects.get_or_create(username=username)
            # set_password stores a hash, never the plain text.
            user.set_password(DEMO_PASSWORD)
            user.save()
            self.stdout.write(f"Client {username} ready (password: {DEMO_PASSWORD}).")
