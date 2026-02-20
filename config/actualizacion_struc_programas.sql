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


-- ==================== QUINTO: MODIFICAR TABLA INSCRIPCIONES =======================
ALTER TABLE inscripciones
DROP COLUMN IF EXISTS descuento_aplicado,
ADD COLUMN IF NOT EXISTS valor_final NUMERIC(10,2) DEFAULT 0;


-- Eliminar la función anterior si existe
DROP FUNCTION IF EXISTS fn_crear_inscripcion(INT, INT, FLOAT, TEXT, DATE);

-- Crear la nueva función con valor_final
CREATE OR REPLACE FUNCTION fn_crear_inscripcion(
    p_estudiante_id INT,
    p_programa_id INT,
    p_valor_final NUMERIC(10,2),
    p_observaciones TEXT,
    p_fecha_inscripcion DATE DEFAULT CURRENT_DATE
)
RETURNS JSON AS $$
DECLARE
    v_inscripcion_id INT;
    v_costo_total NUMERIC(10,2);
    v_resultado JSON;
BEGIN
    -- Obtener el costo total del programa
    SELECT costo_total INTO v_costo_total
    FROM programas
    WHERE id = p_programa_id;
    
    -- Validar que el valor final no sea mayor al costo total
    IF p_valor_final > v_costo_total THEN
        RETURN json_build_object(
            'success', false,
            'message', format('El valor final (%s) no puede ser mayor al costo total del programa (%s)', 
                            p_valor_final, v_costo_total)
        );
    END IF;
    
    -- Insertar la nueva inscripción
    INSERT INTO inscripciones (
        estudiante_id,
        programa_id,
        fecha_inscripcion,
        valor_final,
        observaciones,
        estado
    ) VALUES (
        p_estudiante_id,
        p_programa_id,
        COALESCE(p_fecha_inscripcion, CURRENT_DATE),
        p_valor_final,
        p_observaciones,
        'PREINSCRITO'
    )
    RETURNING id INTO v_inscripcion_id;
    
    -- Actualizar contador de cupos
    UPDATE programas 
    SET cupos_inscritos = cupos_inscritos + 1
    WHERE id = p_programa_id;
    
    -- Retornar éxito
    v_resultado := json_build_object(
        'success', true,
        'id', v_inscripcion_id,
        'message', 'Inscripción creada exitosamente'
    );
    
    RETURN v_resultado;
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- CORRECCIÓN COMPLETA: Reemplazar descuento_aplicado por valor_final
-- =====================================================

-- 1. Actualizar función fn_obtener_detalle_inscripcion
DROP FUNCTION IF EXISTS fn_obtener_detalle_inscripcion(INT);

CREATE OR REPLACE FUNCTION fn_obtener_detalle_inscripcion(p_inscripcion_id INT)
RETURNS JSON AS $$
DECLARE
    v_resultado JSON;
BEGIN
    SELECT json_build_object(
        'inscripcion', json_build_object(
            'id', i.id,
            'fecha_inscripcion', i.fecha_inscripcion,
            'estado', i.estado,
            'valor_final', i.valor_final,
            'observaciones', i.observaciones,
            'created_at', i.created_at
        ),
        'estudiante', json_build_object(
            'id', e.id,
            'ci_completo', e.ci_numero || ' ' || e.ci_expedicion,
            'nombres_completos', e.nombres || ' ' || e.apellido_paterno || ' ' || COALESCE(e.apellido_materno, ''),
            'telefono', e.telefono,
            'email', e.email,
            'profesion', e.profesion
        ),
        'programa', json_build_object(
            'id', p.id,
            'codigo', p.codigo,
            'nombre', p.nombre,
            'duracion_meses', p.duracion_meses,
            'horas_totales', p.horas_totales,
            'costo_total', p.costo_total,
            'costo_matricula', p.costo_matricula,
            'costo_inscripcion', p.costo_inscripcion,
            'fecha_inicio', p.fecha_inicio,
            'fecha_fin', p.fecha_fin,
            'cupos_disponibles', p.cupos_maximos - p.cupos_inscritos
        ),
        'pagos', COALESCE((
            SELECT json_agg(json_build_object(
                'id', t.id,
                'numero_transaccion', t.numero_transaccion,
                'fecha_pago', t.fecha_pago,
                'monto_total', t.monto_total,
                'descuento_total', t.descuento_total,
                'monto_final', t.monto_final,
                'forma_pago', t.forma_pago,
                'estado', t.estado,
                'detalles', (
                    SELECT json_agg(json_build_object(
                        'concepto', cp.nombre,
                        'cantidad', dt.cantidad,
                        'precio_unitario', dt.precio_unitario,
                        'subtotal', dt.subtotal
                    ))
                    FROM detalles_transaccion dt
                    JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
                    WHERE dt.transaccion_id = t.id
                )
            ))
            FROM transacciones t
            WHERE t.estudiante_id = i.estudiante_id
            AND t.programa_id = i.programa_id
            AND t.estado = 'CONFIRMADO'
        ), '[]'::JSON),
        'documentos', COALESCE((
            SELECT json_agg(json_build_object(
                'id', dr.id,
                'tipo_documento', dr.tipo_documento,
                'nombre_original', dr.nombre_original,
                'nombre_archivo', dr.nombre_archivo,
                'extension', dr.extension,
                'tamano_bytes', dr.tamano_bytes,
                'fecha_subida', dr.fecha_subida
            ))
            FROM documentos_respaldo dr
            JOIN transacciones t ON dr.transaccion_id = t.id
            WHERE t.estudiante_id = i.estudiante_id
            AND t.programa_id = i.programa_id
        ), '[]'::JSON),
        'saldo', i.valor_final - COALESCE((
            SELECT SUM(t.monto_final)
            FROM transacciones t
            WHERE t.estudiante_id = i.estudiante_id
            AND t.programa_id = i.programa_id
            AND t.estado = 'CONFIRMADO'
        ), 0)
    ) INTO v_resultado
    FROM inscripciones i
    JOIN estudiantes e ON i.estudiante_id = e.id
    JOIN programas p ON i.programa_id = p.id
    WHERE i.id = p_inscripcion_id;
    
    RETURN v_resultado;
END;
$$ LANGUAGE plpgsql;

-- 2. Actualizar función fn_crear_inscripcion
DROP FUNCTION IF EXISTS fn_crear_inscripcion(INT, INT, FLOAT, TEXT, DATE);

CREATE OR REPLACE FUNCTION fn_crear_inscripcion(
    p_estudiante_id INT,
    p_programa_id INT,
    p_valor_final NUMERIC(10,2),
    p_observaciones TEXT,
    p_fecha_inscripcion DATE DEFAULT CURRENT_DATE
)
RETURNS JSON AS $$
DECLARE
    v_inscripcion_id INT;
    v_costo_total NUMERIC(10,2);
    v_resultado JSON;
BEGIN
    -- Obtener el costo total del programa
    SELECT costo_total INTO v_costo_total
    FROM programas
    WHERE id = p_programa_id;
    
    -- Validar que el valor final no sea mayor al costo total
    IF p_valor_final > v_costo_total THEN
        RETURN json_build_object(
            'success', false,
            'message', format('El valor final (%s) no puede ser mayor al costo total del programa (%s)', 
                            p_valor_final, v_costo_total)
        );
    END IF;
    
    -- Insertar la nueva inscripción
    INSERT INTO inscripciones (
        estudiante_id,
        programa_id,
        fecha_inscripcion,
        valor_final,
        observaciones,
        estado
    ) VALUES (
        p_estudiante_id,
        p_programa_id,
        COALESCE(p_fecha_inscripcion, CURRENT_DATE),
        p_valor_final,
        p_observaciones,
        'PREINSCRITO'
    )
    RETURNING id INTO v_inscripcion_id;
    
    -- Actualizar contador de cupos
    UPDATE programas 
    SET cupos_inscritos = cupos_inscritos + 1
    WHERE id = p_programa_id;
    
    -- Retornar éxito
    v_resultado := json_build_object(
        'success', true,
        'id', v_inscripcion_id,
        'message', 'Inscripción creada exitosamente'
    );
    
    RETURN v_resultado;
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- 3. Actualizar función fn_crear_inscripcion_retroactiva
DROP FUNCTION IF EXISTS fn_crear_inscripcion_retroactiva(INT, INT, DATE, FLOAT, TEXT);

CREATE OR REPLACE FUNCTION fn_crear_inscripcion_retroactiva(
    p_estudiante_id INT,
    p_programa_id INT,
    p_fecha_inscripcion DATE,
    p_valor_final NUMERIC(10,2),
    p_observaciones TEXT
)
RETURNS JSON AS $$
DECLARE
    v_inscripcion_id INT;
    v_costo_total NUMERIC(10,2);
    v_resultado JSON;
BEGIN
    -- Obtener el costo total del programa
    SELECT costo_total INTO v_costo_total
    FROM programas
    WHERE id = p_programa_id;
    
    -- Validar que el valor final no sea mayor al costo total
    IF p_valor_final > v_costo_total THEN
        RETURN json_build_object(
            'success', false,
            'message', format('El valor final (%s) no puede ser mayor al costo total del programa (%s)', 
                            p_valor_final, v_costo_total)
        );
    END IF;
    
    -- Insertar la nueva inscripción
    INSERT INTO inscripciones (
        estudiante_id,
        programa_id,
        fecha_inscripcion,
        valor_final,
        observaciones,
        estado
    ) VALUES (
        p_estudiante_id,
        p_programa_id,
        p_fecha_inscripcion,
        p_valor_final,
        p_observaciones,
        'PREINSCRITO'
    )
    RETURNING id INTO v_inscripcion_id;
    
    -- Actualizar contador de cupos
    UPDATE programas 
    SET cupos_inscritos = cupos_inscritos + 1
    WHERE id = p_programa_id;
    
    -- Retornar éxito
    v_resultado := json_build_object(
        'success', true,
        'id', v_inscripcion_id,
        'message', 'Inscripción retroactiva creada exitosamente'
    );
    
    RETURN v_resultado;
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- 4. Actualizar función fn_actualizar_inscripcion
DROP FUNCTION IF EXISTS fn_actualizar_inscripcion(INT, TEXT, FLOAT, TEXT);

CREATE OR REPLACE FUNCTION fn_actualizar_inscripcion(
    p_inscripcion_id INT,
    p_nuevo_estado TEXT DEFAULT NULL,
    p_nuevo_valor_final NUMERIC(10,2) DEFAULT NULL,
    p_nuevas_observaciones TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_resultado JSON;
BEGIN
    UPDATE inscripciones
    SET 
        estado = COALESCE(p_nuevo_estado, estado),
        valor_final = COALESCE(p_nuevo_valor_final, valor_final),
        observaciones = COALESCE(p_nuevas_observaciones, observaciones)
    WHERE id = p_inscripcion_id;
    
    GET DIAGNOSTICS v_resultado = ROW_COUNT;
    
    IF v_resultado > 0 THEN
        RETURN json_build_object(
            'success', true,
            'message', 'Inscripción actualizada exitosamente'
        );
    ELSE
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró la inscripción'
        );
    END IF;
EXCEPTION WHEN OTHERS THEN
    RETURN json_build_object(
        'success', false,
        'message', SQLERRM
    );
END;
$$ LANGUAGE plpgsql;

-- Agregar columna tipo_movimiento a transacciones si no existe
ALTER TABLE transacciones 
ADD COLUMN IF NOT EXISTS tipo_movimiento VARCHAR(20) DEFAULT 'INGRESO';

-- Función para registrar movimiento de caja cuando se confirma una transacción
CREATE OR REPLACE FUNCTION fn_registrar_movimiento_caja()
RETURNS TRIGGER AS $$
DECLARE
    v_descripcion TEXT;
    v_inscripcion_id TEXT;
BEGIN
    -- Solo insertar cuando el estado cambia a 'CONFIRMADO' 
    -- (asumiendo que 'CONFIRMADO' es el estado final)
    IF (TG_OP = 'INSERT' AND NEW.estado = 'CONFIRMADO') OR 
       (TG_OP = 'UPDATE' AND OLD.estado != 'CONFIRMADO' AND NEW.estado = 'CONFIRMADO') THEN
        
        -- Extraer inscripción_id de las observaciones si existe
        -- Formato esperado: "Pago Inscripción #17"
        v_inscripcion_id := substring(NEW.observaciones from 'Inscripción #(\d+)');
        
        -- Construir descripción detallada
        v_descripcion := 'Pago de inscripción';
        
        IF v_inscripcion_id IS NOT NULL THEN
            v_descripcion := v_descripcion || ' #' || v_inscripcion_id;
        END IF;
        
        v_descripcion := v_descripcion || ' - Transacción: ' || NEW.numero_transaccion;
        
        IF NEW.observaciones IS NOT NULL AND NEW.observaciones != '' THEN
            v_descripcion := v_descripcion || ' - ' || NEW.observaciones;
        END IF;
        
        -- Limitar longitud de descripción si es necesario (varchar sin límite específico)
        v_descripcion := left(v_descripcion, 255);
        
        -- Insertar en movimientos_caja
        INSERT INTO movimientos_caja (
            fecha,
            tipo,
            transaccion_id,
            monto,
            forma_pago,
            descripcion,
            usuario_id,
            created_at
        ) VALUES (
            COALESCE(NEW.fecha_pago, CURRENT_DATE),
            'INGRESO',  -- Todas las transacciones de pago son ingresos
            NEW.id,
            NEW.monto_final,
            NEW.forma_pago,
            v_descripcion,
            NEW.registrado_por,
            CURRENT_TIMESTAMP
        );
        
        RAISE NOTICE '✅ Movimiento de caja registrado para transacción %', NEW.id;
        
    -- Para cuando se anula una transacción (opcional)
    ELSIF (TG_OP = 'UPDATE' AND OLD.estado = 'CONFIRMADO' AND NEW.estado = 'ANULADO') THEN
        -- Aquí podrías registrar un movimiento de anulación si lo deseas
        -- Por ejemplo, insertar un movimiento negativo o marcar como anulado
        RAISE NOTICE 'ℹ️ Transacción % anulada - No se registra movimiento', NEW.id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Eliminar trigger si existe
DROP TRIGGER IF EXISTS tr_registrar_movimiento_caja ON transacciones;

-- Crear el trigger
CREATE TRIGGER tr_registrar_movimiento_caja
    AFTER INSERT OR UPDATE OF estado
    ON transacciones
    FOR EACH ROW
    EXECUTE FUNCTION fn_registrar_movimiento_caja();