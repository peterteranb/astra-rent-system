"""Load the demo data: tables, chairs, two clients, the staff, the admin and three rentals.

Safe to run many times: it creates what is missing and resets the demo
units and passwords to their initial values. It never deletes rentals,
and it creates a demo rental only if its client has none for that unit.
"""
from datetime import date, datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.utils import timezone

from rentals.errors import OperationRejectedError
from rentals.models import Equipment, EquipmentStatus, Rental
from rentals.renting import create_rental
from rentals.roles import MAINTENANCE, OPERATOR

DEMO_PASSWORD = "demo1234"

# Catalog is only tables and chairs for now (ENT-07).
# EQ-06 starts "in review" so the demo can show a rejected request (E1) and
# EQ-05 "in repair"; both appear on the maintenance page.
DEMO_EQUIPMENT = [
    ("EQ-01", "SN-T-001", "Mesa plegable 1,80 m", EquipmentStatus.AVAILABLE),
    ("EQ-02", "SN-T-002", "Mesa plegable 1,80 m", EquipmentStatus.AVAILABLE),
    ("EQ-03", "SN-T-003", "Mesa redonda 1,20 m", EquipmentStatus.AVAILABLE),
    ("EQ-04", "SN-C-001", "Silla plegable blanca", EquipmentStatus.AVAILABLE),
    ("EQ-05", "SN-C-002", "Silla plegable blanca", EquipmentStatus.IN_REPAIR),
    ("EQ-06", "SN-C-003", "Silla Tiffany dorada", EquipmentStatus.IN_REVIEW),
]

# Usernames c01 and c02 stand for clients C-01 and C-02 of the documents.
# The names are fictitious; the operator searches clients by them.
DEMO_CLIENTS = [("c01", "Carla", "Mendoza"), ("c02", "Diego", "Rojas")]
DEMO_STAFF = [("op01", OPERATOR), ("mt01", MAINTENANCE)]
DEMO_ADMIN = "admin"


class Command(BaseCommand):
    """Create or reset the demo data."""

    help = "Create the demo equipment, clients, staff, admin and three rentals."

    def handle(self, *args, **options):
        """Load every part of the demo data."""
        self.create_equipment()
        self.create_clients()
        self.create_staff()
        self.create_admin()
        self.create_rentals()
        self.stdout.write(self.style.SUCCESS("Demo data ready."))

    def create_equipment(self):
        """Create the demo units, or put their initial values back."""
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
        """Create the demo clients with their first and last name."""
        for username, first_name, last_name in DEMO_CLIENTS:
            reset_user(username, first_name, last_name)
            self.stdout.write(f"Client {username} ready (password: {DEMO_PASSWORD}).")

    def create_staff(self):
        """Create the operator and the maintenance user, each in its role's group."""
        for username, role in DEMO_STAFF:
            user = reset_user(username)
            # get_or_create: flush empties the groups and migrate does not rebuild them.
            group, _created = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            self.stdout.write(f"Staff {username} ({role}) ready (password: {DEMO_PASSWORD}).")

    def create_admin(self):
        """Create the administrator, who is the superuser."""
        user = reset_user(DEMO_ADMIN)
        user.is_staff = True
        user.is_superuser = True
        user.save()
        self.stdout.write(f"Admin {DEMO_ADMIN} ready (password: {DEMO_PASSWORD}).")

    def create_rentals(self):
        """Create a future rental, a reservation to pick up and a rented unit to return."""
        users = get_user_model().objects
        operator = users.get(username="op01")
        c01 = users.get(username="c01")
        c02 = users.get(username="c02")
        today = timezone.localdate()
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        # EQ-01 is rented in November but stays available before that (ENT-10).
        self.create_rental_once(
            c01, "EQ-01", local_moment(date(2026, 11, 1), 18), local_moment(date(2026, 11, 5), 9)
        )
        # Reservation to hand over (pickup): the dates follow the day the seed runs,
        # because a reservation not picked up expires at 12:00 of the next day.
        self.create_rental_once(
            c01, "EQ-02", local_moment(tomorrow, 18), local_moment(tomorrow + timedelta(days=1), 9)
        )
        # Rented unit to receive back (return): picked up yesterday, due tomorrow at 09:00.
        rented = self.create_rental_once(
            c02, "EQ-03", local_moment(yesterday, 18), local_moment(tomorrow, 9)
        )
        if rented is not None:
            Rental.objects.filter(pk=rented.pk).update(
                picked_up_at=local_moment(yesterday, 18) + timedelta(minutes=30),
                handed_over_by=operator,
                registered_by=operator,
            )

    def create_rental_once(self, client, inventory_id, start, end):
        """Create the rental unless the client already has one for that unit; return it or None."""
        equipment = Equipment.objects.get(inventory_id=inventory_id)
        if Rental.objects.filter(client=client, equipment=equipment).exists():
            self.stdout.write(f"Rental of {inventory_id} for {client.username} already exists.")
            return None
        try:
            rental = create_rental(client, equipment, start, end)
        except OperationRejectedError as error:
            self.stdout.write(self.style.WARNING(f"Rental of {inventory_id} skipped: {error}"))
            return None
        self.stdout.write(f"Rental of {inventory_id} for {client.username} ready.")
        return rental


def local_moment(day, hour):
    """Return the given day at the given hour in local time (America/La_Paz)."""
    return timezone.make_aware(datetime.combine(day, time(hour, 0)))


def reset_user(username, first_name="", last_name=""):
    """Create the user if missing, set the demo password and name, and return it."""
    user, _created = get_user_model().objects.get_or_create(username=username)
    user.first_name = first_name
    user.last_name = last_name
    # set_password stores a hash, never the plain text.
    user.set_password(DEMO_PASSWORD)
    user.save()
    return user