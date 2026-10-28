"""Páginas de CU-01 y CU-02: el cliente crea su cuenta en la web y el operador la crea en la tienda.

Leen la petición, llaman a registration.register_client y eligen la plantilla; las reglas están ahí.
"""
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse

from rentals.errors import RejectedWithCausesError
from rentals.roles import OPERATOR, role_required

from .forms import SignUpForm
from .registration import REJECTION_TITLE, SignUpData, register_client


def sign_up(request):
    """Muestra el registro del cliente y crea su cuenta; con éxito lo lleva a iniciar sesión (CU-01)."""
    if request.user.is_authenticated:
        return redirect("home")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = try_to_register(form)
        if user:
            messages.success(request, f"Cuenta creada. Ya puedes iniciar sesión con {user.username}.")
            return redirect("login")
    return render(request, "accounts/signup.html", signup_context(form, at_store=False))


@role_required(OPERATOR)
def register_client_at_store(request):
    """Muestra el registro para el operador y crea la cuenta del cliente; luego lo deja listo para rentarle (CU-02)."""
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = try_to_register(form, registered_by=request.user)
        if user:
            messages.success(request, f"Cuenta creada para {user.username}. Ya puedes registrar su renta.")
            return redirect(f"{reverse('walk_in_rental')}?q={user.username}")
    return render(request, "accounts/signup.html", signup_context(form, at_store=True))


def try_to_register(form, registered_by=None):
    """Llama a register_client; si se rechaza, pone cada causa en el formulario y devuelve None."""
    try:
        return register_client(SignUpData(**form.cleaned_data), registered_by)
    except RejectedWithCausesError as error:
        error.add_to(form)
        return None


def signup_context(form, at_store):
    """Datos de la página de registro, en la web o en la tienda."""
    return {"form": form, "at_store": at_store, "rejection_title": REJECTION_TITLE}
