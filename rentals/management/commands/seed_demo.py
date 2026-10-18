"""Load the demo data: tables, chairs, two clients, the staff and the admin.

Safe to run many times: it creates what is missing and resets the demo
units and passwords to their initial values. It never deletes rentals.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from rentals.models import Equipment, EquipmentStatus
from rentals.roles import MAINTENANCE, OPERATOR

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
DEMO_STAFF = [("op01", OPERATOR), ("mt01", MAINTENANCE)]
DEMO_ADMIN = "admin"


class Command(BaseCommand):
    """Create or reset the demo data."""

    help = "Create the demo equipment, the clients c01 and c02, op01, mt01 and admin."

    def handle(self, *args, **options):
        """Load every part of the demo data."""
        self.create_equipment()
        self.create_clients()
        self.create_staff()
        self.create_admin()
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
        """Create the demo clients."""
        for username in DEMO_CLIENTS:
            reset_user(username)
            self.stdout.write(f"Client {username} ready (password: {DEMO_PASSWORD}).")

    def create_staff(self):
        """Create the operator and the maintenance user, each in its role's group."""
        for username, role in DEMO_STAFF:
            user = reset_user(username)
            user.groups.add(Group.objects.get(name=role))
            self.stdout.write(f"Staff {username} ({role}) ready (password: {DEMO_PASSWORD}).")

    def create_admin(self):
        """Create the administrator, who is the superuser."""
        user = reset_user(DEMO_ADMIN)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(f"Admin {DEMO_ADMIN} ready (password: {DEMO_PASSWORD}).")


def reset_user(username):
    """Create the user if missing, set the demo password and return it."""
    user, _created = get_user_model().objects.get_or_create(username=username)
    # set_password stores a hash, never the plain text.
    user.set_password(DEMO_PASSWORD)
    user.save()
    return user
