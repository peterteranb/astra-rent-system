"""Comando seed_demo: borra todo y deja la base con la demo, con fechas relativas a hoy.

Solo con DEBUG=True: borra usuarios, equipos, rentas, deudas e historial y vacía logs/negocio.log.
Con --equipos N completa el catálogo hasta N equipos con mesas y sillas (RC-01: probar con 1000).
"""
import itertools
from datetime import datetime, time, timedelta
from decimal import Decimal
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.test.utils import override_settings
from django.utils import timezone

from accounts.models import Role
from accounts.roles import ADMINISTRATOR, CLIENT, MAINTENANCE, OPERATOR
from rentals import rules
from rentals.models import Debt, Equipment, EquipmentStatus, Rental, StatusChange
from rentals.services.events import log_event
from rentals.statuses import DebtReason, PaymentMethod
from rentals.use_cases.debts import charge_debt, pay_debt
from rentals.use_cases.equipment_status import change_status
from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import create_rental, log_rental_created
from rentals.use_cases.reservation_changes import cancel_rental

# El nombre del módulo empieza con un número: se importa así para usar su create_roles con get_or_create.
ROLES_MIGRATION = import_module("accounts.migrations.0002_roles")

# La demo no manda correos: sus clientes tienen direcciones inventadas.
NO_EMAIL = {"default": {"BACKEND": "django.core.mail.backends.dummy.EmailBackend"}}

# Cumple las reglas de contraseña: 8 caracteres, una mayúscula y un número.
DEMO_PASSWORD = "Demo1234"

# (usuario, nombre, apellido, correo, teléfono, rol)
DEMO_USERS = [
    ("cl01", "Carla", "Mendoza", "carla.mendoza@correo.com", "71000001", CLIENT),
    ("cl02", "Diego", "Rojas", "diego.rojas@correo.com", "71000002", CLIENT),
    ("op01", "Olga", "Pérez", "olga.perez@sergiocorp.com", "71000003", OPERATOR),
    ("mt01", "Mario", "Torres", "mario.torres@sergiocorp.com", "71000004", MAINTENANCE),
    ("ad01", "Ana", "Díaz", "ana.diaz@sergiocorp.com", "71000005", ADMINISTRATOR),
    ("cl03", "Lucía", "Quispe", "lucia.quispe@correo.com", "71000006", CLIENT),
    ("cl04", "Jorge", "Mamani", "jorge.mamani@correo.com", "71000007", CLIENT),
    ("cl05", "Ximena", "Choque", "ximena.choque@correo.com", "71000008", CLIENT),
    ("cl06", "Rodrigo", "Flores", "rodrigo.flores@correo.com", "71000009", CLIENT),
    ("cl07", "Paola", "Vargas", "paola.vargas@correo.com", "71000010", CLIENT),
    ("cl08", "Marcelo", "Gutiérrez", "marcelo.gutierrez@correo.com", "71000011", CLIENT),
    ("cl09", "Wilma", "Condori", "wilma.condori@correo.com", "71000012", CLIENT),
    ("cl10", "Fernando", "Arce", "fernando.arce@correo.com", "71000013", CLIENT),
]

# (prefijo, nombre, fabricante, año, valor en Bs, cantidad). Del valor salen el precio por día (5 %) y los cargos por daño.
# ENT-96: un combo es un equipo más, con su código y su valor; no descuenta las sillas y mesas sueltas.
CATALOG = [
    ("MES", "Mesa plegable 1,80 m", "DURAPLAST", 2024, "400.00", 6),
    ("MES", "Mesa redonda para 10 personas", "MADEANDINA", 2023, "650.00", 3),
    ("MES", "Mesa alta de cóctel", "METALSUR", 2025, "350.00", 3),
    ("SIL", "Silla plegable blanca", "DURAPLAST", 2024, "80.00", 8),
    ("SIL", "Silla Tiffany dorada", "RESINART", 2025, "150.00", 5),
    ("SIL", "Silla de madera", "MADEANDINA", 2023, "120.00", 3),
    ("CMB", "Combo 6 sillas y 1 mesa", "SERGIOCORP", 2025, "3000.00", 1),
    ("CMB", "Combo 10 sillas Tiffany y 1 mesa redonda", "SERGIOCORP", 2025, "2150.00", 1),
]

DEMO_PURPOSE = {
    "MES-00001": "CU-08: reserva pagada de cl01 para hoy, lista para entregar",
    "MES-00002": "CU-04: pedir hoy+8 se rechaza; la reserva cancelada no ocupa",
    "MES-00003": "CU-08: reserva de hoy con pago pendiente: cobrar o cancelar",
    "MES-00004": "CU-05: libre para la renta en tienda",
    "MES-00005": "CU-06 y CU-07: cl01 la modifica o la cancela (faltan más de 24 h)",
    "SIL-00001": "CU-09: venció ayer; al devolverla se crea la deuda por atraso",
    "SIL-00002": "CU-15: renta vencida hace 2 días, en el panel",
    "SIL-00003": "CU-10: en revisión; reparación con «Cobrar el daño» cobra 16 Bs a cl02",
    "SIL-00004": "CU-10: en reparación, pasa a disponible o baja",
    "SIL-00005": "CU-13: una baja ya no cambia",
    "SIL-00006": "CU-11: volvió con atraso; deuda pendiente de cl02",
    "SIL-00007": "CU-09: rentada, se devuelve a tiempo",
    "CMB-00001": "Combo: un equipo más, 150 Bs por día (ENT-96)",
}

# Pasadas, a mano (D-31), días desde hoy: (cliente, equipo, recojo, devolución, vuelta (día, hora, min) o None, nota).
PAST_RENTALS = [
    ("cl01", "MES-00006", -14, -12, (-12, 8, 0), "Llegó bien"),
    ("cl03", "MES-00007", -20, -18, (-18, 8, 15), "Llegó limpia y completa"),
    ("cl03", "SIL-00009", -20, -18, (-18, 8, 40), "Sin observaciones"),
    ("cl04", "MES-00010", -15, -14, (-14, 10, 30), "Llegó bien, en tolerancia"),
    ("cl05", "CMB-00001", -12, -10, (-10, 11, 50), "Completo"),
    ("cl06", "MES-00008", -10, -8, (-7, 15, 0), "Volvió un día después, por la tarde"),
    ("cl07", "SIL-00014", -9, -7, (-7, 13, 0), "Volvió después del mediodía"),
    ("cl08", "CMB-00002", -8, -5, (-5, 8, 55), "Completo"),
    ("cl09", "SIL-00010", -6, -4, (-3, 9, 30), "Volvió al día siguiente"),
    ("cl10", "MES-00011", -5, -3, (-3, 7, 45), "Sin observaciones"),
    ("cl05", "SIL-00013", -2, 1, None, ""),
]

# Equipos cuya deuda por atraso ya se cobró; las demás deudas quedan pendientes.
PAID_LATE_DEBTS = {"MES-00008", "SIL-00010"}

# Hoy y los próximos días: (cliente, equipo, recojo, devolución, pago: "qr", "pendiente" en línea o "tienda").
UPCOMING_RENTALS = [
    ("cl03", "MES-00009", 0, 1, "tienda"),
    ("cl04", "SIL-00011", 0, 2, "qr"),
    ("cl05", "MES-00012", 1, 2, "qr"),
    ("cl06", "CMB-00001", 2, 4, "qr"),
    ("cl08", "SIL-00015", 3, 4, "pendiente"),
    ("cl09", "MES-00007", 4, 6, "tienda"),
    ("cl10", "SIL-00012", 6, 7, "qr"),
]


class Command(BaseCommand):
    """Vacía el log de negocio, borra todos los datos y crea la demo."""

    help = (
        "SOLO PARA LA DEMO: vacía logs/negocio.log, borra usuarios, equipos, rentas, deudas e historial "
        "y crea la demo."
    )

    def add_arguments(self, parser):
        """Agrega --equipos N: cuántos equipos tiene la base en total al terminar."""
        parser.add_argument(
            "--equipos", type=int, default=None, help="Total de equipos; los que pasan del catálogo son mesas y sillas."
        )

    def handle(self, *args, **options):
        """Empieza el log de cero y crea toda la demo en una sola transacción: o queda completa o no cambia nada."""
        # ENT-97: nunca se borra nada; este comando sí borra, así que no corre en producción.
        if not settings.DEBUG:
            raise CommandError("seed_demo borra los datos de la demo; solo se usa con DEBUG=True")
        extra = extra_count(options["equipos"])
        start_business_log()
        # Sin hilo: un correo en segundo plano podría salir cuando override_settings ya devolvió Gmail.
        with override_settings(MAILERS=NO_EMAIL, EMAIL_IN_BACKGROUND=False), transaction.atomic():
            delete_everything()
            ROLES_MIGRATION.create_roles(apps, schema_editor=None)
            users = create_users()
            equipment = create_equipment(extra)
            create_scenario(users, equipment)
            create_upcoming_rentals(users, equipment)
            create_past_rentals(users, equipment)
        self.print_summary()

    def print_summary(self):
        """Imprime los usuarios, una tabla con los equipos de cada caso de uso y cuánto hay de cada cosa."""
        usernames = ", ".join(username for username, *_ in DEMO_USERS)
        self.stdout.write(f"Usuarios (clave {DEMO_PASSWORD}): {usernames}")
        self.stdout.write(f"{'Equipo':<10} {'Estado':<14} {'Rentas':<44} Para qué sirve")
        for unit in Equipment.objects.filter(inventory_id__in=DEMO_PURPOSE).prefetch_related("rentals__client"):
            rentals = ", ".join(
                f"{rental.status.label} de {rental.client.username}" for rental in unit.rentals.all()
            )
            self.stdout.write(
                f"{unit.inventory_id:<10} {unit.get_status_display():<14} "
                f"{rentals or '-':<44} {DEMO_PURPOSE[unit.inventory_id]}"
            )
        debts = Debt.objects.all()
        self.stdout.write(
            f"En total: {Equipment.objects.count()} equipos, {Rental.objects.count()} rentas y "
            f"{debts.count()} deudas ({debts.pending().count()} pendientes)."
        )
        self.stdout.write(self.style.SUCCESS("Demo lista."))


def start_business_log():
    """Vacía logs/negocio.log y escribe DEMO_RESET como su primera línea."""
    # Sin esto el archivo crece sin límite y en la presentación se mezclan las pruebas viejas con la demo.
    settings.BUSINESS_LOG_FILE.write_text("", encoding="utf-8")
    log_event("DEMO_RESET")


def delete_everything():
    """Borra deudas, rentas, historial, equipos y usuarios."""
    # PROTECT: se borra de las hojas hacia la raíz; los usuarios van al final porque todo los nombra.
    Debt.objects.all().delete()
    Rental.objects.all().delete()
    StatusChange.objects.all().delete()
    Equipment.objects.all().delete()
    get_user_model().objects.all().delete()


def create_users():
    """Crea los usuarios de la demo, todos con la misma clave, y los devuelve por nombre de usuario."""
    # Un solo hash para todos: cada uno tarda unos 0,3 s.
    password = make_password(DEMO_PASSWORD)
    return {
        username: get_user_model().objects.create(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            role=Role.objects.get(code=role_code),
            password=password,
        )
        for username, first_name, last_name, email, phone, role_code in DEMO_USERS
    }


def extra_count(total):
    """Devuelve cuántos equipos agregar al catálogo para llegar a total; 0 sin --equipos. Lanza CommandError si no alcanza."""
    catalog_size = sum(row[-1] for row in CATALOG)
    if total is None:
        return 0
    if total < catalog_size:
        raise CommandError(f"--equipos debe ser al menos {catalog_size}: la demo usa {catalog_size} equipos.")
    return total - catalog_size


def create_equipment(extra):
    """Crea los equipos del catálogo y extra mesas y sillas más, disponibles, y los devuelve por código."""
    catalog = (row[:5] for row in CATALOG for _ in range(row[-1]))
    loose_models = [row[:5] for row in CATALOG if row[0] != "CMB"]
    extra_models = itertools.islice(itertools.cycle(loose_models), extra)
    Equipment.objects.bulk_create(build_equipment(itertools.chain(catalog, extra_models)))
    return Equipment.objects.in_bulk(field_name="inventory_id")


def build_equipment(models):
    """Arma un equipo sin guardar por modelo: el código sigue la cuenta de su prefijo y la serie es FABRICANTE-AÑO-NÚMERO."""
    next_number = {prefix: itertools.count(1) for prefix, *_ in CATALOG}
    for position, (prefix, name, maker, year, value) in enumerate(models, start=1):
        yield Equipment(
            inventory_id=f"{prefix}-{next(next_number[prefix]):05d}",
            serial_number=f"{maker}-{year}-{position:05d}",
            name=name,
            value=Decimal(value),
        )


def create_scenario(users, equipment):
    """Crea las rentas, los cambios de estado y la deuda que usa cada caso de uso de la demo (DEMO_PURPOSE).

    Las rentas de cl02 van primero que su deuda: con ella ya no podría rentar (ENT-77).
    """
    cl01, cl02, op01, mt01 = users["cl01"], users["cl02"], users["op01"], users["mt01"]

    pay_with_qr(create_rental(cl01, equipment["MES-00001"], at(0, 18), at(1, 9)), approved=True)

    # La cancelada se crea antes en las mismas fechas: muestra que libera el equipo.
    cancel_rental(create_rental(cl01, equipment["MES-00002"], at(7, 18), at(9, 9)), op01)
    pay_with_qr(create_rental(cl02, equipment["MES-00002"], at(7, 18), at(9, 9)), approved=True)

    pay_with_qr(create_rental(cl02, equipment["MES-00003"], at(0, 18), at(1, 9)), approved=False)
    pay_with_qr(create_rental(cl01, equipment["MES-00005"], at(10, 18), at(12, 9)), approved=True)

    picked_up_in_store(cl01, equipment["SIL-00001"], op01, at(-3, 18), at(-1, 9))
    picked_up_in_store(cl01, equipment["SIL-00002"], op01, at(-4, 18), at(-2, 9))
    picked_up_in_store(cl02, equipment["SIL-00007"], op01, at(-1, 18), at(1, 9))

    on_time = picked_up_in_store(cl02, equipment["SIL-00003"], op01, at(-3, 18), at(-1, 9))
    returned_in_past(on_time, op01, at(-1, 8, 30), "Una pata floja")

    change_status(equipment["SIL-00004"], EquipmentStatus.IN_REPAIR, mt01, "Tapiz roto")
    change_status(equipment["SIL-00005"], EquipmentStatus.RETIRED, mt01, "Estructura partida")

    late = picked_up_in_store(cl02, equipment["SIL-00006"], op01, at(-6, 18), at(-4, 9))
    returned_in_past(late, op01, at(-2, 12, 30), "Volvió dos días tarde")
    reviewed_in_past(equipment["SIL-00006"], mt01, at(-2, 15))


def create_upcoming_rentals(users, equipment):
    """Crea las rentas de hoy y las reservas de los próximos días con create_rental, como en la web."""
    for username, code, start_day, end_day, payment in UPCOMING_RENTALS:
        operator = users["op01"] if payment == "tienda" else None
        rental = create_rental(users[username], equipment[code], at(start_day, 18), at(end_day, 9), operator)
        if operator is None:
            pay_with_qr(rental, approved=payment == "qr")


def create_past_rentals(users, equipment):
    """Crea las rentas de días anteriores: devueltas a tiempo, en tolerancia o con atraso, y una que sigue afuera."""
    op01, mt01 = users["op01"], users["mt01"]
    for username, code, start_day, end_day, returned, note in PAST_RENTALS:
        rental = picked_up_in_store(users[username], equipment[code], op01, at(start_day, 18), at(end_day, 9))
        if returned is None:
            continue
        returned_at = at(*returned)
        debt = returned_in_past(rental, op01, returned_at, note)
        reviewed_in_past(equipment[code], mt01, returned_at + timedelta(hours=2))
        if code in PAID_LATE_DEBTS:
            pay_debt(debt, op01)


def picked_up_in_store(client, unit, operator, start, end):
    """Guarda una renta en tienda ya pagada y recogida en start, con el mismo log que create_rental.

    Se arma a mano porque create_rental rechaza un recojo pasado (ENT-94, D-31).
    """
    rental = Rental.objects.create(
        client=client,
        equipment=unit,
        start_datetime=start,
        end_datetime=end,
        daily_price=rules.daily_price_for(unit.value),
        paid_at=start,
        payment_method=PaymentMethod.CASH,
        registered_by=operator,
        picked_up_at=start,
        handed_over_by=operator,
    )
    log_rental_created(rental)
    return rental


def returned_in_past(rental, operator, moment, note):
    """Pone una devolución en el pasado, manda el equipo a revisión con esa hora y cobra el atraso, si hubo."""
    Rental.objects.filter(pk=rental.pk).update(returned_at=moment, received_by=operator, return_note=note)
    rental.refresh_from_db()
    change = change_status(rental.equipment, EquipmentStatus.IN_REVIEW, operator, note)
    StatusChange.objects.filter(pk=change.pk).update(changed_at=moment)
    if not rental.late_days:
        return None
    return charge_debt(rental, DebtReason.LATE_RETURN, rental.late_charge, operator)


def reviewed_in_past(unit, maintenance, moment):
    """Deja el equipo «Disponible» después de su revisión, con el historial a esa hora."""
    change = change_status(unit, EquipmentStatus.AVAILABLE, maintenance, "Revisado, en buen estado")
    StatusChange.objects.filter(pk=change.pk).update(changed_at=moment)


def at(days, hour, minute=0):
    """Devuelve el día que cae days después de hoy, a esa hora de La Paz."""
    day = timezone.localdate() + timedelta(days=days)
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))
