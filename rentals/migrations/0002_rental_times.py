"""Agrega a la renta los momentos reales de recojo, devolución y cancelación, y quita el estado «rentado» del equipo."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def make_rented_equipment_available(apps, schema_editor):
    """Pasa a «Disponible» los equipos marcados «rentado»: ahora eso sale de las fechas de la renta."""
    Equipment = apps.get_model("rentals", "Equipment")
    Equipment.objects.filter(status="rented").update(status="available")


class Migration(migrations.Migration):
    """Momentos de la renta y estados del equipo sin «rentado»."""

    dependencies = [
        ('rentals', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(make_rented_equipment_available, migrations.RunPython.noop),
        migrations.AddField(
            model_name='rental',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rental',
            name='picked_up_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='rental',
            name='registered_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='registered_rentals', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='rental',
            name='return_note',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='rental',
            name='returned_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='status',
            field=models.CharField(choices=[('available', 'Disponible'), ('in_review', 'En revisión'), ('in_repair', 'En reparación'), ('retired', 'Baja')], default='available', max_length=20),
        ),
    ]
