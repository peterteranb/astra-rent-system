"""Comando seed_demo: deja la base con el escenario de la demo del MVP, con fechas relativas a hoy.

SOLO PARA LA DEMO: borra todas las rentas y todo el historial y los vuelve a crear,
así cada vez que se corre el escenario queda igual.
"""
from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rentals.history import change_status
from rentals.models import Equipment, EquipmentStatus, Rental, StatusChange
from rentals.renting import cancel_rental, create_rental
from accounts.models import Role
from rentals.roles import ADMINISTRATOR, CLIENT, MAINTENANCE, OPERATOR

# Cumple las reglas de contraseña: 8 caracteres, una mayúscula y un número.
DEMO_PASSWORD = "Demo1234"

DEMO_USERS = [
    ("cl01", "Carla", "Mendoza", "carla.mendoza@correo.com", "71000001", CLIENT),
    ("cl02", "Diego", "Rojas", "diego.rojas@correo.com", "71000002", CLIENT),
    ("op01", "Olga", "Pérez", "olga.perez@sergiocorp.com", "71000003", OPERATOR),
    ("mt01", "Mario", "Torres", "mario.torres@sergiocorp.com", "71000004", MAINTENANCE),
    ("ad01", "Ana", "Díaz", "ana.diaz@sergiocorp.com", "71000005", ADMINISTRATOR),
]

# EQ-06 y EQ-07 empiezan «En revisión» para que su única fila de historial
# sea la decisión de mantenimiento.
DEMO_EQUIPMENT = [
    ("EQ-01", "SN-T-001", "Mesa plegable 1,80 m", EquipmentStatus.AVAILABLE),
    ("EQ-02", "SN-T-002", "Mesa plegable 1,80 m", EquipmentStatus.AVAILABLE),
    ("EQ-03", "SN-T-003", "Mesa redonda 1,20 m", EquipmentStatus.AVAILABLE),
    ("EQ-04", "SN-C-001", "Silla plegable blanca", EquipmentStatus.AVAILABLE),
    ("EQ-05", "SN-C-002", "Silla plegable blanca", EquipmentStatus.AVAILABLE),
    ("EQ-06", "SN-C-003", "Silla Tiffany dorada", EquipmentStatus.IN_REVIEW),
    ("EQ-07", "SN-C-004", "Silla Tiffany dorada", EquipmentStatus.IN_REVIEW),
    ("EQ-08", "SN-T-004", "Mesa redonda 1,20 m", EquipmentStatus.AVAILABLE),
]

DEMO_PURPOSE = {
    "EQ-01": "CU-03: entregar la reserva de hoy",
    "EQ-02": "CU-01: pedir hoy+8 se rechaza; la cancelada no ocupa",
    "EQ-03": "CU-04: devolver «A tiempo»",
    "EQ-04": "CU-04: devolver después de las 12:00, «Se cobra un día más»",
    "EQ-05": "CU-05: revisar y dejar disponible",
    "EQ-06": "CU-05: en reparación, pasa a disponible o baja",
    "EQ-07": "CU-07: una baja ya no cambia",
    "EQ-08": "CU-02: libre para la renta en tienda",
}


class Command(BaseCommand):
    """Borra las rentas y el historial y crea el escenario de la demo."""

    help = "SOLO PARA LA DEMO: borra todas las rentas y el historial y crea el escenario del MVP."

    def handle(self, *args, **options):
        """Crea todo el escenario en una sola transacción: o queda completo o no cambia nada."""
        with transaction.atomic():
            Rental.objects.all().delete()
            StatusChange.objects.all().delete()
            users = create_users()
            reset_equipment()
            create_scenario(users)
        self.print_summary()

    def print_summary(self):
        """Imprime una tabla corta: equipo, estado, rentas y para qué sirve en la demo."""
        self.stdout.write(f"Usuarios: cl01, cl02, op01, mt01, ad01 (clave: {DEMO_PASSWORD})")
        self.stdout.write(f"{'Equipo':<7} {'Estado':<14} {'Rentas':<40} Para qué sirve")
        for equipment in Equipment.objects.prefetch_related("rentals__client"):
            rentals = ", ".join(
                f"{rental.status.label} de {rental.client.username}"
                for rental in equipment.rentals.all()
            )
            self.stdout.write(
                f"{equipment.inventory_id:<7} {equipment.get_status_display():<14} "
                f"{rentals or '-':<40} {DEMO_PURPOSE.get(equipment.inventory_id, '')}"
            )
        self.stdout.write(self.style.SUCCESS("Escenario de la demo listo."))


def create_users():
    """Crea o reinicia los usuarios de la demo y los devuelve por nombre de usuario."""
    return {username: reset_user(username, *data) for username, *data in DEMO_USERS}


def reset_user(username, first_name, last_name, email, phone, role_code):
    """Crea el usuario si falta, le pone sus datos, su rol y la clave de la demo, y lo devuelve."""
    user = get_user_model().objects.filter(username=username).first() or get_user_model()(
        username=username
    )
    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.phone = phone
    user.role = Role.objects.get(code=role_code)
    user.is_active = True
    # set_password guarda un hash, nunca la clave en texto.
    user.set_password(DEMO_PASSWORD)
    user.save()
    return user


def reset_equipment():
    """Crea los equipos de la demo o les devuelve sus datos y su estado inicial."""
    # El estado inicial se pone directo y no con change_status: el historial se borró
    # y un equipo de baja de una corrida anterior ya no podría cambiar.
    for inventory_id, serial_number, description, status in DEMO_EQUIPMENT:
        Equipment.objects.update_or_create(
            inventory_id=inventory_id,
            defaults={"serial_number": serial_number, "description": description, "status": status},
        )


def create_scenario(users):
    """Crea las rentas y los cambios de estado de cada equipo de la demo."""
    equipment = {unit.inventory_id: unit for unit in Equipment.objects.all()}
    cl01, cl02, op01, mt01 = users["cl01"], users["cl02"], users["op01"], users["mt01"]

    create_rental(cl01, equipment["EQ-01"], days_from_today(0, 18), days_from_today(1, 9))

    # La cancelada se crea antes en las mismas fechas: muestra que libera el equipo.
    cancelled = create_rental(cl01, equipment["EQ-02"], days_from_today(7, 18), days_from_today(9, 9))
    cancel_rental(cancelled, op01)
    create_rental(cl02, equipment["EQ-02"], days_from_today(7, 18), days_from_today(9, 9))

    rented = create_rental(cl02, equipment["EQ-03"], days_from_today(-1, 18), days_from_today(1, 9))
    mark_picked_up(rented, op01, days_from_today(-1, 18, 30))

    late = create_rental(cl01, equipment["EQ-04"], days_from_today(-3, 18), days_from_today(0, 9))
    mark_picked_up(late, op01, days_from_today(-3, 18, 30))

    returned = create_rental(cl02, equipment["EQ-05"], days_from_today(-3, 18), days_from_today(-1, 9))
    mark_picked_up(returned, op01, days_from_today(-3, 18, 30))
    mark_returned(returned, op01, days_from_today(-1, 8, 30), "Una pata floja")

    change_status(equipment["EQ-06"], EquipmentStatus.IN_REPAIR, mt01, "Tapiz roto")
    change_status(equipment["EQ-07"], EquipmentStatus.RETIRED, mt01, "Estructura partida")

    create_rental(cl01, equipment["EQ-08"], days_from_today(-3, 18), days_from_today(-2, 9))


def mark_picked_up(rental, operator, moment):
    """Pone un recojo en el pasado; register_pickup usaría la hora de ahora."""
    Rental.objects.filter(pk=rental.pk).update(picked_up_at=moment, handed_over_by=operator)


def mark_returned(rental, operator, moment, note):
    """Pone una devolución en el pasado con su nota y su fila de historial con esa misma hora."""
    Rental.objects.filter(pk=rental.pk).update(
        returned_at=moment, received_by=operator, return_note=note
    )
    change = change_status(rental.equipment, EquipmentStatus.IN_REVIEW, operator, note)
    StatusChange.objects.filter(pk=change.pk).update(changed_at=moment)


def days_from_today(days, hour, minute=0):
    """Devuelve el día que cae days después de hoy, a esa hora de La Paz."""
    day = timezone.localdate() + timedelta(days=days)
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))
