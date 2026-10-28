# Casos de uso · versión final

> Versión del 28/10/2026, para la entrega del 30/10. Reemplaza a la versión del MVP (19/10).
> Las respuestas del cliente (ENT-xx) están en [respuestas-del-cliente.md](respuestas-del-cliente.md); ahí cada ENT dice qué parte dijo el cliente y qué parte es una decisión del equipo. Las decisiones del equipo (D-xx), en [decisiones.md](decisiones.md). Las necesidades del encargo (PRE-xx), en [presentacion12-10.md](presentacion12-10.md). La base de datos está en [base-de-datos.md](base-de-datos.md).

## 1. Mapa

```mermaid
flowchart LR
    C([Cliente])
    O([Operador])
    M([Mantenimiento])
    A([Administrador])
    P([Pasarela de pago simulada])

    C --- CU01[CU-01 Crear cuenta]
    C --- CU03[CU-03 Consultar equipos]
    C --- CU04[CU-04 Rentar en línea y pagar con QR]
    C --- CU06[CU-06 Modificar una reserva]
    C --- CU07[CU-07 Cancelar una reserva]
    C --- CU16[CU-16 Mis rentas y mi deuda]
    P --- CU04
    O --- CU02[CU-02 Crear cuenta en tienda]
    O --- CU03
    O --- CU05[CU-05 Rentar en tienda]
    O --- CU06
    O --- CU07
    O --- CU08[CU-08 Entregar el equipo]
    O --- CU09[CU-09 Registrar la devolución]
    O --- CU11[CU-11 Registrar el pago de una deuda]
    M --- CU10[CU-10 Revisar el equipo]
    A --- CU07
    A --- CU12[CU-12 Registrar un equipo]
    A --- CU13[CU-13 Corregir el estado]
    A --- CU14[CU-14 Consultar el historial]
    A --- CU15[CU-15 Panel del responsable]
```

| CU | Nombre | Actor | Historia | Requisitos |
|---|---|---|---|---|
| [CU-01](#cu-01--crear-cuenta) | Crear cuenta | Cliente | HU-01 | RF-15 |
| [CU-02](#cu-02--crear-cuenta-en-tienda) | Crear cuenta en tienda | Operador | HU-02 | RF-15 |
| [CU-03](#cu-03--consultar-equipos-y-disponibilidad) | Consultar equipos y disponibilidad (filtros y paginación) | Cliente, Operador | HU-03 | RF-17 |
| [CU-04](#cu-04--rentar-en-línea-y-pagar-con-qr-simulado) | Rentar en línea y pagar con QR simulado | Cliente, Pasarela | HU-04 | RF-01 a RF-04, RF-13 |
| [CU-05](#cu-05--rentar-en-tienda) | Rentar en tienda (efectivo) | Operador | HU-05 | RF-01 a RF-03, RF-05, RF-13 |
| [CU-06](#cu-06--modificar-una-reserva) | Modificar una reserva | Cliente, Operador | HU-06 | RF-14 |
| [CU-07](#cu-07--cancelar-una-reserva) | Cancelar una reserva | Cliente, Operador, Administrador | HU-07 | RF-14 |
| [CU-08](#cu-08--entregar-el-equipo) | Entregar el equipo (cobra si el pago está pendiente) | Operador | HU-08 | RF-06, RF-07 |
| [CU-09](#cu-09--registrar-la-devolución) | Registrar la devolución (deuda por atraso) | Operador | HU-09 | RF-09, RF-12 |
| [CU-10](#cu-10--revisar-el-equipo) | Revisar el equipo (deuda por daño; cancela las reservas futuras si es baja) | Mantenimiento | HU-10 | RF-10, RF-11 |
| [CU-11](#cu-11--registrar-el-pago-de-una-deuda) | Registrar el pago de una deuda | Operador | HU-11 | RF-12 |
| [CU-12](#cu-12--registrar-un-equipo) | Registrar un equipo | Administrador | HU-12 | RF-16 |
| [CU-13](#cu-13--corregir-el-estado-de-un-equipo) | Corregir el estado de un equipo | Administrador | HU-13 | RF-21 |
| [CU-14](#cu-14--consultar-el-historial) | Consultar el historial (admin de Django) | Administrador | HU-14 | RF-10 |
| [CU-15](#cu-15--ver-el-panel-del-responsable) | Ver el panel del responsable | Administrador | HU-15 | RF-18 |
| [CU-16](#cu-16--consultar-mis-rentas-y-mi-deuda) | Consultar mis rentas y mi deuda | Cliente | HU-16 | RF-12, RF-19 |

## 2. Requisitos funcionales

Las funciones de «Dónde se cumple» están en `rentals/use_cases/` (por ejemplo `renting.create_rental` es `rentals/use_cases/renting.py`), salvo que se diga otra carpeta; las reglas puras, en `rentals/rules.py`. Las pruebas de «Cómo se verifica» están en `tests/` y se corren con `python -m pytest -q`.

| ID | Requisito | Origen | Dónde se cumple | Cómo se verifica |
|---|---|---|---|---|
| RF-01 | Un equipo no tiene dos rentas con fechas que se crucen. Si chocan, se dice cuándo está ocupado y hasta cuándo está libre. Gana el primero que confirma. | ENT-21, ENT-36, ENT-45, PRE-04 | `renting.create_rental`, `rules.periods_overlap` | `unit/test_cruce_de_periodos.py`, `unit/test_mensaje_ocupado.py`, `integration/test_rentar.py`, `system/test_recorridos.py` (rechazo por fechas ocupadas) |
| RF-02 | Recojo desde las 18:00, devolución hasta las 09:00, máximo 5 días. | ENT-18, ENT-19, ENT-52, ENT-72 | `renting.check_period`, `rules.py` | `unit/test_horarios_y_duracion.py`, `unit/test_validar_periodo.py` |
| RF-03 | El precio diario es el 5 % del valor del equipo, se fija al crear la renta y no cambia. Total = días × precio diario; los días son los que hay entre la fecha de recojo y la de devolución. | ENT-71, ENT-72 | `rules.daily_price_for`, `rules.rental_days`, `Rental.total_price` | `unit/test_precio_y_plazos.py`, `unit/test_horarios_y_duracion.py`, `integration/test_rentar.py` (el precio no cambia con el valor) |
| RF-04 | La renta en línea se paga con un QR simulado. Si el pago falla, la reserva queda hecha con el pago pendiente. | ENT-66, ENT-67 | `payments.pay_with_qr` | `integration/test_pagar.py`, `system/test_recorridos.py` (pago fallido) |
| RF-05 | La renta en tienda se paga en efectivo al registrarla y nace «Reservada»; si el cliente se la lleva al momento, el operador registra el recojo (CU-08). | ENT-70, ENT-91, PRE-03 | `renting.create_rental` | `integration/test_pagar.py`, `integration/test_rentar.py`, `system/test_recorridos.py` (renta en tienda) |
| RF-06 | No se entrega un equipo sin pagar: el operador cobra en efectivo o cancela la reserva. | ENT-68 | `handover.register_pickup` | `integration/test_entregar_y_devolver.py` |
| RF-07 | Una reserva no recogida hasta la medianoche de su día de inicio pasa sola a «No recogida» y libera el equipo. | ENT-69 | `rules.is_pickup_expired`, `Rental.status_at` | `unit/test_reserva_vencida.py`, `unit/test_estado_de_la_renta.py`, `unit/test_reglas_de_entrega.py` |
| RF-08 | El estado de la renta se calcula, no se guarda: Cancelada > Devuelta > Rentada > No recogida > Reservada. | ENT-57, ENT-61 | `Rental.status_at` | `unit/test_estado_de_la_renta.py` |
| RF-09 | La devolución hasta las 09:00 del día de vencimiento es a tiempo; hasta las 12:00, tolerancia sin cobro; desde las 12:01, deuda por atraso = días de atraso × precio diario. | ENT-73, PRE-05 | `rules.classify_return`, `rules.late_days`, `handover.register_return` | `unit/test_clasificar_devolucion.py`, `integration/test_deudas.py` |
| RF-10 | El equipo devuelto pasa a «En revisión»; mantenimiento decide disponible, en reparación o baja (definitiva). Cada cambio queda en el historial con quién, cuándo y por qué. | ENT-03, ENT-34, ENT-49, PRE-06, PRE-07 | `history.change_status`, `review.review_equipment` | `unit/test_reglas_de_revision.py`, `integration/test_entregar_y_devolver.py`, `integration/test_revisar.py` |
| RF-11 | Reparación crea una deuda del 20 % del valor y baja una del 100 %, para el cliente de la última renta devuelta. Las deudas por daño de una renta nunca suman más que el valor: una baja después de una reparación cobra el 80 % (D-06). La baja cancela las reservas futuras del equipo y avisa por correo. | ENT-74 | `review.review_equipment`, `rules.damage_charge` | `unit/test_precio_y_plazos.py`, `integration/test_deudas.py` |
| RF-12 | Cada deuda es de una renta y un motivo, y se paga una por una; el operador registra el pago. La deuda total se calcula y se muestra. | ENT-76, ENT-78 | `payments.pay_debt`, `payments.debt_total_of` | `integration/test_deudas.py`, `integration/test_panel.py` |
| RF-13 | Un cliente con deuda pendiente no puede crear rentas, ni en línea ni en tienda; sí puede devolver. | ENT-77 | `renting.check_client_has_no_debt` | `integration/test_deudas.py`, `system/test_recorridos.py` (cliente con deuda) |
| RF-14 | Solo una renta «Reservada» se cancela o modifica. El cliente, hasta 24 h antes del inicio; el operador o el admin, en cualquier momento antes del recojo. Modificar es cambiar las fechas con la misma cantidad de días. | ENT-80, ENT-81, ENT-82 | `renting.cancel_rental`, `renting.modify_rental` | `unit/test_reglas_de_cancelacion.py`, `unit/test_precio_y_plazos.py` (plazo de 24 h), `integration/test_cancelar.py`, `integration/test_modificar.py` |
| RF-15 | El cliente crea su cuenta en la web o el operador en la tienda, con la misma función y las mismas reglas: correo y teléfono únicos, contraseña con al menos 8 caracteres, una mayúscula y un número. | ENT-15, ENT-54, ENT-84 | `accounts/registration.register_client` | `unit/test_contrasena_y_telefono.py`, `integration/test_registro.py`, `integration/test_usuarios.py`, `system/test_registro_web.py` |
| RF-16 | Solo el admin registra equipos, a mano: código `AAA-00000` único, número de serie único, nombre y valor mayor que 0. | ENT-14, ENT-83, PRE-01 | `inventory.register_equipment`, `Equipment` | `unit/test_codigo_de_equipo.py`, `integration/test_registrar_equipo.py` |
| RF-17 | El catálogo se pagina de 20 en 20 y se filtra por código o nombre, por fechas libres y, para el personal, por estado. | ENT-86, PRE-02 | `catalog.browse_catalog` (con `search_catalog` y `catalog_page`) | `integration/test_catalogo.py`, `system/test_recorridos.py` (filtro y páginas) |
| RF-18 | El responsable ve en una página las rentas activas, vencidas, reservas de hoy, pagos pendientes, equipos en revisión o reparación y deudas pendientes. | ENT-87, PRE-06, PRE-08 | `dashboard.manager_summary` | `integration/test_panel.py`, `integration/test_acceso.py` |
| RF-19 | Cada rol ve solo lo suyo y el admin ve todo. Solo el admin bloquea a un usuario desmarcando «Activo»: con su contraseña correcta ve «Tu cuenta está desactivada. Comunícate con la tienda.», su sesión abierta deja de valer y la tienda ya no lo encuentra para rentarle. | ENT-53, ENT-55, ENT-79 | `accounts/roles.role_required`, `LoginForm.confirm_login_allowed`, `AUTHENTICATION_BACKENDS` | `unit/test_roles.py`, `integration/test_acceso.py`, `integration/test_cuenta_desactivada.py` |
| RF-20 | El cliente recibe un correo al crear su cuenta, al confirmar o cancelar una renta y al crearse una deuda. Si el correo falla, la operación sigue. | ENT-85 | `rentals/services/notifications.py` | `integration/test_log_y_correo.py` (confirmación del QR, deuda por atraso y un correo que falla al crear la cuenta). Los correos de bienvenida y de cancelación se revisan en la consola durante la demo. |
| RF-21 | El admin corrige el estado de un equipo desde el admin de Django, con historial y sin crear deudas. | ENT-40, ENT-75, PRE-07 | `rentals/admin.py`, `history.change_status` | `system/test_recorridos.py` (el admin manda a reparación y queda el historial). Que no cree deudas se revisa en el código: la acción solo llama a `change_status`. |

## 3. Requisitos de calidad

| ID | Atributo | Requisito medible | Cómo se comprueba |
|---|---|---|---|
| RC-01 | Rendimiento | Con 1000 equipos, el catálogo muestra páginas de 20 y hace la misma cantidad de consultas que con 20 equipos (ENT-02). | `tests/integration/test_catalogo.py`: cuenta las consultas con 25 y con 1000 equipos. |
| RC-02 | Concurrencia | Si dos clientes confirman a la vez el mismo equipo y fechas, solo una renta se guarda; el segundo recibe «ocupado» (ENT-21, ENT-37). | En el código, cada escritura bloquea la fila con `select_for_update` (diagramas de la sección 5). La prueba con muchas confirmaciones a la vez es el issue #34 del tablero. |
| RC-03 | Seguridad | Cada página del personal responde 403 a otro rol; las contraseñas pasan los validadores; todo formulario lleva CSRF; los secretos viven en `.env`; `check --deploy` sin advertencias, salvo las de HTTPS en local. | `tests/integration/test_acceso.py`, `tests/integration/test_registro.py` y `python manage.py check --deploy` (resultado en [arquitectura.md](arquitectura.md#despliegue)). |
| RC-04 | Usabilidad | Todo rechazo dice en una frase qué pasó y qué hacer, sin términos técnicos; los formularios muestran los requisitos antes de enviar; las páginas se usan sin desplazamiento horizontal en un celular de 360 px y una tablet de 600 px (ENT-01, ENT-42). | Las pruebas comparan el mensaje exacto (por ejemplo `tests/unit/test_validar_periodo.py`); el ancho, a mano con el modo de dispositivo del navegador. |
| RC-05 | Trazabilidad | Cada operación, aceptada o rechazada, escribe una línea en `logs/negocio.log`; cada cambio de estado de un equipo queda en el historial. | `tests/integration/test_log_y_correo.py` (con `caplog`); en el admin, «Cambios de estado». |
| RC-06 | Mantenibilidad | Tasas y formatos en `settings.py`; cada regla tiene prueba de aceptación, límite y rechazo; el CI corre todo en cada push. | `python -m pytest -q` y GitHub Actions en cada push. |
| RC-07 | Despliegue | Desde cero, el sistema queda funcionando en Windows siguiendo el README: con `runserver` para programar o con waitress como en producción (`DEBUG=False`, estilos con whitenoise). | Seguir el README en una máquina limpia: «Instalar en Windows con PowerShell» y «Correr como en producción». |
| RC-08 | Compatibilidad | Funciona en las versiones actuales de Chrome y Firefox. | A mano antes de la entrega, en los dos navegadores. |

## 4. Historias de usuario

| ID | Historia | Dado | Cuando | Entonces |
|---|---|---|---|---|
| HU-01 | Como **cliente**, quiero crear mi cuenta para rentar en línea sin ir a la tienda. | No tengo cuenta | Lleno el formulario y presiono «Registrarme» | Veo «Cuenta creada» y recibo un correo de bienvenida; si algo falla, veo todas las causas juntas y no se guarda nada. |
| HU-02 | Como **operador**, quiero crear la cuenta de un cliente en la tienda para rentarle aunque no tenga cuenta. | El cliente no tiene cuenta | Lleno sus datos | La cuenta queda creada con las mismas reglas que en la web y puedo rentarle de inmediato. |
| HU-03 | Como **cliente**, quiero buscar equipos libres en mis fechas para elegir uno que sí pueda rentar. | Hay 1000 equipos | Escribo «silla» y elijo dos fechas | Veo solo las sillas libres en esas fechas, de 20 en 20. |
| HU-04 | Como **cliente**, quiero rentar y pagar en línea para asegurar el equipo sin ir a la tienda. | Las fechas están libres y no debo nada | Confirmo y pago con el QR | La renta queda «Reservada» y pagada; si el pago falla, queda reservada con el pago pendiente. |
| HU-05 | Como **operador**, quiero rentar a un cliente en la tienda para atender a quien llega sin reserva. | El cliente paga en efectivo | Registro la renta | Queda pagada en efectivo y «Reservada»; se entrega con «Registrar recojo». |
| HU-06 | Como **cliente**, quiero cambiar las fechas de mi reserva para ajustarla si cambia mi evento. | Faltan más de 24 h para el recojo | Elijo otras fechas con los mismos días | La reserva cambia de fechas y el precio no cambia. |
| HU-07 | Como **cliente**, quiero cancelar mi reserva para liberar las fechas si ya no la necesito. | Faltan más de 24 h | Presiono «Cancelar» | La reserva queda «Cancelada», recibo un correo y las fechas quedan libres. |
| HU-08 | Como **operador**, quiero entregar el equipo solo si está pagado para no perder el cobro. | La reserva tiene el pago pendiente | El cliente paga en efectivo | Se registra el pago y el recojo; si no paga, cancelo la reserva. |
| HU-09 | Como **operador**, quiero registrar la devolución y cobrar el atraso para que el equipo vuelva a revisión y la demora se pague. | La renta venció el día 10 | El equipo vuelve el 11 a las 12:01 | Se crea una deuda de 2 días × precio diario y el equipo pasa a revisión. |
| HU-10 | Como **mantenimiento**, quiero decidir qué pasa con un equipo devuelto para que solo se rente lo que está en buen estado. | El equipo está en revisión | Elijo «Baja» | Se crea la deuda del 100 % y se cancelan sus reservas futuras con aviso por correo. |
| HU-11 | Como **operador**, quiero registrar que un cliente pagó su deuda para que pueda volver a rentar. | El cliente debe 40 Bs | Registro el pago | La deuda queda pagada con mi usuario y el cliente puede volver a rentar. |
| HU-12 | Como **admin**, quiero registrar un equipo nuevo para que aparezca en el catálogo. | Tengo el código, la serie, el nombre y el valor | Guardo | El equipo queda «Disponible»; si el código no es `AAA-00000` o se repite, veo la causa. |
| HU-13 | Como **admin**, quiero corregir el estado de un equipo para arreglar un error sin cobrarle a nadie. | El equipo no está de baja | Elijo la acción en el admin | Cambia de estado, queda en el historial y no se crea deuda. |
| HU-14 | Como **admin**, quiero ver la historia de un equipo para saber quién lo cambió, cuándo y por qué. | Hubo cambios | Abro «Cambios de estado» | Veo quién, cuándo, de qué a qué y por qué, sin poder editarlo. |
| HU-15 | Como **responsable**, quiero ver lo urgente en una página para saber qué atender cada día. | Hay rentas vencidas y deudas | Abro el panel | Veo cada lista con su total y un enlace a su vista del admin. |
| HU-16 | Como **cliente**, quiero ver mis rentas, mis pagos y mi deuda para saber qué tengo pendiente. | Tengo rentas y una deuda | Abro «Mis rentas» | Veo el estado de cada renta, si está pagada y el total que debo. |

## 5. Casos de uso

**Cómo leer los diagramas:** la flecha continua es una llamada y la punteada, la respuesta. Los participantes llevan el nombre real del código: `views.X` está en `rentals/views/`, `use_cases.X` en `rentals/use_cases/` y `accounts.X` en `accounts/`. Las validaciones aparecen en el orden en que corren; la primera que falla corta la operación. En `alt`, cada rechazo va primero y **no guarda nada**. «Bloquea la fila» es `SELECT … FOR UPDATE`: si dos personas hacen clic a la vez, la segunda espera y ve lo que guardó la primera. Antes de cada vista, el middleware de Django carga la sesión, revisa el token CSRF e identifica al usuario; las páginas del personal además revisan el rol con `role_required`. En los diagramas, `#59;` es un punto y coma.

**Iniciar sesión:** con un usuario o una contraseña incorrectos se ve «Usuario o contraseña incorrectos.». Una cuenta desactivada por el admin ve «Tu cuenta está desactivada. Comunícate con la tienda.» solo si escribió su contraseña correcta, así el mensaje no da pistas a quien adivina cuentas; el log escribe `LOGIN_REJECTED reason=inactive user=cl01`. Si se desactiva con la sesión abierta, en su siguiente clic vuelve al login (ENT-79).

**Log:** cada operación escribe una línea en `logs/negocio.log` con el formato `2026-10-29 10:15:02 | INFO    | RENTAL_CREATED id=12 equipment=SIL-00001 client=cl01 paid=no`. Cada rechazo escribe `<ACCIÓN>_REJECTED reason="…"` con nivel `WARNING`. Nunca se escribe una contraseña.

---

### CU-01 — Crear cuenta

| | |
|---|---|
| **Actor** | Cliente (sin sesión) |
| **Precondición** | No tiene cuenta. |
| **Flujo normal** | 1. En «Iniciar sesión» presiona «Crear cuenta». 2. Escribe nombre, apellido, correo, teléfono, usuario, contraseña y su confirmación (la página muestra los requisitos de la contraseña). 3. Presiona «Registrarme». 4. Vuelve a «Iniciar sesión» con «Cuenta creada. Ya puedes iniciar sesión con cl03.». |
| **Flujos alternativos** | Si alguna regla falla, se queda en el formulario con los datos escritos (menos las contraseñas) y el título «No se creó la cuenta:» seguido de **todas** las causas: «Falta el campo Correo.» · «El correo no es válido.» · «El teléfono debe tener entre 7 y 15 números.» · «El usuario solo puede tener letras, números y los signos @ . + - _» · «Las contraseñas no coinciden.» · «La contraseña necesita al menos una mayúscula.» · «La contraseña necesita al menos un número.» · los mensajes de Django para contraseñas cortas, comunes, solo numéricas o parecidas al usuario · «El usuario cl03 ya existe.» · «El correo ya está registrado.» · «El teléfono ya está registrado.» · Si otra persona guarda el mismo usuario, correo o teléfono en el mismo instante: «El usuario, el correo o el teléfono ya están registrados.» |
| **Postcondición** | Existe un usuario con rol «cliente» que puede iniciar sesión. |
| **Guarda** | Una fila en `accounts_user` con la contraseña cifrada (`set_password`) y el teléfono solo con dígitos. |
| **Log** | `ACCOUNT_CREATED id=7 username=cl03 role=cliente registered_by=web` · `ACCOUNT_REJECTED reason="No se creó la cuenta: El usuario cl03 ya existe."` |
| **Correo** | Bienvenida. |
| **Origen** | ENT-15, ENT-84, PRE-01 |

```mermaid
sequenceDiagram
    actor C as Cliente
    participant V as accounts.views.sign_up
    participant U as accounts.registration.register_client
    participant BD as PostgreSQL
    C->>V: POST /signup/ con los 7 campos
    V->>U: register_client(SignUpData, registered_by=None)
    U->>U: cleaned: quita espacios y deja el teléfono solo con dígitos
    U->>U: check_new_client: campos, formatos y contraseña
    U->>BD: ¿usuario, correo o teléfono ya existen?
    alt alguna regla falla
        U-->>V: RegistrationRejectedError con todas las causas
        V-->>C: el formulario con «No se creó la cuenta:» y la lista
    else otra persona guardó los mismos datos en ese instante
        U->>BD: guarda el usuario
        BD-->>U: índice único repetido (IntegrityError)
        U-->>V: «El usuario, el correo o el teléfono ya están registrados.»
        V-->>C: el formulario con esa causa
    else todo bien
        U->>BD: guarda el usuario con rol cliente y la contraseña cifrada
        U-->>V: el usuario (el correo de bienvenida sale al confirmar la transacción)
        V-->>C: redirige al login con «Cuenta creada. Ya puedes iniciar sesión con cl03.»
    end
```

---

### CU-02 — Crear cuenta en tienda

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Precondición** | El cliente está en la tienda y no tiene cuenta. |
| **Flujo normal** | 1. Abre «Nuevo cliente». 2. Escribe los datos del cliente; el cliente escribe su contraseña. 3. Presiona «Registrar cliente». 4. Va a «Renta en tienda» con el cliente ya buscado y «Cuenta creada para cl03. Ya puedes registrar su renta.». |
| **Flujos alternativos** | Los mismos de CU-01, con el título «No se creó la cuenta:». |
| **Postcondición** | Igual que CU-01. |
| **Guarda** | Igual que CU-01. |
| **Log** | `ACCOUNT_CREATED id=8 username=cl04 role=cliente registered_by=op01` |
| **Correo** | Bienvenida. |
| **Origen** | ENT-54 («si el cliente no tiene cuenta, el operador puede registrarla»), ENT-84 |

```mermaid
sequenceDiagram
    actor O as Operador
    participant V as accounts.views.register_client_at_store
    participant U as accounts.registration.register_client
    participant BD as PostgreSQL
    O->>V: POST /staff/clients/new/
    V->>U: register_client(SignUpData, registered_by=op01)
    U->>U: check_new_client: campos, formatos y contraseña
    U->>BD: ¿usuario, correo o teléfono ya existen?
    alt alguna regla falla (las mismas de CU-01)
        U-->>V: RegistrationRejectedError con todas las causas
        V-->>O: el formulario con «No se creó la cuenta:» y la lista
    else todo bien
        U->>BD: guarda el usuario con rol cliente
        U-->>V: el usuario (y el correo de bienvenida)
        V-->>O: redirige a /staff/walk-in/?q=cl03 con «Cuenta creada para cl03. Ya puedes registrar su renta.»
    end
```

---

### CU-03 — Consultar equipos y disponibilidad

| | |
|---|---|
| **Actor** | Cliente; operador (también ve el filtro por estado) |
| **Precondición** | Tiene sesión. |
| **Flujo normal** | 1. Abre el catálogo: ve 20 equipos por página, cada uno con su precio por día y sus próximos periodos ocupados. 2. Escribe un código o un nombre, o elige «Libre desde» y «Libre hasta». 3. Presiona «Buscar» y ve solo los equipos que cumplen. 4. Pasa de página con «Anterior» y «Siguiente». |
| **Flujos alternativos** | Solo una fecha: «Elige las dos fechas para ver los equipos libres.» · Fecha final igual o anterior a la inicial: «La fecha final debe ser posterior a la inicial.» (en los dos casos el catálogo se muestra sin filtros, con el mensaje) · Sin resultados: «No hay equipos que coincidan con la búsqueda.» |
| **Postcondición** | No cambia nada. |
| **Guarda** | Nada. |
| **Log** | Nada (es una consulta). |
| **Origen** | ENT-02 (unos 1000 equipos), ENT-64, ENT-86, PRE-02 |

```mermaid
sequenceDiagram
    actor C as Cliente
    participant V as views.renting.catalog
    participant F as forms.CatalogFilterForm
    participant U as use_cases.catalog.browse_catalog
    participant BD as PostgreSQL
    C->>V: GET /?q=silla&free_from=…&free_to=…&page=2
    V->>F: filters()
    alt solo una fecha, o la final no es posterior a la inicial
        F-->>V: sin filtros, y el error en el formulario
    else filtros válidos
        F->>F: catalog_filters: desde las 18:00 del primer día hasta las 09:00 del último (D-13)
        F-->>V: CatalogFilters
    end
    V->>U: browse_catalog(cliente, filtros, página 2, ahora)
    U->>U: search_catalog: el cliente ve solo los «Disponibles», el personal ve todos
    U->>BD: total, 20 equipos y sus próximas rentas (3 consultas)
    U-->>V: la página
    alt la página no tiene equipos
        V-->>C: «No hay equipos que coincidan con la búsqueda.»
    else hay equipos
        V-->>C: el catálogo con el precio por día, los periodos ocupados, «Anterior» y «Siguiente»
    end
```

---

### CU-04 — Rentar en línea y pagar con QR simulado

| | |
|---|---|
| **Actor** | Cliente (`cl01`); Pasarela de pago simulada |
| **Precondición** | Tiene sesión y no tiene deuda pendiente. |
| **Flujo normal** | 1. En el catálogo presiona «Rentar» en un equipo. 2. Elige fecha y hora de recojo y de devolución y presiona «Continuar al pago». 3. La reserva queda guardada con el pago pendiente y ve la pantalla del QR con el total. 4. Presiona «Simular pago exitoso». 5. Ve la renta con «Pago recibido. Tu renta está confirmada.» y recibe el correo de confirmación. |
| **Flujos alternativos** | 2a. Horario o duración: se queda en el formulario con «La fecha y hora de devolución debe ser posterior a la de recojo.» · «La renta no puede durar más de 5 días.» · «El recojo debe ser desde las 18:00.» · «La devolución debe ser hasta las 09:00.» · 2b. Debe dinero: se queda en el formulario con «Tienes una deuda pendiente de 40,00 Bs. Págala en la tienda para volver a rentar.» · 2c. Fechas ocupadas: vuelve al catálogo con «El equipo MES-00002 está ocupado del 05/11/2026 18:00 al 07/11/2026 09:00. Está libre hasta el 05/11/2026 a las 09:00.» · 2d. Equipo no disponible: vuelve al catálogo con «El equipo MES-00002 no está disponible (estado: En revisión).» · 4a. Presiona «Simular pago fallido»: la reserva sigue hecha y ve «Tu reserva está hecha, pero el pago no se completó. Paga en la tienda al recoger el equipo.»; recibe el correo con el pago pendiente. · 4b. Ya pagada: «La renta de MES-00002 ya está pagada.» (si ya no está «Reservada», el mensaje de su estado, como en CU-06). |
| **Postcondición** | La renta queda «Reservada», pagada con QR o con el pago pendiente. |
| **Guarda** | Una fila en `rentals_rental` con `daily_price` (5 % del valor); con el pago exitoso, `paid_at` y `payment_method = qr`. |
| **Log** | `RENTAL_CREATED id=12 equipment=MES-00002 client=cl01 paid=no registered_by=web` · `PAYMENT_APPROVED rental=12 amount=40.00` · `PAYMENT_FAILED rental=12 amount=40.00` · `RENTAL_REJECTED reason="…"` · `PAYMENT_REJECTED reason="…"` |
| **Correo** | Renta confirmada (pagada o con el pago pendiente), al presionar un botón del QR (D-04). |
| **Origen** | ENT-16, ENT-21, ENT-48, ENT-66, ENT-67, ENT-71, ENT-77, PRE-03, PRE-04 |

```mermaid
sequenceDiagram
    actor C as Cliente
    participant V as views.renting (rent_equipment y pay_rental)
    participant R as use_cases.renting.create_rental
    participant P as use_cases.payments.pay_with_qr
    participant BD as PostgreSQL
    C->>V: POST /equipment/MES-00002/rent/ con las fechas
    V->>R: create_rental(cl01, MES-00002, inicio, fin)
    R->>R: check_period: orden, 5 días, recojo desde 18:00 y devolución hasta 09:00
    R->>BD: check_client_has_no_debt: suma sus deudas pendientes
    R->>BD: bloquea el equipo y lee sus rentas (check_equipment_is_free)
    alt 2a. horario o duración
        R-->>V: InvalidPeriodError
        V-->>C: el formulario con el mensaje
    else 2b. deuda pendiente
        R-->>V: DebtPendingError
        V-->>C: el formulario con el mensaje
    else 2c o 2d. fechas ocupadas o equipo no disponible
        R-->>V: EquipmentNotAvailableError
        V-->>C: redirige al catálogo con el mensaje
    else libre
        R->>BD: guarda la renta con daily_price y el pago pendiente
        R-->>V: la renta
        V-->>C: redirige a /rentals/12/pay/: el QR con el total
    end
    C->>V: POST /rentals/12/pay/ con result=approved o failed
    V->>P: pay_with_qr(renta, aprobado)
    P->>BD: bloquea la renta (check_can_pay_online)
    alt 4b. ya pagada o ya no está «Reservada»
        P-->>V: RentalStateError
        V-->>C: la renta con el mensaje
    else 4. pago exitoso
        P->>BD: guarda paid_at y payment_method = qr
        P-->>V: la renta (y el correo de confirmación)
        V-->>C: la renta con «Pago recibido. Tu renta está confirmada.»
    else 4a. pago fallido
        P-->>V: la renta sin cambios (y el correo con el pago pendiente)
        V-->>C: la renta con «Tu reserva está hecha, pero el pago no se completó. Paga en la tienda al recoger el equipo.»
    end
```

---

### CU-05 — Rentar en tienda

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Precondición** | El cliente tiene cuenta (si no, CU-02) y paga en efectivo. |
| **Flujo normal** | 1. Abre «Renta en tienda» y busca al cliente («rojas»). 2. Lo elige y elige el equipo y las fechas. 3. Cobra en efectivo y presiona «Registrar renta». 4. Ve la renta con «Registrada por op01» y «Pagado (efectivo)». 5. Si el cliente se la lleva al momento, registra el recojo como cualquier otro (CU-08). |
| **Flujos alternativos** | 1a. La búsqueda no encuentra a nadie: «No se encontró ningún cliente con «rojas».»; si no tiene cuenta, CU-02. · 3a. El cliente debe dinero: «El cliente cl02 tiene una deuda pendiente de 40,00 Bs. Cóbrala antes de registrar otra renta.» · 3b. Horario, duración o fechas ocupadas: los mensajes de CU-04, pero se queda en el formulario. La lista de equipos solo ofrece los «Disponibles». |
| **Postcondición** | La renta queda «Reservada» y pagada en efectivo (ENT-91). |
| **Guarda** | Una fila en `rentals_rental` con `daily_price`, `paid_at`, `payment_method = cash` y `registered_by`. |
| **Log** | `RENTAL_CREATED id=13 equipment=MES-00008 client=cl02 paid=yes registered_by=op01` · `PAYMENT_CASH rental=13 amount=40.00 received_by=op01` · `RENTAL_REJECTED reason="…"` |
| **Correo** | Renta confirmada (pagada). |
| **Origen** | ENT-54, ENT-70, ENT-77, ENT-91, PRE-03 |

```mermaid
sequenceDiagram
    actor O as Operador
    participant V as views.renting.walk_in_rental
    participant U as use_cases.renting
    participant BD as PostgreSQL
    O->>V: GET /staff/walk-in/?q=rojas
    V->>U: find_clients("rojas")
    U->>BD: hasta 10 clientes activos por usuario, nombre, apellido o correo
    alt 1a. nadie coincide
        V-->>O: «No se encontró ningún cliente con «rojas».»
    else hay clientes
        V-->>O: la lista de clientes y el formulario
    end
    O->>V: POST /staff/walk-in/?q=rojas (cl02, MES-00008, fechas)
    V->>U: create_rental(cl02, MES-00008, inicio, fin, registered_by=op01)
    U->>U: check_period
    U->>BD: check_client_has_no_debt
    U->>BD: bloquea el equipo y lee sus rentas (check_equipment_is_free)
    alt 3b. horario o duración
        U-->>V: InvalidPeriodError
        V-->>O: el formulario con el mensaje
    else 3a. deuda pendiente
        U-->>V: DebtPendingError con el mensaje para el operador (D-07)
        V-->>O: el formulario con el mensaje
    else 3b. fechas ocupadas
        U-->>V: EquipmentNotAvailableError
        V-->>O: el formulario con el mensaje
    else libre
        U->>BD: guarda la renta «Reservada» y pagada en efectivo
        U-->>V: la renta (PAYMENT_CASH en el log y el correo de confirmación)
        V-->>O: redirige a la renta: «Registrada por op01» y «Pagado (efectivo)»
    end
```

---

### CU-06 — Modificar una reserva

| | |
|---|---|
| **Actor** | Cliente (sus reservas, hasta 24 h antes); operador o admin (cualquier reserva, antes del recojo) |
| **Precondición** | La renta está «Reservada». |
| **Flujo normal** | 1. En «Mis rentas» (o en «Reservas por entregar») presiona «Modificar». 2. Elige las fechas nuevas, con la misma cantidad de días. 3. Presiona «Guardar cambios». 4. Vuelve a su lista con «Reserva modificada: MES-00001 ahora va del 06/11/2026 18:00 al 08/11/2026 09:00.». |
| **Flujos alternativos** | Horario o duración: los mensajes de CU-04. · Ya no está reservada: «La renta de MES-00001 ya fue entregada el 28/10/2026 18:30.» (o cancelada, devuelta, o «La reserva de MES-00001 venció a la medianoche.») · Faltan menos de 24 h y es el cliente: «Ya no puedes modificar en línea; comunícate con la tienda.» · Otra cantidad de días: «La reserva es de 2 días. Elige fechas con la misma cantidad de días; para cambiarla, cancela y renta de nuevo.» · Fechas ocupadas o equipo no disponible: los mensajes de CU-04. En todos, se queda en el formulario. |
| **Postcondición** | La reserva tiene las fechas nuevas; el precio no cambia. |
| **Guarda** | `start_datetime` y `end_datetime` de la renta. |
| **Log** | `RENTAL_MODIFIED id=12 equipment=MES-00001 start=2026-11-06T18:00 end=2026-11-08T09:00 by=cl01` · `MODIFY_REJECTED reason="…"` |
| **Origen** | ENT-55, ENT-80, ENT-81 |

```mermaid
sequenceDiagram
    actor C as Cliente
    participant V as views.renting.modify_reservation
    participant U as use_cases.renting.modify_rental
    participant BD as PostgreSQL
    C->>V: POST /rentals/12/modify/ con las fechas nuevas
    V->>U: modify_rental(renta, inicio, fin, cl01)
    U->>U: check_period
    U->>BD: bloquea el equipo y después la renta
    U->>U: check_can_modify, check_same_days y check_equipment_is_free
    alt horario o duración
        U-->>V: InvalidPeriodError
        V-->>C: el formulario con el mensaje
    else ya no está «Reservada»
        U-->>V: RentalStateError
        V-->>C: el formulario con «La renta de MES-00001 ya fue entregada el …»
    else faltan menos de 24 h y es el cliente
        U-->>V: DeadlinePassedError
        V-->>C: el formulario con «Ya no puedes modificar en línea#59; comunícate con la tienda.»
    else otra cantidad de días
        U-->>V: InvalidModificationError
        V-->>C: el formulario con «La reserva es de 2 días. Elige fechas con la misma cantidad de días#59; para cambiarla, cancela y renta de nuevo.»
    else fechas ocupadas o equipo no disponible
        U-->>V: EquipmentNotAvailableError
        V-->>C: el formulario con el mensaje
    else se puede
        U->>BD: guarda start_datetime y end_datetime
        U-->>V: la renta
        V-->>C: «Mis rentas» con «Reserva modificada: MES-00001 ahora va del … al ….» (el operador vuelve a «Reservas por entregar»)
    end
```

---

### CU-07 — Cancelar una reserva

| | |
|---|---|
| **Actor** | Cliente (hasta 24 h antes); operador o admin (antes del recojo; el admin también con la acción del admin) |
| **Precondición** | La renta está «Reservada». |
| **Flujo normal** | 1. Presiona «Cancelar» en la reserva. 2. Ve «Reserva cancelada: MES-00001 de cl01.». 3. El cliente recibe un correo con el motivo («Cancelaste tu reserva.» o «La tienda canceló tu reserva.»). |
| **Flujos alternativos** | Ya no está reservada: «La renta de MES-00001 ya fue cancelada el 27/10/2026 10:00.» (o entregada, devuelta, vencida). · Faltan menos de 24 h y es el cliente: «Ya no puedes cancelar en línea; comunícate con la tienda.» |
| **Postcondición** | La renta queda «Cancelada» y sus fechas quedan libres. La devolución del dinero ocurre fuera del sistema (ENT-82). |
| **Guarda** | `cancelled_at` y `cancelled_by`. |
| **Log** | `RENTAL_CANCELLED id=12 equipment=MES-00001 client=cl01 by=op01 reason="…"` · `CANCEL_REJECTED reason="…"` |
| **Correo** | Renta cancelada, con el motivo. |
| **Origen** | ENT-47, ENT-55, ENT-80, ENT-82 |

```mermaid
sequenceDiagram
    actor C as Cliente u operador
    participant V as views.renting.cancel_reservation
    participant U as use_cases.renting.cancel_rental
    participant BD as PostgreSQL
    C->>V: POST /rentals/12/cancel/
    V->>U: cancel_rental(renta, usuario)
    U->>BD: bloquea la renta
    U->>U: check_can_cancel: primero el estado, después el plazo de 24 h
    alt ya no está «Reservada»
        U-->>V: RentalStateError
        V-->>C: su lista con «La renta de MES-00001 ya fue cancelada el …»
    else faltan menos de 24 h y es el cliente
        U-->>V: DeadlinePassedError
        V-->>C: su lista con «Ya no puedes cancelar en línea#59; comunícate con la tienda.»
    else se puede
        U->>BD: guarda cancelled_at y cancelled_by
        U-->>V: la renta (y el correo con el motivo)
        V-->>C: su lista con «Reserva cancelada: MES-00001 de cl01.»
    end
```

---

### CU-08 — Entregar el equipo

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Precondición** | La renta está «Reservada». |
| **Flujo normal** | 1. Abre «Reservas por entregar». 2. Si está pagada, presiona «Registrar recojo». 3. Ve «Recojo registrado: MES-00001 entregado a cl01.». |
| **Flujos alternativos** | Pago pendiente: el botón dice «Cobrar 40,00 Bs y entregar»; al presionarlo se guarda el cobro en efectivo y el recojo, y ve «Cobro de 40,00 Bs en efectivo y recojo registrados: MES-00001 entregado a cl01.» · El cliente no paga: presiona «Cancelar» (CU-07). · Se intenta entregar sin cobrar: «Falta el pago de 40,00 Bs de esta renta. Cóbralo en efectivo o cancela la reserva si el cliente no paga.» · Ya no está reservada: «La reserva de MES-00001 venció a la medianoche.» (o entregada, cancelada, devuelta). |
| **Postcondición** | La renta queda «Rentada» y pagada. |
| **Guarda** | `picked_up_at` y `handed_over_by`; si se cobró, también `paid_at` y `payment_method = cash`. |
| **Log** | `PAYMENT_CASH rental=12 amount=40.00 received_by=op01` · `PICKUP_REGISTERED id=12 equipment=MES-00001 client=cl01 by=op01` · `PICKUP_REJECTED reason="…"` |
| **Origen** | ENT-56, ENT-57, ENT-68, ENT-69 |

```mermaid
sequenceDiagram
    actor O as Operador
    participant V as views.handover.pickup_reservation
    participant U as use_cases.handover.register_pickup
    participant BD as PostgreSQL
    O->>V: POST /staff/reservations/12/pickup/ (paid_now=yes si cobró)
    V->>U: register_pickup(renta, op01, paid_now)
    U->>BD: bloquea la renta
    U->>U: check_can_pick_up y, con el pago pendiente, check_payment_received
    alt ya no está «Reservada»
        U-->>V: RentalStateError
        V-->>O: la lista con «La reserva de MES-00001 venció a la medianoche.» (o entregada, cancelada, devuelta)
    else pago pendiente y no se cobró
        U-->>V: PaymentRequiredError
        V-->>O: la lista con «Falta el pago de 40,00 Bs de esta renta. Cóbralo en efectivo o cancela la reserva si el cliente no paga.»
    else pago pendiente y se cobró en efectivo
        U->>BD: guarda paid_at, payment_method = cash, picked_up_at y handed_over_by
        V-->>O: la lista con «Cobro de 40,00 Bs en efectivo y recojo registrados: MES-00001 entregado a cl01.»
    else ya estaba pagada
        U->>BD: guarda picked_up_at y handed_over_by
        V-->>O: la lista con «Recojo registrado: MES-00001 entregado a cl01.»
    end
    Note over O,V: Si el cliente no paga, el operador cancela la reserva (CU-07).
```

---

### CU-09 — Registrar la devolución

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Precondición** | La renta está «Rentada»: el equipo salió y todavía no volvió (ENT-93). |
| **Flujo normal** | 1. Abre «Devoluciones pendientes». 2. Elige la renta y escribe cómo llegó el equipo. 3. Presiona «Registrar devolución». 4. Ve «Devolución registrada: MES-00004 recibido de cl01. A tiempo.» (o «En tolerancia, sin cobro.»). |
| **Flujos alternativos** | Sin observación: «Escribe cómo llegó el equipo.» · Nunca se entregó: «La renta de MES-00004 nunca se entregó: solo se devuelve una renta «Rentada».» · Ya devuelta o cancelada: «La renta de MES-00004 ya fue devuelta el 28/10/2026 08:30.» · Llega desde las 12:01 del día de vencimiento: se crea la deuda y ve «… Con 2 días de atraso: deuda de 40,00 Bs.»; el cliente recibe el correo de la deuda. · Si mantenimiento ya le cambió el estado mientras estaba afuera, se respeta (D-28). |
| **Postcondición** | La renta queda «Devuelta» y el equipo «En revisión». |
| **Guarda** | `returned_at`, `received_by`, `return_note`; el estado del equipo y una fila en `rentals_statuschange`; con atraso, una fila en `rentals_debt` con `late_return`. |
| **Log** | `RETURN_REGISTERED id=12 equipment=MES-00004 client=cl01 by=op01 result=late late_days=2` · `STATUS_CHANGED equipment=MES-00004 old=available new=in_review by=op01` · `DEBT_CREATED id=3 rental=12 client=cl01 reason=late_return amount=40.00` · `RETURN_REJECTED reason="…"` |
| **Correo** | Deuda creada (si hubo atraso). |
| **Origen** | ENT-03, ENT-73, ENT-93, PRE-05 |

```mermaid
sequenceDiagram
    actor O as Operador
    participant V as views.handover.return_rental
    participant U as use_cases.handover.register_return
    participant H as use_cases.history.change_status
    participant BD as PostgreSQL
    O->>V: POST /staff/returns/12/ con la observación
    V->>U: register_return(renta, op01, nota)
    alt sin observación
        U-->>V: IncompleteReturnError
        V-->>O: el formulario con «Escribe cómo llegó el equipo.»
    else hay observación
        U->>BD: bloquea la renta (check_can_return)
        alt no está «Rentada»
            U-->>V: RentalStateError
            V-->>O: el formulario con «… nunca se entregó …» o «… ya fue devuelta el …»
        else se puede devolver
            U->>BD: guarda returned_at, received_by y return_note
            U->>H: change_status(equipo, «En revisión», op01, nota), si sigue «Disponible» (D-28)
            H->>BD: bloquea el equipo, guarda el estado y la fila de historial
            alt desde las 12:01 del día de vencimiento
                U->>BD: charge_debt: deuda late_return = días de atraso × precio diario
                V-->>O: «Devolución registrada: MES-00004 recibido de cl01. Con 2 días de atraso: deuda de 40,00 Bs.»
            else hasta las 12:00
                V-->>O: «Devolución registrada: MES-00004 recibido de cl01. A tiempo.» o «… En tolerancia, sin cobro.»
            end
        end
    end
```

---

### CU-10 — Revisar el equipo

| | |
|---|---|
| **Actor** | Mantenimiento (`mt01`) |
| **Precondición** | El equipo está «En revisión» o «En reparación». |
| **Flujo normal** | 1. Abre «Mantenimiento». 2. Elige «Disponible», «En reparación» o «Baja» y escribe un comentario opcional. 3. Presiona «Guardar». 4. Ve «MES-00005 ahora está «Disponible».». |
| **Flujos alternativos** | Estado que no es resultado de revisión: «El equipo MES-00006 solo puede pasar a disponible, en reparación o baja.» · De baja: «El equipo MES-00007 está dado de baja; su estado ya no puede cambiar.» · Mismo estado: «El equipo MES-00006 ya está «En reparación».» · En reparación: se crea la deuda del 20 % para el cliente de la última renta devuelta y ve «MES-00006 ahora está «En reparación». Deuda de 80,00 Bs para cl01.» · Baja: deuda del 100 % (o lo que falta para llegar al valor, si esa renta ya tenía la deuda de reparación: 320,00 Bs después de 80,00 Bs), se cancelan las reservas futuras del equipo (con correo a cada cliente) y ve «MES-00007 ahora está «Baja». Deuda de 400,00 Bs para cl02. Reservas futuras canceladas: 1.» · Sin renta devuelta antes, no hay a quién cobrar y no se crea deuda (D-05). |
| **Postcondición** | El equipo tiene su estado nuevo y queda en el historial. |
| **Guarda** | El estado del equipo y una fila en `rentals_statuschange`; con reparación o baja, una fila en `rentals_debt`; con baja, `cancelled_at` y `cancelled_by` (mantenimiento) en cada reserva futura. Todo en una sola transacción. |
| **Log** | `STATUS_CHANGED equipment=MES-00007 old=in_review new=retired by=mt01` · `DEBT_CREATED id=4 rental=9 client=cl02 reason=retired amount=400.00` · `RENTAL_CANCELLED id=15 … by=mt01 reason="…"` · `REVIEW_REJECTED reason="…"` |
| **Correo** | Deuda creada; renta cancelada a cada cliente afectado. |
| **Origen** | ENT-03, ENT-34, ENT-47, ENT-49, ENT-74, PRE-06 |

```mermaid
sequenceDiagram
    actor T as Mantenimiento
    participant V as views.review.review_equipment_view
    participant U as use_cases.review.review_equipment
    participant H as use_cases.history.change_status
    participant BD as PostgreSQL
    T->>V: POST /maintenance/MES-00007/ con el estado y el comentario
    V->>U: review_equipment(MES-00007, mt01, estado, comentario)
    U->>U: check_review_result
    alt no es disponible, en reparación ni baja
        U-->>V: InvalidStatusChangeError
        V-->>T: la lista con «El equipo MES-00006 solo puede pasar a disponible, en reparación o baja.»
    else es un resultado de revisión
        U->>H: change_status(equipo, estado, mt01, comentario)
        H->>BD: bloquea el equipo y lee su estado (check_status_can_change)
        alt de baja o ya tiene ese estado
            H-->>U: InvalidStatusChangeError
            U-->>V: el mismo rechazo
            V-->>T: la lista con «… está dado de baja#59; su estado ya no puede cambiar.» o «… ya está «En reparación».»
        else se puede cambiar
            H->>BD: guarda el estado nuevo y la fila de historial
            U->>BD: charge_damage: busca la última renta devuelta del equipo
            alt «Disponible»
                V-->>T: «MES-00005 ahora está «Disponible».»
            else «En reparación»
                U->>BD: deuda repair del 20 % del valor (charge_debt)
                V-->>T: «MES-00006 ahora está «En reparación». Deuda de 80,00 Bs para cl01.»
            else «Baja»
                U->>BD: deuda retired: el valor menos lo ya cobrado por daño (D-06)
                U->>BD: cancel_rental en cada reserva futura del equipo
                V-->>T: «MES-00007 ahora está «Baja». Deuda de 400,00 Bs para cl02. Reservas futuras canceladas: 1.»
            end
        end
    end
    Note over U,BD: Sin renta devuelta antes no hay a quién cobrar: no se crea deuda (D-05).
```

---

### CU-11 — Registrar el pago de una deuda

| | |
|---|---|
| **Actor** | Operador (`op01`) |
| **Precondición** | El cliente tiene una deuda pendiente y paga en la tienda. |
| **Flujo normal** | 1. Abre «Deudas»: ve las deudas pendientes y el total por cliente. 2. Cobra y presiona «Registrar pago» en una deuda. 3. Ve «Pago registrado: deuda de 40,00 Bs de cl02.». |
| **Flujos alternativos** | Ya pagada (por ejemplo, otro operador hizo clic antes): «Esta deuda ya se pagó el 28/10/2026 10:00.» |
| **Postcondición** | La deuda queda pagada; si era la última, el cliente puede volver a rentar. |
| **Guarda** | `paid_at` y `paid_received_by` en esa deuda. |
| **Log** | `DEBT_PAID id=3 client=cl02 amount=40.00 received_by=op01` · `DEBT_PAYMENT_REJECTED reason="…"` |
| **Origen** | ENT-76, ENT-77, ENT-78 |

```mermaid
sequenceDiagram
    actor O as Operador
    participant V as views.debts.pay_debt_view
    participant U as use_cases.payments.pay_debt
    participant BD as PostgreSQL
    O->>V: POST /staff/debts/3/pay/
    V->>U: pay_debt(deuda, op01)
    U->>BD: bloquea la deuda (check_debt_is_pending)
    alt ya pagada
        U-->>V: DebtStateError
        V-->>O: la lista con «Esta deuda ya se pagó el 28/10/2026 10:00.»
    else pendiente
        U->>BD: guarda paid_at y paid_received_by
        U-->>V: la deuda
        V-->>O: la lista con «Pago registrado: deuda de 40,00 Bs de cl02.»
    end
```

---

### CU-12 — Registrar un equipo

| | |
|---|---|
| **Actor** | Administrador (`ad01`) |
| **Precondición** | Tiene el código, el número de serie, el nombre y el valor de compra. |
| **Flujo normal** | 1. Abre «Registrar equipo». 2. Escribe el código (`mes-00021` se guarda como `MES-00021`), la serie, el nombre y el valor. 3. Presiona «Registrar equipo». 4. Ve «Equipo registrado: MES-00021 · Mesa plegable 1,80 m.». |
| **Flujos alternativos** | Se queda en el formulario con «No se registró el equipo:» y las causas: «El código debe tener 3 letras, un guion y 5 números, por ejemplo MES-00001.» · «Ya existe un equipo con este código.» · «Ya existe un equipo con este número de serie.» · «El valor debe ser mayor que 0.» · «Falta el campo Nombre.» · Si otro admin guarda el mismo código o serie en el mismo instante: «Ya existe un equipo con este código o número de serie.» También se puede registrar en el admin de Django, con las mismas validaciones. |
| **Postcondición** | El equipo existe, «Disponible», y aparece en el catálogo. |
| **Guarda** | Una fila en `rentals_equipment` con `created_at`. |
| **Log** | `EQUIPMENT_REGISTERED id=21 equipment=MES-00021 value=400.00 by=ad01` · `EQUIPMENT_REJECTED reason="…"` |
| **Origen** | ENT-09, ENT-14, ENT-83, PRE-01 |

```mermaid
sequenceDiagram
    actor A as Administrador
    participant V as views.inventory.register_equipment_view
    participant U as use_cases.inventory.register_equipment
    participant BD as PostgreSQL
    A->>V: POST /equipment/new/
    V->>U: register_equipment(código, serie, nombre, valor, ad01)
    U->>U: normalize_inventory_id: «mes-00021» pasa a «MES-00021»
    U->>BD: check_new_equipment: reglas del modelo y ¿código o serie repetidos?
    alt alguna regla falla
        U-->>V: EquipmentRegistrationError con todas las causas
        V-->>A: el formulario con «No se registró el equipo:» y la lista
    else otro admin guardó el mismo código o serie en ese instante
        U->>BD: guarda el equipo
        BD-->>U: índice único repetido (IntegrityError)
        U-->>V: «Ya existe un equipo con este código o número de serie.»
        V-->>A: el formulario con esa causa
    else todo bien
        U->>BD: guarda el equipo «Disponible»
        U-->>V: el equipo
        V-->>A: «Equipo registrado: MES-00021 · Mesa plegable 1,80 m.»
    end
```

---

### CU-13 — Corregir el estado de un equipo

| | |
|---|---|
| **Actor** | Administrador (`ad01`) |
| **Precondición** | Está en el admin de Django. |
| **Flujo normal** | 1. En «Equipos» marca uno o varios. 2. Elige «Marcar disponible», «Mandar a reparación» o «Dar de baja». 3. Ve «Equipos actualizados: 1.». |
| **Flujos alternativos** | De baja o ya en ese estado: aparecen en «No se cambiaron: MES-00007.». |
| **Postcondición** | El estado cambia y queda en el historial. **No crea deudas** ni cancela reservas (ENT-75): es una corrección, no una revisión. |
| **Guarda** | El estado del equipo y una fila en `rentals_statuschange`. |
| **Log** | `STATUS_CHANGED equipment=MES-00002 old=available new=in_repair by=ad01` · `STATUS_CHANGE_REJECTED reason="…"` |
| **Origen** | ENT-40, ENT-50, ENT-75, PRE-07 |

```mermaid
sequenceDiagram
    actor A as Administrador
    participant V as admin.EquipmentAdmin.change_selected
    participant U as use_cases.history.change_status
    participant BD as PostgreSQL
    A->>V: acción «Mandar a reparación» con los equipos marcados
    loop por cada equipo marcado (apply_to_selected)
        V->>U: change_status(equipo, «En reparación», ad01)
        U->>BD: bloquea el equipo y lee su estado
        alt de baja o ya tiene ese estado
            U-->>V: InvalidStatusChangeError: va a «No se cambiaron»
        else se puede
            U->>BD: guarda el estado nuevo y la fila de historial
        end
    end
    V-->>A: «Equipos actualizados: 1.» y, si hubo rechazos, «No se cambiaron: MES-00007.»
```

---

### CU-14 — Consultar el historial

| | |
|---|---|
| **Actor** | Administrador (`ad01`) |
| **Precondición** | Está en el admin de Django. |
| **Flujo normal** | 1. Abre «Cambios de estado». 2. Filtra por estado nuevo o por quién lo cambió, o busca un código. 3. Ve quién, cuándo, de qué a qué y por qué. |
| **Flujos alternativos** | No puede agregar, editar ni borrar filas: el historial es evidencia. |
| **Postcondición** | No cambia nada. |
| **Guarda** | Nada. |
| **Log** | Nada. |
| **Origen** | ENT-34, PRE-07, PRE-08 |

```mermaid
sequenceDiagram
    actor A as Administrador
    participant V as admin.StatusChangeAdmin
    participant BD as PostgreSQL
    alt busca o filtra
        A->>V: GET /admin/rentals/statuschange/?q=MES-00007
        V->>BD: cambios de ese equipo, el más nuevo primero
        V-->>A: la lista de solo lectura
    else intenta agregar, editar o borrar
        A->>V: abre una fila o busca el botón «Agregar»
        V-->>A: solo lectura: has_add, has_change y has_delete_permission responden False
    end
```

---

### CU-15 — Ver el panel del responsable

| | |
|---|---|
| **Actor** | Administrador (`ad01`): al iniciar sesión llega aquí |
| **Precondición** | Tiene el rol administrador. |
| **Flujo normal** | 1. Abre «Panel». 2. Ve seis listas con su cantidad: rentas activas, rentas vencidas (pasó la devolución y no se devolvió), reservas de hoy, reservas con pago pendiente, equipos en revisión o reparación y deudas pendientes (total y por cliente). 3. Presiona «Ver en el admin» en una lista y llega a esa misma lista filtrada en el admin. |
| **Flujos alternativos** | Lista vacía: «Nada por aquí.» |
| **Postcondición** | No cambia nada. |
| **Guarda** | Nada. |
| **Log** | Nada. |
| **Origen** | ENT-87, PRE-06, PRE-08 |

```mermaid
sequenceDiagram
    actor A as Administrador
    participant V as views.dashboard.manager_dashboard
    participant U as use_cases.dashboard.manager_summary
    participant BD as PostgreSQL
    A->>V: GET /manager/
    V->>U: manager_summary(ahora)
    U->>BD: por cada lista, su total y sus primeras 10 filas, y la deuda total
    U-->>V: ManagerSummary con las seis listas
    alt una lista está vacía
        V-->>A: esa lista dice «Nada por aquí.»
    else la lista tiene filas
        V-->>A: el total, las filas y «Ver en el admin»
    end
```

---

### CU-16 — Consultar mis rentas y mi deuda

| | |
|---|---|
| **Actor** | Cliente (`cl02`) |
| **Precondición** | Tiene sesión. |
| **Flujo normal** | 1. Abre «Mis rentas». 2. Ve cada renta con sus fechas, total, estado y pago («Pagado (QR)», «Pagado (efectivo)» o «Pago pendiente»). 3. Si debe, ve arriba «Tienes una deuda pendiente de 40,00 Bs. Págala en la tienda para volver a rentar.» y el detalle de cada deuda. 4. En sus reservas ve «Modificar» y «Cancelar». |
| **Flujos alternativos** | Sin rentas: «Todavía no tienes rentas.» · Sin deuda: no ve el aviso. |
| **Postcondición** | No cambia nada. |
| **Guarda** | Nada. |
| **Log** | Nada. |
| **Origen** | ENT-55, ENT-76, PRE-08 |

```mermaid
sequenceDiagram
    actor C as Cliente
    participant V as views.renting.client_rentals
    participant U as use_cases.renting.my_rentals
    participant BD as PostgreSQL
    C->>V: GET /my-rentals/
    V->>U: my_rentals(cl02)
    U->>BD: sus rentas, sus deudas pendientes y su suma
    U-->>V: ClientRentals
    alt debe dinero
        V-->>C: arriba, «Tienes una deuda pendiente de 40,00 Bs. Págala en la tienda para volver a rentar.» y cada deuda
    else no debe
        V-->>C: sin aviso de deuda
    end
    alt no tiene rentas
        V-->>C: «Todavía no tienes rentas.»
    else tiene rentas
        V-->>C: la tabla con estado y pago, y «Modificar» y «Cancelar» en sus reservas
    end
```

---

## 6. Qué guarda cada botón

Las funciones están en `rentals/use_cases/`, salvo `accounts.registration` y `UserAdmin` (en `accounts/`).

| Botón | Función | Qué cambia en la base |
|---|---|---|
| Registrarme / Registrar cliente | `accounts.registration.register_client` | Una fila en `accounts_user` |
| Continuar al pago / Registrar renta | `renting.create_rental` | Una fila en `rentals_rental` (en tienda, ya pagada) |
| Simular pago exitoso | `payments.pay_with_qr` | `paid_at`, `payment_method` |
| Guardar cambios (modificar) | `renting.modify_rental` | `start_datetime`, `end_datetime` |
| Cancelar | `renting.cancel_rental` | `cancelled_at`, `cancelled_by` |
| Registrar recojo / Cobrar y entregar | `handover.register_pickup` | `picked_up_at`, `handed_over_by` (y `paid_at`, `payment_method`) |
| Registrar devolución | `handover.register_return` | `returned_at`, `received_by`, `return_note`, estado del equipo, historial y, con atraso, una deuda |
| Guardar (mantenimiento) | `review.review_equipment` | Estado del equipo, historial, deuda y reservas canceladas si es baja |
| Registrar pago (deuda) | `payments.pay_debt` | `paid_at`, `paid_received_by` |
| Registrar equipo | `inventory.register_equipment` | Una fila en `rentals_equipment` |
| Acciones del admin | `history.change_status`, `renting.cancel_rental`, `payments.pay_debt` | Lo mismo que arriba |
| Guardar (admin de usuarios, «Activo») | `UserAdmin.save_model` | `is_active`; el log escribe `ACCOUNT_DEACTIVATED user=cl01 by=ad01` o `ACCOUNT_REACTIVATED` |

## 7. Fuera de alcance

| Qué | Por qué no |
|---|---|
| PIN o verificación por SMS | Necesita un proveedor de SMS pagado; el equipo decidió registrar con correo y teléfono únicos (ENT-84). |
| Notificaciones por SMS, WhatsApp o Telegram | Cada canal necesita una cuenta de empresa y un proveedor; el correo cubre los avisos que definió el equipo (ENT-85). |
| Login con Google | Exige registrar la app en Google y no lo pidió el cliente; el usuario y la contraseña bastan. |
| Lector de código de barras o RFID | Necesita hardware; el admin escribe el código a mano (ENT-83). |
| Importación masiva de equipos | El cliente dijo que «puede mega esperar» (ENT-14). |
| Cliente frecuente | El cliente no definió qué lo hace frecuente (ENT-20); todos rentan como máximo 5 días. |
| Cobro forzoso y reporte de pérdidas | El sistema no cobra a la fuerza: la deuda queda visible y bloquea nuevas rentas (ENT-78). |
| Garantía | El precio no la separa; el daño se cobra como deuda de reparación o baja (ENT-74). |
| Validación real del pago | El QR es simulado (ENT-66); `payments.pay_with_qr` recibe solo «aprobado o no», así una pasarela real se conecta sin tocar la renta (ENT-48). |
| Restricción de exclusión en PostgreSQL (issue #30) | Que una renta ocupe el equipo depende de la hora (una reserva no recogida lo libera a la medianoche, ENT-69) y una restricción de la base no puede mirar la hora. El cruce ya se evita bloqueando la fila del equipo (RC-02, D-24). |
| Errores del servidor (500) en `logs/negocio.log` | El log de negocio registra las operaciones del negocio (RC-05); Django escribe los errores del servidor en su propio log, en la consola. El usuario ve la página 500 en español, sin detalles técnicos. |
