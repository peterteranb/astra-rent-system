# astra-rent-system

Sistema web de renta de mesas y sillas para eventos de SergioCorp (cliente simulado), hecho con Django 6.1 y PostgreSQL.

- **Cliente:** crea su cuenta, busca equipos libres, renta y paga con un QR simulado, modifica o cancela sus reservas y ve su deuda.
- **Operador:** crea cuentas y rentas en la tienda, entrega (cobrando si falta el pago), recibe devoluciones y cobra deudas.
- **Mantenimiento:** revisa lo que vuelve: disponible, en reparación o de baja (con su deuda).
- **Administrador:** registra equipos, ve el panel del responsable y gestiona todo desde `/admin`.

La documentación está en [docs/README.md](docs/README.md): casos de uso, arquitectura, base de datos y respuestas del cliente.

## Camino A: con Docker (recomendado)

Necesitas [Docker Desktop](https://www.docker.com/products/docker-desktop/) abierto y Git.

1. Clonar el repositorio:
   ```powershell
   git clone https://github.com/peterteranb/astra-rent-system.git
   cd astra-rent-system
   ```
2. Crear el archivo de configuración. Ya funciona tal cual para probar; antes de publicar el sitio cambia `DB_PASSWORD` y `SECRET_KEY`:
   ```powershell
   copy .env.example .env
   ```
   Si Windows tiene reservado el puerto 8000, pon `WEB_PORT=8080` en `.env`.
3. Levantar la base y la web (la primera vez descarga las imágenes y tarda unos minutos). Está lista cuando dice `Listening at: http://0.0.0.0:8000`:
   ```powershell
   docker compose up --build
   ```
4. En otra terminal, cargar la demo:
   ```powershell
   docker compose exec web python manage.py seed_demo
   ```
5. Abrir http://localhost:8000 (o el puerto que pusiste en `WEB_PORT`).

Para detener: `Ctrl+C` o `docker compose down`. Los datos quedan en el volumen `pgdata`; para borrarlos: `docker compose down -v`.

## Camino B: a mano en Windows con PowerShell

Necesitas Python 3.12 o superior (lo exige Django 6.1), PostgreSQL 15 o superior en el puerto 5432 y Git.

1. Clonar el repositorio (igual que en el camino A).
2. Crear y activar el entorno virtual. Si PowerShell no deja activarlo, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instalar dependencias:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Crear `.env` y editarlo: pon tu contraseña en `DB_PASSWORD` y, para programar, `DEBUG=True`:
   ```powershell
   copy .env.example .env
   notepad .env
   ```
5. Crear el usuario `astra` y la base `astra_rent` con la misma contraseña del paso 4 (ajusta la carpeta a tu versión de PostgreSQL):
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -v db_password=TU_CONTRASEÑA -f scripts/create_db.sql
   ```
6. Crear las tablas y cargar la demo:
   ```powershell
   python manage.py migrate
   python manage.py seed_demo
   ```
7. Arrancar el servidor y abrir http://127.0.0.1:8080/:
   ```powershell
   python manage.py runserver 8080
   ```

Con `DEBUG=False` corre antes `python manage.py collectstatic --noinput`, para que se vean los estilos.
Después de cada `git pull`, vuelve a ejecutar `python manage.py migrate`.

## Usuarios de la demo

Todos usan la clave `Demo1234`.

| Usuario | Quién es | Qué ve al entrar |
|---|---|---|
| `cl01` | Carla Mendoza, cliente | Catálogo, «Mis rentas» con sus reservas, pagos y botones para modificar o cancelar |
| `cl02` | Diego Rojas, cliente con deuda | Lo mismo, con su deuda de 22,50 Bs: no puede rentar hasta pagarla |
| `op01` | Olga Pérez, operadora | Reservas por entregar, renta en tienda, nuevo cliente, devoluciones y deudas |
| `mt01` | Mario Torres, mantenimiento | Los equipos en revisión o en reparación |
| `ad01` | Ana Díaz, administradora | El panel del responsable, el registro de equipos y el admin de Django |

`seed_demo` crea 8 mesas (`MES-00001` a `MES-00008`) y 12 sillas (`SIL-00001` a `SIL-00012`) y deja listo un caso para cada demostración: una reserva pagada para hoy, una con el pago pendiente, una devolución atrasada, una renta vencida, un equipo en revisión, uno en reparación, uno de baja y la deuda de `cl02`. Al terminar imprime para qué sirve cada equipo.

**Volver a cero:** `python manage.py seed_demo` (con Docker: `docker compose exec web python manage.py seed_demo`). Es solo para la demo: borra deudas, rentas, historial y equipos y crea el mismo escenario con fechas relativas a hoy. No manda correos.

## Ver los logs

Cada operación escribe una línea, aceptada o rechazada:

```text
2026-10-29 10:15:02 | INFO    | RENTAL_CREATED id=12 equipment=SIL-00001 client=cl01 paid=no registered_by=web
2026-10-29 10:16:40 | WARNING | RENTAL_REJECTED reason="Tienes una deuda pendiente de 22,50 Bs. Págala en la tienda para volver a rentar."
```

- Con Docker: `docker compose logs -f web`
- A mano: `Get-Content logs\negocio.log -Wait`

## Correo

Por defecto los correos (bienvenida, renta confirmada, renta cancelada y deuda) se imprimen en la consola. Para mandarlos de verdad con Gmail:

1. En la cuenta de Google, activa la verificación en dos pasos y crea una **contraseña de aplicación** en https://myaccount.google.com/apppasswords.
2. En `.env` pon `EMAIL_HOST_USER=tu.correo@gmail.com` y `EMAIL_HOST_PASSWORD=` con las 16 letras de esa contraseña.
3. Reinicia el servidor. Si un correo falla, la operación sigue y el log escribe `EMAIL_FAILED`.

## Pruebas

```powershell
python -m pytest -q
```

Usan una base temporal que crea pytest-django; la base de la demo y `logs/negocio.log` no se tocan.

| Tipo | Carpeta | Pruebas | Tiempo |
|---|---|---|---|
| Unitarias (sin base de datos) | `tests/unit/` | 90 | 0,3 s |
| Integración (casos de uso con la base, el log y el correo) | `tests/integration/` | 74 | 4,2 s |
| Sistema (recorridos por la web) | `tests/system/` | 11 | 2,8 s |
| **Total** | | **175** | **5,6 s** |

Los tiempos de integración y sistema incluyen crear la base de pruebas.

## Producción

- `.env` define `SECRET_KEY` (obligatoria con `DEBUG=False`), `DEBUG` (por defecto `False`), `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` y los datos de la base.
- `USE_HTTPS=True` activa las cookies seguras, la redirección a HTTPS y HSTS; úsalo solo si el sitio está detrás de HTTPS.
- Los estáticos los sirve whitenoise y la web corre con gunicorn dentro de Docker.
- Las páginas de error 403, 404 y 500 están en español y nunca muestran detalles técnicos.

## Estructura

| Carpeta | Qué tiene |
|---|---|
| `config/` | Configuración de Django, URLs raíz y la configuración de las pruebas |
| `accounts/` | Usuario con rol y teléfono, roles, registro de clientes y login |
| `rentals/` | Modelos, reglas puras (`rules.py`), casos de uso (`renting.py`, `payments.py`, `handover.py`, `review.py`, `inventory.py`, `dashboard.py`, `history.py`), log (`events.py`), correos (`notifications.py`), vistas y admin |
| `rentals/management/commands/` | `seed_demo`, el escenario de la demo |
| `templates/` | Páginas HTML; `includes/` tiene las partes que se repiten |
| `static/` | Estilos del sitio y del admin, y el logo |
| `tests/` | Pruebas unitarias, de integración y de sistema |
| `scripts/` | SQL que crea el usuario y la base de PostgreSQL (camino B) |
| `docs/` | Documentación: ver [docs/README.md](docs/README.md) |

## Equipo

- Uriel ([@peterteranb](https://github.com/peterteranb))
- Andrew ([@andrewest-andrew](https://github.com/andrewest-andrew))
- Sofia ([@arduz-in-zugzwang](https://github.com/arduz-in-zugzwang))
