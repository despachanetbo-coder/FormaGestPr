# Archivo: view/tabs/__init__.py
"""
Módulo de pestañas personalizadas para la aplicación
"""

from .base_tab import BaseTab
from .inicio_tab import InicioTab
from .resumen_tab import ResumenTab

# Exportar todas las clases
__all__ = [
    'BaseTab', 
    'InicioTab',
    'ResumenTab',
]