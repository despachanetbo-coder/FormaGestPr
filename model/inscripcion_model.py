# Archivo: model/inscripcion_model.py
"""
Modelo para gestionar inscripciones de estudiantes a programas académicos
Siguiendo el patrón establecido en usuarios_model.py
"""
import logging
import json
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import date, datetime
from config.database import Database

logger = logging.getLogger(__name__)

class InscripcionModel:
    """Modelo para la tabla inscripciones y procesos relacionados"""
    
    @staticmethod
    def verificar_disponibilidad_programa(programa_id: int) -> Dict[str, Any]:
        """
        Verifica disponibilidad de cupos en un programa
        
        Args:
            programa_id: ID del programa
            
        Returns:
            Dict con información de disponibilidad
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('fn_verificar_disponibilidad_programa', (programa_id,))
            result = cursor.fetchone()
            
            if result:
                disponibilidad = {
                    'disponible': result[0],
                    'cupos_disponibles': result[1],
                    'estado_programa': result[2],
                    'mensaje': result[3]
                }
                
                return {
                    'success': True,
                    'data': disponibilidad
                }
            else:
                return {
                    'success': False,
                    'message': 'No se pudo verificar disponibilidad'
                }
                
        except Exception as e:
            logger.error(f"Error al verificar disponibilidad: {e}")
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def crear_inscripcion(
        estudiante_id: int,
        programa_id: int,
        valor_final: float,
        observaciones: Optional[str] = None,
        fecha_inscripcion: Union[str, datetime, date, None] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva inscripción con el valor final especificado

        Args:
            estudiante_id: ID del estudiante
            programa_id: ID del programa
            valor_final: Valor final acordado para la inscripción
            observaciones: Observaciones adicionales (debe incluir justificación si hay descuento)
            fecha_inscripcion: Fecha de inscripción (si no se proporciona, usa CURRENT_DATE)

        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")

            cursor = connection.cursor()

            # Manejar la fecha de inscripción
            fecha_str = None
            if fecha_inscripcion:
                if isinstance(fecha_inscripcion, str):
                    fecha_str = fecha_inscripcion
                    if '/' in fecha_str:
                        try:
                            fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
                            fecha_str = fecha_dt.strftime('%Y-%m-%d')
                        except ValueError:
                            pass
                elif isinstance(fecha_inscripcion, (datetime, date)):
                    fecha_str = fecha_inscripcion.strftime('%Y-%m-%d')

            # Llamar a la función con valor_final
            cursor.execute(
                "SELECT fn_crear_inscripcion(%s, %s, %s, %s, %s)",
                (estudiante_id, programa_id, valor_final, observaciones, fecha_str)
            )
            if not cursor:
                raise Exception("No se pudo crear la inscripción")
            
            result = cursor.fetchone()[0] # type: ignore

            connection.commit()

            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}

        except Exception as e:
            logger.error(f"Error al crear inscripción: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if connection:
                connection.rollback()
            return {
                'success': False,
                'message': f'Error al crear inscripción: {str(e)}'
            }
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def crear_inscripcion_retroactiva(
        estudiante_id: int,
        programa_id: int,
        fecha_inscripcion: date,
        valor_final: float,  # Cambiado
        observaciones: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea una inscripción con fecha retroactiva
        
        Args:
            estudiante_id: ID del estudiante
            programa_id: ID del programa
            fecha_inscripcion: Fecha retroactiva de inscripción
            valor_final: Valor final acordado para la inscripción
            observaciones: Observaciones adicionales (debe incluir justificación si hay descuento)
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('sp_crear_inscripcion_retroactiva', (
                estudiante_id,
                programa_id,
                fecha_inscripcion.isoformat(),
                valor_final,  # Cambiado
                observaciones
            ))
            if cursor.rowcount == 0:
                raise Exception("No se pudo crear la inscripción retroactiva")
            result = cursor.fetchone()[0] # type: ignore
            
            connection.commit()
            
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al crear inscripción retroactiva: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def registrar_pago_inscripcion(
        inscripcion_id: int,
        forma_pago: str,
        monto_pagado: float,
        fecha_pago: Optional[date] = None,
        numero_comprobante: Optional[str] = None,
        banco_origen: Optional[str] = None,
        cuenta_origen: Optional[str] = None,
        observaciones: Optional[str] = None,
        registrado_por: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Registra pago de una inscripción
        
        Args:
            inscripcion_id: ID de la inscripción
            forma_pago: Forma de pago
            monto_pagado: Monto pagado
            fecha_pago: Fecha del pago
            numero_comprobante: Número de comprobante
            banco_origen: Banco de origen (transferencias)
            cuenta_origen: Cuenta de origen
            observaciones: Observaciones
            registrado_por: ID del usuario que registra
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            # Convertir fecha a string si se proporciona
            fecha_str = fecha_pago.isoformat() if fecha_pago else None
            
            cursor.callproc('sp_registrar_pago_inscripcion', (
                inscripcion_id,
                forma_pago,
                monto_pagado,
                fecha_str,
                numero_comprobante,
                banco_origen,
                cuenta_origen,
                observaciones,
                registrado_por
            ))
            if not cursor.rowcount:
                raise Exception("No se pudo registrar el pago de inscripción")
            
            result = cursor.fetchone()[0] # type: ignore
            
            connection.commit()
            
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al registrar pago de inscripción: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def registrar_pago_completo(
        inscripcion_id: int,
        forma_pago: str,
        monto_pagado: float,
        fecha_pago: Optional[date] = None,
        numero_comprobante: Optional[str] = None,
        banco_origen: Optional[str] = None,
        cuenta_origen: Optional[str] = None,
        observaciones: Optional[str] = None,
        registrado_por: Optional[int] = None,
        documentos: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Registra pago completo con documentos adjuntos
        
        Args:
            inscripcion_id: ID de la inscripción
            forma_pago: Forma de pago
            monto_pagado: Monto pagado
            fecha_pago: Fecha del pago
            numero_comprobante: Número de comprobante
            banco_origen: Banco de origen
            cuenta_origen: Cuenta de origen
            observaciones: Observaciones
            registrado_por: ID del usuario que registra
            documentos: Lista de documentos a adjuntar
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            # Convertir fecha a string si se proporciona
            fecha_str = fecha_pago.isoformat() if fecha_pago else None
            
            # Convertir documentos a JSON string
            documentos_json = json.dumps(documentos) if documentos else None
            
            cursor.callproc('sp_registrar_pago_completo', (
                inscripcion_id,
                forma_pago,
                monto_pagado,
                fecha_str,
                numero_comprobante,
                banco_origen,
                cuenta_origen,
                observaciones,
                registrado_por,
                documentos_json
            ))
            if not cursor.rowcount:
                raise Exception("No se pudo registrar el pago completo")
            
            result = cursor.fetchone()[0] # type: ignore
            
            connection.commit()
            
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al registrar pago completo: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def registrar_documento_respaldo(
        transaccion_id: int,
        tipo_documento: str,
        nombre_original: str,
        nombre_archivo: str,
        extension: str,
        ruta_archivo: str,
        tamano_bytes: Optional[int] = None,
        observaciones: Optional[str] = None,
        subido_por: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Registra documento de respaldo para una transacción
        
        Args:
            transaccion_id: ID de la transacción
            tipo_documento: Tipo de documento
            nombre_original: Nombre original del archivo
            nombre_archivo: Nombre único en el sistema
            extension: Extensión del archivo
            ruta_archivo: Ruta donde se almacena
            tamano_bytes: Tamaño en bytes
            observaciones: Observaciones
            subido_por: ID del usuario que sube
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('sp_registrar_documento_respaldo', (
                transaccion_id,
                tipo_documento,
                nombre_original,
                nombre_archivo,
                extension,
                ruta_archivo,
                tamano_bytes,
                observaciones,
                subido_por
            ))
            if not cursor.rowcount:
                raise Exception("No se pudo registrar el documento de respaldo")
            
            result = cursor.fetchone()[0] # type: ignore
            
            connection.commit()
            
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al registrar documento de respaldo: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def obtener_inscripciones(
        filtro_estado: Optional[str] = None,
        filtro_programa: Optional[int] = None,
        filtro_fecha_desde: Optional[date] = None,
        filtro_fecha_hasta: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene lista de inscripciones con filtros
        
        Args:
            filtro_estado: Filtrar por estado
            filtro_programa: Filtrar por programa
            filtro_fecha_desde: Filtrar desde fecha
            filtro_fecha_hasta: Filtrar hasta fecha
            
        Returns:
            Lista de inscripciones
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            # Convertir fechas a string si se proporcionan
            fecha_desde_str = filtro_fecha_desde.isoformat() if filtro_fecha_desde else None
            fecha_hasta_str = filtro_fecha_hasta.isoformat() if filtro_fecha_hasta else None
            
            cursor.callproc('fn_obtener_inscripciones', (
                filtro_estado,
                filtro_programa,
                fecha_desde_str,
                fecha_hasta_str
            ))
            results = cursor.fetchall()
            
            # Convertir a lista de diccionarios
            columns = [
                'inscripcion_id', 'estudiante_id', 'estudiante_nombre',
                'estudiante_ci', 'programa_id', 'programa_nombre',
                'programa_codigo', 'fecha_inscripcion', 'estado',
                'valor_final', 'cupos_disponibles',
                'pagos_realizados', 'saldo_pendiente'
            ]
            
            inscripciones = []
            for row in results:
                inscripcion = dict(zip(columns, row))
                
                # Convertir tipos de datos
                inscripcion['valor_final'] = float(inscripcion['valor_final'])
                inscripcion['pagos_realizados'] = float(inscripcion['pagos_realizados'])
                inscripcion['saldo_pendiente'] = float(inscripcion['saldo_pendiente'])
                
                inscripciones.append(inscripcion)
            
            return inscripciones
            
        except Exception as e:
            logger.error(f"Error al obtener inscripciones: {e}")
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def obtener_inscripciones_por_estudiante(estudiante_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todas las inscripciones de un estudiante
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Lista de inscripciones del estudiante
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            query = """
            SELECT 
                i.id,
                i.fecha_inscripcion,
                i.estado,
                i.valor_final,
                p.codigo,
                p.nombre as programa_nombre,
                p.costo_total,
                COALESCE(SUM(t.monto_final), 0) as pagado,
                (p.costo_total - COALESCE(SUM(t.monto_final), 0)) - COALESCE(i.valor_final, 0) as saldo
            FROM inscripciones i
            JOIN programas p ON i.programa_id = p.id
            LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
                AND i.programa_id = t.programa_id
                AND t.estado = 'CONFIRMADO'
            WHERE i.estudiante_id = %s
            GROUP BY i.id, p.id
            ORDER BY i.fecha_inscripcion DESC
            """
            
            cursor.execute(query, (estudiante_id,))
            results = cursor.fetchall()
            
            columns = [
                'id', 'fecha_inscripcion', 'estado', 'valor_final',
                'programa_codigo', 'programa_nombre', 'costo_total',
                'pagado', 'saldo'
            ]
            
            inscripciones = []
            for row in results:
                inscripcion = dict(zip(columns, row))
                inscripciones.append(inscripcion)
            
            return inscripciones
            
        except Exception as e:
            logger.error(f"Error al obtener inscripciones por estudiante: {e}")
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def obtener_inscripciones_por_programa(programa_id):
        """Obtener todas las inscripciones de un programa específico"""
        try:
            from config.database import Database

            query = """
            SELECT 
                i.id,
                i.estudiante_id,
                i.programa_id,
                i.fecha_inscripcion,
                i.estado,
                i.observaciones,
                e.nombres,
                e.apellido_paterno,
                e.apellido_materno,
                e.ci_numero || ' ' || e.ci_expedicion as ci,
                e.email,
                e.telefono
            FROM inscripciones i
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE i.programa_id = %s
            ORDER BY e.apellido_paterno, e.apellido_materno, e.nombres DESC
            """
            conn = Database.get_connection()
            if not conn:
                return []

            with conn:
                cursor = conn.cursor()
                with cursor:
                    cursor.execute(query, (programa_id,))
                    if cursor.description is None:
                        logger.warning(f"No se obtuvieron resultados para programa_id: {programa_id}")
                        return []
                    
                    columns = [desc[0] for desc in cursor.description]
                    resultados = []

                    for row in cursor.fetchall():
                        inscripcion = dict(zip(columns, row))
                        # Anidar datos del estudiante
                        inscripcion['estudiante'] = {
                            'nombres': row[6],
                            'apellido_paterno': row[7],
                            'apellido_materno': row[8],
                            'ci': row[9],
                            'email': row[10],
                            'telefono': row[11]
                        }
                        resultados.append(inscripcion)

                    return resultados

        except Exception as e:
            logger.error(f"Error obteniendo inscripciones por programa: {e}")
            return []
    
    @staticmethod
    def obtener_programas_inscritos_estudiante(estudiante_id: int) -> List[Dict]:
        """Obtener todos los programas en los que un estudiante está inscrito"""
        try:
            connection = Database.get_connection()
            if not connection:
                return []
            
            cursor = connection.cursor()
            # Actualizar consulta para incluir valor_final
            query = """
            SELECT 
                i.id,
                i.estudiante_id,
                i.programa_id,
                i.fecha_inscripcion,
                i.estado,
                i.valor_final,  -- Cambiado
                i.observaciones,
                p.codigo as programa_codigo,
                p.nombre as programa_nombre,
                p.costo_total,
                p.costo_matricula,
                p.costo_inscripcion,
                p.costo_mensualidad,
                p.numero_cuotas,
                CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) as estudiante_nombre,
                e.ci_numero,
                e.ci_expedicion
            FROM inscripciones i
            JOIN programas p ON i.programa_id = p.id
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE i.estudiante_id = %s 
            AND i.estado != 'RETIRADO'
            ORDER BY i.fecha_inscripcion DESC
            """
            
            cursor.execute(query, (estudiante_id,))
            if cursor.description is None:
                logger.warning(f"No se obtuvieron resultados para estudiante_id: {estudiante_id}")
                cursor.close()
                Database.return_connection(connection)
                return []
            resultados = cursor.fetchall()
            
            if resultados:
                column_names = [desc[0] for desc in cursor.description]
                inscripciones = []
                for row in resultados:
                    inscripcion = dict(zip(column_names, row))
                    if inscripcion.get('id'):
                        inscripciones.append(inscripcion)
                
                cursor.close()
                Database.return_connection(connection)
                return inscripciones
            else:
                cursor.close()
                Database.return_connection(connection)
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo programas inscritos para estudiante {estudiante_id}: {e}")
            return []
    
    @staticmethod
    def obtener_estudiantes_inscritos_programa(programa_id: int) -> List[Dict]:
        """Obtener todos los estudiantes inscritos en un programa"""
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return []

            cursor = connection.cursor()
            # ACTUALIZAR: cambiar valor_final por valor_final
            query = """
            SELECT 
                i.id as inscripcion_id,
                e.id as estudiante_id,
                e.ci_numero,
                e.ci_expedicion,
                e.nombres,
                e.apellido_paterno,
                e.apellido_materno,
                e.email,
                e.telefono,
                i.estado as estado_inscripcion,
                i.fecha_inscripcion,
                i.valor_final
            FROM inscripciones i
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE i.programa_id = %s 
            AND i.estado NOT IN ('RETIRADO')
            ORDER BY e.apellido_paterno, e.apellido_materno, e.nombres
            """

            cursor.execute(query, (programa_id,))
            if cursor.description is None:
                logger.warning(f"No se obtuvieron resultados para programa_id: {programa_id}")
                cursor.close()
                Database.return_connection(connection)
                return []
            
            resultados = cursor.fetchall()

            estudiantes = []
            if resultados:
                column_names = [desc[0] for desc in cursor.description]
                for row in resultados:
                    estudiante = dict(zip(column_names, row))
                    estudiantes.append(estudiante)

            cursor.close()
            Database.return_connection(connection)
            return estudiantes

        except Exception as e:
            logger.error(f"Error obteniendo estudiantes inscritos en programa: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    @staticmethod
    def obtener_saldo_pendiente_inscripcion(inscripcion_id: int) -> Dict[str, Any]:
        """
        Obtener el saldo pendiente de una inscripción basado en valor_final
        
        Args:
            inscripcion_id: ID de la inscripción
            
        Returns:
            Dict con saldo_pendiente, monto_total y total_pagado
        """
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return {
                    'exito': False,
                    'error': 'No hay conexión a la base de datos',
                    'saldo_pendiente': 0.0,
                    'monto_total': 0.0,
                    'total_pagado': 0.0
                }
            
            cursor = connection.cursor()
            
            # Verificar el esquema de la tabla transacciones
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'transacciones' 
                AND column_name IN ('inscripcion_id', 'estudiante_id', 'programa_id')
            """)
            columnas_transacciones = [row[0] for row in cursor.fetchall()]
            
            logger.debug(f"Columnas disponibles en transacciones: {columnas_transacciones}")
            
            # Obtener información básica de la inscripción con valor_final
            query_inscripcion = """
            SELECT 
                i.estudiante_id,
                i.programa_id,
                p.costo_total,
                i.valor_final,  -- Cambiado
                p.codigo,
                p.nombre,
                e.nombres,
                e.apellido_paterno,
                e.apellido_materno
            FROM inscripciones i
            JOIN programas p ON i.programa_id = p.id
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE i.id = %s
            """
            
            cursor.execute(query_inscripcion, (inscripcion_id,))
            resultado_insc = cursor.fetchone()
            
            if not resultado_insc:
                cursor.close()
                Database.return_connection(connection)
                return {
                    'exito': False,
                    'error': f'No se encontró la inscripción ID: {inscripcion_id}',
                    'saldo_pendiente': 0.0,
                    'monto_total': 0.0,
                    'total_pagado': 0.0
                }
            
            # Desempaquetar resultados
            (estudiante_id, programa_id, costo_total, valor_final, codigo_programa, 
            nombre_programa, nombres, apellido_paterno, apellido_materno) = resultado_insc
            
            # Calcular descuento implícito
            costo_total_float = float(costo_total or 0)
            valor_final_float = float(valor_final or costo_total_float)
            descuento_implicito = 0.0
            
            if costo_total_float > 0:
                descuento_implicito = ((costo_total_float - valor_final_float) / costo_total_float) * 100
            
            # Determinar cómo relacionar transacciones con la inscripción
            if 'inscripcion_id' in columnas_transacciones:
                query_transacciones = """
                SELECT 
                    COALESCE(SUM(t.monto_final), 0) as total_pagado,
                    COUNT(t.id) as cantidad_transacciones
                FROM transacciones t
                WHERE t.inscripcion_id = %s
                AND t.estado NOT IN ('ANULADO', 'RECHAZADO')
                """
                params = (inscripcion_id,)
                
            elif 'estudiante_id' in columnas_transacciones and 'programa_id' in columnas_transacciones:
                query_transacciones = """
                SELECT 
                    COALESCE(SUM(t.monto_final), 0) as total_pagado,
                    COUNT(t.id) as cantidad_transacciones
                FROM transacciones t
                WHERE t.estudiante_id = %s
                AND t.programa_id = %s
                AND t.estado NOT IN ('ANULADO', 'RECHAZADO')
                """
                params = (estudiante_id, programa_id)
                
            elif 'estudiante_id' in columnas_transacciones:
                query_transacciones = """
                SELECT 
                    COALESCE(SUM(t.monto_final), 0) as total_pagado,
                    COUNT(t.id) as cantidad_transacciones
                FROM transacciones t
                WHERE t.estudiante_id = %s
                AND t.estado NOT IN ('ANULADO', 'RECHAZADO')
                """
                params = (estudiante_id,)
                
            else:
                total_pagado = 0.0
                cantidad_transacciones = 0
                cursor.close()
                Database.return_connection(connection)
                
                saldo_pendiente = max(0, valor_final_float)
                
                return {
                    'exito': True,
                    'saldo_pendiente': saldo_pendiente,
                    'monto_total': valor_final_float,
                    'total_pagado': total_pagado,
                    'cantidad_transacciones': cantidad_transacciones,
                    'costo_total': costo_total_float,
                    'valor_final': valor_final_float,
                    'descuento_implicito': descuento_implicito,
                    'estudiante_id': estudiante_id,
                    'programa_id': programa_id,
                    'programa': {
                        'codigo': codigo_programa,
                        'nombre': nombre_programa
                    },
                    'estudiante': {
                        'nombres': nombres,
                        'apellido_paterno': apellido_paterno,
                        'apellido_materno': apellido_materno
                    },
                    'advertencia': 'No se pudieron relacionar transacciones con esta inscripción'
                }
            
            # Ejecutar consulta de transacciones
            cursor.execute(query_transacciones, params)
            resultado_pagos = cursor.fetchone()
            
            total_pagado = float(resultado_pagos[0] or 0) if resultado_pagos else 0.0
            cantidad_transacciones = int(resultado_pagos[1] or 0) if resultado_pagos else 0
            
            cursor.close()
            Database.return_connection(connection)
            
            saldo_pendiente = max(0, valor_final_float - total_pagado)
            
            return {
                'exito': True,
                'saldo_pendiente': saldo_pendiente,
                'monto_total': valor_final_float,
                'total_pagado': total_pagado,
                'cantidad_transacciones': cantidad_transacciones,
                'costo_total': costo_total_float,
                'valor_final': valor_final_float,
                'descuento_implicito': descuento_implicito,
                'estudiante_id': estudiante_id,
                'programa_id': programa_id,
                'programa': {
                    'codigo': codigo_programa,
                    'nombre': nombre_programa
                },
                'estudiante': {
                    'nombres': nombres,
                    'apellido_paterno': apellido_paterno,
                    'apellido_materno': apellido_materno
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo saldo pendiente de inscripción {inscripcion_id}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'exito': False,
                'error': str(e),
                'saldo_pendiente': 0.0,
                'monto_total': 0.0,
                'total_pagado': 0.0
            }
    
    @staticmethod
    def obtener_monto_mensualidad_programa(programa_id: int) -> Dict[str, Any]:
        """
        Obtener el monto de mensualidad de un programa
        
        Args:
            programa_id: ID del programa
            
        Returns:
            Dict con costo_mensualidad y otros datos del programa
        """
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return {'exito': False, 'error': 'No hay conexión', 'costo_mensualidad': 0.0}
            
            cursor = connection.cursor()
            
            query = """
            SELECT 
                costo_mensualidad,
                costo_matricula,
                costo_inscripcion,
                costo_total,
                codigo,
                nombre
            FROM programas 
            WHERE id = %s
            """
            
            cursor.execute(query, (programa_id,))
            resultado = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if not resultado:
                return {'exito': False, 'error': 'Programa no encontrado', 'costo_mensualidad': 0.0}
            
            (costo_mensualidad, costo_matricula, costo_inscripcion, 
            costo_total, codigo, nombre) = resultado
            
            return {
                'exito': True,
                'costo_mensualidad': float(costo_mensualidad or 0),
                'costo_matricula': float(costo_matricula or 0),
                'costo_inscripcion': float(costo_inscripcion or 0),
                'costo_total': float(costo_total or 0),
                'codigo': codigo,
                'nombre': nombre
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo monto mensualidad programa {programa_id}: {e}")
            return {'exito': False, 'error': str(e), 'costo_mensualidad': 0.0}
    
    @staticmethod
    def obtener_detalle_inscripcion(inscripcion_id: int) -> Dict[str, Any]:
        """
        Obtiene detalle completo de una inscripción
        
        Args:
            inscripcion_id: ID de la inscripción
            
        Returns:
            Dict con detalle completo de la inscripción
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            if not cursor:
                raise Exception("No se pudo crear cursor para la base de datos")
            
            cursor.callproc('fn_obtener_detalle_inscripcion', (inscripcion_id,))
            result = cursor.fetchone()[0] # type: ignore
            
            if isinstance(result, str):
                result_data = json.loads(result)
            elif isinstance(result, dict):
                result_data = result
            else:
                result_data = {'success': True, 'data': result}
            
            return result_data
            
        except Exception as e:
            logger.error(f"Error al obtener detalle de inscripción: {e}")
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def diagnosticar_esquema_transacciones():
        """Diagnosticar el esquema actual de la tabla transacciones"""
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return "No hay conexión"
            
            cursor = connection.cursor()
            
            # 1. Verificar columnas de la tabla transacciones
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'transacciones'
                ORDER BY ordinal_position
            """)
            
            columnas = cursor.fetchall()
            
            # 2. Verificar si existe columna inscripcion_id
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'transacciones' 
                    AND column_name = 'inscripcion_id'
                )
            """)
            if cursor.description is None:
                logger.warning("No se pudo verificar la existencia de la columna inscripcion_id")
                tiene_inscripcion_id = False
                raise Exception("No se pudo verificar la existencia de la columna inscripcion_id")
            
            tiene_inscripcion_id = cursor.fetchone()[0] # type: ignore
            
            # 3. Verificar relaciones con inscripciones
            cursor.execute("""
                SELECT 
                    tc.constraint_name,
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage AS ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_name = 'transacciones'
                AND tc.constraint_type = 'FOREIGN KEY'
            """)
            
            relaciones = cursor.fetchall()
            
            cursor.close()
            Database.return_connection(connection)
            
            resultado = {
                'columnas': [{'nombre': col[0], 'tipo': col[1], 'nulo': col[2]} for col in columnas],
                'tiene_inscripcion_id': tiene_inscripcion_id,
                'relaciones': [{
                    'constraint': rel[0],
                    'columna': rel[1],
                    'tabla_foreign': rel[2],
                    'columna_foreign': rel[3]
                } for rel in relaciones]
            }
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error diagnosticando esquema: {e}")
            return f"Error: {str(e)}"
    
    @staticmethod
    def actualizar_inscripcion(
        inscripcion_id: int,
        nuevo_estado: Optional[str] = None,
        nuevo_valor_final: Optional[float] = None,  # Cambiado
        nuevas_observaciones: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Actualiza una inscripción existente
        
        Args:
            inscripcion_id: ID de la inscripción
            nuevo_estado: Nuevo estado
            nuevo_valor_final: Nuevo valor final
            nuevas_observaciones: Nuevas observaciones
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('sp_actualizar_inscripcion', (
                inscripcion_id,
                nuevo_estado,
                nuevo_valor_final,  # Cambiado
                nuevas_observaciones
            ))
            if not cursor.rowcount:
                raise Exception("No se pudo actualizar la inscripción")
            
            result = cursor.fetchone()[0] # type: ignore
            
            connection.commit()
            
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al actualizar inscripción: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def eliminar_inscripcion(
        inscripcion_id: int,
        motivo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Elimina una inscripción
        
        Args:
            inscripcion_id: ID de la inscripción
            motivo: Motivo de eliminación
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('sp_eliminar_inscripcion', (inscripcion_id, motivo))
            if not cursor.rowcount:
                raise Exception("No se pudo eliminar la inscripción")
            
            result = cursor.fetchone()[0] # type: ignore
            
            connection.commit()
            
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al eliminar inscripción: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def obtener_valor_real_programa(programa_id: int) -> float:
        """
        Obtiene el valor real (costo total) de un programa
        
        Args:
            programa_id: ID del programa
            
        Returns:
            Valor real del programa
        """
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return 0.0
            
            cursor = connection.cursor()
            query = "SELECT costo_total FROM programas WHERE id = %s"
            cursor.execute(query, (programa_id,))
            resultado = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if resultado:
                return float(resultado[0] or 0)
            return 0.0
            
        except Exception as e:
            logger.error(f"Error obteniendo valor real del programa {programa_id}: {e}")
            return 0.0
    