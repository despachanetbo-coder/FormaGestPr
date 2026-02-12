# model/programa_model.py
import logging
from typing import Optional, Dict, Any, List
from config.database import Database
from .base_model import BaseModel

logger = logging.getLogger(__name__)

class ProgramaModel(BaseModel):
    """Modelo para programas académicos que hereda de BaseModel"""
    
    @staticmethod
    def crear_programa(datos: dict) -> dict:
        """Crear un nuevo programa académico usando la función fn_insertar_programa"""
        try:
            logger.debug(f"DEBUG - ProgramaModel.crear_programa usando función")
            
            # Llamar a la función de PostgreSQL usando callproc
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo obtener conexión a la base de datos'
                }
            
            cursor = connection.cursor()
            
            # Preparar parámetros para la función (eliminados campos de promoción)
            params = (
                datos.get('codigo'),
                datos.get('nombre'),
                datos.get('duracion_meses'),
                datos.get('horas_totales'),
                datos.get('costo_total'),
                datos.get('costo_mensualidad', 0),
                datos.get('descripcion', ''),
                datos.get('costo_matricula', 0),
                datos.get('costo_inscripcion', 0),
                datos.get('numero_cuotas', 1),
                datos.get('cupos_maximos'),
                datos.get('cupos_inscritos', 0),
                datos.get('estado', 'PLANIFICADO'),
                datos.get('fecha_inicio'),
                datos.get('fecha_fin'),
                datos.get('docente_coordinador_id')
                # NOTA: Se eliminaron los parámetros de promoción
            )
            
            # Ejecutar función usando callproc
            cursor.callproc('fn_insertar_programa', params)
            result = cursor.fetchone()
            
            connection.commit()
            cursor.close()
            Database.return_connection(connection)
            
            if result:
                nuevo_id = result[0]
                mensaje = result[1]
                exito = result[2]
                
                if exito:
                    logger.info(f"✅ Programa creado exitosamente - ID: {nuevo_id}")
                    
                    # Obtener el programa completo para devolverlo
                    programa_completo = ProgramaModel.obtener_programa(nuevo_id)
                    if programa_completo.get('success'):
                        return {
                            'success': True,
                            'data': programa_completo['data'],
                            'message': mensaje
                        }
                    else:
                        # Si no podemos obtener el programa completo, devolver al menos los datos básicos
                        return {
                            'success': True,
                            'data': {
                                'id': nuevo_id,
                                'codigo': datos.get('codigo'),
                                'nombre': datos.get('nombre'),
                                'mensaje': mensaje
                            },
                            'message': mensaje
                        }
                else:
                    logger.error(f"❌ Error en función PostgreSQL: {mensaje}")
                    return {
                        'success': False,
                        'data': None,
                        'message': mensaje
                    }
            else:
                logger.error("❌ No se pudo crear el programa (resultado vacío)")
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo crear el programa'
                }
                
        except Exception as e:
            logger.error(f"❌ Error al crear programa: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'data': None,
                'message': f'Error al crear programa: {str(e)}'
            }
    
    @staticmethod
    def actualizar_programa(programa_id: int, datos: dict) -> dict:
        """Actualizar un programa académico usando la función fn_actualizar_programa"""
        try:
            logger.debug(f"DEBUG - ProgramaModel.actualizar_programa para ID: {programa_id}")
            
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo obtener conexión a la base de datos'
                }
            
            cursor = connection.cursor()
            
            # Preparar parámetros (eliminados campos de promoción)
            params = (
                programa_id,
                datos.get('codigo'),
                datos.get('nombre'),
                datos.get('duracion_meses'),
                datos.get('horas_totales'),
                datos.get('costo_total'),
                datos.get('costo_mensualidad', 0),
                datos.get('descripcion', ''),
                datos.get('costo_matricula'),
                datos.get('costo_inscripcion'),
                datos.get('numero_cuotas'),
                datos.get('cupos_maximos'),
                datos.get('cupos_inscritos'),
                datos.get('estado'),
                datos.get('fecha_inicio'),
                datos.get('fecha_fin'),
                datos.get('docente_coordinador_id')
                # NOTA: Se eliminaron los parámetros de promoción
            )
            
            # Ejecutar función
            cursor.callproc('fn_actualizar_programa', params)
            result = cursor.fetchone()
            
            connection.commit()
            cursor.close()
            Database.return_connection(connection)
            
            if result:
                filas_afectadas = result[0]
                mensaje = result[1]
                exito = result[2]
                
                if exito:
                    logger.info(f"✅ Programa actualizado - Filas afectadas: {filas_afectadas}")
                    
                    # Obtener el programa actualizado
                    programa_actualizado = ProgramaModel.obtener_programa(programa_id)
                    if programa_actualizado.get('success'):
                        return {
                            'success': True,
                            'data': programa_actualizado['data'],
                            'message': mensaje
                        }
                    else:
                        return {
                            'success': True,
                            'data': None,
                            'message': mensaje
                        }
                else:
                    logger.error(f"❌ Error actualizando programa: {mensaje}")
                    return {
                        'success': False,
                        'data': None,
                        'message': mensaje
                    }
            else:
                return {
                    'success': False,
                    'data': None,
                    'message': 'Error al actualizar programa'
                }
                
        except Exception as e:
            logger.error(f"❌ Error al actualizar programa: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error al actualizar programa: {str(e)}'
            }
    
    @staticmethod
    def eliminar_programa(programa_id: int) -> dict:
        """Eliminar (cancelar) un programa académico usando la función fn_eliminar_programa"""
        try:
            logger.debug(f"DEBUG - ProgramaModel.eliminar_programa para ID: {programa_id}")
            
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo obtener conexión a la base de datos'
                }
            
            cursor = connection.cursor()
            
            # Ejecutar función
            cursor.callproc('fn_eliminar_programa', (programa_id,))
            result = cursor.fetchone()
            
            connection.commit()
            cursor.close()
            Database.return_connection(connection)
            
            if result:
                filas_afectadas = result[0]
                mensaje = result[1]
                exito = result[2]
                
                return {
                    'success': exito,
                    'data': None,
                    'message': mensaje
                }
            else:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo eliminar el programa'
                }
                
        except Exception as e:
            logger.error(f"❌ Error al eliminar programa: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error al eliminar programa: {str(e)}'
            }
    
    @staticmethod
    def obtener_programa(programa_id: int) -> dict:
        """Obtener un programa por ID usando la función fn_obtener_programa_por_id"""
        try:
            logger.debug(f"DEBUG - ProgramaModel.obtener_programa para ID: {programa_id}")
            
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo obtener conexión a la base de datos'
                }
            
            cursor = connection.cursor()
            
            # Ejecutar función
            cursor.callproc('fn_obtener_programa_por_id', (programa_id,))
            result = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if result:
                # Mapear resultado a diccionario (eliminados campos de promoción)
                programa = {
                    'id': result[0],
                    'codigo': result[1],
                    'nombre': result[2],
                    'descripcion': result[3],
                    'duracion_meses': result[4],
                    'horas_totales': result[5],
                    'costo_total': result[6],
                    'costo_matricula': result[7],
                    'costo_inscripcion': result[8],
                    'costo_mensualidad': result[9],
                    'numero_cuotas': result[10],
                    'cupos_maximos': result[11],
                    'cupos_inscritos': result[12],
                    'estado': result[13],
                    'fecha_inicio': result[14],
                    'fecha_fin': result[15],
                    'docente_coordinador_id': result[16]
                    # NOTA: Se eliminaron los campos de promoción del mapeo
                }
                
                logger.debug(f"✅ Programa encontrado: {programa['codigo']}")
                return {
                    'success': True,
                    'data': programa,
                    'message': 'Programa obtenido exitosamente'
                }
            else:
                logger.warning(f"⚠️ Programa no encontrado: ID {programa_id}")
                return {
                    'success': False,
                    'data': None,
                    'message': 'Programa no encontrado'
                }
                
        except Exception as e:
            logger.error(f"❌ Error al obtener programa: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error al obtener programa: {str(e)}'
            }
    
    @staticmethod
    def buscar_programas(codigo: Optional[str] = None,
                        nombre: Optional[str] = None,
                        estado: Optional[str] = None,
                        docente_coordinador_id: Optional[int] = None,
                        fecha_inicio_desde: Optional[str] = None,
                        fecha_inicio_hasta: Optional[str] = None,
                        limit: int = 20,
                        offset: int = 0) -> List[Dict]:
        """Buscar programas usando la función fn_buscar_programas"""
        try:
            logger.debug(f"DEBUG - ProgramaModel.buscar_programas")
            
            connection = Database.get_connection()
            if not connection:
                return []
            
            cursor = connection.cursor()
            
            # Preparar parámetros
            params = (
                codigo,
                nombre,
                estado,
                docente_coordinador_id,
                fecha_inicio_desde,
                fecha_inicio_hasta,
                limit,
                offset
            )
            
            # Ejecutar función
            cursor.callproc('fn_buscar_programas', params)
            results = cursor.fetchall()
            
            cursor.close()
            Database.return_connection(connection)
            
            if results:
                programas = []
                for row in results:
                    programa = {
                        'id': row[0],
                        'codigo': row[1],
                        'nombre': row[2],
                        'descripcion': row[3],
                        'duracion_meses': row[4],
                        'horas_totales': row[5],
                        'costo_total': row[6],
                        'costo_matricula': row[7],
                        'costo_inscripcion': row[8],
                        'costo_mensualidad': row[9],
                        'numero_cuotas': row[10],
                        'cupos_maximos': row[11],
                        'cupos_inscritos': row[12],
                        'estado': row[13],
                        'fecha_inicio': row[14],
                        'fecha_fin': row[15],
                        'docente_coordinador_id': row[16]
                        # NOTA: Se eliminaron los campos de promoción del mapeo
                    }
                    programas.append(programa)
                
                logger.info(f"✅ {len(programas)} programas encontrados")
                return programas
                
            else:
                return []
                
        except Exception as e:
            logger.error(f"❌ Error buscando programas: {e}")
            return []
    
    @staticmethod
    def buscar_programas_con_paginacion(codigo: Optional[str] = None,
                                        nombre: Optional[str] = None,
                                        estado: Optional[str] = None,
                                        docente_coordinador_id: Optional[int] = None,
                                        fecha_inicio_desde: Optional[str] = None,
                                        fecha_inicio_hasta: Optional[str] = None,
                                        limit: int = 20,
                                        offset: int = 0) -> Dict:
        """Versión con metadatos de paginación (para compatibilidad)"""
        try:
            # Obtener lista de programas
            programas = ProgramaModel.buscar_programas(
                codigo=codigo,
                nombre=nombre,
                estado=estado,
                docente_coordinador_id=docente_coordinador_id,
                fecha_inicio_desde=fecha_inicio_desde,
                fecha_inicio_hasta=fecha_inicio_hasta,
                limit=limit,
                offset=offset
            )

            # Obtener total para paginación
            total = ProgramaModel.contar_programas(
                codigo=codigo,
                nombre=nombre,
                estado=estado,
                docente_coordinador_id=docente_coordinador_id,
                fecha_inicio_desde=fecha_inicio_desde,
                fecha_inicio_hasta=fecha_inicio_hasta
            )

            return {
                'success': True,
                'data': programas,
                'metadata': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + len(programas)) < total
                },
                'message': f'Se encontraron {len(programas)} programas'
            }

        except Exception as e:
            logger.error(f"❌ Error en buscar_programas_con_paginacion: {e}")
            return {
                'success': False,
                'data': [],
                'metadata': {},
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def contar_programas(codigo: Optional[str] = None,
                        nombre: Optional[str] = None,
                        estado: Optional[str] = None,
                        docente_coordinador_id: Optional[int] = None,
                        fecha_inicio_desde: Optional[str] = None,
                        fecha_inicio_hasta: Optional[str] = None) -> int:
        """Contar programas usando la función fn_contar_programas"""
        try:
            connection = Database.get_connection()
            if not connection:
                return 0
            
            cursor = connection.cursor()
            
            # Preparar parámetros
            params = (
                codigo,
                nombre,
                estado,
                docente_coordinador_id,
                fecha_inicio_desde,
                fecha_inicio_hasta
            )
            
            # Ejecutar función
            cursor.callproc('fn_contar_programas', params)
            result = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if result and result[0]:
                return result[0]
            else:
                return 0
                
        except Exception as e:
            logger.error(f"❌ Error contando programas: {e}")
            return 0
    
    @staticmethod
    def obtener_estadisticas() -> dict:
        """Obtener estadísticas de programas usando la función fn_estadisticas_programas"""
        try:
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo obtener conexión a la base de datos'
                }
            
            cursor = connection.cursor()
            
            # Ejecutar función (sin parámetros)
            cursor.callproc('fn_estadisticas_programas', ())
            result = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if result:
                estadisticas = {
                    'total_programas': result[0],
                    'planificados': result[1],
                    'en_curso': result[2],
                    'finalizados': result[3],
                    'cancelados': result[4],
                    'promedio_duracion': float(result[5]) if result[5] else 0,
                    'promedio_costo': float(result[6]) if result[6] else 0,
                    'promedio_cupos_inscritos': float(result[7]) if result[7] else 0,
                    'total_cupos_disponibles': result[8]
                }
                
                return {
                    'success': True,
                    'data': estadisticas,
                    'message': 'Estadísticas obtenidas exitosamente'
                }
            else:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudieron obtener estadísticas'
                }
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo estadísticas: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error obteniendo estadísticas: {str(e)}'
            }
    
    @staticmethod
    def verificar_codigo_existente(codigo: str, excluir_id: Optional[int] = None) -> bool:
        """Verificar si un código de programa ya existe usando la función fn_verificar_codigo_programa_existente"""
        try:
            connection = Database.get_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            # Ejecutar función
            cursor.callproc('fn_verificar_codigo_programa_existente', (codigo, excluir_id))
            result = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if result and result[0]:
                return bool(result[0])
            else:
                return False
                
        except Exception as e:
            logger.error(f"❌ Error verificando código: {e}")
            return False
    
    # Implementación de métodos abstractos de BaseModel
    @staticmethod
    def buscar_por_filtros(filtros: Dict, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Buscar programas usando filtros"""
        try:
            # Usar el método corregido que devuelve lista
            return ProgramaModel.buscar_programas(
                codigo=filtros.get('codigo'),
                nombre=filtros.get('nombre'),
                estado=filtros.get('estado'),
                docente_coordinador_id=filtros.get('docente_coordinador_id'),
                fecha_inicio_desde=filtros.get('fecha_inicio_desde'),
                fecha_inicio_hasta=filtros.get('fecha_inicio_hasta'),
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Error en buscar_por_filtros: {e}")
            return []
    
    @staticmethod
    def contar_por_filtros(filtros: Dict) -> int:
        """Contar programas usando filtros"""
        try:
            return ProgramaModel.contar_programas(
                codigo=filtros.get('codigo'),
                nombre=filtros.get('nombre'),
                estado=filtros.get('estado'),
                docente_coordinador_id=filtros.get('docente_coordinador_id'),
                fecha_inicio_desde=filtros.get('fecha_inicio_desde'),
                fecha_inicio_hasta=filtros.get('fecha_inicio_hasta')
            )
        except Exception as e:
            logger.error(f"Error en contar_por_filtros: {e}")
            return 0
    
    @staticmethod
    def obtener_por_id(id: int) -> Optional[Dict]:
        """Obtener un programa por ID"""
        try:
            resultado = ProgramaModel.obtener_programa(id)
            if resultado.get('success'):
                return resultado['data']
            else:
                return None
        except Exception as e:
            logger.error(f"Error en obtener_por_id: {e}")
            return None
    
    @staticmethod
    def crear(data: Dict) -> Dict[str, Any]:
        """Crear un nuevo programa"""
        try:
            return ProgramaModel.crear_programa(data)
        except Exception as e:
            logger.error(f"Error en crear: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def actualizar(id: int, data: Dict) -> Dict[str, Any]:
        """Actualizar un programa existente"""
        try:
            return ProgramaModel.actualizar_programa(id, data)
        except Exception as e:
            logger.error(f"Error en actualizar: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error: {str(e)}'
            }
    
    @staticmethod
    def eliminar(id: int) -> Dict[str, Any]:
        """Eliminar un programa"""
        try:
            return ProgramaModel.eliminar_programa(id)
        except Exception as e:
            logger.error(f"Error en eliminar: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error: {str(e)}'
            }