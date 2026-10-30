"""Prueba rentals/forms.py: RentalForm (unión de fechas y horas en La Paz) y ReturnForm (observaciones de devolución)."""
from rentals.forms import RentalForm, ReturnForm
from tests.helpers import local_datetime

DATOS_VALIDOS = {
    "start_date": "2026-10-09",
    "start_time": "18:00",
    "end_date": "2026-10-12",
    "end_time": "09:00",
}


def test_validaciones_y_procesamiento_de_formularios_de_renta_y_devolucion():
    # RentalForm válido junta correctamente fecha y hora con zona horaria; horas inválidas o fechas vacías reportan errores en campo -> integridad del formulario
    # Comprueba que un formulario con datos correctos es válido y procesa las fechas en la zona horaria correcta
    formulario_valido = RentalForm(DATOS_VALIDOS)
    assert formulario_valido.is_valid()
    assert formulario_valido.cleaned_data["start_datetime"] == local_datetime(2026, 10, 9, 18, 0)
    assert formulario_valido.cleaned_data["end_datetime"] == local_datetime(2026, 10, 12, 9, 0)

    # Comprueba que una hora de recojo inválida (ej. formato incorrecto) rechaza el formulario y marca error en su campo
    formulario_hora = RentalForm({**DATOS_VALIDOS, "start_time": "25:00"})
    assert not formulario_hora.is_valid()
    assert "start_time" in formulario_hora.errors

    # Comprueba que omitir la fecha de devolución invalida el formulario y sitúa el error en su campo correspondiente
    formulario_fecha = RentalForm({**DATOS_VALIDOS, "end_date": ""})
    assert not formulario_fecha.is_valid()
    assert "end_date" in formulario_fecha.errors

    # ReturnForm rechaza notas mayores a 200 caracteres pero acepta notas vacías para validación de negocio posterior -> validación de longitud de notas
    # Comprueba que una nota de devolución excesivamente larga (más de 200 caracteres) es rechazada por el formulario
    formulario_nota_larga = ReturnForm({"note": "x" * 201})
    assert not formulario_nota_larga.is_valid()
    assert "note" in formulario_nota_larga.errors

    # Comprueba que el formulario acepta una nota vacía, dejando que el caso de uso aplique su propia regla de obligatoriedad
    formulario_nota_vacia = ReturnForm({"note": ""})
    assert formulario_nota_vacia.is_valid()
    assert formulario_nota_vacia.cleaned_data["note"] == ""