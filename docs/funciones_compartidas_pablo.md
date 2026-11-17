iniciar_sesion(p_nombre_usuario, p_contrasena):
Propósito: Autenticar credenciales contra la tabla usuario y devolver el diccionario de sesión creado con crear_sesion.   
Transacción: Solo lectura; abre y cierra su propia conexión.   
validar_permiso(p_sesion, p_roles_permitidos) y validar_acceso_sucursal(p_sesion, p_id_sucursal_objetivo):Propósito: Validar que el rol autenticado tenga permiso y que gerentes/meseros solo operen sobre su propia sucursal.   
Errores: Lanza PermissionError si no cumple las reglas.   
consultar_mesas_disponibles(p_id_sucursal, p_fecha_hora_inicio, p_fecha_hora_fin_estimada, p_zona=None, p_id_reserva_excluir=None):
Propósito: Consultar mesas libres de reservas confirmada o atendida en un rango horario; reutilizable por Yu-fong antes de asignar mesas en una visita.   
obtener_reservas_por_cliente(p_id_cliente):
Propósito: Entregar al módulo de clientes de Yu-fong el historial de reservas de un cliente con sus mesas y estado. 