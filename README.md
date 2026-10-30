# astra-rent-system

Qué contiene: qué es el sistema de renta de mesas y sillas de SergioCorp, cómo instalarlo y correrlo en Windows, los usuarios de la demo, cómo crear personal, ver la base y los logs, y qué revisar antes de producción.
Cuándo leerlo: primero, para tener el sistema funcionando. La documentación completa está en [docs/README.md](docs/README.md); los IDs (ENT, D, CU, RF, RC) se explican en su [glosario de IDs](docs/README.md#glosario-de-ids).

## Qué es

Un sistema web para que SergioCorp (cliente simulado del curso) rente mesas, sillas y combos para eventos ([ENT-07](docs/respuestas-del-cliente.md#ent-07), [ENT-96](docs/respuestas-del-cliente.md#ent-96)). Está hecho con **Django** 6.1 (un framework web de Python) y **PostgreSQL** (la base de datos). Hay 4 roles y 17 casos de uso ([docs/casos-de-uso.md](docs/casos-de-uso.md)):

- **Cliente:** crea su cuenta, busca equipos libres, renta y paga con un QR simulado, modifica o cancela sus reservas, ve su deuda y gestiona su cuenta en «Mi cuenta».
- **Operador** (la persona de la tienda): crea cuentas (sin conocer la contraseña del cliente) y rentas en la tienda, entrega (cobrando si falta el pago), recibe devoluciones y cobra deudas.
- **Mantenimiento:** revisa los equipos: disponible, en revisión, en reparación o de baja, y decide si cobra el daño.
- **Administrador:** registra equipos, ve el panel del responsable y gestiona todo desde el admin de Django (`/admin/`).

Equipo: Uriel ([@peterteranb](https://github.com/peterteranb)), Andrew ([@andrewest-andrew](https://github.com/andrewest-andrew)) y Sofia ([@arduz-in-zugzwang](https://github.com/arduz-in-zugzwang)).

## Instalar en Windows

Necesitas Python 3.12 o superior (lo exige Django 6.1), PostgreSQL 15 o superior en el puerto 5432 y Git. Los comandos son para PowerShell.

1. Clonar el repositorio:
   ```powershell
   git clone https://github.com/peterteranb/astra-rent-system.git
   cd astra-rent-system
   ```
2. Crear y activar el **entorno virtual** (una carpeta `.venv` con las librerías de este proyecto, separadas de las de tu computadora). Si PowerShell no deja activarlo, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instalar las dependencias:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Crear `.env` (el archivo con la configuración y los secretos de tu máquina; nunca se sube a git) y editarlo: pon tu contraseña en `DB_PASSWORD` y, para programar, `DEBUG=True`:
   ```powershell
   copy .env.example .env
   notepad .env
   ```
5. Crear el usuario `astra` y la base `astra_rent` con la misma contraseña del paso 4 (ajusta `17` a tu versión de PostgreSQL):
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -v db_password=TU_CONTRASEÑA -f scripts/create_db.sql
   ```
6. Crear las tablas y cargar la demo. `migrate` aplica las **migraciones** (los archivos que crean las tablas) y `seed_demo` llena la base con datos de ejemplo:
   ```powershell
   python manage.py migrate
   python manage.py seed_demo
   ```

Después de cada `git pull`, vuelve a ejecutar `python -m pip install -r requirements.txt` y `python manage.py migrate`.

## Correr

Para programar, con el servidor de desarrollo de Django:

```powershell
python manage.py runserver 8080
```

Abre http://127.0.0.1:8080/ e inicia sesión con un usuario de la demo. El servidor se reinicia solo al guardar un archivo. Para detenerlo: `Ctrl+C`. Se usa el puerto 8080 porque en Windows el 8000 a veces está reservado ([D-09](docs/decisiones.md#d-09)).

## Usuarios de demo

Todos usan la clave `Demo1234`. Cada uno, al entrar, llega a la página de su rol.

| Usuario | Quién es | Qué ve al entrar |
|---|---|---|
| `cl01` | Carla Mendoza, cliente | Catálogo; en «Mis rentas», sus reservas con botones para modificar o cancelar |
| `cl02` | Diego Rojas, cliente con deuda | Lo mismo, con su deuda de 12,00 Bs: no puede rentar hasta pagarla |
| `cl03` a `cl10` | Clientes con rentas pasadas, de hoy y de los próximos días (`cl07` debe 6,00 Bs) | Catálogo y «Mis rentas» |
| `op01` | Olga Pérez, operadora | Reservas por entregar, renta en tienda, nuevo cliente, devoluciones y deudas |
| `mt01` | Mario Torres, mantenimiento | Todos los equipos que no están de baja, el último que cambió primero, con el filtro por estado y la casilla para cobrar el daño |
| `ad01` | Ana Díaz, administradora | El panel del responsable, el registro de equipos y el admin de Django |

`seed_demo` crea 30 equipos con nombres de una tienda de eventos y números de serie del fabricante: 12 mesas (plegables de 1,80 m, redondas para 10 personas y altas de cóctel), 16 sillas (plegables blancas, Tiffany doradas y de madera) y 2 combos, cada combo un equipo más que no descuenta las sillas y mesas sueltas (`CMB-00001` «Combo 6 sillas y 1 mesa» vale 3000 Bs: 150 Bs por día). También crea rentas repartidas en el tiempo: devueltas a tiempo, en tolerancia y con atraso, deudas pagadas y pendientes, rentas de hoy y reservas de los próximos días, un equipo en revisión, uno en reparación y uno de baja. Al terminar imprime una tabla con el equipo que usa cada caso de uso de la demo y para qué sirve. Con `--equipos 1000` completa el catálogo hasta 1000 equipos, para probar con muchos ([RC-01](docs/casos-de-uso.md#rc-01)).

«Mi cuenta» (`/account/`, en el menú de todos) edita nombre, apellido, correo y teléfono, y cambia la contraseña. «Olvidé mi contraseña» está en el login. En la demo los correos salen en la terminal: copia el enlace al navegador.

## Empezar de cero

Para dejar la base como nueva, con solo los datos de la demo:

```powershell
python manage.py flush --noinput
python manage.py seed_demo
```

- `flush` es un comando de Django que vacía todas las tablas (también los roles y los usuarios), sin borrarlas.
- `seed_demo` borra lo que quede (usuarios, equipos, rentas, deudas e historial, en el orden que exige la base), crea los 4 roles si faltan, vacía `logs/negocio.log`, escribe `DEMO_RESET` y crea la demo con fechas relativas a hoy ([D-41](docs/decisiones.md#d-41)). No manda correos mientras corre.
- `seed_demo` **solo corre con `DEBUG=True`**; si no, responde «seed_demo borra los datos de la demo; solo se usa con DEBUG=True».
- Basta `python manage.py seed_demo` para volver a la demo sin `flush`: también borra todos los usuarios, incluido un superusuario que hayas creado.

Si la base quedó rota (por ejemplo, de una versión con otras migraciones), bórrala y créala de nuevo como `postgres` y después corre `migrate` y `seed_demo` ([D-03](docs/decisiones.md#d-03)):

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -c "DROP DATABASE astra_rent;" -c "CREATE DATABASE astra_rent OWNER astra;"
```

## Crear personal

El personal (operador, mantenimiento o administrador) no se registra solo: lo crea un administrador.

1. El administrador inicia sesión y entra a `/admin/` → «Usuarios» → «Agregar usuario».
2. Llena los datos: usuario, nombre, apellido, correo y teléfono (7 a 15 números; el correo y el teléfono no pueden ser de otra cuenta).
3. Elige el rol (operador, mantenimiento o administrador) y escribe la contraseña dos veces: al menos 8 caracteres, una mayúscula y un número.
4. Presiona «Guardar».
5. El nuevo usuario entra por el login normal (`/login/`) y llega a la página de su rol: el operador a «Reservas por entregar», mantenimiento a «Mantenimiento» y el administrador al panel.

El rol administrador marca solo `is_staff` e `is_superuser`, que dan acceso al admin; los otros roles no entran al admin. Para bloquear a alguien, el administrador le quita «Activo» (nunca se borra un usuario, [ENT-97](docs/respuestas-del-cliente.md#ent-97)).

**El primer administrador** sale de la consola, porque todavía no hay nadie que pueda entrar al admin:

```powershell
python manage.py createsuperuser
```

Pide usuario, correo, teléfono y contraseña, y el usuario nace con el rol administrador ([ENT-44](docs/respuestas-del-cliente.md#ent-44)). Los roles los crea `migrate`, así que corre `migrate` antes.

## Ver la base de datos

- **pgAdmin 4** (se instala con PostgreSQL): «Servers» → tu servidor → «Databases» → `astra_rent` → «Schemas» → «public» → «Tables». Clic derecho en una tabla → «View/Edit Data» → «All Rows». Para escribir consultas: «Tools» → «Query Tool».
- **psql** (la consola de PostgreSQL), con su ruta completa (ajusta `17` a tu versión):
  ```powershell
  & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U astra -h localhost -d astra_rent
  ```
  Dentro: `\dt` lista las tablas, `\d rentals_rental` muestra las columnas de una tabla y `\q` sale. En pgAdmin también está, ya conectada: clic derecho en `astra_rent` → «PSQL Tool».

Qué guarda cada tabla y 4 consultas útiles (rentas de hoy, deudas pendientes por cliente, historial de un equipo y equipos libres en una fecha): [docs/base-de-datos.md](docs/base-de-datos.md#cómo-ver-la-base).

## Logs

`logs/negocio.log` es el **log de negocio**: una línea por cada acción del sistema, aceptada o rechazada. Sirve para auditar quién hizo qué y cuándo, y para mostrar lo que pasa detrás de cada botón. Cada línea se entiende sin buscar en la base; los rechazos llevan lo que se intentó:

```text
2026-10-29 19:02:11 | INFO    | PAYMENT_APPROVED rental=60 equipment=SIL-00003 "Silla plegable blanca" client=cl01 "Carla Mendoza" period=30/10/2026 18:00-01/11/2026 09:00 amount=8.00 by=cl01
2026-10-29 19:03:40 | WARNING | ACCOUNT_REJECTED username=juan23 email=juan@correo.com reason="Esta contraseña es demasiado común." by=web
```

- Las líneas salen en la terminal del servidor y en el archivo. Para seguir el archivo desde otra terminal: `Get-Content logs\negocio.log -Wait`.
- El archivo crece con cada operación y se conserva entre arranques. `seed_demo` lo vacía al empezar y escribe `DEMO_RESET` como primera línea.
- Para vaciarlo a mano, aunque el servidor esté corriendo: `Clear-Content logs\negocio.log`.
- Qué escribe cada evento: [docs/arquitectura.md](docs/arquitectura.md#eventos-del-log).

## Correo

Por defecto los correos (bienvenida, «Crea tu contraseña», «Olvidé mi contraseña», renta confirmada, reserva modificada por la tienda, renta cancelada y deuda) se imprimen en la terminal. Para mandarlos de verdad con Gmail:

1. En la cuenta de Google, activa la verificación en dos pasos y crea una **contraseña de aplicación** (una clave de 16 letras solo para este sistema) en https://myaccount.google.com/apppasswords.
2. En `.env` pon `EMAIL_HOST_USER=tu.correo@gmail.com` y `EMAIL_HOST_PASSWORD=` con las 16 letras de esa contraseña.
3. Reinicia el servidor.

Los correos salen en un hilo aparte, así la página no espera a Gmail; «Crea tu contraseña» sale en el momento, para que el operador sepa si salió ([D-37](docs/decisiones.md#d-37), [D-40](docs/decisiones.md#d-40)). Si un correo falla, la operación sigue y el log escribe `EMAIL_FAILED`.

## Antes de producción

- [ ] **Nunca** correr `seed_demo` en producción: borra todos los datos (por eso se niega a correr con `DEBUG=False`).
- [ ] En `.env`:
  - `DEBUG=False`;
  - una `SECRET_KEY` nueva (la clave con que Django firma las sesiones y los enlaces de contraseña), generada con:
    ```powershell
    python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
    ```
  - `ALLOWED_HOSTS` con el nombre del servidor (por ejemplo `localhost,127.0.0.1`);
  - la cuenta de Gmail (`EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`);
  - `USE_HTTPS=True` solo si el sitio está detrás de HTTPS.
- [ ] Crear las tablas, el primer administrador y juntar los estilos:
  ```powershell
  python manage.py migrate
  python manage.py createsuperuser
  python manage.py collectstatic --noinput
  ```
  `collectstatic` copia los estilos a `staticfiles/`, donde whitenoise los sirve; vuelve a correrlo cada vez que cambie algo en `static/`.
- [ ] Correr con **waitress**, un servidor web de producción en Python que funciona en Windows (`runserver` es solo para programar):
  ```powershell
  python -m waitress --port=8080 config.wsgi:application
  ```
- [ ] Revisar la configuración: `python manage.py check --deploy` ([docs/pruebas.md](docs/pruebas.md#revisión-de-seguridad-check---deploy)).

Por qué waitress y no `runserver`, qué hacen `collectstatic` y whitenoise, y qué es la `SECRET_KEY`: [docs/arquitectura.md](docs/arquitectura.md#cómo-se-sirve-el-sistema).

## Pruebas

```powershell
python -m pytest -q
```

Usan una base temporal que crea pytest-django; la base de la demo y `logs/negocio.log` no se tocan.

| Tipo | Carpeta | Funciones (casos) |
|---|---|---|
| Unitarias (sin base de datos) | `tests/unit/` | 28 (30) |
| Integración (casos de uso y API con la base, el log y el correo) | `tests/integration/` | 39 (43) |
| Sistema (recorridos por la web) | `tests/system/` | 12 (12) |
| **Total** | | **79 (85)** |

Cobertura: 92 %. Cómo correr un archivo o una sola prueba, qué prueba cubre cada caso de uso y la revisión de seguridad: [docs/pruebas.md](docs/pruebas.md).
