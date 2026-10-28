"""Crea los cuatro roles del sistema (ENT-53)."""
from django.db import migrations

ROLES = [
    ("cliente", "Cliente", "Renta en línea, paga y consulta sus rentas y su deuda."),
    ("operador", "Operador", "Atiende la tienda: crea cuentas, renta, entrega, recibe y cobra."),
    ("mantenimiento", "Mantenimiento", "Revisa los equipos devueltos y decide su estado."),
    ("administrador", "Administrador", "Puede todo: registra equipos, corrige estados y ve el panel."),
]


def create_roles(apps, schema_editor):
    """Crea los roles si no existen."""
    Role = apps.get_model("accounts", "Role")
    for code, name, description in ROLES:
        Role.objects.get_or_create(code=code, defaults={"name": name, "description": description})


def delete_roles(apps, schema_editor):
    """Borra los roles."""
    Role = apps.get_model("accounts", "Role")
    Role.objects.filter(code__in=[code for code, _name, _description in ROLES]).delete()


class Migration(migrations.Migration):
    """Migración de datos con los roles del sistema."""

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_roles, delete_roles),
    ]
