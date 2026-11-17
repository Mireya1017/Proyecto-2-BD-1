# =====================================================
# PRUEBAS DE ALERTAS DE INVENTARIO
# Responsable: Nathalie
# Proyecto 02 - Base de Datos 1
# =====================================================

from funcionalidades_py.inventario import (
    consultar_alertas_existencias,
    consultar_alertas_caducidad
)


def main():
    v_sucursales = [
        (1, "Oakland Mall"),
        (2, "Ciudad Cayalá")
    ]

    for v_id_sucursal, v_nombre in v_sucursales:

        print(f"\n===== ALERTAS: {v_nombre} =====")

        # PRUEBA 1: Existencias por debajo del mínimo
        print("\n--- EXISTENCIAS BAJAS ---")

        v_alertas = consultar_alertas_existencias(
            v_id_sucursal
        )

        if not v_alertas:
            print("No hay insumos por debajo del mínimo.")
        else:
            for v_alerta in v_alertas:
                print(
                    f"Insumo: {v_alerta[0]} | "
                    f"Mínimo: {v_alerta[2]} | "
                    f"Disponible: {v_alerta[3]} "
                    f"{v_alerta[1]}"
                )

        # PRUEBA 2: Próxima caducidad
        print("\n--- PRÓXIMA CADUCIDAD (7 DÍAS) ---")

        v_lotes = consultar_alertas_caducidad(
            v_id_sucursal,
            7
        )

        if not v_lotes:
            print("No hay lotes próximos a caducar.")
        else:
            for v_lote in v_lotes:
                print(
                    f"Insumo: {v_lote[0]} | "
                    f"Lote: {v_lote[1]} | "
                    f"Caducidad: {v_lote[2]} | "
                    f"Disponible: {v_lote[3]} "
                    f"{v_lote[4]} | "
                    f"Días restantes: {v_lote[5]}"
                )


if __name__ == "__main__":
    main()