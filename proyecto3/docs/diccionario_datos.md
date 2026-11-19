Diccionario de datos — Proyecto 3
Objetivo del modelo
Organizar información de reservas, visitas y uso de mesas para analizar la atención del restaurante.

La base analítica se llama restaurante_olap y contiene cuatro dimensiones y tres tablas de hechos.

PK: clave primaria.
FK: clave foránea.

Todos los campos son obligatorios, excepto fact_visita.id_reserva_origen.
1. dim_sucursal
Describe las sucursales del restaurante. Conserva sus identificadores del Proyecto 2.
Campo	Tipo	Descripción
id_sucursal	INTEGER — PK	Identificador positivo de la sucursal.
nombre	VARCHAR(100)	Nombre de la sucursal.
direccion	VARCHAR(200)	Dirección de la sucursal.


2. dim_mesa
Describe las mesas disponibles en cada sucursal. Conserva sus identificadores del Proyecto 2.
Campo	Tipo	Descripción
id_mesa	INTEGER — PK	Identificador positivo de la mesa.
id_sucursal	INTEGER — FK	Sucursal a la que pertenece. Referencia dim_sucursal.
numero	INTEGER	Número de mesa dentro de su sucursal. Mayor que cero.
capacidad	INTEGER	Cantidad de personas que admite. Mayor que cero.
zona	VARCHAR(10)	Ubicación: interior o exterior.


La combinación de sucursal y número de mesa es única.
3. dim_fecha
Calendario que permite agrupar los eventos por fecha, mes y día de la semana.
Campo	Tipo	Descripción
id_fecha	INTEGER — PK	Fecha en formato numérico AAAAMMDD.
fecha	DATE — UNIQUE	Fecha del calendario.
anio	INTEGER	Año de la fecha.
mes	INTEGER	Número del mes.
nombre_mes	VARCHAR(15)	Nombre del mes en español.
dia_mes	INTEGER	Día dentro del mes.
dia_semana	INTEGER	Lunes = 1; domingo = 7.
nombre_dia	VARCHAR(15)	Nombre del día en español.


Ejemplo: el 5 de mayo de 2026 utiliza id_fecha = 20260505.

Las restricciones comprueban que los componentes numéricos coincidan con fecha. El ETL genera los nombres correspondientes en español.
4. dim_hora
Describe los 24 intervalos horarios del día.
Campo	Tipo	Descripción
id_hora	INTEGER — PK	Hora entre 0 y 23.
etiqueta	VARCHAR(5) — UNIQUE	Representación de la hora, por ejemplo 13:00.


La hora 13 representa desde las 13:00 hasta antes de las 14:00. El ETL prepara la etiqueta correspondiente.
5. fact_reserva
Una fila representa una reserva.
Campo	Tipo	Descripción
id_reserva	INTEGER — PK	Identificador positivo de la reserva fuente.
id_sucursal	INTEGER — FK	Referencia dim_sucursal.
id_fecha	INTEGER — FK	Fecha del inicio previsto. Referencia dim_fecha.
id_hora	INTEGER — FK	Hora del inicio previsto. Referencia dim_hora.
fecha_hora_inicio	TIMESTAMP	Inicio previsto de la reserva.
fecha_hora_fin_estimada	TIMESTAMP	Fin estimado, posterior al inicio.
cantidad_personas	INTEGER	Personas reservadas. Mayor que cero.
estado	VARCHAR(15)	confirmada, atendida, cancelada o no_asistio.


Las restricciones comprueban que id_fecha e id_hora coincidan con el inicio previsto.

La estructura admite los cuatro estados, pero el conjunto simulado inicial utiliza solamente los tres estados finales.
6. fact_visita
Una fila representa una visita, aunque utilice varias mesas.
Campo	Tipo	Descripción
id_visita	INTEGER — PK	Identificador positivo de la visita fuente.
id_sucursal	INTEGER — FK	Referencia dim_sucursal.
id_fecha	INTEGER — FK	Fecha de llegada. Referencia dim_fecha.
id_hora	INTEGER — FK	Hora de llegada. Referencia dim_hora.
id_reserva_origen	INTEGER — UNIQUE, opcional	Reserva asociada. NULL significa visita sin reserva.
fecha_hora_llegada	TIMESTAMP	Llegada real del grupo.
fecha_hora_salida	TIMESTAMP	Salida, posterior a la llegada.
cantidad_personas	INTEGER	Personas atendidas. Mayor que cero.
capacidad_asignada	INTEGER	Suma de capacidades de las mesas utilizadas.


La capacidad asignada debe ser igual o superior a la cantidad de personas.

Una reserva no puede asociarse a varias visitas. Pueden existir varias visitas sin reserva.

id_reserva_origen no tiene FK hacia otro hecho: su existencia y correspondencia se comprueban en el ETL.

Las restricciones comprueban que id_fecha e id_hora coincidan con la llegada.
7. fact_uso_mesa
Una fila representa una mesa asignada a una visita.
Campo	Tipo	Descripción
id_visita_origen	INTEGER — parte de PK	Identificador positivo de la visita fuente.
id_mesa	INTEGER — FK, parte de PK	Referencia dim_mesa.
id_sucursal	INTEGER — FK	Referencia dim_sucursal.
id_fecha	INTEGER — FK	Fecha de llegada. Referencia dim_fecha.
fecha_hora_llegada	TIMESTAMP	Llegada de la visita.
fecha_hora_salida	TIMESTAMP	Salida, posterior a la llegada.
fecha_hora_liberacion	TIMESTAMP	Momento en que la mesa vuelve a estar disponible. Igual o posterior a la salida.


La PK compuesta es id_visita_origen, id_mesa. Evita repetir una misma asignación.

id_visita_origen no tiene FK hacia otro hecho: su correspondencia se comprueba en el ETL.

No se almacena cantidad de personas para evitar repetir esa medida por cada mesa.
8. Relaciones y prevención de duplicaciones
- Una sucursal tiene varias mesas.
- Las dimensiones describen los eventos almacenados en los hechos.
- Una reserva y una visita representan eventos diferentes.
- Una visita puede tener varias asignaciones de mesa.
- Los hechos no se conectan mediante claves foráneas entre sí.
Una visita de cinco personas que utiliza dos mesas genera:
- Una fila en fact_visita, con cinco personas.
- Dos filas en fact_uso_mesa.
Las personas y visitas se cuentan desde fact_visita, sin multiplicarlas por las mesas utilizadas.
9. Responsabilidad del ETL
Además de las restricciones SQL, el ETL comprueba:
- Referencias y correspondencias entre archivos.
- Estados de reserva y visitas asociadas.
- Pertenencia de las mesas a la sucursal de la visita.
- Coincidencia de horarios entre visita y asignaciones.
- Ausencia de superposiciones de mesas.
- Capacidad asignada calculada desde las mesas.
- Período, horarios y parámetros de generación.
- Nombres y etiquetas de las dimensiones.
Los timestamps representan hora local de Guatemala.
10. Índices adicionales
Índice	Columnas	Propósito
idx_reserva_sucursal_fecha_hora	Sucursal, fecha y hora	Apoyar consultas de reservas por sucursal y período.
idx_visita_sucursal_fecha_hora	Sucursal, fecha y hora	Apoyar consultas de demanda.
idx_uso_mesa_sucursal_fecha	Sucursal y fecha	Apoyar consultas de asignaciones por período.
idx_uso_mesa_llegada	Mesa y llegada	Apoyar consultas del historial de cada mesa.


Las PK y restricciones UNIQUE ya generan sus propios índices; no se duplican manualmente.