"""API de la sesión y de las cuentas: token CSRF, login, logout, «quién soy», registro del cliente (CU-01) y clientes en la tienda (CU-02).

Usa la sesión normal de Django y las mismas funciones que las páginas.
"""
from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

from rentals.api.responses import api_view, read_json, success, valid_form
from rentals.api.serializers import money, user_data
from rentals.services.formatting import account_created_message
from rentals.use_cases.payments import debt_total_of
from rentals.use_cases.renting import find_clients

from .forms import LoginForm, SignUpForm
from .registration import SignUpData, register_client
from .roles import OPERATOR


@api_view("GET", public=True)
@ensure_csrf_cookie
def csrf(request):
    """Deja la cookie csrftoken y devuelve el mismo token, para mandarlo en X-CSRFToken."""
    return success({"csrf_token": get_token(request)})


@api_view("POST", public=True)
def login_view(request):
    """Inicia la sesión de Django con usuario y contraseña; con éxito devuelve quién es."""
    form = LoginForm(request, data=read_json(request))
    valid_form(form)
    login(request, form.get_user())
    return success(me_data(request.user), f"Hola, {request.user.first_name or request.user.username}.")


@api_view("POST", public=True)
def logout_view(request):
    """Cierra la sesión, si había una."""
    logout(request)
    return success(None, "Sesión cerrada.")


@api_view("GET")
def me(request):
    """Devuelve el usuario con sesión, su rol y cuánto debe."""
    return success(me_data(request.user))


def me_data(user):
    """Datos del usuario con sesión más su deuda total sin pagar (ENT-76)."""
    return {**user_data(user), "debt_total": money(debt_total_of(user))}


@api_view("POST", public=True)
def sign_up(request):
    """Crea la cuenta de un cliente desde la web (CU-01)."""
    user = register_from(request)
    return success(user_data(user), account_created_message(user, at_store=False), status=201)


@api_view("GET", "POST", roles=[OPERATOR])
def store_clients(request):
    """GET busca clientes por usuario, nombre, apellido o correo; POST crea la cuenta en la tienda (CU-02)."""
    if request.method == "GET":
        return success([user_data(user) for user in find_clients(request.GET.get("q", ""))])
    user = register_from(request, registered_by=request.user)
    return success(user_data(user), account_created_message(user, at_store=True), status=201)


def register_from(request, registered_by=None):
    """Lee los datos del registro del cuerpo JSON y llama a register_client, como la página."""
    data = valid_form(SignUpForm(read_json(request)))
    return register_client(SignUpData(**data), registered_by)
