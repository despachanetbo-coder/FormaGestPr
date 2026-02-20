# -*- coding: utf-8 -*-
# Archivo: model/detalle_transaccion_model.py
"""
Modelo para la gestión de detalles de transacciones
Maneja operaciones CRUD para la tabla detalles_transaccion
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

from config.database import Database
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)

class DetalleTransaccionModel:
    """
    Modelo para gestionar los detalles (conceptos) de una transacción
    """
    
    TABLE_NAME = "detalles_transaccion"
    PRIMARY_KEY = "id"
    
    COLUMNS = [
        'transaccion_id', 'concepto_pago_id', 'descripcion',
        'cantidad', 'precio_unitario', 'subtotal', 'orden'
    ]
    
    @classmethod
    def _get_connection(cls):
        """Obtener conexión para transacciones manuales"""
        return Database.get_connection_safe()
    
    @classmethod
    def _return_connection(cls, connection):
        """Devolver conexión al pool"""
        Database.return_connection(connection)
    
    @classmethod
    def crear(cls, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo detalle de transacción
        
        Args:
            datos: Diccionario con los datos del detalle
            
        Returns:
            Dict con resultado y ID creado
        """
        try:
            # Validar datos obligatorios
            campos_requeridos = ['transaccion_id', 'concepto_pago_id', 'descripcion', 
                                'precio_unitario', 'subtotal']
            for campo in campos_requeridos:
                if campo not in datos or datos[campo] is None:
                    return {'success': False, 'error': f'El campo {campo} es obligatorio'}
            
            # Validar que el subtotal sea correcto
            cantidad = datos.get('cantidad', 1)
            precio = datos.get('precio_unitario', 0)
            subtotal_calculado = cantidad * precio
            
            if abs(subtotal_calculado - datos['subtotal']) > 0.01:
                return {'success': False, 'error': 'El subtotal no coincide con cantidad * precio'}
            
            # Filtrar solo columnas válidas
            datos_filtrados = {k: v for k, v in datos.items() if k in cls.COLUMNS}
            
            # Establecer orden si no se proporciona
            if 'orden' not in datos_filtrados:
                # Obtener el último orden para esta transacción
                ultimo_orden = cls._obtener_ultimo_orden(datos['transaccion_id'])
                datos_filtrados['orden'] = ultimo_orden + 1
            
            # Preparar query
            columns = list(datos_filtrados.keys())
            placeholders = ['%s'] * len(columns)
            values = [datos_filtrados[col] for col in columns]
            
            query = f"""
                INSERT INTO {cls.TABLE_NAME} 
                ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor()
                cursor.execute(query, values)
                
                # Obtener ID insertado
                result = cursor.fetchone()
                new_id = result[0] if result else None
                
                connection.commit()
                logger.info(f"✅ Detalle de transacción creado con ID: {new_id}")
                
                return {
                    'success': True, 
                    'id': new_id,
                    'message': 'Detalle registrado exitosamente'
                }
                
            except Exception as e:
                if connection:
                    connection.rollback()
                logger.error(f"❌ Error creando detalle: {e}")
                return {'success': False, 'error': str(e)}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error en método crear: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def _obtener_ultimo_orden(cls, transaccion_id: int) -> int:
        """Obtener el último orden para una transacción"""
        try:
            query = f"""
                SELECT COALESCE(MAX(orden), 0) as ultimo_orden
                FROM {cls.TABLE_NAME}
                WHERE transaccion_id = %s
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return 0
                
                cursor = connection.cursor()
                cursor.execute(query, (transaccion_id,))
                result = cursor.fetchone()
                
                return result[0] if result else 0
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"Error obteniendo último orden: {e}")
            return 0
    
    @classmethod
    def listar_por_transaccion(cls, transaccion_id: int) -> Dict[str, Any]:
        """
        Listar todos los detalles de una transacción
        
        Args:
            transaccion_id: ID de la transacción
            
        Returns:
            Dict con resultado y lista de detalles
        """
        try:
            query = f"""
                SELECT 
                    d.*,
                    cp.nombre as concepto_nombre,
                    cp.codigo as concepto_codigo
                FROM {cls.TABLE_NAME} d
                LEFT JOIN conceptos_pago cp ON d.concepto_pago_id = cp.id
                WHERE d.transaccion_id = %s
                ORDER BY d.orden ASC, d.id ASC
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (transaccion_id,))
                results = cursor.fetchall()
                
                detalles = [dict(row) for row in results]
                
                logger.info(f"✅ {len(detalles)} detalles encontrados para transacción {transaccion_id}")
                
                return {
                    'success': True,
                    'data': detalles,
                    'total': len(detalles)
                }
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error listando detalles: {e}")
            return {'success': False, 'error': str(e), 'data': []}
    
    @classmethod
    def eliminar(cls, detalle_id: int) -> Dict[str, Any]:
        """
        Eliminar un detalle de transacción
        
        Args:
            detalle_id: ID del detalle a eliminar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            query = "DELETE FROM detalles_transaccion WHERE id = %s RETURNING id"
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor()
                cursor.execute(query, (detalle_id,))
                
                result = cursor.fetchone()
                if not result:
                    connection.rollback()
                    return {'success': False, 'error': 'No se pudo eliminar el detalle'}
                
                connection.commit()
                logger.info(f"✅ Detalle {detalle_id} eliminado")
                
                return {
                    'success': True,
                    'id': detalle_id,
                    'message': 'Detalle eliminado exitosamente'
                }
                
            except Exception as e:
                if connection:
                    connection.rollback()
                logger.error(f"❌ Error eliminando detalle {detalle_id}: {e}")
                return {'success': False, 'error': str(e)}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error en método eliminar: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def eliminar_por_transaccion(cls, transaccion_id: int) -> Dict[str, Any]:
        """
        Eliminar todos los detalles de una transacción
        
        Args:
            transaccion_id: ID de la transacción
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            query = "DELETE FROM detalles_transaccion WHERE transaccion_id = %s RETURNING id"
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor()
                cursor.execute(query, (transaccion_id,))
                
                deleted_count = cursor.rowcount
                
                connection.commit()
                logger.info(f"✅ {deleted_count} detalles eliminados para transacción {transaccion_id}")
                
                return {
                    'success': True,
                    'deleted_count': deleted_count,
                    'message': f'{deleted_count} detalles eliminados'
                }
                
            except Exception as e:
                if connection:
                    connection.rollback()
                logger.error(f"❌ Error eliminando detalles de transacción {transaccion_id}: {e}")
                return {'success': False, 'error': str(e)}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error en método eliminar_por_transaccion: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def actualizar(cls, detalle_id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar un detalle de transacción
        
        Args:
            detalle_id: ID del detalle a actualizar
            datos: Diccionario con los datos a actualizar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Filtrar solo columnas válidas
            datos_filtrados = {}
            for k, v in datos.items():
                if k in cls.COLUMNS:
                    datos_filtrados[k] = v
            
            if not datos_filtrados:
                return {'success': False, 'error': 'No hay datos válidos para actualizar'}
            
            # Construir query dinámica
            set_clause = ', '.join([f"{col} = %s" for col in datos_filtrados.keys()])
            values = list(datos_filtrados.values())
            values.append(detalle_id)
            
            query = f"""
                UPDATE {cls.TABLE_NAME}
                SET {set_clause}
                WHERE id = %s
                RETURNING id
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor()
                cursor.execute(query, values)
                
                result = cursor.fetchone()
                if not result:
                    connection.rollback()
                    return {'success': False, 'error': 'No se pudo actualizar el detalle'}
                
                connection.commit()
                logger.info(f"✅ Detalle {detalle_id} actualizado")
                
                return {
                    'success': True,
                    'id': detalle_id,
                    'message': 'Detalle actualizado exitosamente'
                }
                
            except Exception as e:
                if connection:
                    connection.rollback()
                logger.error(f"❌ Error actualizando detalle {detalle_id}: {e}")
                return {'success': False, 'error': str(e)}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error en método actualizar: {e}")
            return {'success': False, 'error': str(e)}