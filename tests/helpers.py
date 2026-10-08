"""Small helpers shared by the tests."""
from datetime import datetime

from django.utils import timezone


def local_datetime(year, month, day, hour, minute=0):
    """Build an aware datetime in the project's time zone (America/La_Paz)."""
    return timezone.make_aware(datetime(year, month, day, hour, minute))
