# main.py (versión actualizada)
import sys
import os
from PySide6.QtWidgets import QApplication
import logging

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug.log', mode='w', encoding='utf-8')
    ]
)

# Asegurar que Python encuentre los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from view.login_window import LoginWindow
from controller.main_controller import MainController

class ApplicationManager:
    """Gestor principal de la aplicación"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = None
        self.main_controller = None
        
        # Configuración global
        self.app.setApplicationName("FormaGestPro")
        self.app.setOrganizationName("DespachaNet")
    
    def show_login(self):
        """Mostrar ventana de login"""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.show()
    
    def on_login_successful(self, user_data):
        """Manejador para login exitoso"""
        print(f"✅ Login exitoso para: {user_data.get('username')}")
        print(f"📊 Datos del usuario: {user_data}")
        
        # CAMBIAR: Pasar datos del usuario al MainController
        self.main_controller = MainController(user_data=user_data)
        self.main_controller.show_window()
        
        # Cerrar ventana de login después de un breve delay
        if self.login_window:
            self.login_window.close()
    
    def run(self):
        """Ejecutar la aplicación"""
        self.show_login()
        return self.app.exec()

def main():
    """Punto de entrada principal de la aplicación"""
    manager = ApplicationManager()
    sys.exit(manager.run())

if __name__ == "__main__":
    main()