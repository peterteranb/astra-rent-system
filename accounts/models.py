"""Tablas de cuentas: los roles del sistema y el usuario con su teléfono y su rol."""
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower

PHONE_FORMAT = r"^[0-9]{7,15}$"


class Role(models.Model):
    """Un rol del sistema (ENT-53); agregar un rol nuevo es agregar una fila."""

    CLIENT = "cliente"
    OPERATOR = "operador"
    MAINTENANCE = "mantenimiento"
    ADMINISTRATOR = "administrador"

    code = models.CharField(verbose_name="Código", max_length=20, unique=True)
    name = models.CharField(verbose_name="Nombre", max_length=50)
    description = models.CharField(verbose_name="Descripción", max_length=200)

    class Meta:
        ordering = ["name"]
        verbose_name = "Rol"
        verbose_name_plural = "Roles"

    def __str__(self):
        """Muestra el nombre del rol, por ejemplo «Operador»."""
        return self.name


class UserManager(DjangoUserManager):
    """Crea usuarios con su rol: cliente por defecto y administrador para createsuperuser."""

    def create_user(self, username, email=None, password=None, **extra_fields):
        """Crea un usuario; si no se dice el rol, es cliente."""
        extra_fields.setdefault("role", Role.objects.get(code=Role.CLIENT))
        return super().create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """Crea un administrador: el superusuario es el rol administrador (ENT-44)."""
        extra_fields["role"] = Role.objects.get(code=Role.ADMINISTRATOR)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    """Una persona con un rol; el correo y el teléfono no se repiten entre cuentas (ENT-84)."""

    email = models.EmailField(verbose_name="Correo")
    phone = models.CharField(
        verbose_name="Teléfono",
        max_length=15,
        unique=True,
        validators=[RegexValidator(PHONE_FORMAT, "El teléfono debe tener entre 7 y 15 números.")],
        error_messages={"unique": "Ya existe una cuenta con este teléfono."},
    )
    role = models.ForeignKey(
        Role, on_delete=models.PROTECT, related_name="users", verbose_name="Rol"
    )

    objects = UserManager()

    REQUIRED_FIELDS = ["email", "phone"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        constraints = [
            # Lower: Carla@correo.com y carla@correo.com son el mismo correo.
            models.UniqueConstraint(
                Lower("email"),
                name="user_email_unique_ignoring_case",
                violation_error_message="Ya existe una cuenta con este correo.",
            ),
        ]

    def save(self, *args, **kwargs):
        """Pone is_staff e is_superuser según el rol: solo el administrador entra al admin (ENT-44)."""
        is_administrator = self.role.code == Role.ADMINISTRATOR
        self.is_staff = is_administrator
        self.is_superuser = is_administrator
        super().save(*args, **kwargs)
