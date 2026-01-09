from PySide6.QtCore import QObject, Signal

class DataModel(QObject):
    """Modelo de datos de ejemplo"""
    
    data_changed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self._data = {}
    
    @property
    def data(self):
        return self._data.copy()
    
    @data.setter
    def data(self, value):
        self._data = value
        self.data_changed.emit(self._data)
    
    def update_item(self, key, value):
        """Actualizar un ítem específico"""
        self._data[key] = value
        self.data_changed.emit(self._data)