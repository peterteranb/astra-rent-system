"""Prueba que las listas del personal y del admin empiezan por lo último que pasó y que el operador puede
ordenar por fecha (ENT-100: «lo último es lo primero que veo»)."""
import pytest

from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de


@pytest.mark.parametrize(
    ("orden", "esperado"),
    [("", ["MES-00002", "MES-00001"]), ("date", ["MES-00001", "MES-00002"]), ("precio", ["MES-00002", "MES-00001"])],
)
def test_reservas_por_entregar_empiezan_por_la_mas_reciente_o_por_la_fecha_de_recojo(
    client, cl01, cl02, op01, mes01, mes02, orden, esperado
):
    # cl01 reserva MES-00001 para hoy+2 y después cl02 MES-00002 para hoy+5 -> sin orden o con uno desconocido va primero la última; con «date», la más próxima
    create_rental(cl01, mes01, dentro_de(2, 18), dentro_de(3, 9))
    create_rental(cl02, mes02, dentro_de(5, 18), dentro_de(6, 9))
    client.force_login(op01)
    respuesta = client.get(f"/staff/reservations/?order={orden}")
    assert list(respuesta.context["reservations"].values_list("equipment__inventory_id", flat=True)) == esperado


def test_el_equipo_recien_registrado_aparece_primero_en_el_admin(client, ad01, mes01, mes02):
    # Se registró MES-00001 y después MES-00002 -> la lista de equipos del admin empieza por MES-00002
    client.force_login(ad01)
    respuesta = client.get("/admin/rentals/equipment/")
    assert list(respuesta.context["cl"].result_list) == [mes02, mes01]
