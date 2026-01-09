# Archivo: model/estudiante_model.py - VERSIÓN OPTIMIZADA Y REORGANIZADA
from config.database import Database
from typing import List, Dict, Optional, Any, Tuple
from datetime import date
import logging
import json

logger = logging.getLogger(__name__)


class EstudianteModel:
    """Modelo optimizado para manejar operaciones CRUD de estudiantes"""
    
    # ===== CONSTANTES Y CONFIGURACIÓN =====
    
    # Columnas básicas de la tabla estudiantes
    COLUMNAS_BASICAS = [
        'id', 'ci_numero', 'ci_expedicion', 'nombres', 'apellido_paterno', 
        'apellido_materno', 'fecha_nacimiento', 'telefono', 'email', 
        'direccion', 'profesion', 'universidad', 'fotografia_url', 
        'activo', 'fecha_registro'
    ]
    
    # Columnas para búsqueda avanzada con detalles
    COLUMNAS_CON_DETALLES = COLUMNAS_BASICAS + [
        'total_programas', 'programas_activos', 'total_pagado', 'total_deuda'
    ]
    
    # ===== MÉTODOS CRUD BÁSICOS =====
    
    @staticmethod
    def crear_estudiante(datos: Dict[str, Any]) -> Dict[str, Any]:
        """Crear un nuevo estudiante usando la función almacenada"""
        try:
            logger.info("=" * 50)
            logger.info("DEBUG - Modelo: Iniciando creación de estudiante CON FUNCIÓN ALMACENADA")
            logger.info(f"DEBUG - Modelo: Datos recibidos: {datos}")

            # Preparar parámetros para la función almacenada
            # NOTA: La función espera 13 parámetros exactamente en este orden:
            # 1. p_ci_numero, 2. p_ci_expedicion, 3. p_nombres, 4. p_apellido_paterno
            # 5. p_apellido_materno, 6. p_fecha_nacimiento, 7. p_telefono
            # 8. p_email, 9. p_direccion, 10. p_profesion, 11. p_universidad
            # 12. p_fotografia_url, 13. p_activo

            params = [
                datos.get('ci_numero'),
                datos.get('ci_expedicion'),
                datos.get('nombres'),
                datos.get('apellido_paterno'),
                datos.get('apellido_materno'),
                datos.get('fecha_nacimiento'),
                datos.get('telefono'),
                datos.get('email'),
                datos.get('direccion'),
                datos.get('profesion'),
                datos.get('universidad'),
                datos.get('fotografia_url'),
                datos.get('activo', True)
            ]

            logger.info(f"DEBUG - Modelo: Parámetros originales: {params}")

            # CONVERTIR datetime.date a string ISO para PostgreSQL
            for i, param in enumerate(params):
                if isinstance(param, date):
                    params[i] = param.isoformat()
                    logger.info(f"DEBUG - Convertido fecha en posición {i}: {param} -> {params[i]}")

            logger.info(f"DEBUG - Modelo: Parámetros después de conversión: {params}")

            # Usar la función almacenada - IMPORTANTE: 13 parámetros
            query = """
                SELECT * FROM public.fn_insertar_estudiante(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """

            logger.info(f"DEBUG - Modelo: Query función almacenada: {query}")
            logger.info(f"DEBUG - Modelo: Número de parámetros: {len(params)}")

            # Asegurar que tenemos exactamente 13 parámetros
            if len(params) != 13:  # Porque incluimos activo que ya está
                logger.error(f"❌ Número incorrecto de parámetros: {len(params)}, se esperaban 13")
                # Ajustar si es necesario
                if len(params) > 13:
                    params = params[:13]
                elif len(params) < 13:
                    # Rellenar con None los faltantes
                    params.extend([None] * (13 - len(params)))

            result = Database.execute_query(query, tuple(params[:13]), fetch_one=True, commit=True)

            logger.info(f"DEBUG - Modelo: Resultado función (crudo): {result}")
            logger.info(f"DEBUG - Modelo: Tipo resultado: {type(result)}")

            if result:
                # La función retorna una tupla con 3 elementos
                nuevo_id = result[0]
                mensaje = result[1]
                exito = result[2]

                logger.info(f"DEBUG - Modelo: Parseado -> id: {nuevo_id}, mensaje: {mensaje}, exito: {exito}")

                # En PostgreSQL, BOOLEAN se representa como 't'/'f' o True/False
                if exito in [True, 't', 'true', 'TRUE', 1, '1']:
                    logger.info(f"✅ Estudiante creado exitosamente - ID: {nuevo_id}")
                    return {
                        'exito': True,
                        'mensaje': mensaje,
                        'nuevo_id': nuevo_id
                    }
                else:
                    logger.error(f"❌ Función almacenada falló: {mensaje}")
                    return {
                        'exito': False,
                        'mensaje': mensaje
                    }
            else:
                logger.error("❌ No se pudo crear el estudiante (resultado None)")
                return {
                    'exito': False,
                    'mensaje': 'La función almacenada no retornó resultados'
                }

        except Exception as e:
            logger.error(f"❌ Error creando estudiante: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'exito': False,
                'mensaje': f'Error al crear estudiante: {str(e)}'
            }
    
    @staticmethod
    def actualizar_estudiante(estudiante_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar un estudiante existente usando UPDATE dinámico
        
        Args:
            estudiante_id: ID del estudiante a actualizar
            data: Diccionario con los campos a actualizar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            logger.info(f"DEBUG - Actualizando estudiante ID {estudiante_id} con datos: {data}")
            
            # Convertir datetime.date a string ISO
            datos_para_sql = data.copy()
            for key, value in datos_para_sql.items():
                if isinstance(value, date):
                    datos_para_sql[key] = value.isoformat()
                    logger.info(f"DEBUG - Convertido fecha {key}: {value} -> {datos_para_sql[key]}")
            
            # Construir UPDATE dinámico basado en los campos proporcionados
            campos_actualizar = []
            params = []
            
            # Mapeo de campos de data a columnas de la tabla
            mapeo_campos = {
                'ci_numero': 'ci_numero',
                'ci_expedicion': 'ci_expedicion',
                'nombres': 'nombres',
                'apellido_paterno': 'apellido_paterno',
                'apellido_materno': 'apellido_materno',
                'fecha_nacimiento': 'fecha_nacimiento',
                'telefono': 'telefono',
                'email': 'email',
                'direccion': 'direccion',
                'profesion': 'profesion',
                'universidad': 'universidad',
                'fotografia_url': 'fotografia_url',
                'activo': 'activo'
            }
            
            # Agregar solo los campos que están presentes en data
            for campo_data, campo_db in mapeo_campos.items():
                if campo_data in data and data[campo_data] is not None:
                    campos_actualizar.append(f"{campo_db} = %s")
                    params.append(data[campo_data])
            
            # Si no hay campos para actualizar
            if not campos_actualizar:
                return {
                    'filas_afectadas': 0,
                    'mensaje': 'No se proporcionaron datos para actualizar',
                    'exito': False
                }
            
            # Agregar ID al final de los parámetros
            params.append(estudiante_id)
            
            # Construir query final
            query = f"""
            UPDATE public.estudiantes 
            SET {', '.join(campos_actualizar)}, fecha_registro = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            logger.info(f"Actualizando estudiante ID: {estudiante_id}")
            
            # Ejecutar UPDATE
            filas_afectadas = Database.execute_query(query, tuple(params), fetch_one=True, commit=True)
            
            if filas_afectadas and filas_afectadas > 0:
                logger.info(f"✅ Estudiante actualizado - Filas afectadas: {filas_afectadas}")
                return {
                    'filas_afectadas': filas_afectadas,
                    'mensaje': 'Estudiante actualizado exitosamente',
                    'exito': True
                }
            
            return {
                'filas_afectadas': 0,
                'mensaje': 'No se encontró el estudiante o no hubo cambios',
                'exito': False
            }
            
        except Exception as e:
            logger.error(f"❌ Error actualizando estudiante: {e}")
            return {
                'filas_afectadas': 0,
                'mensaje': f'Error al actualizar estudiante: {str(e)}',
                'exito': False
            }
    
    @staticmethod
    def obtener_estudiante_por_id(estudiante_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener un estudiante por ID
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Dict con datos del estudiante o None si no existe
        """
        try:
            query = """
            SELECT * FROM public.estudiantes 
            WHERE id = %s
            """
            
            result = Database.execute_query(query, (estudiante_id,), fetch_one=True)
            
            if result:
                estudiante = dict(zip(EstudianteModel.COLUMNAS_BASICAS, result))
                logger.debug(f"Estudiante encontrado: ID {estudiante_id}")
                return estudiante
            
            logger.warning(f"Estudiante no encontrado: ID {estudiante_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo estudiante por ID: {e}")
            return None
    
    @staticmethod
    def buscar_estudiante_id(estudiante_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener estudiante por ID con información detallada
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Dict con datos detallados del estudiante
        """
        try:
            # Usar función almacenada para obtener detalles financieros
            query = "SELECT * FROM fn_buscar_estudiante_id(%s)"
            params = (estudiante_id,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result:
                estudiante = dict(zip(EstudianteModel.COLUMNAS_CON_DETALLES, result))
                logger.debug(f"Estudiante con detalles encontrado: ID {estudiante_id}")
                return estudiante
            
            return None
            
        except Exception as e:
            logger.error(f"Error buscando estudiante con detalles: {e}")
            return None
    
    # ===== MÉTODOS DE BÚSQUEDA =====
    
    @staticmethod
    def buscar_estudiantes(
        ci_numero: Optional[str] = None,
        ci_expedicion: Optional[str] = None,
        nombre: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Buscar estudiantes usando filtros opcionales
        
        Args:
            ci_numero: Número de CI (búsqueda parcial)
            ci_expedicion: Expedición del CI
            nombre: Nombre o apellidos (búsqueda parcial)
            limit: Límite de resultados
            offset: Desplazamiento
            
        Returns:
            Lista de estudiantes encontrados
        """
        try:
            # Usar función almacenada para búsqueda
            query = "SELECT * FROM fn_buscar_estudiantes(%s, %s, %s, %s, %s)"
            params = (ci_numero, ci_expedicion, nombre, limit, offset)
            
            results = Database.execute_query(query, params)
            
            if results:
                estudiantes = [dict(zip(EstudianteModel.COLUMNAS_BASICAS, row)) for row in results]
                logger.debug(f"Búsqueda encontrada: {len(estudiantes)} estudiantes")
                return estudiantes
            
            return []
            
        except Exception as e:
            logger.error(f"Error buscando estudiantes: {e}")
            return []
    
    @staticmethod
    def buscar_estudiantes_completo(
        ci_numero: Optional[str] = None,
        ci_expedicion: Optional[str] = None,
        nombres: Optional[str] = None,
        apellido_paterno: Optional[str] = None,
        apellido_materno: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda avanzada de estudiantes para la interfaz de usuario
        
        Args:
            ci_numero: Número de CI (puede contener '-')
            ci_expedicion: Expedición del CI
            nombres: Nombres (búsqueda parcial)
            apellido_paterno: Apellido paterno (búsqueda parcial)
            apellido_materno: Apellido materno (búsqueda parcial)
            
        Returns:
            Lista de estudiantes encontrados
        """
        try:
            query = """
            SELECT id, ci_numero, ci_expedicion, nombres, apellido_paterno, 
                   apellido_materno, fecha_nacimiento, telefono, email, 
                   direccion, profesion, universidad, fotografia_url, 
                   activo, fecha_registro
            FROM public.estudiantes 
            WHERE 1=1
            """
            
            params = []
            
            # Manejo especial para CI con formato "numero-expedicion"
            if ci_numero:
                if '-' in ci_numero:
                    partes = ci_numero.split('-', 1)
                    query += " AND ci_numero ILIKE %s"
                    params.append(f"%{partes[0]}%")
                    
                    if len(partes) > 1 and partes[1]:
                        query += " AND ci_expedicion ILIKE %s"
                        params.append(f"%{partes[1]}%")
                else:
                    query += " AND ci_numero ILIKE %s"
                    params.append(f"%{ci_numero}%")
            
            if ci_expedicion and ci_expedicion != "Todos":
                query += " AND ci_expedicion = %s"
                params.append(ci_expedicion)
            
            if nombres:
                query += " AND nombres ILIKE %s"
                params.append(f"%{nombres}%")
            
            if apellido_paterno:
                query += " AND apellido_paterno ILIKE %s"
                params.append(f"%{apellido_paterno}%")
            
            if apellido_materno:
                query += " AND apellido_materno ILIKE %s"
                params.append(f"%{apellido_materno}%")
            
            # Ordenar y paginar
            query += " ORDER BY apellido_paterno, apellido_materno, nombres"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            results = Database.execute_query(query, tuple(params))
            
            if results:
                estudiantes = [dict(zip(EstudianteModel.COLUMNAS_BASICAS, row)) for row in results]
                logger.debug(f"Búsqueda completa: {len(estudiantes)} estudiantes")
                return estudiantes
            
            return []
            
        except Exception as e:
            logger.error(f"Error en búsqueda completa de estudiantes: {e}")
            return []
    
    # ===== MÉTODOS DE CONSULTA Y CONTEO =====
    
    @staticmethod
    def contar_estudiantes() -> int:
        """Contar total de estudiantes."""
        try:
            query = "SELECT COUNT(*) FROM estudiantes"
            result = Database.execute_query(query, fetch_one=True)
            return result[0] if result else 0
        except Exception as e:
            logger.error(f"Error contando estudiantes: {e}")
            return 0
    
    @staticmethod
    def obtener_todos_estudiantes(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtener todos los estudiantes (sin filtros)
        
        Args:
            limit: Límite de resultados
            offset: Desplazamiento
            
        Returns:
            Lista de todos los estudiantes
        """
        try:
            return EstudianteModel.buscar_estudiantes(
                ci_numero=None,
                ci_expedicion=None,
                nombre=None,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Error obteniendo todos los estudiantes: {e}")
            return []
    
    # En model/estudiante_model.py
    @staticmethod
    def obtener_total_estudiantes(filtros: Optional[Dict[str, Any]] = None) -> int:
        """Obtener el total de estudiantes que coinciden con los filtros"""
        try:
            ci_numero = None
            ci_expedicion = None
            nombre = None
            
            if filtros:
                ci_numero = filtros.get('ci_numero')
                ci_expedicion = filtros.get('ci_expedicion')
                nombre = filtros.get('nombre')
            
            # Construir query para contar
            query = "SELECT COUNT(*) FROM fn_buscar_estudiantes(%s, %s, %s, NULL, NULL)"
            params = (ci_numero, ci_expedicion, nombre)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result and result[0]:
                return result[0]
            
            return 0
            
        except Exception as e:
            logger.error(f"Error obteniendo total de estudiantes: {e}")
            return 0
    
    @staticmethod
    def obtener_estudiantes_activos(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtener solo estudiantes activos
        
        Args:
            limit: Límite de resultados
            offset: Desplazamiento
            
        Returns:
            Lista de estudiantes activos
        """
        try:
            query = """
            SELECT * FROM public.estudiantes 
            WHERE activo = TRUE
            ORDER BY apellido_paterno, apellido_materno, nombres
            LIMIT %s OFFSET %s
            """
            
            results = Database.execute_query(query, (limit, offset))
            
            if results:
                return [dict(zip(EstudianteModel.COLUMNAS_BASICAS, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo estudiantes activos: {e}")
            return []
    
    # ===== MÉTODOS DE ESTADO =====
    
    @staticmethod
    def eliminar_estudiante(estudiante_id: int) -> Dict[str, Any]:
        """
        Eliminar (desactivar) un estudiante
        
        Args:
            estudiante_id: ID del estudiante a desactivar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Usar función almacenada para eliminar/desactivar
            query = "SELECT * FROM fn_eliminar_estudiante(%s)"
            params = (estudiante_id,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result:
                filas_afectadas, mensaje, exito = result
                logger.info(f"Estudiante eliminado/desactivado: ID {estudiante_id}")
                return {
                    'filas_afectadas': filas_afectadas,
                    'mensaje': mensaje,
                    'exito': exito
                }
            
            return {
                'filas_afectadas': 0,
                'mensaje': 'Estudiante no encontrado',
                'exito': False
            }
            
        except Exception as e:
            logger.error(f"Error eliminando estudiante: {e}")
            return {
                'filas_afectadas': 0,
                'mensaje': f'Error al eliminar estudiante: {str(e)}',
                'exito': False
            }
    
    @staticmethod
    def activar_estudiante(estudiante_id: int) -> Dict[str, Any]:
        """
        Activar un estudiante previamente desactivado
        
        Args:
            estudiante_id: ID del estudiante a activar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Usar función almacenada para activar
            query = "SELECT * FROM fn_activar_estudiante(%s)"
            params = (estudiante_id,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result:
                filas_afectadas, mensaje, exito = result
                logger.info(f"Estudiante activado: ID {estudiante_id}")
                return {
                    'filas_afectadas': filas_afectadas,
                    'mensaje': mensaje,
                    'exito': exito
                }
            
            return {
                'filas_afectadas': 0,
                'mensaje': 'Estudiante no encontrado',
                'exito': False
            }
            
        except Exception as e:
            logger.error(f"Error activando estudiante: {e}")
            return {
                'filas_afectadas': 0,
                'mensaje': f'Error al activar estudiante: {str(e)}',
                'exito': False
            }
    
    # ===== MÉTODOS DE VALIDACIÓN =====
    
    @staticmethod
    def verificar_ci_existente(ci_numero: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verificar si un número de CI ya existe
        
        Args:
            ci_numero: Número de CI a verificar
            excluir_id: ID a excluir de la verificación (para actualizaciones)
            
        Returns:
            True si el CI ya existe, False en caso contrario
        """
        try:
            # Usar función almacenada para verificar CI
            if excluir_id:
                query = "SELECT fn_verificar_ci_existente(%s, %s)"
                params = (ci_numero, excluir_id)
            else:
                query = "SELECT fn_verificar_ci_existente(%s)"
                params = (ci_numero,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            return result[0] if result else False
            
        except Exception as e:
            logger.error(f"Error verificando CI: {e}")
            return False
    
    @staticmethod
    def verificar_email_existente(email: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verificar si un email ya existe
        
        Args:
            email: Email a verificar
            excluir_id: ID a excluir de la verificación
            
        Returns:
            True si el email ya existe, False en caso contrario
        """
        try:
            if excluir_id:
                query = """
                SELECT EXISTS(
                    SELECT 1 FROM public.estudiantes 
                    WHERE email = %s AND id != %s
                )
                """
                params = (email, excluir_id)
            else:
                query = "SELECT EXISTS(SELECT 1 FROM public.estudiantes WHERE email = %s)"
                params = (email,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            return result[0] if result else False
            
        except Exception as e:
            logger.error(f"Error verificando email: {e}")
            return False
    
    @staticmethod
    def validar_datos_estudiante(data: Dict[str, Any], excluir_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Validar datos del estudiante antes de insertar o actualizar
        
        Args:
            data: Datos del estudiante a validar
            excluir_id: ID a excluir de las validaciones
            
        Returns:
            Dict con resultados de validación
        """
        errores = []
        
        # Validar CI
        ci_numero = data.get('ci_numero')
        if not ci_numero:
            errores.append('El número de CI es obligatorio')
        elif EstudianteModel.verificar_ci_existente(ci_numero, excluir_id):
            errores.append('El número de CI ya está registrado')
        
        # Validar email si se proporciona
        email = data.get('email')
        if email and EstudianteModel.verificar_email_existente(email, excluir_id):
            errores.append('El email ya está registrado')
        
        # Validar nombres y apellidos
        if not data.get('nombres'):
            errores.append('Los nombres son obligatorios')
        if not data.get('apellido_paterno'):
            errores.append('El apellido paterno es obligatorio')
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'mensaje': 'Datos válidos' if len(errores) == 0 else '; '.join(errores)
        }
    
    # ===== MÉTODOS DE ESTADÍSTICAS =====
    
    @staticmethod
    def obtener_estadisticas() -> Dict[str, Any]:
        """
        Obtener estadísticas generales de estudiantes
        
        Returns:
            Dict con estadísticas de estudiantes
        """
        try:
            # Usar función almacenada para estadísticas
            query = "SELECT * FROM fn_estadisticas_estudiantes()"
            result = Database.execute_query(query, fetch_one=True)
            
            if result:
                column_names = [
                    'total_estudiantes', 'activos', 'inactivos',
                    'promedio_edad', 'con_email', 'con_telefono'
                ]
                return dict(zip(column_names, result))
            
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    # ===== MÉTODOS DE RELACIONES Y FINANZAS =====
    
    @staticmethod
    def obtener_programas_estudiante(estudiante_id: int) -> List[Dict[str, Any]]:
        """
        Obtener todos los programas académicos de un estudiante
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Lista de programas del estudiante
        """
        try:
            # Usar función almacenada para obtener programas
            query = "SELECT * FROM fn_obtener_programas_estudiante(%s)"
            params = (estudiante_id,)
            
            results = Database.execute_query(query, params)
            
            if results:
                column_names = [
                    'programa_id', 'programa_codigo', 'programa_nombre', 'estado_programa',
                    'estado_inscripcion', 'fecha_inscripcion', 'fecha_inicio', 'fecha_fin',
                    'duracion_meses', 'horas_totales', 'costo_total', 'costo_pagado',
                    'saldo_pendiente', 'porcentaje_pagado', 'docente_coordinador',
                    'promocion_descuento', 'cupos_inscritos', 'cupos_maximos'
                ]
                return [dict(zip(column_names, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo programas del estudiante: {e}")
            return []
    
    @staticmethod
    def obtener_pagos_estudiante_programa(
        estudiante_id: int, 
        programa_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener el detalle de pagos por programa de un estudiante
        
        Args:
            estudiante_id: ID del estudiante
            programa_id: ID del programa (opcional)
            
        Returns:
            Lista de pagos del estudiante
        """
        try:
            if programa_id:
                query = "SELECT * FROM fn_obtener_pagos_estudiante_programa(%s, %s)"
                params = (estudiante_id, programa_id)
            else:
                query = "SELECT * FROM fn_obtener_pagos_estudiante_programa(%s, NULL)"
                params = (estudiante_id,)
            
            results = Database.execute_query(query, params)
            
            if results:
                column_names = [
                    'transaccion_id', 'numero_transaccion', 'fecha_pago', 'forma_pago',
                    'monto_total', 'descuento_total', 'monto_final', 'estado_transaccion',
                    'numero_comprobante', 'observaciones', 'detalles', 'programa_nombre',
                    'programa_codigo', 'usuario_registro'
                ]
                return [dict(zip(column_names, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo pagos del estudiante: {e}")
            return []
    
    @staticmethod
    def obtener_resumen_financiero_estudiante(estudiante_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener resumen financiero del estudiante
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Dict con resumen financiero
        """
        try:
            query = "SELECT * FROM fn_resumen_financiero_estudiante(%s)"
            params = (estudiante_id,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result:
                column_names = [
                    'total_programas', 'total_inscrito', 'total_pagado', 'total_deuda',
                    'promedio_pagado', 'transacciones_totales', 'ultimo_pago',
                    'proximo_vencimiento', 'estado_financiero'
                ]
                return dict(zip(column_names, result))
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen financiero: {e}")
            return None
    
    @staticmethod
    def obtener_cronograma_pagos_estudiante(estudiante_id: int) -> List[Dict[str, Any]]:
        """
        Obtener cronograma de pagos sugerido
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Lista con cronograma de pagos
        """
        try:
            query = "SELECT * FROM fn_cronograma_pagos_estudiante(%s)"
            params = (estudiante_id,)
            
            results = Database.execute_query(query, params)
            
            if results:
                column_names = [
                    'programa_id', 'programa_nombre', 'mes_pago', 'concepto',
                    'monto_sugerido', 'fecha_sugerida', 'estado'
                ]
                return [dict(zip(column_names, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo cronograma de pagos: {e}")
            return []
    
    @staticmethod
    def estudiante_programas_resumen(estudiante_id: int) -> List[Dict[str, Any]]:
        """
        Obtener vista resumida por programa
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Lista con resumen de programas
        """
        try:
            query = "SELECT * FROM fn_estudiante_programas_resumen(%s)"
            params = (estudiante_id,)
            
            results = Database.execute_query(query, params)
            
            if results:
                column_names = [
                    'estudiante_id', 'estudiante_nombre', 'programa_id', 'programa_codigo',
                    'programa_nombre', 'programa_estado', 'fecha_inscripcion',
                    'inscripcion_estado', 'costo_total', 'total_pagado', 'saldo_pendiente',
                    'porcentaje_pagado', 'transacciones_count', 'ultima_transaccion_date',
                    'ultima_transaccion_amount', 'facturas_count', 'facturas_total'
                ]
                return [dict(zip(column_names, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo resumen de programas: {e}")
            return []
    
    @staticmethod
    def estudiante_transacciones_detalle(estudiante_id: int) -> List[Dict[str, Any]]:
        """
        Obtener transacciones detalladas por estudiante
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Lista con transacciones detalladas
        """
        try:
            query = "SELECT * FROM fn_estudiante_transacciones_detalle(%s)"
            params = (estudiante_id,)
            
            results = Database.execute_query(query, params)
            
            if results:
                column_names = [
                    'row_number', 'estudiante_id', 'estudiante_nombre', 'programa_id',
                    'programa_nombre', 'transaccion_id', 'numero_transaccion', 'fecha_pago',
                    'forma_pago', 'monto_total', 'descuento_total', 'monto_final',
                    'transaccion_estado', 'numero_comprobante', 'conceptos', 'factura_numero',
                    'usuario_registro', 'observaciones'
                ]
                return [dict(zip(column_names, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo transacciones detalladas: {e}")
            return []
    
    @staticmethod
    def inscripcion_completa(estudiante_data: Dict[str, Any], programa_id: int) -> Dict[str, Any]:
        """
        Realizar inscripción completa de estudiante a programa
        
        Args:
            estudiante_data: Datos del estudiante
            programa_id: ID del programa
            
        Returns:
            Dict con resultado de la inscripción
        """
        try:
            # Convertir el diccionario a JSONB
            estudiante_json = json.dumps(estudiante_data)
            
            query = "SELECT * FROM fn_inscripcion_completa(%s::jsonb, %s)"
            params = (estudiante_json, programa_id)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result:
                column_names = [
                    'estudiante_id', 'programa_id', 'inscripcion_exito',
                    'mensaje_estudiante', 'mensaje_inscripcion', 'cupos_disponibles',
                    'costo_total', 'detalles_pago'
                ]
                resultado = dict(zip(column_names, result))
                
                # Convertir detalles_pago de string a dict si es necesario
                if isinstance(resultado.get('detalles_pago'), str):
                    try:
                        resultado['detalles_pago'] = json.loads(resultado['detalles_pago'])
                    except:
                        pass
                
                return resultado
            
            return {
                'estudiante_id': None,
                'programa_id': programa_id,
                'inscripcion_exito': False,
                'mensaje_estudiante': 'Error en la inscripción',
                'mensaje_inscripcion': 'Error desconocido',
                'cupos_disponibles': 0,
                'costo_total': 0,
                'detalles_pago': {}
            }
            
        except Exception as e:
            logger.error(f"Error realizando inscripción completa: {e}")
            return {
                'estudiante_id': None,
                'programa_id': programa_id,
                'inscripcion_exito': False,
                'mensaje_estudiante': f'Error: {str(e)}',
                'mensaje_inscripcion': 'Error en el proceso',
                'cupos_disponibles': 0,
                'costo_total': 0,
                'detalles_pago': {}
            }
    
    # ===== MÉTODOS DE UTILIDAD =====
    
    @staticmethod
    def formatear_nombre_estudiante(estudiante: Dict[str, Any]) -> str:
        """
        Formatear nombre completo del estudiante para mostrar
        
        Args:
            estudiante: Dict con datos del estudiante
            
        Returns:
            String con nombre formateado
        """
        nombres = estudiante.get('nombres', '')
        apellido_paterno = estudiante.get('apellido_paterno', '')
        apellido_materno = estudiante.get('apellido_materno', '')
        
        return f"{nombres} {apellido_paterno} {apellido_materno}".strip()
    
    @staticmethod
    def formatear_ci_completo(estudiante: Dict[str, Any]) -> str:
        """
        Formatear CI completo del estudiante para mostrar
        
        Args:
            estudiante: Dict con datos del estudiante
            
        Returns:
            String con CI formateado
        """
        ci_numero = estudiante.get('ci_numero', '')
        ci_expedicion = estudiante.get('ci_expedicion', '')
        
        if ci_numero and ci_expedicion:
            return f"{ci_numero}-{ci_expedicion}"
        return ci_numero or ''
    
    @staticmethod
    def obtener_estudiante_como_json(estudiante_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener estudiante como JSON para uso en formularios
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Dict con datos del estudiante o None
        """
        estudiante = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
        
        if estudiante:
            return {
                'id': estudiante['id'],
                'ci_numero': estudiante['ci_numero'],
                'ci_expedicion': estudiante['ci_expedicion'],
                'nombres': estudiante['nombres'],
                'apellido_paterno': estudiante['apellido_paterno'],
                'apellido_materno': estudiante['apellido_materno'],
                'fecha_nacimiento': estudiante['fecha_nacimiento'],
                'telefono': estudiante['telefono'],
                'email': estudiante['email'],
                'direccion': estudiante['direccion'],
                'profesion': estudiante['profesion'],
                'universidad': estudiante['universidad'],
                'fotografia_url': estudiante['fotografia_url'],
                'activo': estudiante['activo'],
                'fecha_registro': estudiante['fecha_registro']
            }
        
        return None
    
    # ===== MÉTODOS COMPATIBILIDAD CON INTERFAZ EXISTENTE =====
    
    @staticmethod
    def buscar_por_filtros(filtros: Dict[str, Any], limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Método de compatibilidad para búsqueda con filtros"""
        return EstudianteModel.buscar_estudiantes(
            ci_numero=filtros.get('ci_numero'),
            ci_expedicion=filtros.get('ci_expedicion'),
            nombre=filtros.get('nombre'),
            limit=limit,
            offset=offset
        )
    
    @staticmethod
    def contar_por_filtros(filtros: Dict[str, Any]) -> int:
        """Método de compatibilidad para contar con filtros"""
        
        ci_numero=filtros.get('ci_numero'),
        ci_expedicion=filtros.get('ci_expedicion'),
        nombre=filtros.get('nombre')
        
        try:
            # Usar función almacenada para contar
            query = "SELECT fn_contar_estudiantes(%s, %s, %s)"
            params = (ci_numero, ci_expedicion, nombre)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error contando estudiantes: {e}")
            return 0
    
    @staticmethod
    def obtener_por_id(id: int) -> Optional[Dict[str, Any]]:
        """Método de compatibilidad para obtener por ID"""
        return EstudianteModel.obtener_estudiante_por_id(id)
    
    @staticmethod
    def crear(data: Dict[str, Any]) -> Dict[str, Any]:
        """Método de compatibilidad para crear"""
        return EstudianteModel.crear_estudiante(data)
    
    @staticmethod
    def actualizar(id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Método de compatibilidad para actualizar"""
        return EstudianteModel.actualizar_estudiante(id, data)
    
    @staticmethod
    def eliminar(id: int) -> Dict[str, Any]:
        """Método de compatibilidad para eliminar"""
        return EstudianteModel.eliminar_estudiante(id)
    
    @staticmethod
    def obtener_todos() -> List[Dict[str, Any]]:
        """Método de compatibilidad para obtener todos"""
        return EstudianteModel.obtener_todos_estudiantes()
    
    @staticmethod
    def obtener_activos() -> List[Dict[str, Any]]:
        """Método de compatibilidad para obtener activos"""
        return EstudianteModel.obtener_estudiantes_activos()