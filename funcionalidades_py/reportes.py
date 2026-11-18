"""
Módulo de Reporte de Rendimiento de Sucursales.
Agrega reservas y ventas por separado antes de combinarlas para evitar multiplicar totales.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List

from app.database import transaccion, ErrorPermiso
from app.auth import SesionUsuario, validar_permisos_operacion


def reporte_rendimiento_sucursales(
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    id_sucursal: Optional[int] = None,
    sesion: Optional[SesionUsuario] = None,
    conn: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Genera reporte con cantidad de reservas, cantidad de ventas e importe vendido.
    Utiliza CTEs independientes para evitar el producto cartesiano entre reservas y ventas.
    """
    validar_permisos_operacion(sesion, roles_permitidos="administrador")

    with transaccion(conn) as c:
        with c.cursor() as cur:
            nombre_sucursal_filtro = "Todas las sucursales"
            if id_sucursal is not None:
                cur.execute("SELECT nombre FROM sucursal WHERE id_sucursal = %s;", (id_sucursal,))
                s_row = cur.fetchone()
                if s_row:
                    nombre_sucursal_filtro = s_row[0]

            query = """
                WITH metricas_reservas AS (
                    SELECT 
                        r.id_sucursal,
                        COUNT(r.id_reserva) AS total_reservas
                    FROM reserva r
                    WHERE (%s::TIMESTAMP IS NULL OR r.fecha_hora_inicio >= %s)
                      AND (%s::TIMESTAMP IS NULL OR r.fecha_hora_inicio <= %s)
                      AND (%s::INTEGER IS NULL OR r.id_sucursal = %s)
                    GROUP BY r.id_sucursal
                ),
                ventas_visita AS (
                    SELECT 
                        v.id_sucursal,
                        vt.id_venta,
                        COALESCE(SUM(dv.cantidad * dv.precio_unitario), 0.00) AS subtotal_venta
                    FROM visita v
                    JOIN venta vt ON vt.id_visita = v.id_visita
                    JOIN detalle_venta dv ON dv.id_venta = vt.id_venta
                    WHERE (%s::TIMESTAMP IS NULL OR vt.fecha_hora >= %s)
                      AND (%s::TIMESTAMP IS NULL OR vt.fecha_hora <= %s)
                      AND (%s::INTEGER IS NULL OR v.id_sucursal = %s)
                    GROUP BY v.id_sucursal, vt.id_venta
                ),
                metricas_ventas AS (
                    SELECT 
                        vv.id_sucursal,
                        COUNT(vv.id_venta) AS total_ventas,
                        COALESCE(SUM(vv.subtotal_venta), 0.00) AS total_importe
                    FROM ventas_visita vv
                    GROUP BY vv.id_sucursal
                )
                SELECT 
                    s.id_sucursal,
                    s.nombre AS nombre_sucursal,
                    s.direccion,
                    COALESCE(mr.total_reservas, 0)::BIGINT AS cantidad_reservas,
                    COALESCE(mv.total_ventas, 0)::BIGINT AS cantidad_ventas,
                    COALESCE(mv.total_importe, 0.00)::NUMERIC(12,2) AS importe_vendido
                FROM sucursal s
                LEFT JOIN metricas_reservas mr ON mr.id_sucursal = s.id_sucursal
                LEFT JOIN metricas_ventas mv ON mv.id_sucursal = s.id_sucursal
                WHERE (%s::INTEGER IS NULL OR s.id_sucursal = %s)
                ORDER BY 
                    importe_vendido DESC,
                    cantidad_ventas DESC,
                    cantidad_reservas DESC,
                    s.nombre ASC;
            """
            cur.execute(
                query,
                (
                    fecha_desde, fecha_desde,
                    fecha_hasta, fecha_hasta,
                    id_sucursal, id_sucursal,

                    fecha_desde, fecha_desde,
                    fecha_hasta, fecha_hasta,
                    id_sucursal, id_sucursal,

                    id_sucursal, id_sucursal
                )
            )

            filas = []
            total_reservas = 0
            total_ventas = 0
            total_importe = Decimal("0.00")

            for row in cur.fetchall():
                sid, snombre, sdir, c_res, c_ven, imp = row
                filas.append({
                    "id_sucursal": sid,
                    "nombre_sucursal": snombre,
                    "direccion": sdir,
                    "cantidad_reservas": int(c_res),
                    "cantidad_ventas": int(c_ven),
                    "importe_vendido": float(imp)
                })
                total_reservas += int(c_res)
                total_ventas += int(c_ven)
                total_importe += Decimal(str(imp))

            return {
                "filtros": {
                    "fecha_desde": fecha_desde.strftime("%Y-%m-%d %H:%M") if fecha_desde else "Sin límite inferior",
                    "fecha_hasta": fecha_hasta.strftime("%Y-%m-%d %H:%M") if fecha_hasta else "Sin límite superior",
                    "id_sucursal": id_sucursal,
                    "sucursal": nombre_sucursal_filtro
                },
                "filas": filas,
                "totales": {
                    "total_reservas": total_reservas,
                    "total_ventas": total_ventas,
                    "total_importe_vendido": float(total_importe)
                },
                "total_registros": len(filas),
                "tiene_datos": len(filas) > 0 and (total_reservas > 0 or total_ventas > 0)
            }
