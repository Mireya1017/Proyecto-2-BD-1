# Sistema de Gestión de Restaurante - Proyecto 2 BD 1

Sistema administrativo integral para restaurante con sucursales (Oakland Mall y Ciudad Cayalá), desarrollado en Python y PostgreSQL.

---

## Componente de Pablo (Integrante 2) - Operaciones Administrativas y Conexión

### 1. Requisitos y Dependencias
- Python 3.10 o superior.
- PostgreSQL 14 o superior en ejecución.
- Dependencias de Python indicadas en `requirements.txt`:
  ```bash
  pip install -r requirements.txt
  ```

### 2. Configuración de Conexión Externa
El sistema mantiene las credenciales estrictamente fuera del código fuente.
Copie la plantilla de configuración `.env.example` como `.env` y defina los parámetros locales:
```bash
cp .env.example .env
```
Parámetros en `.env`:
```ini
DB_HOST=localhost
DB_PORT=5432
DB_NAME=restaurante_prueba
DB_USER=postgres
DB_PASSWORD=su_contraseña_local
DB_MIN_CONN=1
DB_MAX_CONN=10
```

### 3. Carga de Base de Datos y Datos Iniciales
Ejecutar los scripts de `bd/` en el orden oficial:
1. `bd/estructura.sql`
2. `bd/restricciones.sql`
3. `bd/indices.sql`
4. `bd/triggers.sql`
5. `bd/datos_iniciales.sql`

Opcionalmente, para probar con usuarios, clientes, reservas y ventas de prueba preconfiguradas:
```bash
# Extensión opcional para proveedores y compras (si se desea evaluar dicho módulo)
psql -U postgres -d restaurante_prueba -f bd/extension_compras_proveedores.sql

# Datos de demostración de Pablo
psql -U postgres -d restaurante_prueba -f bd/datos_demostracion_pablo.sql
```

### 4. Inicialización del Primer Administrador
La carga inicial no crea usuarios. Para registrar al administrador inicial en una base vacía, ejecute:
```bash
python setup_admin.py
```
El asistente solicitará nombre de usuario, contraseña (protegida con sal y hash PBKDF2) y sucursal habitual.

### 5. Usuarios de Demostración Preconfigurados
Si cargó `bd/datos_demostracion_pablo.sql`, puede iniciar sesión con:
- **Administrador**: `admin_pablo` | Contraseña: `Admin123!`
- **Gerente Oakland**: `gerente_oakland` | Contraseña: `Gerente123!`
- **Gerente Cayalá**: `gerente_cayala` | Contraseña: `Gerente123!`
- **Mesero Oakland**: `mesero_oakland` | Contraseña: `Mesero123!`
- **Mesero Cayalá**: `mesero_cayala` | Contraseña: `Mesero123!`

### 6. Ejecución de la Consola Administrativa
Inicie la consola principal ejecutando:
```bash
python main.py
```
El menú filtrará automáticamente las opciones autorizadas según el rol autenticado:
1. **Gestión de Reservas de Mesas**:
   - Consulta de disponibilidad en tiempo real con sugerencias de mesas en la misma zona.
   - Creación atómica de reservas con protección de concurrencia (`pg_advisory_xact_lock(308802)`).
   - Búsqueda con filtros múltiples (reserva, cliente, fecha, estado).
   - Modificación con reasignación atómica de mesas.
   - Cancelación manteniendo registros históricos.
2. **Administración de Usuarios** (Exclusivo Administrador):
   - Registro con roles (`administrador`, `gerente`, `mesero`) y sucursales obligatorias.
3. **Consulta de Bitácora de Auditoría** (Exclusivo Administrador):
   - Registros automáticos de triggers con usuario responsable (`app.id_usuario`).
   - Filtros por fecha, usuario, tabla y operación (`INSERT`, `UPDATE`, `DELETE`).
4. **Reporte de Rendimiento por Sucursales** (Exclusivo Administrador):
   - Cantidad de reservas, cantidad de ventas e importe total vendido por sede.
   - Agregación mediante CTEs independientes que elimina el producto cartesiano entre reservas y ventas.
5. **Gestión de Proveedores y Compras Coordinadas**:
   - Registro transaccional coordinado con el ingreso a inventario de Nathalie.

### 7. Ejecución de Pruebas Unitarias
Para verificar la suite completa de pruebas unitarias automatizadas:
```bash
python -m unittest tests/test_pablo.py
```
