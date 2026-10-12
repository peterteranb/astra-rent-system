"""Pruebas UNITARIAS del formulario de renta.

Archivo que se prueba: rentals/forms.py -> RentalForm
Tipo de prueba:        unitaria (no usa base de datos ni paginas).

Que hace RentalForm:
    El navegador envia TEXTO: "2026-10-09" y "18:00". El formulario:
        1. revisa que la fecha sea una fecha real y la hora una hora real,
        2. junta fecha + hora en un datetime con la zona horaria de La Paz,
        3. lo deja en form.cleaned_data["start_datetime"] y ["end_datetime"].
    El formulario NO aplica reglas de negocio (18:00, 09:00, 5 dias, cruces):
    eso lo hace el servicio. Asi la regla vive en un solo lugar (rules.py).

Como funciona cada prueba:
    Se crea el formulario con datos como los que enviaria el navegador:
        form = RentalForm(data={...})
    y se pregunta form.is_valid(). Si es valido, se revisa cleaned_data;
    si no, se revisa form.errors (diccionario campo -> lista de errores).
"""
import pytest

from rentals.forms import RentalForm
from tests.helpers import local_datetime

# Lo que envia el navegador para el periodo de los documentos (09/10 18:00 -> 12/10 09:00).
DATOS_VALIDOS = {
    "start_date": "2026-10-09",
    "start_time": "18:00",
    "end_date": "2026-10-12",
    "end_time": "09:00",
}


def test_datos_validos_se_convierten_en_fecha_y_hora_de_la_paz():
    """Con datos correctos, el formulario arma las dos fechas completas.

    Caso:               el cliente llena bien los cuatro campos.
    Entrada:            recojo 2026-10-09 18:00, devolucion 2026-10-12 09:00 (como texto).
    Condiciones:        ninguna.
    Resultado esperado: el formulario es valido y cleaned_data tiene
                        start_datetime = 09/10/2026 18:00 y end_datetime = 12/10/2026 09:00,
                        ambos en hora de La Paz.
    Requisito:          PRE-CU-01 paso 6 (el cliente indica fecha y hora de recojo
                        y de devolucion).
    Codigo que cubre:   rentals/forms.py -> RentalForm.clean().
    """
    # Preparar
    form = RentalForm(data=DATOS_VALIDOS)

    # Ejecutar
    es_valido = form.is_valid()

    # Comprobar
    assert es_valido is True
    assert form.cleaned_data["start_datetime"] == local_datetime(2026, 10, 9, 18, 0)
    assert form.cleaned_data["end_datetime"] == local_datetime(2026, 10, 12, 9, 0)


@pytest.mark.parametrize(
    "campo, valor, fecha_esperada",
    [
        ("start_time", "17:00", ("start_datetime", local_datetime(2026, 10, 9, 17, 0))),
        ("end_time", "09:30", ("end_datetime", local_datetime(2026, 10, 12, 9, 30))),
    ],
    ids=["recojo a las 17:00", "devolucion a las 09:30"],
)
def test_el_formulario_no_aplica_el_horario_lo_hace_el_servicio(campo, valor, fecha_esperada):
    """Una hora fuera del horario es valida PARA EL FORMULARIO.

    Caso:               el cliente escribe una hora fuera de 18:00 / 09:00.
    Entrada:            recojo a las 17:00, o devolucion a las 09:30.
    Condiciones:        el resto de los datos son correctos.
    Resultado esperado: el formulario es valido y guarda la hora tal como llego.
                        Quien la rechaza despues es el servicio (ver test_check_period.py
                        y test_views.py).
    Requisito:          ENT-19. Esta prueba documenta una DECISION de diseno:
                        la regla vive solo en rules.py, no repetida en el formulario.
    Codigo que cubre:   rentals/forms.py -> RentalForm.clean().
    """
    # Preparar: cambiamos solo un campo de los datos validos
    datos = {**DATOS_VALIDOS, campo: valor}
    form = RentalForm(data=datos)
    nombre, fecha = fecha_esperada

    # Ejecutar
    es_valido = form.is_valid()

    # Comprobar
    assert es_valido is True
    assert form.cleaned_data[nombre] == fecha


@pytest.mark.parametrize(
    "campo, valor",
    [
        ("start_date", ""),
        ("end_date", ""),
        ("start_date", "mañana"),
        ("start_time", "25:00"),
        ("start_time", "tarde"),
    ],
    ids=[
        "falta la fecha de recojo",
        "falta la fecha de devolucion",
        "la fecha no es una fecha",
        "la hora no existe (25:00)",
        "la hora no es una hora",
    ],
)
def test_datos_que_no_son_fecha_u_hora_se_rechazan_en_su_campo(campo, valor):
    """El formulario rechaza datos vacios o mal escritos y dice en que campo.

    Caso:               el cliente deja un campo vacio o escribe algo que no es fecha u hora.
    Entrada:            los datos validos con UN campo cambiado (ver cada fila).
    Condiciones:        ninguna.
    Resultado esperado: el formulario no es valido y el error aparece en ese campo.
    Requisito:          PRE-CU-01 paso 6 y condicion comun del curso
                        ("un error debe producir un mensaje comprensible").
    Codigo que cubre:   rentals/forms.py -> campos DateField y TimeField de RentalForm.
    """
    # Preparar
    datos = {**DATOS_VALIDOS, campo: valor}
    form = RentalForm(data=datos)

    # Ejecutar
    es_valido = form.is_valid()

    # Comprobar
    assert es_valido is False
    assert campo in form.errors


def test_las_ayudas_de_los_campos_muestran_el_horario():
    """Debajo de cada hora, el cliente ve el horario permitido.

    Caso:               el cliente abre el formulario vacio.
    Entrada:            ninguna (formulario nuevo).
    Condiciones:        las horas salen de las constantes de rules.py.
    Resultado esperado: el recojo dice "Desde las 18:00" y la devolucion "Hasta las 09:00".
    Requisito:          ENT-19 y PRE-RC-01 (el cliente sabe la regla antes de equivocarse).
    Codigo que cubre:   rentals/forms.py -> help_text de start_time y end_time.
    """
    # Ejecutar
    form = RentalForm()

    # Comprobar
    assert form.fields["start_time"].help_text == "Desde las 18:00"
    assert form.fields["end_time"].help_text == "Hasta las 09:00"
