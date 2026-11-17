from funcionalidades_py.ventas import consultar_menu


def main():
    print("\n===== MENU DEL RESTAURANTE =====")

    v_productos = consultar_menu()

    for v_producto in v_productos:
        print(
            f"ID: {v_producto[0]} | "
            f"Producto: {v_producto[1]} | "
            f"Precio: Q{v_producto[2]:.2f}"
        )


if __name__ == "__main__":
    main()