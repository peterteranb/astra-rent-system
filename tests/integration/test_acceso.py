"""Prueba accounts/roles.py: control de acceso y permisos por roles en vistas del personal, login y páginas de error."""
from pytest_django.asserts import assertContains, assertRedirects


def test_control_de_acceso_y_respuestas_http_para_roles_y_errores(client, cl01, op01, ad01):
    # Visitante sin sesión intenta ver reservas por entregar -> redirige al login con parámetro next
    # Comprueba que la vista protegida redirige al inicio de sesión cuando no hay usuario autenticado
    respuesta_visitante = client.get("/staff/reservations/")
    assertRedirects(respuesta_visitante, "/login/?next=/staff/reservations/")

    # Cliente autenticado abre una página exclusiva de operador -> responde con código HTTP 403 (prohibido)
    # Comprueba que un usuario con rol de cliente recibe un error 403 al intentar acceder a rutas del personal
    client.force_login(cl01)
    respuesta_cliente = client.get("/staff/reservations/")
    assertContains(respuesta_cliente, "No tienes permiso para ver esta página", status_code=403)

    # Cliente autenticado abre una ruta inexistente -> responde con la página 404 personalizada en español
    # Comprueba que las rutas no encontradas devuelven un código 404 con mensaje limpio en español
    respuesta_404 = client.get("/no-existe/")
    assertContains(respuesta_404, "No encontramos esta página", status_code=404)

    # Credenciales incorrectas en el login -> muestra el mensaje estándar de error de autenticación
    # Comprueba que un intento de inicio de sesión fallido muestra el aviso correspondiente
    respuesta_login = client.post("/login/", {"username": "cl01", "password": "equivocada"})
    assertContains(respuesta_login, "Usuario o contraseña incorrectos.")

    # Administrador inicia sesión correctamente -> accede sin problemas al panel del responsable
    # Comprueba que el administrador ingresa de forma exitosa al panel de gestión principal
    client.force_login(ad01)
    respuesta_admin = client.get("/home/", follow=True)
    assertContains(respuesta_admin, "Panel del responsable")

    # Operador intenta acceder al panel del responsable (restringido a admin) -> recibe un código 403
    # Comprueba que el operador tiene denegado el acceso al panel administrativo superior
    client.force_login(op01)
    assert client.get("/manager/").status_code == 403