"""Comando stress_test: muchos clientes rentan a la vez con los mismos casos de uso que la web (RF-01, ENT-21).

SOLO PARA DESARROLLO (DEBUG=True): crea sus clientes y equipos, los usa y al final los borra.
"""
import threading
import time
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.test.utils import override_settings
from django.utils import timezone

from accounts.registration import SignUpData, register_client
from accounts.roles import ADMINISTRATOR
from rentals import rules
from rentals.errors import EquipmentNotAvailableError
from rentals.models import Equipment, Rental, StatusChange
from rentals.use_cases.inventory import register_equipment
from rentals.use_cases.renting import create_rental

# Los clientes de la prueba tienen correos inventados: no se manda ninguno.
NO_EMAIL = {"default": {"BACKEND": "django.core.mail.backends.dummy.EmailBackend"}}
PASSWORD = "Montaña2026"
# Marcas de lo que crea la prueba, para borrarlo aunque una corrida anterior se haya cortado.
CLIENT_PREFIX = "carga"
SERIAL_PREFIX = "SN-CARGA-"
SAVED = "guardada"
BUSY = "ocupado"


class Command(BaseCommand):
    """Prueba que N rentas a la vez del mismo equipo guardan una sola y que N equipos distintos se rentan todos."""

    help = "SOLO PARA DESARROLLO: N hilos rentan a la vez el mismo equipo y después N equipos distintos."

    def add_arguments(self, parser):
        """Agrega --rentas N: cuántos hilos rentan a la vez."""
        parser.add_argument("--rentas", type=int, default=50, help="Cuántos clientes rentan a la vez.")

    def handle(self, *args, **options):
        """Prepara los datos, corre los dos escenarios, imprime el resumen y siempre limpia lo que creó."""
        # Crea y borra datos: igual que seed_demo, nunca corre en producción (ENT-97).
        if not settings.DEBUG:
            raise CommandError("stress_test crea y borra datos de prueba; solo se usa con DEBUG=True")
        count = options["rentas"]
        if count < 2:
            raise CommandError("--rentas debe ser al menos 2: hacen falta dos clientes que choquen.")
        admin = administrator()
        clean_up()
        with override_settings(MAILERS=NO_EMAIL):
            try:
                clients = create_clients(count)
                equipment = create_equipment(count, admin)
                same = run_scenario(clients, [equipment[0]] * count, days_ahead=7)
                # Otro periodo: en el primero ya quedó rentado el equipo 0.
                different = run_scenario(clients, equipment, days_ahead=10)
            finally:
                clean_up()
        self.print_summary(count, equipment_code(0), same, different)
        if same.saved != 1 or same.busy != count - 1 or different.saved != count:
            raise CommandError("La prueba de carga no dio lo esperado.")
        self.stdout.write(self.style.SUCCESS("Prueba de carga correcta."))

    def print_summary(self, count, code, same, different):
        """Imprime cuántas rentas se guardaron, cuántas se rechazaron y cuánto tardó cada escenario."""
        self.stdout.write(f"1) {count} clientes rentan {code} a la vez en el mismo periodo:")
        self.stdout.write(f"   guardadas {same.saved}, rechazadas por «ocupado» {same.busy}, otros errores {same.other}, {same.seconds:.2f} s")
        self.stdout.write(f"2) {count} clientes rentan {count} equipos distintos a la vez:")
        self.stdout.write(f"   guardadas {different.saved}, rechazadas {different.busy + different.other}, {different.seconds:.2f} s")


@dataclass(frozen=True)
class ScenarioResult:
    """Lo que pasó en un escenario: cuántas rentas se guardaron, cuántas chocaron, otros errores y el tiempo."""

    saved: int
    busy: int
    other: int
    seconds: float


def scenario_result(outcomes, seconds):
    """Cuenta lo que anotó cada hilo."""
    saved, busy = outcomes.count(SAVED), outcomes.count(BUSY)
    return ScenarioResult(saved, busy, len(outcomes) - saved - busy, seconds)


def administrator():
    """Devuelve un administrador para registrar los equipos; lanza CommandError si no hay ninguno."""
    admin = get_user_model().objects.filter(role__code=ADMINISTRATOR, is_active=True).first()
    if admin is None:
        raise CommandError("No hay un administrador activo: corre antes python manage.py seed_demo.")
    return admin


def create_clients(count):
    """Registra count clientes con el mismo caso de uso del registro web (CU-01)."""
    return [
        register_client(
            SignUpData(
                "Carga", f"Cliente {number}", f"carga{number}@correo.com", f"7990{number:04d}",
                f"{CLIENT_PREFIX}{number:04d}", PASSWORD, PASSWORD,
            )
        )
        for number in range(count)
    ]


def equipment_code(number):
    """Código de la mesa número number de la prueba: MES-90000, MES-90001…"""
    return f"MES-9{number:04d}"


def create_equipment(count, admin):
    """Registra count mesas con el mismo caso de uso del administrador (CU-12)."""
    return [
        register_equipment(
            equipment_code(number), f"{SERIAL_PREFIX}{number:04d}", "Mesa plegable 1,80 m", Decimal("400.00"), admin
        )
        for number in range(count)
    ]


def run_scenario(clients, equipment, days_ahead):
    """Lanza un hilo por cliente que renta su equipo en el mismo periodo, todos a la vez, y devuelve el resultado."""
    start, end = rental_period(days_ahead)
    outcomes = []
    # La barrera suelta a todos los hilos juntos: así sí compiten por la misma fila.
    barrier = threading.Barrier(len(clients))
    threads = [
        threading.Thread(target=rent, args=(client, unit, start, end, barrier, outcomes))
        for client, unit in zip(clients, equipment)
    ]
    began = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return scenario_result(outcomes, time.perf_counter() - began)


def rental_period(days_ahead):
    """Una noche de renta: de dentro de days_ahead días a las 18:00 al día siguiente a las 09:00."""
    day = timezone.localdate() + timedelta(days=days_ahead)
    return (
        rules.combine_local(day, rules.EARLIEST_PICKUP_TIME),
        rules.combine_local(day + timedelta(days=1), rules.LATEST_RETURN_TIME),
    )


def rent(client, unit, start, end, barrier, outcomes):
    """Espera a los demás hilos, renta en línea con create_rental y anota si se guardó, chocó u otro error."""
    try:
        barrier.wait()
        create_rental(client, unit, start, end)
        outcomes.append(SAVED)
    except EquipmentNotAvailableError:
        outcomes.append(BUSY)
    # Un error que escapa de un hilo se pierde: se anota para que el resumen lo cuente.
    except Exception as error:  # noqa: BLE001
        outcomes.append(type(error).__name__)
    finally:
        # Cada hilo abre su propia conexión a PostgreSQL; si no se cierra, queda abierta.
        connection.close()


def clean_up():
    """Borra las rentas, el historial, los equipos y los clientes que creó la prueba, por sus marcas."""
    clients = get_user_model().objects.filter(username__regex=rf"^{CLIENT_PREFIX}\d{{4}}$")
    equipment = Equipment.objects.filter(serial_number__startswith=SERIAL_PREFIX)
    # PROTECT: se borra de las hojas hacia la raíz.
    Rental.objects.filter(client__in=clients).delete()
    StatusChange.objects.filter(equipment__in=equipment).delete()
    equipment.delete()
    clients.delete()
