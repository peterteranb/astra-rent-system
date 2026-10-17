"""Create the groups of the staff roles: operador and mantenimiento."""
from django.db import migrations

STAFF_GROUPS = ["operador", "mantenimiento"]


def create_staff_groups(apps, schema_editor):
    """Create the staff groups if they do not exist."""
    Group = apps.get_model("auth", "Group")
    for name in STAFF_GROUPS:
        Group.objects.get_or_create(name=name)


def delete_staff_groups(apps, schema_editor):
    """Delete the staff groups."""
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=STAFF_GROUPS).delete()


class Migration(migrations.Migration):
    """Data migration with the staff groups."""

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("rentals", "0003_status_change"),
    ]

    operations = [
        migrations.RunPython(create_staff_groups, delete_staff_groups),
    ]
