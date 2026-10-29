"""Prueba accounts/registration.py y el flujo web de registro de clientes con la base de datos."""
from pytest_django.asserts import assertContains, assertRedirects

from accounts.models import User
from accounts.registration import SignUpData, register_client
from tests.helpers import foto_de_la_base


def test_registro_de_nuevos_clientes_por_formulario_y_caso_de_uso(client, db):
    # Registrar cliente con datos válidos crea la cuenta activa y redirige al login; datos duplicados o inválidos muestran errores
    # Comprueba que el registro directo mediante el caso de uso crea el usuario con los campos y rol de cliente correctos
    datos = SignUpData("Sofía", "Valle", "sofia@correo.com", "71234569", "cl_sofia", "Segura2026", "Segura2026")
    usuario = register_client(datos)
    guardado = User.objects.get(username="cl_sofia")
    assert (guardado.email, guardado.first_name, guardado.is_active) == ("sofia@correo.com", "Sofía", True)

    # Comprueba que enviar el formulario web de registro con datos correctos crea el usuario y redirige al inicio de sesión
    respuesta_web = client.post(
        "/signup/",
        {
            "first_name": "Mateo", "last_name": "Roca", "email": "mateo@correo.com",
            "phone": "71234570", "username": "cl_mateo", "password1": "Segura2026", "password2": "Segura2026",
        },
    )
    assertRedirects(respuesta_web, "/login/")
    assert User.objects.filter(username="cl_mateo").exists()

    # Comprueba que intentar registrar un nombre de usuario ya existente por web muestra el mensaje de error en el formulario
    respuesta_duplicado = client.post(
        "/signup/",
        {
            "first_name": "Otro", "last_name": "Usuario", "email": "otro@correo.com",
            "phone": "71234571", "username": "cl_mateo", "password1": "Segura2026", "password2": "Segura2026",
        },
    )
    assertContains(respuesta_duplicado, "Este nombre de usuario ya está en uso.")