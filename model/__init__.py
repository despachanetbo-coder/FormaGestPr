# Archivo: model/__init__.py
from .base_model import BaseModel
from .data_model import DataModel
from .docente_model import DocenteModel
from .estudiante_model import EstudianteModel
from .programa_model import ProgramaModel
from .empresa_model import EmpresaModel
from .configuraciones_model import ConfiguracionesModel
from .usuarios_model import UsuariosModel
__all__=[
    "BaseModel",
    "DataModel",
    "DocenteModel",
    "EstudianteModel",
    "ProgramaModel",
    "EmpresaModel",
    "ConfiguracionesModel",
    "UsuariosModel",
]