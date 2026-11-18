# Especificación de Funciones Compartidas - Pablo (Integrante 2)

Este documento define la interfaz pública, parámetros, resultados, excepciones y acuerdos transaccionales
de los módulos desarrollados por Pablo para la integración con los módulos de Nathalie (Inventario)
y Yu-fong (Clientes y Navegación Principal).

---

## 1. Conexión Compartida y Transacciones (`app/database.py`)

### `obtener_conexion() -> connection`
- **Propósito**: Obtiene una conexión reutilizable desde el pool configurado.
- **Parámetros**: Ninguno.
- **Retorno**: Conexión activa a PostgreSQL (`psycopg2.extensions.connection`).
- **Excepciones**: `ErrorConexion` si no se puede conectar al servidor.
- **Responsabilidad**: Debe ser liberada con `liberar_conexion(conn)` si se adquiere manualmente.

### `transaccion(conn=None, id_usuario=None) -> contextmanager`
- **Propósito**: Gestor de contexto transaccional unificado para todas las operaciones del sistema.
- **Parámetros**:
  - `conn`: Conexión opcional. Si es `None`, abre una conexión del pool y es responsable exclusivo de ejecutar `COMMIT` al finalizar o `ROLLBACK` en caso de excepción. Si se pasa una conexión existente, participa de la transacción sin cerrarla ni hacer commit anticipado.
  - `id_usuario`: ID del usuario autenticado. Comunica automáticamente el contexto a la base de datos mediante `SELECT set_config('app.id_usuario', %s, true);` para que los triggers de auditoría registren al responsable.
- **Comportamiento**:
  - `is_local=true` asegura que la variable de sesión se limpie al finalizar la transacción.
  - Traduce excepciones nativas de PostgreSQL a excepciones del dominio (`ErrorDisponibilidad`, `ErrorCapacidad`, `ErrorRestriccion`).

---

## 2. Autenticación y Sesión (`app/auth.py`, `app/usuarios.py`)

### `iniciar_sesion(nombre_usuario: str, contrasena: str, conn=None) -> SesionUsuario`
- **Propósito**: Autentica las credenciales del usuario validando el hash con sal PBKDF2-HMAC-SHA256.
- **Parámetros**: Nombre de usuario y contraseña en texto claro.
- **Retorno**: Objeto inmutable `SesionUsuario` con:
  - `id_usuario`: int
  - `nombre_usuario`: str
  - `rol`: 'administrador', 'gerente' o 'mesero'
  - `id_sucursal`: int (sucursal habitual)
- **Excepciones**: `ErrorAutenticacion` ante credenciales inválidas.

### `validar_permisos_operacion(sesion, roles_permitidos, id_sucursal_operacion=None)`
- **Propósito**: Comprobación obligatoria de seguridad dentro de las operaciones de negocio.
- **Regla**: El administrador tiene acceso global. Los gerentes y meseros solo pueden operar en su sucursal habitual.

---

## 3. Reservas y Disponibilidad (`app/reservas.py`)

### `consultar_disponibilidad_mesas(id_sucursal, fecha_hora_inicio, fecha_hora_fin, zona=None, conn=None) -> List[dict]`
- **Propósito**: Consulta mesas libres sin superposición horaria con reservas confirmadas o atendidas.
- **Uso por Yu-fong**: Debe consultarse antes de asignar mesas a una visita o llegada física.

### `crear_reserva(id_cliente, id_sucursal, fecha_hora_inicio, fecha_hora_fin_estimada, cantidad_personas, ids_mesas, sesion=None, conn=None) -> int`
- **Propósito**: Registro atómico de la reserva y sus mesas asignadas.
- **Garantías**:
  - Adquiere bloqueo consultivo `pg_advisory_xact_lock(308802)`.
  - Valida misma sucursal, misma zona y capacidad total suficiente.
  - Inserta cabecera y detalle en una sola transacción confirmada en conjunto.

### `obtener_reservas_cliente(id_cliente: int, conn=None) -> List[dict]`
- **Propósito**: Función compartida para el módulo de Clientes de Yu-fong.
- **Retorno**: Lista de reservas históricas del cliente con fechas, sucursal, cantidad de personas, estado y mesas.

---

## 4. Coordinación Compras e Inventario (`app/compras.py`)

### `registrar_compra(id_proveedor, id_sucursal, detalles_insumos, funcion_ingreso_lotes=None, sesion=None, conn=None) -> int`
- **Protocolo de Transacción**:
  1. Pablo abre la transacción global `with transaccion(conn, id_usuario=sesion.id_usuario) as c:`.
  2. Pablo inserta cabecera en `compra` y líneas en `detalle_compra`.
  3. Pablo invoca `funcion_ingreso_lotes(conn=c, id_sucursal=id_sucursal, lotes=...)` pasando la **misma conexión**.
  4. Nathalie inserta las existencias en `lote` dentro de esa misma transacción (sin hacer commit).
  5. Pablo ejecuta el `COMMIT` final. Si el inventario falla, la compra completa se revierte (`ROLLBACK`).

---

## 5. Integración con Menú Principal de Consola (`app/consola.py`)

### `obtener_opciones_menu_pablo(sesion: SesionUsuario) -> dict`
- **Propósito**: Entrega a Yu-fong el mapa de opciones listas para conectar al menú general:
  - Administrador: Reservas, Usuarios, Bitácora, Reporte de Sucursales, Proveedores/Compras.
  - Gerente: Reservas, Proveedores/Compras.
  - Mesero: Reservas.
