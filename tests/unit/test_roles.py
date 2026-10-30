"""Prueba accounts/roles.py: has_role(), verificando la asignación de roles y privilegios para administrador, operador y visitantes."""
from django.contrib.auth.models import AnonymousUser

from accounts.models import Role, User
from accounts.roles import ADMINISTRATOR, MAINTENANCE, OPERATOR, has_role


def test_verificacion_de_roles_para_administrador_operador_y_visitantes():
    # Administrador posee todos los roles; operador no tiene rol de mantenimiento; visitante sin sesión carece de privilegios -> jerarquía de roles
    # Comprueba que el administrador agrupa los roles de operador y mantenimiento
    ad01 = User(username="ad01", role=Role(code=ADMINISTRATOR))
    assert has_role(ad01, OPERATOR) is True
    assert has_role(ad01, MAINTENANCE) is True

    # Comprueba que un usuario operador posee el rol de operador pero no el de mantenimiento
    op01 = User(username="op01", role=Role(code=OPERATOR))
    assert has_role(op01, OPERATOR) is True
    assert has_role(op01, MAINTENANCE) is False

    # Comprueba que un usuario anónimo o visitante sin sesión no cuenta con ningún rol operativo
    visitante = AnonymousUser()
    assert has_role(visitante, OPERATOR) is False
    assert has_role(visitante, MAINTENANCE) is False