"""Prueba la API de «Mi cuenta» en accounts/api.py: editar mis datos, cambiar la contraseña, pedir el enlace y
crear un cliente en la tienda sin contraseña (CU-02, CU-17)."""
from django.contrib.auth import get_user_model
from django.core import mail

from tests.conftest import DEMO_PASSWORD
from tests.helpers import foto_de_la_base

JSON = "application/json"


def test_la_api_guarda_mis_datos_y_devuelve_quien_soy(client, cl01):
    # cl01 manda su apellido nuevo -> 200 con sus datos nuevos y el aviso
    client.force_login(cl01)
    datos = {"first_name": "Carla", "last_name": "Mendoza Ríos", "email": "cl01@correo.com", "phone": "71000001"}
    respuesta = client.post("/api/auth/profile/", datos, content_type=JSON)
    # Comprueba la respuesta
    assert (respuesta.status_code, respuesta.json()["data"]["last_name"], respuesta.json()["message"]) == (
        200, "Mendoza Ríos", "Tus datos se guardaron."
    )
    # Comprueba lo guardado
    assert get_user_model().objects.get(username="cl01").last_name == "Mendoza Ríos"


def test_la_api_rechaza_una_contrasena_nueva_comun_y_no_cambia_nada(client, cl01):
    # cl01 elige «Password1», que es muy común -> 400 con la causa y la contraseña sigue igual
    client.force_login(cl01)
    antes = foto_de_la_base()
    datos = {"old_password": DEMO_PASSWORD, "new_password1": "Password1", "new_password2": "Password1"}
    respuesta = client.post("/api/auth/password/", datos, content_type=JSON)
    # Comprueba el rechazo con la causa
    assert (respuesta.status_code, "Esta contraseña es demasiado común." in str(respuesta.json()["errors"])) == (
        400, True
    )
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_la_api_pide_el_enlace_sin_decir_si_la_cuenta_existe(client, cl01):
    # Se pide el enlace para cl01 -> 200 con el mensaje de siempre y sale un correo
    respuesta = client.post("/api/auth/password-reset/", {"email": "cl01@correo.com"}, content_type=JSON)
    assert (respuesta.status_code, respuesta.json()["message"], len(mail.outbox)) == (
        200, "Si el correo es de una cuenta activa, te mandamos un enlace para crear tu contraseña.", 1
    )


def test_la_api_de_la_tienda_crea_al_cliente_sin_contrasena(client, op01):
    # op01 crea a Lucía por la API sin contraseña -> 201, email_sent true y la cuenta sin contraseña utilizable
    client.force_login(op01)
    datos = {"first_name": "Lucía", "last_name": "Quispe", "email": "lucia@correo.com", "phone": "71234567", "username": "cl03"}
    respuesta = client.post("/api/staff/clients/", datos, content_type=JSON)
    # Comprueba la respuesta
    assert (respuesta.status_code, respuesta.json()["data"]["email_sent"]) == (201, True)
    # Comprueba lo guardado
    assert get_user_model().objects.get(username="cl03").has_usable_password() is False
