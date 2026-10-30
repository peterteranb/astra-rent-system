"""Prueba la cuenta desactivada (ENT-79): formularios de login, backends, registro de log en admin y cancelación de reservas (D-27)."""
from pytest_django.asserts import assertContains, assertRedirects

from rentals.models import Rental
from rentals.statuses import RentalStatus
from rentals.use_cases.renting import create_rental, find_clients
from tests.helpers import dentro_de, foto_de_la_base, renta_entregada


def desactivar(usuario):
    """Desactiva lógicamente al usuario en la base de datos."""
    usuario.is_active = False
    usuario.save()


def datos_del_admin(usuario, **cambios):
    """Genera el diccionario de datos enviado por el formulario de edición de usuario en el admin."""
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


def test_comportamiento_bloqueos_y_gestion_de_cuentas_desactivadas(client, cl01, cl02, op01, ad01, mes01, mes02, caplog):
    # Cuenta desactivada con clave correcta avisa el motivo y registra el log; con clave errónea muestra el mensaje genérico
    # Comprueba que intentar iniciar sesión con una cuenta desactivada y clave correcta informa el estado e inscribe el evento en el log
    desactivar(cl01)
    antes = foto_de_la_base()
    respuesta_activa = client.post("/login/", {"username": "cl01", "password": "Demo1234"})
    assertContains(respuesta_activa, "Tu cuenta está desactivada. Comunícate con la tienda.")
    assert caplog.messages == ["LOGIN_REJECTED reason=inactive user=cl01"]
    assert ("_auth_user_id" in client.session, foto_de_la_base()) == (False, antes)

    # Comprueba que un intento con contraseña incorrecta en cuenta desactivada muestra el mensaje general por seguridad
    caplog.clear()
    respuesta_falsa = client.post("/login/", {"username": "cl01", "password": "equivocada"})
    assertContains(respuesta_falsa, "Usuario o contraseña incorrectos.")
    assert caplog.messages == []

    # Sesión activa interrumpida por desactivación redirige al login; admin activa/desactiva cuentas registrando logs y cancelando reservas
    # Comprueba que un usuario con sesión abierta es redirigido al login en su siguiente clic si el admin lo desactiva
    client.force_login(cl01)
    desactivar(cl01)
    assertRedirects(client.get("/my-rentals/"), "/login/?next=/my-rentals/")

    # Comprueba que reactivar la cuenta en el admin actualiza su estado y escribe el log de reactivación
    client.force_login(ad01)
    caplog.clear()
    respuesta_react = client.post(f"/admin/accounts/user/{cl01.pk}/change/", datos_del_admin(cl01, is_active="on"))
    assertRedirects(respuesta_react, "/admin/accounts/user/")
    cl01.refresh_from_db()
    assert (cl01.is_active, caplog.messages) == (True, ["ACCOUNT_REACTIVATED user=cl01 by=ad01"])

    # Búsqueda en tienda omite cuentas inactivas; desactivar en admin cancela reservas futuras pero respeta equipos rentados en mano (D-27)
    # Comprueba que el buscador de clientes de la tienda excluye a los usuarios desactivados
    desactivar(cl02)
    assert list(find_clients("rojas")) == []

    # Comprueba que desactivar en el admin escribe el log, cancela sus reservas futuras y preserva las rentas en curso
    rentada = renta_entregada(cl01, mes01, dentro_de(0, 18), dentro_de(1, 9), op01)
    reserva = create_rental(cl01, mes02, dentro_de(7, 18), dentro_de(9, 9))
    caplog.clear()
    respuesta_desc = client.post(f"/admin/accounts/user/{cl01.pk}/change/", datos_del_admin(cl01))
    assertRedirects(respuesta_desc, "/admin/accounts/user/")
    cl01.refresh_from_db()
    assert (cl01.is_active, "ACCOUNT_DEACTIVATED user=cl01 by=ad01" in caplog.messages) == (False, True)
    reserva.refresh_from_db()
    assert (reserva.status, reserva.cancelled_by) == (RentalStatus.CANCELLED, ad01)
    assert Rental.objects.get(pk=rentada.pk).status == RentalStatus.RENTED

    # Comprueba que las páginas de eliminación del admin devuelven un código 403 y no borran registros (ENT-97)
    antes_borrado = foto_de_la_base()
    resp_del_user = client.get(f"/admin/accounts/user/{cl01.pk}/delete/")
    resp_del_eq = client.get(f"/admin/rentals/equipment/{mes01.pk}/delete/")
    assert (resp_del_user.status_code, resp_del_eq.status_code) == (403, 403)
    assert foto_de_la_base() == antes_borrado