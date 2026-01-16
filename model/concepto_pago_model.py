# Archivo: model/concepto_pago_model.py
# model/concepto_pago_model.py
"""
Modelo para manejar conceptos de pago.
"""

import logging
from typing import List, Dict, Any, Optional

from .base_model import BaseModel
from config.database import Database

logger = logging.getLogger(__name__)


class ConceptoPagoModel(BaseModel):
    """Modelo para manejar conceptos de pago"""
    
    @staticmethod
    def obtener_conceptos_activos() -> List[Dict[str, Any]]:
        """
        Obtener todos los conceptos de pago activos
        
        Returns:
            Lista de conceptos de pago
        """
        try:
            query = """
                SELECT * FROM conceptos_pago
                WHERE activo = TRUE
                ORDER BY orden_visualizacion
            """
            
            results = Database.execute_query(query)
            
            if results:
                column_names = [
                    'id', 'codigo', 'nombre', 'descripcion', 'tipo',
                    'valor_base', 'porcentaje', 'aplica_programa',
                    'aplica_estudiante', 'orden_visualizacion', 'activo',
                    'created_at'
                ]
                return [dict(zip(column_names, row)) for row in results]
            
            return []
            
        except Exception as e:
            logger.error(f"Error obteniendo conceptos de pago: {e}")
            return []
    
    @staticmethod
    def obtener_concepto_por_codigo(
        codigo: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtener concepto de pago por código
        
        Args:
            codigo: Código del concepto
            
        Returns:
            Dict con datos del concepto
        """
        try:
            query = """
                SELECT * FROM conceptos_pago
                WHERE codigo = %s AND activo = TRUE
            """
            params = (codigo,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            
            if result:
                column_names = [
                    'id', 'codigo', 'nombre', 'descripcion', 'tipo',
                    'valor_base', 'porcentaje', 'aplica_programa',
                    'aplica_estudiante', 'orden_visualizacion', 'activo',
                    'created_at'
                ]
                return dict(zip(column_names, result))
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo concepto por código: {e}")
            return None