# Archivo: view/tabs/base_tab.py
import os
from abc import ABC, abstractmethod
from typing import Optional
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QFrame, QLabel, QHBoxLayout
from PySide6.QtCore import Qt, QTimer, QDateTime
from PySide6.QtGui import QFont

# Crear una metaclase que combine QObject y ABC
from PySide6.QtCore import QObject
from abc import ABCMeta

# Metaclase que combina las metaclases de QObject y ABC
class QtABCMeta(type(QObject), ABCMeta): # type: ignore
    pass

class BaseTab(QWidget, ABC, metaclass=QtABCMeta):
    """Clase base abstracta para todas las pestañas de la aplicación"""
    user_data = {}
    
    def __init__(self, tab_id: str, tab_name: str, parent=None):
        super().__init__(parent)
        self.tab_widget = QTabWidget()
        self.tab_id = tab_id
        self.tab_name = tab_name
        
        # ✅ Inicializar atributos comunes
        self.user_data = {}
        
        # Configurar propiedades del widget
        self.setObjectName(self.tab_id)
        
        # Layout principal con header
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 15)
        self.main_layout.setSpacing(0)
        
        # Agregar header a todas las pestañas
        self._create_header()
        
        # Contenedor para contenido específico de cada pestaña
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(15, 20, 15, 15)
        self.content_layout.setSpacing(10)
        
        self.main_layout.addWidget(self.content_widget)
        
        # Inicializar la interfaz
        # self._init_ui()
        
        # Cargar estilos específicos de la pestaña
        self._load_tab_styles()
    
    def _create_header(self) -> None:
        """Crear encabezado con gradiente para todas las pestañas"""
        header_frame = QFrame()
        header_frame.setObjectName("HeaderFrame")
        header_frame.setMinimumHeight(120)
        header_frame.setMaximumHeight(130)
        
        header_layout = QVBoxLayout(header_frame)
        header_layout.setContentsMargins(40, 20, 40, 30)
        
        # Fila superior: Título y nombre de usuario
        top_row = QHBoxLayout()
        
        # Título del dashboard (configurable por pestaña)
        self.title_label = QLabel(f"{self.tab_name}")
        self.title_label.setObjectName("DashboardTitle")
        self.title_label.setStyleSheet("""
            #DashboardTitle {
                font-size: 36px;
                font-weight: bold;
                color: rgba(255, 255, 255, 0.9);
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: rgba(255, 255, 255, 0.01);
            }
        """)
        top_row.addWidget(self.title_label)
        top_row.addStretch()
        
        # ✅ CAMBIO 2: Modificar esta línea para usar datos dinámicos
        nombre_usuario = self._get_user_display_name()  # Método nuevo
        # Nombre del usuario (en lugar de hora)
        # Esto debería venir de tu sistema de autenticación
        self.user_label = QLabel(f"👤 Usuario: {nombre_usuario}")
        self.user_label.setObjectName("UserLabel")
        self.user_label.setStyleSheet("""
            #UserLabel {
                font-size: 14px;
                color: rgba(255, 255, 255, 0.9);
                font-weight: bold;
                padding: 8px 16px;
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
        """)
        top_row.addWidget(self.user_label)
        header_layout.addLayout(top_row)
        
        # Subtítulo (configurable por pestaña)
        self.subtitle_label = QLabel(f"{self.tab_name}")
        self.subtitle_label.setStyleSheet("""
            QLabel {
                font-size: 16px;
                color: rgba(255, 255, 255, 0.8);
                background-color: rgba(255, 255, 255, 0.01);
                padding-top: 5px;
            }
        """)
        header_layout.addWidget(self.subtitle_label)
        header_layout.addStretch()
        
        # Estilo del encabezado con gradiente
        header_frame.setStyleSheet("""
            #HeaderFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2980b9,
                    stop:1 #2c3e50
                );
                border-bottom: 3px solid #1a5276;
            }
        """)
        
        self.main_layout.addWidget(header_frame)
    
    def set_header_title(self, title: str) -> None:
        """Cambiar el título del header"""
        self.title_label.setText(f"{title}")
    
    def set_header_subtitle(self, subtitle: str) -> None:
        """Cambiar el subtítulo del header"""
        self.subtitle_label.setText(subtitle)
    
    def set_user_info(self, username: str, role: Optional[str] = None) -> None:
        """Establecer información del usuario"""
        if role:
            self.user_label.setText(f"👤 {username} ({role})")
        else:
            self.user_label.setText(f"👤 {username}")
    
    def set_header_gradient(self, color1: str, color2: str, color3: Optional[str] = None) -> None:
        """Cambiar el gradiente del header"""
        if color3:
            gradient = f"""
                #HeaderFrame {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {color1},
                        stop:0.5 {color2},
                        stop:1 {color3}
                    );
                }}
            """
        else:
            gradient = f"""
                #HeaderFrame {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:1, y2:0,
                        stop:0 {color1},
                        stop:1 {color2}
                    );
                }}
            """
        
        # Aplicar el nuevo gradiente
        header_frame = self.findChild(QFrame, "HeaderFrame")
        if header_frame:
            current_style = header_frame.styleSheet()
            # Reemplazar solo la parte del gradiente
            if "background: qlineargradient" in current_style:
                lines = current_style.split('\n')
                new_lines = []
                for line in lines:
                    if "background: qlineargradient" in line:
                        new_lines.append(gradient.strip())
                    else:
                        new_lines.append(line)
                header_frame.setStyleSheet('\n'.join(new_lines))
    
    def _get_user_display_name(self) -> str:
        """Obtener nombre para mostrar del usuario"""
        if not self.user_data:
            return "Invitado"
        
        # Prioridad: nombre_completo > username
        nombre_completo = self.user_data.get('nombre_completo', '').strip()
        if nombre_completo:
            return nombre_completo
        
        username = self.user_data.get('username', '').strip()
        if username:
            return username
        
        return "Usuario"
    
    @abstractmethod
    def _init_ui(self):
        """
        Método abstracto para inicializar la interfaz de usuario.
        Debe ser implementado por cada pestaña concreta.
        """
        pass
    
    def _load_tab_styles(self):
        """Cargar estilos específicos para esta pestaña"""
        # Los estilos principales se aplican desde MainWindow
        pass
    
    def apply_styles(self, stylesheet: str):
        """Aplicar estilos específicos a esta pestaña"""
        self.setStyleSheet(stylesheet)
    
    def add_widget(self, widget, stretch=0, alignment=Qt.AlignmentFlag.AlignTop):
        """Agregar un widget al layout del contenido"""
        self.content_layout.addWidget(widget, stretch, alignment)
    
    def add_layout(self, layout, stretch=0):
        """Agregar un sub-layout al layout del contenido"""
        self.content_layout.addLayout(layout, stretch)
    
    def add_stretch(self, stretch=1):
        """Agregar un espacio elástico"""
        self.content_layout.addStretch(stretch)
    
    def add_spacing(self, size: int):
        """Agregar un espacio fijo"""
        self.content_layout.addSpacing(size)
    
    def clear_content(self):
        """Limpiar el contenido específico de la pestaña (no el header)"""
        # Eliminar solo los widgets del contenido
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater() #type:ignore
            elif item.layout():
                # Limpiar layout recursivamente
                self._clear_layout(item.layout())
    
    def _clear_layout(self, layout):
        """Limpiar un layout recursivamente"""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())
    
    def refresh(self):
        """Actualizar el contenido de la pestaña"""
        # Método que puede ser sobrescrito para actualizar datos
        pass
    
    def on_tab_selected(self):
        """Método llamado cuando la pestaña es seleccionada"""
        print(f"Pestaña '{self.tab_name}' seleccionada")
    
    def on_tab_deselected(self):
        """Método llamado cuando la pestaña es deseleccionada"""
        pass
    
    def get_tab_name(self):
        """Obtener el nombre de la pestaña"""
        return self.tab_name
    
    def set_tab_name(self, name: str):
        """Cambiar el nombre de la pestaña"""
        self.tab_name = name
    
    def setup_style(self):
        """Configurar estilos de la aplicación"""
        # Estilo para las pestañas
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #ddd;
                background-color: white;
                border-radius: 10px;
                margin-top: 5px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                padding: 12px 25px;
                margin-right: 3px;
                border: 1px solid #ddd;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: bold;
                color: #2c3e50;
                font-size: 13px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: white;
                border-color: #2980b9;
            }
            QTabBar::tab:hover:!selected {
                background-color: #ecf0f1;
            }
            QTabBar::tab:first {
                margin-left: 5px;
            }
        """)
    
    def set_user_data(self, user_data: dict):
        """
        Actualizar datos del usuario en la pestaña
        
        Args:
            user_data: Diccionario con datos del usuario
        """
        self.user_data = user_data or {}
        
        # Actualizar la etiqueta si ya existe
        if hasattr(self, 'user_label') and self.user_label:
            nombre_usuario = self._get_user_display_name()
            self.user_label.setText(f"👤 {nombre_usuario}")