"""Pruebas de INTEGRACION del servicio que guarda la renta.

Archivo que se prueba: rentals/renting.py -> create_rental(), cancel_rental() y find_clients()
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
from django.utils import timezone

from rentals.errors import EquipmentNotAvailableError, RentalStateError
from rentals.handover import register_pickup
from rentals.models import Equipment, EquipmentStatus, Rental
from rentals.renting import cancel_rental, create_rental, find_clients
from rentals.statuses import RentalStatus
from tests.helpers import dentro_de, foto_de_la_base

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
    Entrada:            c02, eq01, recojo dentro de 7 dias a las 18:00, devolucion 3 dias despues a las 09:00.
    Condiciones:        ya existe la renta de C-01 para ese periodo (fechas futuras, para
                        que la reserva no haya vencido).
    Resultado esperado: se lanza EquipmentNotAvailableError con un mensaje que dice
                        el equipo y las fechas ocupadas; en la base sigue habiendo una sola
                        renta (la de C-01, sin cambios) y ninguna de C-02.
    Requisito:          PRE-RF-01 (escenario de rechazo de la Sesion 6) y
                        PRE-RC-01 (el mensaje dice equipo y fechas).
    Codigo que cubre:   rentals/renting.py -> create_rental() y check_equipment_is_free(),
                        que usa rules.periods_overlap().
    """
    # Preparar: C-01 confirma primero
    inicio = dentro_de(7, 18)
    fin = dentro_de(10, 9)
    create_rental(c01, eq01, inicio, fin)

    # Ejecutar: C-02 pide lo mismo
    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(c02, eq01, inicio, fin)

    # Comprobar: el mensaje que vera C-02 (sin "libre hasta": la renta de C-01 empieza a la vez)
    assert str(error.value) == (
        f"El equipo EQ-01 está ocupado del {inicio:%d/%m/%Y %H:%M} al {fin:%d/%m/%Y %H:%M}."
    )

    # Comprobar: la renta de C-01 sigue igual y no se guardo nada para C-02
    unica = Rental.objects.get()
    assert unica.client == c01
    assert unica.start_datetime == inicio
    assert unica.end_datetime == fin
    assert not Rental.objects.filter(client=c02).exists()


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
    c01, c02, eq01, eq02
):
    """La disponibilidad es por UNIDAD, no por modelo.

    Caso:               C-01 tiene EQ-01; C-02 pide EQ-02 (misma mesa, otra unidad) en las mismas fechas.
    Entrada:            c02, eq02, recojo dentro de 7 dias a las 18:00, devolucion 3 dias despues a las 09:00.
    Condiciones:        EQ-01 y EQ-02 tienen la misma descripcion; EQ-01 ya esta reservado en ese periodo.
    Resultado esperado: la renta de C-02 se guarda; hay dos rentas, una por unidad.
    Requisito:          ENT-09 (cada equipo se registra individualmente) y
                        caso limite "dos unidades del mismo modelo" (Sesion 4).
    Codigo que cubre:   rentals/renting.py -> create_rental() (solo mira las rentas de ESA unidad).
    """
    # Preparar
    inicio = dentro_de(7, 18)
    fin = dentro_de(10, 9)
    create_rental(c01, eq01, inicio, fin)

    # Ejecutar
    renta_c02 = create_rental(c02, eq02, inicio, fin)

    # Comprobar
    assert Rental.objects.count() == 2
    assert renta_c02.equipment == eq02
    assert renta_c02.client == c02


def test_el_mismo_equipo_se_puede_rentar_cuando_termina_la_renta_anterior(c01, c02, eq01):
    """Caso limite: una renta que empieza despues de que termina la otra se acepta.

    Caso:               C-01 tiene EQ-01 hasta el dia 10 desde hoy a las 09:00; C-02 lo pide
                        desde ese mismo dia a las 18:00 hasta dos dias despues a las 09:00.
    Entrada:            c02, eq01, recojo dentro de 10 dias a las 18:00, devolucion dentro de 12 dias a las 09:00.
    Condiciones:        los periodos no comparten ningun minuto.
    Resultado esperado: la renta de C-02 se guarda; EQ-01 tiene dos rentas.
    Requisito:          ENT-10 (el equipo queda apartado solo en su periodo) y caso
                        limite del plan de las Sesiones 8 y 9.
    Codigo que cubre:   rentals/renting.py -> create_rental() con rules.periods_overlap().
    """
    # Preparar
    create_rental(c01, eq01, dentro_de(7, 18), dentro_de(10, 9))
    recojo_siguiente = dentro_de(10, 18)
    devolucion_siguiente = dentro_de(12, 9)

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


# ---------- Fechas ocupadas y libres (B1 #47, B2 #48) ----------

def test_si_la_otra_renta_empieza_despues_el_rechazo_dice_hasta_cuando_esta_libre(c01, c02, eq01):
    """Requisito: B1 (#47), ENT-36 y ENT-64, el rechazo dice cuando esta ocupado y hasta cuando esta libre.
    Caso:      C-01 tiene EQ-01 del dia 7 al 10 desde hoy; C-02 lo pide del dia 5 al 8.
    Esperado:  EquipmentNotAvailableError con el periodo ocupado y "libre hasta" el dia 7 a las 09:00; la base queda igual.
    Ejemplo:   pedido del dia 5 18:00 al 8 09:00 -> "ocupado del dia 7 18:00 al 10 09:00. Esta libre hasta el dia 7 a las 09:00."
    """
    # Preparar
    ocupado_desde = dentro_de(7, 18)
    ocupado_hasta = dentro_de(10, 9)
    create_rental(c01, eq01, ocupado_desde, ocupado_hasta)
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(EquipmentNotAvailableError) as error:
        create_rental(c02, eq01, dentro_de(5, 18), dentro_de(8, 9))

    # Comprobar: la respuesta
    assert str(error.value) == (
        f"El equipo EQ-01 está ocupado del {ocupado_desde:%d/%m/%Y %H:%M} "
        f"al {ocupado_hasta:%d/%m/%Y %H:%M}. "
        f"Está libre hasta el {ocupado_desde:%d/%m/%Y} a las 09:00."
    )

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes


def test_una_renta_en_las_fechas_de_una_reserva_cancelada_se_acepta(op01, c01, c02, eq01):
    """Requisito: B2 (#48) y ENT-55, una reserva cancelada deja libres sus fechas.
    Caso:      OP-01 cancelo la reserva de EQ-01 de C-01; C-02 pide EQ-01 en las mismas fechas.
    Esperado:  la renta de C-02 se guarda "Reservada"; la de C-01 sigue "Cancelada".
    Ejemplo:   reserva cancelada del dia 7 al 10 -> C-02 renta EQ-01 del dia 7 al 10.
    """
    # Preparar
    inicio = dentro_de(7, 18)
    fin = dentro_de(10, 9)
    cancelada = cancel_rental(create_rental(c01, eq01, inicio, fin), op01)

    # Ejecutar
    renta_c02 = create_rental(c02, eq01, inicio, fin)

    # Comprobar: la respuesta
    assert renta_c02.status == RentalStatus.RESERVED

    # Comprobar: lo guardado
    assert list(Rental.objects.order_by("pk")) == [cancelada, renta_c02]
    cancelada.refresh_from_db()
    assert cancelada.status == RentalStatus.CANCELLED


# ---------- Cancelar una reserva (B3 #49) ----------

def test_el_operador_cancela_una_reserva_y_guarda_cuando_y_quien(op01, c01, eq01):
    """Requisito: B3 (#49) y ENT-55, cancelar guarda cuando y quien cancelo.
    Caso:      OP-01 cancela la reserva de EQ-01 de C-01, que empieza en 7 dias.
    Esperado:  la renta queda "Cancelada" con cancelled_at y cancelled_by; nada mas cambia.
    Ejemplo:   reserva sin recojo -> cancelled_at = ahora, cancelled_by = op01.
    """
    # Preparar
    reserva = create_rental(c01, eq01, dentro_de(7, 18), dentro_de(10, 9))
    rentas, equipos, historial = foto_de_la_base()
    antes_de_cancelar = timezone.now()

    # Ejecutar
    renta = cancel_rental(reserva, op01)

    # Comprobar: la respuesta
    assert renta.status == RentalStatus.CANCELLED

    # Comprobar: lo guardado (solo cambian los dos campos de la cancelacion)
    reserva.refresh_from_db()
    assert antes_de_cancelar <= reserva.cancelled_at <= timezone.now()
    rentas[0].update(cancelled_at=reserva.cancelled_at, cancelled_by_id=op01.pk)
    assert foto_de_la_base() == (rentas, equipos, historial)


def test_una_renta_ya_entregada_no_se_cancela_y_la_base_queda_igual(op01, c01, eq01):
    """Requisito: B3 (#49), solo se cancela una reserva que todavia no se recogio.
    Caso:      OP-01 ya entrego a C-01 la reserva de EQ-01 e intenta cancelarla.
    Esperado:  RentalStateError con la fecha de la entrega; la base queda igual.
    Ejemplo:   renta entregada hoy -> "La renta de EQ-01 ya fue entregada el <fecha del recojo>."
    """
    # Preparar
    entregada = register_pickup(create_rental(c01, eq01, dentro_de(1, 18), dentro_de(3, 9)), op01)
    recojo = timezone.localtime(entregada.picked_up_at)
    antes = foto_de_la_base()

    # Ejecutar
    with pytest.raises(RentalStateError) as error:
        cancel_rental(entregada, op01)

    # Comprobar: la respuesta
    assert str(error.value) == f"La renta de EQ-01 ya fue entregada el {recojo:%d/%m/%Y %H:%M}."

    # Comprobar: lo guardado
    assert foto_de_la_base() == antes


# ---------- Buscar al cliente en la tienda (B4 #50) ----------

def test_el_operador_encuentra_al_cliente_por_apellido_y_no_al_personal(c01, c02, op01, mt01):
    """Requisito: B4 (#50) y ENT-54, el operador busca al cliente por nombre, apellido o correo.
    Caso:      C-01, OP-01 y MT-01 se apellidan Perez y C-02 Rojas; OP-01 busca "perez".
    Esperado:  solo aparece C-01: el personal no es cliente.
    Ejemplo:   find_clients("perez") -> [c01].
    """
    # Preparar
    for usuario, apellido in [(c01, "Perez"), (c02, "Rojas"), (op01, "Perez"), (mt01, "Perez")]:
        usuario.last_name = apellido
        usuario.save()

    # Ejecutar
    encontrados = find_clients("perez")

    # Comprobar
    assert list(encontrados) == [c01]
