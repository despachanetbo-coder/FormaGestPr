# Archivo: model/transaccion_model.py
"""
Modelo para la gestión de transacciones de pago
Maneja operaciones CRUD con control de transacciones SQL
"""

import logging
from typing import Optional, Dict, List, Any, Tuple, Union
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

from config.database import Database
from config.constants import EstadoTransaccion, FormaPago
from model.inscripcion_model import InscripcionModel

logger = logging.getLogger(__name__)

class TransaccionModel:
    """
    Modelo para gestionar transacciones de pago
    Todas las operaciones que modifican datos usan transacciones SQL explícitas
    """
    
    # Constantes de la tabla
    TABLE_NAME = "transacciones"
    PRIMARY_KEY = "id"
    
    # Columnas permitidas para inserción/actualización
    COLUMNS = [
        'numero_transaccion', 'estudiante_id', 'programa_id', 'fecha_pago',
        'monto_total', 'descuento_total', 'monto_final', 'forma_pago',
        'estado', 'numero_comprobante', 'banco_origen', 'cuenta_origen',
        'observaciones', 'registrado_por'
    ]
    
    # Columnas de solo lectura (generadas automáticamente)
    READONLY_COLUMNS = ['id', 'fecha_registro']
    
    @classmethod
    def _get_connection(cls):
        """Obtener conexión para transacciones manuales"""
        return Database.get_connection_safe()
    
    @classmethod
    def _return_connection(cls, connection):
        """Devolver conexión al pool"""
        Database.return_connection(connection)
    
    @classmethod
    def _execute_in_transaction(cls, queries_params, return_last_id=True):
        """
        Ejecutar múltiples queries en una transacción
        
        Args:
            queries_params: Lista de tuplas (query, params)
            return_last_id: Si True, retorna el último ID insertado
            
        Returns:
            Dict con resultados o ID insertado
        """
        connection = None
        cursor = None
        try:
            connection = cls._get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            last_id = None
            
            for query, params in queries_params:
                logger.debug(f"Ejecutando query en transacción: {query[:100]}...")
                cursor.execute(query, params if params else ())
                
                # Obtener el último ID si es un INSERT y se solicita
                if return_last_id and query.strip().upper().startswith('INSERT'):
                    cursor.execute("SELECT LASTVAL()")
                    result = cursor.fetchone()
                    if result:
                        last_id = result[0]
            
            connection.commit()
            logger.info(f"✅ Transacción completada exitosamente")
            
            if return_last_id:
                return {'success': True, 'id': last_id}
            return {'success': True, 'rows_affected': cursor.rowcount}
            
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                    logger.warning("↩️ Rollback ejecutado por error")
                except:
                    pass
            logger.error(f"❌ Error en transacción: {e}")
            return {'success': False, 'error': str(e)}
            
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if connection:
                cls._return_connection(connection)
    
    @classmethod
    def crear(cls, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear una nueva transacción
        
        Args:
            datos: Diccionario con los datos de la transacción
            
        Returns:
            Dict con resultado y ID creado
        """
        try:
            # Validar datos obligatorios
            campos_requeridos = ['estudiante_id', 'fecha_pago', 'monto_total', 
                                'descuento_total', 'monto_final', 'forma_pago']
            for campo in campos_requeridos:
                if campo not in datos or datos[campo] is None:
                    return {'success': False, 'error': f'El campo {campo} es obligatorio'}
            
            # Validar montos
            if datos['monto_total'] < 0 or datos['descuento_total'] < 0 or datos['monto_final'] < 0:
                return {'success': False, 'error': 'Los montos no pueden ser negativos'}
            
            if abs(datos['monto_final'] - (datos['monto_total'] - datos['descuento_total'])) > 0.01:
                return {'success': False, 'error': 'El monto final debe ser igual a monto total menos descuento'}
            
            # Filtrar solo columnas válidas
            datos_filtrados = {k: v for k, v in datos.items() if k in cls.COLUMNS}
            
            # Establecer estado por defecto si no se proporciona
            if 'estado' not in datos_filtrados or not datos_filtrados['estado']:
                datos_filtrados['estado'] = EstadoTransaccion.REGISTRADO.value
            
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
                
                # Obtener el número de transacción generado por el trigger
                cursor.execute("SELECT numero_transaccion FROM transacciones WHERE id = %s", (new_id,))
                transaccion = cursor.fetchone()
                
                connection.commit()
                logger.info(f"✅ Transacción creada con ID: {new_id}")
                
                return {
                    'success': True, 
                    'id': new_id,
                    'numero_transaccion': transaccion[0] if transaccion else None,
                    'message': 'Transacción registrada exitosamente'
                }
                
            except Exception as e:
                if connection:
                    connection.rollback()
                logger.error(f"❌ Error creando transacción: {e}")
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
    def actualizar(cls, id_transaccion: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar una transacción existente
        
        Args:
            id_transaccion: ID de la transacción a actualizar
            datos: Diccionario con los datos a actualizar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que la transacción existe
            existe = cls.obtener_por_id(id_transaccion)
            if not existe or not existe.get('success'):
                return {'success': False, 'error': f'Transacción con ID {id_transaccion} no encontrada'}
            
            # Filtrar solo columnas válidas y remover readonly
            datos_filtrados = {}
            for k, v in datos.items():
                if k in cls.COLUMNS and k not in cls.READONLY_COLUMNS:
                    # No permitir actualizar número de transacción (generado automáticamente)
                    if k != 'numero_transaccion':
                        datos_filtrados[k] = v
            
            if not datos_filtrados:
                return {'success': False, 'error': 'No hay datos válidos para actualizar'}
            
            # Validar montos si se proporcionan
            if any(k in datos_filtrados for k in ['monto_total', 'descuento_total', 'monto_final']):
                # Obtener datos actuales para validación completa
                current = cls.obtener_por_id(id_transaccion)['data']
                
                monto_total = datos_filtrados.get('monto_total', current['monto_total'])
                descuento_total = datos_filtrados.get('descuento_total', current['descuento_total'])
                monto_final = datos_filtrados.get('monto_final', current['monto_final'])
                
                if monto_total < 0 or descuento_total < 0 or monto_final < 0:
                    return {'success': False, 'error': 'Los montos no pueden ser negativos'}
                
                if abs(monto_final - (monto_total - descuento_total)) > 0.01:
                    return {'success': False, 'error': 'El monto final debe ser igual a monto total menos descuento'}
            
            # Construir query dinámica
            set_clause = ', '.join([f"{col} = %s" for col in datos_filtrados.keys()])
            values = list(datos_filtrados.values())
            values.append(id_transaccion)
            
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
                
                # Verificar que se actualizó
                result = cursor.fetchone()
                if not result:
                    connection.rollback()
                    return {'success': False, 'error': 'No se pudo actualizar la transacción'}
                
                connection.commit()
                logger.info(f"✅ Transacción {id_transaccion} actualizada")
                
                return {
                    'success': True,
                    'id': id_transaccion,
                    'message': 'Transacción actualizada exitosamente'
                }
                
            except Exception as e:
                if connection:
                    connection.rollback()
                logger.error(f"❌ Error actualizando transacción {id_transaccion}: {e}")
                return {'success': False, 'error': str(e)}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error en método actualizar: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def cambiar_estado(cls, id_transaccion: int, nuevo_estado: str, 
                      observaciones: Optional[str] = None) -> Dict[str, Any]:
        """
        Cambiar el estado de una transacción
        
        Args:
            id_transaccion: ID de la transacción
            nuevo_estado: Nuevo estado (REGISTRADO, CONFIRMADO, ANULADO, etc.)
            observaciones: Observaciones adicionales (opcional)
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar estado
            estados_validos = [e.value for e in EstadoTransaccion]
            if nuevo_estado not in estados_validos:
                return {'success': False, 'error': f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'}
            
            # Preparar datos de actualización
            datos_update = {'estado': nuevo_estado}
            if observaciones:
                datos_update['observaciones'] = observaciones
            
            return cls.actualizar(id_transaccion, datos_update)
            
        except Exception as e:
            logger.error(f"❌ Error cambiando estado: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def obtener_por_id(cls, id_transaccion: int) -> Dict[str, Any]:
        """
        Obtener una transacción por su ID
        
        Args:
            id_transaccion: ID de la transacción
            
        Returns:
            Dict con resultado y datos de la transacción
        """
        try:
            query = f"""
                SELECT 
                    t.*,
                    e.nombres as estudiante_nombre,
                    e.apellido_paterno as estudiante_apellido_paterno,
                    e.apellido_materno as estudiante_apellido_materno,
                    CONCAT(e.ci_numero, ' ', e.ci_expedicion) as estudiante_ci,
                    p.nombre as programa_nombre,
                    p.codigo as programa_codigo,
                    u.nombre_completo as registrado_por_nombre
                FROM {cls.TABLE_NAME} t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                LEFT JOIN usuarios u ON t.registrado_por = u.id
                WHERE t.id = %s
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (id_transaccion,))
                result = cursor.fetchone()
                
                if not result:
                    return {'success': False, 'error': f'Transacción con ID {id_transaccion} no encontrada'}
                
                return {'success': True, 'data': dict(result)}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo transacción {id_transaccion}: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def obtener_por_numero(cls, numero_transaccion: str) -> Dict[str, Any]:
        """
        Obtener una transacción por su número
        
        Args:
            numero_transaccion: Número de transacción
            
        Returns:
            Dict con resultado y datos de la transacción
        """
        try:
            query = f"""
                SELECT 
                    t.*,
                    e.nombres as estudiante_nombre,
                    e.apellido_paterno as estudiante_apellido_paterno,
                    e.apellido_materno as estudiante_apellido_materno,
                    CONCAT(e.ci_numero, ' ', e.ci_expedicion) as estudiante_ci,
                    p.nombre as programa_nombre,
                    p.codigo as programa_codigo,
                    u.nombre_completo as registrado_por_nombre
                FROM {cls.TABLE_NAME} t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                LEFT JOIN usuarios u ON t.registrado_por = u.id
                WHERE t.numero_transaccion = %s
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (numero_transaccion,))
                result = cursor.fetchone()
                
                if not result:
                    return {'success': False, 'error': f'Transacción {numero_transaccion} no encontrada'}
                
                return {'success': True, 'data': dict(result)}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo transacción {numero_transaccion}: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def listar(cls, filtros: Optional[Dict[str, Any]] = None, 
              limite: int = 100, offset: int = 0,
              ordenar_por: str = 'fecha_pago', orden: str = 'DESC') -> Dict[str, Any]:
        """
        Listar transacciones con filtros
        
        Args:
            filtros: Diccionario con filtros (ej: {'estudiante_id': 1, 'estado': 'CONFIRMADO'})
            limite: Número máximo de registros
            offset: Desplazamiento para paginación
            ordenar_por: Columna para ordenar
            orden: 'ASC' o 'DESC'
            
        Returns:
            Dict con resultado, lista de transacciones y total
        """
        try:
            # Validar orden
            orden = orden.upper()
            if orden not in ['ASC', 'DESC']:
                orden = 'DESC'
            
            # Construir WHERE dinámico
            where_clauses = []
            params = []
            
            if filtros:
                for campo, valor in filtros.items():
                    if valor is not None:
                        if campo in cls.COLUMNS + ['estudiante_nombre', 'programa_nombre']:
                            if campo == 'estudiante_nombre':
                                where_clauses.append("CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) ILIKE %s")
                                params.append(f"%{valor}%")
                            elif campo == 'programa_nombre':
                                where_clauses.append("p.nombre ILIKE %s")
                                params.append(f"%{valor}%")
                            elif isinstance(valor, str) and campo not in ['estado', 'forma_pago']:
                                where_clauses.append(f"t.{campo} ILIKE %s")
                                params.append(f"%{valor}%")
                            else:
                                where_clauses.append(f"t.{campo} = %s")
                                params.append(valor)
            
            where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            
            # Query principal
            query = f"""
                SELECT 
                    t.*,
                    CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) as estudiante_nombre_completo,
                    CONCAT(e.ci_numero, ' ', e.ci_expedicion) as estudiante_ci,
                    p.nombre as programa_nombre,
                    p.codigo as programa_codigo
                FROM {cls.TABLE_NAME} t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                {where_sql}
                ORDER BY t.{ordenar_por} {orden}
                LIMIT %s OFFSET %s
            """
            
            # Query para contar total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM {cls.TABLE_NAME} t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                {where_sql}
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                
                # Obtener total
                cursor.execute(count_query, params)
                total_result = cursor.fetchone()
                total = total_result['total'] if total_result else 0
                
                # Obtener datos paginados
                query_params = params + [limite, offset]
                cursor.execute(query, query_params)
                results = cursor.fetchall()
                
                transacciones = [dict(row) for row in results]
                
                return {
                    'success': True,
                    'data': transacciones,
                    'total': total,
                    'limite': limite,
                    'offset': offset,
                    'pagina': (offset // limite) + 1 if limite > 0 else 1,
                    'total_paginas': (total + limite - 1) // limite if limite > 0 else 0
                }
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error listando transacciones: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def listar_por_estudiante(cls, estudiante_id: int, 
                             limite: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Listar transacciones de un estudiante específico"""
        return cls.listar(
            filtros={'estudiante_id': estudiante_id},
            limite=limite,
            offset=offset,
            ordenar_por='fecha_pago',
            orden='DESC'
        )
    
    @classmethod
    def listar_por_programa(cls, programa_id: int,
                           limite: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Listar transacciones de un programa específico"""
        return cls.listar(
            filtros={'programa_id': programa_id},
            limite=limite,
            offset=offset,
            ordenar_por='fecha_pago',
            orden='DESC'
        )
    
    @classmethod
    def listar_por_fecha(cls, fecha_inicio: str, fecha_fin: str,
                        limite: int = 1000, offset: int = 0) -> Dict[str, Any]:
        """Listar transacciones en un rango de fechas"""
        try:
            query = f"""
                SELECT 
                    t.*,
                    CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) as estudiante_nombre_completo,
                    CONCAT(e.ci_numero, ' ', e.ci_expedicion) as estudiante_ci,
                    p.nombre as programa_nombre,
                    p.codigo as programa_codigo
                FROM {cls.TABLE_NAME} t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                WHERE t.fecha_pago BETWEEN %s AND %s
                ORDER BY t.fecha_pago DESC
                LIMIT %s OFFSET %s
            """
            
            count_query = f"""
                SELECT COUNT(*) as total
                FROM {cls.TABLE_NAME} t
                WHERE t.fecha_pago BETWEEN %s AND %s
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                
                # Obtener total
                cursor.execute(count_query, (fecha_inicio, fecha_fin))
                total_result = cursor.fetchone()
                total = total_result['total'] if total_result else 0
                
                # Obtener datos paginados
                cursor.execute(query, (fecha_inicio, fecha_fin, limite, offset))
                results = cursor.fetchall()
                
                transacciones = [dict(row) for row in results]
                
                return {
                    'success': True,
                    'data': transacciones,
                    'total': total,
                    'fecha_inicio': fecha_inicio,
                    'fecha_fin': fecha_fin
                }
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error listando transacciones por fecha: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def obtener_resumen_por_estudiante(cls, estudiante_id: int) -> Dict[str, Any]:
        """
        Obtener resumen de pagos de un estudiante
        
        Returns:
            Dict con total pagado, número de transacciones, etc.
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_transacciones,
                    COALESCE(SUM(monto_final), 0) as total_pagado,
                    COUNT(CASE WHEN estado = 'CONFIRMADO' THEN 1 END) as confirmadas,
                    COUNT(CASE WHEN estado = 'PENDIENTE' THEN 1 END) as pendientes,
                    COALESCE(SUM(CASE WHEN estado = 'CONFIRMADO' THEN monto_final ELSE 0 END), 0) as total_confirmado,
                    MIN(fecha_pago) as primera_transaccion,
                    MAX(fecha_pago) as ultima_transaccion
                FROM transacciones
                WHERE estudiante_id = %s
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (estudiante_id,))
                result = cursor.fetchone()
                
                return {'success': True, 'data': dict(result) if result else {}}
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo resumen: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def obtener_por_inscripcion(cls, estudiante_id: int, programa_id: int) -> Dict[str, Any]:
        """
        Obtener transacciones relacionadas a una inscripción específica
        usando estudiante_id y programa_id
    
        Args:
            estudiante_id: ID del estudiante
            programa_id: ID del programa
    
        Returns:
            Dict con resultado y lista de transacciones
        """
        try:
            query = """
                SELECT 
                    t.id,
                    t.numero_transaccion,
                    t.fecha_pago,
                    t.monto_total,
                    t.descuento_total,
                    t.monto_final,
                    t.forma_pago,
                    t.estado,
                    t.fecha_registro,
                    t.numero_comprobante,
                    t.observaciones,
                    CONCAT(e.apellido_paterno, ' ', e.apellido_materno, ' ', COALESCE(e.nombres, '')) as estudiante_nombre,
                    CONCAT(e.ci_numero, '-', e.ci_expedicion) as estudiante_ci,  -- CORREGIDO: ci_expedicion en lugar de ci_expedicion
                    p.nombre as programa_nombre,
                    p.codigo as programa_codigo
                FROM transacciones t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                WHERE t.estudiante_id = %s AND t.programa_id = %s
                ORDER BY t.numero_transaccion DESC, t.fecha_pago DESC, t.fecha_registro DESC
            """
    
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
    
                from psycopg2.extras import RealDictCursor
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (estudiante_id, programa_id))
                results = cursor.fetchall()
    
                transacciones = [dict(row) for row in results]
    
                # Calcular totales
                total_pagado = sum(t.get('monto_final', 0) for t in transacciones 
                                    if t.get('estado') in ['CONFIRMADO', 'REGISTRADO'])
    
                logger.info(f"✅ Transacciones para estudiante {estudiante_id}, programa {programa_id}: {len(transacciones)} encontradas")
    
                return {
                    'success': True,
                    'data': transacciones,
                    'total_transacciones': len(transacciones),
                    'total_pagado': total_pagado
                }
    
            except Exception as e:
                logger.error(f"❌ Error obteniendo transacciones para inscripción: {e}")
                return {'success': False, 'error': str(e), 'data': []}
    
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
    
        except Exception as e:
            logger.error(f"❌ Error en método obtener_por_inscripcion: {e}")
            return {'success': False, 'error': str(e), 'data': []}
    
    @classmethod
    def anular(cls, id_transaccion: int, motivo: str) -> Dict[str, Any]:
        """
        Anular una transacción (cambiar estado a ANULADO)

        Args:
            id_transaccion: ID de la transacción
            motivo: Motivo de la anulación

        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que la transacción existe y no está ya anulada
            transaccion = cls.obtener_por_id(id_transaccion)
            if not transaccion.get('success'):
                return transaccion

            estado_actual = transaccion['data']['estado']
            if estado_actual == EstadoTransaccion.ANULADO.value:
                return {'success': False, 'error': 'La transacción ya está anulada'}

            if estado_actual == EstadoTransaccion.CONFIRMADO.value:
                return {'success': False, 'error': 'No se puede anular una transacción confirmada'}

            # Preparar observaciones con motivo
            observaciones_actuales = transaccion['data']['observaciones'] or ''
            nueva_observacion = f"ANULADO: {motivo}"
            if observaciones_actuales:
                nueva_observacion = f"{observaciones_actuales}\n{nueva_observacion}"

            # Cambiar estado
            return cls.cambiar_estado(
                id_transaccion, 
                EstadoTransaccion.ANULADO.value,
                nueva_observacion
            )

        except Exception as e:
            logger.error(f"❌ Error anulando transacción {id_transaccion}: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def confirmar(cls, id_transaccion: int) -> Dict[str, Any]:
        """
        Confirmar una transacción (cambiar estado a CONFIRMADO)
        
        Args:
            id_transaccion: ID de la transacción
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que la transacción existe
            transaccion = cls.obtener_por_id(id_transaccion)
            if not transaccion.get('success'):
                return transaccion
            
            estado_actual = transaccion['data']['estado']
            if estado_actual == EstadoTransaccion.ANULADO.value:
                return {'success': False, 'error': 'No se puede confirmar una transacción anulada'}
            
            if estado_actual == EstadoTransaccion.CONFIRMADO.value:
                return {'success': False, 'error': 'La transacción ya está confirmada'}
            
            # Cambiar estado
            return cls.cambiar_estado(id_transaccion, EstadoTransaccion.CONFIRMADO.value)
            
        except Exception as e:
            logger.error(f"❌ Error confirmando transacción {id_transaccion}: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def eliminar(cls, id_transaccion: int) -> Dict[str, Any]:
        """
        Eliminar una transacción (solo si está en estado REGISTRADO)
        
        Args:
            id_transaccion: ID de la transacción
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que la transacción existe y se puede eliminar
            transaccion = cls.obtener_por_id(id_transaccion)
            if not transaccion.get('success'):
                return transaccion
            
            estado_actual = transaccion['data']['estado']
            if estado_actual not in [EstadoTransaccion.REGISTRADO.value, EstadoTransaccion.PENDIENTE.value]:
                return {
                    'success': False, 
                    'error': f'No se puede eliminar una transacción en estado {estado_actual}'
                }
            
            query = "DELETE FROM transacciones WHERE id = %s RETURNING id"
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor()
                cursor.execute(query, (id_transaccion,))
                
                result = cursor.fetchone()
                if not result:
                    connection.rollback()
                    return {'success': False, 'error': 'No se pudo eliminar la transacción'}
                
                connection.commit()
                logger.info(f"✅ Transacción {id_transaccion} eliminada")
                
                return {
                    'success': True,
                    'id': id_transaccion,
                    'message': 'Transacción eliminada exitosamente'
                }
                
            except Exception as e:
                if connection:
                    connection.rollback()
                logger.error(f"❌ Error eliminando transacción {id_transaccion}: {e}")
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
    def obtener_estadisticas(cls, año: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtener estadísticas de transacciones
        
        Args:
            año: Año para filtrar (opcional, por defecto año actual)
            
        Returns:
            Dict con estadísticas
        """
        try:
            if not año:
                año = datetime.now().year
            
            query = f"""
                SELECT 
                    COUNT(*) as total_transacciones,
                    COALESCE(SUM(monto_final), 0) as monto_total,
                    COALESCE(AVG(monto_final), 0) as monto_promedio,
                    COUNT(DISTINCT estudiante_id) as estudiantes_con_pagos,
                    
                    -- Por estado
                    COUNT(CASE WHEN estado = 'REGISTRADO' THEN 1 END) as registradas,
                    COUNT(CASE WHEN estado = 'CONFIRMADO' THEN 1 END) as confirmadas,
                    COUNT(CASE WHEN estado = 'ANULADO' THEN 1 END) as anuladas,
                    
                    -- Por forma de pago
                    COUNT(CASE WHEN forma_pago = 'EFECTIVO' THEN 1 END) as pagos_efectivo,
                    COUNT(CASE WHEN forma_pago = 'TRANSFERENCIA' THEN 1 END) as pagos_transferencia,
                    COUNT(CASE WHEN forma_pago = 'TARJETA' THEN 1 END) as pagos_tarjeta,
                    
                    -- Montos por estado
                    COALESCE(SUM(CASE WHEN estado = 'CONFIRMADO' THEN monto_final ELSE 0 END), 0) as monto_confirmado,
                    COALESCE(SUM(CASE WHEN estado = 'REGISTRADO' THEN monto_final ELSE 0 END), 0) as monto_registrado,
                    
                    -- Montos por forma de pago
                    COALESCE(SUM(CASE WHEN forma_pago = 'EFECTIVO' THEN monto_final ELSE 0 END), 0) as monto_efectivo,
                    COALESCE(SUM(CASE WHEN forma_pago = 'TRANSFERENCIA' THEN monto_final ELSE 0 END), 0) as monto_transferencia,
                    COALESCE(SUM(CASE WHEN forma_pago = 'TARJETA' THEN monto_final ELSE 0 END), 0) as monto_tarjeta,
                    
                    -- Mes con más pagos
                    (
                        SELECT EXTRACT(MONTH FROM fecha_pago)
                        FROM transacciones
                        WHERE EXTRACT(YEAR FROM fecha_pago) = %s
                        GROUP BY EXTRACT(MONTH FROM fecha_pago)
                        ORDER BY COUNT(*) DESC
                        LIMIT 1
                    ) as mes_mas_pagos
                    
                FROM transacciones
                WHERE EXTRACT(YEAR FROM fecha_pago) = %s
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (año, año))
                result = cursor.fetchone()
                
                # Obtener distribución mensual
                monthly_query = """
                    SELECT 
                        EXTRACT(MONTH FROM fecha_pago) as mes,
                        COUNT(*) as cantidad,
                        COALESCE(SUM(monto_final), 0) as monto
                    FROM transacciones
                    WHERE EXTRACT(YEAR FROM fecha_pago) = %s
                    GROUP BY EXTRACT(MONTH FROM fecha_pago)
                    ORDER BY mes
                """
                
                cursor.execute(monthly_query, (año,))
                monthly_results = cursor.fetchall()
                
                distribucion_mensual = []
                for row in monthly_results:
                    distribucion_mensual.append({
                        'mes': int(row['mes']),
                        'cantidad': row['cantidad'],
                        'monto': float(row['monto'])
                    })
                
                return {
                    'success': True,
                    'data': dict(result) if result else {},
                    'distribucion_mensual': distribucion_mensual,
                    'año': año
                }
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {'success': False, 'error': str(e)}
    
    @classmethod
    def validar_datos(cls, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar datos de transacción antes de guardar
        
        Args:
            datos: Diccionario con datos a validar
            
        Returns:
            Dict con resultado de validación y errores
        """
        errores = {}
        
        # Validar estudiante_id
        if 'estudiante_id' not in datos or not datos['estudiante_id']:
            errores['estudiante_id'] = 'El estudiante es obligatorio'
        
        # Validar programa_id (opcional)
        if 'programa_id' in datos and datos['programa_id']:
            # Verificar que el programa existe (se haría en el servicio)
            pass
        
        # Validar fecha_pago
        if 'fecha_pago' not in datos or not datos['fecha_pago']:
            errores['fecha_pago'] = 'La fecha de pago es obligatoria'
        else:
            try:
                if isinstance(datos['fecha_pago'], str):
                    datetime.strptime(datos['fecha_pago'], '%Y-%m-%d')
            except ValueError:
                errores['fecha_pago'] = 'Formato de fecha inválido (use YYYY-MM-DD)'
        
        # Validar montos
        try:
            monto_total = float(datos.get('monto_total', 0))
            descuento_total = float(datos.get('descuento_total', 0))
            monto_final = float(datos.get('monto_final', 0))
            
            if monto_total < 0:
                errores['monto_total'] = 'El monto total no puede ser negativo'
            
            if descuento_total < 0:
                errores['descuento_total'] = 'El descuento no puede ser negativo'
            
            if descuento_total > monto_total:
                errores['descuento_total'] = 'El descuento no puede ser mayor al monto total'
            
            if monto_final < 0:
                errores['monto_final'] = 'El monto final no puede ser negativo'
            
            if abs(monto_final - (monto_total - descuento_total)) > 0.01:
                errores['monto_final'] = 'El monto final debe ser igual a monto total menos descuento'
                
        except (ValueError, TypeError):
            errores['montos'] = 'Los montos deben ser números válidos'
        
        # Validar forma_pago
        formas_validas = [f.value for f in FormaPago]
        if 'forma_pago' not in datos or not datos['forma_pago']:
            errores['forma_pago'] = 'La forma de pago es obligatoria'
        elif datos['forma_pago'] not in formas_validas:
            errores['forma_pago'] = f'Forma de pago inválida. Debe ser una de: {", ".join(formas_validas)}'
        
        # Validaciones específicas por forma de pago
        if datos.get('forma_pago') == FormaPago.TRANSFERENCIA.value:
            if not datos.get('numero_comprobante'):
                errores['numero_comprobante'] = 'El número de comprobante es obligatorio para transferencias'
            if not datos.get('banco_origen'):
                errores['banco_origen'] = 'El banco de origen es obligatorio para transferencias'
        
        elif datos.get('forma_pago') == FormaPago.DEPOSITO.value:
            if not datos.get('numero_comprobante'):
                errores['numero_comprobante'] = 'El número de comprobante es obligatorio para depósitos'
        
        # Validar estado si se proporciona
        if 'estado' in datos and datos['estado']:
            estados_validos = [e.value for e in EstadoTransaccion]
            if datos['estado'] not in estados_validos:
                errores['estado'] = f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'
        
        if errores:
            return {
                'success': False,
                'errors': errores,
                'message': 'Errores de validación'
            }
        
        return {'success': True, 'data': datos}
    
    @classmethod
    def existe_numero_comprobante(cls, numero_comprobante: str, 
                                    excluir_id: Optional[int] = None) -> bool:
        """
        Verificar si un número de comprobante ya existe

        Args:
            numero_comprobante: Número de comprobante a verificar
            excluir_id: ID de transacción a excluir (para actualizaciones)

        Returns:
            True si existe, False si no
        """
        try:
            query = "SELECT id FROM transacciones WHERE numero_comprobante = %s"
            params: List[Union[str, int]] = [numero_comprobante]

            if excluir_id is not None:
                query += " AND id != %s"
                params.append(excluir_id)

            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return False

                cursor = connection.cursor()
                cursor.execute(query, params)
                result = cursor.fetchone()

                return result is not None

            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)

        except Exception as e:
            logger.error(f"❌ Error verificando número de comprobante: {e}")
            return False
    
    @classmethod
    def buscar(cls, termino: str, limite: int = 20) -> Dict[str, Any]:
        """
        Buscar transacciones por término (número, estudiante, etc.)
        
        Args:
            termino: Término de búsqueda
            limite: Límite de resultados
            
        Returns:
            Dict con resultados
        """
        try:
            query = f"""
                SELECT 
                    t.id,
                    t.numero_transaccion,
                    t.fecha_pago,
                    t.monto_final,
                    t.estado,
                    t.forma_pago,
                    CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) as estudiante_nombre_completo,
                    CONCAT(e.ci_numero, ' ', e.ci_expedicion) as estudiante_ci,
                    p.nombre as programa_nombre
                FROM {cls.TABLE_NAME} t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                WHERE 
                    t.numero_transaccion ILIKE %s
                    OR e.nombres ILIKE %s
                    OR e.apellido_paterno ILIKE %s
                    OR e.apellido_materno ILIKE %s
                    OR CONCAT(e.ci_numero, ' ', e.ci_expedicion) ILIKE %s
                    OR CAST(t.id AS TEXT) ILIKE %s
                ORDER BY t.fecha_pago DESC
                LIMIT %s
            """
            
            search_term = f"%{termino}%"
            params = [search_term, search_term, search_term, search_term, search_term, search_term, limite]
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return {
                    'success': True,
                    'data': [dict(row) for row in results],
                    'total': len(results)
                }
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error buscando transacciones: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def obtener_pagos_del_dia(cls) -> Dict[str, Any]:
        """
        Obtener resumen de pagos del día actual
        
        Returns:
            Dict con resumen
        """
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            query = """
                SELECT 
                    COUNT(*) as cantidad,
                    COALESCE(SUM(monto_final), 0) as monto_total,
                    COUNT(CASE WHEN estado = 'CONFIRMADO' THEN 1 END) as confirmados,
                    COALESCE(SUM(CASE WHEN estado = 'CONFIRMADO' THEN monto_final ELSE 0 END), 0) as monto_confirmado,
                    COUNT(CASE WHEN forma_pago = 'EFECTIVO' THEN 1 END) as efectivo,
                    COALESCE(SUM(CASE WHEN forma_pago = 'EFECTIVO' THEN monto_final ELSE 0 END), 0) as monto_efectivo,
                    COUNT(CASE WHEN forma_pago = 'TRANSFERENCIA' THEN 1 END) as transferencia,
                    COALESCE(SUM(CASE WHEN forma_pago = 'TRANSFERENCIA' THEN monto_final ELSE 0 END), 0) as monto_transferencia,
                    COUNT(CASE WHEN forma_pago = 'TARJETA' THEN 1 END) as tarjeta,
                    COALESCE(SUM(CASE WHEN forma_pago = 'TARJETA' THEN monto_final ELSE 0 END), 0) as monto_tarjeta
                FROM transacciones
                WHERE fecha_pago = %s
            """
            
            connection = None
            cursor = None
            try:
                connection = cls._get_connection()
                if not connection:
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                cursor = connection.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, (today,))
                result = cursor.fetchone()
                
                # Obtener lista de pagos del día
                detalle_query = """
                    SELECT 
                        t.numero_transaccion,
                        t.monto_final,
                        t.estado,
                        t.forma_pago,
                        CONCAT(e.nombres, ' ', e.apellido_paterno, ' ', COALESCE(e.apellido_materno, '')) as estudiante
                    FROM transacciones t
                    LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                    WHERE t.fecha_pago = %s
                    ORDER BY t.fecha_registro DESC
                """
                
                cursor.execute(detalle_query, (today,))
                detalles = cursor.fetchall()
                
                return {
                    'success': True,
                    'fecha': today,
                    'resumen': dict(result) if result else {},
                    'detalles': [dict(row) for row in detalles]
                }
                
            finally:
                if cursor:
                    cursor.close()
                if connection:
                    cls._return_connection(connection)
                    
        except Exception as e:
            logger.error(f"❌ Error obteniendo pagos del día: {e}")
            return {'success': False, 'error': str(e)}

    # Funciones de utilidad para manejo de transacciones complejas
    @classmethod
    def crear_transaccion_con_detalles(cls, datos_transaccion: Dict[str, Any], 
                                       items_detalle: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Crear una transacción con sus detalles (función de ejemplo para transacciones complejas)
        Esta función demuestra cómo manejar múltiples operaciones en una transacción

        Args:
            datos_transaccion: Datos de la transacción principal
            items_detalle: Lista de items de detalle (ej: conceptos de pago)

        Returns:
            Dict con resultado
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection_safe()
            if not connection:
                return {'success': False, 'error': 'No se pudo conectar a la base de datos'}

            cursor = connection.cursor()

            # 1. Insertar transacción principal
            transaccion_columns = TransaccionModel.COLUMNS.copy()
            transaccion_values = []
            for col in transaccion_columns:
                if col in datos_transaccion:
                    transaccion_values.append(datos_transaccion[col])
                else:
                    transaccion_values.append(None)

            placeholders = ['%s'] * len(transaccion_columns)
            transaccion_query = f"""
                INSERT INTO transacciones ({', '.join(transaccion_columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """

            cursor.execute(transaccion_query, transaccion_values)
            result = cursor.fetchone()
            if not result:
                raise Exception("No se pudo obtener el ID de la transacción")
            transaccion_id = result[0]

            # 2. Insertar detalles (ejemplo con tabla de conceptos)
            if items_detalle:
                for item in items_detalle:
                    item['transaccion_id'] = transaccion_id
                    detalle_columns = list(item.keys())
                    detalle_values = list(item.values())
                    detalle_placeholders = ['%s'] * len(detalle_columns)

                    detalle_query = f"""
                        INSERT INTO transaccion_conceptos ({', '.join(detalle_columns)})
                        VALUES ({', '.join(detalle_placeholders)})
                    """

                    cursor.execute(detalle_query, detalle_values)

            # 3. Commit si todo está bien
            connection.commit()
            logger.info(f"✅ Transacción compleja creada con ID: {transaccion_id}")

            return {
                'success': True,
                'id': transaccion_id,
                'message': 'Transacción creada exitosamente con sus detalles'
            }

        except Exception as e:
            if connection:
                connection.rollback()
                logger.warning("↩️ Rollback ejecutado por error en transacción compleja")
            logger.error(f"❌ Error en transacción compleja: {e}")
            return {'success': False, 'error': str(e)}

        finally:
            if cursor:
                cursor.close()
            if connection:
                Database.return_connection(connection)
    
    @classmethod
    def crear_transaccion_inicial_inscripcion(cls, inscripcion_id: int, usuario_id: int = 2) -> Dict[str, Any]:
        """
        Crear una transacción inicial para una inscripción (valores por defecto)
    
        Args:
            inscripcion_id: ID de la inscripción
            usuario_id: ID del usuario que registra
    
        Returns:
            Dict con resultado y datos de la transacción creada
        """
        try:
            logger.info(f"📝 Creando transacción inicial para inscripción {inscripcion_id}")
    
            conn = None
            cursor = None
            try:
                conn = cls._get_connection()
                if not conn:
                    logger.error("❌ No se pudo obtener conexión a la base de datos")
                    return {'success': False, 'error': 'No se pudo conectar a la base de datos'}
                
                # Importar aquí para evitar problemas
                from psycopg2.extras import RealDictCursor
                
                # Crear cursor con DictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
    
                # Consulta corregida - usando nombres correctos de columnas
                query = """
                    SELECT 
                        i.id as inscripcion_id,
                        i.estudiante_id,
                        i.programa_id,
                        i.valor_final,
                        i.estado as estado_inscripcion,
                        e.nombres,
                        e.apellido_paterno,
                        e.apellido_materno,
                        CONCAT(e.ci_numero, ' ', e.ci_expedicion) as documento_identidad,
                        p.nombre as programa_nombre,
                        p.codigo as programa_codigo,
                        p.duracion_meses,
                        p.costo_total as programa_costo_total
                    FROM inscripciones i
                    LEFT JOIN estudiantes e ON i.estudiante_id = e.id
                    LEFT JOIN programas p ON i.programa_id = p.id
                    WHERE i.id = %s
                """
    
                logger.debug(f"Ejecutando query para inscripción {inscripcion_id}")
                cursor.execute(query, (inscripcion_id,))
                row = cursor.fetchone()
    
                if not row:
                    logger.error(f"❌ No se encontró la inscripción {inscripcion_id}")
                    return {'success': False, 'error': f'No se encontró la inscripción {inscripcion_id}'}
    
                # Convertir a diccionario
                datos = dict(row)
                logger.info(f"✅ Datos obtenidos de inscripción {inscripcion_id}:")
                logger.info(f"   - Estudiante ID: {datos.get('estudiante_id')}")
                logger.info(f"   - Programa ID: {datos.get('programa_id')}")
                logger.info(f"   - Estudiante: {datos.get('nombres')} {datos.get('apellido_paterno')}")
                logger.info(f"   - Documento: {datos.get('documento_identidad')}")
                logger.info(f"   - Programa: {datos.get('programa_nombre')}")
                logger.info(f"   - Duración (meses): {datos.get('duracion_meses')}")
                logger.info(f"   - Valor final: {datos.get('valor_final')}")
    
                # Verificar que tenemos los IDs necesarios
                estudiante_id = datos.get('estudiante_id')
                programa_id = datos.get('programa_id')
    
                if not estudiante_id:
                    logger.error(f"❌ La inscripción {inscripcion_id} no tiene estudiante_id")
                    return {'success': False, 'error': 'La inscripción no tiene un estudiante asociado'}
    
                if not programa_id:
                    logger.error(f"❌ La inscripción {inscripcion_id} no tiene programa_id")
                    return {'success': False, 'error': 'La inscripción no tiene un programa asociado'}
    
                # Construir nombre del estudiante
                nombres = datos.get('nombres', '')
                apellido_paterno = datos.get('apellido_paterno', '')
                apellido_materno = datos.get('apellido_materno', '')
                nombre_estudiante = f"{nombres} {apellido_paterno} {apellido_materno}".strip()
                if not nombre_estudiante:
                    nombre_estudiante = f"Estudiante ID: {estudiante_id}"
    
                # Construir nombre del programa
                programa_nombre = datos.get('programa_nombre', '')
                programa_codigo = datos.get('programa_codigo', '')
                nombre_programa = f"{programa_codigo} - {programa_nombre}".strip()
                if not nombre_programa or nombre_programa == "-":
                    nombre_programa = f"Programa ID: {programa_id}"
    
                fecha_actual = datetime.now().strftime('%Y-%m-%d')
    
                observaciones = (
                    f"✅ TRANSACCIÓN INICIAL\n"
                    f"📋 Inscripción #{inscripcion_id}\n"
                    f"👤 Estudiante: {nombre_estudiante}\n"
                    f"📚 Programa: {nombre_programa}\n"
                    f"💰 Monto total: {datos.get('valor_final', 0):.2f} Bs."
                )
    
                # Preparar datos para nueva transacción
                datos_nueva = {
                    'numero_transaccion': None,
                    'estudiante_id': estudiante_id,
                    'programa_id': programa_id,
                    'fecha_pago': fecha_actual,
                    'monto_total': 0.0,
                    'descuento_total': 0.0,
                    'monto_final': 0.0,
                    'forma_pago': 'EFECTIVO',
                    'estado': 'REGISTRADO',
                    'numero_comprobante': None,
                    'banco_origen': None,
                    'cuenta_origen': None,
                    'observaciones': observaciones,
                    'registrado_por': usuario_id
                }
    
                logger.info(f"📦 Creando transacción con:")
                logger.info(f"   - estudiante_id: {estudiante_id}")
                logger.info(f"   - programa_id: {programa_id}")
                logger.info(f"   - fecha_pago: {fecha_actual}")
    
                # Crear la transacción usando el método crear existente
                resultado_creacion = cls.crear(datos_nueva)
    
                if resultado_creacion.get('success'):
                    logger.info(f"✅ Transacción creada exitosamente con ID: {resultado_creacion.get('id')}")
                    if resultado_creacion.get('numero_transaccion'):
                        logger.info(f"   Número de transacción: {resultado_creacion.get('numero_transaccion')}")
                else:
                    logger.error(f"❌ Error en cls.crear: {resultado_creacion.get('error')}")
    
                return resultado_creacion
    
            except Exception as e:
                logger.error(f"❌ Error en consulta: {e}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': str(e)}
    
            finally:
                if cursor:
                    cursor.close()
                    logger.debug("Cursor cerrado")
                if conn:
                    cls._return_connection(conn)
                    logger.debug("Conexión devuelta al pool")
    
        except Exception as e:
            logger.error(f"❌ Error general: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}