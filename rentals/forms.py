"""Form for the rental request (PRE-CU-01, step 6)."""
from django import forms

# The browser's "datetime-local" input sends and expects this format.
DATETIME_LOCAL_FORMAT = "%Y-%m-%dT%H:%M"


class RentalForm(forms.Form):
    """Pickup and return date and time chosen by the client.

    It only checks that both values are real dates; the business rules
    are applied by the service.
    """

    start_datetime = forms.DateTimeField(
        label="Fecha y hora de recojo",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_LOCAL_FORMAT),
    )
    end_datetime = forms.DateTimeField(
        label="Fecha y hora de devolución",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format=DATETIME_LOCAL_FORMAT),
    )
