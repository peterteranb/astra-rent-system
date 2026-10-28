# Decisiones y pendientes de la versión final

> Rama `feat/final-version`, 28/10/2026. Lo que se decidió sin una respuesta del cliente, lo que quedó sin hacer y lo que el equipo debe correr.

## 1. Decisiones tomadas sin respuesta del cliente

| # | Tema | Qué se decidió | Por qué |
|---|---|---|---|
| D-01 | Fuente de ENT-66 a ENT-87 | Se marcaron como «Charla en clase 27/10», salvo el pago fallido (ENT-67), que llegó por «WhatsApp 27/10». | El plan no dice de dónde vino cada una; revisar con quien estuvo en la charla. |
| D-02 | `docs/base-de-datos.md` y `.dbml` | Se suben al repositorio en el commit de documentación. Se agregó `value > 0` en `EQUIPO` y el correo único sin distinguir mayúsculas. | Estaban sin seguimiento en `main`; el plan pide que el valor sea mayor que 0 y el correo único «sin distinguir mayúsculas». |
| D-03 | Base local con el usuario nuevo | El permiso para borrar el esquema `public` de `astra_rent` fue denegado en esta sesión. Se probó todo en una base nueva y vacía, `astra_rent_final`, sin tocar la anterior. | El usuario personalizado cambia la tabla de usuarios: la base vieja ya no sirve. Ver la sección 3. |
| D-04 | Correo de la renta en línea | Se envía cuando el cliente presiona un botón del QR (exitoso o fallido). Si cierra la página sin presionar, la reserva queda con el pago pendiente y sin correo. | La reserva ya existe al llegar al QR (ENT-67); así no llegan dos correos por la misma renta. |
| D-05 | Deuda de reparación o baja sin renta devuelta | Si el equipo nunca volvió de una renta, no se crea deuda. | No hay «último cliente» a quien cobrar (ENT-74). |
| D-06 | Reparación y después baja del mismo equipo | Se cobran las dos (20 % y 100 %) al mismo cliente, porque son motivos distintos. Una renta nunca tiene dos deudas del mismo motivo. | Se aplicó la regla tal cual; confirmar con el cliente si debería cobrarse solo la diferencia. |
| D-07 | Mensaje de deuda en la tienda | El cliente ve «Tienes una deuda pendiente…»; el operador ve «El cliente cl02 tiene una deuda pendiente de X Bs. Cóbrala antes de registrar otra renta.». | El mensaje del cliente (ENT-77) habla en segunda persona y confundiría al operador. |
| D-08 | `SECRET_KEY` en `.env.example` | Trae una clave de ejemplo larga para que el camino A funcione con solo copiar el archivo. El README pide cambiarla antes de publicar. | El plan pide que `copy .env.example .env` y `docker compose up` basten; sin clave, `DEBUG=False` no arranca. |
| D-09 | Puerto de Docker | `WEB_PORT` en `.env` (por defecto 8000) cambia el puerto de la máquina. | En Windows el 8000 a veces está reservado (ya pasaba con `runserver`). |
| D-10 | Proxy con HTTPS | `USE_HTTPS=True` no activa `SECURE_PROXY_SSL_HEADER`. | Solo es seguro si el proxy borra esa cabecera; se decide cuando exista el servidor real. |
| D-11 | Correo de la demo | `seed_demo` usa el backend «dummy» mientras corre. | Sus clientes tienen correos inventados; con Gmail configurado rebotarían. |
| D-12 | Plazo de 24 h al modificar | Se cuenta contra el recojo actual de la reserva, no contra el nuevo. | ENT-80 habla del «inicio» de la reserva que se quiere cambiar. |
| D-13 | Filtro «libres entre dos fechas» | Busca libres desde las 18:00 del primer día hasta las 09:00 del último, como una renta. | Así lo que muestra el catálogo coincide con lo que después se puede rentar. |
| D-14 | Rentas activas y vencidas en el panel | «Activas» son las rentadas a tiempo; las vencidas van solo en su lista. | Que una renta no se cuente dos veces. |
| D-15 | Página de inicio del administrador | Llega al panel del responsable (antes, al admin de Django); el admin sigue en el menú. | ENT-87 y la sesión 20 («admin → panel»). |
| D-16 | Usuario bloqueado | Ve «Usuario o contraseña incorrectos.», igual que con una clave mala. | El login de Django no distingue una cuenta inactiva; así tampoco da pistas a quien adivina cuentas. |
| D-17 | Devolución de una renta nunca recogida (ENT-60) | Si llega después de las 12:00 del vencimiento, también crea la deuda por atraso. | La regla de atraso no hace excepciones; el humano revisa el caso (ENT-60). |
| D-18 | Mensajes de contraseña | Los de longitud, contraseña común, solo números y parecida al usuario son los de Django en español. | El plan pide los validadores nativos; los dos propios (mayúscula y número) tienen nuestro texto. |
| D-19 | Migraciones | Se reiniciaron una vez (`0001` en cada app y `accounts.0002_roles` con los roles); después se agregó `rentals.0002` con los mensajes en español de los campos del equipo. | Reiniciar otra vez obligaba a borrar la base de prueba. |

## 2. Lo que quedó sin hacer

| Qué | Estado |
|---|---|
| Comando `stress_test`, prueba de concurrencia con hilos, `seed_demo --equipos N` y la evidencia de `check --deploy` | Los hacen otros integrantes (fuera de esta tarea). El resultado local de `check --deploy` está en la sección 4. |
| Frontend en React y detección de GPU | Los hacen otros integrantes. Las plantillas de Django siguen funcionando y las reglas están en funciones de caso de uso, sin HTTP. |
| Envío real por Gmail | No probado: en esta máquina no hay contraseña de aplicación. Se probó con la consola, con `mail.outbox` y con un fallo simulado del servidor (`EMAIL_FAILED`). |
| Revisión en celular de 360 px, tablet de 600 px, Chrome y Firefox (RC-04, RC-08) | Los estilos son adaptables, pero falta revisarlo a mano en el navegador antes del viernes. |
| Errores 500 en el log de negocio | Django los escribe en su propio logger, no en `logs/negocio.log`. |
| Reiniciar la base local `astra_rent` | Permiso denegado en la sesión; ver la sección 3. |

## 3. Comandos que el equipo debe correr

**Agregar a `.env` (desarrollo).** Ahora `DEBUG` es `False` si no se dice otra cosa y entonces exige `SECRET_KEY`. Agrega estas dos líneas a tu `.env`:

```text
DEBUG=True
SECRET_KEY=cualquier-clave-larga-para-tu-maquina
```

**Instalar las dependencias nuevas** (whitenoise y gunicorn):

```powershell
python -m pip install -r requirements.txt
```

**Reiniciar la base local** (el usuario personalizado cambia las tablas; los datos de la demo se recrean):

```powershell
python manage.py shell -c "from django.db import connection; connection.cursor().execute('DROP SCHEMA public CASCADE; CREATE SCHEMA public;')"
python manage.py migrate
python manage.py seed_demo
```

Si el primer comando falla por permisos, hazlo como `postgres` (ajusta la carpeta a tu versión):

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres -h localhost -c "DROP DATABASE astra_rent;" -c "CREATE DATABASE astra_rent OWNER astra;"
```

En la máquina de Peter quedó además la base de prueba `astra_rent_final`; se puede borrar con `-c "DROP DATABASE astra_rent_final;"`.

**Contraseña de aplicación de Gmail** (para mandar correos de verdad):

1. En la cuenta de Google, activa la verificación en dos pasos.
2. Entra a https://myaccount.google.com/apppasswords, crea una contraseña para «SergioCorp» y copia las 16 letras.
3. En `.env`: `EMAIL_HOST_USER=tu.correo@gmail.com` y `EMAIL_HOST_PASSWORD=` con esas 16 letras. Reinicia el servidor.

**Instalar Docker** (para el camino A del README):

```powershell
winget install Docker.DockerDesktop
```

Después abre Docker Desktop una vez y espera a que diga que está corriendo.

## 4. `check --deploy`

Con `DEBUG=False`, una `SECRET_KEY` propia, `USE_HTTPS=True` y Gmail configurado: **sin advertencias** («System check identified no issues»).

En local, sin HTTPS y sin Gmail, quedan estas, todas esperadas:

| Código | Qué dice | Por qué queda en local |
|---|---|---|
| `mail.E001` | El correo usa el backend de consola, que es solo para desarrollo. | Sin `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` los correos se imprimen. Desaparece al configurar Gmail. |
| `security.W004` | Falta `SECURE_HSTS_SECONDS`. | HSTS solo se activa con `USE_HTTPS=True`; en `http://localhost` rompería el sitio. |
| `security.W008` | `SECURE_SSL_REDIRECT` no está en `True`. | En local no hay HTTPS al que redirigir. |
| `security.W012` | `SESSION_COOKIE_SECURE` no está en `True`. | Con HTTP el navegador no enviaría la cookie y no se podría iniciar sesión. |
| `security.W016` | `CSRF_COOKIE_SECURE` no está en `True`. | Igual que la anterior, para el token CSRF. |

## 5. Docker

- `docker compose build`: **funciona** (28/10/2026, Docker 29.3.1, Compose v5.1.1). Docker Desktop estaba apagado y se inició para la prueba.
- Se probó el camino A completo en una copia aparte del repositorio, con el `.env.example` tal cual y el puerto 8765: `migrate`, `collectstatic`, gunicorn, `seed_demo`, inicio de sesión de `ad01`, el panel del responsable y `logs/negocio.log` en la máquina, con la hora de La Paz. Después se borró con `docker compose down -v`.
- El camino B se probó con `runserver` sobre una base nueva, con `DEBUG=True` y con `DEBUG=False` más `collectstatic`.
