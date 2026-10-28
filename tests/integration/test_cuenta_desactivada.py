"""Prueba la cuenta desactivada (ENT-79): accounts/forms.py LoginForm, los backends de config/settings.py,
el log de accounts/admin.py al cambiar «Activo» y la búsqueda de clientes de la tienda (rentals/renting.py)."""
from pytest_django.asserts import assertContains, assertRedirects

from rentals.renting import find_clients
from tests.helpers import foto_de_la_base


def desactivar(usuario):
    """Quita «Activo» al usuario, como lo hace el admin."""
    usuario.is_active = False
    usuario.save()


def datos_del_admin(usuario, **cambios):
    """Devuelve lo que envía el formulario del admin al guardar al usuario; sin is_active, «Activo» va desmarcado."""
    return {
        "username": usuario.username,
        "first_name": usuario.first_name,
        "last_name": usuario.last_name,
        "email": usuario.email,
        "phone": usuario.phone,
        "role": usuario.role_id,
        "date_joined_0": "2026-10-01",
        "date_joined_1": "10:00:00",
        **cambios,
    }


def test_una_cuenta_desactivada_con_su_clave_ve_que_esta_desactivada(client, cl01, caplog):
    # cl01 está desactivada y escribe su contraseña correcta -> ve por qué no entra y el log lo registra
    desactivar(cl01)
    antes = foto_de_la_base()
    respuesta = client.post("/login/", {"username": "cl01", "password": "Demo1234"})
    assertContains(respuesta, "Tu cuenta está desactivada. Comunícate con la tienda.")
    # Comprueba la línea del log
    assert caplog.messages == ["LOGIN_REJECTED reason=inactive user=cl01"]
    # Comprueba que no inició sesión y que no cambió nada en la base
    assert ("_auth_user_id" in client.session, foto_de_la_base()) == (False, antes)


def test_una_cuenta_desactivada_con_otra_clave_ve_el_mensaje_general(client, cl01, caplog):
    # cl01 está desactivada y escribe una contraseña equivocada -> ve el mensaje general, sin pistas
    desactivar(cl01)
    respuesta = client.post("/login/", {"username": "cl01", "password": "equivocada"})
    assertContains(respuesta, "Usuario o contraseña incorrectos.")
    assert caplog.messages == []


def test_una_cuenta_que_se_desactiva_con_la_sesion_abierta_vuelve_al_login(client, cl01):
    # cl01 tiene la sesión abierta y el admin la desactiva -> en su siguiente clic va al login
    client.force_login(cl01)
    desactivar(cl01)
    respuesta = client.get("/my-rentals/")
    assertRedirects(respuesta, "/login/?next=/my-rentals/")


def test_desactivar_una_cuenta_en_el_admin_escribe_account_deactivated(client, ad01, cl01, caplog):
    # ad01 desmarca «Activo» de cl01 en el admin -> cl01 queda desactivada y el log dice quién lo hizo
    client.force_login(ad01)
    respuesta = client.post(f"/admin/accounts/user/{cl01.pk}/change/", datos_del_admin(cl01))
    assertRedirects(respuesta, "/admin/accounts/user/")
    cl01.refresh_from_db()
    assert (cl01.is_active, caplog.messages) == (False, ["ACCOUNT_DEACTIVATED user=cl01 by=ad01"])


def test_reactivar_una_cuenta_en_el_admin_escribe_account_reactivated(client, ad01, cl01, caplog):
    # cl01 está desactivada y ad01 vuelve a marcar «Activo» -> cl01 queda activa y el log lo registra
    desactivar(cl01)
    client.force_login(ad01)
    respuesta = client.post(f"/admin/accounts/user/{cl01.pk}/change/", datos_del_admin(cl01, is_active="on"))
    assertRedirects(respuesta, "/admin/accounts/user/")
    cl01.refresh_from_db()
    assert (cl01.is_active, caplog.messages) == (True, ["ACCOUNT_REACTIVATED user=cl01 by=ad01"])


def test_la_tienda_no_encuentra_a_un_cliente_desactivado(cl02):
    # cl02 está desactivada y op01 busca «rojas» -> no aparece, así no se le registra una renta
    desactivar(cl02)
    assert list(find_clients("rojas")) == []
