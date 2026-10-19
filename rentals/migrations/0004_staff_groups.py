"""Crea los grupos de los roles del personal: operador y mantenimiento."""
from django.db import migrations

STAFF_GROUPS = ["operador", "mantenimiento"]


def create_staff_groups(apps, schema_editor):
    """Crea los grupos del personal si no existen."""
    Group = apps.get_model("auth", "Group")
    for name in STAFF_GROUPS:
        Group.objects.get_or_create(name=name)


def delete_staff_groups(apps, schema_editor):
    """Borra los grupos del personal."""
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=STAFF_GROUPS).delete()


class Migration(migrations.Migration):
    """Migración de datos con los grupos del personal."""

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("rentals", "0003_status_change"),
    ]

    operations = [
        migrations.RunPython(create_staff_groups, delete_staff_groups),
    ]
