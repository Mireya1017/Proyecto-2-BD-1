# Acuerdos técnicos — Proyecto 3

## 1. Propósito del documento

Este documento establece los acuerdos comunes para desarrollar la primera fase del Proyecto 3: fuentes, modelo analítico, procesamiento, carga, vistas y validación de datos.

Todos los integrantes deben respetar los nombres, estructuras, reglas y fórmulas aquí definidos.

Si es necesario modificar un acuerdo, se comunica al grupo y se actualiza este documento antes de cambiar los componentes afectados.

Estas decisiones corresponden a nuestra implementación. No representan requisitos adicionales establecidos por el catedrático.

La distribución y el diseño del tablero se definirán posteriormente.

## 2. Caso de negocio

**Nombre:** Análisis de reservas y aprovechamiento de mesas del restaurante.

**Sucursales:**

- Oakland Mall.
- Ciudad Cayalá.

**Distribución actualizada del escenario simulado**

Se conservan 2,400 reservas y 3,000 visitas en todo el período de mayo a octubre de 2026. Las cantidades por mes y sucursal son variables.

Los estados de reserva se generan mediante probabilidades, sin exigir porcentajes finales exactos. Las visitas con reserva corresponden a las reservas atendidas; las visitas sin reserva completan el total general.

La generación incorpora pesos mensuales, diarios y horarios documentados en parametros.py. Son supuestos de simulación, no patrones comprobados del restaurante real.

Se mantienen las reglas de horarios, capacidad y ausencia de superposiciones.

Quedan reemplazadas las cuotas anteriores de 200 reservas y 250 visitas mensuales por sucursal, así como los porcentajes obligatorios de 75 %, 12.5 % y 12.5 %.

**Objetivo:**

Analizar la demanda de atención, el comportamiento de las reservas, la duración de las visitas, la liberación de mesas y el aprovechamiento de la capacidad asignada para apoyar decisiones sobre la atención del restaurante.

### Preguntas de negocio

1. ¿Qué días y horarios reciben más visitas y personas?
2. ¿Qué proporción de las reservas fue atendida, cancelada o terminó en inasistencia?
3. ¿Cuánto duran las visitas?
4. ¿Cuánto tiempo transcurre entre la salida del cliente y la liberación de cada mesa?
5. ¿Qué proporción de la capacidad asignada utiliza cada grupo?
6. ¿Qué diferencias existen entre sucursales?

### Límites del análisis

- No se analizarán ventas, inventario, recetas ni preferencias.
- No se calcularán ganancias, costos ni pérdidas monetarias.
- No se estimarán clientes rechazados, porque no contamos con registros de ellos.
- No se medirá el bloqueo anticipado de mesas por reservas.
- El porcentaje de capacidad asignada no se presentará como ocupación del restaurante durante toda la jornada.
- Los datos simulados no se presentarán como operaciones reales.

## 3. Aprovechamiento del Proyecto 2

Se utilizarán como referencia las tablas y reglas de:

- sucursal.
- mesa.
- reserva.
- visita.
- visita_mesa.

Los catálogos de sucursales y mesas se exportarán desde la base del Proyecto 2.

Los eventos adicionales se generarán respetando las reglas relevantes del sistema original.

También se podrá adaptar el mecanismo existente de configuración y conexión de Python.

### Separación de bases

La base analítica se llamará:

`restaurante_olap`

El Proyecto 3 no modificará ni borrará datos de la base operativa del Proyecto 2.

No es necesario trasladar el login, los usuarios, la bitácora ni todos los triggers del Proyecto 2.

Los archivos CSV serán las fuentes del proceso de carga. Posteriormente, Power BI utilizará las tablas y vistas analíticas de PostgreSQL.

## 4. Período y volumen de trabajo

### Período

Desde el 1 de mayo hasta el 31 de octubre de 2026.

La fecha de corte es el 1 de noviembre de 2026 a las 00:00:00, como límite exclusivo.

Los eventos deben pertenecer al período y finalizar antes del corte.

Para esta primera versión:

- Todas las visitas tendrán salida.
- Todas las asignaciones de mesas tendrán liberación.
- No se generarán reservas pendientes de atención.

### Cantidades acordadas

| Elemento | Cantidad |
|---|---:|
| Reservas atendidas | 1800 |
| Reservas canceladas | 300 |
| Reservas con inasistencia | 300 |
| Total de reservas | 2400 |
| Visitas con reserva | 1800 |
| Visitas sin reserva | 1200 |
| Total de visitas | 3000 |

El número de asignaciones de mesas será igual o superior al número de visitas, porque algunas visitas utilizarán varias mesas.

Estas cantidades son metas de generación, no resultados reales del restaurante.

### Variedad de los datos

Los eventos deben distribuirse entre:

- Ambas sucursales.
- Los seis meses.
- Diferentes días y horarios.
- Grupos de distintos tamaños.
- Visitas con una o varias mesas.
- Diferentes duraciones y tiempos de liberación.

No se exige una distribución uniforme.

Los patrones deben ser plausibles y documentados. No deben generarse únicamente para garantizar una conclusión predeterminada.

## 5. Formato de los archivos fuente

Todos los archivos cumplirán lo siguiente:

| Aspecto | Acuerdo |
|---|---|
| Formato | CSV |
| Codificación | UTF-8 |
| Separador | Coma |
| Encabezados | Primera fila, con los nombres exactos acordados |
| Identificadores | Enteros positivos |
| Fechas y horas | AAAA-MM-DD HH:MM:SS |
| Referencia horaria | Hora local de Guatemala |
| Valores ausentes | Campo vacío |
| Texto que contenga comas | Entre comillas dobles |

No utilizar `NULL`, `None`, `N/A` ni cero para representar valores ausentes.

Se utilizará una biblioteca de manejo de CSV para generar los archivos y respetar las reglas de comillas.

Los timestamps se manejarán sin zona horaria incorporada, interpretándolos consistentemente como hora local de Guatemala.

### 5.1 sucursales.csv

Columnas, en este orden:

`id_sucursal,nombre,direccion`

Responsable: Nathalie.

### 5.2 mesas.csv

Columnas, en este orden:

`id_mesa,id_sucursal,numero,capacidad,zona`

Responsable: Nathalie.

### 5.3 reservas.csv

Columnas, en este orden:

`id_reserva,id_sucursal,fecha_hora_inicio,fecha_hora_fin_estimada,cantidad_personas,estado`

Responsable: Yu.

### 5.4 visitas.csv

Columnas, en este orden:

`id_visita,id_sucursal,id_reserva,fecha_hora_llegada,fecha_hora_salida,cantidad_personas`

Responsable: Yu.

### 5.5 visitas_mesas.csv

Columnas, en este orden:

`id_visita,id_mesa,fecha_hora_liberacion`

Responsable: Yu.

### Valores opcionales

Solamente `visitas.id_reserva` podrá estar vacío en las fuentes de esta versión.

Un valor vacío en ese campo significa que la visita llegó sin reserva.

Los identificadores de cada entidad deben ser estables y consistentes entre archivos.

## 6. Modelo analítico

Se utilizarán cuatro dimensiones y tres tablas de hechos.

### Principios

- Una reserva representa un evento diferente de una visita.
- Una visita puede utilizar varias mesas.
- Una visita con tres mesas se cuenta como una visita y tres asignaciones.
- Las cantidades de personas se almacenan en la visita y no se repiten como medida en cada asignación.
- Las dimensiones de sucursal y mesa conservarán los identificadores del Proyecto 2.
- Los datos derivados se calcularán durante el ETL o en las vistas, según este documento.

Todos los campos serán obligatorios, excepto los indicados como opcionales.

### 6.1 dim_sucursal

| Campo | Tipo | Regla |
|---|---|---|
| id_sucursal | INTEGER | PK; identificador del Proyecto 2 |
| nombre | VARCHAR(100) | Obligatorio |
| direccion | VARCHAR(200) | Obligatorio |

### 6.2 dim_mesa

| Campo | Tipo | Regla |
|---|---|---|
| id_mesa | INTEGER | PK; identificador del Proyecto 2 |
| id_sucursal | INTEGER | FK a dim_sucursal |
| numero | INTEGER | Mayor que cero |
| capacidad | INTEGER | Mayor que cero |
| zona | VARCHAR(10) | interior o exterior |

La combinación `id_sucursal, numero` será única.

La relación con sucursal permite conservar y validar la pertenencia de cada mesa.

Al configurar posteriormente Power BI, se evitarán caminos de filtrado ambiguos entre dimensiones y hechos.

### 6.3 dim_fecha

| Campo | Tipo | Regla |
|---|---|---|
| id_fecha | INTEGER | PK con formato numérico AAAAMMDD |
| fecha | DATE | Única |
| anio | INTEGER | Año |
| mes | INTEGER | De 1 a 12 |
| nombre_mes | VARCHAR(15) | Nombre en español |
| dia_mes | INTEGER | De 1 a 31, según la fecha |
| dia_semana | INTEGER | Lunes = 1; domingo = 7 |
| nombre_dia | VARCHAR(15) | Nombre en español |

Ejemplo:

La fecha 2026-05-05 tendrá `id_fecha = 20260505`.

Se cargarán todas las fechas del período, aunque algún día no tenga eventos.

### 6.4 dim_hora

| Campo | Tipo | Regla |
|---|---|---|
| id_hora | INTEGER | PK; de 0 a 23 |
| etiqueta | VARCHAR(5) | Ejemplo: 13:00 |

Cada valor representa una hora completa.

Ejemplo:

`id_hora = 13` incluye eventos desde las 13:00:00 hasta antes de las 14:00:00.

### 6.5 fact_reserva

**Una fila representa una reserva.**

| Campo | Tipo | Regla |
|---|---|---|
| id_reserva | INTEGER | PK; identificador del CSV |
| id_sucursal | INTEGER | FK a dim_sucursal |
| id_fecha | INTEGER | FK a dim_fecha; fecha del inicio previsto |
| id_hora | INTEGER | FK a dim_hora; hora del inicio previsto |
| fecha_hora_inicio | TIMESTAMP | Inicio previsto |
| fecha_hora_fin_estimada | TIMESTAMP | Posterior al inicio |
| cantidad_personas | INTEGER | Mayor que cero |
| estado | VARCHAR(15) | Estado válido |

Estados permitidos por la estructura:

- confirmada.
- atendida.
- cancelada.
- no_asistio.

El conjunto inicial utilizará únicamente los tres estados finales: atendida, cancelada y no_asistio.

### 6.6 fact_visita

**Una fila representa una visita, independientemente de cuántas mesas utilice.**

| Campo | Tipo | Regla |
|---|---|---|
| id_visita | INTEGER | PK; identificador del CSV |
| id_sucursal | INTEGER | FK a dim_sucursal |
| id_fecha | INTEGER | FK a dim_fecha; fecha de llegada |
| id_hora | INTEGER | FK a dim_hora; hora de llegada |
| id_reserva_origen | INTEGER | Opcional; reserva asociada |
| fecha_hora_llegada | TIMESTAMP | Llegada real |
| fecha_hora_salida | TIMESTAMP | Posterior a la llegada |
| cantidad_personas | INTEGER | Mayor que cero |
| capacidad_asignada | INTEGER | Suma de capacidades de sus mesas |

El ETL calculará `capacidad_asignada`.

`id_reserva_origen` se conserva para trazabilidad. Su correspondencia se validará durante el ETL.

No se establecerá una FK entre las dos tablas de hechos.

Una misma reserva no podrá asociarse a más de una visita.

### 6.7 fact_uso_mesa

**Una fila representa una mesa asignada a una visita.**

| Campo | Tipo | Regla |
|---|---|---|
| id_visita_origen | INTEGER | Identificador de la visita fuente |
| id_mesa | INTEGER | FK a dim_mesa |
| id_sucursal | INTEGER | FK a dim_sucursal |
| id_fecha | INTEGER | FK a dim_fecha; fecha de llegada |
| fecha_hora_llegada | TIMESTAMP | Llegada de la visita |
| fecha_hora_salida | TIMESTAMP | Salida de la visita |
| fecha_hora_liberacion | TIMESTAMP | Igual o posterior a la salida |

PK compuesta:

`id_visita_origen, id_mesa`

La correspondencia con la visita se validará en el ETL.

No se establecerá una FK hacia fact_visita.

No se almacenará cantidad de personas en esta tabla para evitar duplicar esa medida.

Esta versión supone que las mesas asignadas acompañan a la visita desde su llegada hasta su salida. Después, cada mesa puede tener su propio momento de liberación.

## 7. Reglas de validación

### Identificación y referencias

- No puede haber IDs duplicados de sucursales, mesas, reservas o visitas.
- No puede repetirse una combinación visita–mesa.
- Toda sucursal referenciada debe existir.
- Toda mesa asignada debe existir.
- Toda reserva asociada a una visita debe existir.

### Catálogos

- Los números y capacidades de mesas deben ser positivos.
- Las zonas válidas son interior y exterior.
- No puede repetirse un número de mesa dentro de una sucursal.
- Los campos obligatorios no pueden estar vacíos.

### Reservas y visitas

- La cantidad de personas debe ser un entero positivo.
- El fin estimado de la reserva debe ser posterior al inicio.
- La salida debe ser posterior a la llegada.
- La liberación debe ser igual o posterior a la salida.
- Los eventos deben respetar el período acordado.
- Las horas reales de llegada no necesitan coincidir exactamente con el horario reservado.

### Coherencia entre archivos

- La visita y su reserva deben pertenecer a la misma sucursal.
- Todas las mesas utilizadas deben pertenecer a la sucursal de la visita.
- Cada visita debe tener al menos una mesa.
- La capacidad total asignada debe alcanzar para el grupo.
- Cada reserva atendida debe tener exactamente una visita.
- Las reservas canceladas o con inasistencia no deben tener una visita asociada.

### Disponibilidad de mesas

Una mesa se considera ocupada desde la llegada de la visita hasta antes de su liberación.

No puede tener asignaciones que se superpongan durante ese intervalo.

Una nueva visita puede comenzar exactamente a la hora en que la asignación anterior libera la mesa.

## 8. Indicadores y fórmulas oficiales

Las duraciones se expresarán en minutos.

Los cálculos conservarán su precisión durante el procesamiento. El redondeo a dos decimales se aplicará al presentar resultados, cuando corresponda.

### Cantidad de visitas

Contar filas de fact_visita.

No contar las filas de fact_uso_mesa como si fueran visitas.

### Personas atendidas

Sumar cantidad_personas desde fact_visita.

### Cantidad de reservas

Contar filas de fact_reserva.

### Porcentaje por estado final

Reservas del estado analizado / total de reservas con estado final × 100.

Estados finales:

- atendida.
- cancelada.
- no_asistio.

Si posteriormente existen reservas confirmadas pendientes, se mostrarán aparte y no se interpretarán como inasistencias.

### Duración de visita

fecha_hora_salida − fecha_hora_llegada.

Se calcula por visita.

### Tiempo hasta liberación

fecha_hora_liberacion − fecha_hora_salida.

Se calcula por asignación de mesa.

Puede incluir limpieza y demora en registrar la liberación. No se presentará como duración exacta de limpieza.

### Tiempo de uso de mesa

fecha_hora_liberacion − fecha_hora_llegada.

Incluye la permanencia del grupo y el tiempo posterior hasta liberar la mesa.

Al sumar tiempos de varias mesas se obtienen minutos-mesa, no minutos únicos de operación del restaurante.

### Capacidad asignada

Suma de capacidades de las mesas utilizadas por una visita.

### Aprovechamiento por visita

cantidad_personas / capacidad_asignada × 100.

### Aprovechamiento agregado

Suma de personas / suma de capacidad asignada × 100.

Ambas sumas deben realizarse con una fila por visita.

Este indicador mide el aprovechamiento de los asientos asignados a los grupos, no la ocupación del restaurante durante toda su jornada.

### Casos sin datos

- Los conteos serán cero cuando corresponda.
- Los promedios sin observaciones serán NULL.
- Los porcentajes con denominador cero serán NULL.
- En la presentación se podrán identificar como “Sin datos”.

Los promedios agregados se calcularán desde los registros originales o mediante sus sumas y conteos. No se promediarán promedios sin considerar sus tamaños.

## 9. Vistas analíticas

### vw_demanda_atencion

Una fila por sucursal, fecha y hora de llegada.

Debe incluir:

- Identificación de sucursal, fecha y hora.
- Cantidad de visitas.
- Cantidad de personas.

### vw_reservas_estado

Una fila por sucursal, fecha prevista y estado.

Debe incluir:

- Identificación de sucursal y fecha.
- Estado.
- Cantidad de reservas.

Los porcentajes se calcularán respetando el denominador documentado.

### vw_duracion_visitas

Una fila por visita.

Debe incluir:

- Identificador de visita.
- Sucursal.
- Fecha y hora de llegada.
- Cantidad de personas.
- Duración en minutos.

### vw_liberacion_mesas

Una fila por asignación visita–mesa.

Debe incluir:

- Identificadores de visita, mesa y sucursal.
- Fecha de llegada.
- Salida y liberación.
- Minutos hasta liberación.

### vw_capacidad_asignada

Una fila por visita.

Debe incluir:

- Identificador de visita.
- Sucursal y fecha.
- Cantidad de personas.
- Capacidad asignada.
- Porcentaje de aprovechamiento por visita.

### vw_uso_mesas

Una fila por asignación visita–mesa.

Debe incluir:

- Identificadores de visita, mesa y sucursal.
- Número y capacidad de mesa.
- Fecha de llegada.
- Minutos de uso.

### Prevención de duplicaciones

No se unirán indiscriminadamente las tres tablas de hechos para sumar todos los indicadores.

Cada medida se calculará desde el hecho correspondiente.

Cuando sea necesario comparar resultados, primero se agregarán al mismo nivel: por ejemplo, sucursal y fecha.

## 10. Generación y carga

### Generación de eventos

El generador:

- Utilizará los catálogos entregados por Nathalie.
- Permitirá configurar el período y las cantidades.
- Utilizará una semilla fija, documentada, para reproducir los resultados.
- Respetará las capacidades y la disponibilidad de las mesas.
- Producirá los tres CSV de eventos acordados.

No será necesario registrar manualmente los eventos mediante el menú del Proyecto 2.

### Estrategia de carga

Se utilizará recarga completa de los datos analíticos.

Orden general:

1. Leer todos los archivos.
2. Validar estructura, tipos y reglas de coherencia.
3. Si hay errores, generar un reporte y detener la carga.
4. Iniciar la sustitución de datos del DataMart dentro de una transacción.
5. Cargar dimensiones.
6. Preparar los campos derivados.
7. Cargar reservas, visitas y usos de mesas.
8. Confirmar únicamente cuando todo termine correctamente.
9. Revertir la operación si ocurre un error durante la carga.

Se preservará el esquema analítico al reemplazar sus datos.

La recarga no afectará la base del Proyecto 2.

### Manejo de errores

No se corregirán silenciosamente IDs, cantidades ni fechas para aceptar registros inválidos.

El reporte de errores incluirá:

- Archivo.
- Número de fila, cuando aplique.
- Campo o registro afectado.
- Motivo del error.

El archivo de errores se generará en:

`python/errores_carga.csv`

Cada ejecución lo reemplazará con el resultado de la validación actual.

Los problemas que involucren varios registros deben identificar las claves relacionadas.

### Resumen de ejecución

El proceso mostrará:

- Archivos procesados.
- Filas leídas por archivo.
- Cantidad de errores.
- Filas cargadas por tabla.
- Confirmación de éxito o reversión.

Si la validación falla antes de cargar, los datos analíticos existentes no se modificarán.

## 11. Estructura de carpetas

proyecto3/
    fuentes/
        sucursales.csv
        mesas.csv
        reservas.csv
        visitas.csv
        visitas_mesas.csv
    sql/
        01_modelo_estrella.sql
        02_vistas_analiticas.sql
        03_validaciones_analiticas.sql
        04_validaciones_catalogos.sql
        extraccion_catalogos_p2.sql
    python/
        conexion.py
        generar_eventos.py
        cargar_datamart.py
    docs/
        acuerdos_tecnicos.md
        modelo_estrella.pdf
        diccionario_datos.md
        fuentes_y_supuestos.md
        indicadores.md
    README.md
    requirements.txt
    config.ini.example

El archivo errores_carga.csv será generado durante la ejecución y no se incluirá como fuente.

La ubicación del dump se indicará en el README al preparar la entrega.

La carpeta del tablero se agregará en la segunda fase.

## 12. Configuración y Git

- Las contraseñas se guardarán en configuración local.
- El repositorio incluirá config.ini.example sin credenciales reales.
- No se subirán archivos privados de configuración.
- No se subirán entornos virtuales, cachés ni reportes temporales de errores.
- Los CSV utilizados para reproducir el proyecto sí formarán parte de las fuentes compartidas.
- requirements.txt especificará las dependencias utilizadas.
- Las rutas se resolverán desde la ubicación del proyecto, evitando rutas personales de Windows.

Cada integrante trabajará en una rama propia y abrirá un pull request para integrar sus cambios.

Cada integrante revisará los archivos preparados antes de realizar un commit.

Los cambios del Proyecto 3 se mantendrán separados de modificaciones ajenas del Proyecto 2.

## 13. Responsabilidades

### Mireya — modelo y estructura

Responsable de:

- Diseñar dimensiones y hechos.
- Definir tipos, PK, FK, restricciones e índices justificados.
- Crear 01_modelo_estrella.sql.
- Elaborar el diagrama.
- Documentar las tablas y su nivel de detalle.
- Comprobar la creación desde cero.

Entregables:

- SQL del modelo.
- Diagrama.
- Diccionario de datos.

### Pablo — vistas e indicadores

Responsable de:

- Crear las seis vistas analíticas.
- Definir y documentar las fórmulas.
- Evitar duplicaciones por uniones entre hechos.
- Comprobar conteos, porcentajes y duraciones.
- Preparar ejemplos con resultados esperados.

Entregables:

- 02_vistas_analiticas.sql.
- 03_validaciones_analiticas.sql.
- indicadores.md.

### Yu — generación, ETL e integración técnica

Responsable de:

- Generar reservas, visitas y asignaciones.
- Programar lectura, validación, transformación y carga.
- Calcular capacidad asignada.
- Gestionar transacciones y cargas repetidas.
- Producir reportes de errores.
- Coordinar la ejecución técnica completa.
- Generar el dump y comprobar su restauración.

Entregables:

- Tres CSV de eventos.
- Código Python.
- Configuración de ejemplo y dependencias.
- Instrucciones de ejecución.
- Dump probado.

Coordinar la integración no implica corregir todos los componentes ajenos. Cada integrante corrige su propio trabajo.

### Nathalie — catálogos y fuentes

Responsable de:

- Extraer sucursales y mesas del Proyecto 2.
- Conservar sus identificadores originales.
- Preparar los dos CSV de catálogos.
- Revisar duplicados, capacidades, zonas y sucursales.
- Documentar las fuentes y columnas de los cinco CSV.
- Documentar los supuestos de generación que entregue Yu.
- Preparar consultas sencillas de comprobación.

Entregables:

- sucursales.csv.
- mesas.csv.
- extraccion_catalogos_p2.sql.
- 04_validaciones_catalogos.sql.
- fuentes_y_supuestos.md.

No le corresponde programar el generador ni el ETL.

### Responsabilidad compartida

Cada integrante:

- Documenta cómo ejecutar su componente.
- Aporta su sección al README.
- Corrige los errores de su parte.
- Comprueba que su componente respete estos acuerdos.
- Entiende cómo se conecta con el proceso completo.

## 14. Orden de trabajo

1. Revisar y aprobar estos acuerdos.
2. Preparar un ejemplo pequeño común con resultados conocidos.
3. Nathalie entrega los catálogos.
4. Mireya desarrolla el modelo.
5. Yu desarrolla generación y ETL.
6. Pablo desarrolla vistas y validaciones sobre el ejemplo.
7. Integrar el recorrido completo con el ejemplo pequeño.
8. Generar y cargar el conjunto completo.
9. Ejecutar las comprobaciones.
10. Restaurar el respaldo en una base de prueba.

Los pasos de desarrollo pueden avanzar en paralelo utilizando la estructura acordada.

## 15. Condiciones para cerrar la fase de datos

La fase estará terminada cuando:

- La estructura se cree desde cero.
- Los cinco CSV respeten el formato acordado.
- La carga funcione con los datos completos.
- Una segunda ejecución no duplique registros.
- Los errores de validación detengan la carga.
- Un fallo durante la escritura revierta la transacción.
- Los conteos coincidan con las cantidades acordadas.
- Las asignaciones no dupliquen las medidas de visitas.
- Las vistas produzcan resultados verificables.
- El respaldo pueda restaurarse.
- El README permita reproducir el proceso.

La siguiente fase será diseñar y construir el tablero entre los cuatro integrantes.