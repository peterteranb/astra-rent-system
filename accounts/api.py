"""API de la sesión y de las cuentas: token CSRF, login, logout, «quién soy», registro del cliente (CU-01), clientes en la tienda (CU-02) y «Mi cuenta» (CU-17).

Usa la sesión normal de Django y las mismas funciones que las páginas.
"""
from django.contrib.auth import login, logout, update_session_auth_hash
from django.middleware.csrf import get_token
from django.views.decorators.csrf import ensure_csrf_cookie

from rentals.api.responses import api_view, read_json, success, valid_form
from rentals.api.serializers import money, user_data
from rentals.services.formatting import account_created_message, store_account_message
from rentals.use_cases.debts import debt_total_of
from rentals.use_cases.renting import find_clients

from .account import update_profile
from .forms import (
    RESET_EMAIL_TEMPLATE,
    RESET_SUBJECT_TEMPLATE,
    AccountPasswordChangeForm,
    ClientPasswordResetForm,
    LoginForm,
    ProfileForm,
    SignUpForm,
    StoreSignUpForm,
)
from .registration import SignUpData, register_client, register_store_client
from .roles import OPERATOR
from .views import site_url

RESET_REQUESTED_MESSAGE = "Si el correo es de una cuenta activa, te mandamos un enlace para crear tu contraseña."


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
    data = valid_form(SignUpForm(read_json(request)))
    user = register_client(SignUpData(**data))
    return success(user_data(user), account_created_message(user), status=201)


@api_view("GET", "POST", roles=[OPERATOR])
def store_clients(request):
    """GET busca clientes por usuario, nombre, apellido o correo; POST crea la cuenta en la tienda, sin contraseña (CU-02)."""
    if request.method == "GET":
        return success([user_data(user) for user in find_clients(request.GET.get("q", ""))])
    data = valid_form(StoreSignUpForm(read_json(request)))
    registration = register_store_client(SignUpData(**data), request.user, site_url(request))
    return success(
        {**user_data(registration.user), "email_sent": registration.email_sent},
        store_account_message(registration),
        status=201,
    )


@api_view("POST")
def update_my_profile(request):
    """Guarda el nombre, apellido, correo y teléfono del usuario con sesión (CU-17)."""
    data = valid_form(ProfileForm(read_json(request)))
    user = update_profile(request.user, **data)
    return success(me_data(user), "Tus datos se guardaron.")


@api_view("POST")
def change_password(request):
    """Cambia la contraseña con el formulario de Django y deja la sesión abierta (CU-17)."""
    form = AccountPasswordChangeForm(request.user, read_json(request))
    valid_form(form)
    form.save()
    update_session_auth_hash(request, form.user)
    return success(None, "Tu contraseña se cambió.")


@api_view("POST", public=True)
def request_password_reset(request):
    """Manda el enlace de Django para crear una contraseña nueva; responde lo mismo exista o no la cuenta (CU-17)."""
    form = ClientPasswordResetForm(read_json(request))
    valid_form(form)
    form.save(
        request=request,
        use_https=request.is_secure(),
        email_template_name=RESET_EMAIL_TEMPLATE,
        subject_template_name=RESET_SUBJECT_TEMPLATE,
    )
    return success(None, RESET_REQUESTED_MESSAGE)
