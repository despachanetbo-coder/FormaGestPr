-- Archivo: config/funciones.sql

-- DROP FUNCTION public.fn_activar_docente(int4);

CREATE OR REPLACE FUNCTION public.fn_activar_docente(p_id integer)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_activar_estudiante(int4);

CREATE OR REPLACE FUNCTION public.fn_activar_estudiante(p_id integer)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_activar_programa(int4);

CREATE OR REPLACE FUNCTION public.fn_activar_programa(p_id integer)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_activar_usuario(int4);

CREATE OR REPLACE FUNCTION public.fn_activar_usuario(p_id integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_actualizar_configuracion(varchar, text, text, varchar, varchar, bool);

CREATE OR REPLACE FUNCTION public.fn_actualizar_configuracion(p_clave character varying, p_valor text, p_descripcion text DEFAULT NULL::text, p_tipo character varying DEFAULT NULL::character varying, p_categoria character varying DEFAULT NULL::character varying, p_editable boolean DEFAULT NULL::boolean)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_actualizar_docente(int4, varchar, d_expedicion_ci, varchar, varchar, varchar, date, d_grado_academico, varchar, varchar, varchar, varchar, text, numeric, bool);

CREATE OR REPLACE FUNCTION public.fn_actualizar_docente(p_id integer, p_ci_numero character varying, p_ci_expedicion d_expedicion_ci, p_nombres character varying, p_apellido_paterno character varying, p_apellido_materno character varying, p_fecha_nacimiento date DEFAULT NULL::date, p_grado_academico d_grado_academico DEFAULT NULL::text, p_titulo_profesional character varying DEFAULT NULL::character varying, p_especialidad character varying DEFAULT NULL::character varying, p_telefono character varying DEFAULT NULL::character varying, p_email character varying DEFAULT NULL::character varying, p_curriculum_url text DEFAULT NULL::text, p_honorario_hora numeric DEFAULT NULL::numeric, p_activo boolean DEFAULT NULL::boolean)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_actualizar_estudiante(int4, varchar, d_expedicion_ci, varchar, varchar, varchar, date, varchar, varchar, text, varchar, varchar, text, bool);

CREATE OR REPLACE FUNCTION public.fn_actualizar_estudiante(p_id integer, p_ci_numero character varying, p_ci_expedicion d_expedicion_ci, p_nombres character varying, p_apellido_paterno character varying, p_apellido_materno character varying, p_fecha_nacimiento date DEFAULT NULL::date, p_telefono character varying DEFAULT NULL::character varying, p_email character varying DEFAULT NULL::character varying, p_direccion text DEFAULT NULL::text, p_profesion character varying DEFAULT NULL::character varying, p_universidad character varying DEFAULT NULL::character varying, p_fotografia_url text DEFAULT NULL::text, p_activo boolean DEFAULT NULL::boolean)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_actualizar_monto_transaccion();

CREATE OR REPLACE FUNCTION public.fn_actualizar_monto_transaccion()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_actualizar_programa(int4, varchar, varchar, int4, int4, numeric, numeric, text, numeric, numeric, int4, int4, int4, d_estado_programa, date, date, int4, numeric, text, date);

CREATE OR REPLACE FUNCTION public.fn_actualizar_programa(p_id integer, p_codigo character varying, p_nombre character varying, p_duracion_meses integer, p_horas_totales integer, p_costo_total numeric, p_costo_mensualidad numeric, p_descripcion text DEFAULT NULL::text, p_costo_matricula numeric DEFAULT NULL::numeric, p_costo_inscripcion numeric DEFAULT NULL::numeric, p_numero_cuotas integer DEFAULT NULL::integer, p_cupos_maximos integer DEFAULT NULL::integer, p_cupos_inscritos integer DEFAULT NULL::integer, p_estado d_estado_programa DEFAULT NULL::text, p_fecha_inicio date DEFAULT NULL::date, p_fecha_fin date DEFAULT NULL::date, p_docente_coordinador_id integer DEFAULT NULL::integer, p_promocion_descuento numeric DEFAULT NULL::numeric, p_promocion_descripcion text DEFAULT NULL::text, p_promocion_valido_hasta date DEFAULT NULL::date)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_actualizar_timestamp();

CREATE OR REPLACE FUNCTION public.fn_actualizar_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$
;

-- DROP FUNCTION public.fn_actualizar_usuario(int4, varchar, text, varchar, varchar, d_rol_usuario, bool);

CREATE OR REPLACE FUNCTION public.fn_actualizar_usuario(p_id integer, p_username character varying DEFAULT NULL::character varying, p_password_hash text DEFAULT NULL::text, p_nombre_completo character varying DEFAULT NULL::character varying, p_email character varying DEFAULT NULL::character varying, p_rol d_rol_usuario DEFAULT NULL::text, p_activo boolean DEFAULT NULL::boolean)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_buscar_configuraciones(varchar, varchar, varchar, bool);

CREATE OR REPLACE FUNCTION public.fn_buscar_configuraciones(p_clave character varying DEFAULT NULL::character varying, p_categoria character varying DEFAULT NULL::character varying, p_tipo character varying DEFAULT NULL::character varying, p_editable boolean DEFAULT NULL::boolean)
 RETURNS TABLE(id integer, clave character varying, valor text, descripcion text, tipo character varying, categoria character varying, editable boolean, created_at timestamp without time zone, updated_at timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_buscar_docentes(varchar, varchar, varchar, varchar, bool, int4, int4);

CREATE OR REPLACE FUNCTION public.fn_buscar_docentes(p_ci_numero character varying DEFAULT NULL::character varying, p_ci_expedicion character varying DEFAULT NULL::character varying, p_nombre character varying DEFAULT NULL::character varying, p_grado_academico character varying DEFAULT NULL::character varying, p_activo boolean DEFAULT NULL::boolean, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0)
 RETURNS TABLE(id integer, ci_numero character varying, ci_expedicion d_expedicion_ci, nombres character varying, apellido_paterno character varying, apellido_materno character varying, fecha_nacimiento date, grado_academico d_grado_academico, titulo_profesional character varying, especialidad character varying, telefono character varying, email character varying, curriculum_url text, honorario_hora numeric, activo boolean, fecha_registro timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_buscar_estudiante_id(int4);

CREATE OR REPLACE FUNCTION public.fn_buscar_estudiante_id(p_id integer)
 RETURNS TABLE(id integer, ci_numero character varying, ci_expedicion d_expedicion_ci, nombres character varying, apellido_paterno character varying, apellido_materno character varying, fecha_nacimiento date, telefono character varying, email character varying, direccion text, profesion character varying, universidad character varying, fotografia_url text, activo boolean, fecha_registro timestamp without time zone, total_programas integer, programas_activos integer, total_pagado numeric, total_deuda numeric)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_buscar_estudiantes(varchar, varchar, varchar, int4, int4);

CREATE OR REPLACE FUNCTION public.fn_buscar_estudiantes(p_ci_numero character varying DEFAULT NULL::character varying, p_ci_expedicion character varying DEFAULT NULL::character varying, p_nombre character varying DEFAULT NULL::character varying, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0)
 RETURNS TABLE(id integer, ci_numero character varying, ci_expedicion d_expedicion_ci, nombres character varying, apellido_paterno character varying, apellido_materno character varying, fecha_nacimiento date, telefono character varying, email character varying, direccion text, profesion character varying, universidad character varying, fotografia_url text, activo boolean, fecha_registro timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_buscar_informacion_completa_estudiante(int4);

CREATE OR REPLACE FUNCTION public.fn_buscar_informacion_completa_estudiante(p_estudiante_id integer)
 RETURNS TABLE(estudiante_id integer, ci_numero character varying, ci_expedicion d_expedicion_ci, nombres_completos character varying, apellidos_completos character varying, fecha_nacimiento date, telefono character varying, email character varying, direccion text, profesion character varying, universidad character varying, fotografia_url text, estudiante_activo boolean, fecha_registro_estudiante timestamp without time zone, programa_id integer, programa_codigo character varying, programa_nombre character varying, programa_descripcion text, programa_duracion_meses integer, programa_horas_totales integer, programa_costo_total numeric, programa_costo_matricula numeric, programa_costo_inscripcion numeric, programa_costo_mensualidad numeric, programa_numero_cuotas integer, programa_estado d_estado_programa, programa_fecha_inicio date, programa_fecha_fin date, programa_cupos_inscritos integer, programa_cupos_maximos integer, programa_promocion_descuento numeric, inscripcion_id integer, inscripcion_estado d_estado_academico, fecha_inscripcion date, inscripcion_descuento_aplicado numeric, inscripcion_observaciones text, transaccion_id integer, numero_transaccion character varying, transaccion_fecha_pago date, transaccion_fecha_registro timestamp without time zone, transaccion_monto_total numeric, transaccion_descuento_total numeric, transaccion_monto_final numeric, transaccion_forma_pago d_forma_pago, transaccion_estado d_estado_transaccion, transaccion_numero_comprobante character varying, transaccion_banco_origen character varying, transaccion_cuenta_origen character varying, transaccion_observaciones text, detalle_transaccion_id integer, concepto_pago_codigo character varying, concepto_pago_nombre character varying, detalle_descripcion character varying, detalle_cantidad integer, detalle_precio_unitario numeric, detalle_subtotal numeric, factura_id integer, numero_factura character varying, factura_nit_ci character varying, factura_razon_social character varying, factura_fecha_emision date, factura_subtotal numeric, factura_iva numeric, factura_it numeric, factura_total numeric, factura_estado character varying, usuario_registro_id integer, usuario_registro_nombre character varying, usuario_registro_rol d_rol_usuario, docente_coordinador_id integer, docente_coordinador_nombre character varying, docente_grado_academico d_grado_academico, movimiento_caja_id integer, movimiento_caja_fecha date, movimiento_caja_tipo d_tipo_movimiento, movimiento_caja_descripcion character varying, total_pagado_programa numeric, saldo_pendiente_programa numeric, porcentaje_pagado_programa numeric, cuotas_pagadas integer, cuotas_pendientes integer)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_buscar_programas(varchar, varchar, d_estado_programa, int4, date, date, int4, int4);

CREATE OR REPLACE FUNCTION public.fn_buscar_programas(p_codigo character varying DEFAULT NULL::character varying, p_nombre character varying DEFAULT NULL::character varying, p_estado d_estado_programa DEFAULT NULL::text, p_docente_coordinador_id integer DEFAULT NULL::integer, p_fecha_inicio_desde date DEFAULT NULL::date, p_fecha_inicio_hasta date DEFAULT NULL::date, p_limit integer DEFAULT 20, p_offset integer DEFAULT 0)
 RETURNS TABLE(id integer, codigo character varying, nombre character varying, descripcion text, duracion_meses integer, horas_totales integer, costo_total numeric, costo_matricula numeric, costo_inscripcion numeric, costo_mensualidad numeric, numero_cuotas integer, cupos_maximos integer, cupos_inscritos integer, estado d_estado_programa, fecha_inicio date, fecha_fin date, docente_coordinador_id integer, promocion_descuento numeric, promocion_descripcion text, promocion_valido_hasta date, created_at timestamp without time zone, updated_at timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_buscar_usuarios(varchar, varchar, d_rol_usuario, bool);

CREATE OR REPLACE FUNCTION public.fn_buscar_usuarios(p_username character varying DEFAULT NULL::character varying, p_nombre_completo character varying DEFAULT NULL::character varying, p_rol d_rol_usuario DEFAULT NULL::text, p_activo boolean DEFAULT NULL::boolean)
 RETURNS TABLE(id integer, username character varying, nombre_completo character varying, email character varying, rol d_rol_usuario, activo boolean, fecha_registro timestamp without time zone, ultimo_acceso timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_cambiar_rol_usuario(int4, d_rol_usuario);

CREATE OR REPLACE FUNCTION public.fn_cambiar_rol_usuario(p_id integer, p_nuevo_rol d_rol_usuario)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_contar_docentes(varchar, varchar, varchar, varchar, bool);

CREATE OR REPLACE FUNCTION public.fn_contar_docentes(p_ci_numero character varying DEFAULT NULL::character varying, p_ci_expedicion character varying DEFAULT NULL::character varying, p_nombre character varying DEFAULT NULL::character varying, p_grado_academico character varying DEFAULT NULL::character varying, p_activo boolean DEFAULT NULL::boolean)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_contar_estudiantes(varchar, varchar, varchar);

CREATE OR REPLACE FUNCTION public.fn_contar_estudiantes(p_ci_numero character varying DEFAULT NULL::character varying, p_ci_expedicion character varying DEFAULT NULL::character varying, p_nombre character varying DEFAULT NULL::character varying)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_contar_programas(varchar, varchar, d_estado_programa, int4, date, date);

CREATE OR REPLACE FUNCTION public.fn_contar_programas(p_codigo character varying DEFAULT NULL::character varying, p_nombre character varying DEFAULT NULL::character varying, p_estado d_estado_programa DEFAULT NULL::text, p_docente_coordinador_id integer DEFAULT NULL::integer, p_fecha_inicio_desde date DEFAULT NULL::date, p_fecha_inicio_hasta date DEFAULT NULL::date)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_cronograma_pagos_estudiante(int4);

CREATE OR REPLACE FUNCTION public.fn_cronograma_pagos_estudiante(p_estudiante_id integer)
 RETURNS TABLE(programa_id integer, programa_nombre character varying, mes_pago integer, concepto character varying, monto_sugerido numeric, fecha_sugerida date, estado character varying)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_editar_empresa(int4, varchar, varchar, varchar, varchar, varchar, text);

CREATE OR REPLACE FUNCTION public.fn_editar_empresa(p_id integer, p_nombre character varying, p_nit character varying, p_direccion character varying, p_telefono character varying, p_email character varying, p_logo_url text)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_eliminar_configuracion(varchar);

CREATE OR REPLACE FUNCTION public.fn_eliminar_configuracion(p_clave character varying)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_eliminar_docente(int4);

CREATE OR REPLACE FUNCTION public.fn_eliminar_docente(p_id integer)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_eliminar_estudiante(int4);

CREATE OR REPLACE FUNCTION public.fn_eliminar_estudiante(p_id integer)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_eliminar_programa(int4);

CREATE OR REPLACE FUNCTION public.fn_eliminar_programa(p_id integer)
 RETURNS TABLE(filas_afectadas integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_eliminar_usuario(int4);

CREATE OR REPLACE FUNCTION public.fn_eliminar_usuario(p_id integer)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_estadisticas_docentes();

CREATE OR REPLACE FUNCTION public.fn_estadisticas_docentes()
 RETURNS TABLE(total_docentes integer, activos integer, inactivos integer, promedio_honorario numeric, con_email integer, con_telefono integer, con_curriculum integer)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_estadisticas_estudiantes();

CREATE OR REPLACE FUNCTION public.fn_estadisticas_estudiantes()
 RETURNS TABLE(total_estudiantes integer, activos integer, inactivos integer, promedio_edad numeric, con_email integer, con_telefono integer)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_estadisticas_programas();

CREATE OR REPLACE FUNCTION public.fn_estadisticas_programas()
 RETURNS TABLE(total_programas integer, planificados integer, en_curso integer, finalizados integer, cancelados integer, promedio_duracion numeric, promedio_costo numeric, promedio_cupos_inscritos numeric, total_cupos_disponibles bigint)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_generar_numero_transaccion();

CREATE OR REPLACE FUNCTION public.fn_generar_numero_transaccion()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_inscribir_estudiante_programa(int4, int4);

CREATE OR REPLACE FUNCTION public.fn_inscribir_estudiante_programa(p_programa_id integer, p_estudiante_id integer)
 RETURNS TABLE(exito boolean, mensaje character varying, cupos_disponibles integer)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_inscripcion_completa(jsonb, int4);

CREATE OR REPLACE FUNCTION public.fn_inscripcion_completa(p_estudiante_data jsonb, p_programa_id integer)
 RETURNS TABLE(estudiante_id integer, programa_id integer, inscripcion_exito boolean, mensaje_estudiante character varying, mensaje_inscripcion character varying, cupos_disponibles integer, costo_total numeric, detalles_pago jsonb)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_insertar_configuracion(varchar, text, text, varchar, varchar, bool);

CREATE OR REPLACE FUNCTION public.fn_insertar_configuracion(p_clave character varying, p_valor text, p_descripcion text DEFAULT NULL::text, p_tipo character varying DEFAULT 'TEXTO'::character varying, p_categoria character varying DEFAULT 'GENERAL'::character varying, p_editable boolean DEFAULT true)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_insertar_docente(varchar, d_expedicion_ci, varchar, varchar, varchar, date, d_grado_academico, varchar, varchar, varchar, varchar, text, numeric, bool);

CREATE OR REPLACE FUNCTION public.fn_insertar_docente(p_ci_numero character varying, p_ci_expedicion d_expedicion_ci, p_nombres character varying, p_apellido_paterno character varying, p_apellido_materno character varying, p_fecha_nacimiento date DEFAULT NULL::date, p_grado_academico d_grado_academico DEFAULT NULL::text, p_titulo_profesional character varying DEFAULT NULL::character varying, p_especialidad character varying DEFAULT NULL::character varying, p_telefono character varying DEFAULT NULL::character varying, p_email character varying DEFAULT NULL::character varying, p_curriculum_url text DEFAULT NULL::text, p_honorario_hora numeric DEFAULT 0, p_activo boolean DEFAULT true)
 RETURNS TABLE(nuevo_id integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_insertar_empresa(varchar, varchar, varchar, varchar, varchar, text);

CREATE OR REPLACE FUNCTION public.fn_insertar_empresa(p_nombre character varying, p_nit character varying, p_direccion character varying, p_telefono character varying, p_email character varying, p_logo_url text)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_insertar_estudiante(varchar, d_expedicion_ci, varchar, varchar, varchar, date, varchar, varchar, text, varchar, varchar, text, bool);

CREATE OR REPLACE FUNCTION public.fn_insertar_estudiante(p_ci_numero character varying, p_ci_expedicion d_expedicion_ci, p_nombres character varying, p_apellido_paterno character varying, p_apellido_materno character varying, p_fecha_nacimiento date DEFAULT NULL::date, p_telefono character varying DEFAULT NULL::character varying, p_email character varying DEFAULT NULL::character varying, p_direccion text DEFAULT NULL::text, p_profesion character varying DEFAULT NULL::character varying, p_universidad character varying DEFAULT NULL::character varying, p_fotografia_url text DEFAULT NULL::text, p_activo boolean DEFAULT true)
 RETURNS TABLE(nuevo_id integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_insertar_programa(varchar, varchar, int4, int4, numeric, numeric, text, numeric, numeric, int4, int4, int4, d_estado_programa, date, date, int4, numeric, text, date);

CREATE OR REPLACE FUNCTION public.fn_insertar_programa(p_codigo character varying, p_nombre character varying, p_duracion_meses integer, p_horas_totales integer, p_costo_total numeric, p_costo_mensualidad numeric, p_descripcion text DEFAULT NULL::text, p_costo_matricula numeric DEFAULT 0, p_costo_inscripcion numeric DEFAULT 0, p_numero_cuotas integer DEFAULT 1, p_cupos_maximos integer DEFAULT NULL::integer, p_cupos_inscritos integer DEFAULT 0, p_estado d_estado_programa DEFAULT 'PLANIFICADO'::text, p_fecha_inicio date DEFAULT NULL::date, p_fecha_fin date DEFAULT NULL::date, p_docente_coordinador_id integer DEFAULT NULL::integer, p_promocion_descuento numeric DEFAULT 0, p_promocion_descripcion text DEFAULT NULL::text, p_promocion_valido_hasta date DEFAULT NULL::date)
 RETURNS TABLE(nuevo_id integer, mensaje character varying, exito boolean)
 LANGUAGE plpgsql
AS $function$
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
    
    -- Validar descuento de promoción
    IF p_promocion_descuento < 0 OR p_promocion_descuento > 100 THEN
        v_mensaje := 'El descuento de promoción debe estar entre 0 y 100';
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
    
    -- Insertar programa
    INSERT INTO programas (
        codigo, nombre, descripcion, duracion_meses, horas_totales,
        costo_total, costo_matricula, costo_inscripcion, costo_mensualidad,
        numero_cuotas, cupos_maximos, cupos_inscritos, estado,
        fecha_inicio, fecha_fin, docente_coordinador_id,
        promocion_descuento, promocion_descripcion, promocion_valido_hasta
    ) VALUES (
        p_codigo, p_nombre, p_descripcion, p_duracion_meses, p_horas_totales,
        p_costo_total, p_costo_matricula, p_costo_inscripcion, p_costo_mensualidad,
        p_numero_cuotas, p_cupos_maximos, p_cupos_inscritos, p_estado,
        p_fecha_inicio, v_fecha_fin_calculada, p_docente_coordinador_id,
        p_promocion_descuento, p_promocion_descripcion, p_promocion_valido_hasta
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
$function$
;

-- DROP FUNCTION public.fn_insertar_usuario(varchar, text, varchar, varchar, d_rol_usuario, bool);

CREATE OR REPLACE FUNCTION public.fn_insertar_usuario(p_username character varying, p_password_hash text, p_nombre_completo character varying, p_email character varying, p_rol d_rol_usuario DEFAULT 'CAJERO'::text, p_activo boolean DEFAULT true)
 RETURNS json
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_listar_configuraciones();

CREATE OR REPLACE FUNCTION public.fn_listar_configuraciones()
 RETURNS TABLE(id integer, clave character varying, valor text, descripcion text, tipo character varying, categoria character varying, editable boolean, created_at timestamp without time zone, updated_at timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_listar_usuarios();

CREATE OR REPLACE FUNCTION public.fn_listar_usuarios()
 RETURNS TABLE(id integer, username character varying, nombre_completo character varying, email character varying, rol d_rol_usuario, activo boolean, fecha_registro timestamp without time zone, ultimo_acceso timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_configuracion(varchar);

CREATE OR REPLACE FUNCTION public.fn_obtener_configuracion(p_clave character varying)
 RETURNS TABLE(id integer, clave character varying, valor text, descripcion text, tipo character varying, categoria character varying, editable boolean, created_at timestamp without time zone, updated_at timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_docente_por_id(int4);

CREATE OR REPLACE FUNCTION public.fn_obtener_docente_por_id(p_id integer)
 RETURNS TABLE(id integer, ci_numero character varying, ci_expedicion d_expedicion_ci, nombres character varying, apellido_paterno character varying, apellido_materno character varying, fecha_nacimiento date, grado_academico d_grado_academico, titulo_profesional character varying, especialidad character varying, telefono character varying, email character varying, curriculum_url text, honorario_hora numeric, activo boolean, fecha_registro timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_estudiante_por_id(int4);

CREATE OR REPLACE FUNCTION public.fn_obtener_estudiante_por_id(p_id integer)
 RETURNS TABLE(id integer, ci_numero character varying, ci_expedicion d_expedicion_ci, nombres character varying, apellido_paterno character varying, apellido_materno character varying, fecha_nacimiento date, telefono character varying, email character varying, direccion text, profesion character varying, universidad character varying, fotografia_url text, activo boolean, fecha_registro timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_pagos_estudiante_programa(int4, int4);

CREATE OR REPLACE FUNCTION public.fn_obtener_pagos_estudiante_programa(p_estudiante_id integer, p_programa_id integer DEFAULT NULL::integer)
 RETURNS TABLE(transaccion_id integer, numero_transaccion character varying, fecha_pago date, forma_pago d_forma_pago, monto_total numeric, descuento_total numeric, monto_final numeric, estado_transaccion d_estado_transaccion, numero_comprobante character varying, observaciones text, detalles text, programa_nombre character varying, programa_codigo character varying, usuario_registro character varying)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_programa_por_id(int4);

CREATE OR REPLACE FUNCTION public.fn_obtener_programa_por_id(p_id integer)
 RETURNS TABLE(id integer, codigo character varying, nombre character varying, descripcion text, duracion_meses integer, horas_totales integer, costo_total numeric, costo_matricula numeric, costo_inscripcion numeric, costo_mensualidad numeric, numero_cuotas integer, cupos_maximos integer, cupos_inscritos integer, estado d_estado_programa, fecha_inicio date, fecha_fin date, docente_coordinador_id integer, promocion_descuento numeric, promocion_descripcion text, promocion_valido_hasta date, created_at timestamp without time zone, updated_at timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_programas_estudiante(int4);

CREATE OR REPLACE FUNCTION public.fn_obtener_programas_estudiante(p_estudiante_id integer)
 RETURNS TABLE(programa_id integer, programa_codigo character varying, programa_nombre character varying, estado_programa d_estado_programa, estado_inscripcion d_estado_academico, fecha_inscripcion date, fecha_inicio date, fecha_fin date, duracion_meses integer, horas_totales integer, costo_total numeric, costo_pagado numeric, saldo_pendiente numeric, porcentaje_pagado numeric, docente_coordinador character varying, promocion_descuento numeric, cupos_inscritos integer, cupos_maximos integer)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_usuario_por_id(int4);

CREATE OR REPLACE FUNCTION public.fn_obtener_usuario_por_id(p_id integer)
 RETURNS TABLE(id integer, username character varying, nombre_completo character varying, email character varying, rol d_rol_usuario, activo boolean, fecha_registro timestamp without time zone, ultimo_acceso timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_obtener_usuario_por_username(varchar);

CREATE OR REPLACE FUNCTION public.fn_obtener_usuario_por_username(p_username character varying)
 RETURNS TABLE(id integer, username character varying, password_hash text, nombre_completo character varying, email character varying, rol d_rol_usuario, activo boolean, fecha_registro timestamp without time zone, ultimo_acceso timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_registrar_movimiento_caja();

CREATE OR REPLACE FUNCTION public.fn_registrar_movimiento_caja()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_resumen_financiero_estudiante(int4);

CREATE OR REPLACE FUNCTION public.fn_resumen_financiero_estudiante(p_estudiante_id integer)
 RETURNS TABLE(total_programas integer, total_inscrito numeric, total_pagado numeric, total_deuda numeric, promedio_pagado numeric, transacciones_totales integer, ultimo_pago date, proximo_vencimiento date, estado_financiero character varying)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_saldo_pendiente_estudiante(int4);

CREATE OR REPLACE FUNCTION public.fn_saldo_pendiente_estudiante(p_estudiante_id integer)
 RETURNS TABLE(programa_id integer, programa_nombre character varying, total_debe numeric, total_pagado numeric, saldo_pendiente numeric)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_ver_empresa();

CREATE OR REPLACE FUNCTION public.fn_ver_empresa()
 RETURNS TABLE(id integer, nombre character varying, nit character varying, direccion character varying, telefono character varying, email character varying, logo_url text, created_at timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_verificar_ci_docente_existente(varchar, int4);

CREATE OR REPLACE FUNCTION public.fn_verificar_ci_docente_existente(p_ci_numero character varying, p_excluir_id integer DEFAULT NULL::integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_verificar_ci_existente(varchar, int4);

CREATE OR REPLACE FUNCTION public.fn_verificar_ci_existente(p_ci_numero character varying, p_excluir_id integer DEFAULT NULL::integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP FUNCTION public.fn_verificar_codigo_programa_existente(varchar, int4);

CREATE OR REPLACE FUNCTION public.fn_verificar_codigo_programa_existente(p_codigo character varying, p_excluir_id integer DEFAULT NULL::integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
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
$function$
;

-- DROP PROCEDURE public.sp_activar_estudiante(in int4, out int4, out varchar, out bool);

CREATE OR REPLACE PROCEDURE public.sp_activar_estudiante(IN p_id integer, OUT p_filas_afectadas integer, OUT p_mensaje character varying, OUT p_exito boolean)
 LANGUAGE plpgsql
AS $procedure$
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
$procedure$
;

-- DROP PROCEDURE public.sp_actualizar_estudiante(out int4, out varchar, out bool, in int4, in varchar, in d_expedicion_ci, in varchar, in varchar, in varchar, in date, in varchar, in varchar, in text, in varchar, in varchar, in text, in bool);

CREATE OR REPLACE PROCEDURE public.sp_actualizar_estudiante(OUT p_filas_afectadas integer, OUT p_mensaje character varying, OUT p_exito boolean, IN p_id integer, IN p_ci_numero character varying, IN p_ci_expedicion d_expedicion_ci, IN p_nombres character varying, IN p_apellido_paterno character varying, IN p_apellido_materno character varying, IN p_fecha_nacimiento date DEFAULT NULL::date, IN p_telefono character varying DEFAULT NULL::character varying, IN p_email character varying DEFAULT NULL::character varying, IN p_direccion text DEFAULT NULL::text, IN p_profesion character varying DEFAULT NULL::character varying, IN p_universidad character varying DEFAULT NULL::character varying, IN p_fotografia_url text DEFAULT NULL::text, IN p_activo boolean DEFAULT NULL::boolean)
 LANGUAGE plpgsql
AS $procedure$
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
$procedure$
;

-- DROP PROCEDURE public.sp_eliminar_estudiante(in int4, out int4, out varchar, out bool);

CREATE OR REPLACE PROCEDURE public.sp_eliminar_estudiante(IN p_id integer, OUT p_filas_afectadas integer, OUT p_mensaje character varying, OUT p_exito boolean)
 LANGUAGE plpgsql
AS $procedure$
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
$procedure$
;

-- DROP PROCEDURE public.sp_registrar_transaccion_completa(int4, int4, date, d_forma_pago, int4, jsonb, numeric, varchar, varchar, varchar, text);

CREATE OR REPLACE PROCEDURE public.sp_registrar_transaccion_completa(IN p_estudiante_id integer, IN p_programa_id integer, IN p_fecha_pago date, IN p_forma_pago d_forma_pago, IN p_registrado_por integer, IN p_detalles jsonb, IN p_descuento_total numeric DEFAULT 0, IN p_numero_comprobante character varying DEFAULT NULL::character varying, IN p_banco_origen character varying DEFAULT NULL::character varying, IN p_cuenta_origen character varying DEFAULT NULL::character varying, IN p_observaciones text DEFAULT NULL::text)
 LANGUAGE plpgsql
AS $procedure$
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
$procedure$
;