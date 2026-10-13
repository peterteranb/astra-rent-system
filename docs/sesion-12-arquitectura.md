# Sesión 12 — Arquitectura y verificación del flujo

<!-- Copiar como docs/sesion-12-arquitectura.md en el repositorio del equipo.
Reemplazar los campos y conservar solo lo pertinente al flujo real.
Una tabla completada describe evidencia; una tabla vacía no acredita trabajo.
No presentar un workflow pendiente como una ejecución aprobada. -->

- Proyecto e integrantes: Sofia Arduz Rengel, Andres Laura Vargas, Peter Uriel Terán Bedregal.
- Fecha real de la actividad: 13/10/2026.
- Requisitos: [Sesión 6](sesion-06-requisitos.md).
- Modelos: [Sesión 7](sesion-07-modelos.md).
- Plan: [Sesiones 8–9](sesion-08-09-plan.md).
- Operación seleccionada: Renta de equipo.
- IDs vigentes y estado de aprobación: [requisitos y caso de uso].
- Tarea/issue que continúa: [ID y enlace].
- Retroalimentación que atiende, si existe: [observación y origen].

## 1. Punto de partida y alcance

- Qué ya funcionaba y con qué evidencia: [enlace/ruta y resultado].
- Problema o brecha que abordamos: [mezcla de responsabilidades, test incompleto, etc.].
- Incluimos hoy: [cambio pequeño y comportamiento].
- Queda pendiente: [integración, política por aclarar, etc.].
- Comando y resultado inicial real: [cantidad de aprobadas/fallidas; entorno; o no ejecutado y causa].

## 2. Responsabilidades y dependencias

| Grupo/componente | Responsabilidad | Código existente o propuesto | Usa qué interfaz de otro grupo |
|---|---|---|---|
| [Nombre] | [Propósito concreto] | [Archivo y función; estado] | [Interfaz/proveedor] |
| [Nombre] | [Propósito concreto] | [Archivo y función; estado] | [Interfaz/proveedor] |
| [Nombre] | [Propósito concreto] | [Archivo y función; estado] | [Interfaz/proveedor] |

- Cohesión: [qué propósito comparten las partes de un grupo].
- Acoplamiento: [qué detalle conoce otro grupo y qué cambio podría afectarlo].
- Mezcla encontrada o frontera que ya estaba separada: [ejemplo del código].

## 3. Interfaz seleccionada

- Proveedor y consumidor: [componentes].
- Operación y firma real o propuesta: [nombre y parámetros; indicar estado].
- Entradas: [datos, significado, unidades y supuestos].
- Resultado aceptado: [respuesta y efectos].
- Resultado de rechazo/repetición: [respuesta y efectos].
- Datos que deben conservarse: [alcance explícito del contrato].
- Consulta y escritura: [quién obtiene los datos; quién guarda y cuándo].
- Restricción de uso/importación para pruebas: [cómo se evita pedir teclado o depender de una conexión real en estas pruebas].

## 4. Vistas del mismo flujo

### Responsabilidades y dependencias

[Insertar un diagrama sencillo mediante Mermaid o imagen con fuente editable.]

- Las flechas significan: [quién depende de quién; no confundir con flujo de información].
- Lo ya implementado y lo propuesto se distinguen mediante: [leyenda].
- Pregunta que responde esta vista: [pregunta concreta].

### Ejecución: éxito y rechazo

- Modelo reutilizado: [enlace y sección de sesión 7].
- Recorrido de éxito en cuatro a seis pasos: [consulta, comprobaciones, cambios, escritura y respuesta].
- Recorrido de rechazo/repetición: [dónde se decide; respuesta y datos conservados].
- Cambio realizado al modelo anterior, si correspondió: [qué y por qué; o ninguno].

### Ubicación

| Componente/datos | Dónde se ejecuta o almacena hoy | Ubicación prevista, si cambia |
|---|---|---|
| [Elemento] | [Equipo/nodo o memoria; estado real] | [Propuesta o sin cambio] |
| [Elemento] | [Ubicación] | [Propuesta o sin cambio] |

- Dónde ejecuta las pruebas CI: [runner; no confundir con el servidor de la aplicación].

## 5. Decisión arquitectónica y calidad

- Objetivo y contexto: [problema y requisito/atributo].
- Observación que permitiría evaluar la mejora: [qué revisar o ejecutar; sin inventar medidas].

| Alternativa | Beneficio | Trabajo adicional o límite |
|---|---|---|
| A: [opción] | [beneficio concreto] | [compromiso] |
| B: [opción] | [beneficio concreto] | [compromiso] |

- Elección y razones: [opción y fundamento].
- Estado: [propuesta / implementada / parcialmente implementada].
- Qué nueva evidencia podría obligarnos a revisarla: [situación].

## 6. Cambio y trazabilidad de las pruebas

- Cambio real o frontera comprobada: [archivos, función, diff/PR].
- Cómo se conservan las reglas acordadas: [explicación].
- Si se corrigió un requisito/modelo: [confirmación del cliente y enlace; o no hubo cambio].

| Requisito | Ruta del caso de uso | Función/contrato | Test real y caso | Respuesta y estado esperados |
|---|---|---|---|---|
| [ID] | [Éxito] | [Función] | [Aceptación; datos] | [Resultado y cambios/conservación] |
| [ID] | [Rechazo/repetición] | [Función] | [Caso y datos] | [Resultado y conservación] |
| [ID] | [Límite] | [Función] | [Límite aprobado] | [Resultado y estado final] |

- Pruebas nuevas, reutilizadas o ampliadas: [cuáles y por qué].
- Comando y resultado final local real: [entorno; aprobadas/fallidas; error si lo hubo].
- Suite anterior: [comando y resultado real; o no ejecutada y causa].
- Alcance no comprobado: [por ejemplo, transacción real, reinicio o solicitudes simultáneas].

## 7. Evidencia de CI y versión

- Archivo de workflow: [enlace dentro del repositorio].
- Dependencias instaladas: [archivo y configuración necesaria].
- Comando que ejecuta: [comando real y carpeta/casos].
- Ejecución de Actions: [URL].
- Commit probado: [SHA de la ejecución].
- Estado real: [aprobado / fallido / en curso / no ejecutado y motivo].
- Resultado: [cantidad de aprobadas/fallidas o error de preparación].
- Reporte de pruebas: [enlace al artefacto, si existe].
- Candidato de código fuente: [nombre y ejecución aprobada en main; o todavía no generado y motivo].
- Commit del MD, si fue posterior: [SHA y diferencia; o coincide].
- Qué falta para una entrega o despliegue en el entorno destino: [instalación, configuración, datos y comprobaciones pendientes reales].

## 8. Plan actualizado y participación

- Tarea/issue y estado real: [enlace; no iniciada/en curso/bloqueada/terminada].
- Evidencia para ese estado: [cambio, pruebas y revisión; qué falta para el cierre].
- Dependencia o riesgo que cambió: [impacto; o sin cambio y razón].
- Siguiente acción, responsable y condición de revisión: [trabajo concreto].
- Aportes individuales: [código, tests, decisión, documentación y revisión].
- Asistencia de IA, si se utilizó: [herramienta, propósito, aporte, verificación y explicación propia].

## 9. Enlaces de entrega

- Este MD en GitHub: [URL directa].
- Pull request, si se utilizó: [URL; estado de revisión/integración].
- Hallazgo principal de la sesión: [qué cambió en nuestra comprensión del diseño y cómo afectará el desarrollo].
