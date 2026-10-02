# Sesión 6 — Hallazgos y requisitos del proyecto

- Proyecto: astra-rent-system — SergioCorp, renta de equipos para eventos (encargo P01, Gestión de préstamos de equipos)
- Integrantes: Sofia Arduz Rengel, Andres Laura Vargas, Peter Uriel Terán Bedregal
- Fecha: 01/10/2026
- Cliente o fuente consultada: Sergio Barrientos (docente en el rol de cliente) — entrevista oral en clase, entrevista por WhatsApp (preguntas de Uriel y de Sofía) y encargo inicial `01_Prestamos_Equipos.md`
- Flujo seleccionado: renta y devolución de un equipo — el cliente renta en línea o con un operador, recoge el equipo, lo devuelve y mantenimiento lo revisa antes de que vuelva a rentarse

**Término único:** el cliente confirmó que "reserva", "préstamo", "renta" y "booking" son lo mismo (ENT-06). En este documento usamos siempre **renta**. Los identificadores del encargo (PRE-01 a PRE-08) conservan su nombre original.

**Nota sobre la entrevista:** el docente no alcanzó a entrevistar a todos los grupos en clase y pidió hacerla por WhatsApp. Las filas con fuente "Clase" vienen de la conversación oral del 01/10; las demás, de los chats escritos del mismo día.

## 1. Hallazgos de la entrevista

| ID | Pregunta | Respuesta o hallazgo | Fuente | Estado |
|---|---|---|---|---|
| ENT-01 | ¿Página web o aplicación? | Página web que se vea en celular, pantalla y tablet. | Clase | confirmado |
| ENT-02 | ¿Qué volumen debe soportar el sistema? | Unos 1000 equipos; en el mejor momento, 70 % rentado. El equipo debe calcular la concurrencia necesaria y comprobarla enviando muchas peticiones a la vez. | Clase | confirmado (volumen); pendiente (significado del 70 %, ver ENT-27) |
| ENT-03 | ¿Qué pasa con un equipo cuando vuelve? | No vuelve directo a rentarse. Mantenimiento lo revisa y lo pasa a disponible, a reparación o a "basura" (baja). | Clase | confirmado |
| ENT-04 | ¿Qué pasa si no se devuelve a tiempo? | Multa del 5 % por cada hora de retraso después de las 9:00, debitada de la tarjeta de crédito. La tarjeta puede simularse (crédito ilimitado o pago siempre válido). | Clase | pendiente (el encargo excluye multas y pagos; base de cálculo en ENT-32) |
| ENT-05 | ¿Cómo es una renta típica, de principio a fin? | Hay un catálogo para ver equipos o combos. Se puede rentar en línea o en persona con un operador. | WhatsApp (Uriel) | confirmado |
| ENT-06 | ¿"Reserva", "préstamo", "renta" y "booking" son lo mismo? | "Es lo mismo". El equipo fija la palabra **renta**. | WhatsApp (Uriel) | confirmado |
| ENT-07 | ¿Qué significa que cualquier empresa podía poner sus productos? | "Con que sea mesas y sillas basta. Para eventos." Es una sola empresa. | WhatsApp (Uriel) | confirmado (una empresa); pendiente (si el catálogo incluye también amplificación) |
| ENT-08 | ¿Qué es un combo? | Equipos sueltos que se rentan juntos. Ejemplo: juego de 6 mesas y 36 sillas. | WhatsApp (Uriel) | confirmado |
| ENT-09 | ¿Se registra cada silla o solo la cantidad? | Cada equipo se registra individualmente en el inventario. | WhatsApp (Uriel) | confirmado |
| ENT-10 | Si alguien renta hoy para dentro de unos días, ¿el equipo queda apartado? | Sí, queda reservado para ese periodo. Si otra persona lo quiere antes (por ejemplo, de mañana al sábado), "en teoría debería poder" y el sistema debe manejar ese caso. El sistema debe alertar si por una renta futura "estamos perdiendo plata". | WhatsApp (Uriel) | confirmado (comportamiento); pendiente (cuándo alertar y confirmación de alcance, ver ENT-26) |
| ENT-11 | ¿Hay información que un rol no deba ver? | "Todavía no. Lo dejo por ahora a sentido común"; se define en la siguiente iteración. | WhatsApp (Uriel) | pendiente |
| ENT-12 | ¿Qué puede hacer el cliente por su cuenta? | Puede rentar equipos desde la web. Los casos de uso los redacta el equipo de forma genérica y el cliente decide si le gusta el flujo. | WhatsApp (Uriel) | confirmado; casos de uso pendientes de revisión |
| ENT-13 | ¿El responsable del servicio y el superusuario son la misma persona? ¿Qué puede hacer? | En esta etapa son lo mismo. "Si es super user puede hacer todo", no solo consultar (corregir registros, dar de baja equipos, rechazar clientes). | WhatsApp (Uriel) | confirmado |
| ENT-14 | ¿Quién registra un equipo nuevo? | El administrador. Una importación masiva (tipo BOQ) "puede mega esperar"; el formato lo decide el equipo. | WhatsApp (Uriel) | confirmado (quién); pendiente (importación y formato) |
| ENT-15 | ¿El cliente nuevo se registra solo o lo registra un operador? | "Puede ser los dos." | WhatsApp (Uriel) | confirmado |
| ENT-16 | ¿Una renta en línea se confirma al instante o requiere aprobación? | Al instante, "como add to cart". | WhatsApp (Uriel) | confirmado |
| ENT-17 | ¿Cuál es la anticipación mínima y máxima para rentar? | "No hay límite con la anticipación. Puede ser al instante." Si hay disponibilidad, se renta. Reemplaza lo dicho en clase ("no un mes antes"). | WhatsApp (Uriel) | confirmado |
| ENT-18 | ¿Cuánto dura una renta? | 5 días por defecto; 2 semanas para clientes frecuentes. (Respondido en la pregunta de anticipación y confirmado en la reformulación.) | WhatsApp (Uriel) | confirmado |
| ENT-19 | ¿Cómo se combinan duración y horarios? | "No hay combinación." Se entrega desde las 18:00 y se devuelve hasta las 9:00 o antes, nunca después. | WhatsApp (Uriel) | confirmado |
| ENT-20 | ¿Qué hace "frecuente" a un cliente y quién lo decide? | "No lo sé todavía. Mostrame el caso de uso." | WhatsApp (Uriel) | pendiente |
| ENT-21 | Si dos clientes quieren el último equipo con un minuto de diferencia, ¿quién se lo queda? | "Se lo queda el primero que le dio click." Qué ve el otro cliente: sin respuesta. | Clase y WhatsApp (Uriel) | confirmado (regla); pendiente (mensaje) |
| ENT-22 | ¿Hasta cuándo se puede recoger el equipo? | Si está disponible desde las 18:00, pueden recogerlo "hasta las 20 de ese día o las 12 del siguiente". | WhatsApp (Uriel) | pendiente (no queda claro cuál de los dos límites) |
| ENT-23 | ¿Qué pasa con la renta si nadie recoge el equipo? | "Los multas si deseas o rentas el equipo a otro." Lo deja a elección del equipo. | WhatsApp (Uriel) | pendiente (decisión a elección del equipo) |
| ENT-24 | ¿El cliente puede cambiar o cancelar una renta? | Sí, con 24 horas de anticipación. Si cancela o cambia después, multa con "porcentaje a elección". | WhatsApp (Uriel) | confirmado (regla de 24 h); pendiente (porcentaje y desde qué hora se cuentan las 24 h) |
| ENT-25 | ¿Qué debe pasar para que el sistema no deje rentar más a un cliente? | Que no haya recogido el equipo de una renta anterior. Al repreguntar si quería decir "devuelto", repitió: "en caso de que no haya recogido", y agregó "o se está burlando con bots". | WhatsApp (Uriel) | confirmado (no recoger); pendiente (cómo detectar bots y cuánto dura el bloqueo) |
| ENT-26 | Las rentas con anticipación y las multas, ¿entran aunque el encargo las deja fuera? | Sin respuesta explícita. Sí siguió describiendo rentas futuras y multas. | WhatsApp (Uriel) | pendiente |
| ENT-27 | ¿El 70 % es un tope o una estimación? | Sin respuesta. | WhatsApp (Uriel) | pendiente |
| ENT-28 | ¿Qué necesita ver el responsable y qué ve el cliente sobre su renta? | Sin respuesta. | WhatsApp (Uriel) | pendiente |
| ENT-29 | En el momento de más movimiento, ¿qué demora sería inaceptable? | Sin respuesta. | WhatsApp (Uriel) | pendiente |
| ENT-30 | ¿Qué es imprescindible para la próxima entrega y qué puede esperar? | Sin respuesta. | WhatsApp (Uriel) | pendiente |
| ENT-31 | Si la devolución vence a las 9:00, ¿una devolución a las 9:00:00 exactas está a tiempo? ¿Hay tolerancia? | "Tolerancia 5 min." | WhatsApp (Sofía) | confirmado |
| ENT-32 | El 5 % por hora de retraso, ¿se calcula sobre el depósito, el valor del equipo o la tarifa? | "No lo sé. Supongo que por la renta. Sino mucha plata." | WhatsApp (Sofía) | pendiente (respuesta tentativa del cliente) |
| ENT-33 | ¿Los estados del equipo son disponible, prestado, en revisión, en reparación y baja? | "Me parece suficiente." En este documento, "prestado" se escribe **rentado**. | WhatsApp (Sofía) | confirmado |
| ENT-34 | ¿Cada cambio de estado exige un motivo? | Es bueno incluir un comentario o razón; puede ser opcional. | WhatsApp (Sofía) | confirmado |

## 2. Alcance del flujo

- Incluye: rentar un equipo o un combo en línea o con un operador, con confirmación al instante (ENT-05, ENT-08, ENT-16); verificar que el equipo esté libre en el periodo pedido y que el primero en confirmar se quede con él (ENT-10, ENT-21); rechazar la renta de un cliente con una renta anterior no recogida (ENT-25); entregar desde las 18:00 (ENT-19); registrar la devolución hasta las 9:00, con 5 minutos de tolerancia (ENT-19, ENT-31); pasar el equipo devuelto a "en revisión" y que mantenimiento lo cambie a disponible, en reparación o baja, con un comentario opcional (ENT-03, ENT-33, ENT-34).
- No incluye: cobros reales ni facturación (el encargo los excluye; la tarjeta se simularía según ENT-04); el cálculo y cobro de multas mientras no se confirme su alcance (ENT-26, ENT-32); la importación masiva de inventario (ENT-14, "puede mega esperar"); las reglas de quién ve qué información (ENT-11, siguiente iteración); el criterio de cliente frecuente (ENT-20); las alertas por pérdida de dinero (ENT-10); sensores, compra de equipos e integraciones externas (exclusiones del encargo).

## 3. Requisitos

### PRE-RF-01 — El primero en confirmar se queda el equipo

- Tipo: funcional
- Origen: PRE-03 y PRE-04 del encargo; ENT-16 y ENT-21 (pregunta propia del equipo, a partir del caso que el cliente pidió demostrar en clase). Adapta el ejemplo de la guía "PRE-RF-01 — Equipo ya prestado" a periodos de fechas.
- Prioridad y razón: alta — es la necesidad central del encargo ("evitar que un equipo se preste dos veces") y el cliente pidió explícitamente una prueba de este caso.
- Estado: aprobado por el cliente (la regla "primero en dar clic"); el texto del mensaje al segundo cliente está propuesto (PRE-RC-01).
- Requisito: si dos clientes confirman la renta del mismo equipo para periodos que se superponen, el sistema debe registrar solo la renta confirmada primero y rechazar la segunda, sin modificar la renta ya registrada.
- Criterio de aceptación o comprobación:
  - Situación inicial: el equipo EQ-01 está disponible del 09/10/2026 18:00 al 12/10/2026 09:00 y no tiene otra renta en ese periodo.
  - Acción: el cliente C-01 confirma la renta de EQ-01 para ese periodo a las 19:51:00; el cliente C-02 confirma la renta de EQ-01 para el mismo periodo a las 19:52:00.
  - Resultado esperado: la renta de C-01 queda confirmada; la de C-02 se rechaza con un mensaje que indica que EQ-01 ya no está disponible en esas fechas. Existe una sola renta de EQ-01 en ese periodo, asociada a C-01, y no se registra ninguna renta para C-02.

### PRE-RF-02 — Devolución hasta las 9:00 con tolerancia de 5 minutos

- Tipo: funcional
- Origen: PRE-05 y PRE-06 del encargo; ENT-19 y ENT-31 (pregunta propia del equipo, hecha por Sofía).
- Prioridad y razón: alta — define cuándo una renta está vencida (PRE-06) y es la base de cualquier multa por atraso.
- Estado: aprobado por el cliente; el instante exacto del límite (09:05:00) y desde cuándo se cuenta el retraso quedan pendientes de aclaración.
- Requisito: al registrar la devolución de una renta, el sistema debe clasificarla como "a tiempo" si la hora registrada no supera los 5 minutos de tolerancia sobre las 9:00 del día de vencimiento, y como "con retraso" en caso contrario. En ambos casos se conserva la fecha y hora registradas.
- Criterio de aceptación o comprobación:
  - Situación inicial: la renta R-01 vence el 12/10/2026 a las 09:00; la renta R-02 vence el mismo día a la misma hora.
  - Acción: el operador registra la devolución de R-01 a las 09:04 y la de R-02 a las 09:20.
  - Resultado esperado: R-01 queda "a tiempo" y R-02 "con retraso"; ambas guardan la hora registrada (09:04 y 09:20). No cambia ninguna otra renta.

### PRE-RF-03 — Rechazo por una renta anterior no recogida

- Tipo: funcional
- Origen: PRE-04 del encargo ("condiciones del solicitante"); ENT-25 (pregunta propia del equipo, con repregunta).
- Prioridad y razón: media — protege la disponibilidad de equipos, pero depende de definir hasta cuándo se puede recoger (ENT-22, pendiente).
- Estado: aprobado por el cliente (bloquear al cliente que no recogió); el límite de recojo y la duración del bloqueo quedan pendientes de aclaración.
- Requisito: si un cliente tiene una renta anterior cuyo equipo no recogió dentro del plazo de recojo, el sistema debe rechazar una nueva renta de ese cliente indicando el motivo, sin crear la renta nueva ni modificar sus rentas existentes.
- Criterio de aceptación o comprobación:
  - Situación inicial: el cliente C-03 tiene la renta R-05, cuyo plazo de recojo ya venció (límite pendiente, ENT-22) sin que recogiera el equipo; el equipo EQ-02 está disponible.
  - Acción: C-03 intenta rentar EQ-02.
  - Resultado esperado: el sistema rechaza la renta e informa que C-03 tiene una renta anterior sin recoger (R-05). No se crea una renta para EQ-02, que sigue disponible, y R-05 no cambia.

### PRE-RF-04 — El equipo devuelto pasa a revisión

- Tipo: funcional
- Origen: PRE-05 y PRE-06 del encargo; ENT-03 (clase), ENT-33 y ENT-34 (preguntas propias del equipo, hechas por Sofía).
- Prioridad y razón: alta — es la necesidad del responsable de mantenimiento ("identificar equipos que no deben volver a circular") e impide rentar un equipo dañado.
- Estado: aprobado por el cliente.
- Requisito: al registrar una devolución, el equipo debe pasar a "en revisión" y no podrá rentarse hasta que mantenimiento lo cambie a "disponible". Mantenimiento también puede cambiarlo a "en reparación" o "baja". Cada cambio de estado guarda quién lo hizo, cuándo y un comentario opcional.
- Criterio de aceptación o comprobación:
  - Situación inicial: el equipo EQ-03 está "rentado" en la renta R-03.
  - Acción: el operador registra la devolución de R-03 a las 08:40; un cliente intenta rentar EQ-03; después, mantenimiento cambia EQ-03 a "disponible" sin comentario.
  - Resultado esperado: tras la devolución, EQ-03 está "en revisión" y el intento de renta se rechaza. Tras el cambio de mantenimiento, EQ-03 está "disponible" y puede rentarse. El historial de EQ-03 conserva los dos cambios de estado, con autor y hora.

### PRE-RC-01 — Mensaje con la causa del rechazo

- Tipo: calidad
- Origen: PRE-04 del encargo ("Operador: mensajes claros") y condiciones comunes del curso ("un error debe producir un mensaje comprensible"). Adapta el ejemplo de calidad de la guía.
- Prioridad y razón: media — sin la causa, el operador o el cliente no saben si deben elegir otras fechas, otro equipo o resolver una renta pendiente.
- Estado: propuesto (el cliente no respondió qué debe ver quien no consigue el equipo, ENT-21).
- Requisito: cuando una renta se rechaza por una regla de negocio, el sistema debe mostrar la causa concreta del rechazo e identificar el equipo, el periodo o la renta involucrados.
- Criterio de aceptación o comprobación:
  - Situación inicial: los casos de rechazo de PRE-RF-01 y PRE-RF-03.
  - Acción: ejecutar cada caso de rechazo.
  - Resultado esperado: el mensaje de PRE-RF-01 indica que EQ-01 no está disponible del 09/10 al 12/10; el de PRE-RF-03 indica que C-03 tiene la renta R-05 sin recoger. Un mensaje genérico como "Error" no cumple el criterio.

### PRE-RT-01 — Aplicación web usable en celular, tablet y computadora

- Tipo: restricción
- Origen: ENT-01; condiciones comunes del encargo ("una interfaz sencilla acordada con el docente").
- Prioridad y razón: alta — determina la arquitectura y la tecnología de la interfaz.
- Estado: aprobado por el cliente.
- Requisito: el sistema debe usarse desde un navegador web en celular, tablet y computadora; no se desarrolla una aplicación nativa.
- Criterio de aceptación o comprobación:
  - Situación inicial: un incremento con el recorrido de renta implementado y publicado en un entorno de prueba.
  - Acción: completar el recorrido de renta desde un celular, una tablet y una computadora.
  - Resultado esperado: el recorrido se completa en los tres dispositivos usando solo el navegador. En esta sesión la restricción queda registrada; no se ha comprobado porque aún no existe la interfaz.

## 4. Escenarios del flujo

| Caso | Requisito relacionado | Datos y acción | Resultado esperado |
|---|---|---|---|
| Normal | PRE-RF-01 | EQ-01 está libre del 09/10 18:00 al 12/10 09:00; C-01 confirma esa renta en línea. | La renta queda confirmada al instante (ENT-16) y EQ-01 deja de aparecer disponible para ese periodo. |
| Límite | PRE-RF-02 | La renta vence el 12/10 a las 09:00; el operador registra la devolución a las 09:05:00 exactas. | Decisión pendiente: falta confirmar si 09:05:00 cuenta como "a tiempo". Sí está acordado que 09:04 es "a tiempo" y 09:20 es "con retraso". |
| Rechazo | PRE-RF-01 | C-01 confirmó EQ-01 para el 09/10–12/10 a las 19:51; C-02 confirma el mismo equipo y periodo a las 19:52. | Se rechaza con la causa (PRE-RC-01). Existe una sola renta, la de C-01, que no cambia; no se crea renta para C-02. |

Estos escenarios están especificados; ninguno fue ejecutado todavía. El código actual (PB-01, datos en memoria) prueba un caso parecido —rechazar un segundo préstamo activo del mismo equipo—, pero no trabaja con periodos de fechas ni con confirmaciones simultáneas.

## 5. Preguntas y decisiones pendientes

| Pregunta | A quién consultar | Impacto mientras no se resuelva |
|---|---|---|
| ¿Las rentas con anticipación y las multas entran en el proyecto, aunque el encargo las excluye? | Sergio (cliente) | Afecta el alcance completo. PRE-RF-01 trabaja con periodos y la regla de PB-01 ("un préstamo activo") deja de bastar. |
| ¿El recojo es hasta las 20:00 del mismo día o hasta las 12:00 del día siguiente? | Sergio (cliente) | PRE-RF-03 no puede decidir cuándo una renta queda "no recogida". |
| ¿Qué pasa con una renta no recogida: se multa o se libera el equipo para otro? (el cliente lo dejó a elección del equipo) | Equipo, con aprobación de Sergio | Queda pendiente la regla de liberación de equipos y el cálculo de multas. |
| ¿Una devolución registrada a las 09:05:00 exactas está a tiempo? ¿El retraso se cuenta desde las 9:00 o desde las 9:05? | Sergio (cliente) | El escenario límite de PRE-RF-02 y el cálculo del 5 % por hora. |
| ¿El 5 % por hora se calcula sobre el precio de la renta? (respuesta tentativa: "supongo que por la renta") | Sergio (cliente) | Cálculo de multa por atraso. |
| ¿Qué porcentaje de multa se aplica al cancelar o cambiar con menos de 24 horas? ¿Las 24 horas se cuentan desde el inicio de la renta (18:00)? (el porcentaje queda a elección del equipo) | Equipo, con aprobación de Sergio | Regla de cancelación y cambio. |
| ¿Qué hace "frecuente" a un cliente y quién lo decide? | Sergio, después de ver el caso de uso | La duración de 2 semanas no puede aplicarse. |
| ¿Qué ve el cliente que no consigue el último equipo? | Sergio (cliente) | El texto de PRE-RC-01 sigue propuesto. |
| ¿Cuándo debe alertar el sistema que se pierde dinero por una renta futura? | Sergio (cliente) | No se puede especificar la alerta (ENT-10). |
| ¿El 70 % es un tope o una estimación? | Sergio (cliente) | Si es un tope, agrega una regla de rechazo; si es una estimación, solo define la prueba de carga. |
| ¿Qué demora sería inaceptable, en qué operación (cargar el catálogo, confirmar una renta) y con cuántos usuarios a la vez? | Sergio (cliente) | No se puede escribir un requisito de rendimiento verificable; no se documentará "que sea rápido". |
| ¿Qué necesita ver el responsable al entrar y qué ve el cliente sobre su renta? | Sergio (cliente) | PRE-08 sin definir. |
| ¿Qué es imprescindible para la próxima entrega y qué puede esperar? | Sergio (cliente) | Orden del backlog sin confirmar por el cliente. |
| ¿Qué información no debe ver cada rol? | Sergio, en la siguiente iteración | Permisos por rol sin definir (ENT-11). |
| ¿El catálogo incluye amplificación además de mesas y sillas? | Sergio (cliente) | Tipos de equipo del catálogo y filtros (PRE-02). |
| ¿Cómo se detecta que un cliente "se burla con bots" y cuánto dura un bloqueo? | Sergio (cliente) | Alcance de PRE-RF-03. |
| ¿El sistema registra la compra de equipos o solo los equipos ya comprados? (el encargo excluye compras) | Sergio (cliente) | Alcance del registro de equipos (PRE-01). |
| Si un combo tiene un equipo no disponible, ¿se rechaza todo el combo o se renta lo disponible? | Sergio (cliente) | Regla de renta de combos (ENT-08). |
| En la clase se habló de un depósito al rentar, pero en la grabación no queda claro si lo propuso el cliente. ¿Hay depósito? | Sergio (cliente) | Alcance de pagos simulados. |

## 6. Revisión por otro equipo

- "Porfsvor omitan el paso de revisión de otro equipo en sus md"

## 7. Siguiente paso

- Tarea: implementar con pruebas la devolución y el paso a revisión en `rent_manager` (PB-05 del backlog), quitando el `skip` de la prueba de devoluciones que quedó pendiente en la iteración 1. En paralelo, redactar los casos de uso genéricos (renta en línea, renta con operador, devolución y revisión) para que el cliente los revise, como pidió en ENT-12.
- Requisito relacionado: PRE-RF-02 y PRE-RF-04
- Responsable inicial: Uriel
- Issue: no corresponde por ahora: el equipo todavía no usa issues; la tarea queda registrada en el backlog de `docs/requisitos.md`.

## 8. Participación y asistencia utilizada

- Aportes de cada integrante: Uriel — preguntas y repreguntas por WhatsApp (bloques de visión general, roles, renta, vistas y prioridad) y reformulación de respuestas; Sofía — preguntas sobre tolerancia de devolución, base de la multa, estados del equipo y motivo de cambio de estado, y rama `docs/sesion-06-requisitos-plan`; Andrew — propuesta inicial de roles y preguntas sobre atribuciones del superusuario frente al administrador y del operador frente al cliente.
- Asistencia de IA, si se utilizó: Claude (Anthropic) se usó para preparar y reformular las preguntas de la entrevista, detectar contradicciones con el encargo y redactar el borrador de este archivo a partir de los chats. 