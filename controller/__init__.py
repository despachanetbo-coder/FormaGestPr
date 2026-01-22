# Archivo: controller/__init__.py
from .base_controller import BaseController
from .auth_controller import AuthController
from .main_controller import MainController
from .docente_controller import DocenteController
from .estudiante_controller import EstudianteController
from .programa_controller import ProgramaController
from .inscripcion_controller import InscripcionController
from .empresa_controller import EmpresaController
from .configuraciones_controller import ConfiguracionesController
from .usuarios_controller import UsuariosController
from .resumen_controller import ResumenController
__all__=[
    "BaseController",
    "AuthController",
    "MainController",
    "DocenteController",
    "EstudianteController",
    "ProgramaController",
    "InscripcionController",
    "EmpresaController",
    "ConfiguracionesController",
    "UsuariosController",
    'ResumenController',
]