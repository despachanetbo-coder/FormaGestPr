-- ============================================================
-- FUNCIONES Y PROCEDIMIENTOS ALMACENADOS PARA CRUD DE PROGRAMAS
-- ============================================================

-- 3.1 Función para buscar programas con filtros
CREATE OR REPLACE FUNCTION fn_buscar_programas(
    p_codigo VARCHAR DEFAULT NULL,
    p_nombre VARCHAR DEFAULT NULL,
    p_estado d_estado_programa DEFAULT NULL,
    p_docente_coordinador_id INTEGER DEFAULT NULL,
    p_fecha_inicio_desde DATE DEFAULT NULL,
    p_fecha_inicio_hasta DATE DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE(
    id INTEGER,
    codigo VARCHAR,
    nombre VARCHAR,
    descripcion TEXT,
    duracion_meses INTEGER,
    horas_totales INTEGER,
    costo_total DECIMAL,
    costo_matricula DECIMAL,
    costo_inscripcion DECIMAL,
    costo_mensualidad DECIMAL,
    numero_cuotas INTEGER,
    cupos_maximos INTEGER,
    cupos_inscritos INTEGER,
    estado d_estado_programa,
    fecha_inicio DATE,
    fecha_fin DATE,
    docente_coordinador_id INTEGER,
    promocion_descuento DECIMAL,
    promocion_descripcion TEXT,
    promocion_valido_hasta DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id, p.codigo, p.nombre, p.descripcion, p.duracion_meses, p.horas_totales,
        p.costo_total, p.costo_matricula, p.costo_inscripcion, p.costo_mensualidad,
        p.numero_cuotas, p.cupos_maximos, p.cupos_inscritos, p.estado,
        p.fecha_inicio, p.fecha_fin, p.docente_coordinador_id,
        p.promocion_descuento, p.promocion_descripcion, p.promocion_valido_hasta,
        p.created_at, p.updated_at
    FROM programas p
    WHERE 
        (p_codigo IS NULL OR p.codigo ILIKE '%' || p_codigo || '%')
        AND (p_nombre IS NULL OR p.nombre ILIKE '%' || p_nombre || '%')
        AND (p_estado IS NULL OR p.estado = p_estado)
        AND (p_docente_coordinador_id IS NULL OR p.docente_coordinador_id = p_docente_coordinador_id)
        AND (p_fecha_inicio_desde IS NULL OR p.fecha_inicio >= p_fecha_inicio_desde)
        AND (p_fecha_inicio_hasta IS NULL OR p.fecha_inicio <= p_fecha_inicio_hasta)
    ORDER BY p.codigo, p.nombre
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 3.2 Función para contar programas con filtros
CREATE OR REPLACE FUNCTION fn_contar_programas(
    p_codigo VARCHAR DEFAULT NULL,
    p_nombre VARCHAR DEFAULT NULL,
    p_estado d_estado_programa DEFAULT NULL,
    p_docente_coordinador_id INTEGER DEFAULT NULL,
    p_fecha_inicio_desde DATE DEFAULT NULL,
    p_fecha_inicio_hasta DATE DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_total INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_total
    FROM programas p
    WHERE 
        (p_codigo IS NULL OR p.codigo ILIKE '%' || p_codigo || '%')
        AND (p_nombre IS NULL OR p.nombre ILIKE '%' || p_nombre || '%')
        AND (p_estado IS NULL OR p.estado = p_estado)
        AND (p_docente_coordinador_id IS NULL OR p.docente_coordinador_id = p_docente_coordinador_id)
        AND (p_fecha_inicio_desde IS NULL OR p.fecha_inicio >= p_fecha_inicio_desde)
        AND (p_fecha_inicio_hasta IS NULL OR p.fecha_inicio <= p_fecha_inicio_hasta);
    
    RETURN COALESCE(v_total, 0);
END;
$$ LANGUAGE plpgsql;

-- 3.3 Función para obtener programa por ID
CREATE OR REPLACE FUNCTION fn_obtener_programa_por_id(p_id INTEGER)
RETURNS TABLE(
    id INTEGER,
    codigo VARCHAR,
    nombre VARCHAR,
    descripcion TEXT,
    duracion_meses INTEGER,
    horas_totales INTEGER,
    costo_total DECIMAL,
    costo_matricula DECIMAL,
    costo_inscripcion DECIMAL,
    costo_mensualidad DECIMAL,
    numero_cuotas INTEGER,
    cupos_maximos INTEGER,
    cupos_inscritos INTEGER,
    estado d_estado_programa,
    fecha_inicio DATE,
    fecha_fin DATE,
    docente_coordinador_id INTEGER,
    promocion_descuento DECIMAL,
    promocion_descripcion TEXT,
    promocion_valido_hasta DATE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id, p.codigo, p.nombre, p.descripcion, p.duracion_meses, p.horas_totales,
        p.costo_total, p.costo_matricula, p.costo_inscripcion, p.costo_mensualidad,
        p.numero_cuotas, p.cupos_maximos, p.cupos_inscritos, p.estado,
        p.fecha_inicio, p.fecha_fin, p.docente_coordinador_id,
        p.promocion_descuento, p.promocion_descripcion, p.promocion_valido_hasta,
        p.created_at, p.updated_at
    FROM programas p
    WHERE p.id = p_id;
END;
$$ LANGUAGE plpgsql;

-- 3.4 Función para verificar si código ya existe (para validación)
CREATE OR REPLACE FUNCTION fn_verificar_codigo_programa_existente(
    p_codigo VARCHAR,
    p_excluir_id INTEGER DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_existe BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 
        FROM programas 
        WHERE codigo = p_codigo 
        AND (p_excluir_id IS NULL OR id != p_excluir_id)
    ) INTO v_existe;
    
    RETURN v_existe;
END;
$$ LANGUAGE plpgsql;

-- 3.5 Función para insertar nuevo programa
CREATE OR REPLACE FUNCTION public.fn_insertar_programa_simple(
    p_codigo VARCHAR,
    p_nombre VARCHAR,
    p_duracion_meses INTEGER,
    p_horas_totales INTEGER,
    p_costo_total NUMERIC,
    p_costo_mensualidad NUMERIC,
    p_descripcion TEXT DEFAULT NULL,
    p_costo_matricula NUMERIC DEFAULT 0,
    p_costo_inscripcion NUMERIC DEFAULT 0,
    p_numero_cuotas INTEGER DEFAULT 1,
    p_cupos_maximos INTEGER DEFAULT NULL,
    p_cupos_inscritos INTEGER DEFAULT 0,
    p_estado VARCHAR DEFAULT 'PLANIFICADO',
    p_fecha_inicio DATE DEFAULT NULL,
    p_fecha_fin DATE DEFAULT NULL
)
RETURNS TABLE(nuevo_id INTEGER, mensaje VARCHAR, exito BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_nuevo_id INTEGER;
BEGIN
    -- Insertar sin validaciones para prueba
    INSERT INTO programas (
        codigo, nombre, descripcion, duracion_meses, horas_totales,
        costo_total, costo_matricula, costo_inscripcion, costo_mensualidad,
        numero_cuotas, cupos_maximos, cupos_inscritos, estado,
        fecha_inicio, fecha_fin, created_at, updated_at
    ) VALUES (
        p_codigo, p_nombre, p_descripcion, p_duracion_meses, p_horas_totales,
        p_costo_total, p_costo_matricula, p_costo_inscripcion, p_costo_mensualidad,
        p_numero_cuotas, p_cupos_maximos, p_cupos_inscritos, p_estado,
        p_fecha_inicio, p_fecha_fin, NOW(), NOW()
    ) RETURNING id INTO v_nuevo_id;
    
    RETURN QUERY SELECT v_nuevo_id, 'Programa creado exitosamente', TRUE;
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN QUERY SELECT NULL::INTEGER, 'Error: ' || SQLERRM, FALSE;
END;
$$;

-- 3.6 Función para actualizar programa
CREATE OR REPLACE FUNCTION fn_actualizar_programa(
    p_id INTEGER,
    p_codigo VARCHAR,
    p_nombre VARCHAR,
    p_duracion_meses INTEGER,
    p_horas_totales INTEGER,
    p_costo_total DECIMAL,
    p_costo_mensualidad DECIMAL,
    p_descripcion TEXT DEFAULT NULL,
    p_costo_matricula DECIMAL DEFAULT NULL,
    p_costo_inscripcion DECIMAL DEFAULT NULL,
    p_numero_cuotas INTEGER DEFAULT NULL,
    p_cupos_maximos INTEGER DEFAULT NULL,
    p_cupos_inscritos INTEGER DEFAULT NULL,
    p_estado d_estado_programa DEFAULT NULL,
    p_fecha_inicio DATE DEFAULT NULL,
    p_fecha_fin DATE DEFAULT NULL,
    p_docente_coordinador_id INTEGER DEFAULT NULL,
    p_promocion_descuento DECIMAL DEFAULT NULL,
    p_promocion_descripcion TEXT DEFAULT NULL,
    p_promocion_valido_hasta DATE DEFAULT NULL
)
RETURNS TABLE(filas_afectadas INTEGER, mensaje VARCHAR, exito BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_filas_afectadas INTEGER;
    v_mensaje VARCHAR;
    v_exito BOOLEAN;
    v_programa_actual RECORD;
    v_fecha_fin_calculada DATE;
BEGIN
    -- Inicializar variables
    v_filas_afectadas := 0;
    v_mensaje := '';
    v_exito := FALSE;
    
    -- Obtener datos actuales del programa
    SELECT * INTO v_programa_actual FROM programas WHERE id = p_id;
    
    IF NOT FOUND THEN
        v_mensaje := 'El programa con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar código único
    IF fn_verificar_codigo_programa_existente(p_codigo, p_id) THEN
        v_mensaje := 'El código de programa ya está registrado en otro programa';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar duración positiva
    IF p_duracion_meses <= 0 THEN
        v_mensaje := 'La duración en meses debe ser mayor a 0';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar horas totales positivas
    IF p_horas_totales <= 0 THEN
        v_mensaje := 'Las horas totales deben ser mayores a 0';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar costos positivos
    IF p_costo_total < 0 OR 
       (p_costo_matricula IS NOT NULL AND p_costo_matricula < 0) OR
       (p_costo_inscripcion IS NOT NULL AND p_costo_inscripcion < 0) OR
       p_costo_mensualidad < 0 THEN
        v_mensaje := 'Todos los costos deben ser positivos o cero';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar número de cuotas positivo
    IF p_numero_cuotas IS NOT NULL AND p_numero_cuotas <= 0 THEN
        v_mensaje := 'El número de cuotas debe ser mayor a 0';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar cupos máximos vs inscritos
    IF p_cupos_maximos IS NOT NULL AND p_cupos_inscritos IS NOT NULL AND p_cupos_inscritos > p_cupos_maximos THEN
        v_mensaje := 'Los cupos inscritos no pueden exceder los cupos máximos';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar descuento de promoción
    IF p_promocion_descuento IS NOT NULL AND (p_promocion_descuento < 0 OR p_promocion_descuento > 100) THEN
        v_mensaje := 'El descuento de promoción debe estar entre 0 y 100';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar fechas si se proporcionan
    IF p_fecha_inicio IS NOT NULL AND p_fecha_fin IS NOT NULL AND p_fecha_fin < p_fecha_inicio THEN
        v_mensaje := 'La fecha de fin no puede ser anterior a la fecha de inicio';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar docente coordinador existe si se proporciona
    IF p_docente_coordinador_id IS NOT NULL AND NOT EXISTS(
        SELECT 1 FROM docentes WHERE id = p_docente_coordinador_id
    ) THEN
        v_mensaje := 'El docente coordinador no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Calcular fecha fin si se actualiza fecha inicio o duración
    IF p_fecha_inicio IS NOT NULL AND p_fecha_fin IS NULL THEN
        v_fecha_fin_calculada := p_fecha_inicio + (p_duracion_meses * INTERVAL '1 month');
    ELSE
        v_fecha_fin_calculada := COALESCE(p_fecha_fin, v_programa_actual.fecha_fin);
    END IF;
    
    -- Actualizar programa
    UPDATE programas
    SET 
        codigo = p_codigo,
        nombre = p_nombre,
        descripcion = COALESCE(p_descripcion, descripcion),
        duracion_meses = p_duracion_meses,
        horas_totales = p_horas_totales,
        costo_total = p_costo_total,
        costo_matricula = COALESCE(p_costo_matricula, costo_matricula),
        costo_inscripcion = COALESCE(p_costo_inscripcion, costo_inscripcion),
        costo_mensualidad = p_costo_mensualidad,
        numero_cuotas = COALESCE(p_numero_cuotas, numero_cuotas),
        cupos_maximos = COALESCE(p_cupos_maximos, cupos_maximos),
        cupos_inscritos = COALESCE(p_cupos_inscritos, cupos_inscritos),
        estado = COALESCE(p_estado, estado),
        fecha_inicio = COALESCE(p_fecha_inicio, fecha_inicio),
        fecha_fin = v_fecha_fin_calculada,
        docente_coordinador_id = COALESCE(p_docente_coordinador_id, docente_coordinador_id),
        promocion_descuento = COALESCE(p_promocion_descuento, promocion_descuento),
        promocion_descripcion = COALESCE(p_promocion_descripcion, promocion_descripcion),
        promocion_valido_hasta = COALESCE(p_promocion_valido_hasta, promocion_valido_hasta),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Programa actualizado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se realizaron cambios en el programa';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al actualizar programa: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- 3.7 Función para eliminar (cambiar estado a 'CANCELADO') programa
CREATE OR REPLACE FUNCTION fn_eliminar_programa(p_id INTEGER)
RETURNS TABLE(filas_afectadas INTEGER, mensaje VARCHAR, exito BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_filas_afectadas INTEGER;
    v_mensaje VARCHAR;
    v_exito BOOLEAN;
BEGIN
    -- Inicializar variables
    v_filas_afectadas := 0;
    v_mensaje := '';
    v_exito := FALSE;
    
    -- Validar que el programa exista
    IF NOT EXISTS(SELECT 1 FROM programas WHERE id = p_id) THEN
        v_mensaje := 'El programa con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar que no tenga estudiantes inscritos (solo si hay cupos inscritos > 0)
    IF EXISTS(SELECT 1 FROM programas WHERE id = p_id AND cupos_inscritos > 0) THEN
        v_mensaje := 'No se puede eliminar un programa con estudiantes inscritos';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- "Eliminar" cambiando estado a CANCELADO (soft delete)
    UPDATE programas
    SET estado = 'CANCELADO', updated_at = CURRENT_TIMESTAMP
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Programa eliminado (cancelado) exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se pudo eliminar el programa';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al eliminar programa: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- 3.8 Función para activar programa (cambiar estado a 'PLANIFICADO')
CREATE OR REPLACE FUNCTION fn_activar_programa(p_id INTEGER)
RETURNS TABLE(filas_afectadas INTEGER, mensaje VARCHAR, exito BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_filas_afectadas INTEGER;
    v_mensaje VARCHAR;
    v_exito BOOLEAN;
BEGIN
    -- Inicializar variables
    v_filas_afectadas := 0;
    v_mensaje := '';
    v_exito := FALSE;
    
    -- Validar que el programa exista
    IF NOT EXISTS(SELECT 1 FROM programas WHERE id = p_id) THEN
        v_mensaje := 'El programa con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Activar programa (cambiar estado a PLANIFICADO)
    UPDATE programas
    SET estado = 'PLANIFICADO', updated_at = CURRENT_TIMESTAMP
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Programa activado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se pudo activar el programa';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al activar programa: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- 3.9 Función para inscribir estudiante a programa (incrementar cupos inscritos)
CREATE OR REPLACE FUNCTION fn_inscribir_estudiante_programa(
    p_programa_id INTEGER,
    p_estudiante_id INTEGER
)
RETURNS TABLE(exito BOOLEAN, mensaje VARCHAR, cupos_disponibles INTEGER)
LANGUAGE plpgsql
AS $$
DECLARE
    v_exito BOOLEAN;
    v_mensaje VARCHAR;
    v_cupos_maximos INTEGER;
    v_cupos_inscritos INTEGER;
    v_cupos_disponibles INTEGER;
BEGIN
    -- Inicializar variables
    v_exito := FALSE;
    v_mensaje := '';
    v_cupos_disponibles := 0;
    
    -- Obtener datos del programa
    SELECT cupos_maximos, cupos_inscritos 
    INTO v_cupos_maximos, v_cupos_inscritos
    FROM programas WHERE id = p_programa_id;
    
    IF NOT FOUND THEN
        v_mensaje := 'El programa no existe';
        RETURN QUERY SELECT v_exito, v_mensaje, v_cupos_disponibles;
        RETURN;
    END IF;
    
    -- Verificar que el programa no esté cancelado
    IF EXISTS(SELECT 1 FROM programas WHERE id = p_programa_id AND estado = 'CANCELADO') THEN
        v_mensaje := 'El programa está cancelado';
        RETURN QUERY SELECT v_exito, v_mensaje, v_cupos_disponibles;
        RETURN;
    END IF;
    
    -- Verificar que haya cupos disponibles (si hay límite)
    IF v_cupos_maximos IS NOT NULL AND v_cupos_inscritos >= v_cupos_maximos THEN
        v_mensaje := 'No hay cupos disponibles en el programa';
        v_cupos_disponibles := 0;
        RETURN QUERY SELECT v_exito, v_mensaje, v_cupos_disponibles;
        RETURN;
    END IF;
    
    -- Verificar que el estudiante no esté ya inscrito (esto depende de otra tabla de inscripciones)
    -- Por ahora solo incrementamos cupos
    UPDATE programas
    SET cupos_inscritos = cupos_inscritos + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_programa_id;
    
    GET DIAGNOSTICS v_cupos_disponibles = ROW_COUNT;
    
    IF v_cupos_disponibles > 0 THEN
        v_mensaje := 'Estudiante inscrito exitosamente';
        v_exito := TRUE;
        
        -- Calcular cupos disponibles restantes
        IF v_cupos_maximos IS NOT NULL THEN
            v_cupos_disponibles := v_cupos_maximos - (v_cupos_inscritos + 1);
        ELSE
            v_cupos_disponibles := -1; -- Indica que no hay límite
        END IF;
    ELSE
        v_mensaje := 'No se pudo inscribir al estudiante';
    END IF;
    
    RETURN QUERY SELECT v_exito, v_mensaje, v_cupos_disponibles;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al inscribir estudiante: ' || SQLERRM;
        RETURN QUERY SELECT v_exito, v_mensaje, v_cupos_disponibles;
END;
$$;

-- 3.10 Función para obtener estadísticas de programas
CREATE OR REPLACE FUNCTION fn_estadisticas_programas()
RETURNS TABLE(
    total_programas INTEGER,
    planificados INTEGER,
    en_curso INTEGER,
    finalizados INTEGER,
    cancelados INTEGER,
    promedio_duracion NUMERIC,
    promedio_costo NUMERIC,
    promedio_cupos_inscritos NUMERIC,
    total_cupos_disponibles BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER AS total_programas,
        COUNT(*) FILTER (WHERE estado = 'PLANIFICADO')::INTEGER AS planificados,
        COUNT(*) FILTER (WHERE estado = 'EN_CURSO')::INTEGER AS en_curso,
        COUNT(*) FILTER (WHERE estado = 'FINALIZADO')::INTEGER AS finalizados,
        COUNT(*) FILTER (WHERE estado = 'CANCELADO')::INTEGER AS cancelados,
        AVG(duracion_meses)::NUMERIC AS promedio_duracion,
        AVG(costo_total)::NUMERIC AS promedio_costo,
        AVG(cupos_inscritos)::NUMERIC AS promedio_cupos_inscritos,
        COALESCE(SUM(GREATEST(cupos_maximos - cupos_inscritos, 0)), 0)::BIGINT AS total_cupos_disponibles
    FROM programas;
END;
$$ LANGUAGE plpgsql;

-- ================================================================
-- FUNCIONES PARA ANÁLISIS DE ESTUDIANTES Y PAGOS EN PROGRAMAS
-- ================================================================

-- 1. OBTENER ESTUDIANTES INSCRITOS A UN PROGRAMA ESPECÍFICO
CREATE OR REPLACE FUNCTION fn_estudiantes_inscritos_programa(
    p_programa_id INTEGER,
    p_activos_only BOOLEAN DEFAULT TRUE
)
RETURNS TABLE(
    estudiante_id INTEGER,
    estudiante_ci VARCHAR(15),
    estudiante_nombre_completo VARCHAR(300),
    estudiante_email VARCHAR(100),
    estudiante_telefono VARCHAR(20),
    fecha_inscripcion DATE,
    estado_academico d_estado_academico,
    programa_nombre VARCHAR(200),
    programa_codigo VARCHAR(20),
    programa_estado d_estado_programa
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id AS estudiante_id,
        e.ci_numero AS estudiante_ci,
        CONCAT(
            e.nombres, ' ', 
            e.apellido_paterno, ' ', 
            COALESCE(e.apellido_materno, '')
        ) AS estudiante_nombre_completo,
        e.email AS estudiante_email,
        e.telefono AS estudiante_telefono,
        i.fecha_inscripcion,
        i.estado AS estado_academico,
        p.nombre AS programa_nombre,
        p.codigo AS programa_codigo,
        p.estado AS programa_estado
    FROM inscripciones i
    INNER JOIN estudiantes e ON i.estudiante_id = e.id
    INNER JOIN programas p ON i.programa_id = p.id
    WHERE i.programa_id = p_programa_id
        AND (p_activos_only = FALSE OR e.activo = TRUE)
        AND (p_activos_only = FALSE OR i.estado != 'RETIRADO')
    ORDER BY e.apellido_paterno, e.apellido_materno, e.nombres;
END;
$$ LANGUAGE plpgsql;

-- 2. SUMA TOTAL PAGADO POR TODOS LOS ESTUDIANTES EN UN PROGRAMA
CREATE OR REPLACE FUNCTION fn_total_pagado_programa(
    p_programa_id INTEGER
)
RETURNS TABLE(
    programa_id INTEGER,
    programa_codigo VARCHAR(20),
    programa_nombre VARCHAR(200),
    total_pagado NUMERIC(12,2),
    costo_total_programa NUMERIC(10,2),
    porcentaje_cobrado NUMERIC(5,2),
    total_estudiantes INTEGER,
    estudiantes_con_pagos INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id AS programa_id,
        p.codigo AS programa_codigo,
        p.nombre AS programa_nombre,
        COALESCE(SUM(t.monto_final), 0) AS total_pagado,
        p.costo_total AS costo_total_programa,
        CASE 
            WHEN p.costo_total > 0 THEN 
                ROUND((COALESCE(SUM(t.monto_final), 0) * 100.0 / p.costo_total), 2)
            ELSE 0 
        END AS porcentaje_cobrado,
        COUNT(DISTINCT i.estudiante_id) AS total_estudiantes,
        COUNT(DISTINCT t.estudiante_id) AS estudiantes_con_pagos
    FROM programas p
    LEFT JOIN inscripciones i ON p.id = i.programa_id
    LEFT JOIN transacciones t ON p.id = t.programa_id 
        AND i.estudiante_id = t.estudiante_id
        AND t.estado = 'CONFIRMADO'
    WHERE p.id = p_programa_id
    GROUP BY p.id, p.codigo, p.nombre, p.costo_total;
END;
$$ LANGUAGE plpgsql;

-- 3. RESUMEN DE PAGOS POR ESTUDIANTE EN UN PROGRAMA
CREATE OR REPLACE FUNCTION fn_resumen_pagos_estudiante_programa(
    p_programa_id INTEGER,
    p_estudiante_id INTEGER DEFAULT NULL
)
RETURNS TABLE(
    estudiante_id INTEGER,
    estudiante_ci VARCHAR(15),
    estudiante_nombre_completo VARCHAR(300),
    programa_codigo VARCHAR(20),
    programa_nombre VARCHAR(200),
    fecha_inscripcion DATE,
    costo_total_programa NUMERIC(10,2),
    total_pagado_estudiante NUMERIC(12,2),
    saldo_pendiente NUMERIC(12,2),
    porcentaje_pagado NUMERIC(5,2),
    numero_transacciones INTEGER,
    ultimo_pago DATE,
    proximo_vencimiento DATE,
    estado_financiero VARCHAR(20)
) AS $$
DECLARE
    v_programa_data RECORD;
    v_numero_cuotas INTEGER;
BEGIN
    -- Obtener datos del programa
    SELECT 
        costo_total,
        numero_cuotas,
        fecha_inicio,
        nombre,
        codigo
    INTO v_programa_data
    FROM programas 
    WHERE id = p_programa_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Programa con ID % no encontrado', p_programa_id;
    END IF;
    
    RETURN QUERY
    SELECT 
        e.id AS estudiante_id,
        e.ci_numero AS estudiante_ci,
        CONCAT(
            e.nombres, ' ', 
            e.apellido_paterno, ' ', 
            COALESCE(e.apellido_materno, '')
        ) AS estudiante_nombre_completo,
        v_programa_data.codigo AS programa_codigo,
        v_programa_data.nombre AS programa_nombre,
        i.fecha_inscripcion,
        v_programa_data.costo_total AS costo_total_programa,
        COALESCE(SUM(t.monto_final), 0) AS total_pagado_estudiante,
        GREATEST(v_programa_data.costo_total - COALESCE(SUM(t.monto_final), 0), 0) AS saldo_pendiente,
        CASE 
            WHEN v_programa_data.costo_total > 0 THEN 
                ROUND((COALESCE(SUM(t.monto_final), 0) * 100.0 / v_programa_data.costo_total), 2)
            ELSE 0 
        END AS porcentaje_pagado,
        COUNT(DISTINCT t.id) AS numero_transacciones,
        MAX(t.fecha_pago) AS ultimo_pago,
        CASE 
            WHEN v_programa_data.numero_cuotas > 0 
                 AND v_programa_data.fecha_inicio IS NOT NULL
                 AND COUNT(DISTINCT t.id) < v_programa_data.numero_cuotas
            THEN (v_programa_data.fecha_inicio + 
                  (COUNT(DISTINCT t.id)) * INTERVAL '1 month')::DATE
            ELSE NULL 
        END AS proximo_vencimiento,
        CASE 
            WHEN COALESCE(SUM(t.monto_final), 0) >= v_programa_data.costo_total THEN 'COMPLETO'
            WHEN COALESCE(SUM(t.monto_final), 0) >= (v_programa_data.costo_total * 0.5) THEN 'PARCIAL'
            WHEN COALESCE(SUM(t.monto_final), 0) > 0 THEN 'INICIAL'
            ELSE 'SIN_PAGOS'
        END::VARCHAR(20) AS estado_financiero
    FROM inscripciones i
    INNER JOIN estudiantes e ON i.estudiante_id = e.id
    LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
        AND i.programa_id = t.programa_id
        AND t.estado = 'CONFIRMADO'
    WHERE i.programa_id = p_programa_id
        AND (p_estudiante_id IS NULL OR e.id = p_estudiante_id)
    GROUP BY 
        e.id, e.ci_numero, e.nombres, e.apellido_paterno, e.apellido_materno,
        i.fecha_inscripcion
    ORDER BY e.apellido_paterno, e.apellido_materno, e.nombres;
END;
$$ LANGUAGE plpgsql;

-- 4. DETALLE DE TRANSACCIONES POR ESTUDIANTE EN UN PROGRAMA
CREATE OR REPLACE FUNCTION fn_detalle_pagos_estudiante_programa(
    p_estudiante_id INTEGER,
    p_programa_id INTEGER
)
RETURNS TABLE(
    transaccion_id INTEGER,
    numero_transaccion VARCHAR(50),
    fecha_pago DATE,
    forma_pago d_forma_pago,
    descripcion_concepto VARCHAR(200),
    cantidad INTEGER,
    precio_unitario NUMERIC(10,2),
    subtotal NUMERIC(10,2),
    descuento_transaccion NUMERIC(10,2),
    monto_final NUMERIC(10,2),
    estado_transaccion d_estado_transaccion,
    numero_comprobante VARCHAR(50),
    registro_usuario VARCHAR(200)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id AS transaccion_id,
        t.numero_transaccion,
        t.fecha_pago,
        t.forma_pago,
        COALESCE(
            STRING_AGG(
                CONCAT(
                    cp.nombre, 
                    CASE WHEN dt.descripcion != cp.nombre 
                         THEN CONCAT(' - ', dt.descripcion) 
                         ELSE '' 
                    END
                ), 
                '; '
            ),
            'Sin detalles'
        ) AS descripcion_concepto,
        SUM(dt.cantidad) AS cantidad,
        ROUND(AVG(dt.precio_unitario), 2) AS precio_unitario,
        SUM(dt.subtotal) AS subtotal,
        t.descuento_total AS descuento_transaccion,
        t.monto_final,
        t.estado AS estado_transaccion,
        t.numero_comprobante,
        u.nombre_completo AS registro_usuario
    FROM transacciones t
    LEFT JOIN detalles_transaccion dt ON t.id = dt.transaccion_id
    LEFT JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
    LEFT JOIN usuarios u ON t.registrado_por = u.id
    WHERE t.estudiante_id = p_estudiante_id
        AND t.programa_id = p_programa_id
        AND t.estado = 'CONFIRMADO'
    GROUP BY 
        t.id, t.numero_transaccion, t.fecha_pago, t.forma_pago,
        t.descuento_total, t.monto_final, t.estado,
        t.numero_comprobante, u.nombre_completo
    ORDER BY t.fecha_pago DESC;
END;
$$ LANGUAGE plpgsql;

-- 5. RESUMEN GLOBAL DE PAGOS PARA TODOS LOS PROGRAMAS
CREATE OR REPLACE FUNCTION fn_resumen_global_pagos_programas()
RETURNS TABLE(
    programa_id INTEGER,
    programa_codigo VARCHAR(20),
    programa_nombre VARCHAR(200),
    programa_estado d_estado_programa,
    estudiantes_inscritos INTEGER,
    estudiantes_con_pagos INTEGER,
    costo_total_programa NUMERIC(10,2),
    total_recaudado NUMERIC(12,2),
    total_pendiente NUMERIC(12,2),
    porcentaje_cobrado NUMERIC(5,2),
    fecha_inicio DATE,
    fecha_fin DATE,
    cupos_inscritos INTEGER,
    cupos_maximos INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id AS programa_id,
        p.codigo AS programa_codigo,
        p.nombre AS programa_nombre,
        p.estado AS programa_estado,
        COUNT(DISTINCT i.estudiante_id) AS estudiantes_inscritos,
        COUNT(DISTINCT CASE WHEN t.estado = 'CONFIRMADO' THEN t.estudiante_id END) AS estudiantes_con_pagos,
        p.costo_total AS costo_total_programa,
        COALESCE(SUM(CASE WHEN t.estado = 'CONFIRMADO' THEN t.monto_final ELSE 0 END), 0) AS total_recaudado,
        GREATEST(
            (p.costo_total * COUNT(DISTINCT i.estudiante_id)) - 
            COALESCE(SUM(CASE WHEN t.estado = 'CONFIRMADO' THEN t.monto_final ELSE 0 END), 0), 
            0
        ) AS total_pendiente,
        CASE 
            WHEN (p.costo_total * COUNT(DISTINCT i.estudiante_id)) > 0 THEN
                ROUND(
                    (COALESCE(SUM(CASE WHEN t.estado = 'CONFIRMADO' THEN t.monto_final ELSE 0 END), 0) * 100.0) / 
                    (p.costo_total * COUNT(DISTINCT i.estudiante_id)), 
                    2
                )
            ELSE 0 
        END AS porcentaje_cobrado,
        p.fecha_inicio,
        p.fecha_fin,
        p.cupos_inscritos,
        p.cupos_maximos
    FROM programas p
    LEFT JOIN inscripciones i ON p.id = i.programa_id
    LEFT JOIN transacciones t ON p.id = t.programa_id 
        AND i.estudiante_id = t.estudiante_id
    WHERE p.estado != 'CANCELADO'
    GROUP BY p.id, p.codigo, p.nombre, p.estado, p.costo_total,
             p.fecha_inicio, p.fecha_fin, p.cupos_inscritos, p.cupos_maximos
    ORDER BY p.codigo;
END;
$$ LANGUAGE plpgsql;

-- 6. TOP 10 ESTUDIANTES CON MAYOR PAGO EN UN PROGRAMA
CREATE OR REPLACE FUNCTION fn_top_estudiantes_pagos_programa(
    p_programa_id INTEGER,
    p_limit INTEGER DEFAULT 10
)
RETURNS TABLE(
    posicion INTEGER,
    estudiante_id INTEGER,
    estudiante_ci VARCHAR(15),
    estudiante_nombre_completo VARCHAR(300),
    total_pagado NUMERIC(12,2),
    porcentaje_pagado NUMERIC(5,2),
    numero_transacciones INTEGER,
    ultimo_pago DATE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ROW_NUMBER() OVER (ORDER BY COALESCE(SUM(t.monto_final), 0) DESC) AS posicion,
        e.id AS estudiante_id,
        e.ci_numero AS estudiante_ci,
        CONCAT(
            e.nombres, ' ', 
            e.apellido_paterno, ' ', 
            COALESCE(e.apellido_materno, '')
        ) AS estudiante_nombre_completo,
        COALESCE(SUM(t.monto_final), 0) AS total_pagado,
        CASE 
            WHEN p.costo_total > 0 THEN 
                ROUND((COALESCE(SUM(t.monto_final), 0) * 100.0 / p.costo_total), 2)
            ELSE 0 
        END AS porcentaje_pagado,
        COUNT(DISTINCT t.id) AS numero_transacciones,
        MAX(t.fecha_pago) AS ultimo_pago
    FROM inscripciones i
    INNER JOIN estudiantes e ON i.estudiante_id = e.id
    INNER JOIN programas p ON i.programa_id = p.id
    LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
        AND i.programa_id = t.programa_id
        AND t.estado = 'CONFIRMADO'
    WHERE i.programa_id = p_programa_id
    GROUP BY e.id, e.ci_numero, e.nombres, e.apellido_paterno, e.apellido_materno, p.costo_total
    ORDER BY total_pagado DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- 7. ESTUDIANTES CON PAGOS PENDIENTES (MOROSOS)
CREATE OR REPLACE FUNCTION fn_estudiantes_morosos_programa(
    p_programa_id INTEGER,
    p_dias_retraso INTEGER DEFAULT 30
)
RETURNS TABLE(
    estudiante_id INTEGER,
    estudiante_ci VARCHAR(15),
    estudiante_nombre_completo VARCHAR(300),
    total_debe NUMERIC(12,2),
    ultimo_pago DATE,
    dias_sin_pagar INTEGER,
    proximo_vencimiento DATE,
    estado VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    WITH pagos_estudiante AS (
        SELECT 
            e.id AS estudiante_id,
            e.ci_numero,
            CONCAT(
                e.nombres, ' ', 
                e.apellido_paterno, ' ', 
                COALESCE(e.apellido_materno, '')
            ) AS nombre_completo,
            p.costo_total,
            p.numero_cuotas,
            p.fecha_inicio,
            COALESCE(SUM(t.monto_final), 0) AS total_pagado,
            MAX(t.fecha_pago) AS ultimo_pago_fecha,
            COUNT(DISTINCT t.id) AS cuotas_pagadas
        FROM inscripciones i
        INNER JOIN estudiantes e ON i.estudiante_id = e.id
        INNER JOIN programas p ON i.programa_id = p.id
        LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
            AND i.programa_id = t.programa_id
            AND t.estado = 'CONFIRMADO'
        WHERE i.programa_id = p_programa_id
        GROUP BY e.id, e.ci_numero, e.nombres, e.apellido_paterno, e.apellido_materno,
                 p.costo_total, p.numero_cuotas, p.fecha_inicio
    )
    SELECT 
        pe.estudiante_id,
        pe.ci_numero AS estudiante_ci,
        pe.nombre_completo AS estudiante_nombre_completo,
        GREATEST(pe.costo_total - pe.total_pagado, 0) AS total_debe,
        pe.ultimo_pago_fecha AS ultimo_pago,
        CASE 
            WHEN pe.ultimo_pago_fecha IS NULL THEN 
                EXTRACT(DAY FROM CURRENT_DATE - pe.fecha_inicio)
            ELSE 
                EXTRACT(DAY FROM CURRENT_DATE - pe.ultimo_pago_fecha)
        END::INTEGER AS dias_sin_pagar,
        CASE 
            WHEN pe.numero_cuotas > pe.cuotas_pagadas 
                 AND pe.fecha_inicio IS NOT NULL
            THEN (pe.fecha_inicio + 
                  (pe.cuotas_pagadas) * INTERVAL '1 month')::DATE
            ELSE NULL 
        END AS proximo_vencimiento,
        CASE 
            WHEN GREATEST(pe.costo_total - pe.total_pagado, 0) = 0 THEN 'AL_DIA'
            WHEN EXTRACT(DAY FROM CURRENT_DATE - COALESCE(pe.ultimo_pago_fecha, pe.fecha_inicio)) > p_dias_retraso 
                 AND pe.cuotas_pagadas < pe.numero_cuotas THEN 'MOROSO'
            WHEN pe.cuotas_pagadas < pe.numero_cuotas THEN 'PENDIENTE'
            ELSE 'REGULAR'
        END::VARCHAR(20) AS estado
    FROM pagos_estudiante pe
    WHERE GREATEST(pe.costo_total - pe.total_pagado, 0) > 0
    ORDER BY dias_sin_pagar DESC, total_debe DESC;
END;
$$ LANGUAGE plpgsql;

-- 8. HISTORIAL MENSUAL DE PAGOS POR PROGRAMA
CREATE OR REPLACE FUNCTION fn_historial_pagos_mensual_programa(
    p_programa_id INTEGER,
    p_ano INTEGER DEFAULT EXTRACT(YEAR FROM CURRENT_DATE),
    p_mes INTEGER DEFAULT EXTRACT(MONTH FROM CURRENT_DATE)
)
RETURNS TABLE(
    fecha DATE,
    estudiante_id INTEGER,
    estudiante_nombre VARCHAR(300),
    forma_pago d_forma_pago,
    concepto VARCHAR(100),
    monto NUMERIC(10,2),
    descuento NUMERIC(10,2),
    neto_pagado NUMERIC(10,2),
    usuario_registro VARCHAR(200)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.fecha_pago AS fecha,
        e.id AS estudiante_id,
        CONCAT(
            e.nombres, ' ', 
            e.apellido_paterno, ' ', 
            COALESCE(e.apellido_materno, '')
        ) AS estudiante_nombre,
        t.forma_pago,
        cp.nombre AS concepto,
        dt.precio_unitario * dt.cantidad AS monto,
        ROUND(
            (dt.subtotal * t.descuento_total / NULLIF(t.monto_total, 0)), 
            2
        ) AS descuento,
        dt.subtotal - ROUND(
            (dt.subtotal * t.descuento_total / NULLIF(t.monto_total, 0)), 
            2
        ) AS neto_pagado,
        u.nombre_completo AS usuario_registro
    FROM transacciones t
    INNER JOIN detalles_transaccion dt ON t.id = dt.transaccion_id
    INNER JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
    INNER JOIN estudiantes e ON t.estudiante_id = e.id
    INNER JOIN usuarios u ON t.registrado_por = u.id
    WHERE t.programa_id = p_programa_id
        AND t.estado = 'CONFIRMADO'
        AND EXTRACT(YEAR FROM t.fecha_pago) = p_ano
        AND EXTRACT(MONTH FROM t.fecha_pago) = p_mes
    ORDER BY t.fecha_pago, e.apellido_paterno, e.apellido_materno, e.nombres;
END;
$$ LANGUAGE plpgsql;

