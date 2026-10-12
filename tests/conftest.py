"""Datos de prueba compartidos (fixtures), tomados de los documentos de las Sesiones 6 y 7.

Que es una fixture:
    Es una funcion marcada con @pytest.fixture que PREPARA un dato para las pruebas.
    Una prueba la pide escribiendo su nombre como parametro, por ejemplo:
        def test_algo(c01, eq01): ...
    pytest ve los nombres, ejecuta estas funciones y le pasa el resultado a la prueba.
    Este archivo se llama conftest.py porque pytest lo busca solo: no hace falta importarlo.

Que significa el parametro db:
    Las fixtures que reciben db pueden escribir en la base de pruebas
    (test_astra_rent, que crea y borra pytest-django). Despues de CADA prueba,
    todo lo creado se deshace, asi que ninguna prueba ve datos de otra.
    No se usa seed_demo: cada prueba crea solo lo que necesita.

Nombres de los datos (los mismos de los documentos):
    c01, c02          -> clientes C-01 y C-02
    eq01, eq02        -> dos mesas iguales, disponibles
    eq03_in_review    -> una mesa devuelta que espera a mantenimiento (PRE-RF-04)
    doc_start/doc_end -> el periodo del escenario: 09/10/2026 18:00 a 12/10/2026 09:00
"""
import pytest
from django.contrib.auth import get_user_model

from rentals.models import Equipment, EquipmentStatus
from tests.helpers import local_datetime

# Clave de los clientes de prueba (la misma que usa seed_demo para la demo).
DEMO_PASSWORD = "demo1234"


@pytest.fixture
def doc_start():
    """Recojo del escenario de los documentos: 09/10/2026 18:00, hora de La Paz."""
    return local_datetime(2026, 10, 9, 18, 0)


@pytest.fixture
def doc_end():
    """Devolucion del escenario de los documentos: 12/10/2026 09:00, hora de La Paz."""
    return local_datetime(2026, 10, 12, 9, 0)


@pytest.fixture
def c01(db):
    """Cliente C-01. create_user guarda la clave como hash, igual que el sistema real."""
    return get_user_model().objects.create_user("c01", password=DEMO_PASSWORD)


@pytest.fixture
def c02(db):
    """Cliente C-02, el que llega segundo en el escenario de rechazo."""
    return get_user_model().objects.create_user("c02", password=DEMO_PASSWORD)


@pytest.fixture
def eq01(db):
    """Equipo EQ-01: mesa plegable, disponible."""
    return Equipment.objects.create(
        inventory_id="EQ-01",
        serial_number="SN-T-001",
        description="Mesa plegable 1,80 m",
        status=EquipmentStatus.AVAILABLE,
    )


@pytest.fixture
def eq02(db):
    """Equipo EQ-02: el MISMO modelo que EQ-01 (otra unidad), disponible."""
    return Equipment.objects.create(
        inventory_id="EQ-02",
        serial_number="SN-T-002",
        description="Mesa plegable 1,80 m",
        status=EquipmentStatus.AVAILABLE,
    )


@pytest.fixture
def eq03_in_review(db):
    """Equipo EQ-03: mesa devuelta que esta "en revision" (PRE-RF-04)."""
    return Equipment.objects.create(
        inventory_id="EQ-03",
        serial_number="SN-T-003",
        description="Mesa redonda 1,20 m",
        status=EquipmentStatus.IN_REVIEW,
    )
