-- ============================================
-- FUNCIONES PARA LA TABLA EMPRESA
-- ============================================

-- Función para ver/obtener los datos de la empresa
CREATE OR REPLACE FUNCTION fn_ver_empresa()
RETURNS TABLE(
    id INTEGER,
    nombre VARCHAR(200),
    nit VARCHAR(20),
    direccion VARCHAR(300),
    telefono VARCHAR(20),
    email VARCHAR(100),
    logo_url TEXT,
    created_at TIMESTAMP
) AS $$
DECLARE
    empresa_record RECORD;
BEGIN
    -- Intentar obtener el primer registro de la empresa
    SELECT * INTO empresa_record FROM empresa LIMIT 1;
    
    -- Si no existe ningún registro, crear uno por defecto
    IF NOT FOUND THEN
        INSERT INTO empresa (nombre, nit, direccion, telefono, email, logo_url)
        VALUES (
            'CONSULTORA FORMACIÓN CONTINUA S.R.L.',
            '194810025',
            NULL,
            NULL,
            NULL,
            NULL
        )
        RETURNING * INTO empresa_record;
    END IF;
    
    -- Retornar el registro
    RETURN QUERY SELECT 
        empresa_record.id,
        empresa_record.nombre,
        empresa_record.nit,
        empresa_record.direccion,
        empresa_record.telefono,
        empresa_record.email,
        empresa_record.logo_url,
        empresa_record.created_at;
END;
$$ LANGUAGE plpgsql;

-- Función para insertar/crear la empresa (solo permite si no existe)
CREATE OR REPLACE FUNCTION fn_insertar_empresa(
    p_nombre VARCHAR(200),
    p_nit VARCHAR(20),
    p_direccion VARCHAR(300),
    p_telefono VARCHAR(20),
    p_email VARCHAR(100),
    p_logo_url TEXT
) RETURNS JSON AS $$
DECLARE
    existing_count INTEGER;
    new_id INTEGER;
BEGIN
    -- Verificar si ya existe algún registro
    SELECT COUNT(*) INTO existing_count FROM empresa;
    
    -- Si ya existe un registro, no permitir insertar otro
    IF existing_count > 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'Ya existe un registro de empresa. No se permiten múltiples registros.',
            'data', NULL
        );
    END IF;
    
    -- Insertar el único registro permitido
    INSERT INTO empresa (nombre, nit, direccion, telefono, email, logo_url)
    VALUES (p_nombre, p_nit, p_direccion, p_telefono, p_email, p_logo_url)
    RETURNING id INTO new_id;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Empresa registrada exitosamente',
        'data', json_build_object('id', new_id)
    );
    
EXCEPTION WHEN unique_violation THEN
    RETURN json_build_object(
        'success', false,
        'message', 'El NIT ya está registrado',
        'data', NULL
    );
END;
$$ LANGUAGE plpgsql;

-- Función para editar/actualizar la empresa
CREATE OR REPLACE FUNCTION fn_editar_empresa(
    p_id INTEGER,
    p_nombre VARCHAR(200),
    p_nit VARCHAR(20),
    p_direccion VARCHAR(300),
    p_telefono VARCHAR(20),
    p_email VARCHAR(100),
    p_logo_url TEXT
) RETURNS JSON AS $$
DECLARE
    rows_affected INTEGER;
    current_nit VARCHAR(20);
BEGIN
    -- Verificar si el NIT ya existe en otro registro (si se está cambiando)
    SELECT nit INTO current_nit FROM empresa WHERE id = p_id;
    
    -- Si el NIT está cambiando, verificar que no exista en otro registro
    IF current_nit != p_nit THEN
        IF EXISTS (SELECT 1 FROM empresa WHERE nit = p_nit AND id != p_id) THEN
            RETURN json_build_object(
                'success', false,
                'message', 'El NIT ya está registrado en otra empresa',
                'data', NULL
            );
        END IF;
    END IF;
    
    -- Actualizar el registro
    UPDATE empresa 
    SET 
        nombre = p_nombre,
        nit = p_nit,
        direccion = p_direccion,
        telefono = p_telefono,
        email = p_email,
        logo_url = p_logo_url
    WHERE id = p_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Verificar si se actualizó correctamente
    IF rows_affected = 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró la empresa con el ID especificado',
            'data', NULL
        );
    END IF;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Empresa actualizada exitosamente',
        'data', json_build_object('id', p_id, 'rows_affected', rows_affected)
    );
    
EXCEPTION WHEN unique_violation THEN
    RETURN json_build_object(
        'success', false,
        'message', 'El NIT ya está registrado',
        'data', NULL
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FUNCIONES PARA LA TABLA CONFIGURACIONES
-- ============================================

-- Función para insertar una configuración
CREATE OR REPLACE FUNCTION fn_insertar_configuracion(
    p_clave VARCHAR(100),
    p_valor TEXT,
    p_descripcion TEXT DEFAULT NULL,
    p_tipo VARCHAR(20) DEFAULT 'TEXTO',
    p_categoria VARCHAR(50) DEFAULT 'GENERAL',
    p_editable BOOLEAN DEFAULT TRUE
) RETURNS JSON AS $$
DECLARE
    new_id INTEGER;
BEGIN
    -- Insertar la nueva configuración
    INSERT INTO configuraciones (clave, valor, descripcion, tipo, categoria, editable)
    VALUES (p_clave, p_valor, p_descripcion, p_tipo, p_categoria, p_editable)
    RETURNING id INTO new_id;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Configuración creada exitosamente',
        'data', json_build_object('id', new_id, 'clave', p_clave)
    );
    
EXCEPTION WHEN unique_violation THEN
    RETURN json_build_object(
        'success', false,
        'message', 'Ya existe una configuración con esta clave',
        'data', NULL
    );
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar una configuración por clave
CREATE OR REPLACE FUNCTION fn_actualizar_configuracion(
    p_clave VARCHAR(100),
    p_valor TEXT,
    p_descripcion TEXT DEFAULT NULL,
    p_tipo VARCHAR(20) DEFAULT NULL,
    p_categoria VARCHAR(50) DEFAULT NULL,
    p_editable BOOLEAN DEFAULT NULL
) RETURNS JSON AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    -- Actualizar la configuración
    UPDATE configuraciones 
    SET 
        valor = p_valor,
        descripcion = COALESCE(p_descripcion, descripcion),
        tipo = COALESCE(p_tipo, tipo),
        categoria = COALESCE(p_categoria, categoria),
        editable = COALESCE(p_editable, editable),
        updated_at = CURRENT_TIMESTAMP
    WHERE clave = p_clave;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Verificar si se actualizó correctamente
    IF rows_affected = 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró la configuración con la clave especificada',
            'data', NULL
        );
    END IF;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Configuración actualizada exitosamente',
        'data', json_build_object('clave', p_clave, 'rows_affected', rows_affected)
    );
END;
$$ LANGUAGE plpgsql;

-- Función para eliminar una configuración por clave
CREATE OR REPLACE FUNCTION fn_eliminar_configuracion(p_clave VARCHAR(100))
RETURNS JSON AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    -- Verificar si la configuración es editable
    IF EXISTS (SELECT 1 FROM configuraciones WHERE clave = p_clave AND editable = FALSE) THEN
        RETURN json_build_object(
            'success', false,
            'message', 'Esta configuración no se puede eliminar porque no es editable',
            'data', NULL
        );
    END IF;
    
    -- Eliminar la configuración
    DELETE FROM configuraciones WHERE clave = p_clave;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Verificar si se eliminó correctamente
    IF rows_affected = 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró la configuración con la clave especificada',
            'data', NULL
        );
    END IF;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Configuración eliminada exitosamente',
        'data', json_build_object('clave', p_clave, 'rows_affected', rows_affected)
    );
END;
$$ LANGUAGE plpgsql;

-- Función para obtener una configuración por clave
CREATE OR REPLACE FUNCTION fn_obtener_configuracion(p_clave VARCHAR(100))
RETURNS TABLE(
    id INTEGER,
    clave VARCHAR(100),
    valor TEXT,
    descripcion TEXT,
    tipo VARCHAR(20),
    categoria VARCHAR(50),
    editable BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        c.id,
        c.clave,
        c.valor,
        c.descripcion,
        c.tipo,
        c.categoria,
        c.editable,
        c.created_at,
        c.updated_at
    FROM configuraciones c
    WHERE c.clave = p_clave;
    
    -- Si no se encuentra, devolver conjunto vacío
    IF NOT FOUND THEN
        RETURN;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Función para buscar configuraciones con filtros
CREATE OR REPLACE FUNCTION fn_buscar_configuraciones(
    p_clave VARCHAR(100) DEFAULT NULL,
    p_categoria VARCHAR(50) DEFAULT NULL,
    p_tipo VARCHAR(20) DEFAULT NULL,
    p_editable BOOLEAN DEFAULT NULL
) RETURNS TABLE(
    id INTEGER,
    clave VARCHAR(100),
    valor TEXT,
    descripcion TEXT,
    tipo VARCHAR(20),
    categoria VARCHAR(50),
    editable BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        c.id,
        c.clave,
        c.valor,
        c.descripcion,
        c.tipo,
        c.categoria,
        c.editable,
        c.created_at,
        c.updated_at
    FROM configuraciones c
    WHERE 
        (p_clave IS NULL OR c.clave ILIKE '%' || p_clave || '%')
        AND (p_categoria IS NULL OR c.categoria = p_categoria)
        AND (p_tipo IS NULL OR c.tipo = p_tipo)
        AND (p_editable IS NULL OR c.editable = p_editable)
    ORDER BY c.categoria, c.clave;
END;
$$ LANGUAGE plpgsql;

-- Función para listar todas las configuraciones
CREATE OR REPLACE FUNCTION fn_listar_configuraciones()
RETURNS TABLE(
    id INTEGER,
    clave VARCHAR(100),
    valor TEXT,
    descripcion TEXT,
    tipo VARCHAR(20),
    categoria VARCHAR(50),
    editable BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        c.id,
        c.clave,
        c.valor,
        c.descripcion,
        c.tipo,
        c.categoria,
        c.editable,
        c.created_at,
        c.updated_at
    FROM configuraciones c
    ORDER BY c.categoria, c.clave;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FUNCIONES PARA LA TABLA USUARIOS
-- ============================================

-- Función para insertar un nuevo usuario
CREATE OR REPLACE FUNCTION fn_insertar_usuario(
    p_username VARCHAR(50),
    p_password_hash TEXT,
    p_nombre_completo VARCHAR(200),
    p_email VARCHAR(100),
    p_rol d_rol_usuario DEFAULT 'CAJERO',
    p_activo BOOLEAN DEFAULT TRUE
) RETURNS JSON AS $$
DECLARE
    new_id INTEGER;
BEGIN
    -- Validar email si se proporciona
    IF p_email IS NOT NULL AND p_email !~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        RETURN json_build_object(
            'success', false,
            'message', 'El formato del email es inválido',
            'data', NULL
        );
    END IF;
    
    -- Insertar el nuevo usuario
    INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol, activo)
    VALUES (p_username, p_password_hash, p_nombre_completo, p_email, p_rol, p_activo)
    RETURNING id INTO new_id;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Usuario creado exitosamente',
        'data', json_build_object('id', new_id, 'username', p_username)
    );
    
EXCEPTION 
    WHEN unique_violation THEN
        RETURN json_build_object(
            'success', false,
            'message', 'El nombre de usuario ya está registrado',
            'data', NULL
        );
    WHEN check_violation THEN
        RETURN json_build_object(
            'success', false,
            'message', 'El email no tiene un formato válido',
            'data', NULL
        );
END;
$$ LANGUAGE plpgsql;

-- Función para actualizar un usuario
CREATE OR REPLACE FUNCTION fn_actualizar_usuario(
    p_id INTEGER,
    p_username VARCHAR(50) DEFAULT NULL,
    p_password_hash TEXT DEFAULT NULL,
    p_nombre_completo VARCHAR(200) DEFAULT NULL,
    p_email VARCHAR(100) DEFAULT NULL,
    p_rol d_rol_usuario DEFAULT NULL,
    p_activo BOOLEAN DEFAULT NULL
) RETURNS JSON AS $$
DECLARE
    rows_affected INTEGER;
    current_username VARCHAR(50);
BEGIN
    -- Verificar si el username ya existe en otro usuario (si se está cambiando)
    IF p_username IS NOT NULL THEN
        SELECT username INTO current_username FROM usuarios WHERE id = p_id;
        
        IF current_username != p_username THEN
            IF EXISTS (SELECT 1 FROM usuarios WHERE username = p_username AND id != p_id) THEN
                RETURN json_build_object(
                    'success', false,
                    'message', 'El nombre de usuario ya está en uso por otro usuario',
                    'data', NULL
                );
            END IF;
        END IF;
    END IF;
    
    -- Validar email si se proporciona
    IF p_email IS NOT NULL AND p_email !~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$' THEN
        RETURN json_build_object(
            'success', false,
            'message', 'El formato del email es inválido',
            'data', NULL
        );
    END IF;
    
    -- Actualizar el usuario
    UPDATE usuarios 
    SET 
        username = COALESCE(p_username, username),
        password_hash = COALESCE(p_password_hash, password_hash),
        nombre_completo = COALESCE(p_nombre_completo, nombre_completo),
        email = COALESCE(p_email, email),
        rol = COALESCE(p_rol, rol),
        activo = COALESCE(p_activo, activo)
    WHERE id = p_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Verificar si se actualizó correctamente
    IF rows_affected = 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró el usuario con el ID especificado',
            'data', NULL
        );
    END IF;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Usuario actualizado exitosamente',
        'data', json_build_object('id', p_id, 'rows_affected', rows_affected)
    );
    
EXCEPTION 
    WHEN unique_violation THEN
        RETURN json_build_object(
            'success', false,
            'message', 'El nombre de usuario ya está registrado',
            'data', NULL
        );
    WHEN check_violation THEN
        RETURN json_build_object(
            'success', false,
            'message', 'El email no tiene un formato válido',
            'data', NULL
        );
END;
$$ LANGUAGE plpgsql;

-- Función para eliminar (desactivar) un usuario
CREATE OR REPLACE FUNCTION fn_eliminar_usuario(p_id INTEGER)
RETURNS JSON AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    -- Desactivar el usuario (eliminación lógica)
    UPDATE usuarios 
    SET activo = FALSE 
    WHERE id = p_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Verificar si se desactivó correctamente
    IF rows_affected = 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró el usuario con el ID especificado',
            'data', NULL
        );
    END IF;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Usuario desactivado exitosamente',
        'data', json_build_object('id', p_id, 'rows_affected', rows_affected)
    );
END;
$$ LANGUAGE plpgsql;

-- Función para activar un usuario
CREATE OR REPLACE FUNCTION fn_activar_usuario(p_id INTEGER)
RETURNS JSON AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    -- Activar el usuario
    UPDATE usuarios 
    SET activo = TRUE 
    WHERE id = p_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Verificar si se activó correctamente
    IF rows_affected = 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró el usuario con el ID especificado',
            'data', NULL
        );
    END IF;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Usuario activado exitosamente',
        'data', json_build_object('id', p_id, 'rows_affected', rows_affected)
    );
END;
$$ LANGUAGE plpgsql;

-- Función para cambiar el rol de un usuario
CREATE OR REPLACE FUNCTION fn_cambiar_rol_usuario(
    p_id INTEGER,
    p_nuevo_rol d_rol_usuario
) RETURNS JSON AS $$
DECLARE
    rows_affected INTEGER;
BEGIN
    -- Cambiar el rol del usuario
    UPDATE usuarios 
    SET rol = p_nuevo_rol
    WHERE id = p_id;
    
    GET DIAGNOSTICS rows_affected = ROW_COUNT;
    
    -- Verificar si se cambió correctamente
    IF rows_affected = 0 THEN
        RETURN json_build_object(
            'success', false,
            'message', 'No se encontró el usuario con el ID especificado',
            'data', NULL
        );
    END IF;
    
    -- Retornar éxito
    RETURN json_build_object(
        'success', true,
        'message', 'Rol de usuario cambiado exitosamente',
        'data', json_build_object('id', p_id, 'nuevo_rol', p_nuevo_rol)
    );
END;
$$ LANGUAGE plpgsql;

-- Función para obtener un usuario por ID
CREATE OR REPLACE FUNCTION fn_obtener_usuario_por_id(p_id INTEGER)
RETURNS TABLE(
    id INTEGER,
    username VARCHAR(50),
    nombre_completo VARCHAR(200),
    email VARCHAR(100),
    rol d_rol_usuario,
    activo BOOLEAN,
    fecha_registro TIMESTAMP,
    ultimo_acceso TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        u.id,
        u.username,
        u.nombre_completo,
        u.email,
        u.rol,
        u.activo,
        u.fecha_registro,
        u.ultimo_acceso
    FROM usuarios u
    WHERE u.id = p_id;
    
    -- Actualizar el último acceso
    UPDATE usuarios 
    SET ultimo_acceso = CURRENT_TIMESTAMP 
    WHERE id = p_id;
END;
$$ LANGUAGE plpgsql;

-- Función para obtener un usuario por username
CREATE OR REPLACE FUNCTION fn_obtener_usuario_por_username(p_username VARCHAR(50))
RETURNS TABLE(
    id INTEGER,
    username VARCHAR(50),
    password_hash TEXT,
    nombre_completo VARCHAR(200),
    email VARCHAR(100),
    rol d_rol_usuario,
    activo BOOLEAN,
    fecha_registro TIMESTAMP,
    ultimo_acceso TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        u.id,
        u.username,
        u.password_hash,
        u.nombre_completo,
        u.email,
        u.rol,
        u.activo,
        u.fecha_registro,
        u.ultimo_acceso
    FROM usuarios u
    WHERE u.username = p_username;
END;
$$ LANGUAGE plpgsql;

-- Función para buscar usuarios con filtros
CREATE OR REPLACE FUNCTION fn_buscar_usuarios(
    p_username VARCHAR(50) DEFAULT NULL,
    p_nombre_completo VARCHAR(200) DEFAULT NULL,
    p_rol d_rol_usuario DEFAULT NULL,
    p_activo BOOLEAN DEFAULT NULL
) RETURNS TABLE(
    id INTEGER,
    username VARCHAR(50),
    nombre_completo VARCHAR(200),
    email VARCHAR(100),
    rol d_rol_usuario,
    activo BOOLEAN,
    fecha_registro TIMESTAMP,
    ultimo_acceso TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        u.id,
        u.username,
        u.nombre_completo,
        u.email,
        u.rol,
        u.activo,
        u.fecha_registro,
        u.ultimo_acceso
    FROM usuarios u
    WHERE 
        (p_username IS NULL OR u.username ILIKE '%' || p_username || '%')
        AND (p_nombre_completo IS NULL OR u.nombre_completo ILIKE '%' || p_nombre_completo || '%')
        AND (p_rol IS NULL OR u.rol = p_rol)
        AND (p_activo IS NULL OR u.activo = p_activo)
    ORDER BY u.nombre_completo;
END;
$$ LANGUAGE plpgsql;

-- Función para listar todos los usuarios
CREATE OR REPLACE FUNCTION fn_listar_usuarios()
RETURNS TABLE(
    id INTEGER,
    username VARCHAR(50),
    nombre_completo VARCHAR(200),
    email VARCHAR(100),
    rol d_rol_usuario,
    activo BOOLEAN,
    fecha_registro TIMESTAMP,
    ultimo_acceso TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY 
    SELECT 
        u.id,
        u.username,
        u.nombre_completo,
        u.email,
        u.rol,
        u.activo,
        u.fecha_registro,
        u.ultimo_acceso
    FROM usuarios u
    ORDER BY u.nombre_completo;
END;
$$ LANGUAGE plpgsql;
