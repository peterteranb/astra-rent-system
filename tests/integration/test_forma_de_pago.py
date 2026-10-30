"""Prueba que la forma de pago sigue visible en el detalle de la renta y en la API, aunque la etiqueta diga
solo «Pagado» (ENT-104)."""
from pytest_django.asserts import assertContains, assertNotContains

from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de


def test_la_renta_pagada_con_qr_dice_pagado_y_la_forma_de_pago_aparte(client, cl01, mes01):
    # cl01 paga con QR y abre su renta y «Mis rentas» por la API -> «Pagado» y, aparte, la forma de pago QR
    renta = pay_with_qr(create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9)), approved=True)
    client.force_login(cl01)

    # Comprueba que el detalle muestra la etiqueta sin el método y la forma de pago en su propia fila
    detalle = client.get(f"/rentals/{renta.pk}/")
    assertContains(detalle, ">Pagado</span>")
    assertNotContains(detalle, "Pagado (QR)")
    assertContains(detalle, "<dt>Forma de pago</dt><dd>QR</dd>", html=True)

    # Comprueba que la API trae payment_label «Pagado» y payment_method «qr» por separado
    [en_la_api] = client.get("/api/my-rentals/").json()["data"]["rentals"]
    assert (en_la_api["payment_label"], en_la_api["payment_method"], en_la_api["payment_method_label"]) == (
        "Pagado", "qr", "QR"
    )
