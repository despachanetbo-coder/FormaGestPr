# view/style/style_manager.py
import os
from PySide6.QtCore import QFile, QTextStream, QIODevice

class StyleManager:
    """Gestor de estilos para la aplicación"""
    
    @staticmethod
    def cargar_estilos_base(widget):
        """Carga los estilos base estructurales"""
        base_path = "views/styles/base.qss"
        if os.path.exists(base_path):
            StyleManager.cargar_qss(widget, base_path)
            
    @staticmethod
    def cargar_tema(widget, tema="light"):
        """Carga el tema de colores"""
        tema_path = f"views/styles/{tema}.qss"
        if os.path.exists(tema_path):
            StyleManager.cargar_qss(widget, tema_path)
            
    @staticmethod
    def cargar_estilos_overlay(widget):
        """Carga estilos específicos para overlays"""
        overlay_path = "views/styles/overlay.qss"
        if os.path.exists(overlay_path):
            StyleManager.cargar_qss(widget, overlay_path)
            
    @staticmethod
    def cargar_qss(widget, qss_path):
        """Carga un archivo QSS específico"""
        try:
            file = QFile(qss_path)
            # Usar QIODeviceBase.OpenModeFlag en PySide6
            if file.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
                stream = QTextStream(file)
                # Leer todo el contenido del archivo
                stylesheet = stream.readAll()
                # Si el widget ya tiene estilos, combinar con los nuevos
                current_stylesheet = widget.styleSheet()
                if current_stylesheet:
                    widget.setStyleSheet(current_stylesheet + "\n" + stylesheet)
                else:
                    widget.setStyleSheet(stylesheet)
                file.close()
        except Exception as e:
            print(f"Error cargando estilos {qss_path}: {e}")
    
    @staticmethod
    def cargar_qss_contenido(widget, qss_contenido):
        """Carga estilos directamente desde contenido de texto"""
        try:
            current_stylesheet = widget.styleSheet()
            if current_stylesheet:
                widget.setStyleSheet(current_stylesheet + "\n" + qss_contenido)
            else:
                widget.setStyleSheet(qss_contenido)
        except Exception as e:
            print(f"Error cargando estilos desde texto: {e}")
    
    @staticmethod
    def cambiar_tema(widget, tema_nombre):
        """Cambia el tema dinámicamente"""
        # Primero, cargar solo los estilos base (sin tema)
        StyleManager.cargar_estilos_base(widget)
        # Luego, cargar el nuevo tema
        StyleManager.cargar_tema(widget, tema_nombre)