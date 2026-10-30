# Pruebas

Qué contiene: qué tipos de pruebas hay, cómo correrlas (toda la suite, un archivo o una sola prueba), qué prueba cubre cada caso de uso, la revisión de seguridad y la cobertura.
Cuándo leerlo: antes de cambiar código, para saber qué prueba lo cuida, y antes de cada commit. Los IDs (CU, RF, RC) se explican en el [glosario de IDs](README.md#glosario-de-ids).

## Qué se prueba y cómo

Una **prueba** es una función que prepara una situación, ejecuta el código y comprueba el resultado; si el resultado no es el esperado, falla. Se corren con **pytest** (con **pytest-django**, que prepara Django para las pruebas). Hay tres tipos:

| Tipo | Carpeta | Qué prueba | Cómo | Funciones (casos) |
|---|---|---|---|---|
| Unitarias | `tests/unit/` | Las reglas puras de `rules.py`, los validadores, los formularios y el estado calculado de una renta. | Objetos sin guardar (`Rental(...)`, `Equipment(...)`), sin base de datos y con la hora fija (`con_la_hora`). | 28 (30) |
| Integración | `tests/integration/` | Cada caso de uso de `use_cases/` y `accounts/` con la base, la API JSON, el admin, el log y el correo. | Una base PostgreSQL temporal; en cada rechazo se compara `foto_de_la_base()` antes y después, para comprobar que no se guardó nada. | 39 (43) |
| Sistema | `tests/system/` | Recorridos completos por la web: del formulario a lo guardado. | El cliente de pruebas de Django inicia sesión y navega como una persona. | 12 (12) |
| **Total** | | | | **79 (85)** |

Algunas pruebas antiguas verifican lo mismo con otros datos usando `parametrize`, por eso hay más casos que funciones.

Palabras que aparecen en las pruebas:

- **fixture:** un dato de prueba que pytest prepara solo cuando una prueba lo pide como parámetro, por ejemplo `cl01` o `mes01` (en `tests/conftest.py`).
- **`caplog`:** captura las líneas del log para compararlas.
- **`mail.outbox`:** la lista de correos que Django «mandó» durante la prueba, sin salir a internet.
- **`foto_de_la_base()`:** copia de usuarios, rentas, equipos, deudas e historial (en `tests/helpers.py`), para comprobar que un rechazo no cambió nada.

## Cómo correrlas

Desde la carpeta del proyecto, con el entorno virtual activado y PostgreSQL encendido (PowerShell):

```powershell
python -m pytest -q                                                   # toda la suite
python -m pytest -q tests/unit                                        # una carpeta
python -m pytest -q tests/integration/test_deudas.py                  # un archivo
python -m pytest -q tests/unit/test_clasificar_devolucion.py::test_devolucion_a_las_09_01_entra_en_tolerancia_sin_deuda   # una sola prueba
python -m pytest -q -k atraso                                         # las pruebas cuyo nombre dice «atraso»
```

- `-q` muestra un punto por prueba que pasa y una `F` por la que falla; al final, el resumen.
- Usan una base temporal que pytest-django crea y borra; la base de la demo y `logs/negocio.log` no se tocan.
- `config/settings_test.py` ajusta Django para probar: los correos salen en el mismo hilo (`EMAIL_IN_BACKGROUND=False`) para leerlos al instante, el log sube al logger raíz para que `caplog` lo capture y las contraseñas usan un hash rápido.
- GitHub Actions corre la suite completa en cada push ([arquitectura.md](arquitectura.md#pruebas-y-ci)).

Antes de cada commit, además de las pruebas:

```powershell
python manage.py makemigrations --check --dry-run    # no falta ninguna migración
python manage.py check                               # la configuración de Django está bien
ruff check .                                         # el estilo del código
```

## Qué prueba cubre cada caso de uso

| CU | Archivo de prueba | Qué comprueba |
|---|---|---|
| [CU-01](casos-de-uso.md#cu-01) | `integration/test_registro.py`, `system/test_registro_web.py`, `unit/test_contrasena_y_telefono.py` | La cuenta se guarda con la contraseña cifrada y el teléfono en dígitos; un registro con errores muestra todas las causas y no guarda nada; la bienvenida sale en un hilo aparte. |
| [CU-02](casos-de-uso.md#cu-02) | `integration/test_correo_crea_tu_contrasena.py`, `integration/test_contrasena_del_cliente.py`, `system/test_registro_web.py` | La cuenta nace sin contraseña, el correo «Crea tu contraseña» sale con la cuenta ya guardada, y si el correo falla el operador ve qué hacer. |
| [CU-03](casos-de-uso.md#cu-03) | `integration/test_catalogo.py`, `integration/test_catalogo_sin_etiquetas.py`, `system/test_recorridos.py` | Filtros por texto, fechas y estado; páginas de 20; las mismas consultas con 25 y con 1000 equipos ([RC-01](casos-de-uso.md#rc-01)); sin etiquetas de libre u ocupado. |
| [CU-04](casos-de-uso.md#cu-04) | `integration/test_rentar.py`, `integration/test_pagar.py`, `unit/test_validar_periodo.py`, `unit/test_mensaje_ocupado.py`, `unit/test_cruce_de_periodos.py` | Cada regla del periodo con su mensaje; el cruce de fechas; el mensaje «ocupado del … al …»; el pago QR exitoso, fallido y ya pagado. |
| [CU-05](casos-de-uso.md#cu-05) | `integration/test_rentar.py`, `integration/test_pagar.py`, `system/test_recorridos.py` | La renta en tienda nace «Reservada» y pagada en efectivo; el cliente con deuda no renta; la búsqueda por apellido. |
| [CU-06](casos-de-uso.md#cu-06) | `integration/test_modificar.py`, `unit/test_reglas_de_cancelacion.py` | Misma cantidad de días; plazo de 24 h para el cliente y hasta el inicio para el personal; el correo cuando modifica la tienda. |
| [CU-07](casos-de-uso.md#cu-07) | `integration/test_cancelar.py`, `unit/test_reglas_de_cancelacion.py`, `system/test_recorridos.py` | La cancelación libera las fechas; el plazo de 24 h; el cliente no cancela la renta de otro. |
| [CU-08](casos-de-uso.md#cu-08) | `integration/test_entregar_y_devolver.py`, `unit/test_reglas_de_entrega.py`, `unit/test_reserva_vencida.py` | Entregar con el pago hecho o cobrando en efectivo; no entregar sin cobrar, vencida o con el equipo en revisión. |
| [CU-09](casos-de-uso.md#cu-09) | `integration/test_entregar_y_devolver.py`, `integration/test_deudas.py`, `unit/test_clasificar_devolucion.py`, `unit/test_horarios_y_duracion.py` | A tiempo, en tolerancia y con atraso; los días de atraso y su deuda; el equipo pasa a «En revisión» ([cómo se cuentan los días](casos-de-uso.md#cómo-se-cuentan-los-días-y-el-atraso)). |
| [CU-10](casos-de-uso.md#cu-10) | `integration/test_revisar.py`, `integration/test_deudas.py`, `unit/test_reglas_de_revision.py`, `unit/test_precio_y_plazos.py` | El estado nuevo y su historial; la deuda solo con la casilla marcada y con su tope; la cancelación de reservas; la baja es definitiva. |
| [CU-11](casos-de-uso.md#cu-11) | `integration/test_deudas.py` | El pago de la deuda con quién la cobró; una deuda ya pagada se rechaza; el cliente vuelve a rentar. |
| [CU-12](casos-de-uso.md#cu-12) | `integration/test_registrar_equipo.py`, `unit/test_codigo_de_equipo.py` | El formato del código, el código y la serie únicos, el valor mayor que 0. |
| [CU-13](casos-de-uso.md#cu-13) | `integration/test_revisar.py`, `system/test_recorridos.py` | La corrección del admin no cobra, deja el historial y cancela las reservas. |
| [CU-14](casos-de-uso.md#cu-14) | `system/test_recorridos.py` | El admin ve el cambio en el historial. |
| [CU-15](casos-de-uso.md#cu-15) | `integration/test_panel.py`, `integration/test_acceso.py` | Las seis listas del panel con sus totales; solo el administrador entra. |
| [CU-16](casos-de-uso.md#cu-16) | `integration/test_forma_de_pago.py`, `unit/test_etiqueta_de_pago.py`, `system/test_recorridos.py` | «Pagado» o «Pago pendiente» y la forma de pago aparte; el aviso de deuda. |
| [CU-17](casos-de-uso.md#cu-17) | `integration/test_mi_cuenta.py`, `integration/test_contrasena_del_cliente.py`, `integration/test_api_mi_cuenta.py` | Editar los datos con las reglas del registro; cambiar y recuperar la contraseña. |

## Muchos equipos

Para probar el catálogo con muchos equipos ([RC-01](casos-de-uso.md#rc-01)): `python manage.py seed_demo --equipos 1000` deja la demo y completa 1000 equipos con mesas y sillas.

## Revisión de seguridad: `check --deploy`

`check --deploy` revisa la configuración de producción. Con las variables de producción puestas solo para esa línea (PowerShell), sin tocar `.env`:

```powershell
$env:DEBUG="False"; $env:SECRET_KEY="clave-de-prueba-larga-y-aleatoria-de-50-caracteres"; $env:USE_HTTPS="True"; python manage.py check --deploy; Remove-Item Env:DEBUG, Env:SECRET_KEY, Env:USE_HTTPS
```

Resultado:

```text
System check identified no issues (0 silenced).
```

En local, sin esas variables, aparecen los avisos de HTTPS (`security.W004`, `W008`, `W012`, `W016`) y, sin Gmail, `mail.E001`; todos son esperados y están explicados en [arquitectura.md](arquitectura.md#revisión-de-seguridad-python-managepy-check---deploy).

## Cobertura

La **cobertura** dice qué parte del código corrió durante las pruebas: líneas y ramas (cada camino de un `if`). La mide `pytest-cov`:

```powershell
python -m pytest --cov=rentals --cov=accounts --cov-branch -q
```

**Total: 92 %** de líneas y ramas (2221 líneas, 292 ramas), medida sobre el código actual. Por módulo, sin los `__init__.py` vacíos ni las migraciones:

| Módulo | Cobertura | | Módulo | Cobertura |
|---|---|---|---|---|
| `accounts/account.py` | 94 % | | `rentals/rules.py` | 98 % |
| `accounts/admin.py` | 96 % | | `rentals/services/events.py` | 98 % |
| `accounts/api.py` | 85 % | | `rentals/services/formatting.py` | 90 % |
| `accounts/forms.py` | 100 % | | `rentals/services/notifications.py` | 100 % |
| `accounts/models.py` | 100 % | | `rentals/statuses.py` | 100 % |
| `accounts/registration.py` | 95 % | | `rentals/use_cases/catalog.py` | 100 % |
| `accounts/roles.py` | 100 % | | `rentals/use_cases/dashboard.py` | 100 % |
| `accounts/validators.py` | 100 % | | `rentals/use_cases/debts.py` | 94 % |
| `accounts/views.py` | 89 % | | `rentals/use_cases/equipment_status.py` | 98 % |
| `rentals/admin.py` | 84 % | | `rentals/use_cases/handover.py` | 99 % |
| `rentals/api/debts.py` | 69 % | | `rentals/use_cases/inventory.py` | 93 % |
| `rentals/api/handover.py` | 71 % | | `rentals/use_cases/payments.py` | 95 % |
| `rentals/api/inventory.py` | 84 % | | `rentals/use_cases/renting.py` | 97 % |
| `rentals/api/renting.py` | 73 % | | `rentals/use_cases/reservation_changes.py` | 100 % |
| `rentals/api/responses.py` | 88 % | | `rentals/use_cases/review.py` | 95 % |
| `rentals/api/review.py` | 84 % | | `rentals/views/dashboard.py` | 100 % |
| `rentals/api/serializers.py` | 92 % | | `rentals/views/debts.py` | 62 % |
| `rentals/errors.py` | 100 % | | `rentals/views/handover.py` | 86 % |
| `rentals/forms.py` | 94 % | | `rentals/views/home.py` | 78 % |
| `rentals/management/commands/seed_demo.py` | 99 % | | `rentals/views/inventory.py` | 45 % |
| `rentals/models.py` | 98 % | | `rentals/views/renting.py` | 79 % |
| | | | `rentals/views/review.py` | 92 % |

Las reglas y los casos de uso están sobre el 90 %. Lo más bajo son vistas y endpoints que solo leen la petición y llaman a un caso de uso ya probado. No se escribieron pruebas solo para subir el número.

## Qué cubre cada archivo de pruebas

Cada archivo con los casos de uso y los requisitos que comprueba.

### Unitarias

| Archivo | CU | RF / RC |
|---|---|---|
| `test_clasificar_devolucion.py` | [CU-09](casos-de-uso.md#cu-09) | [RF-09](casos-de-uso.md#rf-09) (09:00, 09:01, 12:00, 12:01, el día siguiente y 5 días) |
| `test_codigo_de_equipo.py` | [CU-12](casos-de-uso.md#cu-12) | [RF-16](casos-de-uso.md#rf-16) |
| `test_contexto_del_log.py` | — | [RC-05](casos-de-uso.md#rc-05) |
| `test_contrasena_y_telefono.py` | [CU-01](casos-de-uso.md#cu-01), [CU-02](casos-de-uso.md#cu-02) | [RF-15](casos-de-uso.md#rf-15) |
| `test_cruce_de_periodos.py` | [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05) | [RF-01](casos-de-uso.md#rf-01) |
| `test_estado_de_la_renta.py` | [CU-08](casos-de-uso.md#cu-08), [CU-16](casos-de-uso.md#cu-16) | [RF-07](casos-de-uso.md#rf-07), [RF-08](casos-de-uso.md#rf-08) |
| `test_estado_del_equipo.py` | [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05) | [RF-06](casos-de-uso.md#rf-06), [RF-10](casos-de-uso.md#rf-10) |
| `test_etiqueta_de_pago.py` | [CU-16](casos-de-uso.md#cu-16) | [RF-25](casos-de-uso.md#rf-25) |
| `test_formularios.py` | [CU-04](casos-de-uso.md#cu-04), [CU-09](casos-de-uso.md#cu-09) | [RF-02](casos-de-uso.md#rf-02) |
| `test_horarios_y_duracion.py` | [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05) | [RF-02](casos-de-uso.md#rf-02), [RF-03](casos-de-uso.md#rf-03) (1, 2, 5 y 6 días) |
| `test_mensaje_ocupado.py` | [CU-04](casos-de-uso.md#cu-04) | [RF-01](casos-de-uso.md#rf-01) |
| `test_precio_y_plazos.py` | [CU-04](casos-de-uso.md#cu-04), [CU-06](casos-de-uso.md#cu-06), [CU-10](casos-de-uso.md#cu-10) | [RF-03](casos-de-uso.md#rf-03), [RF-11](casos-de-uso.md#rf-11), [RF-14](casos-de-uso.md#rf-14) |
| `test_reglas_de_cancelacion.py` | [CU-06](casos-de-uso.md#cu-06), [CU-07](casos-de-uso.md#cu-07) | [RF-14](casos-de-uso.md#rf-14) |
| `test_reglas_de_entrega.py` | [CU-08](casos-de-uso.md#cu-08), [CU-09](casos-de-uso.md#cu-09) | [RF-06](casos-de-uso.md#rf-06), [RF-07](casos-de-uso.md#rf-07), [RF-09](casos-de-uso.md#rf-09) |
| `test_reglas_de_revision.py` | [CU-10](casos-de-uso.md#cu-10) | [RF-10](casos-de-uso.md#rf-10) |
| `test_reserva_vencida.py` | [CU-08](casos-de-uso.md#cu-08) | [RF-07](casos-de-uso.md#rf-07) |
| `test_roles.py` | — | [RF-19](casos-de-uso.md#rf-19) |
| `test_validar_periodo.py` | [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05) | [RF-02](casos-de-uso.md#rf-02), [RC-04](casos-de-uso.md#rc-04) |

### Integración

| Archivo | CU | RF / RC |
|---|---|---|
| `test_acceso.py` | [CU-15](casos-de-uso.md#cu-15) | [RF-18](casos-de-uso.md#rf-18), [RF-19](casos-de-uso.md#rf-19), [RC-03](casos-de-uso.md#rc-03) |
| `test_api.py` | [CU-04](casos-de-uso.md#cu-04), [CU-08](casos-de-uso.md#cu-08), [CU-10](casos-de-uso.md#cu-10), [CU-12](casos-de-uso.md#cu-12) | [RF-01](casos-de-uso.md#rf-01), [RF-06](casos-de-uso.md#rf-06), [RF-19](casos-de-uso.md#rf-19), [RC-03](casos-de-uso.md#rc-03) |
| `test_api_mi_cuenta.py` | [CU-02](casos-de-uso.md#cu-02), [CU-17](casos-de-uso.md#cu-17) | [RF-15](casos-de-uso.md#rf-15), [RF-23](casos-de-uso.md#rf-23) |
| `test_cancelar.py` | [CU-07](casos-de-uso.md#cu-07) | [RF-14](casos-de-uso.md#rf-14) |
| `test_catalogo.py` | [CU-03](casos-de-uso.md#cu-03) | [RF-17](casos-de-uso.md#rf-17), [RC-01](casos-de-uso.md#rc-01) |
| `test_catalogo_sin_etiquetas.py` | [CU-03](casos-de-uso.md#cu-03) | [RF-17](casos-de-uso.md#rf-17) |
| `test_contrasena_del_cliente.py` | [CU-02](casos-de-uso.md#cu-02), [CU-17](casos-de-uso.md#cu-17) | [RF-15](casos-de-uso.md#rf-15), [RF-20](casos-de-uso.md#rf-20), [RF-23](casos-de-uso.md#rf-23) |
| `test_correo_crea_tu_contrasena.py` | [CU-02](casos-de-uso.md#cu-02) | [RF-15](casos-de-uso.md#rf-15), [RF-20](casos-de-uso.md#rf-20) |
| `test_cuenta_desactivada.py` | — | [RF-19](casos-de-uso.md#rf-19), [RF-22](casos-de-uso.md#rf-22) |
| `test_deudas.py` | [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05), [CU-09](casos-de-uso.md#cu-09), [CU-10](casos-de-uso.md#cu-10), [CU-11](casos-de-uso.md#cu-11) | [RF-09](casos-de-uso.md#rf-09), [RF-11](casos-de-uso.md#rf-11), [RF-12](casos-de-uso.md#rf-12), [RF-13](casos-de-uso.md#rf-13) |
| `test_entregar_y_devolver.py` | [CU-08](casos-de-uso.md#cu-08), [CU-09](casos-de-uso.md#cu-09) | [RF-06](casos-de-uso.md#rf-06), [RF-10](casos-de-uso.md#rf-10) |
| `test_forma_de_pago.py` | [CU-16](casos-de-uso.md#cu-16) | [RF-25](casos-de-uso.md#rf-25) |
| `test_lo_ultimo_primero.py` | [CU-03](casos-de-uso.md#cu-03), [CU-08](casos-de-uso.md#cu-08) | [RF-17](casos-de-uso.md#rf-17), [RF-24](casos-de-uso.md#rf-24) |
| `test_log_explicito.py` | [CU-01](casos-de-uso.md#cu-01), [CU-05](casos-de-uso.md#cu-05), [CU-06](casos-de-uso.md#cu-06), [CU-09](casos-de-uso.md#cu-09) | [RC-05](casos-de-uso.md#rc-05) |
| `test_log_y_correo.py` | [CU-01](casos-de-uso.md#cu-01), [CU-04](casos-de-uso.md#cu-04), [CU-07](casos-de-uso.md#cu-07), [CU-09](casos-de-uso.md#cu-09) | [RF-20](casos-de-uso.md#rf-20), [RF-22](casos-de-uso.md#rf-22), [RC-05](casos-de-uso.md#rc-05) |
| `test_mi_cuenta.py` | [CU-17](casos-de-uso.md#cu-17) | [RF-23](casos-de-uso.md#rf-23) |
| `test_modificar.py` | [CU-06](casos-de-uso.md#cu-06) | [RF-14](casos-de-uso.md#rf-14), [RF-20](casos-de-uso.md#rf-20) |
| `test_pagar.py` | [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05) | [RF-04](casos-de-uso.md#rf-04), [RF-05](casos-de-uso.md#rf-05) |
| `test_panel.py` | [CU-15](casos-de-uso.md#cu-15) | [RF-12](casos-de-uso.md#rf-12), [RF-18](casos-de-uso.md#rf-18) |
| `test_registrar_equipo.py` | [CU-12](casos-de-uso.md#cu-12) | [RF-16](casos-de-uso.md#rf-16) |
| `test_registro.py` | [CU-01](casos-de-uso.md#cu-01) | [RF-15](casos-de-uso.md#rf-15), [RF-20](casos-de-uso.md#rf-20), [RC-03](casos-de-uso.md#rc-03), [RC-04](casos-de-uso.md#rc-04) |
| `test_rentar.py` | [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05) | [RF-01](casos-de-uso.md#rf-01), [RF-03](casos-de-uso.md#rf-03), [RF-05](casos-de-uso.md#rf-05), [RF-20](casos-de-uso.md#rf-20) |
| `test_revisar.py` | [CU-10](casos-de-uso.md#cu-10), [CU-13](casos-de-uso.md#cu-13) | [RF-10](casos-de-uso.md#rf-10), [RF-11](casos-de-uso.md#rf-11), [RF-20](casos-de-uso.md#rf-20), [RF-21](casos-de-uso.md#rf-21) |
| `test_usuarios.py` | [CU-16](casos-de-uso.md#cu-16) | [RF-15](casos-de-uso.md#rf-15), [RF-19](casos-de-uso.md#rf-19) |

### Sistema

| Archivo | CU | RF / RC |
|---|---|---|
| `test_recorridos.py` | [CU-03](casos-de-uso.md#cu-03), [CU-04](casos-de-uso.md#cu-04), [CU-05](casos-de-uso.md#cu-05), [CU-07](casos-de-uso.md#cu-07) a [CU-10](casos-de-uso.md#cu-10), [CU-13](casos-de-uso.md#cu-13), [CU-16](casos-de-uso.md#cu-16) | [RF-01](casos-de-uso.md#rf-01), [RF-04](casos-de-uso.md#rf-04), [RF-05](casos-de-uso.md#rf-05), [RF-13](casos-de-uso.md#rf-13), [RF-17](casos-de-uso.md#rf-17), [RF-21](casos-de-uso.md#rf-21) |
| `test_registro_web.py` | [CU-01](casos-de-uso.md#cu-01), [CU-02](casos-de-uso.md#cu-02) | [RF-15](casos-de-uso.md#rf-15), [RC-04](casos-de-uso.md#rc-04) |
