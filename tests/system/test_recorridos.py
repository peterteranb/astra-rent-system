"""Pruebas de sistema: recorridos completos por la web con el cliente de pruebas de Django,
desde la petición hasta lo guardado (CU-01 a CU-07)."""
from pytest_django.asserts import assertContains, assertRedirects

from rentals.models import Rental, StatusChange
from rentals.renting import create_rental
from rentals.statuses import EquipmentStatus, RentalStatus
from tests.helpers import dentro_de, foto_de_la_base


def periodo(inicio, fin):
    """Datos del formulario de renta para un periodo, como los envía el navegador."""
    return {
        "start_date": f"{inicio:%Y-%m-%d}",
        "start_time": f"{inicio:%H:%M}",
        "end_date": f"{fin:%Y-%m-%d}",
        "end_time": f"{fin:%H:%M}",
    }


def test_ciclo_completo_de_una_renta(client, cl01, op01, mt01, mes01):
    # cl01 renta y paga MES-00001 -> op01 lo entrega -> op01 lo recibe con nota -> mt01 lo deja disponible -> cl01 lo ve libre
    client.force_login(cl01)
    renta_pedida = client.post("/equipment/MES-00001/rent/", periodo(dentro_de(1, 18), dentro_de(2, 9)))
    renta = Rental.objects.get()
    pago = client.post(f"/rentals/{renta.pk}/pay/", {"result": "approved"}, follow=True)
    client.force_login(op01)
    entrega = client.post(f"/staff/reservations/{renta.pk}/pickup/", follow=True)
    devolucion = client.post(f"/staff/returns/{renta.pk}/", {"note": "Pata floja"}, follow=True)
    client.force_login(mt01)
    revision = client.post("/maintenance/MES-00001/", {"status": EquipmentStatus.AVAILABLE, "comment": ""}, follow=True)
    client.force_login(cl01)
    catalogo = client.get("/")
    # Comprueba que el cliente llegó a la pantalla del QR
    assertRedirects(renta_pedida, f"/rentals/{renta.pk}/pay/")
    # Comprueba que el cliente vio su pago recibido
    assertContains(pago, "Pago recibido. Tu renta está confirmada.")
    # Comprueba que el operador vio el recojo registrado
    assertContains(entrega, "Recojo registrado: MES-00001 entregado a cl01.")
    # Comprueba que el operador vio la devolución registrada
    assertContains(devolucion, "Devolución registrada: MES-00001 recibido de cl01.")
    # Comprueba que mantenimiento vio el estado nuevo
    assertContains(revision, "MES-00001 ahora está «Disponible».")
    # Comprueba que el cliente ve MES-00001 libre en el catálogo
    assertContains(catalogo, "Libre")
    # Comprueba que la renta quedó devuelta y el historial tiene la ida a revisión y la vuelta a disponible
    assert (Rental.objects.get().status, StatusChange.objects.count()) == (RentalStatus.RETURNED, 2)


def test_un_pago_qr_fallido_deja_la_reserva_y_avisa_que_se_paga_en_la_tienda(client, cl01, mes01):
    # cl01 renta MES-00001 y el QR falla -> ve que paga al recoger y la reserva queda con el pago pendiente (ENT-67)
    client.force_login(cl01)
    client.post("/equipment/MES-00001/rent/", periodo(dentro_de(1, 18), dentro_de(2, 9)))
    renta = Rental.objects.get()
    respuesta = client.post(f"/rentals/{renta.pk}/pay/", {"result": "failed"}, follow=True)
    renta.refresh_from_db()
    # Comprueba el aviso al cliente
    assertContains(respuesta, "Tu reserva está hecha, pero el pago no se completó. Paga en la tienda al recoger el equipo.")
    # Comprueba que la reserva sigue hecha y sin pagar
    assert (renta.status, renta.paid_at) == (RentalStatus.RESERVED, None)


def test_el_cliente_cancela_desde_mis_rentas_y_no_puede_cancelar_la_de_otro(client, cl01, cl02, mes01, mes02):
    # cl01 cancela su reserva desde «Mis rentas» e intenta cancelar la de cl02 -> la suya se cancela y la otra da 404
    propia = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    ajena = create_rental(cl02, mes02, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(cl01)
    respuesta = client.post(f"/rentals/{propia.pk}/cancel/", follow=True)
    intento = client.post(f"/rentals/{ajena.pk}/cancel/")
    ajena.refresh_from_db()
    # Comprueba que volvió a «Mis rentas» con el aviso
    assertContains(respuesta, "Reserva cancelada: MES-00001 de cl01.")
    # Comprueba que la reserva ajena no existe para cl01 y sigue reservada
    assert (intento.status_code, ajena.status) == (404, RentalStatus.RESERVED)


def test_un_rechazo_por_fechas_ocupadas_se_ve_en_el_catalogo(client, cl01, cl02, mes01):
    # cl01 ya tiene MES-00001 y cl02 pide las mismas fechas -> vuelve al catálogo con «ocupado del» y nada se guarda
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    antes = foto_de_la_base()
    client.force_login(cl02)
    respuesta = client.post("/equipment/MES-00001/rent/", periodo(dentro_de(7, 18), dentro_de(9, 9)), follow=True)
    # Comprueba que volvió al catálogo
    assert respuesta.redirect_chain == [("/", 302)]
    # Comprueba que ve la causa del rechazo
    assertContains(respuesta, "El equipo MES-00001 está ocupado del")
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_renta_en_tienda_de_un_cliente_que_se_lo_lleva_ahora(client, cl02, op01, mes01):
    # op01 busca «rojas», elige a Diego Rojas y marca «Se lo lleva ahora» -> ve «Registrada por» y la renta nace rentada
    client.force_login(op01)
    busqueda = client.get("/staff/walk-in/?q=rojas")
    datos = {"client": cl02.pk, "equipment": "MES-00001", "takes_it_now": "on", **periodo(dentro_de(0, 18), dentro_de(2, 9))}
    respuesta = client.post("/staff/walk-in/?q=rojas", datos, follow=True)
    renta = Rental.objects.get()
    # Comprueba que la búsqueda encontró al cliente por su apellido
    assertContains(busqueda, "Diego Rojas")
    # Comprueba que la confirmación dice quién la registró
    assertContains(respuesta, "Registrada por")
    # Comprueba que el operador puede volver a registrar otra renta en tienda
    assertContains(respuesta, "Nueva renta en tienda")
    # Comprueba que se guardó rentada a nombre de cl02 y registrada por op01
    assert (renta.status, renta.client, renta.registered_by) == (RentalStatus.RENTED, cl02, op01)


def test_el_admin_cancela_manda_a_reparacion_y_no_agrega_rentas(client, ad01, cl01, mes01, mes02):
    # ad01 cancela una reserva y manda MES-00002 a reparación desde el admin -> se guardan con su usuario y no puede agregar rentas
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(ad01)
    cancelacion = client.post(
        "/admin/rentals/rental/", {"action": "cancel_reservations", "_selected_action": [reserva.pk]}, follow=True
    )
    reparacion = client.post(
        "/admin/rentals/equipment/", {"action": "send_to_repair", "_selected_action": [mes02.pk]}, follow=True
    )
    agregar = client.get("/admin/rentals/rental/add/")
    reserva.refresh_from_db()
    cambio = StatusChange.objects.get()
    # Comprueba el aviso de la cancelación
    assertContains(cancelacion, "Reservas canceladas: 1.")
    # Comprueba que la reserva quedó cancelada por ad01
    assert (reserva.status, reserva.cancelled_by) == (RentalStatus.CANCELLED, ad01)
    # Comprueba el aviso del cambio de estado
    assertContains(reparacion, "Equipos actualizados: 1.")
    # Comprueba la fila de historial de MES-00002 con ad01
    assert (cambio.equipment, cambio.new_status, cambio.changed_by) == (mes02, EquipmentStatus.IN_REPAIR, ad01)
    # Comprueba que el admin no puede crear rentas a mano (RF-09)
    assert agregar.status_code == 403
