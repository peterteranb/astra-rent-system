"""Prueba rentals/inventory.py con la base: register_equipment(), el administrador registra un equipo
nuevo (CU-12, ENT-83), y el admin de Django, que valida igual."""
from decimal import Decimal

import pytest
from pytest_django.asserts import assertContains

from rentals.errors import EquipmentRegistrationError
from rentals.inventory import register_equipment
from rentals.models import Equipment
from rentals.statuses import EquipmentStatus
from tests.helpers import foto_de_la_base


def test_registrar_un_equipo_guarda_el_codigo_en_mayusculas_y_disponible(db):
    # El admin escribe «mes-00021» para una mesa de 400 Bs -> se guarda MES-00021, disponible
    register_equipment("mes-00021", "SN-MES-00021", "Mesa plegable 1,80 m", Decimal("400.00"))
    guardado = Equipment.objects.get()
    assert (guardado.inventory_id, guardado.status, guardado.value) == (
        "MES-00021", EquipmentStatus.AVAILABLE, Decimal("400.00")
    )


def test_un_equipo_con_varios_errores_los_muestra_todos_y_no_se_guarda(mes01):
    # Código sin formato, serie repetida de MES-00001, sin nombre y valor 0 -> todas las causas y nada se guarda
    antes = foto_de_la_base()
    with pytest.raises(EquipmentRegistrationError) as error:
        register_equipment("MESA-1", "SN-MES-00001", "", Decimal("0"))
    # Comprueba las cuatro causas juntas: primero las que no consultan la base
    assert error.value.causes == [
        "El código debe tener 3 letras, un guion y 5 números, por ejemplo MES-00001.",
        "Falta el campo Nombre.",
        "El valor debe ser mayor que 0.",
        "Ya existe un equipo con este número de serie.",
    ]
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_un_codigo_repetido_en_minusculas_se_rechaza(mes01):
    # Ya existe MES-00001 y el admin escribe «mes-00001» -> rechazado: es el mismo código
    with pytest.raises(EquipmentRegistrationError) as error:
        register_equipment("mes-00001", "SN-OTRA", "Mesa plegable 1,80 m", Decimal("400.00"))
    assert error.value.causes == ["Ya existe un equipo con este código."]


def test_el_admin_de_django_tambien_valida_el_codigo(client, ad01):
    # ad01 agrega en el admin un equipo «sil-1» -> el admin muestra el formato esperado y no lo guarda
    client.force_login(ad01)
    datos = {"inventory_id": "sil-1", "serial_number": "SN-SIL-1", "name": "Silla", "value": "80"}
    respuesta = client.post("/admin/rentals/equipment/add/", datos)
    # Comprueba el mensaje del formato
    assertContains(respuesta, "El código debe tener 3 letras, un guion y 5 números")
    # Comprueba que no se guardó
    assert Equipment.objects.count() == 0
