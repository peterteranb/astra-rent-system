"""Unit tests for rentals.services.check_period.

check_period runs before the service opens a transaction, so these
tests need no database. The end-to-end "nothing is saved" check is in
tests/integration/test_views.py.
"""
import pytest

from rentals.errors import InvalidPeriodError, OutsideRentalHoursError
from rentals.services import check_period
from tests.helpers import local_datetime

# Period of the documents' scenario (Sesión 06, PRE-RF-01).
DOC_START = local_datetime(2026, 10, 9, 18, 0)
DOC_END = local_datetime(2026, 10, 12, 9, 0)


# ---------- Which error is raised (moved from the integration tests) ----------

def test_return_before_pickup_is_rejected():
    # Act / Assert: start and end swapped
    with pytest.raises(InvalidPeriodError):
        check_period(DOC_END, DOC_START)


def test_rental_longer_than_five_days_is_rejected():
    # Arrange: 09/10 18:00 -> 15/10 09:00 is 5 days and 15 hours (ENT-18)
    too_late_end = local_datetime(2026, 10, 15, 9, 0)

    # Act / Assert
    with pytest.raises(InvalidPeriodError):
        check_period(DOC_START, too_late_end)


def test_pickup_before_18_00_is_rejected():
    # Arrange
    early_start = local_datetime(2026, 10, 9, 17, 0)

    # Act / Assert (ENT-19)
    with pytest.raises(OutsideRentalHoursError):
        check_period(early_start, DOC_END)


def test_return_after_09_00_is_rejected():
    # Arrange
    late_end = local_datetime(2026, 10, 12, 10, 0)

    # Act / Assert (ENT-19)
    with pytest.raises(OutsideRentalHoursError):
        check_period(DOC_START, late_end)


# ---------- Messages shown to the client (PRE-RC-01) ----------

def test_documents_period_passes_without_error():
    # Act / Assert: no exception means the period is accepted
    check_period(DOC_START, DOC_END)


def test_message_for_return_before_pickup():
    # Act
    with pytest.raises(InvalidPeriodError) as error:
        check_period(DOC_END, DOC_START)

    # Assert
    assert str(error.value) == "La fecha y hora de devolución debe ser posterior a la de recojo."


def test_message_for_rental_longer_than_five_days():
    # Act
    with pytest.raises(InvalidPeriodError) as error:
        check_period(DOC_START, local_datetime(2026, 10, 15, 9, 0))

    # Assert
    assert str(error.value) == "La renta no puede durar más de 5 días."


def test_message_for_pickup_before_18_00():
    # Act
    with pytest.raises(OutsideRentalHoursError) as error:
        check_period(local_datetime(2026, 10, 9, 17, 0), DOC_END)

    # Assert
    assert str(error.value) == "El recojo debe ser desde las 18:00."


def test_message_for_return_after_09_00():
    # Act
    with pytest.raises(OutsideRentalHoursError) as error:
        check_period(DOC_START, local_datetime(2026, 10, 12, 10, 0))

    # Assert
    assert str(error.value) == "La devolución debe ser hasta las 09:00."
