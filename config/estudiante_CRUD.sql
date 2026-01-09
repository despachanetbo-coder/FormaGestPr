-- ============================================================
-- PROCEDIMIENTOS ALMACENADOS PARA CRUD DE ESTUDIANTES
-- ============================================================

-- 1.1 Función para buscar estudiantes con filtros
CREATE OR REPLACE FUNCTION fn_buscar_estudiantes(
    p_ci_numero VARCHAR DEFAULT NULL,
    p_ci_expedicion VARCHAR DEFAULT NULL,
    p_nombre VARCHAR DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE(
    id INTEGER,
    ci_numero VARCHAR,
    ci_expedicion d_expedicion_ci,
    nombres VARCHAR,
    apellido_paterno VARCHAR,
    apellido_materno VARCHAR,
    fecha_nacimiento DATE,
    telefono VARCHAR,
    email VARCHAR,
    direccion TEXT,
    profesion VARCHAR,
    universidad VARCHAR,
    fotografia_url TEXT,
    activo BOOLEAN,
    fecha_registro TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id, e.ci_numero, e.ci_expedicion, e.nombres, e.apellido_paterno, 
        e.apellido_materno, e.fecha_nacimiento, e.telefono, e.email, 
        e.direccion, e.profesion, e.universidad, e.fotografia_url, 
        e.activo, e.fecha_registro
    FROM estudiantes e
    WHERE 
        (p_ci_numero IS NULL OR e.ci_numero ILIKE '%' || p_ci_numero || '%')
        AND (p_ci_expedicion IS NULL OR e.ci_expedicion = p_ci_expedicion OR p_ci_expedicion = 'Todos')
        AND (
            p_nombre IS NULL OR 
            e.nombres ILIKE '%' || p_nombre || '%' OR 
            e.apellido_paterno ILIKE '%' || p_nombre || '%' OR 
            e.apellido_materno ILIKE '%' || p_nombre || '%'
        )
    ORDER BY e.apellido_paterno, e.apellido_materno, e.nombres
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 1.2 Función para contar estudiantes con filtros
CREATE OR REPLACE FUNCTION fn_contar_estudiantes(
    p_ci_numero VARCHAR DEFAULT NULL,
    p_ci_expedicion VARCHAR DEFAULT NULL,
    p_nombre VARCHAR DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_total INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_total
    FROM estudiantes e
    WHERE 
        (p_ci_numero IS NULL OR e.ci_numero ILIKE '%' || p_ci_numero || '%')
        AND (p_ci_expedicion IS NULL OR e.ci_expedicion = p_ci_expedicion OR p_ci_expedicion = 'Todos')
        AND (
            p_nombre IS NULL OR 
            e.nombres ILIKE '%' || p_nombre || '%' OR 
            e.apellido_paterno ILIKE '%' || p_nombre || '%' OR 
            e.apellido_materno ILIKE '%' || p_nombre || '%'
        );
    
    RETURN COALESCE(v_total, 0);
END;
$$ LANGUAGE plpgsql;

-- 1.3 Función para obtener estudiante por ID
CREATE OR REPLACE FUNCTION fn_obtener_estudiante_por_id(p_id INTEGER)
RETURNS TABLE(
    id INTEGER,
    ci_numero VARCHAR,
    ci_expedicion d_expedicion_ci,
    nombres VARCHAR,
    apellido_paterno VARCHAR,
    apellido_materno VARCHAR,
    fecha_nacimiento DATE,
    telefono VARCHAR,
    email VARCHAR,
    direccion TEXT,
    profesion VARCHAR,
    universidad VARCHAR,
    fotografia_url TEXT,
    activo BOOLEAN,
    fecha_registro TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id, e.ci_numero, e.ci_expedicion, e.nombres, e.apellido_paterno, 
        e.apellido_materno, e.fecha_nacimiento, e.telefono, e.email, 
        e.direccion, e.profesion, e.universidad, e.fotografia_url, 
        e.activo, e.fecha_registro
    FROM estudiantes e
    WHERE e.id = p_id;
END;
$$ LANGUAGE plpgsql;

-- 1.4 Función para verificar si CI ya existe (para validación)
CREATE OR REPLACE FUNCTION fn_verificar_ci_existente(
    p_ci_numero VARCHAR,
    p_excluir_id INTEGER DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_existe BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 
        FROM estudiantes 
        WHERE ci_numero = p_ci_numero 
        AND (p_excluir_id IS NULL OR id != p_excluir_id)
    ) INTO v_existe;
    
    RETURN v_existe;
END;
$$ LANGUAGE plpgsql;

-- 1.5 Procedimiento para insertar nuevo estudiante
CREATE OR REPLACE FUNCTION fn_insertar_estudiante(
    p_ci_numero VARCHAR,
    p_ci_expedicion d_expedicion_ci,
    p_nombres VARCHAR,
    p_apellido_paterno VARCHAR,
    p_apellido_materno VARCHAR,
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_email VARCHAR DEFAULT NULL,
    p_direccion TEXT DEFAULT NULL,
    p_profesion VARCHAR DEFAULT NULL,
    p_universidad VARCHAR DEFAULT NULL,
    p_fotografia_url TEXT DEFAULT NULL,
    p_activo BOOLEAN DEFAULT TRUE
)
RETURNS TABLE(nuevo_id INTEGER, mensaje VARCHAR, exito BOOLEAN)
LANGUAGE plpgsql
AS $$
DECLARE
    v_nuevo_id INTEGER;
    v_mensaje VARCHAR;
    v_exito BOOLEAN;
BEGIN
    -- Inicializar variables
    v_nuevo_id := NULL;
    v_mensaje := '';
    v_exito := FALSE;
    
    -- Validar CI único
    IF fn_verificar_ci_existente(p_ci_numero) THEN
        v_mensaje := 'El número de CI ya está registrado en el sistema';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar email único si se proporciona
    IF p_email IS NOT NULL AND EXISTS(
        SELECT 1 FROM estudiantes WHERE email = p_email
    ) THEN
        v_mensaje := 'El email ya está registrado en el sistema';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Insertar estudiante
    INSERT INTO estudiantes (
        ci_numero, ci_expedicion, nombres, apellido_paterno, apellido_materno,
        fecha_nacimiento, telefono, email, direccion, profesion, universidad,
        fotografia_url, activo
    ) VALUES (
        p_ci_numero, p_ci_expedicion, p_nombres, p_apellido_paterno, p_apellido_materno,
        p_fecha_nacimiento, p_telefono, p_email, p_direccion, p_profesion, p_universidad,
        p_fotografia_url, p_activo
    ) RETURNING id INTO v_nuevo_id;
    
    v_mensaje := 'Estudiante creado exitosamente con ID: ' || v_nuevo_id;
    v_exito := TRUE;
    
    RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al crear estudiante: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
END;
$$;

-- 1.6 Procedimiento para actualizar estudiante
CREATE OR REPLACE PROCEDURE sp_actualizar_estudiante(
    OUT p_filas_afectadas INTEGER,
    OUT p_mensaje VARCHAR,
    OUT p_exito BOOLEAN,
    IN p_id INTEGER,
    IN p_ci_numero VARCHAR,
    IN p_ci_expedicion d_expedicion_ci,
    IN p_nombres VARCHAR,
    IN p_apellido_paterno VARCHAR,
    IN p_apellido_materno VARCHAR,
    IN p_fecha_nacimiento DATE DEFAULT NULL,
    IN p_telefono VARCHAR DEFAULT NULL,
    IN p_email VARCHAR DEFAULT NULL,
    IN p_direccion TEXT DEFAULT NULL,
    IN p_profesion VARCHAR DEFAULT NULL,
    IN p_universidad VARCHAR DEFAULT NULL,
    IN p_fotografia_url TEXT DEFAULT NULL,
    IN p_activo BOOLEAN DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Inicializar variables de salida
    p_filas_afectadas := 0;
    p_mensaje := '';
    p_exito := FALSE;
    
    -- Validar que el estudiante exista
    IF NOT EXISTS(SELECT 1 FROM estudiantes WHERE id = p_id) THEN
        p_mensaje := 'El estudiante con ID ' || p_id || ' no existe';
        RETURN;
    END IF;
    
    -- Validar CI único (excluyendo el registro actual)
    IF fn_verificar_ci_existente(p_ci_numero, p_id) THEN
        p_mensaje := 'El número de CI ya está registrado en otro estudiante';
        RETURN;
    END IF;
    
    -- Validar email único si se proporciona
    IF p_email IS NOT NULL AND EXISTS(
        SELECT 1 FROM estudiantes WHERE email = p_email AND id != p_id
    ) THEN
        p_mensaje := 'El email ya está registrado en otro estudiante';
        RETURN;
    END IF;
    
    -- Actualizar estudiante
    UPDATE estudiantes
    SET 
        ci_numero = p_ci_numero,
        ci_expedicion = p_ci_expedicion,
        nombres = p_nombres,
        apellido_paterno = p_apellido_paterno,
        apellido_materno = p_apellido_materno,
        fecha_nacimiento = p_fecha_nacimiento,
        telefono = p_telefono,
        email = p_email,
        direccion = p_direccion,
        profesion = p_profesion,
        universidad = p_universidad,
        fotografia_url = p_fotografia_url,
        activo = COALESCE(p_activo, activo)
    WHERE id = p_id;
    
    GET DIAGNOSTICS p_filas_afectadas = ROW_COUNT;
    
    IF p_filas_afectadas > 0 THEN
        p_mensaje := 'Estudiante actualizado exitosamente';
        p_exito := TRUE;
    ELSE
        p_mensaje := 'No se realizaron cambios en el estudiante';
        p_exito := FALSE;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        p_mensaje := 'Error al actualizar estudiante: ' || SQLERRM;
        p_exito := FALSE;
END;
$$;

-- 1.7 Procedimiento para eliminar (desactivar) estudiante
CREATE OR REPLACE PROCEDURE sp_eliminar_estudiante(
    IN p_id INTEGER,
    OUT p_filas_afectadas INTEGER,
    OUT p_mensaje VARCHAR,
    OUT p_exito BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Inicializar variables de salida
    p_filas_afectadas := 0;
    p_mensaje := '';
    p_exito := FALSE;
    
    -- Validar que el estudiante exista
    IF NOT EXISTS(SELECT 1 FROM estudiantes WHERE id = p_id) THEN
        p_mensaje := 'El estudiante con ID ' || p_id || ' no existe';
        RETURN;
    END IF;
    
    -- Validar que no tenga transacciones activas
    IF EXISTS(
        SELECT 1 
        FROM transacciones 
        WHERE estudiante_id = p_id 
        AND estado = 'CONFIRMADO'
        AND fecha_pago >= CURRENT_DATE - INTERVAL '30 days'
    ) THEN
        p_mensaje := 'No se puede eliminar estudiante con transacciones recientes';
        RETURN;
    END IF;
    
    -- "Eliminar" desactivando (soft delete)
    UPDATE estudiantes
    SET activo = FALSE
    WHERE id = p_id;
    
    GET DIAGNOSTICS p_filas_afectadas = ROW_COUNT;
    
    IF p_filas_afectadas > 0 THEN
        p_mensaje := 'Estudiante desactivado exitosamente';
        p_exito := TRUE;
    ELSE
        p_mensaje := 'No se pudo desactivar el estudiante';
        p_exito := FALSE;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        p_mensaje := 'Error al eliminar estudiante: ' || SQLERRM;
        p_exito := FALSE;
END;
$$;

-- 1.8 Procedimiento para activar estudiante
CREATE OR REPLACE PROCEDURE sp_activar_estudiante(
    IN p_id INTEGER,
    OUT p_filas_afectadas INTEGER,
    OUT p_mensaje VARCHAR,
    OUT p_exito BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    -- Inicializar variables de salida
    p_filas_afectadas := 0;
    p_mensaje := '';
    p_exito := FALSE;
    
    -- Validar que el estudiante exista
    IF NOT EXISTS(SELECT 1 FROM estudiantes WHERE id = p_id) THEN
        p_mensaje := 'El estudiante con ID ' || p_id || ' no existe';
        RETURN;
    END IF;
    
    -- Activar estudiante
    UPDATE estudiantes
    SET activo = TRUE
    WHERE id = p_id;
    
    GET DIAGNOSTICS p_filas_afectadas = ROW_COUNT;
    
    IF p_filas_afectadas > 0 THEN
        p_mensaje := 'Estudiante activado exitosamente';
        p_exito := TRUE;
    ELSE
        p_mensaje := 'No se pudo activar el estudiante';
        p_exito := FALSE;
    END IF;
    
EXCEPTION
    WHEN OTHERS THEN
        p_mensaje := 'Error al activar estudiante: ' || SQLERRM;
        p_exito := FALSE;
END;
$$;

-- 1.9 Función para obtener estadísticas de estudiantes
CREATE OR REPLACE FUNCTION fn_estadisticas_estudiantes()
RETURNS TABLE(
    total_estudiantes INTEGER,
    activos INTEGER,
    inactivos INTEGER,
    promedio_edad NUMERIC,
    con_email INTEGER,
    con_telefono INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER AS total_estudiantes,
        COUNT(*) FILTER (WHERE activo = TRUE)::INTEGER AS activos,
        COUNT(*) FILTER (WHERE activo = FALSE)::INTEGER AS inactivos,
        AVG(EXTRACT(YEAR FROM AGE(CURRENT_DATE, fecha_nacimiento)))::NUMERIC AS promedio_edad,
        COUNT(*) FILTER (WHERE email IS NOT NULL AND email != '')::INTEGER AS con_email,
        COUNT(*) FILTER (WHERE telefono IS NOT NULL AND telefono != '')::INTEGER AS con_telefono
    FROM estudiantes;
END;
$$ LANGUAGE plpgsql;

-- Archivo: correccion_procedimientos.sql
-- Convertir sp_actualizar_estudiante a función
CREATE OR REPLACE FUNCTION fn_actualizar_estudiante(
    p_id INTEGER,
    p_ci_numero VARCHAR,
    p_ci_expedicion d_expedicion_ci,
    p_nombres VARCHAR,
    p_apellido_paterno VARCHAR,
    p_apellido_materno VARCHAR,
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_email VARCHAR DEFAULT NULL,
    p_direccion TEXT DEFAULT NULL,
    p_profesion VARCHAR DEFAULT NULL,
    p_universidad VARCHAR DEFAULT NULL,
    p_fotografia_url TEXT DEFAULT NULL,
    p_activo BOOLEAN DEFAULT NULL
)
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
    
    -- Validar que el estudiante exista
    IF NOT EXISTS(SELECT 1 FROM estudiantes WHERE id = p_id) THEN
        v_mensaje := 'El estudiante con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar CI único (excluyendo el registro actual)
    IF fn_verificar_ci_existente(p_ci_numero, p_id) THEN
        v_mensaje := 'El número de CI ya está registrado en otro estudiante';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar email único si se proporciona
    IF p_email IS NOT NULL AND EXISTS(
        SELECT 1 FROM estudiantes WHERE email = p_email AND id != p_id
    ) THEN
        v_mensaje := 'El email ya está registrado en otro estudiante';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Actualizar estudiante
    UPDATE estudiantes
    SET 
        ci_numero = p_ci_numero,
        ci_expedicion = p_ci_expedicion,
        nombres = p_nombres,
        apellido_paterno = p_apellido_paterno,
        apellido_materno = p_apellido_materno,
        fecha_nacimiento = p_fecha_nacimiento,
        telefono = p_telefono,
        email = p_email,
        direccion = p_direccion,
        profesion = p_profesion,
        universidad = p_universidad,
        fotografia_url = p_fotografia_url,
        activo = COALESCE(p_activo, activo)
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Estudiante actualizado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se realizaron cambios en el estudiante';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al actualizar estudiante: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- Convertir sp_eliminar_estudiante a función
CREATE OR REPLACE FUNCTION fn_eliminar_estudiante(p_id INTEGER)
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
    
    -- Validar que el estudiante exista
    IF NOT EXISTS(SELECT 1 FROM estudiantes WHERE id = p_id) THEN
        v_mensaje := 'El estudiante con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar que no tenga transacciones activas
    IF EXISTS(
        SELECT 1 
        FROM transacciones 
        WHERE estudiante_id = p_id 
        AND estado = 'CONFIRMADO'
        AND fecha_pago >= CURRENT_DATE - INTERVAL '30 days'
    ) THEN
        v_mensaje := 'No se puede eliminar estudiante con transacciones recientes';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- "Eliminar" desactivando (soft delete)
    UPDATE estudiantes
    SET activo = FALSE
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Estudiante desactivado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se pudo desactivar el estudiante';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al eliminar estudiante: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- Convertir sp_activar_estudiante a función
CREATE OR REPLACE FUNCTION fn_activar_estudiante(p_id INTEGER)
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
    
    -- Validar que el estudiante exista
    IF NOT EXISTS(SELECT 1 FROM estudiantes WHERE id = p_id) THEN
        v_mensaje := 'El estudiante con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Activar estudiante
    UPDATE estudiantes
    SET activo = TRUE
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Estudiante activado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se pudo activar el estudiante';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al activar estudiante: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- Función para obtener estudiante por ID con información detallada
CREATE OR REPLACE FUNCTION fn_buscar_estudiante_id(p_id INTEGER)
RETURNS TABLE(
    id INTEGER,
    ci_numero VARCHAR,
    ci_expedicion d_expedicion_ci,
    nombres VARCHAR,
    apellido_paterno VARCHAR,
    apellido_materno VARCHAR,
    fecha_nacimiento DATE,
    telefono VARCHAR,
    email VARCHAR,
    direccion TEXT,
    profesion VARCHAR,
    universidad VARCHAR,
    fotografia_url TEXT,
    activo BOOLEAN,
    fecha_registro TIMESTAMP,
    total_programas INTEGER,
    programas_activos INTEGER,
    total_pagado DECIMAL(12,2),
    total_deuda DECIMAL(12,2)
) 
LANGUAGE plpgsql
AS $$
DECLARE
    v_estudiante RECORD;
    v_total_programas INTEGER;
    v_programas_activos INTEGER;
    v_total_pagado DECIMAL(12,2);
    v_total_deuda DECIMAL(12,2);
BEGIN
    -- Obtener información básica del estudiante
    SELECT 
        e.id,
        e.ci_numero,
        e.ci_expedicion,
        e.nombres,
        e.apellido_paterno,
        e.apellido_materno,
        e.fecha_nacimiento,
        e.telefono,
        e.email,
        e.direccion,
        e.profesion,
        e.universidad,
        e.fotografia_url,
        e.activo,
        e.fecha_registro
    INTO v_estudiante
    FROM estudiantes e
    WHERE e.id = p_id;
    
    -- Si no se encuentra el estudiante, retornar conjunto vacío
    IF NOT FOUND THEN
        RETURN;
    END IF;
    
    -- Contar total de programas inscritos
    SELECT COUNT(DISTINCT i.programa_id)
    INTO v_total_programas
    FROM inscripciones i
    WHERE i.estudiante_id = p_id;
    
    -- Contar programas activos (EN_CURSO o FINALIZADO recientemente)
    SELECT COUNT(DISTINCT i.programa_id)
    INTO v_programas_activos
    FROM inscripciones i
    INNER JOIN programas p ON i.programa_id = p.id
    WHERE i.estudiante_id = p_id
    AND p.estado IN ('EN_CURSO', 'FINALIZADO')
    AND (p.fecha_fin IS NULL OR p.fecha_fin >= CURRENT_DATE - INTERVAL '3 months');
    
    -- Calcular total pagado por el estudiante
    SELECT COALESCE(SUM(t.monto_final), 0)
    INTO v_total_pagado
    FROM transacciones t
    WHERE t.estudiante_id = p_id
    AND t.estado = 'CONFIRMADO';
    
    -- Calcular deuda pendiente (costo total de programas menos lo pagado)
    WITH costos_programas AS (
        SELECT 
            i.programa_id,
            p.costo_total AS costo_programa,
            COALESCE(SUM(t.monto_final), 0) AS pagado_programa
        FROM inscripciones i
        INNER JOIN programas p ON i.programa_id = p.id
        LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
            AND i.programa_id = t.programa_id
            AND t.estado = 'CONFIRMADO'
        WHERE i.estudiante_id = p_id
        GROUP BY i.programa_id, p.costo_total
    )
    SELECT COALESCE(SUM(GREATEST(costo_programa - pagado_programa, 0)), 0)
    INTO v_total_deuda
    FROM costos_programas;
    
    -- Retornar resultados combinados
    RETURN QUERY SELECT
        v_estudiante.id,
        v_estudiante.ci_numero,
        v_estudiante.ci_expedicion,
        v_estudiante.nombres,
        v_estudiante.apellido_paterno,
        v_estudiante.apellido_materno,
        v_estudiante.fecha_nacimiento,
        v_estudiante.telefono,
        v_estudiante.email,
        v_estudiante.direccion,
        v_estudiante.profesion,
        v_estudiante.universidad,
        v_estudiante.fotografia_url,
        v_estudiante.activo,
        v_estudiante.fecha_registro,
        v_total_programas,
        v_programas_activos,
        v_total_pagado,
        v_total_deuda;
END;
$$;


-- Función para obtener todos los programas académicos de un estudiante
CREATE OR REPLACE FUNCTION fn_obtener_programas_estudiante(p_estudiante_id INTEGER)
RETURNS TABLE(
    programa_id INTEGER,
    programa_codigo VARCHAR,
    programa_nombre VARCHAR,
    estado_programa d_estado_programa,
    estado_inscripcion d_estado_academico,
    fecha_inscripcion DATE,
    fecha_inicio DATE,
    fecha_fin DATE,
    duracion_meses INTEGER,
    horas_totales INTEGER,
    costo_total DECIMAL(10,2),
    costo_pagado DECIMAL(10,2),
    saldo_pendiente DECIMAL(10,2),
    porcentaje_pagado DECIMAL(5,2),
    docente_coordinador VARCHAR,
    promocion_descuento DECIMAL(5,2),
    cupos_inscritos INTEGER,
    cupos_maximos INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        p.id AS programa_id,
        p.codigo AS programa_codigo,
        p.nombre AS programa_nombre,
        p.estado AS estado_programa,
        i.estado AS estado_inscripcion,
        i.fecha_inscripcion,
        p.fecha_inicio,
        p.fecha_fin,
        p.duracion_meses,
        p.horas_totales,
        p.costo_total,
        COALESCE(SUM(t.monto_final), 0) AS costo_pagado,
        GREATEST(p.costo_total - COALESCE(SUM(t.monto_final), 0), 0) AS saldo_pendiente,
        CASE 
            WHEN p.costo_total > 0 THEN 
                ROUND((COALESCE(SUM(t.monto_final), 0) * 100.0 / p.costo_total), 2)
            ELSE 0 
        END AS porcentaje_pagado,
        CONCAT(d.nombres, ' ', d.apellido_paterno, ' ', COALESCE(d.apellido_materno, '')) AS docente_coordinador,
        p.promocion_descuento,
        p.cupos_inscritos,
        p.cupos_maximos
    FROM inscripciones i
    INNER JOIN programas p ON i.programa_id = p.id
    LEFT JOIN docentes d ON p.docente_coordinador_id = d.id
    LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
        AND i.programa_id = t.programa_id 
        AND t.estado = 'CONFIRMADO'
    WHERE i.estudiante_id = p_estudiante_id
    GROUP BY 
        p.id, p.codigo, p.nombre, p.estado, i.estado, i.fecha_inscripcion,
        p.fecha_inicio, p.fecha_fin, p.duracion_meses, p.horas_totales,
        p.costo_total, d.nombres, d.apellido_paterno, d.apellido_materno,
        p.promocion_descuento, p.cupos_inscritos, p.cupos_maximos
    ORDER BY 
        CASE 
            WHEN p.estado = 'EN_CURSO' THEN 1
            WHEN p.estado = 'PLANIFICADO' THEN 2
            WHEN p.estado = 'FINALIZADO' THEN 3
            ELSE 4
        END,
        i.fecha_inscripcion DESC;
END;
$$;


-- Función para obtener el detalle de pagos por programa de un estudiante
CREATE OR REPLACE FUNCTION fn_obtener_pagos_estudiante_programa(
    p_estudiante_id INTEGER,
    p_programa_id INTEGER DEFAULT NULL
)
RETURNS TABLE(
    transaccion_id INTEGER,
    numero_transaccion VARCHAR,
    fecha_pago DATE,
    forma_pago d_forma_pago,
    monto_total DECIMAL(10,2),
    descuento_total DECIMAL(10,2),
    monto_final DECIMAL(10,2),
    estado_transaccion d_estado_transaccion,
    numero_comprobante VARCHAR,
    observaciones TEXT,
    detalles TEXT,
    programa_nombre VARCHAR,
    programa_codigo VARCHAR,
    usuario_registro VARCHAR
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        t.id AS transaccion_id,
        t.numero_transaccion,
        t.fecha_pago,
        t.forma_pago,
        t.monto_total,
        t.descuento_total,
        t.monto_final,
        t.estado AS estado_transaccion,
        t.numero_comprobante,
        t.observaciones,
        STRING_AGG(
            CONCAT(
                cp.nombre, ': ', 
                dt.cantidad, ' x ', 
                dt.precio_unitario, ' = ', 
                dt.subtotal
            ), 
            '; '
        ) AS detalles,
        p.nombre AS programa_nombre,
        p.codigo AS programa_codigo,
        u.nombre_completo AS usuario_registro
    FROM transacciones t
    INNER JOIN estudiantes e ON t.estudiante_id = e.id
    LEFT JOIN programas p ON t.programa_id = p.id
    LEFT JOIN usuarios u ON t.registrado_por = u.id
    LEFT JOIN detalles_transaccion dt ON t.id = dt.transaccion_id
    LEFT JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
    WHERE t.estudiante_id = p_estudiante_id
        AND (p_programa_id IS NULL OR t.programa_id = p_programa_id)
        AND t.estado = 'CONFIRMADO'
    GROUP BY 
        t.id, t.numero_transaccion, t.fecha_pago, t.forma_pago,
        t.monto_total, t.descuento_total, t.monto_final, t.estado,
        t.numero_comprobante, t.observaciones, p.nombre, p.codigo,
        u.nombre_completo
    ORDER BY t.fecha_pago DESC;
END;
$$;

-- Función para obtener resumen financiero del estudiante
CREATE OR REPLACE FUNCTION fn_resumen_financiero_estudiante(p_estudiante_id INTEGER)
RETURNS TABLE(
    total_programas INTEGER,
    total_inscrito DECIMAL(12,2),
    total_pagado DECIMAL(12,2),
    total_deuda DECIMAL(12,2),
    promedio_pagado DECIMAL(5,2),
    transacciones_totales INTEGER,
    ultimo_pago DATE,
    proximo_vencimiento DATE,
    estado_financiero VARCHAR(20)
) 
LANGUAGE plpgsql
AS $$
DECLARE
    v_ultimo_pago DATE;
    v_proximo_vencimiento DATE;
BEGIN
    -- Obtener datos básicos
    RETURN QUERY
    WITH programas_estudiante AS (
        SELECT 
            i.programa_id,
            p.costo_total,
            COALESCE(SUM(t.monto_final), 0) AS pagado
        FROM inscripciones i
        INNER JOIN programas p ON i.programa_id = p.id
        LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
            AND i.programa_id = t.programa_id
            AND t.estado = 'CONFIRMADO'
        WHERE i.estudiante_id = p_estudiante_id
        GROUP BY i.programa_id, p.costo_total
    ),
    transacciones_estudiante AS (
        SELECT 
            COUNT(*) AS total,
            MAX(fecha_pago) AS ultima_fecha
        FROM transacciones
        WHERE estudiante_id = p_estudiante_id
            AND estado = 'CONFIRMADO'
    )
    SELECT 
        COUNT(*)::INTEGER AS total_programas,
        SUM(costo_total)::DECIMAL(12,2) AS total_inscrito,
        SUM(pagado)::DECIMAL(12,2) AS total_pagado,
        SUM(GREATEST(costo_total - pagado, 0))::DECIMAL(12,2) AS total_deuda,
        CASE 
            WHEN SUM(costo_total) > 0 THEN 
                ROUND((SUM(pagado) * 100.0 / SUM(costo_total)), 2)
            ELSE 0 
        END AS promedio_pagado,
        COALESCE(te.total, 0)::INTEGER AS transacciones_totales,
        te.ultima_fecha AS ultimo_pago,
        NULL::DATE AS proximo_vencimiento,
        CASE 
            WHEN SUM(costo_total) = 0 THEN 'SIN_PROGRAMAS'
            WHEN SUM(pagado) >= SUM(costo_total) THEN 'AL_DIA'
            WHEN SUM(pagado) >= (SUM(costo_total) * 0.5) THEN 'PARCIAL'
            ELSE 'MOROSO'
        END::VARCHAR(20) AS estado_financiero
    FROM programas_estudiante pe
    CROSS JOIN transacciones_estudiante te;
END;
$$;

-- Función para obtener cronograma de pagos sugerido
CREATE OR REPLACE FUNCTION fn_cronograma_pagos_estudiante(p_estudiante_id INTEGER)
RETURNS TABLE(
    programa_id INTEGER,
    programa_nombre VARCHAR,
    mes_pago INTEGER,
    concepto VARCHAR,
    monto_sugerido DECIMAL(10,2),
    fecha_sugerida DATE,
    estado VARCHAR(20)
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH programas_deuda AS (
        SELECT 
            i.programa_id,
            p.nombre AS programa_nombre,
            p.costo_total,
            p.numero_cuotas,
            p.fecha_inicio,
            COALESCE(SUM(t.monto_final), 0) AS pagado,
            GREATEST(p.costo_total - COALESCE(SUM(t.monto_final), 0), 0) AS saldo_pendiente
        FROM inscripciones i
        INNER JOIN programas p ON i.programa_id = p.id
        LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
            AND i.programa_id = t.programa_id
            AND t.estado = 'CONFIRMADO'
        WHERE i.estudiante_id = p_estudiante_id
            AND p.costo_total > COALESCE(SUM(t.monto_final), 0)
        GROUP BY i.programa_id, p.nombre, p.costo_total, p.numero_cuotas, p.fecha_inicio
    )
    SELECT 
        pd.programa_id,
        pd.programa_nombre,
        gs.mes AS mes_pago,
        CONCAT('Cuota ', gs.mes, ' - ', pd.programa_nombre) AS concepto,
        ROUND(pd.saldo_pendiente / pd.numero_cuotas, 2) AS monto_sugerido,
        (pd.fecha_inicio + (gs.mes - 1) * INTERVAL '1 month')::DATE AS fecha_sugerida,
        CASE 
            WHEN (pd.fecha_inicio + (gs.mes - 1) * INTERVAL '1 month') < CURRENT_DATE THEN 'VENCIDO'
            ELSE 'PENDIENTE'
        END AS estado
    FROM programas_deuda pd
    CROSS JOIN generate_series(1, pd.numero_cuotas) AS gs(mes)
    WHERE (pd.fecha_inicio + (gs.mes - 1) * INTERVAL '1 month') >= CURRENT_DATE - INTERVAL '1 month'
    ORDER BY pd.programa_id, gs.mes;
END;
$$;

-- Función para realizar inscripción completa de estudiante a programa
CREATE OR REPLACE FUNCTION fn_inscripcion_completa(
    p_estudiante_data JSONB,
    p_programa_id INTEGER
)
RETURNS TABLE(
    estudiante_id INTEGER,
    programa_id INTEGER,
    inscripcion_exito BOOLEAN,
    mensaje_estudiante VARCHAR,
    mensaje_inscripcion VARCHAR,
    cupos_disponibles INTEGER,
    costo_total DECIMAL(10,2),
    detalles_pago JSONB
) 
LANGUAGE plpgsql
AS $$
DECLARE
    v_estudiante_id INTEGER;
    v_inscripcion_result RECORD;
    v_programa_data RECORD;
    v_costo_total DECIMAL(10,2);
BEGIN
    -- 1. Insertar o verificar estudiante
    IF (p_estudiante_data->>'id')::INTEGER IS NULL THEN
        -- Estudiante nuevo
        SELECT * INTO v_estudiante_id
        FROM fn_insertar_estudiante(
            p_estudiante_data->>'ci_numero',
            (p_estudiante_data->>'ci_expedicion')::d_expedicion_ci,
            p_estudiante_data->>'nombres',
            p_estudiante_data->>'apellido_paterno',
            p_estudiante_data->>'apellido_materno',
            NULLIF(p_estudiante_data->>'fecha_nacimiento', '')::DATE,
            p_estudiante_data->>'telefono',
            p_estudiante_data->>'email',
            p_estudiante_data->>'direccion',
            p_estudiante_data->>'profesion',
            p_estudiante_data->>'universidad',
            p_estudiante_data->>'fotografia_url',
            TRUE
        ) WHERE exito = TRUE;
    ELSE
        -- Estudiante existente
        v_estudiante_id := (p_estudiante_data->>'id')::INTEGER;
    END IF;
    
    -- 2. Verificar que se obtuvo el ID del estudiante
    IF v_estudiante_id IS NULL THEN
        RETURN QUERY SELECT 
            NULL::INTEGER,
            p_programa_id,
            FALSE,
            'Error al registrar estudiante',
            NULL,
            NULL,
            NULL,
            NULL::JSONB;
        RETURN;
    END IF;
    
    -- 3. Obtener información del programa
    SELECT * INTO v_programa_data
    FROM programas 
    WHERE id = p_programa_id;
    
    IF NOT FOUND THEN
        RETURN QUERY SELECT 
            v_estudiante_id,
            p_programa_id,
            FALSE,
            'Estudiante registrado exitosamente',
            'Programa no encontrado',
            NULL,
            NULL,
            NULL::JSONB;
        RETURN;
    END IF;
    
    -- 4. Realizar inscripción
    SELECT * INTO v_inscripcion_result
    FROM fn_inscribir_estudiante_programa(p_programa_id, v_estudiante_id);
    
    -- 5. Preparar respuesta
    v_costo_total := v_programa_data.costo_total;
    
    RETURN QUERY SELECT 
        v_estudiante_id,
        p_programa_id,
        v_inscripcion_result.exito,
        'Estudiante registrado exitosamente',
        v_inscripcion_result.mensaje,
        v_inscripcion_result.cupos_disponibles,
        v_costo_total,
        jsonb_build_object(
            'matricula', v_programa_data.costo_matricula,
            'inscripcion', v_programa_data.costo_inscripcion,
            'mensualidad', v_programa_data.costo_mensualidad,
            'descuento_promocion', v_programa_data.promocion_descuento,
            'numero_cuotas', v_programa_data.numero_cuotas,
            'fecha_inicio', v_programa_data.fecha_inicio,
            'fecha_fin', v_programa_data.fecha_fin
        ) AS detalles_pago;
END;
$$;

-- Función para obtener información completa del estudiante con todas sus relaciones
CREATE OR REPLACE FUNCTION fn_buscar_informacion_completa_estudiante(p_estudiante_id INTEGER)
RETURNS TABLE(
    -- Información del estudiante
    estudiante_id INTEGER,
    ci_numero VARCHAR,
    ci_expedicion d_expedicion_ci,
    nombres_completos VARCHAR,
    apellidos_completos VARCHAR,
    fecha_nacimiento DATE,
    telefono VARCHAR,
    email VARCHAR,
    direccion TEXT,
    profesion VARCHAR,
    universidad VARCHAR,
    fotografia_url TEXT,
    estudiante_activo BOOLEAN,
    fecha_registro_estudiante TIMESTAMP,
    
    -- Información del programa académico
    programa_id INTEGER,
    programa_codigo VARCHAR,
    programa_nombre VARCHAR,
    programa_descripcion TEXT,
    programa_duracion_meses INTEGER,
    programa_horas_totales INTEGER,
    programa_costo_total DECIMAL(10,2),
    programa_costo_matricula DECIMAL(10,2),
    programa_costo_inscripcion DECIMAL(10,2),
    programa_costo_mensualidad DECIMAL(10,2),
    programa_numero_cuotas INTEGER,
    programa_estado d_estado_programa,
    programa_fecha_inicio DATE,
    programa_fecha_fin DATE,
    programa_cupos_inscritos INTEGER,
    programa_cupos_maximos INTEGER,
    programa_promocion_descuento DECIMAL(5,2),
    
    -- Información de la inscripción
    inscripcion_id INTEGER,
    inscripcion_estado d_estado_academico,
    fecha_inscripcion DATE,
    inscripcion_descuento_aplicado DECIMAL(10,2),
    inscripcion_observaciones TEXT,
    
    -- Información de transacciones/pagos
    transaccion_id INTEGER,
    numero_transaccion VARCHAR,
    transaccion_fecha_pago DATE,
    transaccion_fecha_registro TIMESTAMP,
    transaccion_monto_total DECIMAL(10,2),
    transaccion_descuento_total DECIMAL(10,2),
    transaccion_monto_final DECIMAL(10,2),
    transaccion_forma_pago d_forma_pago,
    transaccion_estado d_estado_transaccion,
    transaccion_numero_comprobante VARCHAR,
    transaccion_banco_origen VARCHAR,
    transaccion_cuenta_origen VARCHAR,
    transaccion_observaciones TEXT,
    
    -- Detalles de la transacción
    detalle_transaccion_id INTEGER,
    concepto_pago_codigo VARCHAR,
    concepto_pago_nombre VARCHAR,
    detalle_descripcion VARCHAR,
    detalle_cantidad INTEGER,
    detalle_precio_unitario DECIMAL(10,2),
    detalle_subtotal DECIMAL(10,2),
    
    -- Información de facturación
    factura_id INTEGER,
    numero_factura VARCHAR,
    factura_nit_ci VARCHAR,
    factura_razon_social VARCHAR,
    factura_fecha_emision DATE,
    factura_subtotal DECIMAL(12,2),
    factura_iva DECIMAL(12,2),
    factura_it DECIMAL(12,2),
    factura_total DECIMAL(12,2),
    factura_estado VARCHAR,
    
    -- Información del usuario que registró
    usuario_registro_id INTEGER,
    usuario_registro_nombre VARCHAR,
    usuario_registro_rol d_rol_usuario,
    
    -- Información del docente coordinador
    docente_coordinador_id INTEGER,
    docente_coordinador_nombre VARCHAR,
    docente_grado_academico d_grado_academico,
    
    -- Información de movimiento de caja
    movimiento_caja_id INTEGER,
    movimiento_caja_fecha DATE,
    movimiento_caja_tipo d_tipo_movimiento,
    movimiento_caja_descripcion VARCHAR,
    
    -- Estadísticas y resúmenes
    total_pagado_programa DECIMAL(12,2),
    saldo_pendiente_programa DECIMAL(12,2),
    porcentaje_pagado_programa DECIMAL(5,2),
    cuotas_pagadas INTEGER,
    cuotas_pendientes INTEGER
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH estadisticas_programa AS (
        SELECT 
            t.programa_id,
            t.estudiante_id,
            COUNT(DISTINCT t.id) AS cuotas_pagadas,
            SUM(t.monto_final) AS total_pagado
        FROM transacciones t
        WHERE t.estudiante_id = p_estudiante_id
            AND t.estado = 'CONFIRMADO'
        GROUP BY t.programa_id, t.estudiante_id
    ),
    programa_info AS (
        SELECT 
            p.id AS programa_id,
            p.numero_cuotas,
            p.costo_total,
            COUNT(DISTINCT CASE WHEN t.estado = 'CONFIRMADO' THEN t.id END) AS cuotas_confirmadas
        FROM programas p
        LEFT JOIN transacciones t ON p.id = t.programa_id 
            AND t.estudiante_id = p_estudiante_id
        GROUP BY p.id, p.numero_cuotas, p.costo_total
    )
    SELECT DISTINCT
        -- Información del estudiante
        e.id AS estudiante_id,
        e.ci_numero,
        e.ci_expedicion,
        CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) AS nombres_completos,
        CONCAT(e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) AS apellidos_completos,
        e.fecha_nacimiento,
        e.telefono,
        e.email,
        e.direccion,
        e.profesion,
        e.universidad,
        e.fotografia_url,
        e.activo AS estudiante_activo,
        e.fecha_registro AS fecha_registro_estudiante,
        
        -- Información del programa académico
        p.id AS programa_id,
        p.codigo AS programa_codigo,
        p.nombre AS programa_nombre,
        p.descripcion AS programa_descripcion,
        p.duracion_meses AS programa_duracion_meses,
        p.horas_totales AS programa_horas_totales,
        p.costo_total AS programa_costo_total,
        p.costo_matricula AS programa_costo_matricula,
        p.costo_inscripcion AS programa_costo_inscripcion,
        p.costo_mensualidad AS programa_costo_mensualidad,
        p.numero_cuotas AS programa_numero_cuotas,
        p.estado AS programa_estado,
        p.fecha_inicio AS programa_fecha_inicio,
        p.fecha_fin AS programa_fecha_fin,
        p.cupos_inscritos AS programa_cupos_inscritos,
        p.cupos_maximos AS programa_cupos_maximos,
        p.promocion_descuento AS programa_promocion_descuento,
        
        -- Información de la inscripción
        i.id AS inscripcion_id,
        i.estado AS inscripcion_estado,
        i.fecha_inscripcion,
        i.descuento_aplicado AS inscripcion_descuento_aplicado,
        i.observaciones AS inscripcion_observaciones,
        
        -- Información de transacciones/pagos
        t.id AS transaccion_id,
        t.numero_transaccion,
        t.fecha_pago AS transaccion_fecha_pago,
        t.fecha_registro AS transaccion_fecha_registro,
        t.monto_total AS transaccion_monto_total,
        t.descuento_total AS transaccion_descuento_total,
        t.monto_final AS transaccion_monto_final,
        t.forma_pago AS transaccion_forma_pago,
        t.estado AS transaccion_estado,
        t.numero_comprobante AS transaccion_numero_comprobante,
        t.banco_origen AS transaccion_banco_origen,
        t.cuenta_origen AS transaccion_cuenta_origen,
        t.observaciones AS transaccion_observaciones,
        
        -- Detalles de la transacción
        dt.id AS detalle_transaccion_id,
        cp.codigo AS concepto_pago_codigo,
        cp.nombre AS concepto_pago_nombre,
        dt.descripcion AS detalle_descripcion,
        dt.cantidad AS detalle_cantidad,
        dt.precio_unitario AS detalle_precio_unitario,
        dt.subtotal AS detalle_subtotal,
        
        -- Información de facturación
        f.id AS factura_id,
        f.numero_factura,
        f.nit_ci AS factura_nit_ci,
        f.razon_social AS factura_razon_social,
        f.fecha_emision AS factura_fecha_emision,
        f.subtotal AS factura_subtotal,
        f.iva AS factura_iva,
        f.it AS factura_it,
        f.total AS factura_total,
        f.estado AS factura_estado,
        
        -- Información del usuario que registró
        u.id AS usuario_registro_id,
        u.nombre_completo AS usuario_registro_nombre,
        u.rol AS usuario_registro_rol,
        
        -- Información del docente coordinador
        d.id AS docente_coordinador_id,
        CONCAT(d.nombres, ' ', d.apellido_paterno, ' ', COALESCE(d.apellido_materno, '')) AS docente_coordinador_nombre,
        d.grado_academico AS docente_grado_academico,
        
        -- Información de movimiento de caja
        mc.id AS movimiento_caja_id,
        mc.fecha AS movimiento_caja_fecha,
        mc.tipo AS movimiento_caja_tipo,
        mc.descripcion AS movimiento_caja_descripcion,
        
        -- Estadísticas y resúmenes
        COALESCE(ep.total_pagado, 0) AS total_pagado_programa,
        GREATEST(p.costo_total - COALESCE(ep.total_pagado, 0), 0) AS saldo_pendiente_programa,
        CASE 
            WHEN p.costo_total > 0 THEN 
                ROUND((COALESCE(ep.total_pagado, 0) * 100.0 / p.costo_total), 2)
            ELSE 0 
        END AS porcentaje_pagado_programa,
        COALESCE(ep.cuotas_pagadas, 0) AS cuotas_pagadas,
        GREATEST(p.numero_cuotas - COALESCE(ep.cuotas_pagadas, 0), 0) AS cuotas_pendientes
        
    FROM estudiantes e
    
    -- Inscripciones del estudiante
    LEFT JOIN inscripciones i ON e.id = i.estudiante_id
    
    -- Programas a los que está inscrito
    LEFT JOIN programas p ON i.programa_id = p.id
    
    -- Transacciones/pagos relacionados
    LEFT JOIN transacciones t ON e.id = t.estudiante_id 
        AND (i.programa_id = t.programa_id OR t.programa_id IS NULL)
    
    -- Detalles de transacción
    LEFT JOIN detalles_transaccion dt ON t.id = dt.transaccion_id
    
    -- Conceptos de pago
    LEFT JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
    
    -- Facturas relacionadas
    LEFT JOIN facturas f ON t.id = f.transaccion_id
    
    -- Usuario que registró la transacción
    LEFT JOIN usuarios u ON t.registrado_por = u.id
    
    -- Docente coordinador del programa
    LEFT JOIN docentes d ON p.docente_coordinador_id = d.id
    
    -- Movimientos de caja relacionados
    LEFT JOIN movimientos_caja mc ON t.id = mc.transaccion_id
    
    -- Estadísticas del programa
    LEFT JOIN estadisticas_programa ep ON p.id = ep.programa_id AND e.id = ep.estudiante_id
    
    WHERE e.id = p_estudiante_id
    
    ORDER BY 
        p.id NULLS FIRST,
        t.fecha_pago DESC NULLS FIRST,
        dt.orden ASC NULLS FIRST,
        f.fecha_emision DESC NULLS FIRST;
END;
$$;

-- Función alternativa simplificada para vista rápida
CREATE OR REPLACE FUNCTION fn_resumen_estudiante_completo(p_estudiante_id INTEGER)
RETURNS TABLE(
    estudiante_id INTEGER,
    nombres_completos VARCHAR,
    ci_completo VARCHAR,
    telefono VARCHAR,
    email VARCHAR,
    programa_id INTEGER,
    programa_nombre VARCHAR,
    programa_estado d_estado_programa,
    inscripcion_estado d_estado_academico,
    transaccion_id INTEGER,
    numero_transaccion VARCHAR,
    fecha_pago DATE,
    monto_final DECIMAL(10,2),
    forma_pago d_forma_pago,
    transaccion_estado d_estado_transaccion,
    concepto_pago VARCHAR,
    cantidad INTEGER,
    subtotal DECIMAL(10,2),
    factura_numero VARCHAR,
    factura_total DECIMAL(12,2),
    usuario_registro VARCHAR
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id AS estudiante_id,
        CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) AS nombres_completos,
        CONCAT(e.ci_numero, ' ', e.ci_expedicion) AS ci_completo,
        e.telefono,
        e.email,
        p.id AS programa_id,
        p.nombre AS programa_nombre,
        p.estado AS programa_estado,
        i.estado AS inscripcion_estado,
        t.id AS transaccion_id,
        t.numero_transaccion,
        t.fecha_pago,
        t.monto_final,
        t.forma_pago,
        t.estado AS transaccion_estado,
        cp.nombre AS concepto_pago,
        dt.cantidad,
        dt.subtotal,
        f.numero_factura AS factura_numero,
        f.total AS factura_total,
        u.nombre_completo AS usuario_registro
    FROM estudiantes e
    LEFT JOIN inscripciones i ON e.id = i.estudiante_id
    LEFT JOIN programas p ON i.programa_id = p.id
    LEFT JOIN transacciones t ON e.id = t.estudiante_id 
        AND (i.programa_id = t.programa_id OR t.programa_id IS NULL)
    LEFT JOIN detalles_transaccion dt ON t.id = dt.transaccion_id
    LEFT JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
    LEFT JOIN facturas f ON t.id = f.transaccion_id
    LEFT JOIN usuarios u ON t.registrado_por = u.id
    WHERE e.id = p_estudiante_id
    ORDER BY 
        p.id NULLS FIRST,
        t.fecha_pago DESC NULLS FIRST,
        dt.orden ASC NULLS FIRST;
END;
$$;

-- Ejemplos de uso:
-- SELECT * FROM fn_buscar_informacion_completa_estudiante(102);
-- SELECT * FROM fn_resumen_estudiante_completo(102);

-- Función para obtener vista resumida por programa
CREATE OR REPLACE FUNCTION fn_estudiante_programas_resumen(p_estudiante_id INTEGER)
RETURNS TABLE(
    estudiante_id INTEGER,
    estudiante_nombre VARCHAR,
    programa_id INTEGER,
    programa_codigo VARCHAR,
    programa_nombre VARCHAR,
    programa_estado d_estado_programa,
    fecha_inscripcion DATE,
    inscripcion_estado d_estado_academico,
    costo_total DECIMAL(10,2),
    total_pagado DECIMAL(10,2),
    saldo_pendiente DECIMAL(10,2),
    porcentaje_pagado DECIMAL(5,2),
    transacciones_count INTEGER,
    ultima_transaccion_date DATE,
    ultima_transaccion_amount DECIMAL(10,2),
    facturas_count INTEGER,
    facturas_total DECIMAL(12,2)
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id AS estudiante_id,
        CONCAT(e.nombres, ' ', e.apellido_paterno) AS estudiante_nombre,
        p.id AS programa_id,
        p.codigo AS programa_codigo,
        p.nombre AS programa_nombre,
        p.estado AS programa_estado,
        i.fecha_inscripcion,
        i.estado AS inscripcion_estado,
        p.costo_total,
        COALESCE(SUM(t.monto_final), 0) AS total_pagado,
        GREATEST(p.costo_total - COALESCE(SUM(t.monto_final), 0), 0) AS saldo_pendiente,
        CASE 
            WHEN p.costo_total > 0 THEN 
                ROUND((COALESCE(SUM(t.monto_final), 0) * 100.0 / p.costo_total), 2)
            ELSE 0 
        END AS porcentaje_pagado,
        COUNT(DISTINCT t.id) AS transacciones_count,
        MAX(t.fecha_pago) AS ultima_transaccion_date,
        MAX(CASE WHEN t.fecha_pago = (SELECT MAX(fecha_pago) FROM transacciones 
                                     WHERE estudiante_id = e.id AND programa_id = p.id) 
                THEN t.monto_final END) AS ultima_transaccion_amount,
        COUNT(DISTINCT f.id) AS facturas_count,
        COALESCE(SUM(f.total), 0) AS facturas_total
    FROM estudiantes e
    INNER JOIN inscripciones i ON e.id = i.estudiante_id
    INNER JOIN programas p ON i.programa_id = p.id
    LEFT JOIN transacciones t ON e.id = t.estudiante_id AND p.id = t.programa_id AND t.estado = 'CONFIRMADO'
    LEFT JOIN facturas f ON t.id = f.transaccion_id
    WHERE e.id = p_estudiante_id
    GROUP BY 
        e.id, e.nombres, e.apellido_paterno,
        p.id, p.codigo, p.nombre, p.estado, p.costo_total,
        i.fecha_inscripcion, i.estado
    ORDER BY i.fecha_inscripcion DESC;
END;
$$;

-- Función para obtener transacciones detalladas por estudiante
CREATE OR REPLACE FUNCTION fn_estudiante_transacciones_detalle(p_estudiante_id INTEGER)
RETURNS TABLE(
    row_number BIGINT,
    estudiante_id INTEGER,
    estudiante_nombre VARCHAR,
    programa_id INTEGER,
    programa_nombre VARCHAR,
    transaccion_id INTEGER,
    numero_transaccion VARCHAR,
    fecha_pago DATE,
    forma_pago d_forma_pago,
    monto_total DECIMAL(10,2),
    descuento_total DECIMAL(10,2),
    monto_final DECIMAL(10,2),
    transaccion_estado d_estado_transaccion,
    numero_comprobante VARCHAR,
    conceptos TEXT,
    factura_numero VARCHAR,
    usuario_registro VARCHAR,
    observaciones TEXT
) 
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT 
        ROW_NUMBER() OVER (ORDER BY t.fecha_pago DESC, t.id DESC) AS row_number,
        e.id AS estudiante_id,
        CONCAT(e.nombres, ' ', e.apellido_paterno) AS estudiante_nombre,
        p.id AS programa_id,
        p.nombre AS programa_nombre,
        t.id AS transaccion_id,
        t.numero_transaccion,
        t.fecha_pago,
        t.forma_pago,
        t.monto_total,
        t.descuento_total,
        t.monto_final,
        t.estado AS transaccion_estado,
        t.numero_comprobante,
        STRING_AGG(
            CONCAT(cp.nombre, ' (', dt.cantidad, ' x ', dt.precio_unitario, ') = ', dt.subtotal),
            '; '
        ) AS conceptos,
        f.numero_factura,
        u.nombre_completo AS usuario_registro,
        t.observaciones
    FROM estudiantes e
    LEFT JOIN transacciones t ON e.id = t.estudiante_id
    LEFT JOIN programas p ON t.programa_id = p.id
    LEFT JOIN detalles_transaccion dt ON t.id = dt.transaccion_id
    LEFT JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
    LEFT JOIN facturas f ON t.id = f.transaccion_id
    LEFT JOIN usuarios u ON t.registrado_por = u.id
    WHERE e.id = p_estudiante_id
    GROUP BY 
        e.id, e.nombres, e.apellido_paterno,
        p.id, p.nombre,
        t.id, t.numero_transaccion, t.fecha_pago, t.forma_pago,
        t.monto_total, t.descuento_total, t.monto_final, t.estado,
        t.numero_comprobante, f.numero_factura, u.nombre_completo, t.observaciones
    ORDER BY t.fecha_pago DESC, t.id DESC;
END;
$$;
