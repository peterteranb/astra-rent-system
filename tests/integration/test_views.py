"""Pruebas de INTEGRACION de las paginas web (el recorrido completo del cliente).

Archivos que se prueban: rentals/views.py, accounts/urls.py, accounts/forms.py,
                         las plantillas de templates/ y, por debajo, el servicio y la base.
Tipo de prueba:          integracion (usa la base de pruebas y el "cliente de pruebas" de Django).

Que es el "cliente de pruebas" (parametro client):
    Es un navegador falso que trae pytest-django. Con client.get("/") o
    client.post("/login/", {...}) envia una peticion REAL que pasa por las URLs,
    el middleware (sesion, CSRF), la vista, el servicio, la base y la plantilla.
    Devuelve la respuesta: el codigo (200, 302, 404), el HTML y los datos que
    recibio la plantilla. No abre ningun navegador ni servidor.

Herramientas que se usan para comprobar:
    assertRedirects(respuesta, "/")      -> la respuesta redirige a esa direccion
    assertContains(respuesta, "texto")   -> el HTML contiene ese texto
    assertTemplateUsed(respuesta, "x")   -> se uso esa plantilla
    client.force_login(c01)              -> inicia sesion sin pasar por el formulario
                                            (el login real se prueba aparte)

De donde salen los datos:
    Igual que en test_rental_service.py: las fixtures de tests/conftest.py crean
    los clientes y equipos en una base de pruebas que se vacia despues de cada
    prueba. No se usa seed_demo.
"""
import pytest
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from rentals.models import Rental
from rentals.services import create_rental
from tests.conftest import DEMO_PASSWORD

pytestmark = pytest.mark.django_db

# Lo que envia el formulario del navegador para el periodo de los documentos.
DATOS_DEL_FORMULARIO = {
    "start_date": "2026-10-09",
    "start_time": "18:00",
    "end_date": "2026-10-12",
    "end_time": "09:00",
}


# ---------- Inicio de sesion (PRE-CU-01, pasos 1 a 3 y E2) ----------

def test_login_correcto_abre_sesion_y_lleva_al_catalogo(client, c01):
    """El cliente entra con su usuario y clave y llega al catalogo.

    Caso:               C-01 inicia sesion con datos correctos.
    Entrada:            POST /login/ con usuario "c01" y clave "demo1234".
    Condiciones:        el usuario c01 existe (fixture).
    Resultado esperado: redirige a "/" (el catalogo) y la sesion queda abierta para c01.
    Requisito:          PRE-CU-01 pasos 1 a 3 (inicio de sesion).
    Codigo que cubre:   accounts/urls.py -> LoginView con accounts/forms.py -> LoginForm.
    """
    # Ejecutar
    respuesta = client.post("/login/", {"username": "c01", "password": DEMO_PASSWORD})

    # Comprobar
    assertRedirects(respuesta, "/")
    assert client.session["_auth_user_id"] == str(c01.pk)   # la sesion es de c01


@pytest.mark.parametrize(
    "usuario, clave",
    [("c01", "clave-equivocada"), ("nadie", DEMO_PASSWORD)],
    ids=["clave equivocada", "usuario que no existe"],
)
def test_login_incorrecto_muestra_el_mensaje_e2(client, c01, usuario, clave):
    """Con datos incorrectos no se abre la sesion y se ve el mensaje de E2.

    Caso:               alguien escribe mal la clave, o un usuario que no existe.
    Entrada:            POST /login/ con los datos de cada fila.
    Condiciones:        solo existe el usuario c01.
    Resultado esperado: la misma pantalla de login (200) con "Usuario o contraseña
                        incorrectos." y sin sesion abierta. El mensaje es el mismo
                        en los dos casos, para no revelar que usuarios existen.
    Requisito:          PRE-CU-01, excepcion E2 (credenciales incorrectas).
    Codigo que cubre:   accounts/forms.py -> LoginForm.error_messages; plantilla accounts/login.html.
    """
    # Ejecutar
    respuesta = client.post("/login/", {"username": usuario, "password": clave})

    # Comprobar
    assert respuesta.status_code == 200
    assertTemplateUsed(respuesta, "accounts/login.html")
    assertContains(respuesta, "Usuario o contraseña incorrectos.")
    assert "_auth_user_id" not in client.session            # no hay sesion


def test_cerrar_sesion_vuelve_al_login(client, c01):
    """El boton "Cerrar sesion" termina la sesion.

    Caso:               C-01, con sesion abierta, presiona "Cerrar sesion".
    Entrada:            POST /logout/ (Django solo acepta POST para cerrar sesion).
    Condiciones:        c01 tiene la sesion abierta.
    Resultado esperado: redirige a /login/ y ya no hay sesion.
    Requisito:          PRE-CU-01 (acceso del cliente); condicion del curso de
                        diferenciar quien esta usando el sistema.
    Codigo que cubre:   accounts/urls.py -> LogoutView; boton de templates/base.html.
    """
    # Preparar
    client.force_login(c01)

    # Ejecutar
    respuesta = client.post("/logout/")

    # Comprobar
    assertRedirects(respuesta, "/login/")
    assert "_auth_user_id" not in client.session


def test_sin_sesion_el_catalogo_redirige_al_login(client, db):
    """Nadie ve el catalogo sin iniciar sesion.

    Caso:               un visitante sin sesion abre la pagina principal.
    Entrada:            GET /
    Condiciones:        no hay sesion.
    Resultado esperado: redirige a /login/?next=/ (next recuerda a donde queria ir).
    Requisito:          PRE-CU-01 (el cliente primero inicia sesion); precondicion
                        "el cliente tiene su usuario".
    Codigo que cubre:   rentals/views.py -> catalog() con el decorador @login_required.
    """
    # Ejecutar
    respuesta = client.get("/")

    # Comprobar
    assertRedirects(respuesta, "/login/?next=/")


# ---------- Catalogo (PRE-CU-01, paso 4) ----------

def test_el_catalogo_muestra_los_disponibles_y_oculta_los_que_estan_en_revision(
    client, c01, eq01, eq03_in_review
):
    """El catalogo lista solo los equipos que se pueden rentar.

    Caso:               C-01 abre el catalogo.
    Entrada:            GET / con sesion de c01.
    Condiciones:        EQ-01 esta disponible y EQ-03 esta en revision.
    Resultado esperado: la pagina muestra EQ-01 y no muestra EQ-03.
    Requisito:          PRE-02 (consultar disponibilidad). Mostrar SOLO los
                        disponibles es un SUPUESTO nuestro (S-04).
    Codigo que cubre:   rentals/views.py -> catalog(); rentals/services.py -> list_catalog();
                        plantilla rentals/catalog.html.
    """
    # Preparar
    client.force_login(c01)

    # Ejecutar
    respuesta = client.get("/")

    # Comprobar: lo que recibio la plantilla y lo que se ve en el HTML
    assert list(respuesta.context["equipment_list"]) == [eq01]
    assertContains(respuesta, "EQ-01")
    assert "EQ-03" not in respuesta.content.decode()


# ---------- Renta aceptada (PRE-CU-01, pasos 5 a 9) ----------

def test_recorrido_completo_c01_renta_eq01_y_ve_la_confirmacion(client, c01, eq01):
    """El recorrido normal de punta a punta, como lo haria el cliente en el navegador.

    Caso:               C-01 inicia sesion, abre el catalogo, elige EQ-01 y pide del
                        09/10/2026 18:00 al 12/10/2026 09:00.
    Entrada:            POST /login/, GET /, GET /equipment/EQ-01/rent/, POST con las fechas.
    Condiciones:        EQ-01 esta disponible y sin rentas.
    Resultado esperado: se guarda UNA renta de c01 para EQ-01; el navegador termina en
                        /rentals/<id>/ y la pagina dice "Renta confirmada", el equipo,
                        las fechas y "desde las 18:00".
    Requisito:          PRE-CU-01 completo (pasos 1 a 9), PRE-RF-01 caso normal, ENT-16.
    Codigo que cubre:   todo el flujo: accounts (login), rentals/views.py (catalog,
                        rent_equipment, rental_confirmation), forms.py, services.py y
                        las plantillas.
    """
    # Preparar: inicio de sesion por el formulario real
    client.post("/login/", {"username": "c01", "password": DEMO_PASSWORD})

    # Ejecutar: los tres pasos del cliente (follow=True sigue la redireccion final)
    catalogo = client.get("/")
    formulario = client.get("/equipment/EQ-01/rent/")
    respuesta = client.post("/equipment/EQ-01/rent/", DATOS_DEL_FORMULARIO, follow=True)

    # Comprobar: cada pagina mostro lo que debia
    assertContains(catalogo, "/equipment/EQ-01/rent/")       # el enlace para rentar
    assertTemplateUsed(formulario, "rentals/rent_form.html")

    # Comprobar: en la base hay exactamente la renta confirmada
    renta = Rental.objects.get()
    assert renta.client == c01
    assert renta.equipment == eq01

    # Comprobar: la pagina de confirmacion
    assertRedirects(respuesta, f"/rentals/{renta.pk}/")
    assertContains(respuesta, "Renta confirmada")
    assertContains(respuesta, "09/10/2026 18:00")
    assertContains(respuesta, "12/10/2026 09:00")
    assertContains(respuesta, "desde las 18:00")


# ---------- Renta rechazada ----------

def test_c02_es_rechazado_y_vuelve_al_catalogo_con_el_mensaje_e1(
    client, c01, c02, eq01, doc_start, doc_end
):
    """Rechazo E1 visto por el cliente: vuelve al catalogo con la causa.

    Caso:               C-01 ya confirmo EQ-01; C-02 pide EQ-01 en las mismas fechas.
    Entrada:            POST /equipment/EQ-01/rent/ con sesion de c02.
    Condiciones:        existe la renta de C-01 del 09/10 18:00 al 12/10 09:00.
    Resultado esperado: C-02 termina en el catalogo y ve "El equipo EQ-01 no está
                        disponible del 09/10/2026 18:00 al 12/10/2026 09:00.";
                        no se guarda ninguna renta para C-02.
    Requisito:          PRE-CU-01 excepcion E1 (vuelve al catalogo), PRE-RF-01 y PRE-RC-01.
    Codigo que cubre:   rentals/views.py -> rent_equipment() (except EquipmentNotAvailableError
                        -> messages.error + redirect), plantilla base.html (muestra el mensaje).
    """
    # Preparar
    create_rental(c01, eq01, doc_start, doc_end)
    client.force_login(c02)

    # Ejecutar
    respuesta = client.post("/equipment/EQ-01/rent/", DATOS_DEL_FORMULARIO, follow=True)

    # Comprobar
    assertRedirects(respuesta, "/")
    assertContains(
        respuesta,
        "El equipo EQ-01 no está disponible del 09/10/2026 18:00 al 12/10/2026 09:00.",
    )
    assert not Rental.objects.filter(client=c02).exists()


@pytest.mark.parametrize(
    "campo, valor, mensaje",
    [
        ("start_time", "17:00", "El recojo debe ser desde las 18:00."),
        ("end_time", "09:30", "La devolución debe ser hasta las 09:00."),
        ("end_date", "2026-10-15", "La renta no puede durar más de 5 días."),
    ],
    ids=["recojo a las 17:00", "devolucion a las 09:30", "mas de 5 dias"],
)
def test_un_periodo_invalido_deja_al_cliente_en_el_formulario_con_la_causa(
    client, c01, eq01, campo, valor, mensaje
):
    """Si el periodo rompe una regla, el cliente sigue en el formulario para corregirlo.

    Caso:               C-01 envia el formulario con una hora o fecha que rompe una regla.
    Entrada:            POST /equipment/EQ-01/rent/ con los datos de los documentos y UN
                        campo cambiado (ver cada fila).
    Condiciones:        EQ-01 esta disponible; el formulario acepta el dato, la regla no.
    Resultado esperado: responde 200 con el mismo formulario, el mensaje de la causa,
                        los datos que escribio el cliente todavia en los campos,
                        y no se guarda ninguna renta.
    Requisito:          ENT-18, ENT-19 y PRE-RC-01 (mensaje con la causa).
    Codigo que cubre:   rentals/views.py -> rent_equipment() (except RentalRejectedError
                        -> form.add_error), services.check_period() y la plantilla
                        rentals/rent_form.html.
    """
    # Preparar
    client.force_login(c01)
    datos = {**DATOS_DEL_FORMULARIO, campo: valor}

    # Ejecutar
    respuesta = client.post("/equipment/EQ-01/rent/", datos)

    # Comprobar: sigue en el formulario, con la causa
    assert respuesta.status_code == 200
    assertTemplateUsed(respuesta, "rentals/rent_form.html")
    assertContains(respuesta, mensaje)

    # Comprobar: el cliente no tiene que volver a escribir lo que envio
    assertContains(respuesta, f'value="{valor}"')

    # Comprobar: no se guardo nada
    assert Rental.objects.count() == 0


# ---------- Seguridad y equipos que no existen ----------

def test_un_cliente_no_puede_ver_la_confirmacion_de_otro(
    client, c01, c02, eq01, doc_start, doc_end
):
    """Cada cliente solo ve sus propias rentas.

    Caso:               C-02 abre la direccion de la confirmacion de C-01.
    Entrada:            GET /rentals/<id de la renta de C-01>/ con sesion de c02.
    Condiciones:        la renta existe y es de C-01.
    Resultado esperado: 404 (no encontrado). No se dice "es de otro" para no revelar
                        que la renta existe.
    Requisito:          sentido comun de privacidad (ENT-11 deja los permisos por rol
                        para la siguiente iteracion).
    Codigo que cubre:   rentals/views.py -> rental_confirmation()
                        (get_object_or_404 filtra por client=request.user).
    """
    # Preparar
    renta_de_c01 = create_rental(c01, eq01, doc_start, doc_end)
    client.force_login(c02)

    # Ejecutar
    respuesta = client.get(f"/rentals/{renta_de_c01.pk}/")

    # Comprobar
    assert respuesta.status_code == 404


def test_rentar_un_equipo_que_no_existe_responde_404_y_no_guarda_nada(client, c01, eq01):
    """Un numero de inventario que no existe no rompe el sistema.

    Caso:               C-01 envia una renta para "EQ-999", que no esta en el inventario.
    Entrada:            POST /equipment/EQ-999/rent/ con fechas validas.
    Condiciones:        solo existe EQ-01.
    Resultado esperado: 404 (no encontrado) y ninguna renta guardada; no un 500
                        (error del servidor).
    Requisito:          precondicion de PRE-CU-01 ("el equipo existe en el inventario").
    Codigo que cubre:   rentals/views.py -> rent_equipment() (get_object_or_404).
    """
    # Preparar
    client.force_login(c01)

    # Ejecutar
    respuesta = client.post("/equipment/EQ-999/rent/", DATOS_DEL_FORMULARIO)

    # Comprobar
    assert respuesta.status_code == 404
    assert Rental.objects.count() == 0


@pytest.mark.skip(reason="Pendiente del cliente: los numeros de inventario distinguen mayusculas? (Sesion 04)")
def test_numero_de_inventario_en_minusculas_encuentra_el_mismo_equipo(client, c01, eq01):
    """PENDIENTE: no sabemos si "eq-01" y "EQ-01" deben ser el mismo equipo.

    Caso:               C-01 abre /equipment/eq-01/rent/ (en minusculas).
    Resultado esperado: SI el cliente dice que no distinguen mayusculas, 200.
                        Hoy el sistema responde 404. Se activa cuando Sergio responda.
    Requisito:          pregunta abierta de la Sesion 4.
    Codigo que cubre:   rentals/views.py -> rent_equipment().
    """
    # Preparar
    client.force_login(c01)

    # Ejecutar
    respuesta = client.get("/equipment/eq-01/rent/")

    # Comprobar
    assert respuesta.status_code == 200
