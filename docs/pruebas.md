# Pruebas

Qué se prueba, cómo se corre y la evidencia de la versión final (29/10/2026). Los RF y RC están en [casos-de-uso.md](casos-de-uso.md#2-requisitos-funcionales).

## Qué se prueba y cómo

| Tipo | Carpeta | Qué prueba | Cómo | Funciones (casos) |
|---|---|---|---|---|
| Unitarias | `tests/unit/` | Las reglas puras de `rules.py`, los validadores, los formularios y el estado calculado de una renta. | Objetos sin guardar (`Rental(...)`, `Equipment(...)`), sin base de datos y con la hora fija (`con_la_hora`). | 22 (24) |
| Integración | `tests/integration/` | Cada caso de uso de `use_cases/` y `accounts/` con la base, la API JSON, el admin, el log (`caplog`) y el correo (`mail.outbox`). | PostgreSQL temporal de pytest-django; en cada rechazo se compara `foto_de_la_base()` antes y después. | 36 (40) |
| Sistema | `tests/system/` | Recorridos completos por la web: del formulario a lo guardado. | El cliente de pruebas de Django inicia sesión y navega como una persona. | 12 (12) |
| **Total** | | | | **70 (76)** |

Cada función prueba un caso de uso o una regla; varias revisan en pasos la aceptación, el límite y el rechazo, cada paso con su comentario «Comprueba que…». Las que verifican lo mismo con otros datos usan `parametrize`, por eso hay más casos que funciones.

## Cómo correrlas

Desde la carpeta del proyecto, con el entorno activado y PostgreSQL encendido (PowerShell):

```powershell
python -m pytest -q                                          # toda la suite
python -m pytest -q tests/unit                               # una carpeta
python -m pytest -q tests/integration/test_deudas.py         # un archivo
python -m pytest -q tests/unit/test_etiqueta_de_pago.py -k qr  # los casos cuyo nombre o datos dicen «qr»
```

Usan una base temporal; la base de la demo y `logs/negocio.log` no se tocan. En `config/settings_test.py` los correos salen en el mismo hilo (`EMAIL_IN_BACKGROUND=False`) para leerlos al instante, y el log sube al logger raíz para que `caplog` lo capture. GitHub Actions corre la suite completa en cada push.

## Prueba de carga

`python manage.py stress_test --rentas 50` (solo con `DEBUG=True`) registra 50 clientes con `register_client` y 50 mesas con `register_equipment`, y lanza dos escenarios con 50 hilos que llaman a `create_rental`, el mismo caso de uso que la web. Una barrera (`threading.Barrier`) suelta todos los hilos juntos; cada hilo cierra su conexión y al final el comando borra todo lo que creó. Sale con error si el resultado no es el esperado.

1. **El mismo equipo, el mismo periodo:** debe guardarse 1 renta y rechazarse 49 por «ocupado» (RF-01, RC-02, ENT-21: gana el primer clic). Lo asegura `select_for_update()` sobre la fila del equipo en `create_rental`.
2. **50 equipos distintos:** las 50 rentas se guardan; se mide el tiempo total.

Salida sobre PostgreSQL 18.6 (Python 3.14.6, Windows 11), sin las líneas del log de negocio:

```text
> python manage.py stress_test --rentas 50
1) 50 clientes rentan MES-90000 a la vez en el mismo periodo:
   guardadas 1, rechazadas por «ocupado» 49, otros errores 0, 1.19 s
2) 50 clientes rentan 50 equipos distintos a la vez:
   guardadas 50, rechazadas 0, 1.21 s
Prueba de carga correcta.
```

Para probar el catálogo con muchos equipos: `python manage.py seed_demo --equipos 1000` deja el escenario de la demo y completa 1000 equipos con mesas y sillas.

## Revisión de seguridad: `check --deploy`

Con las variables de producción puestas solo para esa línea (PowerShell), sin tocar `.env`:

```powershell
$env:DEBUG="False"; $env:SECRET_KEY="clave-de-prueba-larga-y-aleatoria-de-50-caracteres"; $env:USE_HTTPS="True"; python manage.py check --deploy; Remove-Item Env:DEBUG, Env:SECRET_KEY, Env:USE_HTTPS
```

Resultado:

```text
System check identified no issues (0 silenced).
```

No queda ningún aviso. En local, sin esas variables, aparecen los avisos de HTTPS (`security.W004`, `W008`, `W012`, `W016`) y, sin Gmail, `mail.E001`; todos son esperados y están explicados en [arquitectura.md](arquitectura.md#revisión-de-seguridad-python-managepy-check---deploy).

## Cobertura

```powershell
python -m pytest --cov=rentals --cov=accounts --cov-branch -q
```

**Total: 88 %** de líneas y ramas (2275 líneas, 298 ramas). Por módulo, sin los `__init__.py` vacíos:

| Módulo | Cobertura | | Módulo | Cobertura |
|---|---|---|---|---|
| `accounts/account.py` | 94 % | | `rentals/models.py` | 98 % |
| `accounts/admin.py` | 96 % | | `rentals/rules.py` | 98 % |
| `accounts/api.py` | 85 % | | `rentals/services/events.py` | 98 % |
| `accounts/forms.py` | 100 % | | `rentals/services/formatting.py` | 90 % |
| `accounts/models.py` | 100 % | | `rentals/services/notifications.py` | 100 % |
| `accounts/registration.py` | 95 % | | `rentals/statuses.py` | 100 % |
| `accounts/roles.py` | 100 % | | `rentals/use_cases/catalog.py` | 100 % |
| `accounts/validators.py` | 100 % | | `rentals/use_cases/dashboard.py` | 100 % |
| `accounts/views.py` | 89 % | | `rentals/use_cases/handover.py` | 99 % |
| `rentals/admin.py` | 84 % | | `rentals/use_cases/history.py` | 98 % |
| `rentals/api/debts.py` | 69 % | | `rentals/use_cases/inventory.py` | 93 % |
| `rentals/api/handover.py` | 71 % | | `rentals/use_cases/payments.py` | 94 % |
| `rentals/api/inventory.py` | 84 % | | `rentals/use_cases/renting.py` | 98 % |
| `rentals/api/renting.py` | 72 % | | `rentals/use_cases/review.py` | 92 % |
| `rentals/api/responses.py` | 88 % | | `rentals/views/dashboard.py` | 100 % |
| `rentals/api/review.py` | 84 % | | `rentals/views/debts.py` | 62 % |
| `rentals/api/serializers.py` | 92 % | | `rentals/views/handover.py` | 86 % |
| `rentals/errors.py` | 100 % | | `rentals/views/home.py` | 78 % |
| `rentals/forms.py` | 94 % | | `rentals/views/inventory.py` | 45 % |
| `rentals/management/commands/seed_demo.py` | 99 % | | `rentals/views/renting.py` | 79 % |
| `rentals/management/commands/stress_test.py` | 0 % | | `rentals/views/review.py` | 92 % |

Las reglas y los casos de uso están sobre el 90 %. Lo más bajo son vistas y endpoints que solo leen la petición y llaman a un caso de uso ya probado, y `stress_test`, que se corre a mano sobre PostgreSQL (arriba). No se escribieron pruebas solo para subir el número.

## Qué cubre cada archivo de pruebas

### Unitarias

| Archivo | CU | RF / RC |
|---|---|---|
| `test_clasificar_devolucion.py` | CU-09 | RF-09 |
| `test_codigo_de_equipo.py` | CU-12 | RF-16 |
| `test_contexto_del_log.py` | — | RC-05 |
| `test_contrasena_y_telefono.py` | CU-01, CU-02 | RF-15 |
| `test_cruce_de_periodos.py` | CU-04, CU-05 | RF-01 |
| `test_estado_de_la_renta.py` | CU-08, CU-16 | RF-07, RF-08 |
| `test_estado_del_equipo.py` | CU-04, CU-05 | RF-06, RF-10 |
| `test_etiqueta_de_pago.py` | CU-16 | RF-25 |
| `test_formularios.py` | CU-04, CU-09 | RF-02 |
| `test_horarios_y_duracion.py` | CU-04, CU-05 | RF-02, RF-03 |
| `test_mensaje_ocupado.py` | CU-04 | RF-01 |
| `test_precio_y_plazos.py` | CU-04, CU-06, CU-10 | RF-03, RF-11, RF-14 |
| `test_reglas_de_cancelacion.py` | CU-06, CU-07 | RF-14 |
| `test_reglas_de_entrega.py` | CU-08, CU-09 | RF-06, RF-07, RF-09 |
| `test_reglas_de_revision.py` | CU-10 | RF-10 |
| `test_reserva_vencida.py` | CU-08 | RF-07 |
| `test_roles.py` | — | RF-19 |
| `test_validar_periodo.py` | CU-04, CU-05 | RF-02, RC-04 |

### Integración

| Archivo | CU | RF / RC |
|---|---|---|
| `test_acceso.py` | CU-15 | RF-18, RF-19, RC-03 |
| `test_api.py` | CU-04, CU-08, CU-10, CU-12 | RF-01, RF-06, RF-19, RC-03 |
| `test_api_mi_cuenta.py` | CU-02, CU-17 | RF-15, RF-23 |
| `test_cancelar.py` | CU-07 | RF-14 |
| `test_catalogo.py` | CU-03 | RF-17, RC-01 |
| `test_catalogo_sin_etiquetas.py` | CU-03 | RF-17 |
| `test_contrasena_del_cliente.py` | CU-02, CU-17 | RF-15, RF-20, RF-23 |
| `test_correo_crea_tu_contrasena.py` | CU-02 | RF-15, RF-20 |
| `test_cuenta_desactivada.py` | — | RF-19, RF-22 |
| `test_deudas.py` | CU-04, CU-05, CU-09, CU-10, CU-11 | RF-09, RF-11, RF-12, RF-13 |
| `test_entregar_y_devolver.py` | CU-08, CU-09 | RF-06, RF-10 |
| `test_forma_de_pago.py` | CU-16 | RF-25 |
| `test_lo_ultimo_primero.py` | CU-08 | RF-24 |
| `test_log_explicito.py` | CU-01, CU-05, CU-06, CU-09 | RC-05 |
| `test_log_y_correo.py` | CU-01, CU-04, CU-07, CU-09 | RF-20, RF-22, RC-05 |
| `test_mi_cuenta.py` | CU-17 | RF-23 |
| `test_modificar.py` | CU-06 | RF-14, RF-20 |
| `test_pagar.py` | CU-04, CU-05 | RF-04, RF-05 |
| `test_panel.py` | CU-15 | RF-12, RF-18 |
| `test_registrar_equipo.py` | CU-12 | RF-16 |
| `test_registro.py` | CU-01 | RF-15, RF-20, RC-03, RC-04 |
| `test_rentar.py` | CU-04, CU-05 | RF-01, RF-03, RF-05, RF-20 |
| `test_revisar.py` | CU-10, CU-13 | RF-10, RF-11, RF-20, RF-21 |
| `test_usuarios.py` | CU-16 | RF-15, RF-19 |

### Sistema

| Archivo | CU | RF / RC |
|---|---|---|
| `test_recorridos.py` | CU-03, CU-04, CU-05, CU-07 a CU-10, CU-13, CU-16 | RF-01, RF-04, RF-05, RF-13, RF-17, RF-21 |
| `test_registro_web.py` | CU-01, CU-02 | RF-15, RC-04 |
