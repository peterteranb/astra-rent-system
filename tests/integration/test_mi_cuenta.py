"""Prueba accounts/account.py y las páginas de «Mi cuenta»: editar mis datos con las reglas del registro y
cambiar la contraseña con la vista de Django (CU-17, ENT-103)."""
import pytest
from django.contrib.auth import get_user_model
from pytest_django.asserts import assertContains, assertRedirects

from accounts.account import update_profile
from rentals.errors import RegistrationRejectedError
from tests.conftest import DEMO_PASSWORD
from tests.helpers import foto_de_la_base


def test_editar_mis_datos_guarda_el_telefono_nuevo_y_el_log_dice_solo_el_campo(cl01, caplog):
    # cl01 cambia su teléfono a 7999-0001 -> se guarda con dígitos y el log nombra el campo, no el número
    update_profile(cl01, "Carla", "Mendoza", "cl01@correo.com", "7999-0001")
    # Comprueba lo guardado
    assert get_user_model().objects.get(username="cl01").phone == "79990001"
    # Comprueba la línea del log, sin el teléfono nuevo
    assert caplog.messages == ['PROFILE_UPDATED user=cl01 "Carla Mendoza" fields=phone by=cl01']


def test_mi_propio_correo_en_mayusculas_no_choca_con_mi_cuenta(cl01):
    # cl01 guarda su mismo correo escrito en mayúsculas -> se acepta: no es de otra cuenta
    update_profile(cl01, "Carla", "Mendoza", "CL01@correo.com", "71000001")
    assert get_user_model().objects.get(username="cl01").email == "CL01@correo.com"


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


def test_cambiar_la_contrasena_con_la_actual_la_guarda_y_sigue_con_sesion(client, cl01, caplog):
    # cl01 escribe su contraseña actual y una nueva válida -> vuelve a «Mi cuenta» con el aviso y la nueva sirve
    client.force_login(cl01)
    datos = {"old_password": DEMO_PASSWORD, "new_password1": "Nueva2026x", "new_password2": "Nueva2026x"}
    respuesta = client.post("/account/password/", datos, follow=True)
    # Comprueba que sigue con sesión en «Mi cuenta» y ve el aviso
    assertRedirects(respuesta, "/account/")
    assertContains(respuesta, "Tu contraseña se cambió.")
    # Comprueba lo guardado y el log
    assert get_user_model().objects.get(username="cl01").check_password("Nueva2026x") is True
    assert caplog.messages == ['PASSWORD_CHANGED user=cl01 "Carla Mendoza" channel=account by=cl01']


def test_cambiar_la_contrasena_con_la_actual_equivocada_no_cambia_nada(client, cl01):
    # cl01 se equivoca en la contraseña actual -> se queda en la página con el error y la contraseña sigue igual
    client.force_login(cl01)
    antes = foto_de_la_base()
    datos = {"old_password": "Equivocada1", "new_password1": "Nueva2026x", "new_password2": "Nueva2026x"}
    respuesta = client.post("/account/password/", datos)
    # Comprueba que se quedó en el formulario con el error
    assert (respuesta.status_code, respuesta.context["form"].has_error("old_password")) == (200, True)
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes
