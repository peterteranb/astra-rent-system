"""Prueba accounts/registration.py con la base: register_client(), el registro en la web (CU-01), con todas las
causas juntas (ENT-84, RC-04). La tienda usa register_store_client (CU-02), probado en test_correo_crea_tu_contrasena.py."""
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


def test_registro_de_nuevos_clientes_por_formulario_y_caso_de_uso(cl01):
    # Lucía se registra bien, otro llena mal varios campos y otro repite los datos de cl01 -> se guarda solo cl03
    # Comprueba que se crea cl03 como cliente, con el teléfono solo en dígitos y la contraseña cifrada
    register_client(DATOS)
    guardado = get_user_model().objects.get(username="cl03")
    assert (guardado.role.code, guardado.phone) == (Role.CLIENT, "71234567")
    assert (guardado.password != "Montaña2026", guardado.check_password("Montaña2026")) == (True, True)

    # Comprueba que un registro con varios errores muestra todas las causas en orden y no guarda nada
    con_errores = SignUpData("Lucía", "", "lucia.correo.com", "71234", "cl04", "Montañaaa", "Montañaab")
    antes = foto_de_la_base()
    with pytest.raises(RegistrationRejectedError) as error:
        register_client(con_errores)
    assert error.value.causes == [
        "Falta el campo Apellido.",
        "El correo no es válido.",
        "El teléfono debe tener entre 7 y 15 números.",
        "Las contraseñas no coinciden.",
        "La contraseña necesita al menos un número.",
    ]
    assert foto_de_la_base() == antes

    # Comprueba que el usuario, el correo en mayúsculas y el teléfono de cl01 se rechazan juntos (ENT-84)
    repetido = SignUpData("Carla", "Mendoza", "CL01@Correo.com", "71000001", "cl01", "Montaña2026", "Montaña2026")
    with pytest.raises(RegistrationRejectedError) as error_repetido:
        register_client(repetido)
    assert error_repetido.value.causes == [
        "El usuario cl01 ya existe.",
        "El correo ya está registrado.",
        "El teléfono ya está registrado.",
    ]
    assert foto_de_la_base() == antes
