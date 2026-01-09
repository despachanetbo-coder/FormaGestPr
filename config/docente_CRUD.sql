-- ============================================================
-- FUNCIONES Y PROCEDIMIENTOS ALMACENADOS PARA CRUD DE DOCENTES
-- ============================================================

-- 2.1 Función para buscar docentes con filtros
CREATE OR REPLACE FUNCTION fn_buscar_docentes(
    p_ci_numero VARCHAR DEFAULT NULL,
    p_ci_expedicion VARCHAR DEFAULT NULL,
    p_nombre VARCHAR DEFAULT NULL,
    p_grado_academico VARCHAR DEFAULT NULL,
    p_activo BOOLEAN DEFAULT NULL,
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
    grado_academico d_grado_academico,
    titulo_profesional VARCHAR,
    especialidad VARCHAR,
    telefono VARCHAR,
    email VARCHAR,
    curriculum_url TEXT,
    honorario_hora DECIMAL,
    activo BOOLEAN,
    fecha_registro TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id, d.ci_numero, d.ci_expedicion, d.nombres, d.apellido_paterno, 
        d.apellido_materno, d.fecha_nacimiento, d.grado_academico, d.titulo_profesional, 
        d.especialidad, d.telefono, d.email, d.curriculum_url, d.honorario_hora, 
        d.activo, d.fecha_registro
    FROM docentes d
    WHERE 
        (p_ci_numero IS NULL OR d.ci_numero ILIKE '%' || p_ci_numero || '%')
        AND (p_ci_expedicion IS NULL OR d.ci_expedicion = p_ci_expedicion OR p_ci_expedicion = 'Todos')
        AND (
            p_nombre IS NULL OR 
            d.nombres ILIKE '%' || p_nombre || '%' OR 
            d.apellido_paterno ILIKE '%' || p_nombre || '%' OR 
            d.apellido_materno ILIKE '%' || p_nombre || '%'
        )
        AND (p_grado_academico IS NULL OR d.grado_academico = p_grado_academico OR p_grado_academico = 'Todos')
        AND (p_activo IS NULL OR d.activo = p_activo)
    ORDER BY d.apellido_paterno, d.apellido_materno, d.nombres
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- 2.2 Función para contar docentes con filtros
CREATE OR REPLACE FUNCTION fn_contar_docentes(
    p_ci_numero VARCHAR DEFAULT NULL,
    p_ci_expedicion VARCHAR DEFAULT NULL,
    p_nombre VARCHAR DEFAULT NULL,
    p_grado_academico VARCHAR DEFAULT NULL,
    p_activo BOOLEAN DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_total INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO v_total
    FROM docentes d
    WHERE 
        (p_ci_numero IS NULL OR d.ci_numero ILIKE '%' || p_ci_numero || '%')
        AND (p_ci_expedicion IS NULL OR d.ci_expedicion = p_ci_expedicion OR p_ci_expedicion = 'Todos')
        AND (
            p_nombre IS NULL OR 
            d.nombres ILIKE '%' || p_nombre || '%' OR 
            d.apellido_paterno ILIKE '%' || p_nombre || '%' OR 
            d.apellido_materno ILIKE '%' || p_nombre || '%'
        )
        AND (p_grado_academico IS NULL OR d.grado_academico = p_grado_academico OR p_grado_academico = 'Todos')
        AND (p_activo IS NULL OR d.activo = p_activo);
    
    RETURN COALESCE(v_total, 0);
END;
$$ LANGUAGE plpgsql;

-- 2.3 Función para obtener docente por ID
CREATE OR REPLACE FUNCTION fn_obtener_docente_por_id(p_id INTEGER)
RETURNS TABLE(
    id INTEGER,
    ci_numero VARCHAR,
    ci_expedicion d_expedicion_ci,
    nombres VARCHAR,
    apellido_paterno VARCHAR,
    apellido_materno VARCHAR,
    fecha_nacimiento DATE,
    grado_academico d_grado_academico,
    titulo_profesional VARCHAR,
    especialidad VARCHAR,
    telefono VARCHAR,
    email VARCHAR,
    curriculum_url TEXT,
    honorario_hora DECIMAL,
    activo BOOLEAN,
    fecha_registro TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        d.id, d.ci_numero, d.ci_expedicion, d.nombres, d.apellido_paterno, 
        d.apellido_materno, d.fecha_nacimiento, d.grado_academico, d.titulo_profesional, 
        d.especialidad, d.telefono, d.email, d.curriculum_url, d.honorario_hora, 
        d.activo, d.fecha_registro
    FROM docentes d
    WHERE d.id = p_id;
END;
$$ LANGUAGE plpgsql;

-- 2.4 Función para verificar si CI ya existe (para validación)
CREATE OR REPLACE FUNCTION fn_verificar_ci_docente_existente(
    p_ci_numero VARCHAR,
    p_excluir_id INTEGER DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_existe BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 
        FROM docentes 
        WHERE ci_numero = p_ci_numero 
        AND (p_excluir_id IS NULL OR id != p_excluir_id)
    ) INTO v_existe;
    
    RETURN v_existe;
END;
$$ LANGUAGE plpgsql;

-- 2.5 Función para insertar nuevo docente
CREATE OR REPLACE FUNCTION fn_insertar_docente(
    p_ci_numero VARCHAR,
    p_ci_expedicion d_expedicion_ci,
    p_nombres VARCHAR,
    p_apellido_paterno VARCHAR,
    p_apellido_materno VARCHAR,
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_grado_academico d_grado_academico DEFAULT NULL,
    p_titulo_profesional VARCHAR DEFAULT NULL,
    p_especialidad VARCHAR DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_email VARCHAR DEFAULT NULL,
    p_curriculum_url TEXT DEFAULT NULL,
    p_honorario_hora DECIMAL DEFAULT 0,
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
    IF fn_verificar_ci_docente_existente(p_ci_numero) THEN
        v_mensaje := 'El número de CI ya está registrado en el sistema';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar email único si se proporciona
    IF p_email IS NOT NULL AND EXISTS(
        SELECT 1 FROM docentes WHERE email = p_email
    ) THEN
        v_mensaje := 'El email ya está registrado en el sistema';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar honorario hora no negativo
    IF p_honorario_hora < 0 THEN
        v_mensaje := 'El honorario por hora no puede ser negativo';
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Insertar docente
    INSERT INTO docentes (
        ci_numero, ci_expedicion, nombres, apellido_paterno, apellido_materno,
        fecha_nacimiento, grado_academico, titulo_profesional, especialidad,
        telefono, email, curriculum_url, honorario_hora, activo
    ) VALUES (
        p_ci_numero, p_ci_expedicion, p_nombres, p_apellido_paterno, p_apellido_materno,
        p_fecha_nacimiento, p_grado_academico, p_titulo_profesional, p_especialidad,
        p_telefono, p_email, p_curriculum_url, p_honorario_hora, p_activo
    ) RETURNING id INTO v_nuevo_id;
    
    v_mensaje := 'Docente creado exitosamente con ID: ' || v_nuevo_id;
    v_exito := TRUE;
    
    RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al crear docente: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
END;
$$;

-- 2.6 Función para actualizar docente
CREATE OR REPLACE FUNCTION fn_actualizar_docente(
    p_id INTEGER,
    p_ci_numero VARCHAR,
    p_ci_expedicion d_expedicion_ci,
    p_nombres VARCHAR,
    p_apellido_paterno VARCHAR,
    p_apellido_materno VARCHAR,
    p_fecha_nacimiento DATE DEFAULT NULL,
    p_grado_academico d_grado_academico DEFAULT NULL,
    p_titulo_profesional VARCHAR DEFAULT NULL,
    p_especialidad VARCHAR DEFAULT NULL,
    p_telefono VARCHAR DEFAULT NULL,
    p_email VARCHAR DEFAULT NULL,
    p_curriculum_url TEXT DEFAULT NULL,
    p_honorario_hora DECIMAL DEFAULT NULL,
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
    
    -- Validar que el docente exista
    IF NOT EXISTS(SELECT 1 FROM docentes WHERE id = p_id) THEN
        v_mensaje := 'El docente con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar CI único (excluyendo el registro actual)
    IF fn_verificar_ci_docente_existente(p_ci_numero, p_id) THEN
        v_mensaje := 'El número de CI ya está registrado en otro docente';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar email único si se proporciona
    IF p_email IS NOT NULL AND EXISTS(
        SELECT 1 FROM docentes WHERE email = p_email AND id != p_id
    ) THEN
        v_mensaje := 'El email ya está registrado en otro docente';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Validar honorario hora no negativo si se proporciona
    IF p_honorario_hora IS NOT NULL AND p_honorario_hora < 0 THEN
        v_mensaje := 'El honorario por hora no puede ser negativo';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Actualizar docente
    UPDATE docentes
    SET 
        ci_numero = p_ci_numero,
        ci_expedicion = p_ci_expedicion,
        nombres = p_nombres,
        apellido_paterno = p_apellido_paterno,
        apellido_materno = p_apellido_materno,
        fecha_nacimiento = p_fecha_nacimiento,
        grado_academico = p_grado_academico,
        titulo_profesional = p_titulo_profesional,
        especialidad = p_especialidad,
        telefono = p_telefono,
        email = p_email,
        curriculum_url = p_curriculum_url,
        honorario_hora = COALESCE(p_honorario_hora, honorario_hora),
        activo = COALESCE(p_activo, activo)
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Docente actualizado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se realizaron cambios en el docente';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al actualizar docente: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- 2.7 Función para eliminar (desactivar) docente
CREATE OR REPLACE FUNCTION fn_eliminar_docente(p_id INTEGER)
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
    
    -- Validar que el docente exista
    IF NOT EXISTS(SELECT 1 FROM docentes WHERE id = p_id) THEN
        v_mensaje := 'El docente con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- "Eliminar" desactivando (soft delete)
    UPDATE docentes
    SET activo = FALSE
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Docente desactivado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se pudo desactivar el docente';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al eliminar docente: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- 2.8 Función para activar docente
CREATE OR REPLACE FUNCTION fn_activar_docente(p_id INTEGER)
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
    
    -- Validar que el docente exista
    IF NOT EXISTS(SELECT 1 FROM docentes WHERE id = p_id) THEN
        v_mensaje := 'El docente con ID ' || p_id || ' no existe';
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
        RETURN;
    END IF;
    
    -- Activar docente
    UPDATE docentes
    SET activo = TRUE
    WHERE id = p_id;
    
    GET DIAGNOSTICS v_filas_afectadas = ROW_COUNT;
    
    IF v_filas_afectadas > 0 THEN
        v_mensaje := 'Docente activado exitosamente';
        v_exito := TRUE;
    ELSE
        v_mensaje := 'No se pudo activar el docente';
        v_exito := FALSE;
    END IF;
    
    RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
    
EXCEPTION
    WHEN OTHERS THEN
        v_mensaje := 'Error al activar docente: ' || SQLERRM;
        v_exito := FALSE;
        RETURN QUERY SELECT v_filas_afectadas, v_mensaje, v_exito;
END;
$$;

-- 2.9 Función para obtener estadísticas de docentes
CREATE OR REPLACE FUNCTION fn_estadisticas_docentes()
RETURNS TABLE(
    total_docentes INTEGER,
    activos INTEGER,
    inactivos INTEGER,
    promedio_honorario NUMERIC,
    con_email INTEGER,
    con_telefono INTEGER,
    con_curriculum INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER AS total_docentes,
        COUNT(*) FILTER (WHERE activo = TRUE)::INTEGER AS activos,
        COUNT(*) FILTER (WHERE activo = FALSE)::INTEGER AS inactivos,
        AVG(honorario_hora)::NUMERIC AS promedio_honorario,
        COUNT(*) FILTER (WHERE email IS NOT NULL AND email != '')::INTEGER AS con_email,
        COUNT(*) FILTER (WHERE telefono IS NOT NULL AND telefono != '')::INTEGER AS con_telefono,
        COUNT(*) FILTER (WHERE curriculum_url IS NOT NULL AND curriculum_url != '')::INTEGER AS con_curriculum
    FROM docentes;
END;
$$ LANGUAGE plpgsql;