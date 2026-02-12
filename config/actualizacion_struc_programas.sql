-- ============================================================================
-- SCRIPT DE ACTUALIZACIÓN DE PROGRAMA ACADÉMICO UNSXX
-- Versión: 1.0.0
-- Fecha: 2024
-- Descripción: Actualiza tabla 'programas' eliminando campos de promoción
-- ============================================================================

-- ==================== PRIMERO: VALIDAR EXISTENCIA DE CAMPOS =================
DO $$
DECLARE
    column_exists BOOLEAN;
BEGIN
    -- Verificar si la columna promocion_descuento existe
    SELECT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'programas' 
        AND column_name = 'promocion_descuento'
        AND table_schema = 'public'
    ) INTO column_exists;
    
    IF column_exists THEN
        RAISE NOTICE '✅ Campos de promoción detectados. Procediendo con actualización...';
    ELSE
        RAISE NOTICE '✅ La tabla ya está actualizada. No se requieren cambios.';
    END IF;
END $$;

-- ==================== SEGUNDO: ELIMINAR CAMPOS DE PROMOCIÓN =================
-- Nota: Los comandos ALTER TABLE se ejecutarán condicionalmente en Tarea 2

-- Comandos para eliminar campos (se ejecutarán solo si existen):
-- 1. ALTER TABLE programas DROP COLUMN IF EXISTS promocion_descuento;
-- 2. ALTER TABLE programas DROP COLUMN IF EXISTS promocion_descripcion;
-- 3. ALTER TABLE programas DROP COLUMN IF EXISTS promocion_valido_hasta;

-- ==================== TERCERO: ACTUALIZAR FUNCIONES ========================

-- ========== FUNCIÓN fn_insertar_programa (NUEVA VERSIÓN) ==========
CREATE OR REPLACE FUNCTION public.fn_insertar_programa(
    p_codigo VARCHAR(20),
    p_nombre VARCHAR(200),
    p_duracion_meses INTEGER,
    p_horas_totales INTEGER,
    p_costo_total NUMERIC(10,2),
    p_costo_mensualidad NUMERIC(10,2),
    p_descripcion TEXT DEFAULT NULL,
    p_costo_matricula NUMERIC(10,2) DEFAULT 0,
    p_costo_inscripcion NUMERIC(10,2) DEFAULT 0,
    p_numero_cuotas INTEGER DEFAULT 1,
    p_cupos_maximos INTEGER DEFAULT NULL,
    p_cupos_inscritos INTEGER DEFAULT 0,
    p_estado d_estado_programa DEFAULT 'PLANIFICADO',
    p_fecha_inicio DATE DEFAULT NULL,
    p_fecha_fin DATE DEFAULT NULL,
    p_docente_coordinador_id INTEGER DEFAULT NULL
)
RETURNS TABLE(nuevo_id INTEGER, mensaje VARCHAR, exito BOOLEAN) 
LANGUAGE plpgsql
AS $$
DECLARE
    v_nuevo_id INTEGER;
    v_mensaje VARCHAR;
    v_exito BOOLEAN;
    v_fecha_fin_calculada DATE;
BEGIN
    -- Inicializar variables
    v_nuevo_id := NULL;
    v_mensaje := '';
    v_exito := FALSE;
    
    -- Validar código único
    IF fn_verificar_codigo_programa_existente(p_codigo) THEN
        v_mensaje := 'El código de programa ya está registrado en el sistema';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar duración positiva
    IF p_duracion_meses <= 0 THEN
        v_mensaje := 'La duración en meses debe ser mayor a 0';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar horas totales positivas
    IF p_horas_totales <= 0 THEN
        v_mensaje := 'Las horas totales deben ser mayores a 0';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar costos positivos
    IF p_costo_total < 0 OR p_costo_matricula < 0 OR p_costo_inscripcion < 0 OR p_costo_mensualidad < 0 THEN
        v_mensaje := 'Todos los costos deben ser positivos o cero';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar número de cuotas positivo
    IF p_numero_cuotas <= 0 THEN
        v_mensaje := 'El número de cuotas debe ser mayor a 0';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar cupos máximos vs inscritos
    IF p_cupos_maximos IS NOT NULL AND p_cupos_inscritos > p_cupos_maximos THEN
        v_mensaje := 'Los cupos inscritos no pueden exceder los cupos máximos';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar fechas si se proporcionan
    IF p_fecha_inicio IS NOT NULL AND p_fecha_fin IS NOT NULL AND p_fecha_fin < p_fecha_inicio THEN
        v_mensaje := 'La fecha de fin no puede ser anterior a la fecha de inicio';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar docente coordinador existe si se proporciona
    IF p_docente_coordinador_id IS NOT NULL AND NOT EXISTS(
        SELECT 1 FROM docentes WHERE id = p_docente_coordinador_id
    ) THEN
        v_mensaje := 'El docente coordinador no existe';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Calcular fecha fin si no se proporciona y hay fecha inicio
    IF p_fecha_inicio IS NOT NULL AND p_fecha_fin IS NULL THEN
        v_fecha_fin_calculada := p_fecha_inicio + (p_duracion_meses * INTERVAL '1 month');
    ELSE
        v_fecha_fin_calculada := p_fecha_fin;
    END IF;
    
    -- Insertar programa (SIN campos de promoción)
    INSERT INTO programas (
        codigo, nombre, descripcion, duracion_meses, horas_totales,
        costo_total, costo_matricula, costo_inscripcion, costo_mensualidad,
        numero_cuotas, cupos_maximos, cupos_inscritos, estado,
        fecha_inicio, fecha_fin, docente_coordinador_id
        -- NOTA: Se omiten promocion_descuento, promocion_descripcion, promocion_valido_hasta
    ) VALUES (
        p_codigo, p_nombre, p_descripcion, p_duracion_meses, p_horas_totales,
        p_costo_total, p_costo_matricula, p_costo_inscripcion, p_costo_mensualidad,
        p_numero_cuotas, p_cupos_maximos, p_cupos_inscritos, p_estado,
        p_fecha_inicio, v_fecha_fin_calculada, p_docente_coordinador_id
    ) RETURNING id INTO v_nuevo_id;
    
    v_mensaje := 'Programa creado exitosamente con ID: ' || v_nuevo_id;
    v_exito := TRUE;
    
    RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al crear programa: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
END;
$$;

-- ========== FUNCIÓN fn_actualizar_programa (NUEVA VERSIÓN) ==========
CREATE OR REPLACE FUNCTION public.fn_actualizar_programa(
    p_id INTEGER,
    p_codigo VARCHAR(20),
    p_nombre VARCHAR(200),
    p_duracion_meses INTEGER,
    p_horas_totales INTEGER,
    p_costo_total NUMERIC(10,2),
    p_costo_mensualidad NUMERIC(10,2),
    p_descripcion TEXT DEFAULT NULL,
    p_costo_matricula NUMERIC(10,2) DEFAULT NULL,
    p_costo_inscripcion NUMERIC(10,2) DEFAULT NULL,
    p_numero_cuotas INTEGER DEFAULT NULL,
    p_cupos_maximos INTEGER DEFAULT NULL,
    p_cupos_inscritos INTEGER DEFAULT NULL,
    p_estado d_estado_programa DEFAULT NULL,
    p_fecha_inicio DATE DEFAULT NULL,
    p_fecha_fin DATE DEFAULT NULL,
    p_docente_coordinador_id INTEGER DEFAULT NULL
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
    
    -- Actualizar programa (SIN campos de promoción)
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
        -- NOTA: Se omiten promocion_descuento, promocion_descripcion, promocion_valido_hasta
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

-- ========== FUNCIÓN fn_obtener_programa_por_id (NUEVA VERSIÓN) ==========
CREATE OR REPLACE FUNCTION public.fn_obtener_programa_por_id(p_id INTEGER)
RETURNS TABLE(
    id INTEGER, 
    codigo VARCHAR(20), 
    nombre VARCHAR(200), 
    descripcion TEXT, 
    duracion_meses INTEGER, 
    horas_totales INTEGER, 
    costo_total NUMERIC(10,2), 
    costo_matricula NUMERIC(10,2), 
    costo_inscripcion NUMERIC(10,2), 
    costo_mensualidad NUMERIC(10,2), 
    numero_cuotas INTEGER, 
    cupos_maximos INTEGER, 
    cupos_inscritos INTEGER, 
    estado d_estado_programa, 
    fecha_inicio DATE, 
    fecha_fin DATE, 
    docente_coordinador_id INTEGER,
    created_at TIMESTAMP, 
    updated_at TIMESTAMP
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id, p.codigo, p.nombre, p.descripcion, p.duracion_meses, p.horas_totales,
        p.costo_total, p.costo_matricula, p.costo_inscripcion, p.costo_mensualidad,
        p.numero_cuotas, p.cupos_maximos, p.cupos_inscritos, p.estado,
        p.fecha_inicio, p.fecha_fin, p.docente_coordinador_id,
        p.created_at, p.updated_at
        -- NOTA: Se omiten promocion_descuento, promocion_descripcion, promocion_valido_hasta
    FROM programas p
    WHERE p.id = p_id;
END;
$$;

-- ========== FUNCIÓN fn_buscar_programas (NUEVA VERSIÓN) ==========
CREATE OR REPLACE FUNCTION public.fn_buscar_programas(
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
    codigo VARCHAR(20), 
    nombre VARCHAR(200), 
    descripcion TEXT, 
    duracion_meses INTEGER, 
    horas_totales INTEGER, 
    costo_total NUMERIC(10,2), 
    costo_matricula NUMERIC(10,2), 
    costo_inscripcion NUMERIC(10,2), 
    costo_mensualidad NUMERIC(10,2), 
    numero_cuotas INTEGER, 
    cupos_maximos INTEGER, 
    cupos_inscritos INTEGER, 
    estado d_estado_programa, 
    fecha_inicio DATE, 
    fecha_fin DATE, 
    docente_coordinador_id INTEGER,
    created_at TIMESTAMP, 
    updated_at TIMESTAMP
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id, p.codigo, p.nombre, p.descripcion, p.duracion_meses, p.horas_totales,
        p.costo_total, p.costo_matricula, p.costo_inscripcion, p.costo_mensualidad,
        p.numero_cuotas, p.cupos_maximos, p.cupos_inscritos, p.estado,
        p.fecha_inicio, p.fecha_fin, p.docente_coordinador_id,
        p.created_at, p.updated_at
        -- NOTA: Se omiten promocion_descuento, promocion_descripcion, promocion_valido_hasta
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
$$;

-- ========== FUNCIÓN fn_contar_programas (SE MANTIENE IGUAL) ==========
-- Esta función no necesita cambios ya que no selecciona campos específicos

-- ==================== CUARTO: VERIFICAR INTEGRIDAD ========================
DO $$
BEGIN
    RAISE NOTICE '============================================';
    RAISE NOTICE '✅ Actualización de funciones completada';
    RAISE NOTICE '============================================';
END $$;