"""Páginas de registro de clientes, login y cierre de sesión."""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import LoginForm

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            # Quien ya tiene sesión va directo a la página de su rol.
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    # LogoutView solo acepta POST: el botón de cerrar sesión es un formulario.
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", views.sign_up, name="sign_up"),
    path("staff/clients/new/", views.register_client_at_store, name="register_client_at_store"),
]
