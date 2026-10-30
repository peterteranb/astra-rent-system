"""Prueba que la forma de pago sigue visible en el detalle de la renta y en la API, aunque la etiqueta diga
solo «Pagado» (ENT-104)."""
from pytest_django.asserts import assertContains, assertNotContains

from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de


def test_el_detalle_de_una_renta_pagada_con_qr_muestra_la_forma_de_pago(client, cl01, mes01):
    # cl01 paga con QR y abre su renta -> ve «Pagado» y, aparte, «Forma de pago» QR
    renta = pay_with_qr(create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9)), approved=True)
    client.force_login(cl01)
    respuesta = client.get(f"/rentals/{renta.pk}/")
    # Comprueba la etiqueta sin el método
    assertContains(respuesta, ">Pagado</span>")
    assertNotContains(respuesta, "Pagado (QR)")
    # Comprueba la forma de pago en el detalle
    assertContains(respuesta, "<dt>Forma de pago</dt><dd>QR</dd>", html=True)


def test_la_api_de_mis_rentas_trae_la_etiqueta_y_la_forma_de_pago_aparte(client, cl01, mes01):
    # cl01 paga con QR y pide «Mis rentas» por la API -> payment_label «Pagado» y payment_method «qr»
    pay_with_qr(create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9)), approved=True)
    client.force_login(cl01)
    [renta] = client.get("/api/my-rentals/").json()["data"]["rentals"]
    assert (renta["payment_label"], renta["payment_method"], renta["payment_method_label"]) == ("Pagado", "qr", "QR")
