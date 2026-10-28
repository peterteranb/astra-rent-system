# Decisiones y pendientes de la versión final

> Rama `feat/final-version`, 28/10/2026. Lo que se decidió sin una respuesta del cliente, lo que quedó sin hacer y lo que el equipo debe correr.

## 1. Decisiones tomadas sin respuesta del cliente

| # | Tema | Qué se decidió | Por qué |
|---|---|---|---|
| D-01 | Fuente de ENT-66 a ENT-87 | Se marcaron como «Charla en clase 27/10», salvo el pago fallido (ENT-67), que llegó por «WhatsApp 27/10». | El plan no dice de dónde vino cada una; revisar con quien estuvo en la charla. |
| D-02 | `docs/base-de-datos.md` y `.dbml` | Se suben al repositorio en el commit de documentación. | Estaban sin seguimiento en `main` y el resto de los documentos los enlaza. |
| D-03 | Base local con el usuario nuevo | El permiso para borrar el esquema `public` de `astra_rent` fue denegado en esta sesión. Se probó todo en una base nueva y vacía, `astra_rent_final`, sin tocar la anterior. | El usuario personalizado cambia la tabla de usuarios: la base vieja ya no sirve. Ver el comando en la sección 3. |
| D-04 | Correo de la renta en línea | Se envía cuando el cliente presiona un botón del QR (exitoso o fallido). Si cierra la página sin presionar, la reserva queda con el pago pendiente y sin correo. | La reserva ya existe al llegar al QR (ENT-67); así no llegan dos correos por la misma renta. |
| D-05 | Deuda de reparación o baja sin renta devuelta | Si el equipo nunca volvió de una renta, no se crea deuda. | No hay «último cliente» a quien cobrar (ENT-74). |
| D-06 | Reparación y después baja del mismo equipo | Se cobran las dos (20 % y 100 %) al mismo cliente, porque son motivos distintos. Una renta nunca tiene dos deudas del mismo motivo. | Se aplicó la regla tal cual; confirmar con el cliente si debería cobrarse solo la diferencia. |
| D-07 | Mensaje de deuda en la tienda | El cliente ve «Tienes una deuda pendiente…»; el operador ve «El cliente cl02 tiene una deuda pendiente de X Bs. Cóbrala antes de registrar otra renta.». | El mensaje del cliente (ENT-77) habla en segunda persona y confundiría al operador. |
| D-08 | `SECRET_KEY` en `.env.example` | Trae una clave de ejemplo larga para que el camino A funcione con solo copiar el archivo. El README pide cambiarla antes de publicar. | El plan pide que `copy .env.example .env` y `docker compose up` basten; sin clave, `DEBUG=False` no arranca. |
| D-09 | Puerto de Docker | `WEB_PORT` en `.env` (por defecto 8000) cambia el puerto de la máquina. | En Windows el 8000 a veces está reservado (ya pasaba con `runserver`). |
| D-10 | Proxy con HTTPS | `USE_HTTPS=True` no activa `SECURE_PROXY_SSL_HEADER`. | Solo es seguro si el proxy borra esa cabecera; se decide cuando exista el servidor real. |
| D-11 | Correo de la demo | `seed_demo` usa el backend «dummy» mientras corre. | Sus clientes tienen correos inventados; con Gmail configurado rebotarían. |

## 2. `check --deploy`

Con `DEBUG=False`, una `SECRET_KEY` propia, `USE_HTTPS=True` y Gmail configurado: **sin advertencias** («System check identified no issues»).

En local, sin HTTPS y sin Gmail, quedan estas, todas esperadas:

| Código | Qué dice | Por qué queda en local |
|---|---|---|
| `mail.E001` | El correo usa el backend de consola, que es solo para desarrollo. | Sin `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` los correos se imprimen. Desaparece al configurar Gmail. |
| `security.W004` | Falta `SECURE_HSTS_SECONDS`. | HSTS solo se activa con `USE_HTTPS=True`; en `http://localhost` rompería el sitio. |
| `security.W008` | `SECURE_SSL_REDIRECT` no está en `True`. | En local no hay HTTPS al que redirigir. |
| `security.W012` | `SESSION_COOKIE_SECURE` no está en `True`. | Con HTTP el navegador no enviaría la cookie y no se podría iniciar sesión. |
| `security.W016` | `CSRF_COOKIE_SECURE` no está en `True`. | Igual que la anterior, para el token CSRF. |

## 3. Docker

- `docker compose build`: **funciona** (28/10/2026, Docker 29.3.1, Compose v5.1.1).
- Se probó el camino A completo en una copia aparte del repositorio, con el `.env.example` tal cual y el puerto 8765: `migrate`, `collectstatic`, gunicorn, `seed_demo`, inicio de sesión de `ad01`, el panel del responsable y `logs/negocio.log` en la máquina, con la hora de La Paz. Después se borró con `docker compose down -v`.
- El camino B se probó con `runserver` sobre una base nueva, con `DEBUG=True` y con `DEBUG=False` más `collectstatic`.
