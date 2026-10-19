"""Forms for the rental request (PRE-CU-01, step 6) and for the return note (C5)."""
from datetime import datetime

from django import forms
from django.utils import timezone

from . import rules
from .models import Rental


def combine_local(day, chosen_time):
    """Join a date and a time into an aware datetime in local time."""
    # make_aware uses the project's TIME_ZONE (America/La_Paz).
    return timezone.make_aware(datetime.combine(day, chosen_time))


class RentalForm(forms.Form):
    """Pickup and return date and time chosen by the client.

    The client may type any minute. The form only checks that real dates
    and times arrive; the 18:00 / 09:00 window is checked by the service
    (rules.py), so its message is the one the client sees. clean() leaves
    start_datetime and end_datetime in cleaned_data, so the view and the
    service do not change.
    """

    start_date = forms.DateField(
        label="Fecha de recojo",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    # No min/max on the input on purpose: the server applies the rule
    # and explains the cause (PRE-RC-01).
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
        cleaned_data = super().clean()
        # Combine only when both parts are valid; otherwise the field
        # errors already tell the client what is missing.
        if cleaned_data.get("start_date") and cleaned_data.get("start_time"):
            cleaned_data["start_datetime"] = combine_local(
                cleaned_data["start_date"], cleaned_data["start_time"]
            )
        if cleaned_data.get("end_date") and cleaned_data.get("end_time"):
            cleaned_data["end_datetime"] = combine_local(
                cleaned_data["end_date"], cleaned_data["end_time"]
            )
        return cleaned_data


class ReturnForm(forms.Form):
    """Note the operator writes about how the unit arrived."""

    # Not required on purpose: register_return checks the note, so the
    # operator sees its message (PRE-RC-01). max_length matches the model,
    # so a long note gets a form error instead of a database error.
    note = forms.CharField(
        label="Observación",
        required=False,
        max_length=Rental._meta.get_field("return_note").max_length,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
