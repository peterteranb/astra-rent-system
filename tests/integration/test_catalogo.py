"""Prueba rentals/use_cases/catalog.py con la base: search_catalog() y catalog_page(), el catálogo filtrado y
paginado (CU-03, ENT-64, ENT-86) y que con 1000 equipos haga las mismas consultas (RC-01)."""
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from rentals.models import Equipment
from rentals.statuses import EquipmentStatus
from rentals.use_cases.catalog import CatalogFilters, catalog_page, search_catalog
from rentals.use_cases.renting import cancel_rental, create_rental
from tests.helpers import dentro_de


def crear_sillas(cantidad, desde=1):
    """Crea sillas disponibles SIL-00001, SIL-00002… de 80 Bs en una sola consulta."""
    Equipment.objects.bulk_create(
        Equipment(
            inventory_id=f"SIL-{numero:05d}", serial_number=f"SN-SIL-{numero:05d}",
            name="Silla plegable blanca", value=Decimal("80.00"),
        )
        for numero in range(desde, desde + cantidad)
    )


def consultas_de_una_pagina():
    """Cuenta las consultas que hace armar la primera página del catálogo."""
    ahora = timezone.now()
    with CaptureQueriesContext(connection) as consultas:
        catalog_page(search_catalog(CatalogFilters(), ahora), 1, ahora)
    return len(consultas)


def test_el_catalogo_muestra_el_periodo_ocupado_y_omite_la_reserva_cancelada(cl01, cl02, op01, mes01):
    # MES-00001 tiene una reserva de cl01 y otra cancelada de cl02 -> el catálogo muestra solo la de cl01
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(create_rental(cl02, mes01, dentro_de(12, 18), dentro_de(13, 9)), op01)
    ahora = timezone.now()
    [entrada] = catalog_page(search_catalog(CatalogFilters(), ahora), 1, ahora).object_list
    # Comprueba que la entrada es de MES-00001
    assert entrada.equipment == mes01
    # Comprueba que el único periodo ocupado es la reserva vigente
    assert entrada.busy_rentals == [reserva]


def test_libres_entre_dos_fechas_omite_el_equipo_ocupado(cl01, mes01, mes02):
    # MES-00001 está reservada de hoy+7 a hoy+9 y se buscan libres de hoy+8 a hoy+10 -> solo MES-00002
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    filtros = CatalogFilters(free_start=dentro_de(8, 18), free_end=dentro_de(10, 9))
    assert list(search_catalog(filtros, timezone.now())) == [mes02]


def test_libres_desde_el_dia_que_termina_otra_renta_incluye_el_equipo(cl01, mes01):
    # MES-00001 vuelve hoy+9 a las 09:00 y se buscan libres desde hoy+9 18:00 -> aparece, no se cruza
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    filtros = CatalogFilters(free_start=dentro_de(9, 18), free_end=dentro_de(11, 9))
    assert list(search_catalog(filtros, timezone.now())) == [mes01]


def test_buscar_por_nombre_y_el_cliente_no_ve_los_equipos_en_revision(mes01, mes03_en_revision):
    # Se busca «mesa»: MES-00001 está disponible y MES-00003 en revisión -> el cliente ve solo MES-00001
    assert list(search_catalog(CatalogFilters(text="mesa"), timezone.now())) == [mes01]


def test_el_personal_filtra_por_estado(mes01, mes03_en_revision):
    # El operador filtra «En revisión» -> ve MES-00003
    filtros = CatalogFilters(status=EquipmentStatus.IN_REVIEW)
    assert list(search_catalog(filtros, timezone.now(), staff=True)) == [mes03_en_revision]


def test_cada_pagina_tiene_20_equipos(db):
    # Hay 45 sillas y se pide la página 3 -> tiene las 5 últimas, de SIL-00041 a SIL-00045
    crear_sillas(45)
    ahora = timezone.now()
    pagina = catalog_page(search_catalog(CatalogFilters(), ahora), 3, ahora)
    codigos = [entrada.equipment.inventory_id for entrada in pagina.object_list]
    assert (pagina.paginator.num_pages, codigos[0], len(codigos)) == (3, "SIL-00041", 5)


def test_con_1000_equipos_la_pagina_hace_las_mismas_consultas_que_con_25(db):
    # Se cuentan las consultas con 25 sillas y otra vez con 1000 -> son las mismas (RC-01, ENT-02)
    crear_sillas(25)
    con_pocos = consultas_de_una_pagina()
    crear_sillas(975, desde=26)
    assert consultas_de_una_pagina() == con_pocos
