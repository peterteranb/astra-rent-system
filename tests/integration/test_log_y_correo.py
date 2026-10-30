"""Prueba rentals/services/events.py y notifications.py con la base: log de negocio, notificaciones por correo y comandos de seed_demo."""
import smtplib
import threading
from datetime import timedelta
from io import StringIO
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import CommandError, call_command

from accounts.registration import SignUpData, register_client
from rentals.errors import EquipmentNotAvailableError, RegistrationRejectedError
from rentals.models import Equipment
from rentals.services.events import log_event
from rentals.use_cases.handover import register_return
from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import cancel_rental, create_rental
from tests.helpers import con_la_hora, dentro_de, foto_de_la_base, local_datetime, renta_entregada

HOY = local_datetime(2026, 10, 29, 10)
DATOS = SignUpData("Lucía", "Quispe", "lucia@correo.com", "71234567", "cl03", "Montaña2026", "Montaña2026")


def fallar_anotando_el_hilo(hilos):
    """Hace de send_mail: anota en qué hilo corre y falla como un servidor de correo sin conexión."""

    def enviar(*args, **kwargs):
        """Guarda el hilo actual y lanza el error del servidor."""
        hilos.append(threading.current_thread())
        raise smtplib.SMTPException("sin conexión")

    return enviar


def escribir_y_avisar(terminado):
    """Hace de log_event: escribe la línea de verdad y avisa que el hilo del correo ya terminó."""

    def escribir(*args, **kwargs):
        """Escribe la línea y marca el aviso."""
        log_event(*args, **kwargs)
        terminado.set()

    return escribir


def test_registro_de_eventos_en_log_notificaciones_y_comandos_demo(
    cl01, cl02, op01, mt01, mes01, mes02, caplog, db, settings, tmp_path, django_capture_on_commit_callbacks
):
    # Rentar en línea escribe RENTAL_CREATED en el log; rechazos registran WARNING con la causa; errores de correo escriben EMAIL_FAILED sin contraseñas
    # Comprueba que una reserva en línea registra correctamente el evento RENTAL_CREATED en el log de negocio
    with con_la_hora(HOY):
        renta = create_rental(cl01, mes01, local_datetime(2026, 11, 5, 18), local_datetime(2026, 11, 7, 9))
    assert caplog.messages == [
        (
            f'RENTAL_CREATED rental={renta.pk} equipment=MES-00001 "Mesa plegable 1,80 m" client=cl01 "Carla Mendoza" '
            "period=05/11/2026 18:00-07/11/2026 09:00 amount=40.00 by=cl01 payment=pending"
        )
    ]

    # Comprueba que un intento de reserva rechazado por fechas ocupadas inscribe un nivel WARNING con el motivo en el log
    caplog.clear()
    with con_la_hora(HOY), pytest.raises(EquipmentNotAvailableError):
        create_rental(cl02, mes01, local_datetime(2026, 11, 5, 18), local_datetime(2026, 11, 7, 9))
    [registro] = caplog.records
    assert (registro.levelname, registro.getMessage()) == (
        "WARNING",
        (
            'RENTAL_REJECTED equipment=MES-00001 "Mesa plegable 1,80 m" client=cl02 "Diego Rojas" '
            "period=05/11/2026 18:00-07/11/2026 09:00 "
            'reason="El equipo MES-00001 está ocupado del 05/11/2026 18:00 al 07/11/2026 09:00." by=cl02'
        ),
    )

    # Comprueba que los registros de cuentas y rechazos nunca exponen contraseñas en texto plano dentro del archivo de log
    caplog.clear()
    register_client(DATOS)
    with pytest.raises(RegistrationRejectedError):
        register_client(DATOS)
    assert all("Montaña2026" not in msg for msg in caplog.messages)

    # Pagos por QR y devoluciones tardías envían correos automáticos al cliente; fallos de SMTP registran EMAIL_FAILED preservando el registro
    # Comprueba que un pago QR exitoso despacha la notificación por correo electrónico con el monto detallado
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True), con_la_hora(HOY):
        pay_with_qr(renta, approved=True)
    [correo_pago] = mail.outbox
    assert (correo_pago.to, correo_pago.subject, "Pagado (QR): 40,00 Bs." in correo_pago.body) == (
        ["cl01@correo.com"], "Renta confirmada: MES-00001", True
    )

    # Comprueba que una devolución tardía notifica de forma automática al cliente sobre la deuda generada.
    # Se usa mes02 (libre) y fechas relativas a hoy para que la renta sea válida; la devolución se simula
    # 3 h después del vencimiento para que cuente como atraso de 1 día.
    inicio_tarde = dentro_de(1, 18)
    fin_tarde = dentro_de(3, 9)
    renta_tardia = renta_entregada(cl01, mes02, inicio_tarde, fin_tarde, op01)
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True), con_la_hora(fin_tarde + timedelta(hours=3, minutes=1)):
        register_return(renta_tardia, op01, "Llegó bien")
    [correo_deuda] = mail.outbox
    assert (correo_deuda.to, correo_deuda.subject) == (["cl01@correo.com"], "Tienes una deuda de 20,00 Bs")

    # Comprueba que si el servidor SMTP falla al crear una cuenta, la operación se completa y el log registra la excepción como EMAIL_FAILED
    caplog.clear()
    sin_conexion = smtplib.SMTPException("sin conexión")
    with (
        mock.patch("rentals.services.notifications.send_mail", side_effect=sin_conexion),
        django_capture_on_commit_callbacks(execute=True),
    ):
        register_client(SignUpData("Ana", "Paz", "ana@correo.com", "71234568", "cl04", "Montaña2026", "Montaña2026"))
    assert get_user_model().objects.filter(username="cl04").exists()
    assert caplog.messages[-1] == 'EMAIL_FAILED to=cl04 subject="Bienvenido a SergioCorp" error=SMTPException'

    # Comprueba que con EMAIL_IN_BACKGROUND el correo de la cancelación sale en otro hilo y, si falla, el log escribe EMAIL_FAILED
    settings.EMAIL_IN_BACKGROUND = True
    hilos, terminado = [], threading.Event()
    reserva = create_rental(cl02, mes01, dentro_de(14, 18), dentro_de(15, 9))
    with (
        mock.patch("rentals.services.notifications.send_mail", side_effect=fallar_anotando_el_hilo(hilos)),
        mock.patch("rentals.services.notifications.log_event", side_effect=escribir_y_avisar(terminado)),
        django_capture_on_commit_callbacks(execute=True),
    ):
        cancel_rental(reserva, op01)
    assert terminado.wait(timeout=5) is True
    assert (hilos[0] is threading.main_thread(), hilos[0].daemon) == (False, True)
    assert caplog.messages[-1] == 'EMAIL_FAILED to=cl02 subject="Renta cancelada: MES-00001" error=SMTPException'
    settings.EMAIL_IN_BACKGROUND = False

    # Comando seed_demo con DEBUG=True vacía el log (DEMO_RESET) y crea los equipos; con DEBUG=False se bloquea de forma segura
    # Comprueba que ejecutar seed_demo con DEBUG habilitado reinicia el log con DEMO_RESET y puebla la base de equipos
    caplog.clear()
    log_viejo = tmp_path / "negocio.log"
    log_viejo.write_text("2026-10-27 10:00:00 | INFO    | RENTAL_CREATED id=1\n", encoding="utf-8")
    settings.BUSINESS_LOG_FILE = log_viejo
    settings.DEBUG = True
    call_command("seed_demo", stdout=StringIO())
    assert log_viejo.read_text(encoding="utf-8") == ""
    assert (caplog.messages[0], Equipment.objects.count()) == ("DEMO_RESET", 21)

    # Comprueba que con --equipos 50 quedan 50 equipos, solo mesas, sillas y el combo, sin códigos ni series repetidos (ENT-07, RC-01)
    call_command("seed_demo", "--equipos", "50", stdout=StringIO())
    codigos = set(Equipment.objects.values_list("inventory_id", flat=True))
    series = set(Equipment.objects.values_list("serial_number", flat=True))
    otros = Equipment.objects.exclude(inventory_id__regex=r"^(MES|SIL|CMB)-").count()
    assert (Equipment.objects.count(), len(codigos), len(series), otros) == (50, 50, 50, 0)

    # Comprueba que ejecutar seed_demo con DEBUG=False rechaza la ejecución lanzando una excepción y mantiene la base intacta
    settings.DEBUG = False
    antes_base = foto_de_la_base()
    with pytest.raises(CommandError) as error_debug:
        call_command("seed_demo", stdout=StringIO())
    assert str(error_debug.value) == "seed_demo borra los datos de la demo; solo se usa con DEBUG=True"
    assert foto_de_la_base() == antes_base