"""Páginas de login y de cierre de sesión."""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

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
]
