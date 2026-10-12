"""Unit tests for rentals.forms.RentalForm, without database.

The form only checks that a real date and a real time arrive, and
joins them into datetimes. The business rules (including the 18:00 /
09:00 window) are tested in test_rules.py and test_check_period.py.
"""
import pytest

from rentals.forms import RentalForm
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


def test_form_accepts_pickup_at_17_00_and_leaves_the_rule_to_the_service():
    """El formulario acepta un recojo a las 17:00, fuera de la ventana.

    Llama a: RentalForm.is_valid()
    Requisito: ENT-19 (recojo desde las 18:00); la regla la aplica el servicio, no el formulario.
    Espera: el formulario es válido y start_datetime queda a las 17:00 del 09/10/2026.
    """
    # Preparar
    data = {**DOC_FORM_DATA, "start_time": "17:00"}

    # Ejecutar
    form = RentalForm(data=data)

    # Comprobar
    assert form.is_valid()
    assert form.cleaned_data["start_datetime"] == local_datetime(2026, 10, 9, 17, 0)


def test_form_accepts_return_at_09_30_and_leaves_the_rule_to_the_service():
    """El formulario acepta una devolución a las 09:30, fuera de la ventana.

    Llama a: RentalForm.is_valid()
    Requisito: ENT-19 (devolución hasta las 09:00); la regla la aplica el servicio, no el formulario.
    Espera: el formulario es válido y end_datetime queda a las 09:30 del 12/10/2026.
    """
    # Preparar
    data = {**DOC_FORM_DATA, "end_time": "09:30"}

    # Ejecutar
    form = RentalForm(data=data)

    # Comprobar
    assert form.is_valid()
    assert form.cleaned_data["end_datetime"] == local_datetime(2026, 10, 12, 9, 30)


def test_form_accepts_pickup_time_with_any_minute():
    """El formulario acepta una hora con minutos sueltos (18:15).

    Llama a: RentalForm.is_valid()
    Requisito: PRE-CU-01 paso 6 (el cliente introduce la hora de recojo).
    Espera: el formulario es válido y start_datetime queda a las 18:15.
    """
    # Preparar
    data = {**DOC_FORM_DATA, "start_time": "18:15"}

    # Ejecutar
    form = RentalForm(data=data)

    # Comprobar
    assert form.is_valid()
    assert form.cleaned_data["start_datetime"] == local_datetime(2026, 10, 9, 18, 15)


@pytest.mark.parametrize("bad_time", ["25:00", "tarde"])
def test_form_rejects_text_that_is_not_a_time(bad_time):
    """El formulario rechaza una hora que no existe o un texto que no es hora.

    Llama a: RentalForm.is_valid()
    Requisito: PRE-CU-01 paso 6 (el cliente introduce la hora de recojo).
    Espera: el formulario no es válido y el error está en start_time.
    """
    # Preparar
    data = {**DOC_FORM_DATA, "start_time": bad_time}

    # Ejecutar
    form = RentalForm(data=data)

    # Comprobar
    assert not form.is_valid()
    assert "start_time" in form.errors


def test_help_texts_show_the_window_taken_from_rules():
    """Las ayudas de los campos de hora muestran la ventana de rules.py.

    Llama a: RentalForm() (campos start_time y end_time)
    Requisito: ENT-19 (recojo desde las 18:00, devolución hasta las 09:00).
    Espera: "Desde las 18:00" en el recojo y "Hasta las 09:00" en la devolución.
    """
    # Ejecutar
    form = RentalForm()

    # Comprobar
    assert form.fields["start_time"].help_text == "Desde las 18:00"
    assert form.fields["end_time"].help_text == "Hasta las 09:00"
