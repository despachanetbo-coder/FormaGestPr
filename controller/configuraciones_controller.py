# controller/configuraciones_controller.py
import logging
from typing import Dict, List, Optional, Any
from model.configuraciones_model import ConfiguracionesModel
from utils.validators import Validators

logger = logging.getLogger(__name__)

class ConfiguracionesController:
    """Controlador para la tabla configuraciones"""
    
    @staticmethod
    def validar_datos_configuracion(datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida los datos de la configuración
        
        Args:
            datos: Diccionario con los datos de la configuración
        
        Returns:
            Dict con resultado de validación y datos limpios
        """
        errores = []
        datos_limpios = {}
        
        # Validar clave (obligatoria)
        clave = datos.get('clave')
        if not clave or clave.strip() == "":
            errores.append("La clave es requerida")
        elif len(clave.strip()) > 100:
            errores.append("La clave no puede exceder los 100 caracteres")
        else:
            datos_limpios['clave'] = clave.strip()
        
        # Validar valor (obligatorio)
        valor = datos.get('valor')
        if valor is None:
            errores.append("El valor es requerido")
        else:
            # Convertir a string para validar longitud
            valor_str = str(valor)
            if len(valor_str) > 10000:  # Límite razonable para texto
                errores.append("El valor es demasiado largo")
            else:
                datos_limpios['valor'] = valor
        
        # Validar descripción (opcional)
        descripcion = datos.get('descripcion')
        if descripcion is not None:
            descripcion_str = str(descripcion)
            if len(descripcion_str) > 500:
                errores.append("La descripción no puede exceder los 500 caracteres")
            else:
                datos_limpios['descripcion'] = descripcion
        
        # Validar tipo (opcional, con valores permitidos)
        tipo = datos.get('tipo')
        if tipo is not None:
            tipos_permitidos = ['TEXTO', 'NUMERO', 'BOOLEANO', 'FECHA', 'JSON', 'RUTA']
            if str(tipo).upper() not in tipos_permitidos:
                errores.append(f"Tipo inválido. Debe ser uno de: {', '.join(tipos_permitidos)}")
            else:
                datos_limpios['tipo'] = str(tipo).upper()
        
        # Validar categoría (opcional)
        categoria = datos.get('categoria')
        if categoria is not None:
            categoria_str = str(categoria)
            if len(categoria_str) > 50:
                errores.append("La categoría no puede exceder los 50 caracteres")
            else:
                datos_limpios['categoria'] = categoria_str
        
        # Validar editable (opcional, booleano)
        editable = datos.get('editable')
        if editable is not None:
            valido, valor_booleano = Validators.validar_booleano(editable)
            if not valido:
                errores.append("El campo editable debe ser un valor booleano")
            else:
                datos_limpios['editable'] = valor_booleano
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'datos_limpios': datos_limpios
        }
    
    @staticmethod
    def insertar_configuracion(datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta una nueva configuración
        
        Args:
            datos: Diccionario con los datos de la configuración
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar datos
            validacion = ConfiguracionesController.validar_datos_configuracion(datos)
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Llamar al modelo
            resultado = ConfiguracionesModel.insertar_configuracion(
                clave=validacion['datos_limpios']['clave'],
                valor=validacion['datos_limpios']['valor'],
                descripcion=validacion['datos_limpios'].get('descripcion'),
                tipo=validacion['datos_limpios'].get('tipo', 'TEXTO'),
                categoria=validacion['datos_limpios'].get('categoria', 'GENERAL'),
                editable=validacion['datos_limpios'].get('editable', True)
            )
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al insertar configuración: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al insertar configuración'
                }
                
        except Exception as e:
            logger.error(f"Error al insertar configuración: {e}")
            return {
                'success': False,
                'message': f"Error al insertar configuración: {str(e)}"
            }
    
    @staticmethod
    def actualizar_configuracion(clave: str, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza una configuración existente
        
        Args:
            clave: Clave de la configuración a actualizar
            datos: Diccionario con los datos a actualizar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar que la clave no esté vacía
            if not clave or clave.strip() == "":
                return {
                    'success': False,
                    'message': 'La clave de la configuración es requerida'
                }
            
            # Validar datos
            validacion = ConfiguracionesController.validar_datos_configuracion(datos)
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Llamar al modelo
            resultado = ConfiguracionesModel.actualizar_configuracion(
                clave=clave,
                valor=validacion['datos_limpios']['valor'],
                descripcion=validacion['datos_limpios'].get('descripcion'),
                tipo=validacion['datos_limpios'].get('tipo'),
                categoria=validacion['datos_limpios'].get('categoria'),
                editable=validacion['datos_limpios'].get('editable')
            )
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al actualizar configuración: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al actualizar configuración'
                }
                
        except Exception as e:
            logger.error(f"Error al actualizar configuración: {e}")
            return {
                'success': False,
                'message': f"Error al actualizar configuración: {str(e)}"
            }
    
    @staticmethod
    def eliminar_configuracion(clave: str) -> Dict[str, Any]:
        """
        Elimina una configuración
        
        Args:
            clave: Clave de la configuración a eliminar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if not clave or clave.strip() == "":
                return {
                    'success': False,
                    'message': 'La clave de la configuración es requerida'
                }
            
            resultado = ConfiguracionesModel.eliminar_configuracion(clave)
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al eliminar configuración: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al eliminar configuración'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar configuración: {e}")
            return {
                'success': False,
                'message': f"Error al eliminar configuración: {str(e)}"
            }
    
    @staticmethod
    def obtener_configuracion(clave: str) -> Dict[str, Any]:
        """
        Obtiene una configuración por clave
        
        Args:
            clave: Clave de la configuración
        
        Returns:
            Dict con los datos de la configuración
        """
        try:
            if not clave or clave.strip() == "":
                return {
                    'success': False,
                    'message': 'La clave de la configuración es requerida'
                }
            
            configuracion = ConfiguracionesModel.obtener_configuracion(clave)
            
            if configuracion:
                return {
                    'success': True,
                    'data': configuracion
                }
            else:
                return {
                    'success': False,
                    'message': f'Configuración con clave "{clave}" no encontrada'
                }
                
        except Exception as e:
            logger.error(f"Error al obtener configuración: {e}")
            return {
                'success': False,
                'message': f"Error al obtener configuración: {str(e)}"
            }
    
    @staticmethod
    def buscar_configuraciones(filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Busca configuraciones con filtros
        
        Args:
            filtros: Diccionario con filtros de búsqueda
        
        Returns:
            Dict con resultados
        """
        try:
            clave = filtros.get('clave')
            categoria = filtros.get('categoria')
            tipo = filtros.get('tipo')
            editable = filtros.get('editable')
            
            configuraciones = ConfiguracionesModel.buscar_configuraciones(
                clave=clave,
                categoria=categoria,
                tipo=tipo,
                editable=editable
            )
            
            return {
                'success': True,
                'data': configuraciones
            }
            
        except Exception as e:
            logger.error(f"Error al buscar configuraciones: {e}")
            return {
                'success': False,
                'message': f"Error al buscar configuraciones: {str(e)}"
            }
    
    @staticmethod
    def listar_configuraciones() -> Dict[str, Any]:
        """
        Lista todas las configuraciones
        
        Returns:
            Dict con lista de configuraciones
        """
        try:
            configuraciones = ConfiguracionesModel.listar_configuraciones()
            
            return {
                'success': True,
                'data': configuraciones
            }
            
        except Exception as e:
            logger.error(f"Error al listar configuraciones: {e}")
            return {
                'success': False,
                'message': f"Error al listar configuraciones: {str(e)}"
            }