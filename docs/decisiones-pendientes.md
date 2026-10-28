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
