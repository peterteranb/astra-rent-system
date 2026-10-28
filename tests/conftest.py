"""Datos de prueba compartidos (fixtures) con los mismos nombres de la demo: cl01, cl02, op01, mt01, ad01 y los equipos.

Una prueba pide un dato escribiendo su nombre como parámetro, por ejemplo test_algo(cl01, mes01).
Las fixtures que reciben db escriben en la base de pruebas, que se deshace después de cada prueba.
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role
from accounts.roles import CLIENT, MAINTENANCE, OPERATOR
from rentals.models import Equipment, EquipmentStatus

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
def mes01(db):
    """MES-00001: mesa plegable de 400 Bs, disponible; su día cuesta 20 Bs."""
    return Equipment.objects.create(
        inventory_id="MES-00001", serial_number="SN-MES-00001", name="Mesa plegable 1,80 m",
        value=Decimal("400.00"),
    )


@pytest.fixture
def mes02(db):
    """MES-00002: otra mesa plegable igual, disponible."""
    return Equipment.objects.create(
        inventory_id="MES-00002", serial_number="SN-MES-00002", name="Mesa plegable 1,80 m",
        value=Decimal("400.00"),
    )


@pytest.fixture
def mes03_en_revision(db):
    """MES-00003: mesa redonda de 350 Bs devuelta, que espera a mantenimiento."""
    return Equipment.objects.create(
        inventory_id="MES-00003",
        serial_number="SN-MES-00003",
        name="Mesa redonda 1,20 m",
        value=Decimal("350.00"),
        status=EquipmentStatus.IN_REVIEW,
    )
