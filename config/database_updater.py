# utils/database_updater.py
import logging
from config.database import Database
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

class DatabaseUpdater:
    """Gestor de actualizaciones de base de datos"""
    
    @staticmethod
    def verificar_estructura_programa() -> Dict[str, Any]: # <-- LInea: 12
        """
        Verificar si la tabla programas tiene los campos de promoción
        
        Returns:
            Dict con resultados de verificación
        """
        try:
            connection = Database.get_connection()
            if not connection:
                logger.error("❌ No se pudo obtener conexión para verificar estructura")
                return {'existe_promocion': False, 'error': True}
            
            cursor = connection.cursor()
            
            # Verificar si existen los campos de promoción
            campos_verificar = [
                'promocion_descuento',
                'promocion_descripcion', 
                'promocion_valido_hasta'
            ]
            
            resultados = {}
            
            for campo in campos_verificar:
                query = """
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'programas' 
                        AND column_name = %s
                        AND table_schema = 'public'
                    )
                """
                cursor.execute(query, (campo,))
                row = cursor.fetchone()
                resultado = row[0] if row else False
                resultados[campo] = resultado
            
            cursor.close()
            Database.return_connection(connection)
            
            # Determinar si existe al menos un campo de promoción
            existe_promocion = any(resultados.values())
            
            logger.info(f"✅ Verificación completada. Campos de promoción encontrados: {resultados}")
            logger.info(f"   ¿Requiere actualización?: {'SI' if existe_promocion else 'NO'}")
            
            return {
                'existe_promocion': existe_promocion,
                'campos_detallados': resultados, # <-- Línea: 61
                'error': False
            }
            
        except Exception as e:
            logger.error(f"❌ Error verificando estructura: {e}")
            return {'existe_promocion': False, 'error': True}
    
    @staticmethod
    def ejecutar_actualizacion() -> bool:
        """
        Ejecutar script SQL de actualización
        
        Returns:
            True si la actualización fue exitosa
        """
        connection = Database.get_connection()
        cursor = connection.cursor() if connection else None
        try:
            if not connection:
                logger.error("❌ No se pudo obtener conexión para actualización")
                return False
            
            cursor = connection.cursor()
            
            # Script SQL de actualización (versión completa)
            sql_script = """
            -- ==================== 1. ELIMINAR CAMPOS DE PROMOCIÓN ====================
            ALTER TABLE programas DROP COLUMN IF EXISTS promocion_descuento;
            ALTER TABLE programas DROP COLUMN IF EXISTS promocion_descripcion;
            ALTER TABLE programas DROP COLUMN IF EXISTS promocion_valido_hasta;
            
            -- ==================== 2. ACTUALIZAR FUNCIONES ====================
            -- Función fn_insertar_programa (simplificada - versión completa en archivo separado)
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
                -- Código de la función (simplificado para ejemplo)
                -- Validación básica
                IF fn_verificar_codigo_programa_existente(p_codigo) THEN
                    v_mensaje := 'El código de programa ya está registrado';
                    RETURN QUERY SELECT NULL, v_mensaje, FALSE;
                    RETURN;
                END IF;
                
                -- Insertar sin campos de promoción
                INSERT INTO programas (
                    codigo, nombre, descripcion, duracion_meses, horas_totales,
                    costo_total, costo_matricula, costo_inscripcion, costo_mensualidad,
                    numero_cuotas, cupos_maximos, cupos_inscritos, estado,
                    fecha_inicio, fecha_fin, docente_coordinador_id
                ) VALUES (
                    p_codigo, p_nombre, p_descripcion, p_duracion_meses, p_horas_totales,
                    p_costo_total, p_costo_matricula, p_costo_inscripcion, p_costo_mensualidad,
                    p_numero_cuotas, p_cupos_maximos, p_cupos_inscritos, p_estado,
                    p_fecha_inicio, p_fecha_fin, p_docente_coordinador_id
                ) RETURNING id INTO v_nuevo_id;
                
                v_mensaje := 'Programa creado exitosamente';
                v_exito := TRUE;
                
                RETURN QUERY SELECT v_nuevo_id, v_mensaje, v_exito;
                
            EXCEPTION
                WHEN OTHERS THEN
                    v_mensaje := 'Error al crear programa: ' || SQLERRM;
                    v_exito := FALSE;
                    RETURN QUERY SELECT NULL, v_mensaje, v_exito;
            END;
            $$;
            
            -- ==================== 3. VERIFICACIÓN FINAL ====================
            DO $$
            BEGIN
                RAISE NOTICE '✅ Actualización completada exitosamente';
            END $$;
            """
            
            # Ejecutar script completo
            cursor.execute(sql_script)
            connection.commit()
            
            cursor.close()
            Database.return_connection(connection)
            
            logger.info("✅ Script de actualización ejecutado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando actualización: {e}")
            if connection:
                connection.rollback()
                cursor.close() if cursor else None
                Database.return_connection(connection)
            return False
    
    @staticmethod
    def ejecutar_script_externo(ruta_script: str) -> bool:
        """
        Ejecutar script SQL desde archivo externo
        
        Args:
            ruta_script: Ruta al archivo SQL
            
        Returns:
            True si la ejecución fue exitosa
        """
        connection = Database.get_connection()
        cursor = connection.cursor() if connection else None
        try:
            with open(ruta_script, 'r', encoding='utf-8') as file:
                sql_content = file.read()
            
            if not connection:
                logger.error(f"❌ No se pudo obtener conexión para ejecutar script: {ruta_script}")
                return False
            
            cursor = connection.cursor()
            cursor.execute(sql_content)
            connection.commit()
            
            cursor.close()
            Database.return_connection(connection)
            
            logger.info(f"✅ Script externo ejecutado: {ruta_script}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando script externo {ruta_script}: {e}")
            if connection:
                connection.rollback()
                cursor.close() if cursor else None
                Database.return_connection(connection)
            return False