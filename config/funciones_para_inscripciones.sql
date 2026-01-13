-- ============================================
-- 1. FUNCIÓN PARA VERIFICAR DISPONIBILIDAD
-- ============================================
CREATE OR REPLACE FUNCTION fn_verificar_disponibilidad_programa(
    p_programa_id INTEGER
)
RETURNS TABLE (
    disponible BOOLEAN,
    cupos_disponibles INTEGER,
    estado_programa d_estado_programa,
    mensaje TEXT
) AS $$
DECLARE
    v_cupos_maximos INTEGER;
    v_cupos_inscritos INTEGER;
    v_estado d_estado_programa;
    v_fecha_inicio DATE;
    v_fecha_fin DATE;
BEGIN
    -- Obtener información del programa
    SELECT cupos_maximos, cupos_inscritos, estado, fecha_inicio, fecha_fin
    INTO v_cupos_maximos, v_cupos_inscritos, v_estado, v_fecha_inicio, v_fecha_fin
    FROM programas
    WHERE id = p_programa_id;
    
    -- Verificar si el programa existe
    IF NOT FOUND THEN
        RETURN QUERY SELECT 
            FALSE, 
            0, 
            NULL::d_estado_programa, 
            'Programa no encontrado';
        RETURN;
    END IF;
    
    -- Verificar estado del programa
    IF v_estado NOT IN ('INSCRIPCIONES', 'EN_CURSO') THEN
        RETURN QUERY SELECT 
            FALSE, 
            0, 
            v_estado, 
            'Programa no está en periodo de inscripciones. Estado: ' || v_estado;
        RETURN;
    END IF;
    
    -- Verificar fechas si el programa está en curso
    IF v_estado = 'EN_CURSO' AND v_fecha_fin < CURRENT_DATE THEN
        RETURN QUERY SELECT 
            FALSE, 
            0, 
            v_estado, 
            'Programa ya finalizó';
        RETURN;
    END IF;
    
    -- Verificar cupos
    IF v_cupos_maximos IS NOT NULL AND v_cupos_inscritos >= v_cupos_maximos THEN
        RETURN QUERY SELECT 
            FALSE, 
            0, 
            v_estado, 
            'Cupos agotados';
        RETURN;
    END IF;
    
    -- Calcular cupos disponibles
    RETURN QUERY SELECT 
        TRUE,
        COALESCE(v_cupos_maximos - v_cupos_inscritos, 9999),
        v_estado,
        'Programa disponible para inscripción';
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 2. FUNCIÓN PARA CREAR INSCRIPCIÓN
-- ============================================
CREATE OR REPLACE FUNCTION fn_crear_inscripcion(
    p_estudiante_id INTEGER,
    p_programa_id INTEGER,
    p_descuento_aplicado DECIMAL(10,2) DEFAULT 0,
    p_observaciones TEXT DEFAULT NULL,
    p_fecha_inscripcion DATE DEFAULT CURRENT_DATE
)
RETURNS JSON AS $$
DECLARE
    v_inscripcion_id INTEGER;
    v_estudiante_nombre TEXT;
    v_programa_nombre TEXT;
    v_codigo_programa VARCHAR(20);
    v_resultado JSON;
    v_disponibilidad RECORD;
BEGIN
    -- Verificar disponibilidad del programa
    SELECT * INTO v_disponibilidad
    FROM fn_verificar_disponibilidad_programa(p_programa_id);
    
    IF NOT v_disponibilidad.disponible THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', v_disponibilidad.mensaje,
            'inscripcion_id', NULL
        );
    END IF;
    
    -- Verificar si ya está inscrito
    IF EXISTS (
        SELECT 1 FROM inscripciones 
        WHERE estudiante_id = p_estudiante_id 
        AND programa_id = p_programa_id
    ) THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'El estudiante ya está inscrito en este programa',
            'inscripcion_id', NULL
        );
    END IF;
    
    -- Obtener nombres para auditoría
    SELECT CONCAT(nombres, ' ', apellido_paterno, ' ', COALESCE(apellido_materno, ''))
    INTO v_estudiante_nombre
    FROM estudiantes WHERE id = p_estudiante_id;
    
    SELECT nombre, codigo
    INTO v_programa_nombre, v_codigo_programa
    FROM programas WHERE id = p_programa_id;
    
    IF v_estudiante_nombre IS NULL THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Estudiante no encontrado',
            'inscripcion_id', NULL
        );
    END IF;
    
    IF v_programa_nombre IS NULL THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Programa no encontrado',
            'inscripcion_id', NULL
        );
    END IF;
    
    -- Crear la inscripción
    INSERT INTO inscripciones (
        estudiante_id,
        programa_id,
        fecha_inscripcion,
        estado,
        descuento_aplicado,
        observaciones
    ) VALUES (
        p_estudiante_id,
        p_programa_id,
        p_fecha_inscripcion,
        CASE 
            WHEN p_descuento_aplicado > 0 THEN 'PREINSCRITO'
            ELSE 'INSCRITO'
        END,
        p_descuento_aplicado,
        p_observaciones
    ) RETURNING id INTO v_inscripcion_id;
    
    -- Actualizar cupos inscritos
    UPDATE programas 
    SET cupos_inscritos = cupos_inscritos + 1,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_programa_id;
    
    -- Registrar en log de auditoría (si existe tabla auditoria)
    -- INSERT INTO auditoria_inscripciones (...)
    
    RETURN json_build_object(
        'success', TRUE,
        'message', 'Inscripción creada exitosamente',
        'inscripcion_id', v_inscripcion_id,
        'data', json_build_object(
            'estudiante', v_estudiante_nombre,
            'programa', v_programa_nombre,
            'codigo_programa', v_codigo_programa,
            'fecha', p_fecha_inscripcion,
            'descuento', p_descuento_aplicado
        )
    );
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Error al crear inscripción: ' || SQLERRM,
            'inscripcion_id', NULL
        );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 3. FUNCIÓN PARA INSCRIPCIÓN RETROACTIVA
-- ============================================
CREATE OR REPLACE FUNCTION fn_crear_inscripcion_retroactiva(
    p_estudiante_id INTEGER,
    p_programa_id INTEGER,
    p_fecha_inscripcion DATE,
    p_descuento_aplicado DECIMAL(10,2) DEFAULT 0,
    p_observaciones TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_programa_estado d_estado_programa;
    v_fecha_inicio DATE;
    v_fecha_fin DATE;
    v_resultado JSON;
BEGIN
    -- Verificar que el programa exista y obtener fechas
    SELECT estado, fecha_inicio, fecha_fin
    INTO v_programa_estado, v_fecha_inicio, v_fecha_fin
    FROM programas
    WHERE id = p_programa_id;
    
    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Programa no encontrado',
            'inscripcion_id', NULL
        );
    END IF;
    
    -- Validaciones para inscripción retroactiva
    IF p_fecha_inscripcion > CURRENT_DATE THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'No se puede crear inscripción con fecha futura',
            'inscripcion_id', NULL
        );
    END IF;
    
    IF v_fecha_inicio IS NOT NULL AND p_fecha_inscripcion < v_fecha_inicio THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Fecha de inscripción anterior al inicio del programa',
            'inscripcion_id', NULL
        );
    END IF;
    
    IF v_fecha_fin IS NOT NULL AND v_fecha_fin < CURRENT_DATE THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Programa ya finalizó, no se permiten inscripciones retroactivas',
            'inscripcion_id', NULL
        );
    END IF;
    
    -- Crear inscripción retroactiva
    SELECT * INTO v_resultado
    FROM sp_crear_inscripcion(
        p_estudiante_id,
        p_programa_id,
        p_descuento_aplicado,
        p_observaciones,
        p_fecha_inscripcion
    );
    
    RETURN v_resultado;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 4. FUNCIÓN PARA REGISTRAR PAGO DE INSCRIPCIÓN
-- ============================================
CREATE OR REPLACE FUNCTION fn_registrar_pago_inscripcion(
    p_inscripcion_id INTEGER,
    p_forma_pago d_forma_pago,
    p_monto_pagado DECIMAL(10,2),
    p_fecha_pago DATE DEFAULT CURRENT_DATE,
    p_numero_comprobante VARCHAR(50) DEFAULT NULL,
    p_banco_origen VARCHAR(100) DEFAULT NULL,
    p_cuenta_origen VARCHAR(50) DEFAULT NULL,
    p_observaciones TEXT DEFAULT NULL,
    p_registrado_por INTEGER DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_transaccion_id INTEGER;
    v_numero_transaccion VARCHAR(50);
    v_inscripcion RECORD;
    v_programa RECORD;
    v_monto_total DECIMAL(10,2);
    v_descuento_total DECIMAL(10,2);
    v_monto_final DECIMAL(10,2);
    v_conceptos_pagados TEXT[];
    v_resultado JSON;
BEGIN
    -- Obtener información de la inscripción
    SELECT i.*, p.costo_matricula, p.costo_inscripcion, p.costo_total
    INTO v_inscripcion
    FROM inscripciones i
    JOIN programas p ON i.programa_id = p.id
    WHERE i.id = p_inscripcion_id;
    
    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Inscripción no encontrada',
            'transaccion_id', NULL
        );
    END IF;
    
    -- Verificar estado de la inscripción
    IF v_inscripcion.estado = 'CONCLUIDO' OR v_inscripcion.estado = 'RETIRADO' THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Inscripción no activa: ' || v_inscripcion.estado,
            'transaccion_id', NULL
        );
    END IF;
    
    -- Calcular montos
    v_monto_total := v_inscripcion.costo_matricula + v_inscripcion.costo_inscripcion;
    v_descuento_total := COALESCE(v_inscripcion.descuento_aplicado, 0);
    v_monto_final := v_monto_total - v_descuento_total;
    
    -- Verificar monto pagado
    IF p_monto_pagado < v_monto_final THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Monto insuficiente. Se esperaba: ' || v_monto_final,
            'transaccion_id', NULL
        );
    END IF;
    
    -- Generar número de transacción único
    v_numero_transaccion := 'TRANS-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || 
                           LPAD(NEXTVAL('seq_transacciones_numero'::REGCLASS)::TEXT, 6, '0');
    
    -- Crear transacción
    INSERT INTO transacciones (
        numero_transaccion,
        estudiante_id,
        programa_id,
        fecha_pago,
        monto_total,
        descuento_total,
        monto_final,
        forma_pago,
        estado,
        numero_comprobante,
        banco_origen,
        cuenta_origen,
        observaciones,
        registrado_por
    ) VALUES (
        v_numero_transaccion,
        v_inscripcion.estudiante_id,
        v_inscripcion.programa_id,
        p_fecha_pago,
        v_monto_total,
        v_descuento_total,
        p_monto_pagado,  -- Registrar monto realmente pagado
        p_forma_pago,
        'CONFIRMADO',
        p_numero_comprobante,
        p_banco_origen,
        p_cuenta_origen,
        p_observaciones,
        p_registrado_por
    ) RETURNING id INTO v_transaccion_id;
    
    -- Registrar detalles de la transacción
    -- Matrícula
    IF v_inscripcion.costo_matricula > 0 THEN
        INSERT INTO detalles_transaccion (
            transaccion_id,
            concepto_pago_id,
            descripcion,
            cantidad,
            precio_unitario,
            subtotal,
            orden
        )
        SELECT 
            v_transaccion_id,
            cp.id,
            'Matrícula - ' || p.nombre,
            1,
            v_inscripcion.costo_matricula,
            v_inscripcion.costo_matricula,
            1
        FROM conceptos_pago cp
        CROSS JOIN programas p
        WHERE cp.codigo = 'MATRICULA'
        AND p.id = v_inscripcion.programa_id;
        
        v_conceptos_pagados := array_append(v_conceptos_pagados, 'Matrícula');
    END IF;
    
    -- Inscripción
    IF v_inscripcion.costo_inscripcion > 0 THEN
        INSERT INTO detalles_transaccion (
            transaccion_id,
            concepto_pago_id,
            descripcion,
            cantidad,
            precio_unitario,
            subtotal,
            orden
        )
        SELECT 
            v_transaccion_id,
            cp.id,
            'Inscripción - ' || p.nombre,
            1,
            v_inscripcion.costo_inscripcion,
            v_inscripcion.costo_inscripcion,
            2
        FROM conceptos_pago cp
        CROSS JOIN programas p
        WHERE cp.codigo = 'INSCRIPCION'
        AND p.id = v_inscripcion.programa_id;
        
        v_conceptos_pagados := array_append(v_conceptos_pagados, 'Inscripción');
    END IF;
    
    -- Aplicar descuento si existe
    IF v_descuento_total > 0 THEN
        INSERT INTO detalles_transaccion (
            transaccion_id,
            concepto_pago_id,
            descripcion,
            cantidad,
            precio_unitario,
            subtotal,
            orden
        )
        SELECT 
            v_transaccion_id,
            cp.id,
            'Descuento aplicado',
            1,
            -v_descuento_total,
            -v_descuento_total,
            3
        FROM conceptos_pago cp
        WHERE cp.codigo = 'DESCUENTO' OR cp.nombre ILIKE '%descuento%'
        LIMIT 1;
    END IF;
    
    -- Actualizar estado de la inscripción
    UPDATE inscripciones 
    SET estado = 'INSCRITO',
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_inscripcion_id;
    
    -- Registrar movimiento de caja
    INSERT INTO movimientos_caja (
        fecha,
        tipo,
        transaccion_id,
        monto,
        forma_pago,
        descripcion,
        usuario_id
    ) VALUES (
        p_fecha_pago,
        'INGRESO',
        v_transaccion_id,
        p_monto_pagado,
        p_forma_pago,
        'Pago inscripción - Transacción: ' || v_numero_transaccion,
        p_registrado_por
    );
    
    RETURN json_build_object(
        'success', TRUE,
        'message', 'Pago registrado exitosamente',
        'transaccion_id', v_transaccion_id,
        'numero_transaccion', v_numero_transaccion,
        'data', json_build_object(
            'monto_total', v_monto_total,
            'descuento', v_descuento_total,
            'monto_pagado', p_monto_pagado,
            'conceptos', v_conceptos_pagados,
            'fecha_pago', p_fecha_pago
        )
    );
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Error al registrar pago: ' || SQLERRM,
            'transaccion_id', NULL
        );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 5. FUNCIÓN PARA REGISTRAR DOCUMENTO DE RESPALDO
-- ============================================
CREATE OR REPLACE FUNCTION fn_registrar_documento_respaldo(
    p_transaccion_id INTEGER,
    p_tipo_documento VARCHAR(50),
    p_nombre_original VARCHAR(200),
    p_nombre_archivo VARCHAR(200),
    p_extension d_extension_archivo,
    p_ruta_archivo TEXT,
    p_tamano_bytes INTEGER DEFAULT NULL,
    p_observaciones TEXT DEFAULT NULL,
    p_subido_por INTEGER DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_documento_id INTEGER;
    v_transaccion_numero VARCHAR(50);
BEGIN
    -- Verificar que la transacción existe
    SELECT numero_transaccion INTO v_transaccion_numero
    FROM transacciones 
    WHERE id = p_transaccion_id;
    
    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Transacción no encontrada',
            'documento_id', NULL
        );
    END IF;
    
    -- Validar tamaño del archivo si se proporciona
    IF p_tamano_bytes IS NOT NULL AND p_tamano_bytes > 10485760 THEN -- 10MB máximo
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Archivo demasiado grande (máximo 10MB)',
            'documento_id', NULL
        );
    END IF;
    
    -- Registrar documento
    INSERT INTO documentos_respaldo (
        transaccion_id,
        tipo_documento,
        nombre_original,
        nombre_archivo,
        extension,
        ruta_archivo,
        tamano_bytes,
        observaciones,
        subido_por
    ) VALUES (
        p_transaccion_id,
        p_tipo_documento,
        p_nombre_original,
        p_nombre_archivo,
        p_extension,
        p_ruta_archivo,
        p_tamano_bytes,
        p_observaciones,
        p_subido_por
    ) RETURNING id INTO v_documento_id;
    
    -- Actualizar observaciones de la transacción si es necesario
    UPDATE transacciones 
    SET observaciones = COALESCE(observaciones, '') || 
                       ' | Documento adjunto: ' || p_tipo_documento || ' (' || p_extension || ')'
    WHERE id = p_transaccion_id;
    
    RETURN json_build_object(
        'success', TRUE,
        'message', 'Documento registrado exitosamente',
        'documento_id', v_documento_id,
        'data', json_build_object(
            'transaccion', v_transaccion_numero,
            'tipo_documento', p_tipo_documento,
            'nombre_archivo', p_nombre_archivo,
            'ruta', p_ruta_archivo
        )
    );
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Error al registrar documento: ' || SQLERRM,
            'documento_id', NULL
        );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 6. FUNCIÓN PARA OBTENER INSCRIPCIONES
-- ============================================
CREATE OR REPLACE FUNCTION fn_obtener_inscripciones(
    p_filtro_estado d_estado_academico DEFAULT NULL,
    p_filtro_programa INTEGER DEFAULT NULL,
    p_filtro_fecha_desde DATE DEFAULT NULL,
    p_filtro_fecha_hasta DATE DEFAULT NULL
)
RETURNS TABLE (
    inscripcion_id INTEGER,
    estudiante_id INTEGER,
    estudiante_nombre TEXT,
    estudiante_ci VARCHAR(15),
    programa_id INTEGER,
    programa_nombre VARCHAR(200),
    programa_codigo VARCHAR(20),
    fecha_inscripcion DATE,
    estado d_estado_academico,
    descuento_aplicado DECIMAL(10,2),
    cupos_disponibles INTEGER,
    pagos_realizados DECIMAL(10,2),
    saldo_pendiente DECIMAL(10,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        i.id,
        e.id,
        CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')),
        e.ci_numero,
        p.id,
        p.nombre,
        p.codigo,
        i.fecha_inscripcion,
        i.estado,
        COALESCE(i.descuento_aplicado, 0),
        COALESCE(p.cupos_maximos - p.cupos_inscritos, 0),
        COALESCE(SUM(t.monto_final), 0),
        COALESCE(p.costo_total - SUM(t.monto_final), p.costo_total) - COALESCE(i.descuento_aplicado, 0)
    FROM inscripciones i
    JOIN estudiantes e ON i.estudiante_id = e.id
    JOIN programas p ON i.programa_id = p.id
    LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
        AND i.programa_id = t.programa_id
        AND t.estado = 'CONFIRMADO'
    WHERE (p_filtro_estado IS NULL OR i.estado = p_filtro_estado)
        AND (p_filtro_programa IS NULL OR p.id = p_filtro_programa)
        AND (p_filtro_fecha_desde IS NULL OR i.fecha_inscripcion >= p_filtro_fecha_desde)
        AND (p_filtro_fecha_hasta IS NULL OR i.fecha_inscripcion <= p_filtro_fecha_hasta)
    GROUP BY i.id, e.id, p.id
    ORDER BY i.fecha_inscripcion DESC, e.apellido_paterno, e.nombres;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 7. FUNCIÓN PARA ACTUALIZAR INSCRIPCIÓN
-- ============================================
CREATE OR REPLACE FUNCTION fn_actualizar_inscripcion(
    p_inscripcion_id INTEGER,
    p_nuevo_estado d_estado_academico DEFAULT NULL,
    p_nuevo_descuento DECIMAL(10,2) DEFAULT NULL,
    p_nuevas_observaciones TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_old_estado d_estado_academico;
    v_old_descuento DECIMAL(10,2);
    v_old_observaciones TEXT;
BEGIN
    -- Obtener valores actuales
    SELECT estado, descuento_aplicado, observaciones
    INTO v_old_estado, v_old_descuento, v_old_observaciones
    FROM inscripciones
    WHERE id = p_inscripcion_id;
    
    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Inscripción no encontrada'
        );
    END IF;
    
    -- Actualizar registro
    UPDATE inscripciones
    SET estado = COALESCE(p_nuevo_estado, estado),
        descuento_aplicado = COALESCE(p_nuevo_descuento, descuento_aplicado),
        observaciones = COALESCE(p_nuevas_observaciones, observaciones),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = p_inscripcion_id;
    
    RETURN json_build_object(
        'success', TRUE,
        'message', 'Inscripción actualizada exitosamente',
        'data', json_build_object(
            'cambios', json_build_object(
                'estado_anterior', v_old_estado,
                'estado_nuevo', COALESCE(p_nuevo_estado, v_old_estado),
                'descuento_anterior', v_old_descuento,
                'descuento_nuevo', COALESCE(p_nuevo_descuento, v_old_descuento)
            )
        )
    );
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Error al actualizar inscripción: ' || SQLERRM
        );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 8. FUNCIÓN PARA ELIMINAR INSCRIPCIÓN
-- ============================================
CREATE OR REPLACE FUNCTION fn_eliminar_inscripcion(
    p_inscripcion_id INTEGER,
    p_motivo TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_programa_id INTEGER;
    v_estado d_estado_academico;
    v_tiene_pagos BOOLEAN;
BEGIN
    -- Obtener información de la inscripción
    SELECT programa_id, estado INTO v_programa_id, v_estado
    FROM inscripciones
    WHERE id = p_inscripcion_id;
    
    IF NOT FOUND THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Inscripción no encontrada'
        );
    END IF;
    
    -- Verificar si tiene pagos asociados
    SELECT EXISTS(
        SELECT 1 FROM transacciones t
        JOIN inscripciones i ON t.estudiante_id = i.estudiante_id 
            AND t.programa_id = i.programa_id
        WHERE i.id = p_inscripcion_id
        AND t.estado = 'CONFIRMADO'
    ) INTO v_tiene_pagos;
    
    IF v_tiene_pagos THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'No se puede eliminar inscripción con pagos confirmados'
        );
    END IF;
    
    -- Eliminar inscripción (CASCADE eliminará transacciones no confirmadas)
    DELETE FROM inscripciones WHERE id = p_inscripcion_id;
    
    -- Actualizar cupos del programa
    IF v_programa_id IS NOT NULL THEN
        UPDATE programas 
        SET cupos_inscritos = GREATEST(cupos_inscritos - 1, 0),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = v_programa_id;
    END IF;
    
    -- Registrar en log de eliminaciones (si existe)
    -- INSERT INTO log_eliminaciones (...)
    
    RETURN json_build_object(
        'success', TRUE,
        'message', 'Inscripción eliminada exitosamente'
    );
    
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Error al eliminar inscripción: ' || SQLERRM
        );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 9. FUNCIÓN PARA OBTENER DETALLES DE INSCRIPCIÓN
-- ============================================
CREATE OR REPLACE FUNCTION fn_obtener_detalle_inscripcion(
    p_inscripcion_id INTEGER
)
RETURNS JSON AS $$
DECLARE
    v_result JSON;
BEGIN
    SELECT json_build_object(
        'inscripcion', json_build_object(
            'id', i.id,
            'fecha_inscripcion', i.fecha_inscripcion,
            'estado', i.estado,
            'descuento_aplicado', i.descuento_aplicado,
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
        'saldo', p.costo_total - COALESCE((
            SELECT SUM(t.monto_final)
            FROM transacciones t
            WHERE t.estudiante_id = i.estudiante_id 
            AND t.programa_id = i.programa_id
            AND t.estado = 'CONFIRMADO'
        ), 0) - COALESCE(i.descuento_aplicado, 0)
    ) INTO v_result
    FROM inscripciones i
    JOIN estudiantes e ON i.estudiante_id = e.id
    JOIN programas p ON i.programa_id = p.id
    WHERE i.id = p_inscripcion_id;
    
    IF v_result IS NULL THEN
        RETURN json_build_object(
            'success', FALSE,
            'message', 'Inscripción no encontrada'
        );
    END IF;
    
    RETURN json_build_object(
        'success', TRUE,
        'data', v_result
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- 10. FUNCIÓN PARA REGISTRAR PAGO CON DOCUMENTOS
-- ============================================
CREATE OR REPLACE FUNCTION sp_registrar_pago_completo(
    p_inscripcion_id INTEGER,
    p_forma_pago d_forma_pago,
    p_monto_pagado DECIMAL(10,2),
    p_fecha_pago DATE DEFAULT CURRENT_DATE,
    p_numero_comprobante VARCHAR(50) DEFAULT NULL,
    p_banco_origen VARCHAR(100) DEFAULT NULL,
    p_cuenta_origen VARCHAR(50) DEFAULT NULL,
    p_observaciones TEXT DEFAULT NULL,
    p_registrado_por INTEGER DEFAULT NULL,
    p_documentos JSON DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    v_resultado_pago JSON;
    v_transaccion_id INTEGER;
    v_documento JSON;
    v_resultado_documento JSON;
    v_documentos_procesados INTEGER := 0;
    v_documentos_fallidos INTEGER := 0;
BEGIN
    -- Registrar el pago primero
    SELECT * INTO v_resultado_pago
    FROM sp_registrar_pago_inscripcion(
        p_inscripcion_id,
        p_forma_pago,
        p_monto_pagado,
        p_fecha_pago,
        p_numero_comprobante,
        p_banco_origen,
        p_cuenta_origen,
        p_observaciones,
        p_registrado_por
    );
    
    -- Verificar si el pago fue exitoso
    IF (v_resultado_pago->>'success')::BOOLEAN = FALSE THEN
        RETURN v_resultado_pago;
    END IF;
    
    -- Obtener ID de la transacción creada
    v_transaccion_id := (v_resultado_pago->'data'->>'transaccion_id')::INTEGER;
    
    -- Procesar documentos si se proporcionaron
    IF p_documentos IS NOT NULL THEN
        FOR v_documento IN SELECT * FROM json_array_elements(p_documentos)
        LOOP
            -- Registrar cada documento
            SELECT * INTO v_resultado_documento
            FROM sp_registrar_documento_respaldo(
                v_transaccion_id,
                COALESCE((v_documento->>'tipo_documento'), 'COMPROBANTE_PAGO'),
                (v_documento->>'nombre_original'),
                (v_documento->>'nombre_archivo'),
                (v_documento->>'extension')::d_extension_archivo,
                (v_documento->>'ruta_archivo'),
                (v_documento->>'tamano_bytes')::INTEGER,
                COALESCE((v_documento->>'observaciones'), ''),
                p_registrado_por
            );
            
            IF (v_resultado_documento->>'success')::BOOLEAN THEN
                v_documentos_procesados := v_documentos_procesados + 1;
            ELSE
                v_documentos_fallidos := v_documentos_fallidos + 1;
                RAISE NOTICE 'Error al registrar documento: %', v_resultado_documento->>'message';
            END IF;
        END LOOP;
    END IF;
    
    -- Actualizar respuesta con información de documentos
    v_resultado_pago := jsonb_set(
        v_resultado_pago::jsonb,
        '{data,documentos}'::text[],
        jsonb_build_object(
            'procesados', v_documentos_procesados,
            'fallidos', v_documentos_fallidos
        )
    );
    
    RETURN v_resultado_pago;
END;
$$ LANGUAGE plpgsql;