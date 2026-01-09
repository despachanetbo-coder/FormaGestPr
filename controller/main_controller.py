# Archivo: controller/main_controller.py
from PySide6.QtCore import QObject, Signal, Slot
from view.main_window import MainWindow

class MainController(QObject):
    """Controlador principal que maneja la lógica de la aplicación"""
    
    # Señales (opcional)
    data_loaded = Signal(dict)
    status_changed = Signal(str)
    
    def __init__(self):
        self.main_window = MainWindow()
        self.model = None  # Se inicializará cuando crees los modelos
        self.view = self.main_window
        
        # Conectar señales y slots
        self._connect_signals()
        
    def _connect_signals(self):
        """Conectar todas las señales entre vista y controlador"""
        # Ejemplo: self.view.boton_clicado.connect(self._on_boton_clicado)
        pass
    
    def show_window(self):
        """Mostrar la ventana principal"""
        self.view.showMaximized()
    
    @Slot()
    def _on_boton_clicado(self):
        """Ejemplo de manejador de eventos"""
        print("Botón clicado desde el controlador")
        # Lógica de negocio aquí