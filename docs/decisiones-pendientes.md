# Decisiones y pendientes de la versión final

> Rama `feat/final-version`, 28/10/2026. Lo que se decidió sin una respuesta del cliente, lo que quedó sin hacer y lo que el equipo debe correr.

## 1. Decisiones tomadas sin respuesta del cliente

| # | Tema | Qué se decidió | Por qué |
|---|---|---|---|
| D-01 | Fuente de ENT-66 a ENT-87 | Se marcaron como «Charla en clase 27/10», salvo el pago fallido (ENT-67), que llegó por «WhatsApp 27/10». | El plan no dice de dónde vino cada una; revisar con quien estuvo en la charla. |
| D-02 | `docs/base-de-datos.md` y `.dbml` | Se suben al repositorio en el commit de documentación. | Estaban sin seguimiento en `main` y el resto de los documentos los enlaza. |
| D-03 | Base local con el usuario nuevo | El permiso para borrar el esquema `public` de `astra_rent` fue denegado en esta sesión. Se probó todo en una base nueva y vacía, `astra_rent_final`, sin tocar la anterior. | El usuario personalizado cambia la tabla de usuarios: la base vieja ya no sirve. Ver el comando en la sección 3. |
