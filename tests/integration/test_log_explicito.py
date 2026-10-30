"""Prueba que cada línea del log de rentas, pagos, deudas y cuentas se entiende sin buscar en la base, y que
los rechazos llevan lo que se intentó (ENT-101)."""
import pytest

from accounts.registration import SignUpData, register_client
from rentals.errors import EquipmentNotAvailableError, InvalidModificationError, RegistrationRejectedError
from rentals.use_cases.handover import register_return
from rentals.use_cases.renting import create_rental, modify_rental
from tests.helpers import con_la_hora, foto_de_la_base, local_datetime, renta_entregada

HOY = local_datetime(2026, 10, 29, 10)


def test_un_rechazo_por_fechas_ocupadas_lleva_cliente_equipo_y_fechas_pedidas(cl01, cl02, mes01, caplog):
    # cl02 pide del 06/11 al 07/11 un equipo que cl01 ya tiene -> RENTAL_REJECTED con lo pedido, el motivo y quién
    with con_la_hora(HOY):
        create_rental(cl01, mes01, local_datetime(2026, 11, 5, 18), local_datetime(2026, 11, 7, 9))
        caplog.clear()
        antes = foto_de_la_base()
        with pytest.raises(EquipmentNotAvailableError):
            create_rental(cl02, mes01, local_datetime(2026, 11, 6, 18), local_datetime(2026, 11, 7, 9))
    # Comprueba la línea con los datos intentados
    assert caplog.messages == [
        'RENTAL_REJECTED equipment=MES-00001 "Mesa plegable 1,80 m" client=cl02 "Diego Rojas" '
        "period=06/11/2026 18:00-07/11/2026 09:00 "
        'reason="El equipo MES-00001 está ocupado del 05/11/2026 18:00 al 07/11/2026 09:00." by=cl02'
    ]
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_un_rechazo_al_modificar_lleva_las_fechas_que_se_pidieron(cl01, mes01, caplog):
    # cl01 quiere pasar su reserva de 2 días a 1 día -> MODIFY_REJECTED con las fechas nuevas pedidas
    with con_la_hora(HOY):
        reserva = create_rental(cl01, mes01, local_datetime(2026, 11, 5, 18), local_datetime(2026, 11, 7, 9))
        caplog.clear()
        antes = foto_de_la_base()
        with pytest.raises(InvalidModificationError):
            modify_rental(reserva, local_datetime(2026, 11, 10, 18), local_datetime(2026, 11, 11, 9), cl01)
    # Comprueba que la línea tiene la renta y el periodo pedido
    assert caplog.messages[0].startswith(
        f'MODIFY_REJECTED rental={reserva.pk} equipment=MES-00001 "Mesa plegable 1,80 m" client=cl01 "Carla Mendoza" '
        "period=10/11/2026 18:00-11/11/2026 09:00 amount=40.00 reason="
    )
    # Comprueba que la base quedó igual
    assert foto_de_la_base() == antes


def test_la_deuda_por_atraso_dice_su_monto_su_renta_y_quien_la_registro(cl01, op01, mes01, caplog):
    # MES-00001 vence el 03/10 y op01 la recibe a las 12:01 -> DEBT_CREATED con la deuda de 20 Bs y la renta
    renta = renta_entregada(cl01, mes01, local_datetime(2026, 10, 1, 18), local_datetime(2026, 10, 3, 9), op01)
    with con_la_hora(local_datetime(2026, 10, 3, 12, 1)):
        register_return(renta, op01, "Llegó bien")
    deuda = renta.debts.get()
    # Comprueba la línea de la deuda
    assert caplog.messages[-1] == (
        f'DEBT_CREATED debt={deuda.pk} charge=late_return rental={renta.pk} equipment=MES-00001 "Mesa plegable 1,80 m" '
        'client=cl01 "Carla Mendoza" period=01/10/2026 18:00-03/10/2026 09:00 amount=20.00 by=op01'
    )
    # Comprueba que la deuda guardada es la del log
    assert deuda.amount == 20


def test_un_registro_rechazado_lleva_usuario_correo_y_motivo_sin_la_contrasena(db, caplog):
    # juan23 elige una contraseña muy común en la web -> ACCOUNT_REJECTED con su usuario, su correo y el motivo
    datos = SignUpData("Juan", "Pérez", "juan@correo.com", "71234567", "juan23", "Password1", "Password1")
    antes = foto_de_la_base()
    with pytest.raises(RegistrationRejectedError):
        register_client(datos)
    # Comprueba la línea, igual al ejemplo del cliente y sin la contraseña
    assert caplog.messages == [
        'ACCOUNT_REJECTED username=juan23 email=juan@correo.com reason="Esta contraseña es demasiado común." by=web'
    ]
    # Comprueba que no se creó la cuenta
    assert foto_de_la_base() == antes
