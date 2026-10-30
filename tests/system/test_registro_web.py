"""Pruebas de sistema del registro: el cliente crea su cuenta en la web (CU-01) y el operador
en la tienda (CU-02), desde el formulario hasta lo guardado."""
from django.contrib.auth import get_user_model
from pytest_django.asserts import assertContains, assertNotContains, assertRedirects

FORMULARIO = {
    "first_name": "Lucía",
    "last_name": "Quispe",
    "email": "lucia.quispe@correo.com",
    "phone": "71234567",
    "username": "cl03",
    "password": "Montaña2026",
    "password_confirmation": "Montaña2026",
}


def test_el_cliente_crea_su_cuenta_y_entra_al_catalogo(client, db):
    # Lucía se registra como cl03 y luego inicia sesión -> ve «Cuenta creada» y después el catálogo
    registro = client.post("/signup/", FORMULARIO, follow=True)
    ingreso = client.post("/login/", {"username": "cl03", "password": "Montaña2026"}, follow=True)
    # Comprueba que volvió al login con el aviso
    assertContains(registro, "Cuenta creada. Ya puedes iniciar sesión con cl03.")
    # Comprueba que al ingresar llegó al catálogo
    assert ingreso.redirect_chain[-1][0] == "/"


def test_un_registro_rechazado_muestra_las_causas_y_no_devuelve_la_contrasena(client, db):
    # Lucía repite mal la contraseña -> ve «No se creó la cuenta:» con la causa y no se guarda nada
    respuesta = client.post("/signup/", {**FORMULARIO, "password_confirmation": "Otra2026"})
    # Comprueba el título y la causa
    assertContains(respuesta, "No se creó la cuenta:")
    assertContains(respuesta, "Las contraseñas no coinciden.")
    # Comprueba que el correo sigue escrito pero la contraseña no vuelve a la página
    assertContains(respuesta, "lucia.quispe@correo.com")
    assertNotContains(respuesta, "Montaña2026")
    # Comprueba que no se creó la cuenta
    assert get_user_model().objects.filter(username="cl03").exists() is False


def test_el_operador_crea_la_cuenta_y_queda_listo_para_rentarle(client, op01):
    # op01 registra a Lucía en la tienda -> va a «Renta en tienda» con cl03 ya buscado
    client.force_login(op01)
    respuesta = client.post("/staff/clients/new/", FORMULARIO)
    seguida = client.get(respuesta.url)
    # Comprueba que va a la renta en tienda con la búsqueda hecha
    assertRedirects(respuesta, "/staff/walk-in/?q=cl03")
    # Comprueba el aviso y que el cliente aparece para elegirlo
    assertContains(seguida, "Cuenta creada para cl03. Le enviamos un correo para crear su contraseña. Ya puedes registrar su renta.")
    assertContains(seguida, "Lucía Quispe")
