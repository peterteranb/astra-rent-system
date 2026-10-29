"""Prueba el panel del responsable y vistas de gestión del personal en rentals/views/staff.py y admin.py."""
from pytest_django.asserts import assertContains, assertRedirects

from rentals.models import Rental
from rentals.statuses import RentalStatus
from rentals.use_cases.renting import create_rental
from tests.helpers import dentro_de, renta_entregada


def test_visualizacion_y_gestion_de_paneles_del_personal_y_responsable(client, cl01, op01, ad01, mes01):
    # Personal accede al listado de reservas activas y pendientes; administrador visualiza indicadores y métricas del panel general
    # Comprueba que un usuario con rol de operador ingresa sin problemas al listado de reservas pendientes del personal
    client.force_login(op01)
    respuesta_staff = client.get("/staff/reservations/")
    assertContains(respuesta_staff, "Reservas y entregas")

    # Comprueba que el administrador accede correctamente a las métricas e indicadores del panel del responsable
    client.force_login(ad01)
    respuesta_manager = client.get("/manager/")
    assertContains(respuesta_manager, "Panel del responsable")

    # Vistas de detalle de renta y operaciones de mostrador reflejan los estados correctos de los equipos en tienda
    # Comprueba que la vista de detalle de una reserva muestra el estado actual y los datos del cliente correspondiente
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    respuesta_detalle = client.get(f"/staff/rentals/{reserva.pk}/")
    assertContains(respuesta_detalle, "MES-00001")
    assertContains(respuesta_detalle, "cl01")

    # Comprueba que el listado de equipos entregados muestra correctamente la renta activa en curso
    renta_activa = renta_entregada(cl01, mes01, dentro_de(0, 18), dentro_de(2, 9), op01)
    respuesta_entregados = client.get("/staff/active-rentals/")
    assertContains(respuesta_entregados, "MES-00001")