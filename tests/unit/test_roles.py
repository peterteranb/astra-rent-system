"""Prueba accounts/roles.py: has_role(), quién tiene cada rol (ENT-13: el administrador puede hacer todo)."""
from django.contrib.auth.models import AnonymousUser

from accounts.models import Role, User
from accounts.roles import ADMINISTRATOR, MAINTENANCE, OPERATOR, has_role


def test_el_administrador_tiene_todos_los_roles():
    # ad01 tiene el rol administrador -> es operador y también mantenimiento
    ad01 = User(username="ad01", role=Role(code=ADMINISTRATOR))
    # Comprueba el rol de operador
    assert has_role(ad01, OPERATOR) is True
    # Comprueba el rol de mantenimiento
    assert has_role(ad01, MAINTENANCE) is True


def test_el_operador_no_tiene_el_rol_de_mantenimiento():
    # op01 es operador -> es operador pero no mantenimiento
    op01 = User(username="op01", role=Role(code=OPERATOR))
    # Comprueba el rol de operador
    assert has_role(op01, OPERATOR) is True
    # Comprueba el rol de mantenimiento
    assert has_role(op01, MAINTENANCE) is False


def test_un_visitante_sin_sesion_no_tiene_ningun_rol():
    # Alguien sin sesión -> no es operador ni mantenimiento
    visitante = AnonymousUser()
    # Comprueba el rol de operador
    assert has_role(visitante, OPERATOR) is False
    # Comprueba el rol de mantenimiento
    assert has_role(visitante, MAINTENANCE) is False
