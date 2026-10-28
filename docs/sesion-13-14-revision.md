# Sesiones 13–14 — Revisión del estado del proyecto

> **Documento histórico** de una iteración anterior: se conserva como evidencia y no se actualiza. Lo vigente está en el [índice de la documentación](README.md).

## 1. Proyecto y versión revisada

- Proyecto: astra-rent-system — SergioCorp (renta de mesas y sillas).
- Integrantes: Sofia Arduz Rengel, Andrés Laura Vargas, Peter Uriel Terán Bedregal.
- Fecha real: 14/10/2026.
- Operación: rentar un equipo en línea (PRE-CU-01) — `rentals/services.py -> create_rental()`.
- Versión: código en `main` (`3b18466`, PR #28); CI en la rama `docs/sesion-12-arquitectura.md-plan` (commit `7d9d206`, [Actions 38483627007](https://github.com/peterteranb/astra-rent-system/actions/runs/38483627007), 4 aprobadas, [PR #40](https://github.com/peterteranb/astra-rent-system/pull/40)).
- Evidencias: [Sesión 6](sesion-06-requisitos.md) · [Sesión 7](sesion-07-modelos.md) · [Sesiones 8–9](sesion-08-09-plan.md) · [Sesión 12](sesion-12-arquitectura.md) · [README](../README.md) · [issue #30](https://github.com/peterteranb/astra-rent-system/issues/30).

## 2. Diagnóstico

| Punto # | Estado | Evidencia concreta | Hallazgo: qué está bien o qué falta |
|---|---|---|---|
| 1 | P | `sesion-06-requisitos.md` §3; `rules.py`, `services.py` | Hay IDs y criterios, y el código aplica PRE-RF-01, PRE-RC-01 y parte de PRE-RF-04; faltan PRE-RF-02/03, y ENT-18/19 aparecen como confirmados (S6) y como «supuesto» (README, S12). |
| 2 | P | `sesion-07-modelos.md` §2 y §4; `views.rent_equipment` | Actor, éxito, E1/E2 y datos conservados coinciden con el código; el modelo aún dice que no se revisan horarios ni duración. |
| 3 | R | `sesion-08-09-plan.md` §3 y §7; issue #30 | El plan sigue en «no iniciada» aunque el flujo está en `main`, y falta la prueba de que la base rechaza rentas cruzadas (tarea B / T-02). |
| 4 | P | `sesion-12-arquitectura.md` §2 y §4; imports de `rules.py` y `views.py` | Interacción, reglas y datos se localizan, pero el diagrama omite que `views.py` y `forms.py` usan `rules`, y `rules.py` sí importa `EquipmentStatus` de `models.py`. |
| 5 | C | `sesion-12-arquitectura.md` §4 y §5 | Django (modelos–plantillas–vistas) más una capa de servicio, en una sola máquina; la decisión y su costo están explicados. |
| 6 | P | `models.py` (`Equipment`, `Rental`); `0001_initial.py` | Entidades, IDs, cinco estados y relaciones están en PostgreSQL; la base solo impide fin ≤ inicio, no el cruce de periodos. |
| 7 | P | `models.py`; `errors.py`; `views.py` | Las clases y la herencia de errores tienen sentido (E1 se captura antes que la base); falta el diagrama de clases. |
| 8 | P | `services.create_rental`; `sesion-12-arquitectura.md` §3 | El rechazo llega antes de guardar; falta un diagrama de secuencia (la sesión 12 cita uno que en la sesión 7 es un diagrama de flujo). |
| 9 | P | `tests/` (81 pasan, 5 omitidas); `tests/sesion12/`; Actions 38483627007 | Las pruebas comprueban datos y el CI verde identifica un commit; pero el CI solo corre 4 de 86 pruebas. |
| 10 | P | `README.md`; `sesion-12-arquitectura.md` §5 y §8 | El README permite ejecutar el proyecto; cuenta 82 pruebas y no menciona el CI. |

## 3. Caso crítico

- **Requisito:** PRE-RF-01 (el primero en confirmar se queda el equipo) y PRE-RC-01 (mensaje con la causa).
- **Recorrido:** `sesion-07-modelos.md` E1 → `views.rent_equipment` → `create_rental` → `check_equipment_is_free` → `rules.periods_overlap`. Tests: `test_si_c01_ya_tiene_eq01_la_renta_de_c02_en_esas_fechas_se_rechaza`, `test_c02_es_rechazado_y_vuelve_al_catalogo_con_el_mensaje_e1`, `test_rechazo_y_repeticion_no_crean_otra_renta_ni_cambian_nada`.
- **Resultado esperado:** C-02 es rechazado con equipo y fechas; queda solo la renta de C-01, sin cambios.
- **Correspondencia:** correcta por la web y el servicio. El caso P01 (devolución repetida) no se puede revisar porque la devolución aún no existe.
- **Discrepancia real:** el plan prometía que la base rechazara el cruce, pero hoy solo lo impide el servicio. `rentals/admin.py` permite crear rentas sin pasar por `create_rental`, así que `/admin` podría guardar dos rentas cruzadas (según el código; aún no lo probamos).
- **Fortalezas:**
  1. `create_rental` valida antes de la transacción, bloquea el equipo y guarda al final; las pruebas de la sesión 12 comprueban que tras un rechazo la base queda idéntica.
  2. `rules.py` son funciones puras, probadas sin base de datos en `tests/unit/`.

## 4. Correcciones prioritarias

| Prioridad | Problema | Cambio posterior | Cómo comprobaremos la corrección | Responsable / tarea del plan |
|---|---|---|---|---|
| Alta | Solo `create_rental` impide rentas cruzadas; la base y `/admin` no. | Restricción de exclusión en PostgreSQL (`btree_gist`) por migración. | Una prueba que guarda una renta cruzada y espera `IntegrityError`; probar lo mismo en `/admin`. | Peter; T-02, [issue #30](https://github.com/peterteranb/astra-rent-system/issues/30) |
| Media | Los documentos no coinciden con el código (plan, sesión 7, sesión 12). | Actualizar estado y alcance, y corregir los puntos 1, 2, 4 y 8. | Cada afirmación cita archivo, función o test; PR revisado. | Andrés (sesiones 7 y 12) y Sofia (sesiones 8–9) |
| Media | El CI solo corre 4 de 86 pruebas y el README cuenta 82. | El workflow ejecuta `python -m pytest -q`; se actualiza el README. | Actions verde con `81 passed, 5 skipped`; README con 86. | Peter (CI) y Sofia (README) |

**Estado del incremento: necesita correcciones, sin estar bloqueado.** El flujo de renta funciona y está probado, pero el cruce de periodos solo lo impide el código y varios documentos están desactualizados; conviene corregirlo antes de añadir nuevas formas de escribir rentas (renta en persona, roles).