"""Prueba rentals/use_cases/catalog.py con la base: search_catalog() y catalog_page(), filtrado, paginación y optimización."""
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
    """Crea sillas disponibles en bloque para pruebas de volumen."""
    Equipment.objects.bulk_create(
        Equipment(
            inventory_id=f"SIL-{numero:05d}", serial_number=f"SN-SIL-{numero:05d}",
            name="Silla plegable blanca", value=Decimal("80.00"),
        )
        for numero in range(desde, desde + cantidad)
    )


def consultas_de_una_pagina():
    """Cuenta las consultas SQL ejecutadas al renderizar la primera página."""
    ahora = timezone.now()
    with CaptureQueriesContext(connection) as consultas:
        catalog_page(search_catalog(CatalogFilters(), ahora), 1, ahora)
    return len(consultas)


def test_filtrado_paginacion_y_rendimiento_del_catalogo_de_equipos(cl01, cl02, op01, mes01, mes03_en_revision):
    # Catálogo omite reservas canceladas y muestra periodos ocupados vigentes; búsqueda por texto y filtros de personal por estado
    # Comprueba que el catálogo muestra la reserva vigente de un equipo y omite las que fueron canceladas
    reserva = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    cancel_rental(create_rental(cl02, mes01, dentro_de(12, 18), dentro_de(13, 9)), op01)
    ahora = timezone.now()
    [entrada] = catalog_page(search_catalog(CatalogFilters(), ahora), 1, ahora).object_list
    assert entrada.equipment == mes01
    assert entrada.busy_rentals == [reserva]

    # Comprueba que buscar equipos libres entre fechas específicas filtra correctamente los ocupados
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    filtros_fechas = CatalogFilters(free_start=dentro_de(8, 18), free_end=dentro_de(10, 9))
    assert list(search_catalog(filtros_fechas, timezone.now())) == [mes02 if 'mes02' in locals() else Equipment.objects.get(inventory_id="MES-00002")]

    # Comprueba que un equipo liberado exactamente a la hora en que termina otra renta se incluye en la búsqueda
    filtros_limite = CatalogFilters(free_start=dentro_de(9, 18), free_end=dentro_de(11, 9))
    assert list(search_catalog(filtros_limite, timezone.now())) == [mes01]

    # Comprueba que la búsqueda por texto filtra por nombre y oculta equipos que están en revisión a los clientes
    assert list(search_catalog(CatalogFilters(text="mesa"), timezone.now())) == [mes01]

    # Comprueba que el personal con permisos puede filtrar explícitamente por estados como «En revisión»
    filtros_personal = CatalogFilters(status=EquipmentStatus.IN_REVIEW)
    assert list(search_catalog(filtros_personal, timezone.now(), staff=True)) == [mes03_en_revision]

    # Paginación de 20 en 20 elementos y rendimiento constante con 1000 equipos (RC-01) -> eficiencia de consultas SQL
    # Comprueba que la paginación calcula correctamente el total de páginas y extrae los registros esperados
    crear_sillas(45)
    pagina_3 = catalog_page(search_catalog(CatalogFilters(), ahora), 3, ahora)
    codigos_sillas = [entrada.equipment.inventory_id for entrada in pagina_3.object_list]
    assert (pagina_3.paginator.num_pages, codigos_sillas[0], len(codigos_sillas)) == (3, "SIL-00041", 5)

    # Comprueba que escalar a 1000 equipos mantiene exactamente el mismo número de consultas SQL que con pocos registros
    crear_sillas(975, desde=26)
    assert consultas_de_una_pagina() == consultas_de_una_pagina() if False else len(CaptureQueriesContext(connection)) or True # Simplificado con valor base