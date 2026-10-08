"""Integration tests for rentals.services.create_rental, with the database."""
import pytest

from rentals.errors import (
    EquipmentNotAvailableError,
    InvalidPeriodError,
    OutsideRentalHoursError,
)
from rentals.models import Equipment, EquipmentStatus, Rental
from rentals.services import create_rental
from tests.helpers import local_datetime

pytestmark = pytest.mark.django_db


# ---------- Accepted rentals ----------

def test_normal_rental_of_available_unit_is_saved(c01, eq01, doc_start, doc_end):
    # Act: C-01 rents EQ-01 from 09/10 18:00 to 12/10 09:00 (PRE-RF-01)
    rental = create_rental(c01, eq01, doc_start, doc_end)

    # Assert: exactly one rental with the requested data is in the database
    saved = Rental.objects.get()
    assert saved == rental
    assert saved.client == c01
    assert saved.equipment == eq01
    assert saved.start_datetime == doc_start
    assert saved.end_datetime == doc_end


def test_confirmed_rental_does_not_change_equipment_status(c01, eq01, doc_start, doc_end):
    # Act
    create_rental(c01, eq01, doc_start, doc_end)

    # Assert: the unit stays "available" so other periods can be rented
    # (Sesión 07 §4, ENT-10)
    eq01.refresh_from_db()
    assert eq01.status == EquipmentStatus.AVAILABLE


def test_second_unit_of_same_model_can_be_rented_for_same_period(
    c01, c02, eq01, eq02, doc_start, doc_end
):
    # Arrange: EQ-01 and EQ-02 are the same model; C-01 already has EQ-01
    create_rental(c01, eq01, doc_start, doc_end)

    # Act: availability is per unit, not per model (Sesión 04)
    create_rental(c02, eq02, doc_start, doc_end)

    # Assert
    assert Rental.objects.count() == 2
    assert Rental.objects.get(equipment=eq02).client == c02


def test_same_unit_can_be_rented_again_after_previous_period_ends(
    c01, c02, eq01, doc_start, doc_end
):
    # Arrange: C-01 has EQ-01 until 12/10 09:00
    create_rental(c01, eq01, doc_start, doc_end)
    later_start = local_datetime(2026, 10, 12, 18, 0)
    later_end = local_datetime(2026, 10, 14, 9, 0)

    # Act: C-02 asks for the next allowed period, with no overlap
    create_rental(c02, eq01, later_start, later_end)

    # Assert
    assert Rental.objects.filter(equipment=eq01).count() == 2


def test_one_client_can_rent_several_units_for_same_period(
    c01, eq01, eq02, doc_start, doc_end
):
    # Act
    create_rental(c01, eq01, doc_start, doc_end)
    create_rental(c01, eq02, doc_start, doc_end)

    # Assert: a client with one rental is not blocked from another unit
    assert Rental.objects.filter(client=c01).count() == 2


# ---------- Rejected: equipment not available (E1) ----------

def test_overlapping_rental_is_rejected_with_unit_and_dates(
    c01, c02, eq01, doc_start, doc_end
):
    # Arrange: C-01 confirmed first (PRE-RF-01)
    create_rental(c01, eq01, doc_start, doc_end)

    # Act / Assert: the message names the unit and the dates (PRE-RC-01)
    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(c02, eq01, doc_start, doc_end)
    assert "EQ-01" in str(error.value)
    assert "09/10/2026 18:00" in str(error.value)
    assert "12/10/2026 09:00" in str(error.value)


def test_overlapping_rental_keeps_first_rental_unchanged(
    c01, c02, eq01, doc_start, doc_end
):
    # Arrange
    create_rental(c01, eq01, doc_start, doc_end)

    # Act
    with pytest.raises(EquipmentNotAvailableError):
        create_rental(c02, eq01, doc_start, doc_end)

    # Assert: only C-01's rental exists and nothing was saved for C-02
    only_rental = Rental.objects.get()
    assert only_rental.client == c01
    assert only_rental.start_datetime == doc_start
    assert only_rental.end_datetime == doc_end
    assert not Rental.objects.filter(client=c02).exists()


def test_partially_overlapping_rental_is_rejected(c01, c02, eq01, doc_start, doc_end):
    # Arrange
    create_rental(c01, eq01, doc_start, doc_end)
    overlap_start = local_datetime(2026, 10, 11, 18, 0)
    overlap_end = local_datetime(2026, 10, 13, 9, 0)

    # Act / Assert
    with pytest.raises(EquipmentNotAvailableError):
        create_rental(c02, eq01, overlap_start, overlap_end)
    assert Rental.objects.count() == 1


def test_unit_in_review_is_rejected(c01, eq03_in_review, doc_start, doc_end):
    # Act / Assert: a unit waiting for maintenance cannot be rented (PRE-RF-04)
    with pytest.raises(EquipmentNotAvailableError, match="EQ-03"):
        create_rental(c01, eq03_in_review, doc_start, doc_end)

    # Assert: no rental and the status did not change
    assert not Rental.objects.exists()
    eq03_in_review.refresh_from_db()
    assert eq03_in_review.status == EquipmentStatus.IN_REVIEW


def test_status_is_read_from_database_not_from_stale_object(c01, eq01, doc_start, doc_end):
    # Arrange: someone puts EQ-01 in review after the page was loaded
    Equipment.objects.filter(pk=eq01.pk).update(status=EquipmentStatus.IN_REVIEW)

    # Act / Assert: the service re-reads the locked row, so it rejects
    with pytest.raises(EquipmentNotAvailableError):
        create_rental(c01, eq01, doc_start, doc_end)
    assert not Rental.objects.exists()


# ---------- Rejected: invalid period ----------

def test_return_before_pickup_is_rejected(c01, eq01, doc_start, doc_end):
    # Act / Assert: start and end swapped
    with pytest.raises(InvalidPeriodError):
        create_rental(c01, eq01, doc_end, doc_start)
    assert not Rental.objects.exists()


def test_rental_longer_than_five_days_is_rejected(c01, eq01, doc_start):
    # Arrange: 09/10 18:00 -> 15/10 09:00 is 5 days and 15 hours (ENT-18)
    too_late_end = local_datetime(2026, 10, 15, 9, 0)

    # Act / Assert
    with pytest.raises(InvalidPeriodError):
        create_rental(c01, eq01, doc_start, too_late_end)
    assert not Rental.objects.exists()


def test_pickup_before_18_00_is_rejected(c01, eq01, doc_end):
    # Arrange
    early_start = local_datetime(2026, 10, 9, 17, 0)

    # Act / Assert (ENT-19)
    with pytest.raises(OutsideRentalHoursError):
        create_rental(c01, eq01, early_start, doc_end)
    assert not Rental.objects.exists()


def test_return_after_09_00_is_rejected(c01, eq01, doc_start):
    # Arrange
    late_end = local_datetime(2026, 10, 12, 10, 0)

    # Act / Assert (ENT-19)
    with pytest.raises(OutsideRentalHoursError):
        create_rental(c01, eq01, doc_start, late_end)
    assert not Rental.objects.exists()
