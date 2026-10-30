"""Prueba el catálogo de la página y de la API sin las etiquetas «Libre» ni «Ocupado del … al …» (CU-03, ENT-99:
a quien renta no le interesa cuándo usan el equipo otras personas)."""
from pytest_django.asserts import assertContains, assertNotContains

from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de


def test_el_catalogo_muestra_el_equipo_reservado_sin_decir_cuando_lo_usan_otros(client, cl01, cl02, mes01):
    # MES-00001 está reservada por cl01 y cl02 abre el catálogo sin fechas, en la página y por la API -> la ve para rentar, sin etiquetas
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(cl02)

    # Comprueba que la página muestra el botón para rentar, sin «Ocupado» ni «Libre»
    respuesta = client.get("/")
    assertContains(respuesta, "/equipment/MES-00001/rent/")
    assertNotContains(respuesta, "Ocupado")
    assertNotContains(respuesta, "Libre</span>")

    # Comprueba que la API trae el equipo sin busy_periods
    [equipo] = client.get("/api/catalog/").json()["data"]["results"]
    assert equipo == {
        "inventory_id": "MES-00001",
        "name": "Mesa plegable 1,80 m",
        "status": "available",
        "status_label": "Disponible",
        "daily_price": "20.00",
    }
