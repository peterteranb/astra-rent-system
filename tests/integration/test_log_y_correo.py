"""Prueba rentals/services/events.py y rentals/services/notifications.py con la base: el log de negocio de cada operación,
aceptada o rechazada (RC-05), los correos al cliente, que no tumban la operación si fallan (ENT-85), y el log
que seed_demo vuelve a cero."""
import smtplib
from io import StringIO
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.management import call_command

from accounts.registration import SignUpData, register_client
from rentals.errors import EquipmentNotAvailableError, InvalidStatusChangeError, RegistrationRejectedError
from rentals.models import Equipment
from rentals.statuses import EquipmentStatus
from rentals.use_cases.handover import register_return
from rentals.use_cases.payments import pay_with_qr
from rentals.use_cases.renting import create_rental
from rentals.use_cases.review import review_equipment
from tests.helpers import con_la_hora, dentro_de, local_datetime

DATOS = SignUpData("Lucía", "Quispe", "lucia@correo.com", "71234567", "cl03", "Montaña2026", "Montaña2026")


def test_rentar_en_linea_escribe_rental_created(cl01, mes01, caplog):
    # cl01 reserva MES-00001 en línea -> el log tiene la línea con la renta, el equipo, el cliente y sin pago
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    assert caplog.messages == [
        f"RENTAL_CREATED id={renta.pk} equipment=MES-00001 client=cl01 paid=no registered_by=web"
    ]


def test_un_rechazo_escribe_rental_rejected_con_la_causa(cl01, cl02, mes01, caplog):
    # cl02 pide fechas ocupadas -> el log tiene RENTAL_REJECTED con nivel WARNING y la causa
    create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    caplog.clear()
    with pytest.raises(EquipmentNotAvailableError):
        create_rental(cl02, mes01, dentro_de(8, 18), dentro_de(9, 9))
    [registro] = caplog.records
    assert (registro.levelname, registro.getMessage().startswith('RENTAL_REJECTED reason="El equipo MES-00001')) == (
        "WARNING", True
    )


def test_un_rechazo_que_viene_de_otro_caso_de_uso_se_escribe_una_sola_vez(mt01, caplog):
    # mt01 revisa un equipo de baja: lo rechaza history.change_status dentro de la revisión -> una sola línea
    retirado = Equipment.objects.create(
        inventory_id="SIL-00005", serial_number="SN-SIL-00005", name="Silla", value=150, status=EquipmentStatus.RETIRED
    )
    with pytest.raises(InvalidStatusChangeError):
        review_equipment(retirado, mt01, EquipmentStatus.AVAILABLE)
    assert [registro.getMessage().split()[0] for registro in caplog.records] == ["STATUS_CHANGE_REJECTED"]


def test_el_log_del_registro_nunca_tiene_la_contrasena(db, caplog):
    # Lucía se registra bien y después repite el registro -> ninguna línea del log tiene su contraseña
    register_client(DATOS)
    with pytest.raises(RegistrationRejectedError):
        register_client(DATOS)
    # Comprueba que se escribieron la creación y el rechazo
    assert [mensaje.split()[0] for mensaje in caplog.messages] == ["ACCOUNT_CREATED", "ACCOUNT_REJECTED"]
    # Comprueba que la contraseña no aparece en ninguna línea
    assert all("Montaña2026" not in mensaje for mensaje in caplog.messages)


def test_el_pago_qr_manda_la_confirmacion_al_cliente(cl01, mes01, django_capture_on_commit_callbacks):
    # cl01 paga con QR -> recibe «Renta confirmada: MES-00001» con el monto pagado
    renta = create_rental(cl01, mes01, dentro_de(7, 18), dentro_de(9, 9))
    with django_capture_on_commit_callbacks(execute=True):
        pay_with_qr(renta, approved=True)
    [correo] = mail.outbox
    assert (correo.to, correo.subject, "Pagado (QR): 40,00 Bs." in correo.body) == (
        ["cl01@correo.com"], "Renta confirmada: MES-00001", True
    )


def test_la_devolucion_tardia_manda_el_correo_de_la_deuda(cl01, op01, mes01, django_capture_on_commit_callbacks):
    # MES-00001 vence el 03/10 y vuelve a las 12:01 -> cl01 recibe el aviso de su deuda de 20 Bs
    renta = create_rental(
        cl01, mes01, local_datetime(2026, 10, 1, 18), local_datetime(2026, 10, 3, 9), registered_by=op01, picked_up_now=True
    )
    mail.outbox.clear()
    with django_capture_on_commit_callbacks(execute=True), con_la_hora(local_datetime(2026, 10, 3, 12, 1)):
        register_return(renta, op01, "Llegó bien")
    [correo] = mail.outbox
    assert (correo.to, correo.subject) == (["cl01@correo.com"], "Tienes una deuda de 20,00 Bs")


def test_si_el_correo_falla_la_cuenta_se_crea_y_el_log_dice_email_failed(db, caplog, django_capture_on_commit_callbacks):
    # El servidor de correo no responde al crear la cuenta de Lucía -> la cuenta queda creada y el log escribe EMAIL_FAILED
    sin_conexion = smtplib.SMTPException("sin conexión")
    with mock.patch("rentals.services.notifications.send_mail", side_effect=sin_conexion):
        with django_capture_on_commit_callbacks(execute=True):
            register_client(DATOS)
    # Comprueba que la cuenta se creó
    assert get_user_model().objects.filter(username="cl03").exists()
    # Comprueba la línea del error, sin detalles técnicos del servidor
    assert caplog.messages[-1] == 'EMAIL_FAILED to=cl03 subject="Bienvenido a SergioCorp" error=SMTPException'


def test_volver_a_cero_la_demo_vacia_el_log_y_empieza_con_demo_reset(db, settings, tmp_path, caplog):
    # El log tiene líneas de pruebas viejas y se corre seed_demo -> el archivo se vacía y la primera línea es DEMO_RESET
    log_viejo = tmp_path / "negocio.log"
    log_viejo.write_text("2026-10-27 10:00:00 | INFO    | RENTAL_CREATED id=1\n", encoding="utf-8")
    settings.BUSINESS_LOG_FILE = log_viejo
    call_command("seed_demo", stdout=StringIO())
    # Comprueba que no quedó la línea vieja (en las pruebas el log va solo a la consola)
    assert log_viejo.read_text(encoding="utf-8") == ""
    # Comprueba que DEMO_RESET va primero y que el escenario se creó
    assert (caplog.messages[0], Equipment.objects.count()) == ("DEMO_RESET", 20)
