# service/programa_estado_service.py
"""
Servicio para gestionar la actualización automática de estados de programas
según su fecha de conclusión y reglas de negocio.
"""
from datetime import datetime, date
import logging
from typing import List, Dict, Any, Optional, Union

from model.programa_model import ProgramaModel

logger = logging.getLogger(__name__)

class ProgramaEstadoService:
    """
    Servicio que maneja la lógica de negocio para actualizar automáticamente
    el estado de los programas según su fecha de conclusión.
    
    Reglas:
    - Si fecha_fin <= fecha_sistema y estado != CANCELADO → estado = CONCLUIDO
    - El estado CANCELADO se mantiene (fue una decisión manual)
    """
    
    @staticmethod
    def verificar_y_actualizar_estados() -> Dict[str, Any]:
        """
        Verifica todos los programas activos y actualiza su estado a CONCLUIDO
        si su fecha de fin es menor o igual a la fecha actual.
        
        Returns:
            Dict con estadísticas de la operación
        """
        try:
            fecha_actual = date.today()
            logger.info(f"🔄 Iniciando verificación de estados de programas - Fecha sistema: {fecha_actual}")
            
            # Obtener todos los programas que NO estén en estado CONCLUIDO o CANCELADO
            # y cuya fecha_fin sea <= fecha_actual
            programas_a_actualizar = ProgramaModel.obtener_programas_para_concluir(fecha_actual)
            
            # Validar que programas_a_actualizar sea una lista
            if not isinstance(programas_a_actualizar, list):
                logger.error(f"Error: ProgramaModel.obtener_programas_para_concluir retornó {type(programas_a_actualizar)}")
                return {
                    'success': False,
                    'actualizados': 0,
                    'mensaje': 'Error en formato de datos retornados por el modelo'
                }
            
            if not programas_a_actualizar:
                logger.info("✅ No hay programas pendientes de concluir")
                return {
                    'success': True,
                    'actualizados': 0,
                    'mensaje': 'No hay programas pendientes de concluir'
                }
            
            logger.info(f"📊 Se encontraron {len(programas_a_actualizar)} programas para concluir")
            
            actualizados = 0
            errores = []
            
            for programa in programas_a_actualizar:
                try:
                    # Manejar diferentes formatos de retorno (tupla o diccionario)
                    programa_dict = ProgramaEstadoService._convertir_a_diccionario(programa)
                    
                    if not programa_dict:
                        error_msg = "Formato de programa no válido"
                        logger.error(error_msg)
                        errores.append(error_msg)
                        continue
                    
                    programa_id = programa_dict.get('id')
                    codigo = programa_dict.get('codigo', 'SIN CÓDIGO')
                    nombre = programa_dict.get('nombre', 'SIN NOMBRE')
                    fecha_fin = programa_dict.get('fecha_fin')
                    
                    # Verificar nuevamente la fecha (doble validación)
                    if fecha_fin:
                        fecha_fin_date = ProgramaEstadoService._convertir_a_fecha(fecha_fin)
                        
                        if fecha_fin_date and fecha_fin_date <= fecha_actual:
                            # Actualizar el estado a CONCLUIDO
                            resultado = ProgramaModel.actualizar_estado(programa_id, 'CONCLUIDO')
                            
                            if resultado and resultado.get('success'):
                                actualizados += 1
                                logger.info(f"✅ Programa concluido: {codigo} - {nombre} (ID: {programa_id})")
                                
                                # Ya no intentamos registrar en bitácora
                                # Simplemente hacemos log del cambio
                                logger.debug(f"Cambio de estado registrado para programa {programa_id}: {nombre} -> CONCLUIDO")
                            else:
                                error_msg = f"Error actualizando programa {codigo}: {resultado.get('message', 'Error desconocido') if resultado else 'Resultado nulo'}"
                                logger.error(error_msg)
                                errores.append(error_msg)
                    
                except Exception as e:
                    error_msg = f"Error procesando programa: {str(e)}"
                    logger.error(error_msg)
                    errores.append(error_msg)
            
            # Resumen final
            resumen = {
                'success': len(errores) == 0,
                'actualizados': actualizados,
                'errores': errores,
                'total_procesados': len(programas_a_actualizar),
                'fecha_verificacion': fecha_actual.isoformat(),
                'mensaje': f"Procesados: {len(programas_a_actualizar)}, Actualizados: {actualizados}, Errores: {len(errores)}"
            }
            
            if actualizados > 0:
                logger.info(f"🎯 {actualizados} programas concluidos automáticamente")
            
            if errores:
                logger.warning(f"⚠️ {len(errores)} errores durante la actualización")
            
            return resumen
            
        except Exception as e:
            logger.error(f"Error en verificación de estados: {e}", exc_info=True)
            return {
                'success': False,
                'actualizados': 0,
                'error': str(e),
                'mensaje': f"Error en verificación: {str(e)}"
            }
    
    @staticmethod
    def verificar_programa_especifico(programa_id: int) -> Dict[str, Any]:
        """
        Verifica y actualiza un programa específico si corresponde.
        Útil cuando se carga un programa en el overlay.
        
        Args:
            programa_id: ID del programa a verificar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            fecha_actual = date.today()
            
            # Obtener el programa
            programa = ProgramaModel.obtener_por_id(programa_id)
            
            # Convertir a diccionario si es necesario
            programa_dict = ProgramaEstadoService._convertir_a_diccionario(programa)
            
            if not programa_dict:
                return {
                    'success': False,
                    'mensaje': f'Programa ID {programa_id} no encontrado o formato inválido'
                }
            
            # Verificar si cumple condiciones para concluir
            estado_actual = programa_dict.get('estado')
            fecha_fin = programa_dict.get('fecha_fin')
            
            # Si ya está CONCLUIDO o CANCELADO, no hacer nada
            if estado_actual in ['CONCLUIDO', 'CANCELADO']:
                return {
                    'success': True,
                    'actualizado': False,
                    'mensaje': f'Programa ya está en estado {estado_actual}',
                    'estado_anterior': estado_actual,
                    'estado_nuevo': estado_actual
                }
            
            # Verificar fecha
            if fecha_fin:
                fecha_fin_date = ProgramaEstadoService._convertir_a_fecha(fecha_fin)
                
                if fecha_fin_date and fecha_fin_date <= fecha_actual:
                    # Actualizar a CONCLUIDO
                    resultado = ProgramaModel.actualizar_estado(programa_id, 'CONCLUIDO')
                    
                    if resultado and resultado.get('success'):
                        logger.info(f"✅ Programa {programa_dict.get('codigo', 'N/A')} concluido automáticamente (verificación específica)")
                        
                        # Ya no intentamos registrar en bitácora
                        logger.debug(f"Cambio de estado registrado para programa {programa_id} -> CONCLUIDO")
                        
                        return {
                            'success': True,
                            'actualizado': True,
                            'mensaje': 'Programa concluido automáticamente',
                            'estado_anterior': estado_actual,
                            'estado_nuevo': 'CONCLUIDO'
                        }
                    else:
                        return {
                            'success': False,
                            'actualizado': False,
                            'mensaje': resultado.get('message', 'Error al actualizar') if resultado else 'Error al actualizar'
                        }
            
            # No cumple condiciones
            return {
                'success': True,
                'actualizado': False,
                'mensaje': 'Programa no cumple condiciones para concluir',
                'estado_anterior': estado_actual,
                'estado_nuevo': estado_actual
            }
            
        except Exception as e:
            logger.error(f"Error verificando programa específico {programa_id}: {e}", exc_info=True)
            return {
                'success': False,
                'actualizado': False,
                'error': str(e)
            }
    
    @staticmethod
    def _convertir_a_diccionario(programa: Any) -> Optional[Dict[str, Any]]:
        """
        Convierte diferentes formatos de programa a diccionario.
        
        Args:
            programa: Puede ser tupla, diccionario o None
            
        Returns:
            Diccionario con los datos del programa o None si no es válido
        """
        if programa is None:
            return None
        
        # Si ya es diccionario, retornarlo
        if isinstance(programa, dict):
            return programa
        
        # Si es tupla, intentar convertir a diccionario (asumiendo orden específico)
        if isinstance(programa, (tuple, list)):
            # Intentar mapear por posición si conocemos la estructura
            # Este mapeo debe coincidir con el orden de columnas en la consulta SQL
            if len(programa) >= 4:
                return {
                    'id': programa[0],
                    'codigo': programa[1],
                    'nombre': programa[2],
                    'fecha_fin': programa[3],
                    'estado': programa[4] if len(programa) > 4 else None
                }
        
        # Si no se puede convertir, retornar None
        logger.warning(f"No se pudo convertir programa a diccionario: {type(programa)}")
        return None
    
    @staticmethod
    def _convertir_a_fecha(fecha_valor: Any) -> Optional[date]:
        """
        Convierte diferentes formatos de fecha a objeto date.
        
        Args:
            fecha_valor: Puede ser date, datetime, string o None
            
        Returns:
            Objeto date o None si no es válido
        """
        if fecha_valor is None:
            return None
        
        if isinstance(fecha_valor, date):
            return fecha_valor
        
        if isinstance(fecha_valor, datetime):
            return fecha_valor.date()
        
        if isinstance(fecha_valor, str):
            try:
                # Intentar diferentes formatos de fecha
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]:
                    try:
                        return datetime.strptime(fecha_valor, fmt).date()
                    except ValueError:
                        continue
            except Exception:
                pass
        
        logger.warning(f"No se pudo convertir fecha: {fecha_valor} ({type(fecha_valor)})")
        return None