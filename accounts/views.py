"""Páginas de CU-01, CU-02 y CU-17: el cliente crea su cuenta en la web, el operador la crea en la tienda y cada usuario gestiona la suya.

Leen la petición, llaman a registration.py o account.py y eligen la plantilla; las reglas están ahí.
"""
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy

from rentals.errors import RejectedWithCausesError
from rentals.services.formatting import account_created_message, store_account_message

from .account import PROFILE_REJECTION_TITLE, update_profile
from .forms import AccountPasswordChangeForm, ProfileForm, SignUpForm, StoreSignUpForm
from .registration import REJECTION_TITLE, SignUpData, register_client, register_store_client
from .roles import OPERATOR, role_required


def sign_up(request):
    """Muestra el registro del cliente y crea su cuenta; con éxito lo lleva a iniciar sesión (CU-01)."""
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = try_to_register(form, register_client)
        if user:
            messages.success(request, account_created_message(user))
            return redirect("login")
    return render(request, "accounts/signup.html", signup_context(form, at_store=False))


@role_required(OPERATOR)
def register_client_at_store(request):
    """Muestra el registro para el operador, sin contraseña, y crea la cuenta del cliente; luego lo deja listo para rentarle (CU-02)."""
    form = StoreSignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        registration = try_to_register(
            form, lambda data: register_store_client(data, request.user, site_url(request))
        )
        if registration:
            level = messages.SUCCESS if registration.email_sent else messages.WARNING
            messages.add_message(request, level, store_account_message(registration))
            return redirect(f"{reverse('walk_in_rental')}?q={registration.user.username}")
    return render(request, "accounts/signup.html", signup_context(form, at_store=True))


def site_url(request):
    """Dirección del sistema que ve la persona, para armar los enlaces de los correos."""
    return request.build_absolute_uri("/")


def try_to_register(form, register):
    """Llama a register con los datos del formulario; si se rechaza, pone cada causa en el formulario y devuelve None."""
    try:
        return register(SignUpData(**form.cleaned_data))
    except RejectedWithCausesError as error:
        error.add_to(form)
        return None


def signup_context(form, at_store):
    """Datos de la página de registro, en la web o en la tienda."""
    return {"form": form, "at_store": at_store, "rejection_title": REJECTION_TITLE}


@login_required
def my_account(request):
    """Muestra «Mi cuenta» y guarda el nombre, apellido, correo y teléfono nuevos (CU-17)."""
    form = ProfileForm(request.POST or None, initial=profile_of(request.user))
    if request.method == "POST" and form.is_valid():
        try:
            update_profile(request.user, **form.cleaned_data)
        except RejectedWithCausesError as error:
            error.add_to(form)
        else:
            messages.success(request, "Tus datos se guardaron.")
            return redirect("my_account")
    return render(
        request, "accounts/my_account.html", {"form": form, "rejection_title": PROFILE_REJECTION_TITLE}
    )


def profile_of(user):
    """Los datos actuales de la cuenta, para llenar el formulario."""
    return {"first_name": user.first_name, "last_name": user.last_name, "email": user.email, "phone": user.phone}


class PasswordChangeView(SuccessMessageMixin, auth_views.PasswordChangeView):
    """Cambiar la contraseña con la vista de Django: pide la actual, usa los mismos validadores y no cierra la sesión (CU-17)."""

    form_class = AccountPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("my_account")
    success_message = "Tu contraseña se cambió."
