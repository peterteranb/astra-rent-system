"""Pone en español los nombres de los modelos y de sus campos para el admin; no cambia ninguna tabla."""
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rentals', '0005_rental_handover_users'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='equipment',
            options={'ordering': ['inventory_id'], 'verbose_name': 'Equipo', 'verbose_name_plural': 'Equipos'},
        ),
        migrations.AlterModelOptions(
            name='rental',
            options={'ordering': ['start_datetime'], 'verbose_name': 'Renta', 'verbose_name_plural': 'Rentas'},
        ),
        migrations.AlterModelOptions(
            name='statuschange',
            options={'ordering': ['changed_at'], 'verbose_name': 'Cambio de estado', 'verbose_name_plural': 'Cambios de estado'},
        ),
        migrations.AlterField(
            model_name='equipment',
            name='description',
            field=models.CharField(max_length=200, verbose_name='Descripción'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='inventory_id',
            field=models.CharField(max_length=20, unique=True, verbose_name='Código'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='serial_number',
            field=models.CharField(max_length=50, verbose_name='Número de serie'),
        ),
        migrations.AlterField(
            model_name='equipment',
            name='status',
            field=models.CharField(choices=[('available', 'Disponible'), ('in_review', 'En revisión'), ('in_repair', 'En reparación'), ('retired', 'Baja')], default='available', max_length=20, verbose_name='Estado'),
        ),
        migrations.AlterField(
            model_name='rental',
            name='client',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='rentals', to=settings.AUTH_USER_MODEL, verbose_name='Cliente'),
        ),
        migrations.AlterField(
            model_name='rental',
            name='end_datetime',
            field=models.DateTimeField(verbose_name='Devolución hasta'),
        ),
        migrations.AlterField(
            model_name='rental',
            name='equipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='rentals', to='rentals.equipment', verbose_name='Equipo'),
        ),
        migrations.AlterField(
            model_name='rental',
            name='start_datetime',
            field=models.DateTimeField(verbose_name='Recojo desde'),
        ),
        migrations.AlterField(
            model_name='statuschange',
            name='changed_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Fecha'),
        ),
        migrations.AlterField(
            model_name='statuschange',
            name='changed_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='status_changes', to=settings.AUTH_USER_MODEL, verbose_name='Cambiado por'),
        ),
        migrations.AlterField(
            model_name='statuschange',
            name='comment',
            field=models.TextField(blank=True, verbose_name='Comentario'),
        ),
        migrations.AlterField(
            model_name='statuschange',
            name='equipment',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='status_changes', to='rentals.equipment', verbose_name='Equipo'),
        ),
        migrations.AlterField(
            model_name='statuschange',
            name='new_status',
            field=models.CharField(choices=[('available', 'Disponible'), ('in_review', 'En revisión'), ('in_repair', 'En reparación'), ('retired', 'Baja')], max_length=20, verbose_name='Estado nuevo'),
        ),
        migrations.AlterField(
            model_name='statuschange',
            name='old_status',
            field=models.CharField(choices=[('available', 'Disponible'), ('in_review', 'En revisión'), ('in_repair', 'En reparación'), ('retired', 'Baja')], max_length=20, verbose_name='Estado anterior'),
        ),
    ]
