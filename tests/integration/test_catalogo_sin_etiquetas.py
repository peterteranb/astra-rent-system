"""Prueba el catálogo de la página y de la API sin las etiquetas «Libre» ni «Ocupado del … al …» (CU-03, ENT-99:
a quien renta no le interesa cuándo usan el equipo otras personas)."""
from pytest_django.asserts import assertContains, assertNotContains

from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de


def test_sin_fechas_el_catalogo_muestra_el_equipo_reservado_sin_etiquetas(client, cl01, cl02, mes01):
    # MES-00001 está reservada por cl01 y cl02 abre el catálogo sin fechas -> la ve para rentar, sin «Ocupado» ni «Libre»
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(cl02)
    respuesta = client.get("/")
    # Comprueba que el equipo aparece con su botón para rentar
    assertContains(respuesta, "/equipment/MES-00001/rent/")
    # Comprueba que no dice cuándo lo usan otros
    assertNotContains(respuesta, "Ocupado")
    assertNotContains(respuesta, "Libre</span>")


def test_la_api_del_catalogo_no_trae_los_periodos_ocupados(client, cl01, cl02, mes01):
    # MES-00001 está reservada por cl01 y cl02 pide el catálogo por la API -> el equipo viene sin busy_periods
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(cl02)
    [equipo] = client.get("/api/catalog/").json()["data"]["results"]
    assert equipo == {
        "inventory_id": "MES-00001",
        "name": "Mesa plegable 1,80 m",
        "status": "available",
        "status_label": "Disponible",
        "daily_price": "20.00",
    }
