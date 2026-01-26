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
        descuento_aplicado: float = 0.0,
        observaciones: Optional[str] = None,
        fecha_inscripcion: Union[str, datetime, date, None] = None
    ) -> Dict[str, Any]:
        """
        Crea una nueva inscripción
        
        Args:
            estudiante_id: ID del estudiante
            programa_id: ID del programa
            descuento_aplicado: Descuento aplicado
            observaciones: Observaciones adicionales
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
                    # Ya es string, usar directamente o validar formato
                    fecha_str = fecha_inscripcion
                    # Si el string viene en formato QDate (dd/MM/yyyy), convertirlo
                    if '/' in fecha_str:
                        try:
                            fecha_dt = datetime.strptime(fecha_str, '%d/%m/%Y')
                            fecha_str = fecha_dt.strftime('%Y-%m-%d')
                        except ValueError:
                            # Si no se puede convertir, usar como está
                            pass
                elif isinstance(fecha_inscripcion, (datetime, date)):
                    fecha_str = fecha_inscripcion.strftime('%Y-%m-%d')
            
            cursor.callproc('fn_crear_inscripcion', (
                estudiante_id,
                programa_id,
                descuento_aplicado,
                observaciones,
                fecha_str
            ))
            result = cursor.fetchone()[0]
            
            connection.commit()
            
            # Parsear resultado JSON
            if isinstance(result, str):
                return json.loads(result)
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al crear inscripción: {e}")
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
    def crear_inscripcion_retroactiva(
        estudiante_id: int,
        programa_id: int,
        fecha_inscripcion: date,
        descuento_aplicado: float = 0.0,
        observaciones: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Crea una inscripción con fecha retroactiva
        
        Args:
            estudiante_id: ID del estudiante
            programa_id: ID del programa
            fecha_inscripcion: Fecha retroactiva de inscripción
            descuento_aplicado: Descuento aplicado
            observaciones: Observaciones adicionales
            
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
                descuento_aplicado,
                observaciones
            ))
            result = cursor.fetchone()[0]
            
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
            result = cursor.fetchone()[0]
            
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
            result = cursor.fetchone()[0]
            
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
            result = cursor.fetchone()[0]
            
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
                'descuento_aplicado', 'cupos_disponibles',
                'pagos_realizados', 'saldo_pendiente'
            ]
            
            inscripciones = []
            for row in results:
                inscripcion = dict(zip(columns, row))
                
                # Convertir tipos de datos
                inscripcion['descuento_aplicado'] = float(inscripcion['descuento_aplicado'])
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
    def obtener_programas_inscritos_estudiante(estudiante_id: int) -> List[Dict]:
        """Obtener todos los programas en los que un estudiante está inscrito"""
        try:
            connection = Database.get_connection()
            if not connection:
                return []
            
            cursor = connection.cursor()
            query = """
            SELECT 
                i.id,
                i.estudiante_id,
                i.programa_id,
                i.fecha_inscripcion,
                i.estado,
                i.descuento_aplicado,
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
            resultados = cursor.fetchall()
            
            if resultados:
                column_names = [desc[0] for desc in cursor.description]
                inscripciones = []
                for row in resultados:
                    inscripcion = dict(zip(column_names, row))
                    # Asegurarnos de que el ID sea válido
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
                i.descuento_aplicado
            FROM inscripciones i
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE i.programa_id = %s 
            AND i.estado NOT IN ('RETIRADO')
            ORDER BY e.apellido_paterno, e.apellido_materno, e.nombres
            """
            
            cursor.execute(query, (programa_id,))
            resultados = cursor.fetchall()
            
            estudiantes = []
            column_names = [desc[0] for desc in cursor.description]
            
            for row in resultados:
                estudiante = dict(zip(column_names, row))
                estudiantes.append(estudiante)
            
            cursor.close()
            Database.return_connection(connection)
            return estudiantes
            
        except Exception as e:
            logger.error(f"Error obteniendo estudiantes inscritos en programa: {e}")
            return []
    
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
            
            cursor.callproc('fn_obtener_detalle_inscripcion', (inscripcion_id,))
            result = cursor.fetchone()[0]
            
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
    def actualizar_inscripcion(
        inscripcion_id: int,
        nuevo_estado: Optional[str] = None,
        nuevo_descuento: Optional[float] = None,
        nuevas_observaciones: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Actualiza una inscripción existente
        
        Args:
            inscripcion_id: ID de la inscripción
            nuevo_estado: Nuevo estado
            nuevo_descuento: Nuevo descuento
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
                nuevo_descuento,
                nuevas_observaciones
            ))
            result = cursor.fetchone()[0]
            
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
            result = cursor.fetchone()[0]
            
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
                i.descuento_aplicado,
                p.codigo,
                p.nombre as programa_nombre,
                p.costo_total,
                COALESCE(SUM(t.monto_final), 0) as pagado,
                (p.costo_total - COALESCE(SUM(t.monto_final), 0)) - COALESCE(i.descuento_aplicado, 0) as saldo
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
                'id', 'fecha_inscripcion', 'estado', 'descuento_aplicado',
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