"""Unit tests for rentals.forms.RentalForm, without database.

The form only checks that real dates arrive; the business rules are
tested in test_rules.py and test_check_period.py.
"""
from rentals.forms import RentalForm
from tests.helpers import local_datetime

# What the browser sends for the documents' period.
DOC_FORM_DATA = {
    "start_datetime": "2026-10-09T18:00",
    "end_datetime": "2026-10-12T09:00",
}


def test_form_with_both_dates_is_valid():
    # Act
    form = RentalForm(data=DOC_FORM_DATA)

    # Assert
    assert form.is_valid()


def test_form_turns_input_into_local_aware_datetimes():
    # Act
    form = RentalForm(data=DOC_FORM_DATA)
    form.is_valid()

    # Assert: the values are aware datetimes in America/La_Paz
    assert form.cleaned_data["start_datetime"] == local_datetime(2026, 10, 9, 18, 0)
    assert form.cleaned_data["end_datetime"] == local_datetime(2026, 10, 12, 9, 0)


def test_form_without_pickup_date_is_invalid():
    # Arrange
    data = {**DOC_FORM_DATA, "start_datetime": ""}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "start_datetime" in form.errors


def test_form_without_return_date_is_invalid():
    # Arrange
    data = {**DOC_FORM_DATA, "end_datetime": ""}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "end_datetime" in form.errors


def test_form_with_invalid_date_format_is_invalid():
    # Arrange: text that is not a date
    data = {**DOC_FORM_DATA, "start_datetime": "mañana a las 6"}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "start_datetime" in form.errors
