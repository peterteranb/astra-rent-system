"""Integration tests for the web pages of PRE-CU-01.

They use Django's test client (the `client` fixture of pytest-django),
which sends real requests through URLs, views, the service and the
templates, and then check the database and the rendered HTML.
"""
import pytest
from pytest_django.asserts import assertContains, assertRedirects, assertTemplateUsed

from rentals.models import EquipmentStatus, Rental
from rentals.services import create_rental
from tests.conftest import DEMO_PASSWORD

pytestmark = pytest.mark.django_db

# What the browser's datetime-local inputs send for the documents' period.
DOC_FORM_DATA = {
    "start_datetime": "2026-10-09T18:00",
    "end_datetime": "2026-10-12T09:00",
}


# ---------- Login and logout (steps 1 to 3, E2) ----------

def test_login_with_correct_credentials_redirects_to_catalog(client, c01):
    # Act
    response = client.post("/login/", {"username": "c01", "password": DEMO_PASSWORD})

    # Assert: the session is open and the client lands on the catalog
    assertRedirects(response, "/")
    assert client.session["_auth_user_id"] == str(c01.pk)


def test_login_with_wrong_password_shows_e2_message(client, c01):
    # Act
    response = client.post("/login/", {"username": "c01", "password": "wrong"})

    # Assert: same page, E2 message, and no session opened
    assert response.status_code == 200
    assertTemplateUsed(response, "accounts/login.html")
    assertContains(response, "Usuario o contraseña incorrectos.")
    assert "_auth_user_id" not in client.session


def test_login_with_unknown_user_shows_e2_message(client, db):
    # Act
    response = client.post("/login/", {"username": "nobody", "password": DEMO_PASSWORD})

    # Assert
    assertContains(response, "Usuario o contraseña incorrectos.")
    assert "_auth_user_id" not in client.session


def test_catalog_requires_login(client, db):
    # Act
    response = client.get("/")

    # Assert: an anonymous visitor is sent to the login page first
    assertRedirects(response, "/login/?next=/")


def test_logout_with_post_closes_the_session(client, c01):
    # Arrange
    client.force_login(c01)

    # Act
    response = client.post("/logout/")

    # Assert
    assertRedirects(response, "/login/")
    assert "_auth_user_id" not in client.session


# ---------- Catalog (step 4) ----------

def test_catalog_lists_available_units_and_hides_units_in_review(
    client, c01, eq01, eq03_in_review
):
    # Arrange
    client.force_login(c01)

    # Act
    response = client.get("/")

    # Assert
    assertTemplateUsed(response, "rentals/catalog.html")
    assert list(response.context["equipment_list"]) == [eq01]
    assertContains(response, "EQ-01")
    assert "EQ-03" not in response.content.decode()


# ---------- Rental accepted (steps 5 to 9) ----------

def test_full_flow_login_catalog_and_accepted_rental(client, c01, eq01):
    # Arrange: log in through the real login form
    client.post("/login/", {"username": "c01", "password": DEMO_PASSWORD})

    # Act: open the catalog, then the unit's form, then send the dates
    catalog = client.get("/")
    form_page = client.get("/equipment/EQ-01/rent/")
    response = client.post("/equipment/EQ-01/rent/", DOC_FORM_DATA, follow=True)

    # Assert: each page rendered its template
    assertContains(catalog, "/equipment/EQ-01/rent/")
    assertTemplateUsed(form_page, "rentals/rent_form.html")
    assertTemplateUsed(response, "rentals/rental_confirmation.html")

    # Assert: the database has exactly the confirmed rental
    rental = Rental.objects.get()
    assert rental.client == c01
    assert rental.equipment == eq01
    assertRedirects(response, f"/rentals/{rental.pk}/")

    # Assert: the confirmation shows unit, local dates and pickup hour
    assertContains(response, "Renta confirmada")
    assertContains(response, "EQ-01")
    assertContains(response, "09/10/2026 18:00")
    assertContains(response, "12/10/2026 09:00")
    assertContains(response, "desde las 18:00")


def test_client_cannot_see_another_clients_confirmation(
    client, c01, c02, eq01, doc_start, doc_end
):
    # Arrange: C-01 owns the rental, C-02 is logged in
    rental = create_rental(c01, eq01, doc_start, doc_end)
    client.force_login(c02)

    # Act
    response = client.get(f"/rentals/{rental.pk}/")

    # Assert
    assert response.status_code == 404


# ---------- Rental rejected (E1) ----------

def test_overlapping_rental_is_rejected_and_client_returns_to_catalog(
    client, c01, c02, eq01, doc_start, doc_end
):
    # Arrange: C-01 confirmed EQ-01 first; C-02 is logged in
    create_rental(c01, eq01, doc_start, doc_end)
    client.force_login(c02)

    # Act: C-02 asks for the same unit and period
    response = client.post("/equipment/EQ-01/rent/", DOC_FORM_DATA, follow=True)

    # Assert: back on the catalog with a message naming unit and dates
    assertRedirects(response, "/")
    assertTemplateUsed(response, "rentals/catalog.html")
    assertContains(response, "El equipo EQ-01 no está disponible del 09/10/2026 18:00 al 12/10/2026 09:00.")

    # Assert: only C-01's rental exists
    assert Rental.objects.get().client == c01
    assert not Rental.objects.filter(client=c02).exists()


def test_unit_in_review_is_rejected_and_client_returns_to_catalog(
    client, c01, eq03_in_review
):
    # Arrange
    client.force_login(c01)

    # Act
    response = client.post("/equipment/EQ-03/rent/", DOC_FORM_DATA, follow=True)

    # Assert: E1 message, no rental, status unchanged (PRE-RF-04)
    assertRedirects(response, "/")
    assertContains(response, "El equipo EQ-03 no está disponible (estado: En revisión).")
    assert not Rental.objects.exists()
    eq03_in_review.refresh_from_db()
    assert eq03_in_review.status == EquipmentStatus.IN_REVIEW


def test_pickup_outside_allowed_hours_stays_on_form_with_message(client, c01, eq01):
    # Arrange
    client.force_login(c01)
    early_pickup = {**DOC_FORM_DATA, "start_datetime": "2026-10-09T17:00"}

    # Act
    response = client.post("/equipment/EQ-01/rent/", early_pickup)

    # Assert: the form is shown again with the cause; nothing saved
    assert response.status_code == 200
    assertTemplateUsed(response, "rentals/rent_form.html")
    assertContains(response, "El recojo debe ser desde las 18:00.")
    assert not Rental.objects.exists()


def test_missing_dates_stay_on_form_without_saving(client, c01, eq01):
    # Arrange
    client.force_login(c01)

    # Act
    response = client.post("/equipment/EQ-01/rent/", {})

    # Assert
    assert response.status_code == 200
    assert response.context["form"].errors
    assert not Rental.objects.exists()


# ---------- Unit that does not exist ----------

def test_form_of_unit_not_in_inventory_returns_404(client, c01, eq01):
    # Arrange
    client.force_login(c01)

    # Act
    response = client.get("/equipment/EQ-999/rent/")

    # Assert
    assert response.status_code == 404


def test_rental_of_unit_not_in_inventory_returns_404_and_saves_nothing(
    client, c01, eq01
):
    # Arrange
    client.force_login(c01)

    # Act
    response = client.post("/equipment/EQ-999/rent/", DOC_FORM_DATA)

    # Assert
    assert response.status_code == 404
    assert not Rental.objects.exists()


@pytest.mark.skip(reason="Pending client decision: are inventory numbers case-sensitive? (Sesión 04)")
def test_inventory_number_in_lowercase_finds_the_same_unit(client, c01, eq01):
    # Arrange
    client.force_login(c01)

    # Act: today "eq-01" does not match "EQ-01" and answers 404
    response = client.get("/equipment/eq-01/rent/")

    # Assert
    assert response.status_code == 200
