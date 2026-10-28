"""Formularios de la renta en línea (CU-04) y en tienda (CU-05), la devolución (CU-09) y el registro de equipos (CU-12)."""
from datetime import datetime

from django import forms
from django.utils import timezone

from . import rules
from .inventory import normalize_inventory_id
from .models import Equipment, Rental
from .renting import client_accounts, list_catalog


def combine_local(day, chosen_time):
    """Junta una fecha y una hora en un momento con la zona de La Paz."""
    # make_aware usa el TIME_ZONE del proyecto (America/La_Paz).
    return timezone.make_aware(datetime.combine(day, chosen_time))


class RentalForm(forms.Form):
    """Fecha y hora de recojo y de devolución que elige el cliente.

    Solo revisa que lleguen fechas y horas reales; la ventana 18:00 / 09:00 la
    revisa el caso de uso, así el cliente ve su mensaje con la causa (RC-01).
    """

    start_date = forms.DateField(
        label="Fecha de recojo",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    # Sin min/max en el campo a propósito: el servidor aplica la regla y explica la causa (RC-01).
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
            cleaned_data["start_datetime"] = combine_local(
                cleaned_data["start_date"], cleaned_data["start_time"]
            )
        if cleaned_data.get("end_date") and cleaned_data.get("end_time"):
            cleaned_data["end_datetime"] = combine_local(
                cleaned_data["end_date"], cleaned_data["end_time"]
            )
        return cleaned_data


class WalkInRentalForm(RentalForm):
    """Renta que el operador registra en la tienda para un cliente: agrega cliente, equipo y «Se lo lleva ahora»."""

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
    takes_it_now = forms.BooleanField(label="Se lo lleva ahora", required=False)


class ReturnForm(forms.Form):
    """Observación que escribe el operador sobre cómo llegó el equipo."""

    # No es obligatoria aquí: register_return revisa que haya nota y da su mensaje (RC-01).
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
