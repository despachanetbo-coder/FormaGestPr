# Archivo main.py
import sys
import os
from PySide6.QtWidgets import QApplication
import logging  # <-- AGREGAR

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

from controller.main_controller import MainController

def main():
    """Punto de entrada principal de la aplicación"""
    app = QApplication(sys.argv)
    
    # Configuración global de la aplicación
    app.setApplicationName("FormaGestPro")
    app.setOrganizationName("DespachaNet")
    
    # Crear y mostrar el controlador principal
    controller = MainController()
    controller.show_window()
    
    # Ejecutar el bucle de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()