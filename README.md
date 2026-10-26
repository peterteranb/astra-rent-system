# astra-rent-system

Sistema web de renta de mesas y sillas para eventos de SergioCorp (cliente simulado), hecho con Django 6.1 y PostgreSQL.
El cliente renta en línea; el operador entrega, recibe y renta en la tienda; mantenimiento revisa lo que vuelve; el admin gestiona todo desde `/admin`.

## Requisitos

- Python 3.12 o superior (lo exige Django 6.1)
- PostgreSQL 15 o superior en el puerto 5432 (se probó con la 18)
- Git

## Puesta en marcha

1. Clonar el repositorio:
   ```powershell
   git clone https://github.com/peterteranb/astra-rent-system.git
   cd astra-rent-system
   ```
2. Crear y activar el entorno virtual: `python -m venv .venv` y luego `.venv\Scripts\activate`.
   Si PowerShell no deja activarlo, ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
3. Instalar dependencias:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Copiar `.env.example` a `.env` y poner tu contraseña en `DB_PASSWORD`. El archivo `.env` no se sube a git.
5. Crear el usuario `astra` y la base `astra_rent` con la misma contraseña del paso 4 (ajusta la carpeta de tu versión):
   ```powershell
   & "C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -h localhost -v db_password=TU_CONTRASEÑA -f scripts/create_db.sql
   ```
6. Crear las tablas y cargar la demo:
   ```powershell
   python manage.py migrate
   python manage.py seed_demo
   ```
7. Arrancar el servidor (el puerto 8000 puede estar reservado en Windows):
   ```powershell
   python manage.py runserver 8080
   ```
8. Abrir http://127.0.0.1:8080/

Después de cada `git pull`, vuelve a ejecutar `python manage.py migrate`.

## Usuarios de la demo

Todos usan la clave `demo1234`.

| Usuario | Quién es | Qué ve |
|---|---|---|
| `cl01` | Carla Mendoza, cliente | Catálogo con los periodos ocupados y «Mis rentas» |
| `cl02` | Diego Rojas, cliente | Lo mismo que `cl01`, con sus propias rentas |
| `op01` | Olga Pérez, operadora | Renta en tienda, Reservas por entregar y Devoluciones |
| `mt01` | Mario Torres, mantenimiento | Los equipos en revisión o en reparación |
| `ad01` | Ana Díaz, administradora (superusuario) | El admin de Django y todas las páginas del personal |

`seed_demo` deja un equipo listo para cada caso de uso (EQ-01 a EQ-08) y al terminar imprime para qué sirve cada uno.

**Volver a cero:** `python manage.py seed_demo`. Es solo para la demo: borra todas las rentas y el historial y crea el mismo escenario con fechas relativas a hoy.

## Pruebas

```powershell
python -m pytest -q
```

Usan una base temporal que crea pytest-django; la base de la demo no se toca. `config/settings_test.py` usa un hash de contraseñas rápido solo para las pruebas.

| Tipo | Carpeta | Pruebas | Tiempo |
|---|---|---|---|
| Unitarias (sin base de datos) | `tests/unit/` | 63 (76 %) | 0,2 s |
| Integración (casos de uso con la base) | `tests/integration/` | 16 (19 %) | 1,9 s |
| Sistema (recorridos por la web) | `tests/system/` | 4 (5 %) | 1,9 s |
| **Total** | | **83** | **2,1 s** |

Los tiempos de integración y sistema por separado incluyen crear la base de pruebas (unos 1,5 s); juntas, todas las pruebas tardan 2,1 s.

## Estructura

| Carpeta | Qué tiene |
|---|---|
| `config/` | Configuración de Django, URLs raíz y la configuración de las pruebas |
| `accounts/` | Login y cierre de sesión |
| `rentals/` | Modelos, reglas puras (`rules.py`), casos de uso (`renting.py`, `handover.py`, `review.py`, `history.py`), vistas y admin |
| `rentals/management/commands/` | `seed_demo`, el escenario de la demo |
| `templates/` | Páginas HTML; `includes/` tiene las partes que se repiten |
| `static/` | Estilos del sitio y del admin, y el logo |
| `tests/` | Pruebas unitarias, de integración y de sistema |
| `scripts/` | SQL que crea el usuario y la base de PostgreSQL |
| `docs/` | Casos de uso, arquitectura, respuestas del cliente y entregas de cada sesión: ver [docs/README.md](docs/README.md) |

## Equipo

- Uriel ([@peterteranb](https://github.com/peterteranb))
- Andrew ([@andrewest-andrew](https://github.com/andrewest-andrew))
- Sofia ([@arduz-in-zugzwang](https://github.com/arduz-in-zugzwang))
