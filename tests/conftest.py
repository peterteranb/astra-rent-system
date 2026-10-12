"""Shared test data, taken from the documents (Sesión 06 and 07).

Each fixture creates fresh rows; pytest-django rolls the database back
after every test, so tests never share data.
"""
import pytest
from django.contrib.auth import get_user_model

from rentals.models import Equipment, EquipmentStatus
from tests.helpers import local_datetime

DEMO_PASSWORD = "demo1234"


@pytest.fixture
def doc_start():
    """Pickup of the documents' scenario: 09/10/2026 18:00."""
    return local_datetime(2026, 10, 9, 18, 0)


@pytest.fixture
def doc_end():
    """Return of the documents' scenario: 12/10/2026 09:00."""
    return local_datetime(2026, 10, 12, 9, 0)


@pytest.fixture
def c01(db):
    """Client C-01 of the documents."""
    return get_user_model().objects.create_user("c01", password=DEMO_PASSWORD)


@pytest.fixture
def c02(db):
    """Client C-02 of the documents."""
    return get_user_model().objects.create_user("c02", password=DEMO_PASSWORD)


@pytest.fixture
def eq01(db):
    """Unit EQ-01, available."""
    return Equipment.objects.create(
        inventory_id="EQ-01",
        serial_number="SN-T-001",
        description="Mesa plegable 1,80 m",
        status=EquipmentStatus.AVAILABLE,
    )


@pytest.fixture
def eq02(db):
    """Unit EQ-02, same model as EQ-01, available."""
    return Equipment.objects.create(
        inventory_id="EQ-02",
        serial_number="SN-T-002",
        description="Mesa plegable 1,80 m",
        status=EquipmentStatus.AVAILABLE,
    )


@pytest.fixture
def eq03_in_review(db):
    """Unit EQ-03, returned and waiting for maintenance (PRE-RF-04)."""
    return Equipment.objects.create(
        inventory_id="EQ-03",
        serial_number="SN-T-003",
        description="Mesa redonda 1,20 m",
        status=EquipmentStatus.IN_REVIEW,
    )
