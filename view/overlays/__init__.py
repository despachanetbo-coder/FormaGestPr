# Archivo: view/overlays/__init__.py
"""
    Módulo de formularios flotantes para la aplicación
"""

from .base_overlay import BaseOverlay
from .docente_overlay import DocenteOverlay
from .estudiante_overlay import EstudianteOverlay
from .programa_overlay import ProgramaOverlay
# Exportar todas las clases
__all__ = [
    'BaseOverlay',
    'DocenteOverlay',
    'EstudianteOverlay',
    'ProgramaOverlay',
]
