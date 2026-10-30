"""Caso de uso CU-03: el catálogo con sus filtros, de 20 en 20, sin decir cuándo usan el equipo otras personas (ENT-99)."""
from dataclasses import dataclass

from django.core.paginator import Paginator
from django.db.models import Q

from accounts.roles import is_store_staff

from .. import rules
from ..models import Equipment, Rental
from ..statuses import EquipmentStatus

# ENT-02 y ENT-86: con unos 1000 equipos, el catálogo se muestra de 20 en 20.
CATALOG_PAGE_SIZE = 20


@dataclass(frozen=True)
class CatalogFilters:
    """Lo que se busca en el catálogo: texto del código o nombre, un periodo libre y, para el personal, un estado."""

    text: str = ""
    free_start: object = None
    free_end: object = None
    status: str = ""


def list_catalog():
    """Devuelve los equipos que muestra el catálogo: solo los «Disponibles».

    ENT-61: un equipo con rentas futuras sigue disponible; para ver solo los
    libres se filtra por fechas. create_rental vuelve a revisar el equipo.
    """
    return Equipment.objects.filter(status=EquipmentStatus.AVAILABLE)


def catalog_filters(text, free_from, free_to, status):
    """Arma los filtros del catálogo con lo que escribió la persona.

    Las dos fechas se buscan como una renta: desde las 18:00 del primer día
    hasta las 09:00 del último (D-13), así lo que se ve libre se puede rentar.
    """
    return CatalogFilters(
        text=text.strip(),
        free_start=free_from and rules.combine_local(free_from, rules.EARLIEST_PICKUP_TIME),
        free_end=free_to and rules.combine_local(free_to, rules.LATEST_RETURN_TIME),
        status=status,
    )


def browse_catalog(user, filters, page_number, now):
    """Devuelve la página del catálogo que ve user con esos filtros (CU-03)."""
    equipment = search_catalog(filters, now, staff=is_store_staff(user))
    return catalog_page(equipment, page_number)


def search_catalog(filters, now, staff=False):
    """Devuelve los equipos que cumplen los filtros (ENT-86); el cliente solo ve los «Disponibles»."""
    equipment = Equipment.objects.all() if staff else list_catalog()
    if staff and filters.status:
        equipment = equipment.filter(status=filters.status)
    if filters.text:
        equipment = equipment.filter(
            Q(inventory_id__icontains=filters.text) | Q(name__icontains=filters.text)
        )
    if filters.free_start and filters.free_end:
        equipment = equipment.exclude(pk__in=busy_equipment(filters.free_start, filters.free_end, now))
    return equipment


def busy_equipment(start, end, now):
    """Devuelve los ids de los equipos con una renta que en now ocupa algún momento entre start y end (RF-01)."""
    # Mismo cruce que rules.periods_overlap, pero en SQL para no traer las rentas de 1000 equipos.
    return (
        Rental.objects.occupying_at(now)
        .filter(start_datetime__lt=end, end_datetime__gt=start)
        .values("equipment")
    )


def catalog_page(equipment, page_number):
    """Devuelve una página de 20 equipos: siempre dos consultas, contar y traer la página, con 20 o con 1000 (RC-01)."""
    return Paginator(equipment, CATALOG_PAGE_SIZE).get_page(page_number)
