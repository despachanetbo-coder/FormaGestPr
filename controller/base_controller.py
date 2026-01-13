"""
Clase base para controladores
"""
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseController:
    """Controlador base con funcionalidades comunes"""
    
    def __init__(self, db_config: Dict[str, Any]):
        """Inicializa con configuración de base de datos"""
        self.db_config = db_config
    
    def validar_campos_requeridos(
        self,
        data: Dict[str, Any],
        campos_requeridos: list
    ) -> Dict[str, Any]:
        """
        Valida que los campos requeridos estén presentes
        
        Args:
            data: Diccionario con datos
            campos_requeridos: Lista de campos requeridos
            
        Returns:
            Dict con resultado de validación
        """
        for campo in campos_requeridos:
            if campo not in data or data[campo] in (None, '', []):
                return {
                    'success': False,
                    'message': f'Campo requerido faltante: {campo}'
                }
        
        return {'success': True, 'message': 'Validación exitosa'}
    
    def formatear_respuesta(
        self,
        success: bool,
        message: str,
        data: Any = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Formatea respuesta estándar
        
        Args:
            success: Indica si fue exitoso
            message: Mensaje descriptivo
            data: Datos adicionales
            error: Detalle del error (si aplica)
            
        Returns:
            Dict con respuesta formateada
        """
        respuesta = {
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        if data is not None:
            respuesta['data'] = data
        
        if error and not success:
            respuesta['error'] = error
            logger.error(f"{message}: {error}")
        
        return respuesta