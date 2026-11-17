# ------------------------------------------
# Contiene la lógica para registrar clientes
# ------------------------------------------

# Registra el nombre y teléfono de un cliente
def registrar_cliente(p_conexion, p_sesion, p_datos):
    nombre = p_datos["nombre"].strip()
    telefono = p_datos.get("telefono")

    if not nombre:
        raise ValueError("El nombre del cliente es obligatorio.")

    if len(nombre) > 120:
        raise ValueError("El nombre no puede superar los 120 caracteres.")

    if telefono is not None:
        telefono = telefono.strip()

        if not telefono:
            telefono = None
        elif len(telefono) > 20:
            raise ValueError("El teléfono no puede superar 20 caracteres.")

    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para registrar clientes.")

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO cliente (nombre, telefono)
            VALUES (%s, %s)
            RETURNING id_cliente;
            """,
            (nombre, telefono)
        )

        id_cliente = cursor.fetchone()[0]

    return id_cliente

# ------------------------------------------

# Busca en base al nombre del cliente
def buscar_clientes(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para buscar clientes.")

    nombre = p_datos.get("nombre", "").strip()

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_cliente, nombre, telefono
            FROM cliente
            WHERE nombre ILIKE %s
            ORDER BY nombre, id_cliente;
            """,
            (f"%{nombre}%",)
        )

        clientes = cursor.fetchall()

    return clientes

# ------------------------------------------

# Busca en base al ID del cliente
def obtener_cliente(p_conexion, p_sesion, p_datos):
    if p_sesion["rol"] not in ("administrador", "gerente", "mesero"):
        raise PermissionError("No tiene permiso para consultar clientes.")

    id_cliente = p_datos["id_cliente"]

    with p_conexion.cursor() as cursor:
        cursor.execute(
            """
            SELECT id_cliente, nombre, telefono
            FROM cliente
            WHERE id_cliente = %s;
            """,
            (id_cliente,)
        )

        cliente = cursor.fetchone()

    return cliente

# FIN DEL CÓDIGO :)