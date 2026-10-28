"""Prueba accounts/models.py con la base: el usuario con rol, is_staff e is_superuser automáticos
según el rol (ENT-44) y el correo único sin distinguir mayúsculas (ENT-84)."""
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import Role


def test_createsuperuser_crea_un_administrador_que_entra_al_admin(ad01):
    # Se crea ad01 con createsuperuser -> tiene el rol administrador, is_staff e is_superuser
    guardado = get_user_model().objects.get(username="ad01")
    assert (guardado.role.code, guardado.is_staff, guardado.is_superuser) == (
        Role.ADMINISTRATOR, True, True
    )


def test_al_dejar_de_ser_administrador_pierde_el_admin(ad01):
    # ad01 pasa a operador -> pierde is_staff e is_superuser al guardarse
    ad01.role = Role.objects.get(code=Role.OPERATOR)
    ad01.save()
    guardado = get_user_model().objects.get(username="ad01")
    assert (guardado.is_staff, guardado.is_superuser) == (False, False)


def test_el_mismo_correo_con_otras_mayusculas_se_rechaza(cl01):
    # cl01 usa cl01@correo.com y otra cuenta pide CL01@Correo.com -> la base lo rechaza
    with pytest.raises(IntegrityError):
        get_user_model().objects.create_user(
            "cl09", email="CL01@Correo.com", password="Demo1234", phone="71000009"
        )
