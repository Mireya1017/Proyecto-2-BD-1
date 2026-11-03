# =====================================================
# PRUEBA DEL METODO FEFO
# Responsable: Nathalie
# Simulacion sin modificar PostgreSQL
# =====================================================

from datetime import date
from decimal import Decimal


def simular_consumo_fefo(p_lotes, p_cantidad):
    v_pendiente = Decimal(str(p_cantidad))
    v_consumos = []

    if v_pendiente <= 0 or not v_pendiente.is_finite():
        raise ValueError("La cantidad debe ser positiva.")

    # Primero los lotes con caducidad mas cercana.
    # En caso de empate, primero el ID menor.
    v_lotes_ordenados = sorted(
        p_lotes,
        key=lambda lote: (
            lote["fecha_caducidad"],
            lote["id_lote"]
        )
    )

    for v_lote in v_lotes_ordenados:

        if v_lote["fecha_caducidad"] < date.today():
            continue

        v_disponible = Decimal(
            str(v_lote["cantidad_disponible"])
        )

        if v_disponible <= 0:
            continue

        v_consumir = min(v_pendiente, v_disponible)

        v_consumos.append({
            "id_lote": v_lote["id_lote"],
            "cantidad_consumida": v_consumir,
            "cantidad_restante": v_disponible - v_consumir
        })

        v_pendiente -= v_consumir

        if v_pendiente == 0:
            break

    if v_pendiente > 0:
        raise ValueError(
            "Inventario insuficiente para completar la venta."
        )

    return v_consumos


def main():
    # Datos de ejemplo de Oakland Mall.
    v_lotes = [
        {
            "id_lote": 1,
            "fecha_caducidad": date(2026, 11, 7),
            "cantidad_disponible": Decimal("5000.000")
        },
        {
            "id_lote": 19,
            "fecha_caducidad": date(2026, 11, 15),
            "cantidad_disponible": Decimal("2000.000")
        }
    ]

    v_resultado = simular_consumo_fefo(
    v_lotes,
    Decimal("8000.000")
    )

    print("\n===== SIMULACION FEFO =====")

    for v_consumo in v_resultado:
        print(
            f"Lote: {v_consumo['id_lote']} | "
            f"Consumido: {v_consumo['cantidad_consumida']} g | "
            f"Restante: {v_consumo['cantidad_restante']} g"
        )


if __name__ == "__main__":
    main()