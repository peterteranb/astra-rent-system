"""Prueba accounts/registration.py con la base: register_client(), la misma función para el registro
en la web (CU-01) y en la tienda (CU-02), con todas las causas juntas (ENT-84, RC-04)."""
import pytest
from django.contrib.auth import get_user_model

from accounts.models import Role
from accounts.registration import SignUpData, register_client
from rentals.errors import RegistrationRejectedError
from tests.helpers import foto_de_la_base

DATOS = SignUpData(
    first_name="Lucía",
    last_name="Quispe",
    email="lucia.quispe@correo.com",
    phone="7123-4567",
    username="cl03",
    password="Montaña2026",
    password_confirmation="Montaña2026",
)


def test_registrar_un_cliente_guarda_su_rol_su_telefono_y_la_contrasena_cifrada(db):
    # Lucía llena bien el formulario -> se crea cl03 como cliente, teléfono con dígitos y contraseña cifrada
    register_client(DATOS)
    guardado = get_user_model().objects.get(username="cl03")
    # Comprueba el rol y el teléfono normalizado
    assert (guardado.role.code, guardado.phone) == (Role.CLIENT, "71234567")
    # Comprueba que la contraseña se guardó cifrada y sirve para entrar
    assert (guardado.password != "Montaña2026", guardado.check_password("Montaña2026")) == (True, True)


def test_un_registro_con_varios_errores_muestra_todas_las_causas_y_no_guarda(db):
    # Sin apellido, correo sin @, teléfono corto y contraseñas distintas sin número -> todas las causas, nada se guarda
    datos = SignUpData("Lucía", "", "lucia.correo.com", "71234", "cl03", "Montañaaa", "Montañaab")
    antes = foto_de_la_base()
    with pytest.raises(RegistrationRejectedError) as error:
        register_client(datos)
    # Comprueba las causas en el orden en que se revisan
    assert error.value.causes == [
        "Falta el campo Apellido.",
        "El correo no es válido.",
        "El teléfono debe tener entre 7 y 15 números.",
        "Las contraseñas no coinciden.",
        "La contraseña necesita al menos un número.",
    ]
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_usuario_correo_y_telefono_de_otra_cuenta_se_rechazan(cl01):
    # cl01 ya usa ese usuario, su correo en mayúsculas y su teléfono -> las tres causas (ENT-84)
    datos = SignUpData("Carla", "Mendoza", "CL01@Correo.com", "71000001", "cl01", "Montaña2026", "Montaña2026")
    with pytest.raises(RegistrationRejectedError) as error:
        register_client(datos)
    assert error.value.causes == [
        "El usuario cl01 ya existe.",
        "El correo ya está registrado.",
        "El teléfono ya está registrado.",
    ]
