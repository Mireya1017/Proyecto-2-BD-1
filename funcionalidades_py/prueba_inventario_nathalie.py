# =====================================================
# PRUEBA DEL MODULO DE INVENTARIO
# Responsable: Nathalie
# =====================================================

from funcionalidades_py.inventario import (
    consultar_existencias,
    consultar_lotes
)


def main():
    print("\n===== INVENTARIO OAKLAND MALL =====")

    v_existencias = consultar_existencias(1)

    for v_insumo in v_existencias:
        print(
            f"Insumo: {v_insumo[1]} | "
            f"Disponible: {v_insumo[4]} "
            f"{v_insumo[2]}"
        )

    print("\n===== LOTES DE POLLO =====")

    v_lotes = consultar_lotes(1, 1)

    for v_lote in v_lotes:
        print(
            f"Lote: {v_lote[0]} | "
            f"Caducidad: {v_lote[2]} | "
            f"Cantidad: {v_lote[3]} | "
            f"Estado: {v_lote[5]}"
        )


if __name__ == "__main__":
    main()


