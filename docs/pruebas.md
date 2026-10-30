# Pruebas

## Prueba de carga

`python manage.py stress_test --rentas 50` (solo con `DEBUG=True`) registra 50 clientes con `register_client` y 50 mesas con `register_equipment`, y lanza dos escenarios con 50 hilos que llaman a `create_rental`, el mismo caso de uso que la web. Una barrera (`threading.Barrier`) suelta todos los hilos juntos; cada hilo cierra su conexión y al final el comando borra todo lo que creó. Sale con error si el resultado no es el esperado.

1. **El mismo equipo, el mismo periodo:** debe guardarse 1 renta y rechazarse 49 por «ocupado» (RF-01, ENT-21: gana el primer clic). Lo asegura `select_for_update()` sobre la fila del equipo en `create_rental`.
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
