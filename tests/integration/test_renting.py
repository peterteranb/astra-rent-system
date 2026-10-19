"""Pruebas de INTEGRACION del servicio que guarda la renta.

Archivo que se prueba: rentals/renting.py -> create_rental()
Tipo de prueba:        integracion (usa una base PostgreSQL de pruebas).

Que hace create_rental():
    Es el caso de uso PRE-CU-01 en codigo. Recibe cliente, equipo, recojo y devolucion, y:
        1. revisa el periodo (check_period),
        2. abre una transaccion y BLOQUEA la fila del equipo (select_for_update),
        3. revisa que el equipo este disponible y sin rentas que se crucen,
        4. guarda la renta y la devuelve.
    Si algo falla, lanza EquipmentNotAvailableError (E1) y NO guarda nada.

De donde salen los datos (no se usa seed_demo):
    pytest-django crea una base aparte llamada test_astra_rent, le aplica las
    migraciones y la borra al terminar. La base de demo NO se toca.
    Los clientes y equipos los crean las "fixtures" de tests/conftest.py
    (c01, c02, eq01, eq02, eq03_in_review, doc_start, doc_end). Una prueba las
    pide escribiendolas como parametros, y pytest las crea antes de ejecutarla.
    Al terminar cada prueba, todo lo que creo se deshace: cada prueba empieza
    con la base vacia.

pytestmark = pytest.mark.django_db le da permiso de usar la base a todas las
pruebas de este archivo.
"""
import pytest

from rentals.errors import EquipmentNotAvailableError
from rentals.models import Equipment, EquipmentStatus, Rental
from rentals.renting import create_rental
from tests.helpers import local_datetime

pytestmark = pytest.mark.django_db


def test_una_renta_valida_se_guarda_y_el_equipo_sigue_disponible(c01, eq01, doc_start, doc_end):
    """Caso normal: C-01 renta EQ-01 y la renta queda guardada en la base.

    Caso:               C-01 renta EQ-01 del 09/10/2026 18:00 al 12/10/2026 09:00.
    Entrada:            cliente c01, equipo eq01 (disponible), recojo y devolucion de los documentos.
    Condiciones:        la base no tiene ninguna renta.
    Resultado esperado: existe UNA renta con ese cliente, ese equipo y esas fechas,
                        y EQ-01 sigue "disponible" (para poder rentarlo en otras fechas).
    Requisito:          PRE-RF-01 (caso normal), ENT-16 (se confirma al instante)
                        y ENT-10 (el equipo queda ocupado solo en ese periodo).
    Codigo que cubre:   rentals/renting.py -> create_rental(); rentals/models.py -> Rental.
    """
    # Ejecutar
    renta = create_rental(c01, eq01, doc_start, doc_end)

    # Comprobar: hay exactamente una renta y tiene los datos pedidos
    guardada = Rental.objects.get()          # .get() falla si hay 0 o mas de 1
    assert guardada == renta
    assert guardada.client == c01
    assert guardada.equipment == eq01
    assert guardada.start_datetime == doc_start
    assert guardada.end_datetime == doc_end

    # Comprobar: el estado del equipo NO cambio (Sesion 7, seccion 4)
    eq01.refresh_from_db()                   # vuelve a leer EQ-01 desde la base
    assert eq01.status == EquipmentStatus.AVAILABLE


def test_si_c01_ya_tiene_eq01_la_renta_de_c02_en_esas_fechas_se_rechaza(
    c01, c02, eq01
):
    """Rechazo E1: el segundo cliente no puede rentar el mismo equipo en las mismas fechas.

    Caso:               C-01 confirmo EQ-01 primero; despues C-02 pide EQ-01 para el mismo periodo.
    Entrada:            c02, eq01, recojo 09/10 18:00, devolucion 12/10 09:00.
    Condiciones:        ya existe la renta de C-01 para ese periodo.
    Resultado esperado: se lanza EquipmentNotAvailableError con un mensaje que dice
                        el equipo y las fechas; en la base sigue habiendo una sola
                        renta (la de C-01, sin cambios) y ninguna de C-02.
    Requisito:          PRE-RF-01 (escenario de rechazo de la Sesion 6) y
                        PRE-RC-01 (el mensaje dice equipo y fechas).
    Codigo que cubre:   rentals/renting.py -> create_rental() y check_equipment_is_free(),
                        que usa rules.periods_overlap().
    """
    inicio_futuro = local_datetime(2026, 10, 25, 18, 0)
    fin_futuro = local_datetime(2026, 10, 28, 9, 0)

    create_rental(c01, eq01, inicio_futuro, fin_futuro)

    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(c02, eq01, inicio_futuro, fin_futuro)

    assert "está ocupado desde el" in str(error.value)

    unica = Rental.objects.get()
    assert unica.client == c01


def test_un_equipo_en_revision_no_se_puede_rentar(c01, eq03_in_review, doc_start, doc_end):
    """Rechazo E1: un equipo devuelto que espera a mantenimiento no se renta.

    Caso:               C-01 intenta rentar EQ-03, que esta "en revision".
    Entrada:            c01, eq03_in_review, recojo y devolucion de los documentos.
    Condiciones:        EQ-03 no tiene rentas, pero su estado no es "disponible".
    Resultado esperado: se lanza EquipmentNotAvailableError con el estado en el
                        mensaje; no se guarda ninguna renta y EQ-03 sigue "en revision".
    Requisito:          PRE-RF-04 (un equipo en revision no se renta) y PRE-RC-01.
    Codigo que cubre:   rentals/renting.py -> check_equipment_is_free(), que usa
                        rules.is_rentable_status().
    """
    # Ejecutar
    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(c01, eq03_in_review, doc_start, doc_end)

    # Comprobar: mensaje con la causa
    assert str(error.value) == "El equipo EQ-03 no está disponible (estado: En revisión)."

    # Comprobar: no se guardo nada y el estado no cambio
    assert Rental.objects.count() == 0
    eq03_in_review.refresh_from_db()
    assert eq03_in_review.status == EquipmentStatus.IN_REVIEW


def test_otra_unidad_del_mismo_modelo_si_se_puede_rentar_en_las_mismas_fechas(
    c01, c02, eq01, eq02, doc_start, doc_end
):
    """La disponibilidad es por UNIDAD, no por modelo.

    Caso:               C-01 tiene EQ-01; C-02 pide EQ-02 (misma mesa, otra unidad) en las mismas fechas.
    Entrada:            c02, eq02, recojo y devolucion de los documentos.
    Condiciones:        EQ-01 y EQ-02 tienen la misma descripcion; EQ-01 ya esta rentado en ese periodo.
    Resultado esperado: la renta de C-02 se guarda; hay dos rentas, una por unidad.
    Requisito:          ENT-09 (cada equipo se registra individualmente) y
                        caso limite "dos unidades del mismo modelo" (Sesion 4).
    Codigo que cubre:   rentals/renting.py -> create_rental() (solo mira las rentas de ESA unidad).
    """
    # Preparar
    create_rental(c01, eq01, doc_start, doc_end)

    # Ejecutar
    renta_c02 = create_rental(c02, eq02, doc_start, doc_end)

    # Comprobar
    assert Rental.objects.count() == 2
    assert renta_c02.equipment == eq02
    assert renta_c02.client == c02


def test_el_mismo_equipo_se_puede_rentar_cuando_termina_la_renta_anterior(
    c01, c02, eq01, doc_start, doc_end
):
    """Caso limite: una renta que empieza despues de que termina la otra se acepta.

    Caso:               C-01 tiene EQ-01 hasta el 12/10 09:00; C-02 lo pide del 12/10 18:00 al 14/10 09:00.
    Entrada:            c02, eq01, recojo 12/10 18:00, devolucion 14/10 09:00.
    Condiciones:        los periodos no comparten ningun minuto.
    Resultado esperado: la renta de C-02 se guarda; EQ-01 tiene dos rentas.
    Requisito:          ENT-10 (el equipo queda apartado solo en su periodo) y caso
                        limite del plan de las Sesiones 8 y 9.
    Codigo que cubre:   rentals/renting.py -> create_rental() con rules.periods_overlap().
    """
    # Preparar
    create_rental(c01, eq01, doc_start, doc_end)
    recojo_siguiente = local_datetime(2026, 10, 12, 18, 0)
    devolucion_siguiente = local_datetime(2026, 10, 14, 9, 0)

    # Ejecutar
    create_rental(c02, eq01, recojo_siguiente, devolucion_siguiente)

    # Comprobar
    assert Rental.objects.filter(equipment=eq01).count() == 2


def test_el_estado_se_vuelve_a_leer_de_la_base_al_confirmar(c01, eq01, doc_start, doc_end):
    """El servicio no confia en datos viejos: lee el estado real al confirmar.

    Caso:               el cliente abrio el formulario con EQ-01 disponible, pero mientras
                        lo llenaba alguien puso EQ-01 "en revision".
    Entrada:            c01, eq01 (el objeto en memoria todavia dice "disponible").
    Condiciones:        en la BASE, EQ-01 ya esta "en revision".
    Resultado esperado: se lanza EquipmentNotAvailableError y no se guarda la renta.
    Requisito:          situacion del encargo: "un equipo esta disponible al abrir la
                        pantalla, pero ya no lo esta al confirmar"; PRE-RF-04.
    Codigo que cubre:   rentals/renting.py -> create_rental(): select_for_update().get()
                        vuelve a leer la fila del equipo antes de revisarla.
    """
    # Preparar: cambiamos el estado directo en la base, sin tocar el objeto eq01
    Equipment.objects.filter(pk=eq01.pk).update(status=EquipmentStatus.IN_REVIEW)

    # Ejecutar
    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(c01, eq01, doc_start, doc_end)

    # Comprobar
    assert "estado: En revisión" in str(error.value)
    assert Rental.objects.count() == 0
