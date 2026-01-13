# Archivo: view/tabs/__init__.py
"""
    Módulo de estilos personalizadas para la aplicación
"""

"""
    En esta carpeta también se tiene archivos de estilos específicos
    para diferentes componentes de la interfaz de usuario.
    
    view/styles/base.qss: Estilos base para la aplicación.
    view/styles/light.qss: Estilos de color para el tema claro.
    view/styles/overlay.qss: Estilos específicos para formularios flotantes.
"""

from .style_manager import StyleManager
# Exportar todas las clases
__all__ = [
    'StyleManager'
]