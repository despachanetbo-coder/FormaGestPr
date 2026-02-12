# controller/programa_controller.py - VERSIÓN COMPLETA CORREGIDA
import logging
from model.programa_model import ProgramaModel
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ProgramaController:
    
    @staticmethod
    def crear_programa(datos: dict) -> dict:
        """Crear un nuevo programa académico"""
        try:
            logger.debug("DEBUG - ProgramaController.crear_programa")
            
            # Validaciones básicas
            campos_requeridos = ['codigo', 'nombre', 'duracion_meses', 'horas_totales', 'costo_total']
            for campo in campos_requeridos:
                if not datos.get(campo):
                    return {
                        'success': False,
                        'message': f'El campo {campo} es requerido',
                        'data': None
                    }
            
            # Verificar que el código no exista
            if ProgramaModel.verificar_codigo_existente(datos['codigo']):
                return {
                    'success': False,
                    'message': f'El código {datos["codigo"]} ya está registrado',
                    'data': None
                }
            
            # Llamar al modelo para crear el programa
            resultado = ProgramaModel.crear_programa(datos)
            
            return resultado
                
        except Exception as e:
            logger.error(f"❌ Error en controlador crear_programa: {e}")
            return {
                'success': False,
                'message': f'Error interno del sistema: {str(e)}',
                'data': None
            }
    
    @staticmethod
    def actualizar_programa(programa_id: int, datos: dict) -> dict:
        """Actualizar un programa existente"""
        try:
            logger.debug(f"DEBUG - ProgramaController.actualizar_programa para ID: {programa_id}")
            
            # Verificar que el programa existe
            programa_existente = ProgramaModel.obtener_programa(programa_id)
            if not programa_existente['success']:
                return programa_existente
            
            # Verificar que el código no exista (si cambió)
            if datos.get('codigo') and datos['codigo'] != programa_existente['data']['codigo']:
                if ProgramaModel.verificar_codigo_existente(datos['codigo'], programa_id):
                    return {
                        'success': False,
                        'message': f'El código {datos["codigo"]} ya está registrado en otro programa',
                        'data': None
                    }
            
            # Llamar al modelo para actualizar
            resultado = ProgramaModel.actualizar_programa(programa_id, datos)
            
            return resultado
                
        except Exception as e:
            logger.error(f"❌ Error en controlador actualizar_programa: {e}")
            return {
                'success': False,
                'message': f'Error interno del sistema: {str(e)}',
                'data': None
            }
    
    @staticmethod
    def eliminar_programa(programa_id: int) -> dict:
        """Eliminar (cancelar) un programa"""
        try:
            logger.debug(f"DEBUG - ProgramaController.eliminar_programa para ID: {programa_id}")
            
            # Llamar al modelo para eliminar
            resultado = ProgramaModel.eliminar_programa(programa_id)
            
            return resultado
                
        except Exception as e:
            logger.error(f"❌ Error en controlador eliminar_programa: {e}")
            return {
                'success': False,
                'message': f'Error interno del sistema: {str(e)}',
                'data': None
            }
    
    @staticmethod
    def obtener_programa(programa_id: int) -> dict:
        """Obtener un programa por ID"""
        try:
            return ProgramaModel.obtener_programa(programa_id)
        except Exception as e:
            logger.error(f"❌ Error en controlador obtener_programa: {e}")
            return {
                'success': False,
                'message': f'Error interno del sistema: {str(e)}',
                'data': None
            }
    
    @staticmethod
    def buscar_programas(filtros: Optional[dict] = None) -> dict:
        """Buscar programas con filtros"""
        try:
            if filtros is None:
                filtros = {}
            
            resultado = ProgramaModel.buscar_programas_con_paginacion(
                codigo=filtros.get('codigo'),
                nombre=filtros.get('nombre'),
                estado=filtros.get('estado'),
                docente_coordinador_id=filtros.get('docente_coordinador_id'),
                fecha_inicio_desde=filtros.get('fecha_inicio_desde'),
                fecha_inicio_hasta=filtros.get('fecha_inicio_hasta'),
                limit=filtros.get('limit', 20),
                offset=filtros.get('offset', 0)
            )
            
            return resultado
                
        except Exception as e:
            logger.error(f"❌ Error en controlador buscar_programas: {e}")
            return {
                'success': False,
                'data': [],
                'metadata': {},
                'message': f'Error interno del sistema: {str(e)}'
            }
    
    @staticmethod
    def obtener_estadisticas() -> dict:
        """Obtener estadísticas de programas"""
        try:
            return ProgramaModel.obtener_estadisticas()
        except Exception as e:
            logger.error(f"❌ Error en controlador obtener_estadisticas: {e}")
            return {
                'success': False,
                'data': None,
                'message': f'Error interno del sistema: {str(e)}'
            }