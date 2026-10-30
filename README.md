# astra-rent-system

Qué contiene: qué es el sistema de renta de mesas y sillas de SergioCorp, cómo instalarlo en Windows desde cero y usarlo (con React o con las páginas clásicas de Django), los usuarios de la demo, cómo crear personal, ver la base y los logs, cómo correrlo en modo producción y publicarlo en internet, y qué hacer si algo falla.
Cuándo leerlo: primero, para tener el sistema funcionando. La documentación completa está en [docs/README.md](docs/README.md); los IDs (ENT, D, CU, RF, RC) se explican en su [glosario de IDs](docs/README.md#glosario-de-ids).

## Qué es

Un sistema web para que SergioCorp rente mesas, sillas y combos para eventos ([ENT-07](docs/respuestas-del-cliente.md#ent-07), [ENT-96](docs/respuestas-del-cliente.md#ent-96)). Está hecho con **Django** 6.1 (un framework web de Python) y **PostgreSQL** (la base de datos). Hay 4 roles y 17 casos de uso ([docs/casos-de-uso.md](docs/casos-de-uso.md)):

- **Cliente:** crea su cuenta, busca equipos libres, renta y paga con un QR simulado, modifica o cancela sus reservas, ve su deuda y gestiona su cuenta en «Mi cuenta».
- **Operador** (la persona de la tienda): crea cuentas (sin conocer la contraseña del cliente) y rentas en la tienda, entrega (cobrando si falta el pago), recibe devoluciones y cobra deudas.
- **Mantenimiento:** revisa los equipos: disponible, en revisión, en reparación o de baja, y decide si cobra el daño.
- **Administrador:** registra equipos, ve el panel del responsable y gestiona todo desde el admin de Django (`/admin/`).

Se usa desde el **frontend en React** (`http://localhost:5173`, carpeta [`frontend/`](frontend/README.md)), que habla con Django por la API JSON ([docs/api.md](docs/api.md)). Las **páginas clásicas** de Django (`http://localhost:8080`) siguen funcionando y tienen el admin.

Equipo: Uriel ([@peterteranb](https://github.com/peterteranb)), Andrew ([@andrewest-andrew](https://github.com/andrewest-andrew)) y Sofia ([@arduz-in-zugzwang](https://github.com/arduz-in-zugzwang)).

## Antes de empezar: qué instalar

Los comandos de esta guía son para **PowerShell** (búscalo en el menú Inicio). Instala estos programas una sola vez. Después de instalar cada uno, **abre una terminal nueva** (las abiertas no ven los programas recién instalados) y comprueba que responde con su versión.

| Programa | Para qué | Descarga | Al instalar | Comprobar |
|---|---|---|---|---|
| **Python 3.12 o superior** (lo exige Django 6.1) | Corre el sistema | https://www.python.org/downloads/ | Marca la casilla **«Add python.exe to PATH»** en la primera pantalla. | `python --version` |
| **PostgreSQL 15 o superior** | La base de datos | https://www.postgresql.org/download/windows/ | Deja el puerto `5432`. El instalador pide una contraseña para el usuario **`postgres`**: **anótala**, se usa en el paso 5. Trae **pgAdmin**, para ver la base. | `& "C:\Program Files\PostgreSQL\17\bin\psql.exe" --version` (cambia `17` por tu versión) |
| **Git** | Descarga el código | https://git-scm.com/download/win | Las opciones por defecto sirven. | `git --version` |
| **Node.js 20.19 o superior** (la versión LTS) | El frontend de React, la forma principal de usar el sistema | https://nodejs.org/ | Las opciones por defecto sirven. | `node --version` |

`psql` no queda en el PATH: por eso se llama con su ruta completa. Para saber qué versión de PostgreSQL tienes (el número de la carpeta):

```powershell
dir "C:\Program Files\PostgreSQL"
```

## Instalar en Windows

1. Descargar el código y entrar a su carpeta:
   ```powershell
   git clone https://github.com/peterteranb/astra-rent-system.git
   cd astra-rent-system
   ```
2. Crear y activar el **entorno virtual** (una carpeta `.venv` con las librerías de este proyecto, separadas de las de tu computadora):
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```
   Si PowerShell responde que «la ejecución de scripts está deshabilitada», ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, responde `S` y vuelve a activarlo. Sabes que está activo porque la línea empieza con `(.venv)`. Cada vez que abras una terminal nueva para este proyecto, entra a la carpeta y actívalo otra vez.
3. Instalar las librerías:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Crear `.env`, el archivo con la configuración y los secretos de tu máquina (nunca se sube a git), copiando el ejemplo:
   ```powershell
   copy .env.example .env
   notepad .env
   ```
   Qué poner en cada línea:

   | Línea | Qué poner |
   |---|---|
   | `DB_NAME`, `DB_USER`, `DB_HOST`, `DB_PORT` | Déjalas como están (`astra_rent`, `astra`, `localhost`, `5432`). |
   | `DB_PASSWORD` | Una contraseña **nueva** que inventas ahora para el usuario `astra` de la base (no es la de `postgres`). Por ejemplo `Astra2026`. La vas a usar en el paso 5. |
   | `SECRET_KEY` | Para usarlo en tu máquina con `DEBUG=True`, la del ejemplo sirve. Para tener una propia, genera una y pega el resultado después del `=`: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
   | `DEBUG` | `True` para usarlo en tu máquina (ya viene así). En producción va `False`. |
   | `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `USE_HTTPS` | Déjalas como están; solo cambian para [producción](#producción-paso-a-paso). |
   | `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | **Opcional.** Si quedan vacías el sistema funciona igual: los correos se imprimen en la terminal del servidor, con sus enlaces (por ejemplo el de «Crea tu contraseña»), y se copian al navegador. Para mandarlos de verdad: [Correo](#correo). |

   Guarda el archivo y cierra el Bloc de notas.
5. Crear el usuario `astra` y la base `astra_rent`. Cambia `17` por tu versión de PostgreSQL y `TU_CONTRASEÑA` por la que pusiste en `DB_PASSWORD`:
   ```powershell
   & "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -v db_password=TU_CONTRASEÑA -f scripts/create_db.sql
   ```
   Pide `Contraseña para usuario postgres:`: es la que anotaste al instalar PostgreSQL (mientras la escribes no se ve nada; es normal). Debe responder `CREATE ROLE`, `ALTER ROLE` y `CREATE DATABASE`.
6. Crear las tablas y cargar la demo. `migrate` aplica las **migraciones** (los archivos que crean las tablas) y `seed_demo` llena la base con datos de ejemplo:
   ```powershell
   python manage.py migrate
   python manage.py seed_demo
   ```

Después de cada `git pull`, vuelve a ejecutar `python -m pip install -r requirements.txt` y `python manage.py migrate`.

## Usar el sistema

La forma principal de usarlo es el **frontend en React**. Necesita **dos terminales abiertas a la vez**, cada una en la carpeta del proyecto:

1. **Terminal 1, Django en el puerto 8080** (con el entorno activado). Atiende la API y la base:
   ```powershell
   .venv\Scripts\activate
   python manage.py runserver 8080
   ```
2. **Terminal 2, React en el puerto 5173:**
   ```powershell
   cd frontend
   npm install     # solo la primera vez
   npm run dev
   ```
3. Abre **http://localhost:5173** e inicia sesión con un [usuario de la demo](#usuarios-de-demo).

Para detener cada servidor: `Ctrl+C` en su terminal. Django se reinicia solo al guardar un archivo de Python y React se actualiza solo al guardar uno de `frontend/`. Se usa el puerto 8080 porque en Windows el 8000 a veces está reservado ([D-09](docs/decisiones.md#d-09)).

React no tiene reglas de negocio: cada pantalla le pide los datos a la **API JSON** de Django ([docs/api.md](docs/api.md)).
La API llama a los mismos casos de uso (`rentals/use_cases/`) que las páginas de Django, así que una renta se valida igual desde cualquiera de las dos.
Las dos usan la misma base: lo que hagas en una se ve en la otra.

### Páginas clásicas (Django, puerto 8080)

Las páginas hechas con plantillas de Django siguen funcionando en **http://localhost:8080**, con los mismos usuarios y las mismas funciones. Además, son las únicas que tienen:

- el **admin de Django** (`/admin/`), donde el administrador gestiona usuarios, equipos, rentas, deudas e historial (en React es el enlace «Admin» del menú);
- la página del enlace **«Crea tu contraseña»** (`/reset/…/`) de los correos. Si el enlace viene con la dirección de React (`localhost:5173`), Vite se lo pasa a Django y se abre igual.

Más detalles del frontend en [frontend/README.md](frontend/README.md).

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
- **psql** (la consola de PostgreSQL), con su ruta completa (ajusta `17` a tu versión); pide la contraseña de `DB_PASSWORD`:
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

## Producción, paso a paso

`runserver` es solo para programar. En producción el sistema corre con **waitress**, un servidor web de producción en Python que funciona en Windows ([D-21](docs/decisiones.md#d-21)). Haz estos pasos **en este orden**, con el entorno activado:

1. **Con `DEBUG=True` todavía**, carga la demo:
   ```powershell
   python manage.py migrate
   python manage.py seed_demo
   ```
   Va primero porque `seed_demo` se niega a correr con `DEBUG=False`. Si el sistema va a guardar datos reales, **no** corras `seed_demo` (borra todo): crea el primer administrador con `python manage.py createsuperuser`.
2. **Edita `.env`** (`notepad .env`):
   - `DEBUG=False`;
   - una `SECRET_KEY` nueva, la clave con que Django firma las sesiones y los enlaces de contraseña. Genérala y pega el resultado:
     ```powershell
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```
   - `ALLOWED_HOSTS=localhost,127.0.0.1,.trycloudflare.com` (los nombres por los que se puede entrar; el punto inicial acepta cualquier dirección del túnel);
   - `CSRF_TRUSTED_ORIGINS=https://*.trycloudflare.com` (deja enviar formularios desde la dirección `https` del túnel);
   - la cuenta de Gmail (`EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD`, ver [Correo](#correo));
   - `USE_HTTPS=False`. El túnel ya da HTTPS. Con `True`, la página se redirigiría sin fin: el túnel le habla a waitress por HTTP y Django, que no sabe que hay un proxy delante, vuelve a mandar al navegador a `https` en cada visita ([D-10](docs/decisiones.md#d-10)).
3. **Junta los estilos** en `staticfiles/`, de donde whitenoise los sirve con `DEBUG=False`. Repítelo cada vez que cambie algo en `static/`:
   ```powershell
   python manage.py collectstatic --noinput
   ```
4. **Revisa la configuración:**
   ```powershell
   python manage.py check --deploy
   ```
   Con esta configuración quedan 4 avisos de HTTPS, esperados: `security.W004` (sin HSTS), `security.W008` (sin redirección a HTTPS), `security.W012` y `security.W016` (las cookies de sesión y de CSRF no son «solo HTTPS»). Los cuatro dependen de `USE_HTTPS`, que queda en `False` por lo explicado en el paso 2: entre el navegador y Cloudflare la conexión ya va cifrada, y el tramo sin cifrar es el de `cloudflared` a waitress, dentro de la misma computadora. Si falta Gmail aparece también `mail.E001`: el correo usa la consola, que es solo para desarrollo. Detalle de cada aviso: [docs/arquitectura.md](docs/arquitectura.md#revisión-de-seguridad-python-managepy-check---deploy).
5. **Arranca waitress:**
   ```powershell
   python -m waitress --port=8080 config.wsgi:application
   ```
   Abre http://localhost:8080/. Para detenerlo: `Ctrl+C`.

Qué pasa de verdad al correrlo:

- waitress atiende en el **puerto 8080 de esa computadora**. Escucha en todas sus direcciones IPv4 (`0.0.0.0`, lo que trae waitress por defecto), pero Django solo responde a los nombres de `ALLOWED_HOSTS`.
- Atiende **4 peticiones a la vez** (4 hilos, lo que trae por defecto); las demás esperan su turno. `--threads=8`, por ejemplo, lo cambia.
- Que varias personas a la vez no se pisen lo cuidan **PostgreSQL y los bloqueos**: cada operación que escribe (rentar, modificar, entregar, devolver, pagar, cambiar el estado de un equipo) corre en una transacción y bloquea con `select_for_update` la renta o el equipo que toca. Si dos personas rentan el mismo equipo en las mismas fechas al mismo tiempo, la segunda espera a que termine la primera y recibe el rechazo de equipo ocupado ([ENT-21](docs/respuestas-del-cliente.md#ent-21): el equipo es del primero que confirmó).

Por qué waitress y no `runserver`, qué hacen `collectstatic` y whitenoise, y qué es la `SECRET_KEY`: [docs/arquitectura.md](docs/arquitectura.md#cómo-se-sirve-el-sistema).

## Publicarlo en internet (URL pública)

Con un **túnel de Cloudflare** cualquiera puede abrir el sistema desde cualquier red, sin abrir puertos en el router. No hace falta una cuenta de Cloudflare ni cambiar código: `ALLOWED_HOSTS` y `CSRF_TRUSTED_ORIGINS` se leen de `.env` en `config/settings.py`, y ya los pusiste en el paso 2 de [producción](#producción-paso-a-paso).

1. Instala `cloudflared` (una sola vez):
   ```powershell
   winget install --id Cloudflare.cloudflared
   ```
   Abre una terminal nueva y comprueba: `cloudflared --version`.
2. Con waitress corriendo, en **otra terminal**:
   ```powershell
   cloudflared tunnel --url http://localhost:8080
   ```
   Entre sus mensajes imprime una dirección `https://<algo>.trycloudflare.com`. Esa dirección la abre cualquiera, desde cualquier red, mientras la computadora, waitress y `cloudflared` sigan encendidos.
3. **Para el frontend de React**, con `npm run dev` corriendo (ver [Usar el sistema](#usar-el-sistema)), abre otro túnel en otra terminal:
   ```powershell
   cloudflared tunnel --url http://localhost:5173
   ```
   Da otra dirección `https://<otra-cosa>.trycloudflare.com`. React le pide los datos a Django en el 8080 de esa misma computadora, así que Django debe seguir corriendo con el `.env` del paso 2. Por esa dirección, el enlace «Admin» del menú sigue apuntando a `localhost:8080`: solo funciona en la computadora que corre Django.

Límites:

- La dirección **cambia cada vez** que se abre el túnel.
- Depende de que **esa computadora esté encendida** y con los programas corriendo.
- Cloudflare ofrece estos túneles rápidos **para pruebas**, sin garantía de disponibilidad.

Un servidor fijo con dominio propio queda como trabajo futuro.

## Problemas comunes

| Qué pasa | Por qué | Qué hacer |
|---|---|---|
| `psql : El término 'psql' no se reconoce…` | El instalador de PostgreSQL no agrega `psql` al PATH. | Llámalo con su ruta completa: `& "C:\Program Files\PostgreSQL\17\bin\psql.exe" …`, con tu versión en lugar de `17` (la ves con `dir "C:\Program Files\PostgreSQL"`). |
| Al activar el entorno: «la ejecución de scripts está deshabilitada en este sistema» | PowerShell bloquea scripts por defecto. | Ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, responde `S` y vuelve a correr `.venv\Scripts\activate`. |
| `Error: That port is already in use.` o waitress no arranca en el 8080 | Otro programa (o un servidor que quedó abierto en otra terminal) usa el puerto. | Cierra la otra terminal con `Ctrl+C`. Si no la encuentras: `Get-NetTCPConnection -LocalPort 8080` muestra el `OwningProcess`; ciérralo con `Stop-Process -Id <ese número>`. |
| `password authentication failed for user "astra"` | La contraseña de `DB_PASSWORD` en `.env` no es la del usuario `astra` de la base. | Pon en `.env` la misma que usaste en el paso 5, o cámbiala en la base para que coincida: `& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -c "ALTER USER astra WITH PASSWORD 'la-de-tu-env';"` |
| `seed_demo borra los datos de la demo; solo se usa con DEBUG=True` | `.env` tiene `DEBUG=False`. | Pon `DEBUG=True`, corre `seed_demo` y, si vas a producción, vuelve a `DEBUG=False`. |
| La página sale sin estilos o con «Server Error (500)» | Con `DEBUG=False` los estilos salen de `staticfiles/`, y no se corrió `collectstatic` (o se corrió antes de cambiar `static/`). | `python manage.py collectstatic --noinput`, o `DEBUG=True` para usarlo en tu máquina. |
| React muestra «Algo salió mal. Inténtalo de nuevo.» en todo, y la terminal de Vite dice `http proxy error … ECONNREFUSED 127.0.0.1:8080` | Django está apagado: React le pide los datos al puerto 8080. | Arranca Django en otra terminal: `python manage.py runserver 8080` (o waitress). |

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

Cobertura: 92 % de las líneas y ramas del código **se ejecutan** durante las pruebas (pytest-cov). Ese número no dice por sí solo que el comportamiento esté validado: eso lo hacen los `assert` de cada prueba y la tabla que une cada caso de uso y requisito con su prueba ([docs/pruebas.md](docs/pruebas.md#qué-prueba-cubre-cada-caso-de-uso)).

Cómo correr un archivo o una sola prueba y la revisión de seguridad: [docs/pruebas.md](docs/pruebas.md).
