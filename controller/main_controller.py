# Archivo: controller/main_controller.py
from PySide6.QtCore import QObject, Signal, Slot
from view.main_window import MainWindow

class MainController(QObject):
    """Controlador principal que maneja la lógica de la aplicación"""
    
    # Señales (opcional)
    data_loaded = Signal(dict)
    status_changed = Signal(str)
    
    def __init__(self, user_data=None):  # CAMBIAR: Agregar parámetro user_data
        super().__init__()  # IMPORTANTE: Llamar al constructor de QObject
        
        self.user_data = user_data or {}  # CAMBIAR: Almacenar datos del usuario
        self.main_window = None  # CAMBIAR: No crear MainWindow aún
        self.model = None  # Se inicializará cuando crees los modelos
        self.view = None  # CAMBIAR: Inicializar como None
        
        # Conectar señales y slots
        self._connect_signals()
        
    def _connect_signals(self):
        """Conectar todas las señales entre vista y controlador"""
        # Ejemplo: self.view.boton_clicado.connect(self._on_boton_clicado)
        pass
    
    def show_window(self):
        """Mostrar la ventana principal"""
        if not self.main_window:
            # CAMBIAR: Crear MainWindow con datos del usuario
            self.main_window = MainWindow(user_data=self.user_data)
            self.view = self.main_window
            
            # Conectar señales si es necesario
            self._connect_window_signals()
        
        if self.view:
            self.view.showMaximized()
            print(f"✅ Ventana principal mostrada para usuario: {self.user_data.get('username', 'Invitado')}")
    
    def _connect_window_signals(self):
        """Conectar señales específicas de MainWindow"""
        if self.main_window:
            # Aquí puedes conectar señales específicas
            # Ejemplo: self.main_window.some_signal.connect(self.some_slot)
            pass
    
    @Slot()
    def _on_boton_clicado(self):
        """Ejemplo de manejador de eventos"""
        print("Botón clicado desde el controlador")
        # Lógica de negocio aquí
    
    def set_user_data(self, user_data: dict):
        """Establecer datos del usuario después del login exitoso"""
        self.user_data = user_data or {}
        print(f"Datos del usuario establecidos: {self.user_data.get('username', 'Desconocido')}")
        
        # Si la ventana ya está creada, actualizar sus datos
        if self.main_window:
            self.main_window.user_data = self.user_data
            # Notificar a las pestañas para que actualicen
            self._update_tabs_user_data()
    
    def _update_tabs_user_data(self):
        """Actualizar datos del usuario en todas las pestañas"""
        if not self.main_window:
            return
        
        # Iterar sobre todas las pestañas y actualizar user_data
        for tab_index, tab in self.main_window.tabs_dict.items():
            if hasattr(tab, 'set_user_data'):
                tab.set_user_data(self.user_data)
