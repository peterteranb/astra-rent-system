# rentals/urls.py
from django.urls import path
from .views import create_rental_view

urlpatterns = [
    path('rentals/', create_rental_view, name='create_rental'),
]