"""Prueba rentals/forms.py: RentalForm, que junta fecha y hora en La Paz, y ReturnForm, la observación
de la devolución. Los formularios solo revisan que lleguen datos reales; las reglas las aplica el caso de uso."""
from rentals.forms import RentalForm, ReturnForm
from tests.helpers import local_datetime

DATOS_VALIDOS = {
    "start_date": "2026-10-09",
    "start_time": "18:00",
    "end_date": "2026-10-12",
    "end_time": "09:00",
}


def test_rental_form_junta_fecha_y_hora_en_la_paz():
    # Elige del 09/10 18:00 al 12/10 09:00 -> el formulario entrega esos momentos en hora de La Paz
    formulario = RentalForm(DATOS_VALIDOS)
    # Comprueba que los datos son válidos
    assert formulario.is_valid()
    # Comprueba el recojo junto en un solo momento
    assert formulario.cleaned_data["start_datetime"] == local_datetime(2026, 10, 9, 18, 0)
    # Comprueba la devolución junta en un solo momento
    assert formulario.cleaned_data["end_datetime"] == local_datetime(2026, 10, 12, 9, 0)


def test_rental_form_con_hora_invalida_da_error_en_su_campo():
    # Escribe «25:00» como hora de recojo -> el error sale en ese campo
    formulario = RentalForm({**DATOS_VALIDOS, "start_time": "25:00"})
    # Comprueba que el formulario se rechaza
    assert not formulario.is_valid()
    # Comprueba que el error está en la hora de recojo
    assert "start_time" in formulario.errors


def test_rental_form_sin_fecha_da_error_en_su_campo():
    # No elige la fecha de devolución -> el error sale en ese campo
    formulario = RentalForm({**DATOS_VALIDOS, "end_date": ""})
    # Comprueba que el formulario se rechaza
    assert not formulario.is_valid()
    # Comprueba que el error está en la fecha de devolución
    assert "end_date" in formulario.errors


def test_return_form_rechaza_una_nota_de_mas_de_200_caracteres():
    # Escribe una observación de 201 caracteres -> el formulario la rechaza antes de llegar a la base
    formulario = ReturnForm({"note": "x" * 201})
    # Comprueba que el formulario se rechaza
    assert not formulario.is_valid()
    # Comprueba que el error está en la observación
    assert "note" in formulario.errors


def test_return_form_acepta_la_nota_vacia():
    # Deja la observación vacía -> el formulario la acepta, porque la revisa register_return con su mensaje
    formulario = ReturnForm({"note": ""})
    # Comprueba que el formulario es válido
    assert formulario.is_valid()
    # Comprueba que la nota llega vacía al caso de uso
    assert formulario.cleaned_data["note"] == ""
