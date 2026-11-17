BEGIN;

CREATE INDEX idx_reserva_sucursal_fecha
ON reserva (id_sucursal, fecha_hora_inicio);

CREATE INDEX idx_reserva_cliente
ON reserva (id_cliente);

CREATE INDEX idx_reserva_mesa_mesa
ON reserva_mesa (id_mesa);

CREATE INDEX idx_visita_cliente_fecha
ON visita (id_cliente, fecha_hora_llegada);

CREATE INDEX idx_visita_mesa_mesa
ON visita_mesa (id_mesa);

CREATE INDEX idx_lote_sucursal_insumo_caducidad
ON lote (id_sucursal, id_insumo, fecha_caducidad);

CREATE INDEX idx_venta_visita
ON venta (id_visita);

CREATE INDEX idx_bitacora_usuario_fecha
ON bitacora (id_usuario, fecha_hora);

COMMIT;
