-- Archivo: config/Estructura_Base_de_Datos.sql
-- ============================================================
-- SCRIPT DE CREACIÓN DE BASE DE DATOS - FORMA GEST PRO
-- PostgreSQL 18 - Versión 2.0.0 (Simplificada y Funcional)
-- ============================================================

-- 1. ELIMINAR BASE DE DATOS EXISTENTE (OPCIONAL - SOLO SI QUIERES REINICIAR)
-- DROP DATABASE IF EXISTS formagestpro_db;
-- CREATE DATABASE formagestpro_db;

-- 2. DOMINIOS PARA VALIDACIÓN
CREATE DOMAIN d_expedicion_ci AS TEXT 
    CHECK (VALUE IN ('BE', 'CH', 'CB', 'LP', 'OR', 'PD', 'PT', 'SC', 'TJ', 'EX'));

CREATE DOMAIN d_grado_academico AS TEXT 
    CHECK (VALUE IN ('LIC.', 'ING.', 'M.Sc.', 'Mg.', 'MBA', 'Ph.D.', 'Dr.'));

CREATE DOMAIN d_estado_programa AS TEXT 
    CHECK (VALUE IN ('PLANIFICADO', 'INSCRIPCIONES', 'EN_CURSO', 'CONCLUIDO', 'CANCELADO'));

CREATE DOMAIN d_estado_academico AS TEXT 
    CHECK (VALUE IN ('PREINSCRITO', 'INSCRITO', 'EN_CURSO', 'CONCLUIDO', 'RETIRADO'));

CREATE DOMAIN d_forma_pago AS TEXT 
    CHECK (VALUE IN ('EFECTIVO', 'TRANSFERENCIA', 'TARJETA', 'DEPOSITO', 'QR'));

CREATE DOMAIN d_estado_transaccion AS TEXT 
    CHECK (VALUE IN ('REGISTRADO', 'CONFIRMADO', 'ANULADO'));

CREATE DOMAIN d_tipo_movimiento AS TEXT 
    CHECK (VALUE IN ('INGRESO', 'EGRESO'));

CREATE DOMAIN d_rol_usuario AS TEXT 
    CHECK (VALUE IN ('ADMINISTRADOR', 'COORDINADOR', 'CAJERO', 'CONSULTA'));

CREATE DOMAIN d_extension_archivo AS TEXT 
    CHECK (VALUE IN ('jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'));

-- 3. SECUENCIAS
CREATE SEQUENCE seq_estudiantes_id START 1;
CREATE SEQUENCE seq_docentes_id START 1;
CREATE SEQUENCE seq_programas_id START 1;
CREATE SEQUENCE seq_conceptos_pago_id START 1;
CREATE SEQUENCE seq_transacciones_id START 1;
CREATE SEQUENCE seq_detalles_transaccion_id START 1;
CREATE SEQUENCE seq_documentos_respaldo_id START 1;
CREATE SEQUENCE seq_facturas_id START 1;
CREATE SEQUENCE seq_usuarios_id START 1;

-- 4. TABLAS PRINCIPALES - NUEVA ESTRUCTURA

-- 4.1 EMPRESA (Configuración básica)
CREATE TABLE empresa (
    id SERIAL PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL DEFAULT 'CONSULTORA FORMACIÓN CONTINUA S.R.L.',
    nit VARCHAR(20) UNIQUE NOT NULL DEFAULT '194810025',
    direccion VARCHAR(300),
    telefono VARCHAR(20),
    email VARCHAR(100),
    logo_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4.2 ESTUDIANTES (Simplificado)
CREATE TABLE estudiantes (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_estudiantes_id'),
    ci_numero VARCHAR(15) NOT NULL,
    ci_expedicion d_expedicion_ci NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100),
    fecha_nacimiento DATE,
    telefono VARCHAR(20),
    email VARCHAR(100),
    direccion TEXT,
    profesion VARCHAR(100),
    universidad VARCHAR(200),
    fotografia_url TEXT,
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_estudiante_ci UNIQUE (ci_numero),
    CONSTRAINT ck_email_valido CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 4.3 DOCENTES (Simplificado)
CREATE TABLE docentes (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_docentes_id'),
    ci_numero VARCHAR(15) NOT NULL,
    ci_expedicion d_expedicion_ci NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellido_paterno VARCHAR(100) NOT NULL,
    apellido_materno VARCHAR(100),
    fecha_nacimiento DATE,
    grado_academico d_grado_academico,
    titulo_profesional VARCHAR(200),
    especialidad VARCHAR(200),
    telefono VARCHAR(20),
    email VARCHAR(100),
    curriculum_url TEXT,
    honorario_hora DECIMAL(10,2),
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_docente_ci UNIQUE (ci_numero),
    CONSTRAINT ck_email_docente_valido CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT ck_honorario_positivo CHECK (honorario_hora >= 0)
);

-- 4.4 PROGRAMAS ACADÉMICOS (Simplificado y más claro)
CREATE TABLE programas (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_programas_id'),
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    duracion_meses INTEGER NOT NULL,
    horas_totales INTEGER NOT NULL,
    costo_total DECIMAL(10,2) NOT NULL,
    costo_matricula DECIMAL(10,2) DEFAULT 0,
    costo_inscripcion DECIMAL(10,2) DEFAULT 0,
    costo_mensualidad DECIMAL(10,2) NOT NULL,
    numero_cuotas INTEGER NOT NULL DEFAULT 1,
    cupos_maximos INTEGER,
    cupos_inscritos INTEGER DEFAULT 0,
    estado d_estado_programa DEFAULT 'PLANIFICADO',
    fecha_inicio DATE,
    fecha_fin DATE,
    docente_coordinador_id INTEGER,
    promocion_descuento DECIMAL(5,2) DEFAULT 0,
    promocion_descripcion TEXT,
    promocion_valido_hasta DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_programa_coordinador 
        FOREIGN KEY (docente_coordinador_id) 
        REFERENCES docentes(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT ck_cupos_validos CHECK (cupos_inscritos <= cupos_maximos),
    CONSTRAINT ck_costos_positivos CHECK (
        costo_total >= 0 AND 
        costo_matricula >= 0 AND 
        costo_inscripcion >= 0 AND 
        costo_mensualidad >= 0
    ),
    CONSTRAINT ck_duracion_positiva CHECK (duracion_meses > 0),
    CONSTRAINT ck_cuotas_positivas CHECK (numero_cuotas > 0)
);

-- 4.5 CONCEPTOS DE PAGO (Catálogo de conceptos cobrables)
CREATE TABLE conceptos_pago (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_conceptos_pago_id'),
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(20) DEFAULT 'FIJO' CHECK (tipo IN ('FIJO', 'VARIABLE', 'PORCENTAJE')),
    valor_base DECIMAL(10,2),
    porcentaje DECIMAL(5,2),
    aplica_programa BOOLEAN DEFAULT TRUE,
    aplica_estudiante BOOLEAN DEFAULT TRUE,
    orden_visualizacion INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO conceptos_pago (codigo, nombre, descripcion, tipo, valor_base, orden_visualizacion) VALUES
('MATRICULA', 'Matrícula', 'Pago por derecho a matrícula en el programa', 'FIJO', 0, 1),
('INSCRIPCION', 'Inscripción', 'Pago por proceso de inscripción', 'FIJO', 0, 2),
('MENSUALIDAD', 'Mensualidad', 'Pago mensual del programa', 'FIJO', 0, 3),
('CERTIFICACION', 'Certificación', 'Costo de certificado', 'FIJO', 0, 4),
('MATERIAL', 'Material', 'Costo de materiales', 'FIJO', 0, 5);

-- 4.6 INSCRIPCIONES (Relación estudiante-programa)
CREATE TABLE inscripciones (
    id SERIAL PRIMARY KEY,
    estudiante_id INTEGER NOT NULL,
    programa_id INTEGER NOT NULL,
    fecha_inscripcion DATE DEFAULT CURRENT_DATE,
    estado d_estado_academico DEFAULT 'PREINSCRITO',
    descuento_aplicado DECIMAL(10,2) DEFAULT 0,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_inscripcion_estudiante 
        FOREIGN KEY (estudiante_id) 
        REFERENCES estudiantes(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_inscripcion_programa 
        FOREIGN KEY (programa_id) 
        REFERENCES programas(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT uk_inscripcion_unica UNIQUE (estudiante_id, programa_id)
);

-- 4.11 USUARIOS DEL SISTEMA
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_usuarios_id'),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre_completo VARCHAR(200) NOT NULL,
    email VARCHAR(100),
    rol d_rol_usuario DEFAULT 'CAJERO',
    activo BOOLEAN DEFAULT TRUE,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ultimo_acceso TIMESTAMP,
    
    CONSTRAINT ck_email_usuario_valido CHECK (email IS NULL OR email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- 4.7 TRANSACCIONES (Tabla principal de pagos)
CREATE TABLE transacciones (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_transacciones_id'),
    numero_transaccion VARCHAR(50) UNIQUE NOT NULL,
    estudiante_id INTEGER,
    programa_id INTEGER,
    fecha_pago DATE NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    monto_total DECIMAL(10,2) NOT NULL,
    descuento_total DECIMAL(10,2) DEFAULT 0,
    monto_final DECIMAL(10,2) NOT NULL,
    forma_pago d_forma_pago NOT NULL,
    estado d_estado_transaccion DEFAULT 'REGISTRADO',
    numero_comprobante VARCHAR(50),
    banco_origen VARCHAR(100),
    cuenta_origen VARCHAR(50),
    observaciones TEXT,
    registrado_por INTEGER,
    
    CONSTRAINT fk_transaccion_estudiante 
        FOREIGN KEY (estudiante_id) 
        REFERENCES estudiantes(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_transaccion_programa 
        FOREIGN KEY (programa_id) 
        REFERENCES programas(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_transaccion_registrado_por 
        FOREIGN KEY (registrado_por) 
        REFERENCES usuarios(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT ck_montos_validos CHECK (
        monto_total >= 0 AND 
        descuento_total >= 0 AND 
        monto_final >= 0 AND
        monto_final = monto_total - descuento_total
    )
);

-- 4.8 DETALLES DE TRANSACCIÓN (Conceptos específicos del pago)
CREATE TABLE detalles_transaccion (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_detalles_transaccion_id'),
    transaccion_id INTEGER NOT NULL,
    concepto_pago_id INTEGER NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    cantidad INTEGER DEFAULT 1,
    precio_unitario DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL,
    orden INTEGER DEFAULT 0,
    
    CONSTRAINT fk_detalle_transaccion 
        FOREIGN KEY (transaccion_id) 
        REFERENCES transacciones(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_detalle_concepto 
        FOREIGN KEY (concepto_pago_id) 
        REFERENCES conceptos_pago(id) 
        ON DELETE RESTRICT,
    
    CONSTRAINT ck_cantidad_positiva CHECK (cantidad > 0),
    CONSTRAINT ck_precio_positivo CHECK (precio_unitario >= 0),
    CONSTRAINT ck_subtotal_correcto CHECK (subtotal = cantidad * precio_unitario)
);

-- 4.9 DOCUMENTOS DE RESPALDO (Archivos adjuntos)
CREATE TABLE documentos_respaldo (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_documentos_respaldo_id'),
    transaccion_id INTEGER NOT NULL,
    tipo_documento VARCHAR(50) NOT NULL,
    nombre_original VARCHAR(200) NOT NULL,
    nombre_archivo VARCHAR(200) NOT NULL,
    extension d_extension_archivo NOT NULL,
    ruta_archivo TEXT NOT NULL,
    tamano_bytes INTEGER,
    observaciones TEXT,
    subido_por INTEGER,
    fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_documento_transaccion 
        FOREIGN KEY (transaccion_id) 
        REFERENCES transacciones(id) 
        ON DELETE CASCADE,
    
    CONSTRAINT fk_documento_subido_por 
        FOREIGN KEY (subido_por) 
        REFERENCES usuarios(id) 
        ON DELETE SET NULL
);

-- 4.10 FACTURAS (Solo registro, pueden estar asociadas a transacciones)
CREATE TABLE facturas (
    id INTEGER PRIMARY KEY DEFAULT nextval('seq_facturas_id'),
    transaccion_id INTEGER,
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    nit_ci VARCHAR(20) NOT NULL,
    razon_social VARCHAR(200) NOT NULL,
    direccion VARCHAR(300),
    fecha_emision DATE NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    iva DECIMAL(12,2) DEFAULT 0,
    it DECIMAL(12,2) DEFAULT 0,
    total DECIMAL(12,2) NOT NULL,
    estado VARCHAR(20) DEFAULT 'EMITIDA',
    exportada_siat BOOLEAN DEFAULT FALSE,
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_factura_transaccion 
        FOREIGN KEY (transaccion_id) 
        REFERENCES transacciones(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT ck_total_factura CHECK (total = subtotal + iva + it)
);

-- 4.12 MOVIMIENTOS DE CAJA (Registro simplificado para cierre de caja)
CREATE TABLE movimientos_caja (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    tipo d_tipo_movimiento NOT NULL,
    transaccion_id INTEGER,
    monto DECIMAL(10,2) NOT NULL,
    forma_pago d_forma_pago NOT NULL,
    descripcion VARCHAR(200) NOT NULL,
    usuario_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_movimiento_transaccion 
        FOREIGN KEY (transaccion_id) 
        REFERENCES transacciones(id) 
        ON DELETE SET NULL,
    
    CONSTRAINT fk_movimiento_usuario 
        FOREIGN KEY (usuario_id) 
        REFERENCES usuarios(id) 
        ON DELETE RESTRICT
);

-- 4.13 CONFIGURACIONES DEL SISTEMA
CREATE TABLE configuraciones (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT,
    descripcion TEXT,
    tipo VARCHAR(20) DEFAULT 'TEXTO',
    categoria VARCHAR(50) DEFAULT 'GENERAL',
    editable BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. ÍNDICES PARA OPTIMIZACIÓN
CREATE INDEX idx_estudiantes_ci ON estudiantes(ci_numero);
CREATE INDEX idx_estudiantes_nombre ON estudiantes(nombres, apellido_paterno);
CREATE INDEX idx_docentes_ci ON docentes(ci_numero);
CREATE INDEX idx_programas_codigo ON programas(codigo);
CREATE INDEX idx_programas_estado ON programas(estado);
CREATE INDEX idx_transacciones_numero ON transacciones(numero_transaccion);
CREATE INDEX idx_transacciones_fecha ON transacciones(fecha_pago DESC);
CREATE INDEX idx_transacciones_estudiante ON transacciones(estudiante_id);
CREATE INDEX idx_transacciones_programa ON transacciones(programa_id);
CREATE INDEX idx_detalles_transaccion ON detalles_transaccion(transaccion_id);
CREATE INDEX idx_inscripciones_estudiante ON inscripciones(estudiante_id);
CREATE INDEX idx_inscripciones_programa ON inscripciones(programa_id);
CREATE INDEX idx_movimientos_caja_fecha ON movimientos_caja(fecha DESC);
CREATE INDEX idx_facturas_numero ON facturas(numero_factura);
CREATE INDEX idx_facturas_fecha ON facturas(fecha_emision DESC);

-- 6. FUNCIONES Y TRIGGERS

-- 6.1 Función para generar número de transacción automático
CREATE OR REPLACE FUNCTION fn_generar_numero_transaccion()
RETURNS TRIGGER AS $$
DECLARE
    prefijo VARCHAR(10);
    anio VARCHAR(4);
    consecutivo INTEGER;
    nuevo_numero VARCHAR(50);
BEGIN
    -- Formato: T-YYYY-000001
    SELECT TO_CHAR(CURRENT_DATE, 'YYYY') INTO anio;
    
    -- Obtener último consecutivo del año
    SELECT COALESCE(MAX(SUBSTRING(numero_transaccion FROM '^T-\d{4}-(\d+)$')::INTEGER), 0) + 1
    INTO consecutivo
    FROM transacciones
    WHERE numero_transaccion LIKE 'T-' || anio || '-%';
    
    nuevo_numero := 'T-' || anio || '-' || LPAD(consecutivo::TEXT, 6, '0');
    
    NEW.numero_transaccion := nuevo_numero;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para generar número de transacción
CREATE TRIGGER tr_generar_numero_transaccion
    BEFORE INSERT ON transacciones
    FOR EACH ROW
    WHEN (NEW.numero_transaccion IS NULL)
    EXECUTE FUNCTION fn_generar_numero_transaccion();

-- 6.2 Función para actualizar monto total de transacción desde detalles
CREATE OR REPLACE FUNCTION fn_actualizar_monto_transaccion()
RETURNS TRIGGER AS $$
DECLARE
    total_transaccion DECIMAL(10,2);
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
        -- Calcular nuevo total
        SELECT COALESCE(SUM(subtotal), 0)
        INTO total_transaccion
        FROM detalles_transaccion
        WHERE transaccion_id = COALESCE(NEW.transaccion_id, OLD.transaccion_id);
        
        -- Actualizar transacción
        UPDATE transacciones
        SET monto_total = total_transaccion,
            monto_final = total_transaccion - COALESCE(descuento_total, 0)
        WHERE id = COALESCE(NEW.transaccion_id, OLD.transaccion_id);
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar montos
CREATE TRIGGER tr_actualizar_monto_transaccion
    AFTER INSERT OR UPDATE OR DELETE ON detalles_transaccion
    FOR EACH ROW
    EXECUTE FUNCTION fn_actualizar_monto_transaccion();

-- 6.3 Función para registrar movimiento de caja automático
CREATE OR REPLACE FUNCTION fn_registrar_movimiento_caja()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' AND NEW.estado = 'CONFIRMADO' THEN
        INSERT INTO movimientos_caja (fecha, tipo, transaccion_id, monto, forma_pago, descripcion, usuario_id)
        VALUES (
            NEW.fecha_pago,
            'INGRESO',
            NEW.id,
            NEW.monto_final,
            NEW.forma_pago,
            'Pago transacción ' || NEW.numero_transaccion,
            NEW.registrado_por
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para movimiento de caja
CREATE TRIGGER tr_registrar_movimiento_caja
    AFTER INSERT OR UPDATE ON transacciones
    FOR EACH ROW
    EXECUTE FUNCTION fn_registrar_movimiento_caja();

-- 6.4 Función para actualizar updated_at
CREATE OR REPLACE FUNCTION fn_actualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para updated_at en programas
CREATE TRIGGER tr_actualizar_timestamp_programa
    BEFORE UPDATE ON programas
    FOR EACH ROW
    EXECUTE FUNCTION fn_actualizar_timestamp();

-- 7. DATOS INICIALES

-- 7.1 Empresa
INSERT INTO empresa (nombre, nit, direccion, telefono, email) VALUES
('CONSULTORA FORMACIÓN CONTINUA S.R.L.', '194810025', 'Calle Calama Nro 104 piso 1', '+591 67935343', 'info@formacioncontinua.bo')
ON CONFLICT (nit) DO NOTHING;

-- 7.2 Usuario administrador (contraseña: admin123)
INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol) VALUES
('admin', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'Administrador Principal', 'admin@formacioncontinua.bo', 'ADMINISTRADOR')
ON CONFLICT (username) DO NOTHING;

-- 7.3 Configuraciones iniciales
INSERT INTO configuraciones (clave, valor, descripcion, tipo, categoria) VALUES
('EMPRESA_NOMBRE', 'CONSULTORA FORMACIÓN CONTINUA S.R.L.', 'Nombre legal de la empresa', 'TEXTO', 'EMPRESA'),
('EMPRESA_NIT', '194810025', 'NIT de la empresa', 'TEXTO', 'EMPRESA'),
('EMPRESA_DIRECCION', 'Calle Calama Nro 104 piso 1', 'Dirección fiscal', 'TEXTO', 'EMPRESA'),
('EMPRESA_TELEFONO', '+591 67935343', 'Teléfono de contacto', 'TEXTO', 'EMPRESA'),
('EMPRESA_EMAIL', 'info@formacioncontinua.bo', 'Email de contacto', 'TEXTO', 'EMPRESA'),
('SISTEMA_VERSION', '2.0.0', 'Versión actual del sistema', 'TEXTO', 'SISTEMA'),
('IVA_PORCENTAJE', '13', 'Porcentaje de IVA aplicable', 'NUMERO', 'IMPUESTOS'),
('IT_PORCENTAJE', '3', 'Porcentaje de IT aplicable', 'NUMERO', 'IMPUESTOS'),
('RUTA_ARCHIVOS', '/var/www/formagestpro/archivos/', 'Ruta base para almacenamiento de archivos', 'TEXTO', 'ARCHIVOS'),
('DIAS_VENCIMIENTO', '15', 'Días para vencimiento de cuotas', 'NUMERO', 'FINANZAS'),
('CORREO_NOTIFICACIONES', 'notificaciones@formacioncontinua.bo', 'Email para notificaciones', 'TEXTO', 'CORREO')
ON CONFLICT (clave) DO UPDATE SET valor = EXCLUDED.valor;

-- 8. VISTAS PARA REPORTES

-- 8.1 Vista: Transacciones con detalles completos
CREATE OR REPLACE VIEW vw_transacciones_completas AS
SELECT 
    t.id,
    t.numero_transaccion,
    t.fecha_pago,
    t.fecha_registro,
    e.nombres || ' ' || e.apellido_paterno || ' ' || COALESCE(e.apellido_materno, '') AS estudiante,
    p.nombre AS programa,
    t.monto_total,
    t.descuento_total,
    t.monto_final,
    t.forma_pago,
    t.estado,
    t.numero_comprobante,
    u.nombre_completo AS registrado_por,
    COUNT(dt.id) AS cantidad_conceptos
FROM transacciones t
LEFT JOIN estudiantes e ON t.estudiante_id = e.id
LEFT JOIN programas p ON t.programa_id = p.id
LEFT JOIN usuarios u ON t.registrado_por = u.id
LEFT JOIN detalles_transaccion dt ON t.id = dt.transaccion_id
GROUP BY t.id, e.nombres, e.apellido_paterno, e.apellido_materno, p.nombre, u.nombre_completo;

-- 8.2 Vista: Detalles de transacciones con conceptos
CREATE OR REPLACE VIEW vw_detalles_transaccion AS
SELECT 
    dt.id,
    t.numero_transaccion,
    t.fecha_pago,
    cp.nombre AS concepto,
    dt.descripcion,
    dt.cantidad,
    dt.precio_unitario,
    dt.subtotal,
    e.nombres || ' ' || e.apellido_paterno AS estudiante,
    p.nombre AS programa
FROM detalles_transaccion dt
JOIN transacciones t ON dt.transaccion_id = t.id
JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
LEFT JOIN estudiantes e ON t.estudiante_id = e.id
LEFT JOIN programas p ON t.programa_id = p.id;

-- 8.3 Vista: Estado de estudiantes por programa
CREATE OR REPLACE VIEW vw_estudiantes_programa AS
SELECT 
    i.id AS inscripcion_id,
    e.id AS estudiante_id,
    e.ci_numero,
    e.nombres || ' ' || e.apellido_paterno || ' ' || COALESCE(e.apellido_materno, '') AS estudiante,
    e.telefono,
    e.email,
    p.id AS programa_id,
    p.codigo AS programa_codigo,
    p.nombre AS programa,
    i.estado AS estado_academico,
    i.fecha_inscripcion,
    COUNT(t.id) AS transacciones_realizadas,
    COALESCE(SUM(t.monto_final), 0) AS total_pagado
FROM inscripciones i
JOIN estudiantes e ON i.estudiante_id = e.id
JOIN programas p ON i.programa_id = p.id
LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id AND i.programa_id = t.programa_id
GROUP BY i.id, e.id, e.ci_numero, e.nombres, e.apellido_paterno, e.apellido_materno, e.telefono, e.email, 
         p.id, p.codigo, p.nombre, i.estado, i.fecha_inscripcion;

-- 8.4 Vista: Resumen financiero diario
CREATE OR REPLACE VIEW vw_resumen_financiero_diario AS
SELECT 
    fecha_pago AS fecha,
    forma_pago,
    COUNT(*) AS cantidad_transacciones,
    SUM(monto_final) AS total_ingresos,
    AVG(monto_final) AS promedio_transaccion
FROM transacciones
WHERE estado = 'CONFIRMADO'
GROUP BY fecha_pago, forma_pago
ORDER BY fecha_pago DESC;

-- 9. PROCEDIMIENTOS ALMACENADOS ÚTILES

-- 9.1 Procedimiento para registrar transacción completa
CREATE OR REPLACE PROCEDURE sp_registrar_transaccion_completa(
    p_estudiante_id INTEGER,
    p_programa_id INTEGER,
    p_fecha_pago DATE,
    p_forma_pago d_forma_pago,
    p_registrado_por INTEGER,
    p_detalles JSONB,
    p_descuento_total DECIMAL(10,2) DEFAULT 0,
    p_numero_comprobante VARCHAR(50) DEFAULT NULL,
    p_banco_origen VARCHAR(100) DEFAULT NULL,
    p_cuenta_origen VARCHAR(50) DEFAULT NULL,
    p_observaciones TEXT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_transaccion_id INTEGER;
    v_detalle JSONB;
    v_concepto_id INTEGER;
    v_descripcion TEXT;
    v_cantidad INTEGER;
    v_precio_unitario DECIMAL(10,2);
    v_subtotal DECIMAL(10,2);
    v_orden INTEGER;
BEGIN
    -- Validar que haya detalles
    IF p_detalles IS NULL OR jsonb_array_length(p_detalles) = 0 THEN
        RAISE EXCEPTION 'Debe proporcionar al menos un detalle para la transacción';
    END IF;
    
    -- Insertar transacción principal (sin número de transacción, se genera automáticamente)
    INSERT INTO transacciones (
        estudiante_id, programa_id, fecha_pago, forma_pago, descuento_total,
        numero_comprobante, banco_origen, cuenta_origen, observaciones, registrado_por,
        estado
    ) VALUES (
        p_estudiante_id, p_programa_id, p_fecha_pago, p_forma_pago, p_descuento_total,
        p_numero_comprobante, p_banco_origen, p_cuenta_origen, p_observaciones, p_registrado_por,
        'CONFIRMADO'
    ) RETURNING id INTO v_transaccion_id;
    
    -- Insertar detalles
    FOR v_detalle IN SELECT * FROM jsonb_array_elements(p_detalles)
    LOOP
        -- Extraer valores del JSON
        v_concepto_id := (v_detalle->>'concepto_pago_id')::INTEGER;
        v_descripcion := v_detalle->>'descripcion';
        v_cantidad := COALESCE((v_detalle->>'cantidad')::INTEGER, 1);
        v_precio_unitario := (v_detalle->>'precio_unitario')::DECIMAL(10,2);
        v_subtotal := (v_detalle->>'subtotal')::DECIMAL(10,2);
        v_orden := COALESCE((v_detalle->>'orden')::INTEGER, 0);
        
        -- Validar que el concepto existe
        IF NOT EXISTS (SELECT 1 FROM conceptos_pago WHERE id = v_concepto_id) THEN
            RAISE EXCEPTION 'Concepto de pago con ID % no existe', v_concepto_id;
        END IF;
        
        -- Validar cálculos
        IF v_subtotal != (v_cantidad * v_precio_unitario) THEN
            RAISE EXCEPTION 'El subtotal no coincide con cantidad * precio unitario';
        END IF;
        
        -- Insertar detalle
        INSERT INTO detalles_transaccion (
            transaccion_id, concepto_pago_id, descripcion, 
            cantidad, precio_unitario, subtotal, orden
        ) VALUES (
            v_transaccion_id,
            v_concepto_id,
            v_descripcion,
            v_cantidad,
            v_precio_unitario,
            v_subtotal,
            v_orden
        );
    END LOOP;
    
    RAISE NOTICE 'Transacción % registrada exitosamente', v_transaccion_id;
END;
$$;

-- 9.2 Función para obtener saldo pendiente por estudiante
CREATE OR REPLACE FUNCTION fn_saldo_pendiente_estudiante(p_estudiante_id INTEGER)
RETURNS TABLE(
    programa_id INTEGER,
    programa_nombre VARCHAR(200),
    total_debe DECIMAL(10,2),
    total_pagado DECIMAL(10,2),
    saldo_pendiente DECIMAL(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id,
        p.nombre,
        p.costo_total,
        COALESCE(SUM(t.monto_final), 0),
        p.costo_total - COALESCE(SUM(t.monto_final), 0)
    FROM inscripciones i
    JOIN programas p ON i.programa_id = p.id
    LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id AND i.programa_id = t.programa_id AND t.estado = 'CONFIRMADO'
    WHERE i.estudiante_id = p_estudiante_id
    GROUP BY p.id, p.nombre, p.costo_total;
END;
$$ LANGUAGE plpgsql;

-- 10. VERIFICACIÓN FINAL
DO $$
BEGIN
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'BASE DE DATOS REDISEÑADA EXITOSAMENTE';
    RAISE NOTICE 'Versión: 2.0.0 - Estructura Simplificada';
    RAISE NOTICE '=========================================';
    RAISE NOTICE 'Tablas creadas: %', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE 'Vistas creadas: %', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'public');
    RAISE NOTICE 'Funciones creadas: %', (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'public');
    RAISE NOTICE 'Triggers creados: %', (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'public');
    RAISE NOTICE '=========================================';
END $$;

-- Mostrar estructura final
SELECT 
    table_name AS "Tabla",
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) AS "Columnas",
    (SELECT COUNT(*) FROM information_schema.table_constraints 
        WHERE table_name = t.table_name AND constraint_type = 'FOREIGN KEY') AS "FKs"
FROM information_schema.tables t
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;