from funcionalidades_py.inventario import registrar_entrada


def probar_error(p_nombre, p_sesion, p_datos):
    try:
        registrar_entrada(None, p_sesion, p_datos)
        print(f"ERROR: {p_nombre} no fue rechazado")
    except (PermissionError, ValueError) as v_error:
        print(f"CORRECTO: {p_nombre}")
        print(f"Motivo: {v_error}\n")


def main():
    # Sesiones simuladas exclusivamente para probar
    # validaciones locales, sin conexión a PostgreSQL.
    v_gerente = {
        "id_usuario": 1,
        "rol": "gerente",
        "id_sucursal": 1
    }

    v_mesero = {
        "id_usuario": 2,
        "rol": "mesero",
        "id_sucursal": 1
    }

    v_datos = {
        "id_insumo": 1,
        "id_sucursal": 1,
        "fecha_recepcion": "2026-11-02",
        "fecha_caducidad": "2026-11-15",
        "cantidad": "2000.000"
    }

    # Prueba 1: mesero sin permisos
    probar_error(
        "Mesero sin permisos",
        v_mesero,
        v_datos
    )

    # Prueba 2: gerente de otra sucursal
    probar_error(
        "Gerente de otra sucursal",
        v_gerente,
        {**v_datos, "id_sucursal": 2}
    )

    # Prueba 3: cantidad negativa
    probar_error(
        "Cantidad negativa",
        v_gerente,
        {**v_datos, "cantidad": "-500"}
    )

        # Prueba 4: fecha de caducidad anterior a recepción
    probar_error(
        "Fecha de caducidad invalida",
        v_gerente,
        {
            **v_datos,
            "fecha_recepcion": "2026-11-10",
            "fecha_caducidad": "2026-11-05"
        }
    )


if __name__ == "__main__":
    main()