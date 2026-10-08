# astra-rent-system

Sistema web de renta de mesas y sillas para eventos de SergioCorp (cliente simulado).
Proyecto P01 del curso de Ingeniería de Software, hecho con Django y PostgreSQL.
El superusuario administra equipos y rentas desde `/admin`.

**Flujo cubierto (PRE-CU-01):** login → catálogo → rentar un equipo con fecha y hora de recojo y devolución → confirmación, o rechazo con la causa (E1: equipo no disponible; E2: usuario o contraseña incorrectos).

## Requisitos

- Python 3.12 o superior (lo exige Django 6.1)
- PostgreSQL 15 o superior (lo exige Django 6.1; se probó con la 18.6) en el puerto 5432
- Git

## Puesta en marcha

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/peterteranb/astra-rent-system.git
   cd astra-rent-system
   ```
2. Crear y activar el entorno virtual.
   - Windows (PowerShell): `python -m venv .venv` y luego `.venv\Scripts\activate`.
     Si PowerShell no deja activarlo, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
   - Linux: `python3 -m venv .venv` y luego `source .venv/bin/activate`.
3. Instalar dependencias:
   ```bash
   python -m pip install -r requirements.txt
   ```
4. Copiar `.env.example` a `.env` y poner tu contraseña en `DB_PASSWORD`. El archivo `.env` no se sube a git.
5. Crear el usuario `astra` y la base `astra_rent` (usa la misma contraseña del paso 4):
   - Windows (ajusta la carpeta de la versión):
     ```powershell
     & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -v db_password=TU_CONTRASEÑA -f scripts/create_db.sql
     ```
   - Linux:
     ```bash
     psql -U postgres -h localhost -v db_password=TU_CONTRASEÑA -f scripts/create_db.sql
     ```
6. Crear las tablas y cargar los datos de demo:
   ```bash
   python manage.py migrate
   python manage.py seed_demo
   ```
7. Arrancar el servidor. Usamos el puerto 8080 porque en Windows el 8000 puede estar reservado:
   ```bash
   python manage.py runserver 8080
   ```
8. Abrir http://127.0.0.1:8080/

Después de cada `git pull`, vuelve a ejecutar `python manage.py migrate`.

## Usuarios de prueba y qué probar

`seed_demo` crea los equipos EQ-01 a EQ-06 (mesas y sillas; EQ-06 está «en revisión») y dos clientes. Se puede ejecutar varias veces: no duplica datos ni borra rentas.

| Usuario | Contraseña |
|---|---|
| `c01` | `demo1234` |
| `c02` | `demo1234` |

- **Renta exitosa:** entra como `c01`, elige EQ-01 y pide del 09/10/2026 18:00 al 12/10/2026 09:00. Verás «Renta confirmada».
- **Rechazo E1 (cruce):** cierra sesión, entra como `c02` y pide EQ-01 en las mismas fechas. Vuelves al catálogo con «El equipo EQ-01 no está disponible del 09/10/2026 18:00 al 12/10/2026 09:00.».
- **Rechazo E1 (en revisión):** EQ-06 no aparece en el catálogo; abre http://127.0.0.1:8080/equipment/EQ-06/rent/ y pide cualquier fecha.
- **Rechazo E2:** en el login usa una contraseña incorrecta. Verás «Usuario o contraseña incorrectos.».
- **Administración:** crea un superusuario con `python manage.py createsuperuser` y entra en http://127.0.0.1:8080/admin/ (ahí puedes borrar las rentas de prueba).

## Pruebas

```bash
python -m pytest -q
```

Usan una base de pruebas temporal que crea pytest-django; tu base de demo no se toca.

| Tipo | Carpeta | Cantidad |
|---|---|---|
| Unitarias (sin base de datos) | `tests/unit/` | 49 |
| Integración (base de datos, vistas y plantillas) | `tests/integration/` | 27 (1 omitida) |
| Línea base de la iteración 1 (`rent_manager`) | `tests/test_loans*.py` | 25 (4 omitidas) |
| **Total** | | **101: 96 pasan, 5 omitidas** |

Las omitidas (`skip`) corresponden a decisiones pendientes del cliente.

## Estructura

| Archivo | Para qué sirve |
|---|---|
| `config/settings.py` | Configuración de Django: base de datos desde `.env`, zona horaria America/La_Paz, idioma, plantillas y login |
| `config/urls.py` | URLs raíz: `/admin`, login/logout y páginas de renta |
| `accounts/urls.py` | Login (`LoginView`) y logout (solo POST) |
| `accounts/forms.py` | Formulario de login con el mensaje de E2 |
| `rentals/urls.py` | Catálogo, formulario de renta y confirmación |
| `rentals/views.py` | Lee la petición, llama al servicio y elige la plantilla |
| `rentals/forms.py` | Fecha (`type="date"`) y hora (lista cada 30 min) de recojo y devolución |
| `rentals/services.py` | `create_rental`: aplica las reglas, bloquea la fila del equipo y guarda la renta |
| `rentals/errors.py` | Errores de rechazo: `RentalRejectedError` y sus 3 subclases |
| `rentals/rules.py` | Reglas puras: cruce de periodos, estado, duración máxima y horarios |
| `rentals/models.py` | Modelos `Equipment` (estados de ENT-33) y `Rental` |
| `rentals/admin.py` | Pantallas de `/admin` para equipos y rentas |
| `rentals/management/commands/seed_demo.py` | Carga los datos de demo |
| `rentals/migrations/0001_initial.py` | Crea las tablas de equipos y rentas |
| `templates/base.html` | Plantilla común: cabecera, cerrar sesión y mensajes |
| `templates/accounts/login.html` | Pantalla de login |
| `templates/rentals/catalog.html` | Catálogo de equipos disponibles |
| `templates/rentals/rent_form.html` | Formulario de renta |
| `templates/rentals/rental_confirmation.html` | Confirmación de la renta |
| `static/css/style.css` | Estilos base (adaptables a celular) |
| `rent_manager/loans.py` | Código de la iteración 1, congelado como línea base de regresión |
| `tests/conftest.py` | Datos de prueba compartidos (EQ-01, C-01, C-02, fechas de los documentos) |
| `tests/helpers.py` | `local_datetime`: fechas con la zona horaria del proyecto |
| `tests/unit/test_rules.py` | Pruebas de las reglas puras |
| `tests/unit/test_check_period.py` | Pruebas de `check_period` y sus mensajes |
| `tests/unit/test_rental_form.py` | Pruebas del formulario de renta |
| `tests/integration/test_rental_service.py` | Pruebas del servicio con base de datos |
| `tests/integration/test_views.py` | Pruebas de las páginas con el cliente de pruebas de Django |
| `tests/test_loans.py`, `tests/test_loans_edge_cases.py` | Pruebas de la iteración 1 |
| `scripts/create_db.sql` | Crea el usuario y la base de PostgreSQL |
| `docs/` | Documentos de cada sesión (requisitos, modelos, plan) |

## Supuestos en el código (`# ASSUMPTION`)

Reglas que tomamos sin confirmación del cliente. Lista generada con `grep -rn "# ASSUMPTION" --include=*.py .`:

| Archivo y línea | Supuesto |
|---|---|
| `rentals/forms.py:9` | Las horas se eligen en pasos de 30 minutos. |
| `rentals/rules.py:8` | No se rechazan fechas pasadas (ENT-17: no hay límite de anticipación). |
| `rentals/rules.py:16` | El cliente elige la hora dentro de la ventana de ENT-19 (recojo desde las 18:00, devolución hasta las 09:00); fuera de ella se rechaza. |
| `rentals/rules.py:21` | La tolerancia de 5 minutos de ENT-31 vale para registrar la devolución, no para pedir la renta. |
| `rentals/rules.py:26` | Una renta de más de 5 días se rechaza (ENT-18); el plazo de 2 semanas del cliente frecuente no se aplica (ENT-20). |
| `rentals/services.py:18` | El catálogo muestra solo los equipos «disponibles» (PRE-02). |

## Equipo

- Uriel ([@peterteranb](https://github.com/peterteranb))
- Andrew ([@andrewest-andrew](https://github.com/andrewest-andrew))
- Sofia ([@arduz-in-zugzwang](https://github.com/arduz-in-zugzwang))
