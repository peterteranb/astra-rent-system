"""Form for the rental request (PRE-CU-01, step 6)."""
from datetime import date, datetime, time, timedelta

from django import forms
from django.utils import timezone

from . import rules

# ASSUMPTION: 30-minute steps. No document fixes how precise the chosen
# time must be; a short list is easier to use on a phone than a free
# time input.
TIME_STEP = timedelta(minutes=30)

# Last step before midnight, so the pickup stays on the chosen date.
LAST_PICKUP_TIME = time(23, 30)
FIRST_RETURN_TIME = time(0, 0)


def build_time_choices(first, last):
    """Return ("HH:MM", "HH:MM") pairs every TIME_STEP from first to last, both included."""
    # Any fixed date works: it is only needed to add timedelta to a time.
    current = datetime.combine(date(2000, 1, 1), first)
    end = datetime.combine(date(2000, 1, 1), last)
    choices = []
    while current <= end:
        text = current.strftime("%H:%M")
        choices.append((text, text))
        current += TIME_STEP
    return choices


# Offer only times allowed by ENT-19; rules.py still checks them on the server.
PICKUP_TIME_CHOICES = build_time_choices(rules.EARLIEST_PICKUP_TIME, LAST_PICKUP_TIME)
RETURN_TIME_CHOICES = build_time_choices(FIRST_RETURN_TIME, rules.LATEST_RETURN_TIME)


def combine_local(day, time_text):
    """Join a date and an "HH:MM" text into an aware datetime in local time."""
    # make_aware uses the project's TIME_ZONE (America/La_Paz).
    return timezone.make_aware(datetime.combine(day, time.fromisoformat(time_text)))


class RentalForm(forms.Form):
    """Pickup and return date and time chosen by the client.

    clean() leaves start_datetime and end_datetime in cleaned_data, so
    the view and the service do not change. The business rules are
    applied by the service.
    """

    start_date = forms.DateField(
        label="Fecha de recojo",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    start_time = forms.ChoiceField(label="Hora de recojo", choices=PICKUP_TIME_CHOICES)
    end_date = forms.DateField(
        label="Fecha de devolución",
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    end_time = forms.ChoiceField(label="Hora de devolución", choices=RETURN_TIME_CHOICES)

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
