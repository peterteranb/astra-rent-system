"""Páginas de registro de clientes, login, cierre de sesión, «Mi cuenta» y recuperar la contraseña con las vistas de Django."""
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views
from .forms import (
    RESET_EMAIL_TEMPLATE,
    RESET_SUBJECT_TEMPLATE,
    ClientPasswordResetForm,
    LoginForm,
    ResetSetPasswordForm,
)

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            # Quien ya tiene sesión va directo a la página de su rol.
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    # LogoutView solo acepta POST: el botón de cerrar sesión es un formulario.
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", views.sign_up, name="sign_up"),
    path("staff/clients/new/", views.register_client_at_store, name="register_client_at_store"),
    path("account/", views.my_account, name="my_account"),
    path("account/password/", views.PasswordChangeView.as_view(), name="password_change"),
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            form_class=ClientPasswordResetForm,
            template_name="accounts/password_reset_form.html",
            email_template_name=RESET_EMAIL_TEMPLATE,
            subject_template_name=RESET_SUBJECT_TEMPLATE,
        ),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            form_class=ResetSetPasswordForm, template_name="accounts/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
