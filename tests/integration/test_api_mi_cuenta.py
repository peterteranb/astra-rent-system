"""Prueba la API de «Mi cuenta» en accounts/api.py: editar mis datos, cambiar la contraseña, pedir el enlace y
crear un cliente en la tienda sin contraseña (CU-02, CU-17)."""
from django.contrib.auth import get_user_model
from django.core import mail

from tests.conftest import DEMO_PASSWORD
from tests.helpers import foto_de_la_base

JSON = "application/json"


def test_la_api_de_mi_cuenta_guarda_datos_cuida_la_contrasena_y_crea_clientes_sin_contrasena(client, cl01, op01):
    # cl01 edita sus datos, prueba una contraseña común y pide el enlace; op01 crea a Lucía sin contraseña -> cada respuesta con su efecto
    # Comprueba que cl01 guarda su apellido nuevo y recibe 200 con sus datos y el aviso
    client.force_login(cl01)
    datos = {"first_name": "Carla", "last_name": "Mendoza Ríos", "email": "cl01@correo.com", "phone": "71000001"}
    perfil = client.post("/api/auth/profile/", datos, content_type=JSON)
    assert (perfil.status_code, perfil.json()["data"]["last_name"], perfil.json()["message"]) == (
        200, "Mendoza Ríos", "Tus datos se guardaron."
    )
    assert get_user_model().objects.get(username="cl01").last_name == "Mendoza Ríos"

    # Comprueba que «Password1», muy común, se rechaza con 400 y la contraseña sigue igual
    antes = foto_de_la_base()
    comun = {"old_password": DEMO_PASSWORD, "new_password1": "Password1", "new_password2": "Password1"}
    rechazo = client.post("/api/auth/password/", comun, content_type=JSON)
    assert (rechazo.status_code, "Esta contraseña es demasiado común." in str(rechazo.json()["errors"])) == (400, True)
    assert foto_de_la_base() == antes

    # Comprueba que pedir el enlace responde el mensaje de siempre, sin decir si la cuenta existe, y sale un correo
    client.logout()
    enlace = client.post("/api/auth/password-reset/", {"email": "cl01@correo.com"}, content_type=JSON)
    assert (enlace.status_code, enlace.json()["message"], len(mail.outbox)) == (
        200, "Si el correo es de una cuenta activa, te mandamos un enlace para crear tu contraseña.", 1
    )

    # Comprueba que op01 crea a Lucía por la API con 201, email_sent true y la cuenta sin contraseña utilizable
    client.force_login(op01)
    lucia = {"first_name": "Lucía", "last_name": "Quispe", "email": "lucia@correo.com", "phone": "71234567", "username": "cl03"}
    alta = client.post("/api/staff/clients/", lucia, content_type=JSON)
    assert (alta.status_code, alta.json()["data"]["email_sent"]) == (201, True)
    assert get_user_model().objects.get(username="cl03").has_usable_password() is False
