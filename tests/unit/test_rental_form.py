"""Unit tests for rentals.forms.RentalForm, without database.

The form only checks that a real date and one of the offered times
arrive, and joins them into datetimes. The business rules are tested
in test_rules.py and test_check_period.py.
"""
from rentals.forms import PICKUP_TIME_CHOICES, RETURN_TIME_CHOICES, RentalForm
from tests.helpers import local_datetime

# What the browser sends for the documents' period.
DOC_FORM_DATA = {
    "start_date": "2026-10-09",
    "start_time": "18:00",
    "end_date": "2026-10-12",
    "end_time": "09:00",
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

    # Assert: same names as before, aware datetimes in America/La_Paz
    assert form.cleaned_data["start_datetime"] == local_datetime(2026, 10, 9, 18, 0)
    assert form.cleaned_data["end_datetime"] == local_datetime(2026, 10, 12, 9, 0)


def test_form_without_pickup_date_is_invalid():
    # Arrange
    data = {**DOC_FORM_DATA, "start_date": ""}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "start_date" in form.errors


def test_form_without_return_date_is_invalid():
    # Arrange
    data = {**DOC_FORM_DATA, "end_date": ""}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "end_date" in form.errors


def test_form_with_invalid_date_format_is_invalid():
    # Arrange: text that is not a date
    data = {**DOC_FORM_DATA, "start_date": "mañana"}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "start_date" in form.errors


def test_pickup_time_outside_the_list_is_invalid():
    # Arrange: 17:00 is not offered (pickup is from 18:00, ENT-19)
    data = {**DOC_FORM_DATA, "start_time": "17:00"}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "start_time" in form.errors


def test_return_time_outside_the_list_is_invalid():
    # Arrange: 09:30 is not offered (return is until 09:00, ENT-19)
    data = {**DOC_FORM_DATA, "end_time": "09:30"}

    # Act
    form = RentalForm(data=data)

    # Assert
    assert not form.is_valid()
    assert "end_time" in form.errors


def test_pickup_times_go_from_18_00_to_23_30_every_30_minutes():
    # Act
    values = [value for value, _label in PICKUP_TIME_CHOICES]

    # Assert
    assert values == [
        "18:00", "18:30", "19:00", "19:30", "20:00", "20:30",
        "21:00", "21:30", "22:00", "22:30", "23:00", "23:30",
    ]


def test_return_times_go_from_00_00_to_09_00_every_30_minutes():
    # Act
    values = [value for value, _label in RETURN_TIME_CHOICES]

    # Assert
    assert values[0] == "00:00"
    assert values[-1] == "09:00"
    assert len(values) == 19
