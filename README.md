# astra-rent-system

Sistema web de renta de mesas y sillas para eventos de SergioCorp (cliente simulado), hecho con Django 6.1 y PostgreSQL.

- **Cliente:** crea su cuenta, busca equipos libres, renta y paga con un QR simulado, modifica o cancela sus reservas, ve su deuda y gestiona su cuenta en «Mi cuenta».
- **Operador:** crea cuentas (sin conocer la contraseña del cliente) y rentas en la tienda, entrega (cobrando si falta el pago), recibe devoluciones y cobra deudas.
- **Mantenimiento:** revisa lo que vuelve: disponible, en reparación o de baja (con su deuda).
- **Administrador:** registra equipos, ve el panel del responsable y gestiona todo desde `/admin`.

La documentación está en [docs/README.md](docs/README.md): casos de uso, requisitos, arquitectura, base de datos, respuestas del cliente y decisiones del equipo.

## Instalar en Windows con PowerShell

Necesitas Python 3.12 o superior (lo exige Django 6.1), PostgreSQL 15 o superior en el puerto 5432 y Git.

1. Clonar el repositorio:
   ```powershell
   git clone https://github.com/peterteranb/astra-rent-system.git
   cd astra-rent-system
   ```
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
7. Arrancar el servidor de desarrollo y abrir http://127.0.0.1:8080/:
   ```powershell
   python manage.py runserver 8080
   ```

Después de cada `git pull`, vuelve a ejecutar `python -m pip install -r requirements.txt` y `python manage.py migrate`.

## Actualizar tu máquina (para el equipo)

Si ya tenías el proyecto de una versión anterior:

1. En `.env`, para programar, agrega estas dos líneas. `DEBUG` ahora es `False` si no se dice otra cosa, y entonces exige `SECRET_KEY`:
   ```text
   DEBUG=True
   SECRET_KEY=cualquier-clave-larga-para-tu-maquina
   ```
2. Instala las dependencias nuevas (whitenoise y waitress):
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Reinicia la base local: el usuario personalizado cambió las tablas y la demo se vuelve a crear:
   ```powershell
   python manage.py shell -c "from django.db import connection; connection.cursor().execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')"
   python manage.py migrate
   python manage.py seed_demo
   ```
   Si el primer comando falla por permisos, borra y crea la base como `postgres` (ajusta la carpeta a tu versión) y después corre `migrate` y `seed_demo`:
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -c "DROP DATABASE astra_rent;" -c "CREATE DATABASE astra_rent OWNER astra;"
   ```

## Correr como en producción

`runserver` es solo para programar. En producción la web corre con waitress, un servidor web de producción en Python puro que funciona en Windows, y whitenoise sirve los estilos:

```powershell
# en .env: DEBUG=False, una SECRET_KEY propia y ALLOWED_HOSTS=localhost,127.0.0.1
python manage.py collectstatic --noinput
python -m waitress --port=8080 config.wsgi:application
```

- Abre http://localhost:8080/. El log de negocio sale en esa terminal y en `logs/negocio.log`. Para detenerlo: `Ctrl+C`.
- Vuelve a correr `collectstatic` cada vez que cambie algo en `static/`.
- `USE_HTTPS=True` activa las cookies seguras, la redirección a HTTPS y HSTS; úsalo solo si el sitio está detrás de HTTPS.
- Las páginas de error 403, 404 y 500 están en español y nunca muestran detalles técnicos.

## Usuarios de la demo

Todos usan la clave `Demo1234`.

| Usuario | Quién es | Qué ve al entrar |
|---|---|---|
| `cl01` | Carla Mendoza, cliente | Catálogo, «Mis rentas» con sus reservas, pagos y botones para modificar o cancelar |
| `cl02` | Diego Rojas, cliente con deuda | Lo mismo, con su deuda de 12,00 Bs: no puede rentar hasta pagarla |
| `op01` | Olga Pérez, operadora | Reservas por entregar, renta en tienda, nuevo cliente, devoluciones y deudas |
| `mt01` | Mario Torres, mantenimiento | Todos los equipos que no están de baja, el último que cambió primero, con el filtro por estado y la casilla para cobrar el daño |
| `ad01` | Ana Díaz, administradora | El panel del responsable, el registro de equipos y el admin de Django |

`seed_demo` crea 30 equipos (12 mesas, 16 sillas y 2 combos, un equipo más cada uno que no descuenta las sillas y mesas sueltas), 8 clientes más (`cl03` a `cl10`) y rentas repartidas en el tiempo: devueltas a tiempo, en tolerancia y con atraso, deudas pagadas y pendientes, rentas de hoy y reservas de los próximos días. Deja listo un caso para cada demostración: una reserva pagada para hoy, una con el pago pendiente, una devolución atrasada, una renta vencida, un equipo en revisión, uno en reparación, uno de baja y la deuda de `cl02`. Al terminar imprime para qué sirve cada equipo.

**Volver a cero:** `python manage.py seed_demo`. Es solo para la demo y el desarrollo: con `DEBUG=False` se niega a correr («seed_demo borra los datos de la demo; solo se usa con DEBUG=True»). Vacía `logs/negocio.log`, borra todos los usuarios, deudas, rentas, historial y equipos y crea la misma demo con fechas relativas a hoy. No manda correos.

## Mi cuenta y la contraseña

- **Mi cuenta** (`/account/`, en el menú de todos): cada usuario edita su nombre, apellido, correo y teléfono, con las mismas reglas del registro. El usuario y el rol no se cambian.
- **Cambiar contraseña** (`/account/password/`): la vista de Django; pide la actual y usa los mismos validadores del registro. La sesión sigue abierta.
- **Olvidé mi contraseña** (enlace en el login, `/password-reset/`): el flujo de Django por correo. El enlace abre una página para escribir la contraseña nueva.
- **Cliente creado en la tienda:** el operador **no** escribe la contraseña. La cuenta nace sin contraseña y el cliente recibe «Crea tu contraseña de SergioCorp» con el enlace de Django. Si el correo falla, el operador ve «La cuenta se creó, pero no se pudo enviar el correo. Pide al cliente que use "Olvidé mi contraseña" con su correo.».
- En la demo los correos salen en la consola: copia el enlace de la terminal al navegador.

## El log de negocio: `logs/negocio.log`

Es el registro de cada acción del sistema, aceptada o rechazada: sirve para auditar quién hizo qué y cuándo, y para mostrar en la presentación lo que pasa detrás de cada botón. Cada operación escribe una línea que se entiende sin buscar en la base; los rechazos llevan lo que se intentó:

```text
2026-10-29 19:02:11 | INFO    | PAYMENT_APPROVED rental=60 equipment=SIL-00003 "Silla blanca plegable" client=cl01 "Carla Mendoza" period=30/10/2026 18:00-01/11/2026 09:00 amount=8.00 by=cl01
2026-10-29 19:03:40 | WARNING | ACCOUNT_REJECTED username=juan23 email=juan@correo.com reason="Esta contraseña es demasiado común." by=web
```

Qué escribe cada evento: [docs/arquitectura.md](docs/arquitectura.md#eventos-del-log).

- Las líneas salen en la terminal del servidor y en el archivo. Para seguir el archivo desde otra terminal: `Get-Content logs\negocio.log -Wait`.
- El archivo crece con cada operación y se conserva entre arranques. `seed_demo` lo vacía al empezar y escribe `DEMO_RESET` como primera línea.
- Para vaciarlo a mano, aunque el servidor esté corriendo: `Clear-Content logs\negocio.log`.

## Correo

Por defecto los correos (bienvenida, «Crea tu contraseña», «Olvidé mi contraseña», renta confirmada, reserva modificada por la tienda, renta cancelada y deuda) se imprimen en la consola. Para mandarlos de verdad con Gmail:

1. En la cuenta de Google, activa la verificación en dos pasos y crea una **contraseña de aplicación** para «SergioCorp» en https://myaccount.google.com/apppasswords.
2. En `.env` pon `EMAIL_HOST_USER=tu.correo@gmail.com` y `EMAIL_HOST_PASSWORD=` con las 16 letras de esa contraseña.
3. Reinicia el servidor. Si un correo falla, la operación sigue y el log escribe `EMAIL_FAILED`.

## Pruebas

```powershell
python -m pytest -q
```

Usan una base temporal que crea pytest-django; la base de la demo y `logs/negocio.log` no se tocan.

| Tipo | Carpeta | Pruebas | Tiempo |
|---|---|---|---|
| Unitarias (sin base de datos) | `tests/unit/` | 24 | 0,1 s |
| Integración (casos de uso y API con la base, el log y el correo) | `tests/integration/` | 40 | 5,6 s |
| Sistema (recorridos por la web) | `tests/system/` | 12 | 2,3 s |
| **Total** | | **76** | **6,6 s** |

Los tiempos de integración y sistema incluyen crear la base de pruebas. Son 70 funciones de prueba; las que verifican lo mismo con otros datos usan `parametrize`, por eso hay 76 casos. La cobertura y `check --deploy` están en [docs/pruebas.md](docs/pruebas.md).

## Estructura

| Carpeta | Qué tiene |
|---|---|
| `config/` | Configuración de Django, URLs raíz y la configuración de las pruebas |
| `accounts/` | Usuario con rol y teléfono, roles (`roles.py`), registro de clientes, login y «Mi cuenta» (`account.py`) |
| `rentals/` | Modelos, reglas puras (`rules.py`), estados y errores, formularios y admin |
| `rentals/use_cases/` | Un archivo por grupo de casos de uso: `catalog`, `renting`, `payments`, `handover`, `review`, `inventory`, `history` y `dashboard` |
| `rentals/services/` | Log de negocio (`events.py`), correos (`notifications.py`) y textos para mostrar (`formatting.py`) |
| `rentals/views/` | Las páginas de cada caso de uso |
| `rentals/api/`, `accounts/api.py` | La API JSON para el frontend en React, sobre los mismos casos de uso: ver [docs/api.md](docs/api.md) |
| `rentals/management/commands/` | `seed_demo`, el escenario de la demo |
| `templates/` | Páginas HTML; `includes/` tiene las partes que se repiten |
| `static/` | Estilos del sitio y del admin, y el logo |
| `tests/` | Pruebas unitarias, de integración y de sistema |
| `scripts/` | SQL que crea el usuario y la base de PostgreSQL |
| `docs/` | Documentación: ver [docs/README.md](docs/README.md) |

## Equipo

- Uriel ([@peterteranb](https://github.com/peterteranb))
- Andrew ([@andrewest-andrew](https://github.com/andrewest-andrew))
- Sofia ([@arduz-in-zugzwang](https://github.com/arduz-in-zugzwang))
