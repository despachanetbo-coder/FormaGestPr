# Archivo: model/__init__.py
from .base_model import BaseModel
from .data_model import DataModel
from .docente_model import DocenteModel
from .estudiante_model import EstudianteModel
from .programa_model import ProgramaModel
from .inscripcion_model import InscripcionModel
from .empresa_model import EmpresaModel
from .configuraciones_model import ConfiguracionesModel
from .usuarios_model import UsuariosModel
from .resumen_model import ResumenModel
__all__=[
    "BaseModel",
    "DataModel",
    "DocenteModel",
    "EstudianteModel",
    "ProgramaModel",
    "InscripcionModel",
    "EmpresaModel",
    "ConfiguracionesModel",
    "UsuariosModel",
    'ResumenModel',
]