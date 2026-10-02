# Sesión 7 — Historias, casos de uso y modelos

- Proyecto: SergioCorp
- Integrantes: Sofia Arduz Rengel, Andres Laura Vargas, Peter Uriel Terán Bedregal
- Fecha: 02/10/2026
- Requisitos de origen: docs/sesion-06-requisitos.md
- Flujo seleccionado: Renta de un equipo realizado por un cliente
- IDs seleccionados y estado de aprobación: [IDs y estado]

## 1. Historia [ID-HU-01]

Como [rol], quiero [objetivo] para [valor].
Como cliente, quiero ingresar al sistema con mis credenciales, elegir el equipo que quiero rentar yrecibir la confirmación de la venta para rentar un equipo. //mofidicar

- Requisitos relacionados: [IDs]

## 2. Caso de uso [ID-CU-01 — Nombre]

- Objetivo: Rentar un equipo  
- Actor principal: Cliente  
- Disparador: La página web  
  - Precondiciones: 
    El cliente ya tiene su usuario en el sistema, 
    el equipo existe en el inventario. 
    El estado del equipo es "disponible".
- Poscondición de éxito: Confirmación de la renta.
- Garantía ante rechazo: Se muestra como mensaje "no disponible".

### Flujo principal

1. [Acción del actor]
2. [Respuesta o comprobación del sistema]
3. [Continuar hasta el resultado observable]

### E1 — Ruta de rechazo o excepción

- Ocurre en el paso: [...]
- Condición: [...] que exista el equipo
- Respuesta del sistema: [...]
- Estado final y datos que se conservan: [...]
- El caso termina o continúa en: [...]

## 3. Modelo [ID-MOD-01]

- Tipo elegido: [actividad simplificada / secuencia]
- Pregunta que responde: [...]
- Alcance y aspectos que deja fuera: [...]

[Insertar el diagrama con su ruta principal y su ruta de rechazo.]

## 4. Estados o efectos sobre los datos
- Entidad que se está modelando: [...]

| Estado actual | Evento y condición | Estado siguiente | Efecto sobre los datos |
|---|---|---|---|
| [...] | [...] | [...] | [...] |
| [...] | [...] | [...] | [...] |

[Si no corresponde una tabla de estados, explicar por qué e indicar los cambios y la conservación de datos.]

## 5. Trazabilidad

| Requisito de sesión 6 | Historia / caso de uso | Paso o rama del modelo | Escenario de aceptación relacionado |
|---|---|---|---|
| [ID] | [IDs] | [paso/rama] | [caso normal, límite o rechazo; enlace o referencia exacta] |

Los escenarios se han recorrido sobre el modelo; eso no equivale a ejecutar pruebas del programa.

## 6. Revisión recibida

## 7. Dudas y cambios en los requisitos

| Requisito | Duda o cambio | Estado / confirmación del cliente | Impacto |
|---|---|---|---|
| [...] | [...] | [...] | [...] |

[Si no hubo cambios, indicarlo. Las correcciones aprobadas también deben quedar en el archivo de la sesión 6.]

## 8. Siguiente paso y participación

- Tarea de desarrollo derivada del modelo: [...]
- Requisito que la justifica: [...]
- Responsable inicial: [...]
- Issue existente o nuevo, si corresponde: [enlace]
- Aportes de cada integrante: [...]
- Asistencia de IA, si se utilizó: [herramienta, propósito, aporte y verificación]
