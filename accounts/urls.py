"""Login and logout pages (PRE-CU-01, steps 1 to 3)."""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from .forms import LoginForm

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            authentication_form=LoginForm,
            # A client who is already logged in goes straight to the catalog.
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    # LogoutView only accepts POST, so the logout button is a small form.
    path("logout/", LogoutView.as_view(), name="logout"),
]
