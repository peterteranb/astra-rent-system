"""Prueba la API JSON de rentals/api/ y accounts/api.py: el código HTTP, el formato
{"data", "message"} o {"errors"} y un rechazo con el mismo mensaje de las páginas, por grupo."""
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


def test_la_sesion_pide_el_token_csrf_y_luego_inicia(cl01):
    # cl01 intenta el login sin token -> 403; pide /api/csrf/, lo manda en X-CSRFToken -> entra y /me/ dice su rol
    navegador = Client(enforce_csrf_checks=True)
    credenciales = {"username": "cl01", "password": DEMO_PASSWORD}
    sin_token = navegador.post("/api/auth/login/", credenciales, content_type=JSON)
    token = navegador.get("/api/csrf/").json()["data"]["csrf_token"]
    entrada = navegador.post("/api/auth/login/", credenciales, content_type=JSON, headers={"X-CSRFToken": token})
    yo = navegador.get("/api/auth/me/")
    # Comprueba el rechazo sin token, en JSON y en español
    assert (sin_token.status_code, sin_token.json()) == (
        403, {"errors": ["La sesión de seguridad venció. Recarga la página e inténtalo de nuevo."]}
    )
    # Comprueba que el login con el token entró
    assert (entrada.status_code, entrada.json()["message"]) == (200, "Hola, Carla.")
    # Comprueba quién es, su rol y su deuda como texto con dos decimales
    assert (yo.json()["data"]["username"], yo.json()["data"]["role"], yo.json()["data"]["debt_total"]) == (
        "cl01", "cliente", "0.00"
    )


def test_un_login_incorrecto_responde_400_y_sin_sesion_401(client, cl01):
    # cl01 se equivoca de contraseña -> 400 con el mensaje de la página; sin sesión, /me/ responde 401
    respuesta = client.post("/api/auth/login/", {"username": "cl01", "password": "equivocada"}, content_type=JSON)
    yo = client.get("/api/auth/me/")
    # Comprueba el rechazo con el mismo texto que la página de login
    assert (respuesta.status_code, respuesta.json()) == (400, {"errors": ["Usuario o contraseña incorrectos."]})
    # Comprueba que sin sesión responde 401 en JSON
    assert (yo.status_code, yo.json()) == (401, {"errors": ["Inicia sesión para continuar."]})


def test_el_cliente_reserva_por_la_api_y_las_fechas_ocupadas_se_rechazan(client, cl01, cl02, mes01):
    # cl01 reserva MES-00001 -> 201 «Reservada»; cl02 pide las mismas fechas -> 400 con el mismo mensaje y nada se guarda
    inicio, fin = dentro_de(7, 18), dentro_de(9, 9)
    client.force_login(cl01)
    reserva = client.post("/api/rentals/", {"equipment": "MES-00001", **periodo(inicio, fin)}, content_type=JSON)
    client.force_login(cl02)
    antes = foto_de_la_base()
    rechazo = client.post("/api/rentals/", {"equipment": "MES-00001", **periodo(inicio, fin)}, content_type=JSON)
    # Comprueba la reserva: 201, estado, fechas ISO con zona y total con dos decimales
    assert (reserva.status_code, reserva.json()["data"]["status"]) == (201, RentalStatus.RESERVED)
    assert (reserva.json()["data"]["start"], reserva.json()["data"]["total_price"]) == (inicio.isoformat(), "40.00")
    # Comprueba el rechazo con la causa
    assert (rechazo.status_code, rechazo.json()) == (
        400, {"errors": [f"El equipo MES-00001 está ocupado del {inicio:%d/%m/%Y %H:%M} al {fin:%d/%m/%Y %H:%M}."]}
    )
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_el_cliente_no_puede_pagar_la_reserva_de_otro(client, cl01, cl02, mes01):
    # cl02 intenta pagar la reserva de cl01 -> 404 en JSON, sin decir que existe, y la renta sigue sin pagar
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    client.force_login(cl02)
    antes = foto_de_la_base()
    respuesta = client.post(f"/api/rentals/{renta.pk}/pay/", {"approved": True}, content_type=JSON)
    # Comprueba el 404 en JSON y en español
    assert (respuesta.status_code, respuesta.json()) == (404, {"errors": ["No encontramos lo que buscas."]})
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_el_operador_entrega_cobrando_y_sin_cobrar_se_rechaza(client, cl01, op01, mes01):
    # Reserva de hoy con el pago pendiente: sin paid_now -> 400 y nada cambia; con paid_now -> 200 con el cobro
    renta = create_rental(cl01, mes01, dentro_de(0, 18), dentro_de(2, 9))
    client.force_login(op01)
    lista = client.get("/api/staff/reservations/")
    antes = foto_de_la_base()
    rechazo = client.post(f"/api/staff/rentals/{renta.pk}/pickup/", {}, content_type=JSON)
    despues_del_rechazo = foto_de_la_base()
    entrega = client.post(f"/api/staff/rentals/{renta.pk}/pickup/", {"paid_now": True}, content_type=JSON)
    # Comprueba que la reserva aparece en la lista
    assert [fila["id"] for fila in lista.json()["data"]] == [renta.pk]
    # Comprueba el rechazo con el monto y que la base quedó igual
    assert (rechazo.status_code, rechazo.json()["errors"]) == (
        400, ["Falta el pago de 40,00 Bs de esta renta. Cóbralo en efectivo o cancela la reserva si el cliente no paga."]
    )
    assert despues_del_rechazo == antes
    # Comprueba la entrega con el mensaje de la página y la renta rentada
    assert (entrega.status_code, entrega.json()["message"]) == (
        200, "Cobro de 40,00 Bs en efectivo y recojo registrados: MES-00001 entregado a cl01."
    )
    assert Rental.objects.get().status == RentalStatus.RENTED


def test_un_cliente_recibe_403_en_la_api_del_operador(client, cl01):
    # cl01 pide la lista de reservas del operador -> 403 en JSON
    client.force_login(cl01)
    respuesta = client.get("/api/staff/reservations/")
    # Comprueba el 403 en JSON y en español
    assert (respuesta.status_code, respuesta.json()) == (403, {"errors": ["No tienes permiso para hacer esto."]})


def test_mantenimiento_revisa_por_la_api_y_un_estado_invalido_se_rechaza(client, mt01, mes03_en_revision):
    # mt01 manda MES-00003 a «reservado» -> 400 y nada cambia; luego lo deja disponible -> 200 con el mensaje
    client.force_login(mt01)
    lista = client.get("/api/maintenance/equipment/")
    antes = foto_de_la_base()
    rechazo = client.post("/api/maintenance/equipment/MES-00003/review/", {"status": "reserved"}, content_type=JSON)
    despues_del_rechazo = foto_de_la_base()
    revision = client.post(
        "/api/maintenance/equipment/MES-00003/review/", {"status": EquipmentStatus.AVAILABLE}, content_type=JSON
    )
    # Comprueba que la lista trae el equipo con su estado
    assert [(fila["inventory_id"], fila["status"]) for fila in lista.json()["data"]] == [
        ("MES-00003", EquipmentStatus.IN_REVIEW)
    ]
    # Comprueba el rechazo con la causa y que la base quedó igual
    assert (rechazo.status_code, rechazo.json()["errors"]) == (
        400, ["El equipo MES-00003 solo puede pasar a disponible, en reparación o baja."]
    )
    assert despues_del_rechazo == antes
    # Comprueba el mensaje y el estado guardado
    assert (revision.status_code, revision.json()["message"]) == (200, "MES-00003 ahora está «Disponible».")
    assert Equipment.objects.get().status == EquipmentStatus.AVAILABLE


def test_el_admin_registra_un_equipo_y_un_codigo_invalido_se_rechaza(client, ad01):
    # ad01 registra MES-00021 -> 201; con el código «MESA-1» -> 400 con la causa y no se guarda
    client.force_login(ad01)
    alta = client.post(
        "/api/admin/equipment/",
        {"inventory_id": "mes-00021", "serial_number": "SN-21", "name": "Mesa plegable", "value": "400.00"},
        content_type=JSON,
    )
    antes = foto_de_la_base()
    rechazo = client.post(
        "/api/admin/equipment/",
        {"inventory_id": "MESA-1", "serial_number": "SN-22", "name": "Mesa plegable", "value": "400.00"},
        content_type=JSON,
    )
    panel = client.get("/api/manager/dashboard/")
    # Comprueba el alta con el código en mayúsculas y el precio por día
    assert (alta.status_code, alta.json()["data"]["inventory_id"], alta.json()["data"]["daily_price"]) == (
        201, "MES-00021", "20.00"
    )
    # Comprueba el rechazo con la causa y que la base quedó igual
    assert (rechazo.status_code, rechazo.json()["errors"]) == (
        400, ["El código debe tener 3 letras, un guion y 5 números, por ejemplo MES-00001."]
    )
    assert foto_de_la_base() == antes
    # Comprueba que el panel responde con la deuda total como texto
    assert (panel.status_code, panel.json()["data"]["debt_total"]) == (200, "0.00")
