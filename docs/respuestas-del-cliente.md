# Respuestas del cliente

> Lo que dijo SergioCorp (Sergio Barrientos) en clase, por WhatsApp, en el audio del 15/10, en la charla del 27/10, por WhatsApp el 28/10 y al revisar el sistema el 29/10. El código y los documentos citan estas respuestas como ENT-xx.
> Desde ENT-66, cada fila separa lo que dijo el cliente («Cliente: …») de lo que decidió el equipo para completarlo («Equipo: …»). El estado dice `confirmado` para lo del cliente y `decisión del equipo` para lo demás.
> Si una respuesta cambió después, la fila dice cuál la reemplaza: vale la más nueva.

## Vocabulario

| Término | Significado | Fuente |
|---|---|---|
| Renta | Un cliente, un equipo y un periodo. | ENT-06 |
| Reservada | Renta confirmada cuyo equipo todavía no se recogió. | ENT-55, ENT-57 |
| Rentada | Renta cuyo equipo el cliente ya recogió. | ENT-57 |
| Estado del equipo | Solo su condición física: disponible, en revisión, en reparación o baja. «Reservado» y «rentado» dependen de las fechas de cada renta. | ENT-61 |
| No recogida | Reserva que nadie recogió hasta la medianoche de su día de inicio; deja el equipo libre. | ENT-69 |
| Pago pendiente | Reserva hecha cuyo pago no se completó; se cobra en efectivo al recoger. | ENT-67, ENT-68 |
| Deuda | Cargo de una renta por atraso, reparación o baja. Mientras no se paga, el cliente no puede rentar. | ENT-76, ENT-77 |
| Combo | Un equipo más, con código propio (por ejemplo `CMB-00001`) y su valor; no descuenta las sillas y mesas sueltas. | ENT-96 |

## Respuestas

| ID | Pregunta | Respuesta | Fuente | Estado |
|---|---|---|---|---|
| ENT-01 | ¿Página web o aplicación? | Página web que se vea en celular, pantalla y tablet. | Clase | confirmado |
| ENT-02 | ¿Qué volumen debe soportar? | Unos 1000 equipos; en el mejor momento, 70 % rentado. Hay que comprobar la concurrencia con muchas peticiones a la vez. | Clase | confirmado (volumen); pendiente (70 %, ENT-27) |
| ENT-03 | ¿Qué pasa con un equipo cuando vuelve? | No vuelve directo a rentarse: mantenimiento lo pasa a disponible, reparación o baja. | Clase | confirmado |
| ENT-04 | ¿Qué pasa si no se devuelve a tiempo? | Multa del 5 % por hora después de las 9:00. | Clase | reemplazado por ENT-63 |
| ENT-05 | ¿Cómo es una renta típica? | Catálogo de equipos o combos; se renta en línea o en persona con un operador. | WhatsApp (Peter) | confirmado |
| ENT-06 | ¿«Reserva», «préstamo», «renta» y «booking» son lo mismo? | «Es lo mismo». | WhatsApp (Peter) | confirmado; ver Vocabulario |
| ENT-07 | ¿Varias empresas publican productos? | «Con que sea mesas y sillas basta. Para eventos.» Una sola empresa. | WhatsApp (Peter) | confirmado |
| ENT-08 | ¿Qué es un combo? | Equipos sueltos que se rentan juntos (6 mesas y 36 sillas). | WhatsApp (Peter) | reemplazado por ENT-96 |
| ENT-09 | ¿Se registra cada silla o solo la cantidad? | Cada equipo se registra individualmente. | WhatsApp (Peter) | confirmado |
| ENT-10 | ¿Una renta futura aparta el equipo? | Sí, solo para ese periodo; antes debería poder rentarse. | WhatsApp (Peter) | confirmado; precisado en ENT-61 y ENT-64 |
| ENT-11 | ¿Hay información que un rol no deba ver? | «Lo dejo por ahora a sentido común.» | WhatsApp (Peter) | reemplazado por ENT-55 |
| ENT-12 | ¿Qué hace el cliente por su cuenta? | Renta desde la web. Los casos de uso los propone el equipo. | WhatsApp (Peter) | confirmado |
| ENT-13 | ¿Responsable y superusuario son la misma persona? | Sí. «Si es super user puede hacer todo.» | WhatsApp (Peter) | confirmado (ver ENT-44) |
| ENT-14 | ¿Quién registra un equipo nuevo? | El administrador. La importación masiva «puede mega esperar». | WhatsApp (Peter) | confirmado |
| ENT-15 | ¿El cliente se registra solo o lo registra un operador? | «Puede ser los dos.» | WhatsApp (Peter) | confirmado (ver ENT-54) |
| ENT-16 | ¿La renta en línea se confirma al instante? | Al instante, «como add to cart». | WhatsApp (Peter) | confirmado |
| ENT-17 | ¿Anticipación mínima y máxima? | «No hay límite con la anticipación. Puede ser al instante.» | WhatsApp (Peter) | confirmado; precisado en ENT-94 (no se elige una fecha pasada) |
| ENT-18 | ¿Cuánto dura una renta? | 5 días; 2 semanas para clientes frecuentes. | WhatsApp (Peter) | confirmado (5 días); pendiente (frecuentes, ENT-20) |
| ENT-19 | ¿Horarios de entrega y devolución? | Se entrega desde las 18:00 y se devuelve hasta las 9:00. | WhatsApp (Peter) | confirmado (ver ENT-52 y ENT-65) |
| ENT-20 | ¿Qué hace «frecuente» a un cliente? | «No lo sé todavía. Mostrame el caso de uso.» | WhatsApp (Peter) | pendiente |
| ENT-21 | Dos clientes quieren el último equipo: ¿quién se lo queda? | «El primero que le dio click.» | Clase y WhatsApp | confirmado |
| ENT-22 | ¿Hasta cuándo se puede recoger? | «Hasta las 20 de ese día o las 12 del siguiente.» | WhatsApp (Peter) | reemplazado por ENT-59 |
| ENT-23 | ¿Qué pasa si nadie recoge? | «Los multas si deseas o rentas el equipo a otro.» | WhatsApp (Peter) | reemplazado por ENT-59 |
| ENT-24 | ¿El cliente puede cambiar o cancelar? | Sí, con 24 h de anticipación; si no, multa. | WhatsApp (Peter) | reemplazado por ENT-80 |
| ENT-25 | ¿Cuándo se bloquea a un cliente? | Si no recogió una renta anterior. | WhatsApp (Peter) | reemplazado por ENT-58 |
| ENT-26 | ¿Rentas con anticipación y multas entran aunque el encargo las excluye? | Sin respuesta explícita. | WhatsApp (Peter) | confirmado por ENT-47 y ENT-63 |
| ENT-27 | ¿El 70 % es un tope o una estimación? | Sin respuesta. | WhatsApp (Peter) | pendiente |
| ENT-28 | ¿Qué ve el responsable y qué ve el cliente? | Sin respuesta. | WhatsApp (Peter) | reemplazado por ENT-55 |
| ENT-29 | ¿Qué demora sería inaceptable? | Sin respuesta. | WhatsApp (Peter) | pendiente |
| ENT-30 | ¿Qué es imprescindible para la próxima entrega? | Sin respuesta. | WhatsApp (Peter) | reemplazado por ENT-35 |
| ENT-31 | ¿Hay tolerancia en la devolución de las 9:00? | «Tolerancia 5 min.» | WhatsApp (Sofia) | reemplazado por ENT-63 |
| ENT-32 | ¿Sobre qué se calcula el 5 %? | «Supongo que por la renta.» | WhatsApp (Sofia) | reemplazado por ENT-63 |
| ENT-33 | ¿Estados del equipo: disponible, prestado, en revisión, en reparación y baja? | «Me parece suficiente.» | WhatsApp (Sofia) | confirmado, salvo «prestado»: ver ENT-61 |
| ENT-34 | ¿Cada cambio de estado exige un motivo? | «Es bueno incluir un comentario; puede ser opcional.» | WhatsApp (Sofia) | confirmado |
| ENT-35 | ¿Qué se muestra en el MVP del 19/10? | Interfaz mínima con varios casos de uso; casos frontera de la devolución (disponible, reparación o baja); mostrar qué se activa en el middleware y el backend; unos 40 s por caso; CI/CD. | WhatsApp 14/10 | confirmado |
| ENT-36 | Si el pedido choca con una renta futura, ¿qué responde el sistema? | «El equipo está disponible hasta el primero de noviembre», para que el cliente pueda ajustar su fecha. | Audio 15/10 | confirmado (ver ENT-64) |
| ENT-37 | ¿Qué recibe el segundo cliente que confirma a la vez? | «En el momento en que se haga la primera reserva, al segundo ya le tiene que rebotar inmediatamente.» | Audio 15/10 | confirmado |
| ENT-38 | ¿Tolerancia de la devolución? | «Media hora. Un periodo de gracia.» | Audio 15/10 | reemplazado por ENT-63 |
| ENT-39 | ¿Penalidad por no recoger? | Penalidad parametrizada de 10 % o 15 %. | Audio 15/10 | reemplazado por ENT-58 |
| ENT-40 | ¿El administrador también cambia el estado de un equipo? | Sí: puede ponerlo en reparación o de baja. | Audio 15/10 | confirmado |
| ENT-41 | ¿Cuánto detalle en los mensajes de rechazo? | «No nos compliquemos con tantas excepciones por ahora.» | Audio 15/10 | confirmado |
| ENT-42 | ¿Debe verse en todos los dispositivos? | «Que esté disponible para todos los dispositivos sin problemas.» | Audio 15/10 | confirmado |
| ENT-43 | ¿Qué momentos guarda una renta? | Cuatro: cuándo puede recoger, cuándo recoge de verdad, cuándo debe devolver y cuándo devuelve de verdad. | Audio 15/10 | confirmado |
| ENT-44 | ¿Administrador y superusuario son roles distintos? | «Yo diría que el administrador sea equivalente al superusuario.» | Audio 15/10 | confirmado |
| ENT-45 | ¿Cada mesa y silla se registra aparte, la renta aparta solo sus fechas y gana el primero? | «Sí. First come first served.» | WhatsApp 15/10 | confirmado |
| ENT-46 | ¿El catálogo muestra solo lo disponible? | «Lo menos problemático es solo mostrar lo disponible.» | WhatsApp 15/10 | reemplazado por ENT-64 |
| ENT-47 | Si el equipo se rompe antes de una renta futura, ¿qué pasa? | «Tu sistema es optimista porque quieres hacer plata.» El administrador devuelve el dinero al cliente afectado; es su trabajo. | WhatsApp 15/10 | confirmado |
| ENT-48 | ¿Cómo se simula el pago? | Un QR: una lectura cobrada y otra rechazada. Un middleware que maneje pago exitoso o fallido («Bool. True false»), para poder cambiar a una pasarela sin tocar la renta. | WhatsApp 15/10 | confirmado; se hace con ENT-66 |
| ENT-49 | ¿Mantenimiento elige disponible, reparación o baja? ¿Reparación vuelve a disponible? ¿Baja es definitiva? | Sí a las tres. | WhatsApp 15/10 | confirmado |
| ENT-50 | ¿Se usa el admin de Django como interfaz del administrador? | «Me encanta. Pero en lo posible traten de personalizarlo»: su logo y sus casos de uso claros. | WhatsApp 15/10 | confirmado |
| ENT-51 | Si las fechas chocan, ¿el sistema dice desde cuándo no está disponible? | «Debería decirlo. […] El mismo sistema consulta y devuelve.» | WhatsApp 15/10 | confirmado |
| ENT-52 | ¿Las horas de recojo y devolución son fijas? | «No son fijas. Es hasta. O desde.» | WhatsApp 15/10 | confirmado |
| ENT-53 | ¿Cuáles son los roles? | «Quedamos en 4: cliente, operador, mantenimiento y admin (o superusuario)». El operador renta a nombre de un cliente; mantenimiento revisa lo que vuelve. «Todo correcto». | WhatsApp 17/10 | confirmado |
| ENT-54 | ¿Qué hace el operador y cómo encuentra al cliente? | «Operador solo es tienda»: recibe equipo, entrega equipo y valida reservas. Busca al cliente por nombre, apellido, id o correo. Si el cliente no tiene cuenta, el operador puede registrarla. | WhatsApp 17/10 | confirmado |
| ENT-55 | ¿Qué ve cada rol? | Admin: todo. Operador: qué reservas hay y qué se debe devolver; puede hacer, deshacer o modificar reservas. Cliente: qué equipos hay disponibles y qué ha reservado. | WhatsApp 17/10 | confirmado |
| ENT-56 | ¿El operador registra que el cliente recogió el equipo? | «Se registra porque tiene q estar todo inventariado.» | WhatsApp 17/10 | confirmado |
| ENT-57 | ¿Cuándo una renta pasa a «rentada»? | Primero está «reservada» y pasa a «rentada» al recoger. Si la hace el operador en la tienda, puede pasar directo a «rentada». | WhatsApp 17/10 | confirmado; «directo a rentada», reemplazado por ENT-91 |
| ENT-58 | ¿Cómo se paga y qué pasa si no recoge? | Pago completo por adelantado, con la garantía incluida. «La multa es por devolución tardía. Mejor q sea plata a bloquear cliente.» | WhatsApp 17/10 | confirmado; precisado en ENT-77 |
| ENT-59 | ¿Hasta cuándo se espera el recojo? | «Si el equipo no es recogido hasta las doce del día queda disponible para ser rentado por otros.» El sistema lo detecta por la hora y lo cambia a las 12:01. | WhatsApp 17/10 | reemplazado por ENT-69 |
| ENT-60 | ¿Se puede devolver una renta que nunca se recogió? | «El sistema te deja. Ahí entra el humano para ver quién hizo fraude.» | WhatsApp 17/10 | reemplazado por ENT-93 |
| ENT-61 | ¿Importa el estado «rentado» del equipo? | «Su estado por defecto es disponible y es por las fechas q su estado va cambiar a reservado o rentado. Un equipo puede estar rentado para todo nov y dic, pero sigue apareciendo disponible para octubre.» | WhatsApp 17/10 | confirmado |
| ENT-62 | ¿Cuándo se paga y el QR va el lunes? | Se paga al hacer la renta, en línea o en la tienda. El QR no es para el lunes. Si el pago falla, la renta se libera. | WhatsApp 17/10 | confirmado (pago al rentar); el pago fallido, reemplazado por ENT-67 |
| ENT-63 | ¿Cómo se clasifica la devolución? | «Se hace hasta las 9 am y hay multas si lo devuelve hasta las 12 del medio día; si lo devuelve después, paga un día de renta más aunque sean las 12:01.» | WhatsApp 17/10 | reemplazado por ENT-73 |
| ENT-64 | ¿El equipo con una renta futura aparece en el catálogo? | Debe decir que «no está disponible del 1 al 5». Propuesta del equipo: avisarlo y dejar rentarlo para antes o después, bajo riesgo de la tienda. Respuesta: «Me parece sexi.» | WhatsApp 17/10 | reemplazado por ENT-99 |
| ENT-65 | ¿La hora límite de devolución la elige el cliente? | «Siempre desde las 9 am. La tienda abre a las 6, 7 u 8 y ellos tienen q devolver el equipo hasta las 9 sin multas.» | WhatsApp 17/10 | confirmado |
| ENT-66 | ¿Cómo se paga en línea? | Cliente: se paga completo al reservar; el pago falla o no falla, sin validación real. · Equipo: una pantalla de QR simulado con dos botones, «Simular pago exitoso» y «Simular pago fallido». | Charla 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-67 | ¿Qué pasa si el pago QR falla? | Cliente: la reserva queda hecha aunque el pago falle. · Equipo: queda con el pago pendiente y el cliente ve «Tu reserva está hecha, pero el pago no se completó. Paga en la tienda al recoger el equipo». | WhatsApp 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-68 | ¿Se entrega una reserva sin pagar? | Cliente: al recoger, si debe, paga y se lleva el equipo; si no paga, el equipo vuelve a estar disponible. · Equipo: el operador cobra en efectivo y entrega; si el cliente no paga, se registra como cancelación de la renta y las fechas quedan libres. | WhatsApp 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-69 | ¿Hasta cuándo se espera el recojo? | Cliente: si nunca lo recoge, a la medianoche queda disponible. · Equipo: la reserva pasa sola a «No recogida» a la medianoche de su día de inicio, también si estaba pagada. | WhatsApp 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-70 | ¿Cómo se paga en la tienda? | Equipo: en efectivo, al registrar la renta. | Equipo | decisión del equipo |
| ENT-71 | ¿Cuánto cuesta un día de renta? | Equipo: el 5 % del valor del equipo. Se fija al crear la renta y no cambia si después cambia el valor. | Equipo | decisión del equipo |
| ENT-72 | ¿Cómo se cuentan los días? | Equipo: son los días entre la fecha de recojo y la de devolución: recojo a las 18:00 del día D y devolución a las 09:00 del día D+n son n días, máximo 5. Total = días × precio diario. | Equipo | decisión del equipo |
| ENT-73 | ¿Qué se cobra por devolver tarde? | Cliente: hay tolerancia hasta las 12:00; después se cobra un día extra. · Equipo: hasta las 09:00 del día de vencimiento es a tiempo; de 09:00 a 12:00, tolerancia sin cobro; desde las 12:01, una deuda de días de atraso × precio diario. Los días de atraso son los mediodías vencidos desde el día de vencimiento. | Charla 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-74 | ¿Qué se cobra por un equipo dañado? | Cliente: si se da de baja, se cobra el valor total del equipo, y se rastrea al último cliente que lo rentó. · Equipo: si mantenimiento lo manda a reparación, el 20 % del valor; la baja cancela sus reservas futuras con aviso por correo; lo paga el cliente de la última renta devuelta; las deudas por daño de una renta no pasan del valor del equipo, así que una baja después de una reparación cobra el 80 % (D-06). | Charla 27/10 | confirmado (cliente) · decisión del equipo (equipo); el cobro automático y la cancelación solo por baja, reemplazados por ENT-88 y ENT-90 |
| ENT-75 | ¿Las correcciones del admin crean deudas? | Equipo: no. | Equipo | decisión del equipo |
| ENT-76 | ¿Cómo se guardan y pagan las deudas? | Cliente: la deuda se registra («no me pagó»); el sistema no cobra. · Equipo: cada deuda es de una renta y un motivo, sin repetirse; se paga una por una y el operador registra el pago y quién lo recibió. | Charla 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-77 | ¿El cliente con deuda puede rentar? | Cliente: con deuda no puede rentar y se le avisa que tiene deuda. · Equipo: vale en línea y en tienda, con el mensaje «Tienes una deuda pendiente de X Bs. Págala en la tienda para volver a rentar». Sí puede devolver los equipos que tenga. | Charla 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-78 | ¿Qué pasa si el cliente no paga su deuda? | Cliente: el sistema no cobra a la fuerza: la deuda queda registrada. No hay reporte de pérdidas. | Charla 27/10 | confirmado |
| ENT-79 | ¿Se puede bloquear a un usuario? | Cliente: sí, aunque podría crear otra cuenta. · Equipo: solo el admin, desmarcando «Activo»; el usuario ya no puede iniciar sesión y, si escribe su contraseña correcta, ve «Tu cuenta está desactivada. Comunícate con la tienda.»; la tienda ya no lo encuentra para rentarle. | Charla 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-80 | ¿Quién cancela o modifica una reserva y hasta cuándo? | Cliente: el cliente puede cambiar o cancelar con 24 h de anticipación (ENT-24); el operador puede hacer, deshacer o modificar reservas (ENT-55). · Equipo: solo una renta «Reservada»; fuera de plazo el cliente ve «Ya no puedes cancelar en línea; comunícate con la tienda»; el operador y el admin, en cualquier momento antes del recojo. | WhatsApp (ENT-24, ENT-55) | confirmado (cliente) · decisión del equipo (equipo); modificar por el personal, reemplazado por ENT-95 |
| ENT-81 | ¿Qué es modificar? | Equipo: cambiar las fechas del mismo equipo con la misma cantidad de días; el precio no cambia. Para más días, se cancela y se renta de nuevo. | Equipo | decisión del equipo |
| ENT-82 | ¿Cómo se devuelve el dinero de una cancelación? | Equipo: fuera del sistema. | Equipo | decisión del equipo; confirmado en ENT-89 |
| ENT-83 | ¿Cómo se registra un equipo? | Cliente: solo el admin, a mano; el formato del código lo define el equipo; se guarda el valor total del equipo. · Equipo: código `AAA-00000` único (3 letras, guion, 5 números), número de serie único y nombre. Sin lector de código de barras ni importación masiva (ENT-14). | Charla 27/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-84 | ¿Cómo se registra un cliente? | Equipo (sale de PRE-01): en la web o en la tienda con los mismos datos: nombre, apellido, correo, teléfono, usuario y contraseña. Correo y teléfono no se repiten. Sin PIN ni SMS. Recibe un correo de bienvenida. | Equipo | decisión del equipo; la contraseña en la tienda, reemplazada por ENT-102 |
| ENT-85 | ¿Qué correos recibe el cliente? | Equipo: bienvenida, renta confirmada (pagada o con pago pendiente), renta cancelada con el motivo y deuda creada. | Equipo | decisión del equipo; en la tienda, «Crea tu contraseña» en lugar de la bienvenida (ENT-102) |
| ENT-86 | ¿Cómo se busca en el catálogo de 1000 equipos? | Equipo (sale de PRE-02): por páginas, buscando por código o nombre y mostrando solo los libres entre dos fechas; el personal también filtra por estado. | Equipo | decisión del equipo |
| ENT-87 | ¿Qué ve el responsable? | Equipo (sale de PRE-06 y PRE-08): una página con rentas activas, vencidas, reservas de hoy, pagos pendientes, equipos en revisión o reparación y deudas pendientes. | Equipo | decisión del equipo |
| ENT-88 | ¿Qué pasa con las reservas de un equipo que va a reparación o se da de baja? | Cliente: sus reservas futuras se cancelan automáticamente. · Equipo: vale para mantenimiento y para el admin; cada cliente recibe un correo con el motivo y el log escribe una línea por cancelación. | WhatsApp 28/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-89 | ¿Qué pasa con el dinero de una renta pagada que se cancela? | Cliente: el sistema solo cancela; la devolución del dinero es manual. | WhatsApp 28/10 | confirmado |
| ENT-90 | ¿Qué equipos revisa mantenimiento y quién decide el cobro del daño? | Cliente: puede cambiar el estado de **cualquier** equipo y **decide si cobra** la deuda o no. · Equipo: la casilla «Cobrar el daño al último cliente» solo aparece si el equipo tiene una renta devuelta y el estado nuevo es reparación o baja; viene sin marcar. | WhatsApp 28/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-91 | ¿Se mantiene «Se lo lleva ahora» en la renta en tienda? | Cliente: se elimina. · Equipo: en tienda la renta nace «Reservada» y se entrega con «Registrar recojo». | WhatsApp 28/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-92 | ¿Dónde se paga una deuda? | Cliente: solo en la tienda, en persona. | WhatsApp 28/10 | confirmado |
| ENT-93 | ¿Qué rentas se pueden devolver? | Cliente: solo una renta **Rentada**. | WhatsApp 28/10 | confirmado |
| ENT-94 | ¿Se puede elegir una fecha pasada? | Cliente: no se puede elegir una fecha anterior. · Equipo: el recojo de hoy a las 18:00 vale hasta la medianoche, porque el cliente puede recogerlo hasta entonces. | WhatsApp 28/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-95 | ¿Quién modifica una reserva y hasta cuándo? | Cliente: el cliente hasta 24 h antes; el operador o el admin en cualquier momento **antes de que empiece**. · Equipo: el límite de cantidad de cambios queda para la siguiente iteración. | WhatsApp 28/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-96 | ¿Qué es un combo? | Cliente: un combo es un equipo más (por ejemplo, «Combo 6 sillas y 1 mesa»); sin carritos. · Equipo: el precio sale de su valor como cualquier equipo. | WhatsApp 28/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-97 | ¿Se borran datos del sistema? | Cliente: **nunca se borra nada del historial**. | WhatsApp 28/10 | confirmado |
| ENT-98 | ¿Qué pasa con un cliente desactivado? | Cliente: sin respuesta. · Equipo: nunca se borra; al desactivarlo se cancelan sus reservas todavía no recogidas y las rentas que tiene en la mano siguen hasta que las devuelva; si se reactiva, vuelve a rentar (D-27). | WhatsApp 28/10 | decisión del equipo |
| ENT-99 | ¿El catálogo dice cuándo está ocupado cada equipo? | Cliente: a quien renta no le interesa cuándo usan el equipo otras personas; se quitan las etiquetas «Libre» y «Ocupado del … al …». · Equipo: sin fechas se ven los equipos disponibles; con las dos fechas, solo los libres en ese periodo. El mensaje al rentar fechas que chocan («El equipo X está ocupado del … al …») se queda. | Revisión del sistema 29/10 | confirmado (cliente) · decisión del equipo (equipo); reemplaza a ENT-64 |
| ENT-100 | ¿En qué orden se ven las listas? | Cliente: «Tiene que haber un filtrado por defecto de la última acción. Lo último es lo primero que veo». · Equipo: el admin, las páginas del personal y la API van del más nuevo al más viejo; el admin tiene `date_hierarchy` y filtro por fecha; «Reservas por entregar» y «Devoluciones» también se ordenan por fecha de recojo o de devolución, que sirve para atender en la tienda. | Revisión del sistema 29/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-101 | ¿Qué dice cada línea del log? | Cliente: cada línea dice todo lo necesario a la vista, sin buscar en la base qué es «rental=60». · Equipo: la renta, el equipo y el cliente con sus nombres, el periodo, el monto y quién actuó; los rechazos llevan lo que se intentó; nunca contraseñas. | Revisión del sistema 29/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-102 | ¿El operador conoce la contraseña del cliente? | Cliente: el operador no debe conocer la contraseña del cliente. · Equipo: en la tienda la cuenta nace sin contraseña y el cliente recibe el correo «Crea tu contraseña» con el enlace de Django; si el correo falla, el operador le pide usar «Olvidé mi contraseña». El registro web sigue igual. | Revisión del sistema 29/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-103 | ¿El cliente puede cambiar su contraseña? | Cliente: el cliente cambia su contraseña. · Equipo: «Mi cuenta» con «Cambiar contraseña» (pide la actual y usa los validadores del registro), editar nombre, apellido, correo y teléfono con las reglas del registro y «Olvidé mi contraseña» por correo. El usuario y el rol no cambian. | Revisión del sistema 29/10 | confirmado (cliente) · decisión del equipo (equipo) |
| ENT-104 | ¿Qué dice la etiqueta del pago? | Cliente: la etiqueta dice «Pagado». · Equipo: solo «Pagado» o «Pago pendiente» en las páginas, el admin y la API; la forma de pago (QR o efectivo) sigue guardada y se ve en el detalle de la renta y en el admin. | Revisión del sistema 29/10 | confirmado (cliente) · decisión del equipo (equipo) |
