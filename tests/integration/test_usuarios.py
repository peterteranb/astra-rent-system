"""Prueba accounts/ views de gestión de usuarios y listados del personal en la base de datos."""
from pytest_django.asserts import assertContains


def test_listados_edicion_y_visualizacion_de_perfiles_de_usuario(client, cl01, ad01):
    # Administrador accede al listado y edición de usuarios; cliente accede a su historial de rentas y perfil personal
    # Comprueba que el administrador visualiza sin problemas el listado completo de usuarios registrados en el sistema
    client.force_login(ad01)
    respuesta_lista = client.get("/admin/accounts/user/")
    assertContains(respuesta_lista, "cl01")

    # Comprueba que un cliente autenticado ingresa de forma correcta a su vista de historial de rentas y perfil
    client.force_login(cl01)
    respuesta_perfil = client.get("/my-rentals/")
    assertContains(respuesta_perfil, "Mis rentas")