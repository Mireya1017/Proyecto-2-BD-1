# Proyecto 3 — Fuentes de datos y supuestos

**Responsable:** Nathalie
**Proyecto:** Análisis de reservas y aprovechamiento de mesas
**Base analítica:** `restaurante_olap`

## 1. Objetivo

Documentar la procedencia, estructura y reglas de generación de las fuentes utilizadas para construir el DataMart del restaurante.

El análisis comprende las sucursales Oakland Mall y Ciudad Cayalá, durante el período del 1 de mayo al 31 de octubre de 2026.

## 2. Fuentes de datos

El Proyecto 3 utiliza cinco archivos CSV:

| Archivo | Procedencia | Descripción |
|---|---|---|
| `sucursales.csv` | Proyecto 2 | Catálogo de sucursales. |
| `mesas.csv` | Proyecto 2 | Catálogo de mesas, capacidades y zonas. |
| `reservas.csv` | Generador Python de Nathalie | Reservas simuladas. |
| `visitas.csv` | Generador Python de Yu | Visitas con y sin reserva. |
| `visitas_mesas.csv` | Generador Python de Yu | Asignaciones de mesas y liberaciones. |

Los catálogos conservan los identificadores originales del Proyecto 2.

## 3. Estructura de los archivos

### sucursales.csv

`id_sucursal,nombre,direccion`

Contiene el identificador, nombre y dirección de cada sucursal.

### mesas.csv

`id_mesa,id_sucursal,numero,capacidad,zona`

Contiene el identificador de mesa, sucursal, número, capacidad y zona.

### reservas.csv

`id_reserva,id_sucursal,fecha_hora_inicio,fecha_hora_fin_estimada,cantidad_personas,estado`

Contiene las reservas generadas, incluyendo fechas, cantidad de personas y estado final.

Los estados permitidos son `atendida`, `cancelada` y `no_asistio`.

### visitas.csv

`id_visita,id_sucursal,id_reserva,fecha_hora_llegada,fecha_hora_salida,cantidad_personas`

Contiene las visitas generadas por Yu. El campo `id_reserva` queda vacío cuando la visita no proviene de una reserva.

### visitas_mesas.csv

`id_visita,id_mesa,fecha_hora_liberacion`

Relaciona las visitas con las mesas utilizadas y registra el momento de liberación.

## 4. Formato común

Todos los archivos utilizan:

- Codificación UTF-8.
- Separador coma.
- Encabezados exactos.
- Fechas y horas en formato `AAAA-MM-DD HH:MM:SS`.
- Hora local de Guatemala.
- Identificadores enteros positivos.
- Campos ausentes representados mediante valores vacíos.

Únicamente `visitas.id_reserva` puede estar vacío. No se utilizan los textos `NULL`, `None` o `N/A` para representar ausencia.

## 5. Parámetros de generación

Los parámetros compartidos se encuentran en `proyecto3/python/parametros.py`.

**Período de generación:** desde el 1 de mayo de 2026, inclusive, hasta el 1 de noviembre de 2026, exclusivo.

**Distribución actualizada del escenario simulado**

Se conservan 2,400 reservas y 3,000 visitas en todo el período de mayo a octubre de 2026. Las cantidades por mes y sucursal son variables.

Los estados de reserva se generan mediante probabilidades, sin exigir porcentajes finales exactos. Las visitas con reserva corresponden a las reservas atendidas; las visitas sin reserva completan el total general.

La generación incorpora pesos mensuales, diarios y horarios documentados en parametros.py. Son supuestos de simulación, no patrones comprobados del restaurante real.

Se mantienen las reglas de horarios, capacidad y ausencia de superposiciones.

Quedan reemplazadas las cuotas anteriores de 200 reservas y 250 visitas mensuales por sucursal, así como los porcentajes obligatorios de 75 %, 12.5 % y 12.5 %.

**Reservas por mes y sucursal:**

| Estado | Cantidad |
|---|---:|
| Atendida | 150 |
| Cancelada | 25 |
| No asistió | 25 |
| **Total** | **200** |

Para dos sucursales y seis meses se generan 2,400 reservas.

El horario de inicio de reservas comprende las horas completas entre las 11:00 y las 20:00. Cada reserva tiene una duración estimada de 90 minutos.

Los grupos contienen entre una y ocho personas, con probabilidades definidas en `parametros.py`.

## 6. Reglas del generador de reservas

El archivo `generar_reservas.py`:

1. Lee los catálogos originales.
2. Comprueba los identificadores y referencias.
3. Genera reservas para cada mes y sucursal.
4. Asigna horarios únicos por sucursal, fecha y hora.
5. Distribuye los estados según las cantidades acordadas.
6. Genera tamaños de grupo mediante probabilidades.
7. Ordena los registros por sucursal y fecha.
8. Asigna identificadores consecutivos desde uno.
9. Exporta `reservas.csv`.

No asigna mesas ni genera visitas. Estas responsabilidades corresponden al generador de Yu.

## 7. Reproducibilidad

Se utiliza la semilla `3088` para el generador de reservas y `3089` para el generador de visitas.

Se comprobó que ejecutar nuevamente el generador de reservas, conservando los mismos archivos de entrada y parámetros, produce un CSV idéntico.

También se verificaron los 2,400 registros, los identificadores consecutivos, los horarios únicos, las cantidades por estado, el período y las duraciones.

## 8. Ejemplo pequeño compartido

La carpeta `proyecto3/fuentes/ejemplo/` contiene un conjunto reducido para verificar la integración.

Nathalie preparó los catálogos de las dos sucursales, sus doce mesas y seis reservas que incluyen los tres estados finales.

Yu completará las visitas y asignaciones de mesas para comprobar la coherencia del ejemplo antes de procesar el conjunto completo.

## 9. Supuestos y limitaciones

- Los catálogos provienen de la base operativa del Proyecto 2.
- Las reservas y visitas son datos simulados, no registros históricos reales.
- Las probabilidades del tamaño de grupo orientan la generación; no representan porcentajes finales obligatorios.
- La duración de 90 minutos corresponde al período estimado de reserva, no necesariamente a la duración real de una visita.
- Los horarios generados son únicos por sucursal, fecha y hora de inicio, pero pueden existir intervalos de reservas que se superponen.
- La asignación de mesas y la comprobación de disponibilidad corresponden al generador de visitas.
- La generación de CSV no modifica la base operativa del Proyecto 2.
- La carga al DataMart se realizará posteriormente sobre `restaurante_olap`.

## 10. Ejecución

Desde la raíz del repositorio:

```powershell
python proyecto3/python/generar_reservas.py
```

El programa lee los catálogos de `proyecto3/fuentes/` y genera `reservas.csv` en el mismo directorio.

La extracción de catálogos se documenta en `sql/extraccion_catalogos_p2.sql`.

Las consultas analíticas de mesas se encuentran en `sql/04_consultas_catalogos.sql` y deberán ejecutarse sobre `restaurante_olap` después de cargar sus dimensiones.