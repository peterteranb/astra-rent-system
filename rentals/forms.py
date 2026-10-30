"""Formularios del catálogo (CU-03), la renta en línea (CU-04) y en tienda (CU-05), el orden de las listas del operador, la devolución (CU-09) y el registro de equipos (CU-12)."""
from django import forms

from . import rules
from .models import Equipment, Rental
from .statuses import EquipmentStatus
from .use_cases.catalog import CatalogFilters, catalog_filters, list_catalog
from .use_cases.handover import ORDER_BY_DATE, ORDER_RECENT
from .use_cases.inventory import normalize_inventory_id
from .use_cases.renting import client_accounts


class CatalogFilterForm(forms.Form):
    """Filtros del catálogo: código o nombre, libres entre dos fechas y, para el personal, el estado (ENT-86)."""

    q = forms.CharField(label="Código o nombre", required=False, max_length=100)
    free_from = forms.DateField(
        label="Libre desde",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    free_to = forms.DateField(
        label="Libre hasta",
        required=False,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    status = forms.ChoiceField(
        label="Estado", required=False, choices=[("", "Todos"), *EquipmentStatus.choices]
    )

    def clean(self):
        """Revisa que lleguen las dos fechas y en orden."""
        cleaned_data = super().clean()
        free_from, free_to = cleaned_data.get("free_from"), cleaned_data.get("free_to")
        if bool(free_from) != bool(free_to):
            raise forms.ValidationError("Elige las dos fechas para ver los equipos libres.")
        if free_from and free_to <= free_from:
            raise forms.ValidationError("La fecha final debe ser posterior a la inicial.")
        return cleaned_data

    def filters(self):
        """Devuelve los filtros listos para catalog.search_catalog; sin filtros si el formulario tiene errores."""
        if not self.is_valid():
            return CatalogFilters()
        data = self.cleaned_data
        return catalog_filters(data["q"], data["free_from"], data["free_to"], data["status"])


class RentalForm(forms.Form):
    """Fecha y hora de recojo y de devolución que elige el cliente.

    Solo revisa que lleguen fechas y horas reales; la ventana 18:00 / 09:00 la
    revisa el caso de uso, así el cliente ve su mensaje con la causa (RC-04).
    """

    start_date = forms.DateField(
        label="Fecha de recojo",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    # Sin min/max en el campo a propósito: el servidor aplica la regla y explica la causa (RC-04).
    start_time = forms.TimeField(
        label="Hora de recojo",
        help_text=f"Desde las {rules.EARLIEST_PICKUP_TIME:%H:%M}",
        widget=forms.TimeInput(attrs={"type": "time", "step": "60"}, format="%H:%M"),
    )
    end_date = forms.DateField(
        label="Fecha de devolución",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    end_time = forms.TimeField(
        label="Hora de devolución",
        help_text=f"Hasta las {rules.LATEST_RETURN_TIME:%H:%M}",
        widget=forms.TimeInput(attrs={"type": "time", "step": "60"}, format="%H:%M"),
    )

    def clean(self):
        """Agrega start_datetime y end_datetime en hora de La Paz cuando la fecha y la hora son válidas."""
        cleaned_data = super().clean()
        # Si falta una parte, el error de su campo ya le dice al cliente qué falta.
        if cleaned_data.get("start_date") and cleaned_data.get("start_time"):
            cleaned_data["start_datetime"] = rules.combine_local(
                cleaned_data["start_date"], cleaned_data["start_time"]
            )
        if cleaned_data.get("end_date") and cleaned_data.get("end_time"):
            cleaned_data["end_datetime"] = rules.combine_local(
                cleaned_data["end_date"], cleaned_data["end_time"]
            )
        return cleaned_data


class OnlineRentalForm(RentalForm):
    """Renta en línea desde la API: el código del equipo llega con las fechas y no en la dirección."""

    # Cualquier equipo, como la página: create_rental dice por qué uno no se puede rentar.
    equipment = forms.ModelChoiceField(
        label="Equipo", queryset=Equipment.objects.all(), to_field_name="inventory_id"
    )


class WalkInRentalForm(RentalForm):
    """Renta que el operador registra en la tienda para un cliente: agrega el cliente y el equipo."""

    # La página muestra solo los resultados de la búsqueda, pero se acepta cualquier
    # cliente: así el POST no depende de repetir la búsqueda.
    client = forms.ModelChoiceField(
        label="Cliente", queryset=client_accounts(), widget=forms.RadioSelect
    )
    # create_rental vuelve a revisar el equipo al guardar; la lista solo ayuda a elegir.
    equipment = forms.ModelChoiceField(
        label="Equipo",
        queryset=list_catalog(),
        to_field_name="inventory_id",
        empty_label="Elige un equipo",
    )


class ListOrderForm(forms.Form):
    """Selector «Ordenar por» de «Reservas por entregar» y «Devoluciones»: más recientes o por fecha (ENT-100)."""

    date_label = ""
    order = forms.ChoiceField(label="Ordenar por", required=False)

    def __init__(self, data=None):
        """Arma las dos opciones; date_label dice qué fecha usa la lista."""
        super().__init__(data)
        self.fields["order"].choices = [(ORDER_RECENT, "Más recientes"), (ORDER_BY_DATE, self.date_label)]

    def chosen_order(self):
        """Devuelve el orden elegido; sin elegir o con un valor desconocido, los más recientes."""
        if self.is_valid() and self.cleaned_data["order"]:
            return self.cleaned_data["order"]
        return ORDER_RECENT


class ReservationsOrderForm(ListOrderForm):
    """Orden de «Reservas por entregar»: más recientes o por fecha de recojo."""

    date_label = "Fecha de recojo"


class ReturnsOrderForm(ListOrderForm):
    """Orden de «Devoluciones»: más recientes o por fecha de devolución."""

    date_label = "Fecha de devolución"


class ReturnForm(forms.Form):
    """Observación que escribe el operador sobre cómo llegó el equipo."""

    # No es obligatoria aquí: register_return revisa que haya nota y da su mensaje (RC-04).
    # max_length es el del modelo, así una nota larga da error de formulario y no de base.
    note = forms.CharField(
        label="Observación",
        required=False,
        max_length=Rental._meta.get_field("return_note").max_length,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class EquipmentForm(forms.Form):
    """Datos de un equipo nuevo que escribe el administrador (CU-12).

    Los campos no son obligatorios aquí: register_equipment revisa todo y junta las causas.
    """

    inventory_id = forms.CharField(
        label="Código",
        required=False,
        max_length=20,
        help_text="3 letras, un guion y 5 números, por ejemplo MES-00021.",
    )
    serial_number = forms.CharField(label="Número de serie", required=False, max_length=50)
    name = forms.CharField(label="Nombre", required=False, max_length=100)
    value = forms.DecimalField(label="Valor de compra (Bs)", required=False, decimal_places=2)


class EquipmentAdminForm(forms.ModelForm):
    """Equipo en el admin de Django: valida igual que el modelo y guarda el código en mayúsculas (ENT-83)."""

    class Meta:
        model = Equipment
        fields = ["inventory_id", "serial_number", "name", "value"]

    def clean_inventory_id(self):
        """Devuelve el código sin espacios y en mayúsculas, antes de revisar su formato."""
        return normalize_inventory_id(self.cleaned_data["inventory_id"])
