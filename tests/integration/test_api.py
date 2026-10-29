"""Prueba la API JSON de rentals/api/ y accounts/api.py: códigos HTTP, formato de respuestas y validación de permisos."""
from django.test import Client

from rentals.models import Equipment, Rental
from rentals.statuses import EquipmentStatus, RentalStatus
from rentals.use_cases.renting import create_rental
from tests.conftest import DEMO_PASSWORD
from tests.helpers import dentro_de, foto_de_la_base

JSON = "application/json"


def periodo(inicio, fin):
    """Fechas y horas de una renta como las manda el frontend."""
    return {
        "start_date": f"{inicio:%Y-%m-%d}",
        "start_time": f"{inicio:%H:%M}",
        "end_date": f"{fin:%Y-%m-%d}",
        "end_time": f"{fin:%H:%M}",
    }


def test_autenticacion_csrf_sesion_y_respuestas_de_perfil_en_api(client, cl01):
    # Solicitud sin token CSRF rechaza con 403; con token válido permite login y consulta del rol y deudas en /me/
    # Comprueba que la petición sin token de seguridad recibe un error 403 en formato JSON
    navegador = Client(enforce_csrf_checks=True)
    credenciales = {"username": "cl01", "password": DEMO_PASSWORD}
    sin_token = navegador.post("/api/auth/login/", credenciales, content_type=JSON)
    assert (sin_token.status_code, sin_token.json()) == (
        403, {"errors": ["La sesión de seguridad venció. Recarga la página e inténtalo de nuevo."]}
    )

    # Comprueba que al proveer el token CSRF la autenticación es exitosa y /me/ devuelve el rol y datos correctos
    token = navegador.get("/api/csrf/").json()["data"]["csrf_token"]
    entrada = navegador.post("/api/auth/login/", credenciales, content_type=JSON, headers={"X-CSRFToken": token})
    yo = navegador.get("/api/auth/me/")
    assert (entrada.status_code, entrada.json()["message"]) == (200, "Hola, Carla.")
    assert (yo.json()["data"]["username"], yo.json()["data"]["role"], yo.json()["data"]["debt_total"]) == (
        "cl01", "cliente", "0.00"
    )

    # Credenciales incorrectas responden 400 y consultas sin sesión devuelven 401 en JSON
    # Comprueba que un error de clave responde 400 y consultar sin sesión responde 401 estructurado
    respuesta_mal = client.post("/api/auth/login/", {"username": "cl01", "password": "equivocada"}, content_type=JSON)
    yo_sin_sesion = client.get("/api/auth/me/")
    assert (respuesta_mal.status_code, respuesta_mal.json()) == (400, {"errors": ["Usuario o contraseña incorrectos."]})
    assert (yo_sin_sesion.status_code, yo_sin_sesion.json()) == (401, {"errors": ["Inicia sesión para continuar."]})


def test_operaciones_de_rentas_pagos_y_mantenimiento_por_api(client, cl01, cl02, op01, mt01, ad01, mes01, mes03_en_revision):
    # Cliente reserva por API (201); solapamiento posterior rechaza con 400; cliente ajeno recibe 404 al intentar pagar otra reserva
    # Comprueba la creación exitosa de una reserva vía API y el rechazo por fechas ocupadas con el mensaje exacto
    inicio, fin = dentro_de(7, 18), dentro_de(9, 9)
    client.force_login(cl01)
    reserva = client.post("/api/rentals/", {"equipment": "MES-00001", **periodo(inicio, fin)}, content_type=JSON)
    assert (reserva.status_code, reserva.json()["data"]["status"]) == (201, RentalStatus.RESERVED)

    client.force_login(cl02)
    antes = foto_de_la_base()
    rechazo = client.post("/api/rentals/", {"equipment": "MES-00001", **periodo(inicio, fin)}, content_type=JSON)
    assert (rechazo.status_code, rechazo.json()) == (
        400, {"errors": [f"El equipo MES-00001 está ocupado del {inicio:%d/%m/%Y %H:%M} al {fin:%d/%m/%Y %H:%M}."]}
    )
    assert foto_de_la_base() == antes

    # Comprueba que intentar pagar la reserva de otro usuario devuelve 404 en JSON sin filtrar información
    renta_cl01 = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(cl02)
    respuesta_ajena = client.post(f"/api/rentals/{renta_cl01.pk}/pay/", {"approved": True}, content_type=JSON)
    assert (respuesta_ajena.status_code, respuesta_ajena.json()) == (404, {"errors": ["No encontramos lo que buscas."]})

    # Operador entrega exigiendo cobro pendiente (400 si falta, 200 con paid_now); cliente recibe 403 en rutas de operador
    # Comprueba que el operador no puede entregar sin cobrar el pendiente y que al marcar paid_now se procesa con éxito
    renta_tienda = create_rental(cl01, mes01, dentro_de(0, 18), within_fin := dentro_de(2, 9)) if False else create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(2, 9))
    client.force_login(op01)
    rechazo_pago = client.post(f"/api/staff/rentals/{renta_tienda.pk}/pickup/", {}, content_type=JSON)
    assert (rechazo_pago.status_code, rechazo_pago.json()["errors"]) == (
        400, ["Falta el pago de 40,00 Bs de esta renta. Cóbralo en efectivo o cancela la reserva si el cliente no paga."]
    )

    entrega_ok = client.post(f"/api/staff/rentals/{renta_tienda.pk}/pickup/", {"paid_now": True}, content_type=JSON)
    assert (entrega_ok.status_code, entrega_ok.json()["message"]) == (
        200, "Cobro de 40,00 Bs en efectivo y recojo registrados: MES-00001 entregado a cl01."
    )

    # Comprueba que un cliente recibe 403 al intentar consultar endpoints exclusivos del operador
    client.force_login(cl01)
    assert client.get("/api/staff/reservations/").status_code == 403

    # Mantenimiento revisa equipos por API; admin registra equipos validando formatos incorrectos
    # Comprueba que mantenimiento actualiza estados correctamente y rechaza transiciones inválidas con 400
    client.force_login(mt01)
    rechazo_rev = client.post("/api/maintenance/equipment/MES-00003/review/", {"status": "reserved"}, content_type=JSON)
    assert (rechazo_rev.status_code, rechazo_rev.json()["errors"]) == (
        400, ["El equipo MES-00003 solo puede pasar a disponible, en revisión, en reparación o baja."]
    )

    revision_ok = client.post(
        "/api/maintenance/equipment/MES-00003/review/", {"status": EquipmentStatus.AVAILABLE}, content_type=JSON
    )
    assert (revision_ok.status_code, revision_ok.json()["message"]) == (200, "MES-00003 ahora está «Disponible».")

    # Comprueba que el administrador registra equipos correctamente y rechaza códigos con formato inválido con 400
    client.force_login(ad01)
    alta_eq = client.post(
        "/api/admin/equipment/",
        {"inventory_id": "mes-00021", "serial_number": "SN-21", "name": "Mesa plegable", "value": "400.00"},
        content_type=JSON,
    )
    assert (alta_eq.status_code, alta_eq.json()["data"]["inventory_id"]) == (201, "MES-00021")

    rechazo_eq = client.post(
        "/api/admin/equipment/",
        {"inventory_id": "MESA-1", "serial_number": "SN-22", "name": "Mesa plegable", "value": "400.00"},
        content_type=JSON,
    )
    assert (rechazo_eq.status_code, rechazo_eq.json()["errors"]) == (
        400, ["El código debe tener 3 letras, un guion y 5 números, por ejemplo MES-00001."]
    )