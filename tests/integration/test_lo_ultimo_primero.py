"""Prueba que las listas del personal y del admin empiezan por lo último que pasó y que el operador puede
ordenar por fecha (ENT-100: «lo último es lo primero que veo»)."""
from rentals.use_cases.handover import reservations_to_hand_over
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de


def test_la_reserva_recien_creada_aparece_primero_en_reservas_por_entregar(cl01, cl02, mes01, mes02):
    # cl01 reserva MES-00001 para hoy+2 y después cl02 reserva MES-00002 para hoy+5 -> la de cl02 va primero
    primera = create_rental(cl01, mes01, dentro_de(2, 18), dentro_de(3, 9))
    ultima = create_rental(cl02, mes02, dentro_de(5, 18), dentro_de(6, 9))
    assert list(reservations_to_hand_over()) == [ultima, primera]


def test_ordenar_por_fecha_de_recojo_pone_primero_la_mas_proxima(client, cl01, cl02, op01, mes01, mes02):
    # Las mismas dos reservas y op01 elige «Fecha de recojo» -> la de hoy+2 va primero
    primera = create_rental(cl01, mes01, dentro_de(2, 18), dentro_de(3, 9))
    ultima = create_rental(cl02, mes02, dentro_de(5, 18), dentro_de(6, 9))
    client.force_login(op01)
    respuesta = client.get("/staff/reservations/?order=date")
    assert list(respuesta.context["reservations"]) == [primera, ultima]


def test_un_orden_desconocido_muestra_los_mas_recientes(client, cl01, cl02, op01, mes01, mes02):
    # op01 abre la lista con ?order=precio, que no existe -> ve el orden por defecto, la más nueva primero
    primera = create_rental(cl01, mes01, dentro_de(2, 18), dentro_de(3, 9))
    ultima = create_rental(cl02, mes02, dentro_de(5, 18), dentro_de(6, 9))
    client.force_login(op01)
    respuesta = client.get("/staff/reservations/?order=precio")
    assert list(respuesta.context["reservations"]) == [ultima, primera]


def test_el_equipo_recien_registrado_aparece_primero_en_el_admin(client, ad01, mes01, mes02):
    # Se registró MES-00001 y después MES-00002 -> la lista de equipos del admin empieza por MES-00002
    client.force_login(ad01)
    respuesta = client.get("/admin/rentals/equipment/")
    assert list(respuesta.context["cl"].result_list) == [mes02, mes01]
