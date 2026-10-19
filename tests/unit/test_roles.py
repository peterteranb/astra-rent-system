"""Prueba rentals/roles.py: has_role(), quién tiene cada rol del personal
(ENT-13: el superusuario puede hacer todo)."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser

from rentals.roles import MAINTENANCE, OPERATOR, has_role


def test_el_superusuario_tiene_todos_los_roles():
    # ad01 es superusuario sin grupos -> es operador y también mantenimiento
    ad01 = get_user_model()(username="ad01", is_superuser=True)
    # Comprueba el rol de operador
    assert has_role(ad01, OPERATOR) is True
    # Comprueba el rol de mantenimiento
    assert has_role(ad01, MAINTENANCE) is True


def test_un_visitante_sin_sesion_no_tiene_ningun_rol():
    # Alguien sin sesión -> no es operador ni mantenimiento
    visitante = AnonymousUser()
    # Comprueba el rol de operador
    assert has_role(visitante, OPERATOR) is False
    # Comprueba el rol de mantenimiento
    assert has_role(visitante, MAINTENANCE) is False
