"""Unit tests for the pure business rules in rentals/rules.py.

No database: every test builds its own datetimes. Times are local
(America/La_Paz), the same as the rules receive them from the service.
"""
from datetime import datetime

import pytest

from rentals.models import EquipmentStatus
from rentals.rules import (
    ends_after_start,
    is_pickup_time_allowed,
    is_rentable_status,
    is_return_time_allowed,
    is_within_max_duration,
    periods_overlap,
)

# Period of the documents' scenario (Sesión 06, PRE-RF-01).
DOC_START = datetime(2026, 10, 9, 18, 0)
DOC_END = datetime(2026, 10, 12, 9, 0)


# ---------- periods_overlap (PRE-RF-01) ----------

def test_same_period_overlaps():
    # Arrange / Act: C-02 asks for exactly the period C-01 already has
    result = periods_overlap(DOC_START, DOC_END, DOC_START, DOC_END)

    # Assert
    assert result is True


def test_new_period_starting_inside_existing_one_overlaps():
    # Arrange
    new_start = datetime(2026, 10, 11, 18, 0)
    new_end = datetime(2026, 10, 13, 9, 0)

    # Act
    result = periods_overlap(new_start, new_end, DOC_START, DOC_END)

    # Assert
    assert result is True


def test_new_period_ending_inside_existing_one_overlaps():
    # Arrange
    new_start = datetime(2026, 10, 8, 18, 0)
    new_end = datetime(2026, 10, 10, 9, 0)

    # Act
    result = periods_overlap(new_start, new_end, DOC_START, DOC_END)

    # Assert
    assert result is True


def test_new_period_containing_existing_one_overlaps():
    # Arrange
    new_start = datetime(2026, 10, 8, 18, 0)
    new_end = datetime(2026, 10, 13, 9, 0)

    # Act
    result = periods_overlap(new_start, new_end, DOC_START, DOC_END)

    # Assert
    assert result is True


def test_new_period_starting_exactly_when_existing_ends_does_not_overlap():
    # Arrange: boundary case of Sesión 08-09, the second rental starts
    # at the very instant the first one ends
    new_start = DOC_END
    new_end = datetime(2026, 10, 13, 9, 0)

    # Act
    result = periods_overlap(new_start, new_end, DOC_START, DOC_END)

    # Assert
    assert result is False


def test_new_period_ending_exactly_when_existing_starts_does_not_overlap():
    # Arrange
    new_start = datetime(2026, 10, 8, 18, 0)
    new_end = DOC_START

    # Act
    result = periods_overlap(new_start, new_end, DOC_START, DOC_END)

    # Assert
    assert result is False


def test_new_period_entirely_after_existing_one_does_not_overlap():
    # Arrange
    new_start = datetime(2026, 10, 20, 18, 0)
    new_end = datetime(2026, 10, 22, 9, 0)

    # Act
    result = periods_overlap(new_start, new_end, DOC_START, DOC_END)

    # Assert
    assert result is False


# ---------- is_rentable_status (PRE-RF-04, ENT-33) ----------

def test_available_equipment_is_rentable():
    # Act / Assert
    assert is_rentable_status(EquipmentStatus.AVAILABLE) is True


@pytest.mark.parametrize(
    "status",
    [
        EquipmentStatus.RENTED,
        EquipmentStatus.IN_REVIEW,
        EquipmentStatus.IN_REPAIR,
        EquipmentStatus.RETIRED,
    ],
)
def test_equipment_in_any_other_status_is_not_rentable(status):
    # Act / Assert: only "available" can be rented
    assert is_rentable_status(status) is False


# ---------- ends_after_start ----------

def test_period_ending_after_it_starts_is_valid():
    # Act / Assert
    assert ends_after_start(DOC_START, DOC_END) is True


def test_period_ending_at_the_same_instant_it_starts_is_invalid():
    # Act / Assert: a zero-length rental makes no sense
    assert ends_after_start(DOC_START, DOC_START) is False


def test_period_ending_before_it_starts_is_invalid():
    # Act / Assert: start and end swapped by mistake
    assert ends_after_start(DOC_END, DOC_START) is False


# ---------- is_within_max_duration (ENT-18) ----------

def test_documents_period_of_less_than_five_days_is_allowed():
    # Act / Assert: 09/10 18:00 -> 12/10 09:00 is 2 days and 15 hours
    assert is_within_max_duration(DOC_START, DOC_END) is True


def test_period_of_exactly_five_days_is_allowed():
    # Arrange
    end = datetime(2026, 10, 14, 18, 0)

    # Act / Assert: the limit itself is accepted (<= 5 days)
    assert is_within_max_duration(DOC_START, end) is True


def test_period_one_minute_longer_than_five_days_is_rejected():
    # Arrange
    end = datetime(2026, 10, 14, 18, 1)

    # Act / Assert
    assert is_within_max_duration(DOC_START, end) is False


# ---------- is_pickup_time_allowed / is_return_time_allowed (ENT-19) ----------

def test_pickup_at_exactly_18_00_is_allowed():
    # Act / Assert
    assert is_pickup_time_allowed(datetime(2026, 10, 9, 18, 0)) is True


def test_pickup_later_in_the_evening_is_allowed():
    # Act / Assert
    assert is_pickup_time_allowed(datetime(2026, 10, 9, 21, 30)) is True


def test_pickup_one_minute_before_18_00_is_rejected():
    # Act / Assert
    assert is_pickup_time_allowed(datetime(2026, 10, 9, 17, 59)) is False


def test_return_at_exactly_09_00_is_allowed():
    # Act / Assert
    assert is_return_time_allowed(datetime(2026, 10, 12, 9, 0)) is True


def test_return_early_in_the_morning_is_allowed():
    # Act / Assert
    assert is_return_time_allowed(datetime(2026, 10, 12, 7, 15)) is True


def test_return_one_minute_after_09_00_is_rejected():
    # Act / Assert
    assert is_return_time_allowed(datetime(2026, 10, 12, 9, 1)) is False
