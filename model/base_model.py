# Archivo: models/base_model.py
from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, List, Optional
from config.database import Database
import logging

logger = logging.getLogger(__name__)

class BaseModel(QObject):
    """Clase base para todos los modelos de datos"""
    # Usar get_instance() en lugar de crear una nueva instancia directamente
    db = Database.get_instance()
    data_changed = Signal(dict)
    error_occurred = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._data = {}
    
    @property
    def data(self) -> Dict:
        """Obtener una copia de los datos del modelo"""
        return self._data.copy()
    
    @data.setter
    def data(self, value: Dict):
        """Establecer nuevos datos y emitir señal de cambio"""
        self._data = value
        self.data_changed.emit(self._data)
    
    def update_item(self, key: str, value: Any):
        """Actualizar un ítem específico en los datos"""
        self._data[key] = value
        self.data_changed.emit(self._data)
    
    def clear(self):
        """Limpiar todos los datos del modelo"""
        self._data.clear()
        self.data_changed.emit(self._data)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtener un valor del modelo con valor por defecto"""
        return self._data.get(key, default)
    
    def setdefault(self, key: str, default: Any = None) -> Any:
        """Establecer un valor por defecto si la clave no existe"""
        return self._data.setdefault(key, default)
    
    def has_key(self, key: str) -> bool:
        """Verificar si una clave existe en los datos"""
        return key in self._data
    
    def emit_error(self, error_message: str):
        """Emitir señal de error"""
        logger.error(error_message)
        self.error_occurred.emit(error_message)
    
    # Métodos abstractos que deben ser implementados por las clases hijas
    @staticmethod
    def buscar_por_filtros(filtros: Dict, limit: int = 20, offset: int = 0) -> List[Dict]:
        """Buscar registros usando filtros"""
        raise NotImplementedError("Este método debe ser implementado en la clase hija")
    
    @staticmethod
    def contar_por_filtros(filtros: Dict) -> int:
        """Contar registros usando filtros"""
        raise NotImplementedError("Este método debe ser implementado en la clase hija")
    
    @staticmethod
    def obtener_por_id(id: int) -> Optional[Dict]:
        """Obtener un registro por ID"""
        raise NotImplementedError("Este método debe ser implementado en la clase hija")
    
    @staticmethod
    def crear(data: Dict) -> Dict[str, Any]:
        """Crear un nuevo registro"""
        raise NotImplementedError("Este método debe ser implementado en la clase hija")
    
    @staticmethod
    def actualizar(id: int, data: Dict) -> Dict[str, Any]:
        """Actualizar un registro existente"""
        raise NotImplementedError("Este método debe ser implementado en la clase hija")
    
    @staticmethod
    def eliminar(id: int) -> Dict[str, Any]:
        """Eliminar un registro"""
        raise NotImplementedError("Este método debe ser implementado en la clase hija")
    
    @staticmethod
    def obtener_ruta_de_config(clave: str) -> Optional[str]:
        """Obtener la ruta del archivo asociado a un registro"""
        raise NotImplementedError("Este método debe ser implementado en la clase hija")