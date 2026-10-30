"""Comando seed_demo: deja la base con el escenario de la demo, con fechas relativas a hoy.

SOLO PARA LA DEMO Y EL DESARROLLO (DEBUG=True): vacía logs/negocio.log, borra todas las deudas, rentas,
historial y equipos y los vuelve a crear, así cada vez que se corre el escenario queda igual.
Con --equipos N completa el catálogo hasta N equipos con mesas y sillas generadas (RC-01: probar con 1000).
"""
import itertools
from datetime import datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
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
from rentals.use_cases.history import change_status
from rentals.use_cases.payments import charge_debt, pay_with_qr
from rentals.use_cases.renting import cancel_rental, create_rental, log_rental_created

# La demo no manda correos: sus clientes tienen direcciones inventadas.
NO_EMAIL = {"default": {"BACKEND": "django.core.mail.backends.dummy.EmailBackend"}}

# Cumple las reglas de contraseña: 8 caracteres, una mayúscula y un número.
DEMO_PASSWORD = "Demo1234"

DEMO_USERS = [
    ("cl01", "Carla", "Mendoza", "carla.mendoza@correo.com", "71000001", CLIENT),
    ("cl02", "Diego", "Rojas", "diego.rojas@correo.com", "71000002", CLIENT),
    ("op01", "Olga", "Pérez", "olga.perez@sergiocorp.com", "71000003", OPERATOR),
    ("mt01", "Mario", "Torres", "mario.torres@sergiocorp.com", "71000004", MAINTENANCE),
    ("ad01", "Ana", "Díaz", "ana.diaz@sergiocorp.com", "71000005", ADMINISTRATOR),
]

# Valores de compra en Bs: de ellos salen el precio por día (5 %) y los cargos por daño.
DEMO_MODELS = {
    "MES": [
        ("Mesa plegable 1,80 m", "400.00"),
        ("Mesa plegable 1,80 m", "400.00"),
        ("Mesa redonda 1,20 m", "350.00"),
        ("Mesa redonda 1,20 m", "350.00"),
        ("Mesa rectangular de madera 2,40 m", "650.00"),
        ("Mesa rectangular de madera 2,40 m", "650.00"),
        ("Mesa cóctel alta", "300.00"),
        ("Mesa cóctel alta", "300.00"),
    ],
    "SIL": [
        ("Silla plegable blanca", "80.00"),
        ("Silla plegable blanca", "80.00"),
        ("Silla plegable blanca", "80.00"),
        ("Silla Tiffany dorada", "150.00"),
        ("Silla Tiffany dorada", "150.00"),
        ("Silla Tiffany dorada", "150.00"),
        ("Silla Tiffany blanca", "150.00"),
        ("Silla acolchada negra", "120.00"),
        ("Silla acolchada negra", "120.00"),
        ("Silla acolchada negra", "120.00"),
        ("Silla acolchada negra", "120.00"),
        ("Silla acolchada negra", "120.00"),
    ],
    # ENT-96: un combo es un equipo más, con su código y su valor; no descuenta las sillas y mesas sueltas.
    "CMB": [
        ("Combo 6 sillas y 1 mesa", "3000.00"),
    ],
}

# ENT-07: solo mesas y sillas. Estos pocos modelos se repiten para llenar un catálogo grande.
EXTRA_MODELS = {
    "MES": [
        ("Mesa plegable 1,80 m", "400.00"),
        ("Mesa redonda 1,20 m", "350.00"),
        ("Mesa rectangular de madera 2,40 m", "650.00"),
        ("Mesa cóctel alta", "300.00"),
    ],
    "SIL": [
        ("Silla plegable blanca", "80.00"),
        ("Silla Tiffany dorada", "150.00"),
        ("Silla acolchada negra", "120.00"),
    ],
}

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


class Command(BaseCommand):
    """Vacía el log de negocio, borra las deudas, rentas, historial y equipos y crea el escenario de la demo."""

    help = (
        "SOLO PARA LA DEMO: vacía logs/negocio.log, borra deudas, rentas, historial y equipos "
        "y crea el escenario de la demo."
    )

    def add_arguments(self, parser):
        """Agrega --equipos N: cuántos equipos tiene la base en total al terminar."""
        parser.add_argument(
            "--equipos", type=int, default=None, help="Total de equipos; los que pasan del escenario son mesas y sillas libres."
        )

    def handle(self, *args, **options):
        """Empieza el log de cero y crea todo el escenario en una sola transacción: o queda completo o no cambia nada."""
        # ENT-97: nunca se borra nada; este comando sí borra, así que no corre en producción.
        if not settings.DEBUG:
            raise CommandError("seed_demo borra los datos de la demo; solo se usa con DEBUG=True")
        extra = extra_count(options["equipos"])
        start_business_log()
        # Sin hilo: un correo en segundo plano podría salir cuando override_settings ya devolvió Gmail.
        with override_settings(MAILERS=NO_EMAIL, EMAIL_IN_BACKGROUND=False), transaction.atomic():
            # PROTECT: se borra de las hojas hacia la raíz.
            Debt.objects.all().delete()
            Rental.objects.all().delete()
            StatusChange.objects.all().delete()
            Equipment.objects.all().delete()
            users = create_users()
            equipment = create_equipment()
            create_scenario(users, equipment)
            Equipment.objects.bulk_create(extra_units(extra))
        self.print_summary(extra)

    def print_summary(self, extra):
        """Imprime una tabla corta: equipo, estado, rentas y para qué sirve en la demo; los generados, solo cuántos son."""
        self.stdout.write(f"Usuarios: cl01, cl02, op01, mt01, ad01 (clave: {DEMO_PASSWORD})")
        self.stdout.write(f"{'Equipo':<10} {'Estado':<14} {'Rentas':<44} Para qué sirve")
        scenario_codes = [code for code, _, _ in scenario_models()]
        for unit in Equipment.objects.filter(inventory_id__in=scenario_codes).prefetch_related("rentals__client"):
            rentals = ", ".join(
                f"{rental.status.label} de {rental.client.username}" for rental in unit.rentals.all()
            )
            self.stdout.write(
                f"{unit.inventory_id:<10} {unit.get_status_display():<14} "
                f"{rentals or '-':<44} {DEMO_PURPOSE.get(unit.inventory_id, 'Libre')}"
            )
        if extra:
            self.stdout.write(f"Además: {extra} mesas y sillas libres generadas.")
        self.stdout.write(self.style.SUCCESS("Escenario de la demo listo."))


def start_business_log():
    """Vacía logs/negocio.log y escribe DEMO_RESET como su primera línea."""
    # Sin esto el archivo crece sin límite y en la presentación se mezclan las pruebas viejas con la demo.
    settings.BUSINESS_LOG_FILE.write_text("", encoding="utf-8")
    log_event("DEMO_RESET")


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


def create_equipment():
    """Crea las 8 mesas, las 12 sillas y el combo de la demo, disponibles, y los devuelve por código."""
    return {
        code: Equipment.objects.create(inventory_id=code, serial_number=f"SN-{code}", name=name, value=Decimal(value))
        for code, name, value in scenario_models()
    }


def scenario_models():
    """Genera el código, el nombre y el valor de cada equipo del escenario: MES-00001… SIL-00001… CMB-00001."""
    for prefix, models in DEMO_MODELS.items():
        for number, (name, value) in enumerate(models, start=1):
            yield f"{prefix}-{number:05d}", name, value


def extra_count(total):
    """Devuelve cuántos equipos generar para llegar a total; 0 sin --equipos. Lanza CommandError si no alcanza para la demo."""
    scenario_size = len(list(scenario_models()))
    if total is None:
        return 0
    if total < scenario_size:
        raise CommandError(f"--equipos debe ser al menos {scenario_size}: el escenario de la demo usa {scenario_size} equipos.")
    return total - scenario_size


def extra_units(count):
    """Genera count equipos sin guardar, alternando mesa y silla, con códigos que siguen a los de la demo."""
    numbers = {prefix: itertools.count(len(DEMO_MODELS[prefix]) + 1) for prefix in EXTRA_MODELS}
    for prefix in itertools.islice(itertools.cycle(EXTRA_MODELS), count):
        number = next(numbers[prefix])
        name, value = EXTRA_MODELS[prefix][number % len(EXTRA_MODELS[prefix])]
        code = f"{prefix}-{number:05d}"
        yield Equipment(inventory_id=code, serial_number=f"SN-{code}", name=name, value=Decimal(value))


def create_scenario(users, equipment):
    """Crea las rentas, los cambios de estado y la deuda de la demo.

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
    change_status(equipment["SIL-00006"], EquipmentStatus.AVAILABLE, mt01, "Revisada, en buen estado")
    late.refresh_from_db()
    charge_debt(late, DebtReason.LATE_RETURN, late.late_charge, op01)


def picked_up_in_store(client, unit, operator, start, end):
    """Guarda una renta en tienda ya pagada y recogida en start, con el mismo log que create_rental.

    Se arma a mano porque create_rental rechaza un recojo pasado (ENT-94) y la demo necesita rentas de días anteriores.
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
    """Pone una devolución en el pasado con su nota y su fila de historial con esa misma hora."""
    Rental.objects.filter(pk=rental.pk).update(
        returned_at=moment, received_by=operator, return_note=note
    )
    change = change_status(rental.equipment, EquipmentStatus.IN_REVIEW, operator, note)
    StatusChange.objects.filter(pk=change.pk).update(changed_at=moment)


def at(days, hour, minute=0):
    """Devuelve el día que cae days después de hoy, a esa hora de La Paz."""
    day = timezone.localdate() + timedelta(days=days)
    return timezone.make_aware(datetime.combine(day, time(hour, minute)))
