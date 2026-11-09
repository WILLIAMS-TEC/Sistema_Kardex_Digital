USE SISTEMA_KARDEX;

DELETE FROM USUARIOS;

-- Asegurar los roles maestros del sistema
IF NOT EXISTS (SELECT 1 FROM ROLES WHERE ID_ROL = 1)
BEGIN
    SET IDENTITY_INSERT ROLES ON;
    INSERT INTO ROLES (ID_ROL, NOMBRE_ROL, DESCRIPCION) VALUES 
    (1, 'Administrador', 'Control total y auditoría del sistema'),
    (2, 'Encargado de Bodega', 'Operaciones y solicitudes de inventario'),
    (3, 'Consulta / Supervisión', 'Lectura de inventario y descarga de reportes');
    SET IDENTITY_INSERT ROLES OFF;
END

-- Configuro ÚNICAMENTE el usuario Administrador por defecto: Williams
-- Con este insert garantizo que solo exista la cuenta de Williams con rol de Administrador (ID_ROL = 1)
INSERT INTO USUARIOS (NOMBRE_COMPLETO, CORREO, PASSW_ORD, ID_ROL, ESTADO) VALUES 
('Williams', 'SEQUENW7@GMAIL.COM', 'admin123', 1, 1);

-- 2. TIPOS DE MOVIMIENTOS

IF NOT EXISTS (SELECT 1 FROM TIPOS_MOVIMIENTOS WHERE ID_TIPO_MOVIMIENTO = 1)
BEGIN
    INSERT INTO TIPOS_MOVIMIENTOS (NOMBRE_TIPO, EFECTO_STOCK) VALUES 
    ('ENTRADA', 1),
    ('SALIDA', -1),
    ('DEVOLUCION', 1),
    ('AJUSTE_POSITIVO', 1),
    ('AJUSTE_NEGATIVO', -1),
    ('TRASLADO', 0);
END

-- 3. MOTIVOS DE EXCEPCIONES
IF NOT EXISTS (SELECT 1 FROM MOTIVOS_EXCEPCIONES WHERE ID_MOTIVO = 1)
BEGIN
    INSERT INTO MOTIVOS_EXCEPCIONES (DESCRIPCION_MOTIVO) VALUES 
    ('Producto Dañado'),
    ('Diferencia en Conteo Físico'),
    ('Devolución de Cliente'),
    ('Vencimiento');
END

-- 4. BODEGAS
IF NOT EXISTS (SELECT 1 FROM BODEGAS WHERE ID_BODEGA = 1)
BEGIN
    INSERT INTO BODEGAS (NOMBRE_BODEGA, UBICACION, ESTADO) VALUES 
    ('Bodega Central', 'Edificio Principal - Planta Baja', 1),
    ('Bodega Sucursal Norte', 'Zona 4', 1);
END

-- 5. CATEGORÍAS

IF NOT EXISTS (SELECT 1 FROM CATEGORIAS WHERE ID_CATEGORIA = 1)
BEGIN
    INSERT INTO CATEGORIAS (NOMBRE_CATEGORIA, DESCRIPCION) VALUES 
    ('Electrónica', 'Equipos electrónicos y de cómputo'),
    ('Mobiliario', 'Sillas, escritorios y muebles de oficina'),
    ('Papelería', 'Insumos de oficina generales');
END

-- 6. UNIDADES DE MEDIDA

IF NOT EXISTS (SELECT 1 FROM UNIDADES_MEDIDA WHERE ID_UNIDAD = 1)
BEGIN
    INSERT INTO UNIDADES_MEDIDA (NOMBRE_UNIDAD, SIMBOLO) VALUES 
    ('Unidad', 'Un'),
    ('Caja (12 Unidades)', 'Cj'),
    ('Paquete', 'Pq');
END


-- 7. PRODUCTOS

IF NOT EXISTS (SELECT 1 FROM PRODUCTOS WHERE ID_PRODUCTO = 1)
BEGIN
    INSERT INTO PRODUCTOS (CODIGO_UNICO, DESCRIPCION_PRODUCTO, ID_CATEGORIA, ID_UNIDAD, STOCK_MINIMO, COSTO_PROMEDIO, ESTADO) VALUES 
    ('ELEC-001', 'Laptop Dell Latitude 3420', 1, 1, 5, 5500.00, 1),
    ('ELEC-002', 'Monitor LG 24 Pulgadas', 1, 1, 10, 1200.00, 1),
    ('MOB-001', 'Silla Ergonómica Ejecutiva', 2, 1, 4, 850.00, 1),
    ('PAP-001', 'Resma de Papel Tamaño Carta', 3, 2, 20, 35.00, 1);
END

-- 8. EXISTENCIAS POR BODEGA (SEMAFORIZACIÓN VIVA)
IF NOT EXISTS (SELECT 1 FROM EXISTENCIAS_BODEGAS WHERE ID_EXISTENCIA = 1)
BEGIN
    INSERT INTO EXISTENCIAS_BODEGAS (ID_PRODUCTO, ID_BODEGA, STOCK_ACTUAL) VALUES 
    (1, 1, 15), -- Óptimo (Verde)
    (2, 1, 8),  -- Bajo stock, menor al mínimo de 10 (Amarillo)
    (3, 1, 0),  -- Agotado (Rojo)
    (4, 2, 50); -- Óptimo en otra bodega (Verde)
END

-- 9. PERMISOS Y ROLES
IF NOT EXISTS (SELECT 1 FROM PERMISOS WHERE ID_PERMISO = 1)
BEGIN
    INSERT INTO PERMISOS (CODIGO_PERMISO, NOMBRE_PERMISO) VALUES
    ('INV_CONSULTA', 'Consultar Inventario'),
    ('INV_REGISTRO', 'Registrar Movimientos'),
    ('ADM_USUARIOS', 'Gestionar Usuarios'),
    ('ADM_CATALOGO', 'Gestionar Catálogo'),
    ('ADM_AUTORIZA', 'Autorizar Ajustes');

    INSERT INTO ROLES_PERMISOS (ID_ROL, ID_PERMISO) VALUES 
    (1,1), (1,2), (1,3), (1,4), (1,5), -- Administrador: Control Total
    (2,1), (2,2), (2,4),               -- Encargado de Bodega: Operativo
    (3,1);                             -- Consultas: Solo Lectura
END
