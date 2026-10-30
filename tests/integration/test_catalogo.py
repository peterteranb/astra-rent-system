"""Prueba rentals/use_cases/catalog.py con la base: search_catalog() y catalog_page(), el catálogo filtrado y
paginado (CU-03, ENT-86) y que con 1000 equipos haga las mismas consultas (RC-01)."""
from decimal import Decimal

from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from rentals.models import Equipment
from rentals.statuses import EquipmentStatus
from rentals.use_cases.catalog import CatalogFilters, catalog_page, search_catalog
from rentals.use_cases.renting import create_rental
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
        list(catalog_page(search_catalog(CatalogFilters(), ahora), 1))
    return len(consultas)


def test_filtrado_paginacion_y_rendimiento_del_catalogo_de_equipos(cl01, mes01, mes02, mes03_en_revision):
    # MES-00001 está reservada de hoy+7 a hoy+9 -> se filtra por fechas, texto y estado, y se pagina de 20 en 20
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))

    # Comprueba que buscar libres de hoy+8 a hoy+10 omite MES-00001, que está ocupada
    filtros_fechas = CatalogFilters(free_start=dentro_de(8, 18), free_end=dentro_de(10, 9))
    assert list(search_catalog(filtros_fechas, timezone.now())) == [mes02]

    # Comprueba que desde hoy+9 18:00, cuando MES-00001 ya volvió, aparece como libre
    filtros_limite = CatalogFilters(free_start=dentro_de(9, 18), free_end=dentro_de(11, 9))
    assert list(search_catalog(filtros_limite, timezone.now())) == [mes01, mes02]

    # Comprueba que buscar «mesa» no muestra al cliente MES-00003, que está en revisión
    assert list(search_catalog(CatalogFilters(text="mesa"), timezone.now())) == [mes01, mes02]

    # Comprueba que el personal puede filtrar por «En revisión»
    filtros_personal = CatalogFilters(status=EquipmentStatus.IN_REVIEW)
    assert list(search_catalog(filtros_personal, timezone.now(), staff=True)) == [mes03_en_revision]

    # Comprueba que con 47 equipos la página 3 tiene los 7 últimos
    crear_sillas(45)
    pagina_3 = catalog_page(search_catalog(CatalogFilters(), timezone.now()), 3)
    codigos = [equipo.inventory_id for equipo in pagina_3.object_list]
    assert (pagina_3.paginator.num_pages, len(codigos), codigos[-1]) == (3, 7, "SIL-00045")

    # Comprueba que con 1000 sillas la página hace las mismas consultas que con 45 (RC-01, ENT-02)
    con_pocos = consultas_de_una_pagina()
    crear_sillas(955, desde=46)
    assert consultas_de_una_pagina() == con_pocos
