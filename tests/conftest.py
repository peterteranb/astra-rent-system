"""Datos de prueba compartidos (fixtures) con los mismos nombres de la demo: cl01, cl02, op01, mt01, ad01 y los equipos.

Una prueba pide un dato escribiendo su nombre como parámetro, por ejemplo test_algo(cl01, eq01).
Las fixtures que reciben db escriben en la base de pruebas, que se deshace después de cada prueba.
"""
import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role
from rentals.models import Equipment, EquipmentStatus
from rentals.roles import CLIENT, MAINTENANCE, OPERATOR

DEMO_PASSWORD = "Demo1234"


def create_user(username, first_name, last_name, phone, role=CLIENT):
    """Crea un usuario de prueba con la clave de la demo, su teléfono y su rol (los roles los crea la migración)."""
    return get_user_model().objects.create_user(
        username,
        email=f"{username}@correo.com",
        password=DEMO_PASSWORD,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        role=Role.objects.get(code=role),
    )


@pytest.fixture
def cl01(db):
    """Cliente Carla Mendoza."""
    return create_user("cl01", "Carla", "Mendoza", "71000001")


@pytest.fixture
def cl02(db):
    """Cliente Diego Rojas, el que el operador busca por «rojas»."""
    return create_user("cl02", "Diego", "Rojas", "71000002")


@pytest.fixture
def op01(db):
    """Operadora Olga Pérez."""
    return create_user("op01", "Olga", "Pérez", "71000003", OPERATOR)


@pytest.fixture
def mt01(db):
    """Mario Torres, de mantenimiento."""
    return create_user("mt01", "Mario", "Torres", "71000004", MAINTENANCE)


@pytest.fixture
def ad01(db):
    """Ana Díaz, administradora: createsuperuser le pone el rol administrador (ENT-44)."""
    return get_user_model().objects.create_superuser(
        "ad01", "ad01@correo.com", DEMO_PASSWORD, phone="71000005"
    )


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
