# model/transaccion_model.py
"""
Modelo para manejar transacciones y documentos de respaldo.
"""

import logging
import json
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pathlib import Path

from config.database import Database
from config.constants import EstadoTransaccion
from .base_model import BaseModel

logger = logging.getLogger(__name__)

class TransaccionModel(BaseModel):
    """Modelo para manejar transacciones financieras"""
    
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
        Registrar pago de una inscripción usando función almacenada
        
        Args:
            inscripcion_id: ID de la inscripción
            forma_pago: Forma de pago
            monto_pagado: Monto pagado
            fecha_pago: Fecha de pago
            numero_comprobante: Número de comprobante
            banco_origen: Banco de origen
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
            
            # Ejecutar función almacenada
            cursor.callproc('fn_registrar_pago_inscripcion', (
                inscripcion_id,
                forma_pago,
                monto_pagado,
                fecha_pago.isoformat() if fecha_pago else None,
                numero_comprobante,
                banco_origen,
                cuenta_origen,
                observaciones,
                registrado_por
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
            logger.error(f"Error al registrar pago: {e}")
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
    @staticmethod
    def obtener_transacciones_inscripcion(inscripcion_id: int) -> List[Dict]:
        """Obtener todas las transacciones de una inscripción"""
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return []
            
            cursor = connection.cursor()
            query = """
            SELECT 
                t.id,
                t.numero_transaccion,
                t.fecha_pago,
                t.monto_final,
                t.forma_pago,
                t.numero_comprobante,
                t.estado,
                t.observaciones,
                t.banco_origen,
                t.cuenta_origen,
                COUNT(dt.id) as numero_documentos
            FROM transacciones t
            LEFT JOIN documentos_respaldo dt ON t.id = dt.transaccion_id
            WHERE t.estudiante_id = (
                SELECT estudiante_id FROM inscripciones WHERE id = %s
            )
            AND t.programa_id = (
                SELECT programa_id FROM inscripciones WHERE id = %s
            )
            GROUP BY t.id, t.numero_transaccion, t.fecha_pago, t.monto_final, 
                    t.forma_pago, t.numero_comprobante, t.estado, 
                    t.observaciones, t.banco_origen, t.cuenta_origen
            ORDER BY t.fecha_pago DESC
            """
            
            cursor.execute(query, (inscripcion_id, inscripcion_id))
            resultados = cursor.fetchall()
            
            transacciones = []
            column_names = [desc[0] for desc in cursor.description]
            
            for row in resultados:
                transaccion = dict(zip(column_names, row))
                # Formatear fecha si es datetime
                if transaccion.get('fecha_pago'):
                    if isinstance(transaccion['fecha_pago'], datetime):
                        transaccion['fecha_pago'] = transaccion['fecha_pago'].strftime('%Y-%m-%d')
                    elif isinstance(transaccion['fecha_pago'], date):
                        transaccion['fecha_pago'] = transaccion['fecha_pago'].isoformat()
                transacciones.append(transaccion)
            
            cursor.close()
            Database.return_connection(connection)
            return transacciones
            
        except Exception as e:
            logger.error(f"Error obteniendo transacciones de inscripción: {e}")
            return []
    
    @staticmethod
    def obtener_transaccion(
        transaccion_id: int
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener una transacción por ID
        
        Args:
            transaccion_id: ID de la transacción
            
        Returns:
            Dict con datos de la transacción
        """
        try:
            query = """
                SELECT t.*, 
                        CONCAT(e.nombres, ' ', e.apellido_paterno) as estudiante_nombre,
                        p.nombre as programa_nombre,
                        u.nombre_completo as usuario_registro
                FROM transacciones t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                LEFT JOIN usuarios u ON t.registrado_por = u.id
                WHERE t.id = %s
            """
            params = (transaccion_id,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result:
                column_names = [
                    'id', 'numero_transaccion', 'estudiante_id', 'programa_id',
                    'fecha_pago', 'fecha_registro', 'monto_total', 'descuento_total',
                    'monto_final', 'forma_pago', 'estado', 'numero_comprobante',
                    'banco_origen', 'cuenta_origen', 'observaciones', 'registrado_por',
                    'estudiante_nombre', 'programa_nombre', 'usuario_registro'
                ]
                return dict(zip(column_names, result))
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo transacción: {e}")
            return None
    
    @staticmethod
    def obtener_detalles_transaccion(transaccion_id: int) -> List[Dict]:
        """Obtener detalles de una transacción"""
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return []
            
            cursor = connection.cursor()
            query = """
            SELECT 
                dt.id,
                dt.transaccion_id,
                dt.concepto_pago_id,
                cp.codigo as concepto_codigo,
                cp.nombre as concepto_nombre,
                dt.descripcion,
                dt.cantidad,
                dt.precio_unitario,
                dt.subtotal,
                dt.orden
            FROM detalles_transaccion dt
            JOIN conceptos_pago cp ON dt.concepto_pago_id = cp.id
            WHERE dt.transaccion_id = %s
            ORDER BY dt.orden
            """
            
            cursor.execute(query, (transaccion_id,))
            resultados = cursor.fetchall()
            
            detalles = []
            column_names = [desc[0] for desc in cursor.description]
            
            for row in resultados:
                detalle = dict(zip(column_names, row))
                detalles.append(detalle)
            
            cursor.close()
            Database.return_connection(connection)
            return detalles
            
        except Exception as e:
            logger.error(f"Error obteniendo detalles de transacción: {e}")
            return []
    
    @staticmethod
    def obtener_documentos_respaldo(
        transaccion_id: int
    ) -> List[Dict[str, Any]]:
        """
        Obtener documentos de respaldo de una transacción
        
        Args:
            transaccion_id: ID de la transacción
            
        Returns:
            Lista de documentos
        """
        try:
            query = """
                SELECT dr.*, u.nombre_completo as usuario_subida
                FROM documentos_respaldo dr
                LEFT JOIN usuarios u ON dr.subido_por = u.id
                WHERE dr.transaccion_id = %s
                ORDER BY dr.fecha_subida DESC
            """
            params = (transaccion_id,)
            
            results = Database.execute_query(query, params)
            
            if results:
                column_names = [
                    'id', 'transaccion_id', 'tipo_documento', 'nombre_original',
                    'nombre_archivo', 'extension', 'ruta_archivo', 'tamano_bytes',
                    'observaciones', 'subido_por', 'fecha_subida', 'usuario_subida'
                ]
                return [dict(zip(column_names, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo documentos de respaldo: {e}")
            return []
    
    def subir_documento_respaldo(
        self,
        transaccion_id: int,
        tipo_documento: str,
        ruta_archivo: str,
        observaciones: Optional[str] = None,
        subido_por: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Subir documento de respaldo para una transacción
        
        Args:
            transaccion_id: ID de la transacción
            tipo_documento: Tipo de documento
            ruta_archivo: Ruta del archivo
            observaciones: Observaciones
            subido_por: ID del usuario que sube
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            # Verificar que el archivo existe
            if not Path(ruta_archivo).exists():
                return {
                    'success': False,
                    'message': 'El archivo no existe'
                }
            
            # Obtener información del archivo
            archivo_path = Path(ruta_archivo)
            nombre_original = archivo_path.name
            extension = archivo_path.suffix.lower().lstrip('.')
            tamano_bytes = archivo_path.stat().st_size
            
            # Generar nombre único para el archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_archivo = f"doc_{transaccion_id}_{timestamp}{archivo_path.suffix}"
            
            # Definir ruta de almacenamiento
            # (Aquí deberías configurar tu sistema de almacenamiento)
            ruta_destino = self.obtener_ruta_de_config("RUTA_RESPALDOS")
            if not ruta_destino:
                raise Exception("No se ha configurado la ruta de respaldos")
            ruta_destino = Path(ruta_destino) / nombre_archivo
            
            # Copiar archivo a destino
            import shutil
            shutil.copy2(ruta_archivo, ruta_destino)
            
            # Guardar en base de datos
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            query = """
                INSERT INTO documentos_respaldo (
                    transaccion_id, tipo_documento, nombre_original,
                    nombre_archivo, extension, ruta_archivo, tamano_bytes,
                    observaciones, subido_por
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            params = (
                transaccion_id, tipo_documento, nombre_original,
                nombre_archivo, extension, str(ruta_destino), tamano_bytes,
                observaciones, subido_por
            )
            
            cursor.execute(query, params)
            documento_id = cursor.fetchone()[0]
            
            connection.commit()
            
            return {
                'success': True,
                'message': 'Documento subido exitosamente',
                'data': {'documento_id': documento_id}
            }
                
        except Exception as e:
            logger.error(f"Error al subir documento: {e}")
            if connection:
                connection.rollback()
            return {
                'success': False,
                'message': f'Error al subir documento: {str(e)}'
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
    def eliminar_documento_respaldo(
        documento_id: int
    ) -> Dict[str, Any]:
        """
        Eliminar documento de respaldo
        
        Args:
            documento_id: ID del documento
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            # Primero obtener información del documento
            query_select = """
                SELECT ruta_archivo FROM documentos_respaldo
                WHERE id = %s
            """
            result = Database.execute_query(query_select, (documento_id,), fetch_one=True)
            
            if not result:
                return {
                    'success': False,
                    'message': 'Documento no encontrado'
                }
            
            ruta_archivo = result[0]
            
            # Eliminar archivo físico
            if Path(ruta_archivo).exists():
                Path(ruta_archivo).unlink()
            
            # Eliminar registro de base de datos
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            query_delete = """
                DELETE FROM documentos_respaldo
                WHERE id = %s
                RETURNING id
            """
            cursor.execute(query_delete, (documento_id,))
            
            connection.commit()
            
            return {
                'success': True,
                'message': 'Documento eliminado exitosamente'
            }
                
        except Exception as e:
            logger.error(f"Error al eliminar documento: {e}")
            if connection:
                connection.rollback()
            return {
                'success': False,
                'message': f'Error al eliminar documento: {str(e)}'
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
    def anular_transaccion(
        transaccion_id: int,
        motivo_anulacion: str,
        anulado_por: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Anular una transacción
        
        Args:
            transaccion_id: ID de la transacción
            motivo_anulacion: Motivo de anulación
            anulado_por: ID del usuario que anula
            
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
            
            # Actualizar estado de transacción
            query = """
                UPDATE transacciones
                SET estado = %s,
                    observaciones = COALESCE(observaciones, '') || '\nANULADA: ' || %s
                WHERE id = %s
                RETURNING id
            """
            cursor.execute(query, (
                EstadoTransaccion.ANULADO,
                motivo_anulacion,
                transaccion_id
            ))
            
            # Revertir movimiento de caja si existe
            query_movimiento = """
                UPDATE movimientos_caja
                SET descripcion = descripcion || ' (ANULADO)'
                WHERE transaccion_id = %s
            """
            cursor.execute(query_movimiento, (transaccion_id,))
            
            connection.commit()
            
            return {
                'success': True,
                'message': 'Transacción anulada exitosamente'
            }
                
        except Exception as e:
            logger.error(f"Error al anular transacción: {e}")
            if connection:
                connection.rollback()
            return {
                'success': False,
                'message': f'Error al anular transacción: {str(e)}'
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
    def obtener_ruta_de_config(
        clave: str
    ) -> Optional[str]:
        """
        Obtener la ruta del archivo asociado a una transacción
        
        Args:
            id: ID de la transacción
            
        Returns:
            Ruta del archivo o None si no existe
        """
        from config.database import Database
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            cursor = connection.cursor()
            
            cursor.callproc('fn_obtener_ruta_configuracion', (clave,))
            result = cursor.fetchone()[0]
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo ruta de configuración: {e}")
            return None
        finally:
            try:
                if cursor is not None:
                    cursor.close()
            except:
                pass
            
            if connection is not None:
                Database.return_connection(connection)
    
    # En el archivo model/transaccion_model.py, agregar:
    
    @staticmethod
    def crear_transaccion_completa(
        estudiante_id: Optional[int] = None,
        programa_id: Optional[int] = None,
        fecha_pago: Optional[str] = None,
        monto_total: float = 0,
        descuento_total: float = 0,
        forma_pago: str = 'EFECTIVO',
        estado: str = 'REGISTRADO',
        numero_comprobante: Optional[str] = None,
        banco_origen: Optional[str] = None,
        cuenta_origen: Optional[str] = None,
        observaciones: Optional[str] = None,
        registrado_por: Optional[int] = None,
        detalles: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Crear una transacción completa de manera coherente con la base de datos
        
        Args:
            estudiante_id: ID del estudiante (opcional)
            programa_id: ID del programa (opcional)
            fecha_pago: Fecha del pago (YYYY-MM-DD)
            monto_total: Monto total
            descuento_total: Descuento aplicado
            forma_pago: Forma de pago
            estado: Estado de la transacción
            numero_comprobante: Número de comprobante
            banco_origen: Banco de origen (para transferencias)
            cuenta_origen: Cuenta de origen (para transferencias)
            observaciones: Observaciones
            registrado_por: ID del usuario que registra
            detalles: Lista de detalles de la transacción
            
        Returns:
            Diccionario con resultado de la operación
        """
        connection = None
        cursor = None
        
        try:
            connection = Database.get_connection()
            if not connection:
                return {'exito': False, 'mensaje': 'Error de conexión a la base de datos'}
            
            cursor = connection.cursor()
            
            # Calcular monto final
            monto_final = monto_total - descuento_total
            
            # 1. Insertar transacción principal (el número se genera automáticamente)
            query_transaccion = """
            INSERT INTO transacciones (
                estudiante_id, programa_id, fecha_pago,
                monto_total, descuento_total, monto_final,
                forma_pago, estado, numero_comprobante,
                banco_origen, cuenta_origen, observaciones,
                registrado_por
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, numero_transaccion
            """
            
            cursor.execute(query_transaccion, (
                estudiante_id if estudiante_id else None,
                programa_id if programa_id else None,
                fecha_pago,
                monto_total,
                descuento_total,
                monto_final,
                forma_pago,
                estado,
                numero_comprobante if numero_comprobante else None,
                banco_origen if banco_origen else None,
                cuenta_origen if cuenta_origen else None,
                observaciones if observaciones else None,
                registrado_por if registrado_por else None
            ))
            
            transaccion_id, numero_transaccion = cursor.fetchone()
            
            # 2. Insertar detalles si existen
            if detalles:
                for detalle in detalles:
                    query_detalle = """
                    INSERT INTO detalles_transaccion (
                        transaccion_id, concepto_pago_id, descripcion,
                        cantidad, precio_unitario, subtotal, orden
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(query_detalle, (
                        transaccion_id,
                        detalle.get('concepto_pago_id', 1),
                        detalle.get('descripcion', ''),
                        detalle.get('cantidad', 1),
                        detalle.get('precio_unitario', 0),
                        detalle.get('subtotal', 0),
                        detalle.get('orden', 0)
                    ))
                    
            connection.commit()
            
            logger.info(f"✅ Transacción creada: ID={transaccion_id}, Número={numero_transaccion}")
            
            return {
                'exito': True,
                'transaccion_id': transaccion_id,
                'numero_transaccion': numero_transaccion,
                'mensaje': 'Transacción registrada exitosamente'
            }
            
        except Exception as e:
            logger.error(f"❌ Error creando transacción completa: {e}")
            if connection:
                connection.rollback()
            return {
                'exito': False,
                'mensaje': f'Error al registrar transacción: {str(e)}'
            }
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
            
    @classmethod
    def generar_numero_transaccion(cls) -> str:
        """Generar número de transacción único"""
        try:
            import random
            
            fecha = datetime.now().strftime('%Y%m%d')
            secuencia = str(random.randint(1000, 9999))
            
            return f"TRX-{fecha}-{secuencia}"
        
        except Exception as e:
            logger.error(f"Error generando número de transacción: {e}")
            return f"TRX-{int(datetime.now().timestamp())}"
    
    @staticmethod
    def obtener_transacciones_filtradas(filtros: Optional[Dict] = None) -> List[Dict]:
        """Obtener transacciones con filtros"""
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            
            where_clauses = []
            params = []
            
            if filtros:
                # Filtrar por fecha
                if 'fecha_desde' in filtros:
                    where_clauses.append("t.fecha_pago >= %s")
                    params.append(filtros['fecha_desde'])
                    
                if 'fecha_hasta' in filtros:
                    where_clauses.append("t.fecha_pago <= %s")
                    params.append(filtros['fecha_hasta'])
                    
                # Filtrar por estado
                if 'estado' in filtros:
                    where_clauses.append("t.estado = %s")
                    params.append(filtros['estado'])
                    
                # Filtrar por forma de pago
                if 'forma_pago' in filtros:
                    where_clauses.append("t.forma_pago = %s")
                    params.append(filtros['forma_pago'])
                    
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            query = f"""
                SELECT t.*, 
                        e.nombres || ' ' || e.apellido_paterno as estudiante_nombre,
                        p.nombre as programa_nombre
                FROM transacciones t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                WHERE {where_sql}
                ORDER BY t.fecha_pago DESC
            """
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            transacciones = []
            column_names = [desc[0] for desc in cursor.description]
            
            for row in resultados:
                transaccion = dict(zip(column_names, row))
                # Formatear fechas
                for key in ['fecha_pago', 'fecha_registro']:
                    if key in transaccion and transaccion[key]:
                        if isinstance(transaccion[key], (datetime, date)):
                            transaccion[key] = transaccion[key].isoformat()
                transacciones.append(transaccion)
                
            return transacciones
        
        except Exception as e:
            logger.error(f"Error obteniendo transacciones filtradas: {e}")
            return []
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def obtener_transacciones_por_filtros(
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        estado: Optional[str] = None,
        forma_pago: Optional[str] = None,
        estudiante_id: Optional[int] = None,
        programa_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Obtener transacciones filtradas
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            
            # Construir query dinámica
            query = """
                SELECT t.*, 
                        e.nombres || ' ' || e.apellido_paterno as estudiante_nombre,
                        p.nombre as programa_nombre,
                        u.nombre_completo as usuario_registro
                FROM transacciones t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                LEFT JOIN usuarios u ON t.registrado_por = u.id
                WHERE 1=1
            """
            
            params = []
            
            if fecha_desde:
                query += " AND t.fecha_pago >= %s"
                params.append(fecha_desde)
                
            if fecha_hasta:
                query += " AND t.fecha_pago <= %s"
                params.append(fecha_hasta)
                
            if estado:
                query += " AND t.estado = %s"
                params.append(estado)
                
            if forma_pago:
                query += " AND t.forma_pago = %s"
                params.append(forma_pago)
                
            if estudiante_id:
                query += " AND t.estudiante_id = %s"
                params.append(estudiante_id)
                
            if programa_id:
                query += " AND t.programa_id = %s"
                params.append(programa_id)
                
            query += " ORDER BY t.fecha_pago DESC, t.id DESC"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            resultados = cursor.fetchall()
            
            transacciones = []
            column_names = [desc[0] for desc in cursor.description]
            
            for row in resultados:
                transaccion = dict(zip(column_names, row))
                # Formatear fechas
                for key in ['fecha_pago', 'fecha_registro']:
                    if key in transaccion and transaccion[key]:
                        if isinstance(transaccion[key], (datetime, date)):
                            transaccion[key] = transaccion[key].strftime('%Y-%m-%d')
                transacciones.append(transaccion)
                
            return transacciones
        
        except Exception as e:
            logger.error(f"Error obteniendo transacciones filtradas: {e}")
            return []
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def contar_transacciones_por_filtros(
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        estado: Optional[str] = None,
        forma_pago: Optional[str] = None,
        estudiante_id: Optional[int] = None,
        programa_id: Optional[int] = None
    ) -> int:
        """
        Contar transacciones filtradas
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return 0

            cursor = connection.cursor()

            query = "SELECT COUNT(*) FROM transacciones t WHERE 1=1"
            params = []

            if fecha_desde:
                query += " AND t.fecha_pago >= %s"
                params.append(fecha_desde)

            if fecha_hasta:
                query += " AND t.fecha_pago <= %s"
                params.append(fecha_hasta)

            if estado:
                query += " AND t.estado = %s"
                params.append(estado)

            if forma_pago:
                query += " AND t.forma_pago = %s"
                params.append(forma_pago)

            if estudiante_id:
                query += " AND t.estudiante_id = %s"
                params.append(estudiante_id)

            if programa_id:
                query += " AND t.programa_id = %s"
                params.append(programa_id)

            cursor.execute(query, params)
            resultado = cursor.fetchone()

            return resultado[0] if resultado else 0

        except Exception as e:
            logger.error(f"Error contando transacciones: {e}")
            return 0
        finally:
            try:
                if cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    