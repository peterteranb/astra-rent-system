"""Prueba accounts/account.py y las páginas de «Mi cuenta»: editar mis datos con las reglas del registro y
cambiar la contraseña con la vista de Django (CU-17, ENT-103)."""
import pytest
from django.contrib.auth import get_user_model
from pytest_django.asserts import assertContains, assertRedirects

from accounts.account import update_profile
from rentals.errors import RegistrationRejectedError
from tests.conftest import DEMO_PASSWORD
from tests.helpers import foto_de_la_base


@pytest.mark.parametrize(
    ("correo", "telefono", "campo", "guardado"),
    [("cl01@correo.com", "7999-0001", "phone", "79990001"), ("CL01@correo.com", "71000001", "email", "CL01@correo.com")],
)
def test_editar_mis_datos_guarda_el_cambio_y_el_log_dice_solo_el_campo(cl01, caplog, correo, telefono, campo, guardado):
    # cl01 cambia su teléfono, o escribe su mismo correo en mayúsculas (no choca con su cuenta) -> se guarda y el log nombra solo el campo
    update_profile(cl01, "Carla", "Mendoza", correo, telefono)
    # Comprueba lo guardado
    assert getattr(get_user_model().objects.get(username="cl01"), campo) == guardado
    # Comprueba la línea del log, sin el valor nuevo
    assert caplog.messages == [f'PROFILE_UPDATED user=cl01 "Carla Mendoza" fields={campo} by=cl01']


def test_el_correo_de_otra_cuenta_y_un_nombre_vacio_se_rechazan_sin_guardar(cl01, cl02):
    # cl01 deja el nombre vacío y pone el correo de cl02 -> las dos causas juntas y nada cambia
    antes = foto_de_la_base()
    with pytest.raises(RegistrationRejectedError) as error:
        update_profile(cl01, "", "Mendoza", "cl02@correo.com", "71000001")
    # Comprueba las causas
    assert error.value.causes == ["Falta el campo Nombre.", "El correo ya está registrado."]
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_la_pagina_mi_cuenta_guarda_el_apellido_y_no_deja_cambiar_el_usuario(client, cl01):
    # cl01 manda su apellido nuevo y otro usuario desde «Mi cuenta» -> ve el aviso, cambia el apellido y el usuario no
    client.force_login(cl01)
    datos = {"first_name": "Carla", "last_name": "Rojas", "email": "cl01@correo.com", "phone": "71000001", "username": "otro"}
    respuesta = client.post("/account/", datos, follow=True)
    # Comprueba el aviso
    assertContains(respuesta, "Tus datos se guardaron.")
    # Comprueba lo guardado
    assert get_user_model().objects.filter(username="cl01", last_name="Rojas").exists() is True


def test_cambiar_la_contrasena_pide_la_actual_y_la_guarda_sin_cerrar_la_sesion(client, cl01, caplog):
    # cl01 se equivoca en la contraseña actual y después la escribe bien -> la primera vez nada cambia; la segunda se guarda
    client.force_login(cl01)
    nueva = {"new_password1": "Nueva2026x", "new_password2": "Nueva2026x"}

    # Comprueba que con la actual equivocada se queda en el formulario con el error y la base no cambia
    antes = foto_de_la_base()
    equivocada = client.post("/account/password/", {"old_password": "Equivocada1", **nueva})
    assert (equivocada.status_code, equivocada.context["form"].has_error("old_password")) == (200, True)
    assert foto_de_la_base() == antes

    # Comprueba que con la actual correcta sigue con sesión en «Mi cuenta», ve el aviso, la nueva sirve y el log lo dice
    caplog.clear()
    respuesta = client.post("/account/password/", {"old_password": DEMO_PASSWORD, **nueva}, follow=True)
    assertRedirects(respuesta, "/account/")
    assertContains(respuesta, "Tu contraseña se cambió.")
    assert get_user_model().objects.get(username="cl01").check_password("Nueva2026x") is True
    assert caplog.messages == ['PASSWORD_CHANGED user=cl01 "Carla Mendoza" channel=account by=cl01']
