"""Datos de prueba compartidos (fixtures) con los mismos nombres de la demo: cl01, cl02, op01, mt01, ad01 y los equipos.

Una prueba pide un dato escribiendo su nombre como parámetro, por ejemplo test_algo(cl01, eq01).
Las fixtures que reciben db escriben en la base de pruebas, que se deshace después de cada prueba.
"""
import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from rentals.models import Equipment, EquipmentStatus
from rentals.roles import MAINTENANCE, OPERATOR

DEMO_PASSWORD = "demo1234"


def create_user(username, first_name, last_name, group=None):
    """Crea un usuario de prueba con la clave de la demo y, si se pide, lo pone en el grupo de su rol."""
    user = get_user_model().objects.create_user(
        username, password=DEMO_PASSWORD, first_name=first_name, last_name=last_name
    )
    if group:
        user.groups.add(Group.objects.get(name=group))
    return user


@pytest.fixture
def cl01(db):
    """Cliente Carla Mendoza."""
    return create_user("cl01", "Carla", "Mendoza")


@pytest.fixture
def cl02(db):
    """Cliente Diego Rojas, el que el operador busca por «rojas»."""
    return create_user("cl02", "Diego", "Rojas")


@pytest.fixture
def op01(db):
    """Operadora Olga Pérez; el grupo lo crea la migración 0004."""
    return create_user("op01", "Olga", "Pérez", OPERATOR)


@pytest.fixture
def mt01(db):
    """Mario Torres, de mantenimiento."""
    return create_user("mt01", "Mario", "Torres", MAINTENANCE)


@pytest.fixture
def ad01(db):
    """Ana Díaz, administradora: el superusuario (ENT-44)."""
    return get_user_model().objects.create_superuser("ad01", password=DEMO_PASSWORD)


@pytest.fixture
def eq01(db):
    """EQ-01: mesa plegable disponible."""
    return Equipment.objects.create(
        inventory_id="EQ-01", serial_number="SN-T-001", description="Mesa plegable 1,80 m"
    )


@pytest.fixture
def eq02(db):
    """EQ-02: otra mesa plegable igual, disponible."""
    return Equipment.objects.create(
        inventory_id="EQ-02", serial_number="SN-T-002", description="Mesa plegable 1,80 m"
    )


@pytest.fixture
def eq03_en_revision(db):
    """EQ-03: mesa redonda devuelta que espera a mantenimiento."""
    return Equipment.objects.create(
        inventory_id="EQ-03",
        serial_number="SN-T-003",
        description="Mesa redonda 1,20 m",
        status=EquipmentStatus.IN_REVIEW,
    )
