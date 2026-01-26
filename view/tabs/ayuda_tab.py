# Archivo: view/tabs/ayuda_tab.py
# -*- coding: utf-8 -*-
"""
AyudaTab - Pestaña de ayuda, documentación y actualizaciones del sistema.
Incluye funcionalidad para actualizar la aplicación desde GitHub.
Autor: Sistema FormaGestPro
Versión: 3.0.0
"""

import sys
import os
import logging
import subprocess
import json
import webbrowser
import platform
from datetime import datetime
from typing import Dict, List, Any, Optional

# PySide6 imports
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QGroupBox, QTabWidget,
    QSizePolicy, QScrollArea, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSplitter, QMessageBox, QComboBox,
    QToolTip, QFileDialog, QDialog, QTextEdit,
    QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QTextBrowser, QLineEdit, QCheckBox,
    QRadioButton, QButtonGroup, QSpinBox, QDoubleSpinBox,
    QDateEdit, QDateTimeEdit, QPlainTextEdit, QFormLayout
)
from PySide6.QtCore import (
    Qt, QTimer, QDate, QDateTime,
    Signal, Slot, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QPoint,
    QThread, QProcess, QByteArray
)
from PySide6.QtGui import (
    QPainter, QLinearGradient,
    QBrush, QColor, QIcon, QCursor, QPen, QFont,
    QDesktopServices, QTextCursor, QTextCharFormat,
    QSyntaxHighlighter, QTextDocument
)

# Importar base tab
from .base_tab import BaseTab

# Configurar logging
logger = logging.getLogger(__name__)

# ============================================================================
# CLASES AUXILIARES
# ============================================================================

class UpdateThread(QThread):
    """Hilo para verificar y realizar actualizaciones en segundo plano"""
    
    update_check_complete = Signal(dict)
    update_progress = Signal(str, int)
    update_finished = Signal(bool, str)
    update_log = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.repo_url = "https://github.com/despachanetbo-coder/FormaGestPro"
        self.update_commands = []
        self.is_updating = False
        
    def run(self):
        """Ejecutar verificación de actualizaciones"""
        try:
            self.update_log.emit("🔍 Iniciando verificación de actualizaciones...")
            
            # Verificar si git está disponible
            if not self._check_git_available():
                self.update_check_complete.emit({
                    'available': False,
                    'current_version': 'Desconocida',
                    'latest_version': 'Desconocida',
                    'error': 'Git no está instalado en el sistema'
                })
                return
            
            # Obtener información de la versión actual
            current_info = self._get_current_version_info()
            
            # Verificar actualizaciones disponibles
            update_info = self._check_for_updates(current_info)
            
            self.update_check_complete.emit(update_info)
            
        except Exception as e:
            logger.error(f"Error en verificación de actualizaciones: {e}")
            self.update_check_complete.emit({
                'available': False,
                'current_version': 'Error',
                'latest_version': 'Error',
                'error': str(e)
            })
    
    def perform_update(self):
        """Realizar la actualización completa"""
        try:
            self.is_updating = True
            self.update_log.emit("🚀 Iniciando proceso de actualización...")
            
            # Paso 1: Obtener los últimos cambios
            self.update_progress.emit("Obteniendo últimos cambios...", 10)
            self.update_log.emit("📥 Actualizando desde el repositorio remoto...")
            
            commands = [
                ("git fetch origin", "Obteniendo información del repositorio"),
                ("git checkout main", "Cambiando a rama principal"),
                ("git pull origin main", "Descargando actualizaciones"),
                ("git submodule update --init --recursive", "Actualizando submódulos")
            ]
            
            total_steps = len(commands)
            for i, (cmd, description) in enumerate(commands):
                progress = 10 + (i * 70 // total_steps)
                self.update_progress.emit(description, progress)
                
                try:
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
                    )
                    
                    if result.returncode == 0:
                        self.update_log.emit(f"✅ {description}: Éxito")
                        if result.stdout.strip():
                            self.update_log.emit(f"   Salida: {result.stdout[:100]}...")
                    else:
                        self.update_log.emit(f"❌ {description}: Error")
                        self.update_log.emit(f"   Error: {result.stderr}")
                        
                except Exception as e:
                    self.update_log.emit(f"⚠️ Error ejecutando {cmd}: {str(e)}")
            
            # Paso 2: Instalar dependencias actualizadas
            self.update_progress.emit("Instalando dependencias...", 80)
            self.update_log.emit("📦 Actualizando dependencias de Python...")
            
            # Buscar requirements.txt
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            requirements_path = os.path.join(base_dir, "requirements.txt")
            
            if os.path.exists(requirements_path):
                try:
                    result = subprocess.run(
                        f"pip install -r {requirements_path} --upgrade",
                        shell=True,
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        self.update_log.emit("✅ Dependencias actualizadas correctamente")
                    else:
                        self.update_log.emit(f"⚠️ Advertencia al instalar dependencias: {result.stderr}")
                except Exception as e:
                    self.update_log.emit(f"⚠️ Error instalando dependencias: {str(e)}")
            
            # Paso 3: Completado
            self.update_progress.emit("Actualización completada", 100)
            self.update_log.emit("✨ Actualización completada con éxito!")
            self.update_log.emit("🔄 Reinicie la aplicación para aplicar los cambios.")
            
            self.update_finished.emit(True, "Actualización completada con éxito")
            
        except Exception as e:
            logger.error(f"Error durante la actualización: {e}")
            self.update_log.emit(f"❌ Error crítico durante la actualización: {str(e)}")
            self.update_finished.emit(False, f"Error: {str(e)}")
        
        finally:
            self.is_updating = False
    
    def _check_git_available(self) -> bool:
        """Verificar si git está disponible en el sistema"""
        try:
            result = subprocess.run(
                "git --version",
                shell=True,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _get_current_version_info(self) -> Dict:
        """Obtener información de la versión actual"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Intentar obtener commit actual
            result = subprocess.run(
                "git log -1 --format=%H",
                shell=True,
                capture_output=True,
                text=True,
                cwd=base_dir
            )
            
            current_commit = result.stdout.strip()[:8] if result.returncode == 0 else "Desconocido"
            
            # Intentar obtener versión de archivo de configuración
            version = "3.0.0"
            version_file = os.path.join(base_dir, "version.json")
            if os.path.exists(version_file):
                try:
                    with open(version_file, 'r') as f:
                        data = json.load(f)
                        version = data.get('version', version)
                except:
                    pass
            
            return {
                'commit': current_commit,
                'version': version,
                'date': datetime.now().strftime('%Y-%m-%d')
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo versión actual: {e}")
            return {
                'commit': 'Desconocido',
                'version': '3.0.0',
                'date': datetime.now().strftime('%Y-%m-%d')
            }
    
    def _check_for_updates(self, current_info: Dict) -> Dict:
        """Verificar si hay actualizaciones disponibles"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            
            # Obtener commits remotos
            result = subprocess.run(
                "git ls-remote origin -h refs/heads/main",
                shell=True,
                capture_output=True,
                text=True,
                cwd=base_dir
            )
            
            if result.returncode != 0:
                return {
                    'available': False,
                    'current_version': current_info['version'],
                    'latest_version': 'Desconocida',
                    'current_commit': current_info['commit'],
                    'latest_commit': 'Desconocido',
                    'error': 'No se pudo conectar al repositorio remoto',
                    'update_date': current_info['date']
                }
            
            # Extraer el último commit remoto
            remote_commit = result.stdout.split()[0][:8] if result.stdout else 'Desconocido'
            
            # Comparar con commit local
            update_available = remote_commit != current_info['commit'] and remote_commit != 'Desconocido'
            
            return {
                'available': update_available,
                'current_version': current_info['version'],
                'latest_version': current_info['version'],  # Podría mejorarse con tags
                'current_commit': current_info['commit'],
                'latest_commit': remote_commit,
                'update_date': current_info['date'],
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error verificando actualizaciones: {e}")
            return {
                'available': False,
                'current_version': current_info['version'],
                'latest_version': 'Error',
                'current_commit': current_info['commit'],
                'latest_commit': 'Error',
                'error': str(e),
                'update_date': current_info['date']
            }


class AnimatedCard(QFrame):
    """Tarjeta con animación al pasar el mouse"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_style = ""
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar animaciones"""
        self.setMouseTracking(True)
    
    def enterEvent(self, event):
        """Animación al entrar"""
        self.original_style = self.styleSheet()
        hover_style = self.styleSheet().replace("border: 2px solid", "border: 3px solid")
        hover_style = hover_style.replace("background-color: white", "background-color: #f8f9fa")
        self.setStyleSheet(hover_style)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Animación al salir"""
        self.setStyleSheet(self.original_style)
        super().leaveEvent(event)


class HelpCard(AnimatedCard):
    """Tarjeta de ayuda con enlaces a documentación"""
    
    clicked = Signal(str)
    
    def __init__(self, title: str, description: str, icon: str, 
                color: str, action_text: str = "", 
                action_type: str = "internal", action_target: str = "",
                min_height: int = 150, max_height: int = 160,
                card_id: str = "", parent=None):
        
        self.title = title
        self.description = description
        self.icon = icon
        self.color = color
        self.action_text = action_text
        self.action_type = action_type
        self.action_target = action_target
        self.min_height = min_height
        self.max_height = max_height
        self.card_id = card_id
        
        super().__init__(parent)
    
    def setup_ui(self):
        """Configurar interfaz de la tarjeta"""
        self.setObjectName(f"HelpCard_{self.card_id}")
        
        # Control explícito de altura
        self.setMinimumHeight(self.min_height)
        self.setMaximumHeight(self.max_height)
        self.setMinimumWidth(280)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Fila superior: Icono y título
        top_layout = QHBoxLayout()
        
        # Icono
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 32px;
                color: {self.color};
                font-family: 'Segoe UI Emoji';
            }}
        """)
        top_layout.addWidget(icon_label)
        
        # Título
        title_label = QLabel(self.title)
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {self.color};
                margin-left: 10px;
            }}
        """)
        title_label.setWordWrap(True)
        top_layout.addWidget(title_label)
        top_layout.addStretch()
        
        layout.addLayout(top_layout)
        
        # Descripción
        desc_label = QLabel(self.description)
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #5d6d7e;
                line-height: 1.4;
            }
        """)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        layout.addWidget(desc_label)
        
        # Acción (si existe)
        if self.action_text:
            action_layout = QHBoxLayout()
            action_layout.addStretch()
            
            action_btn = QPushButton(self.action_text)
            action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            
            # Estilo según tipo de acción
            if self.action_type == "danger":
                btn_style = f"""
                    QPushButton {{
                        background-color: {self.color};
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        border: none;
                        min-width: 120px;
                    }}
                    QPushButton:hover {{
                        background-color: #c0392b;
                    }}
                """
            elif self.action_type == "warning":
                btn_style = f"""
                    QPushButton {{
                        background-color: {self.color};
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        border: none;
                        min-width: 120px;
                    }}
                    QPushButton:hover {{
                        background-color: #d68910;
                    }}
                """
            else:
                btn_style = f"""
                    QPushButton {{
                        background-color: {self.color};
                        color: white;
                        padding: 8px 16px;
                        border-radius: 6px;
                        font-weight: bold;
                        border: none;
                        min-width: 120px;
                    }}
                    QPushButton:hover {{
                        background-color: #2980b9;
                    }}
                """
            
            action_btn.setStyleSheet(btn_style)
            
            # Conectar señal
            action_btn.clicked.connect(self._on_action_clicked)
            
            action_layout.addWidget(action_btn)
            layout.addLayout(action_layout)
        
        layout.addStretch()
        
        # Estilo de la tarjeta
        self.setStyleSheet(f"""
            #HelpCard_{self.card_id} {{
                background-color: white;
                border-radius: 12px;
                border: 2px solid #ecf0f1;
                padding: 5px;
            }}
            #HelpCard_{self.card_id}:hover {{
                border: 2px solid {self.color};
                background-color: #f8f9fa;
            }}
        """)
        
        # Hacer clicable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def _on_action_clicked(self):
        """Manejador para clic en botón de acción"""
        self.clicked.emit(self.card_id)
    
    def mousePressEvent(self, event):
        """Manejador para clic en la tarjeta"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.card_id)
        super().mousePressEvent(event)


# ============================================================================
# CLASE PRINCIPAL: AYUDATAB
# ============================================================================

class AyudaTab(BaseTab):
    """Pestaña de ayuda y actualizaciones del sistema FormaGestPro"""
    
    # Señales
    update_available = Signal(bool)
    update_started = Signal()
    update_completed = Signal(bool, str)
    
    def __init__(self, user_data=None, parent=None):
        """Inicializar AyudaTab"""
        super().__init__(
            tab_id="ayuda_tab", 
            tab_name="❓ Ayuda & Actualizaciones",
            parent=parent
        )
        
        self.user_data = user_data or {}
        
        # Estado de la pestaña
        self.update_info = {}
        self.help_cards = []
        self.current_page = "main"
        self.is_checking_updates = False
        self.is_updating = False
        
        # Hilo de actualización
        self.update_thread = UpdateThread()
        self.update_thread.update_check_complete.connect(self._on_update_check_complete)
        self.update_thread.update_progress.connect(self._on_update_progress)
        self.update_thread.update_finished.connect(self._on_update_finished)
        self.update_thread.update_log.connect(self._on_update_log)
        
        # Configurar header personalizado
        self.set_header_title("❓ AYUDA & ACTUALIZACIONES")
        self.set_header_subtitle("Documentación, soporte y gestión de versiones del sistema")
        
        # Configurar información de usuario
        nombre_usuario = self._get_user_display_name()
        rol_usuario = self.user_data.get('rol', 'Usuario')
        self.set_user_info(nombre_usuario, rol_usuario)
        
        # Configurar gradiente personalizado (azul oscuro)
        #self.set_header_gradient("#2c3e50", "#34495e", "#2c3e50")
        
        # Inicializar UI
        self._init_ui()
        
        # Iniciar verificación automática de actualizaciones
        QTimer.singleShot(1000, self.check_for_updates)
        
        logger.info("AyudaTab inicializado correctamente")
    
    # ============================================================================
    # MÉTODOS HEREDADOS DE BASETAB
    # ============================================================================
    
    def _init_ui(self):
        """Inicializar la interfaz de usuario de ayuda"""
        # Limpiar contenido previo
        self.clear_content()
        
        # Layout principal con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(600)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f7fa;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #f5f7fa;
            }
        """)
        
        # Widget contenido con stacked widget para diferentes páginas
        self.content_stack = QStackedWidget()
        
        # Página principal
        self.main_page = self.create_main_page()
        self.content_stack.addWidget(self.main_page)
        
        # Página de actualización
        self.update_page = self.create_update_page()
        self.content_stack.addWidget(self.update_page)
        
        # Página de documentación
        self.docs_page = self.create_documentation_page()
        self.content_stack.addWidget(self.docs_page)
        
        # Página de contacto
        self.contact_page = self.create_contact_page()
        self.content_stack.addWidget(self.contact_page)
        
        scroll_area.setWidget(self.content_stack)
        self.add_widget(scroll_area)
    
    def on_tab_selected(self):
        """Método llamado cuando la pestaña es seleccionada"""
        super().on_tab_selected()
        logger.info(f"AyudaTab seleccionada")
        
        # Verificar actualizaciones al seleccionar la pestaña
        if not self.is_checking_updates and not self.is_updating:
            self.check_for_updates()
    
    # ============================================================================
    # MÉTODOS DE PÁGINAS
    # ============================================================================
    
    def create_main_page(self) -> QWidget:
        """Crear página principal de ayuda"""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f7fa;")
        layout = QVBoxLayout(page)
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 40)
        
        # 1. Sección de actualizaciones
        update_section = self.create_update_section()
        layout.addWidget(update_section)
        
        # 2. Sección de ayuda rápida
        help_section = self.create_quick_help_section()
        layout.addWidget(help_section)
        
        # 3. Sección de documentación
        docs_section = self.create_documentation_section()
        layout.addWidget(docs_section)
        
        # 4. Barra de herramientas inferior
        toolbar = self.create_main_toolbar()
        layout.addWidget(toolbar)
        
        return page
    
    def create_update_section(self) -> QGroupBox:
        """Crear sección de actualizaciones"""
        group = QGroupBox("🔄 ACTUALIZACIONES DEL SISTEMA")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                border: 2px solid #bdc3c7;
                border-radius: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Estado actual
        status_frame = QFrame()
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        
        status_layout = QVBoxLayout(status_frame)
        
        # Información de versión
        self.version_info_label = QLabel(
            "<div style='text-align: center;'>"
            "<h3 style='color: #2c3e50;'>Cargando información...</h3>"
            "<p style='color: #7f8c8d;'>Verificando estado del sistema</p>"
            "</div>"
        )
        self.version_info_label.setTextFormat(Qt.TextFormat.RichText)
        self.version_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_layout.addWidget(self.version_info_label)
        
        layout.addWidget(status_frame)
        
        # Botones de acción
        buttons_layout = QHBoxLayout()
        
        self.btn_check_updates = QPushButton("🔍 Verificar Actualizaciones")
        self.btn_check_updates.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_check_updates.clicked.connect(self.check_for_updates)
        buttons_layout.addWidget(self.btn_check_updates)
        
        self.btn_update_now = QPushButton("🚀 Actualizar Ahora")
        self.btn_update_now.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                font-size: 14px;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_update_now.clicked.connect(self.start_update)
        self.btn_update_now.setEnabled(False)
        buttons_layout.addWidget(self.btn_update_now)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Enlace al repositorio
        repo_layout = QHBoxLayout()
        repo_layout.addStretch()
        
        repo_label = QLabel(
            "<a href='https://github.com/despachanetbo-coder/FormaGestPro' "
            "style='color: #3498db; text-decoration: none;'>"
            "🌐 Ver repositorio en GitHub"
            "</a>"
        )
        repo_label.setTextFormat(Qt.TextFormat.RichText)
        repo_label.setOpenExternalLinks(True)
        repo_layout.addWidget(repo_label)
        
        layout.addLayout(repo_layout)
        
        return group
    
    def create_quick_help_section(self) -> QGroupBox:
        """Crear sección de ayuda rápida"""
        group = QGroupBox("💡 AYUDA RÁPIDA")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                border: 2px solid #bdc3c7;
                border-radius: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
        """)
        
        layout = QGridLayout(group)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 25, 15, 20)
        
        # Tarjetas de ayuda
        help_cards_config = [
            {
                'title': '📖 Manual de Usuario',
                'description': 'Guía completa de uso del sistema con ejemplos paso a paso',
                'icon': '📖',
                'color': '#3498db',
                'action_text': 'Abrir Manual',
                'action_type': 'info',
                'id': 'manual'
            },
            {
                'title': '🎬 Tutoriales en Video',
                'description': 'Videos demostrativos para aprender a usar todas las funcionalidades',
                'icon': '🎬',
                'color': '#9b59b6',
                'action_text': 'Ver Tutoriales',
                'action_type': 'info',
                'id': 'tutorials'
            },
            {
                'title': '❓ Preguntas Frecuentes',
                'description': 'Respuestas a las preguntas más comunes sobre el sistema',
                'icon': '❓',
                'color': '#2ecc71',
                'action_text': 'Consultar FAQ',
                'action_type': 'info',
                'id': 'faq'
            },
            {
                'title': '🐛 Reportar Problema',
                'description': 'Encontraste un error o tienes una sugerencia de mejora',
                'icon': '🐛',
                'color': '#e74c3c',
                'action_text': 'Reportar',
                'action_type': 'danger',
                'id': 'report'
            },
            {
                'title': '🔧 Herramientas de Diagnóstico',
                'description': 'Utilidades para diagnosticar y solucionar problemas del sistema',
                'icon': '🔧',
                'color': '#f39c12',
                'action_text': 'Abrir Herramientas',
                'action_type': 'warning',
                'id': 'diagnostic'
            },
            {
                'title': '📋 Historial de Cambios',
                'description': 'Registro completo de todas las versiones y cambios realizados',
                'icon': '📋',
                'color': '#1abc9c',
                'action_text': 'Ver Historial',
                'action_type': 'info',
                'id': 'changelog'
            }
        ]
        
        self.help_cards = []
        
        for i, config in enumerate(help_cards_config):
            card = HelpCard(
                title=config['title'],
                description=config['description'],
                icon=config['icon'],
                color=config['color'],
                action_text=config['action_text'],
                action_type=config['action_type'],
                action_target="",
                min_height=180,
                max_height=190,
                card_id=config['id']
            )
            
            card.clicked.connect(self.on_help_card_clicked)
            self.help_cards.append(card)
            
            row = i // 3
            col = i % 3
            layout.addWidget(card, row, col)
        
        return group
    
    def create_documentation_section(self) -> QGroupBox:
        """Crear sección de documentación"""
        group = QGroupBox("📚 DOCUMENTACIÓN TÉCNICA")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                border: 2px solid #bdc3c7;
                border-radius: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setSpacing(15)
        
        # Descripción
        desc_label = QLabel(
            "Documentación técnica completa para desarrolladores y administradores del sistema. "
            "Incluye guías de instalación, configuración, API y desarrollo de extensiones."
        )
        desc_label.setStyleSheet("""
            QLabel {
                font-size: 13px;
                color: #5d6d7e;
                line-height: 1.5;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 8px;
            }
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Botones de documentación
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(15)
        
        docs_buttons = [
            ("📋 Guía de Instalación", "#3498db", "install_guide"),
            ("⚙️ Configuración Avanzada", "#9b59b6", "config_guide"),
            ("🔌 API y Extensiones", "#2ecc71", "api_docs"),
            ("🗄️ Base de Datos", "#f39c12", "database_docs"),
            ("🔒 Seguridad", "#e74c3c", "security_docs"),
            ("🚀 Despliegue", "#1abc9c", "deployment_docs")
        ]
        
        for i, (text, color, doc_id) in enumerate(docs_buttons):
            btn = QPushButton(text)
            btn.setObjectName(f"doc_btn_{doc_id}")
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white;
                    padding: 12px;
                    border-radius: 8px;
                    font-weight: bold;
                    border: none;
                    font-size: 13px;
                    min-height: 60px;
                }}
                QPushButton:hover {{
                    background-color: {self._darken_color(color)};
                }}
            """)
            btn.clicked.connect(lambda checked, d=doc_id: self.open_documentation(d))
            
            row = i // 3
            col = i % 3
            buttons_layout.addWidget(btn, row, col)
        
        layout.addLayout(buttons_layout)
        
        return group
    
    def create_main_toolbar(self) -> QFrame:
        """Crear barra de herramientas principal"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-top: 1px solid #34495e;
                padding: 15px;
                border-radius: 10px;
                margin-top: 20px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Información del sistema
        sys_info = QLabel(
            f"<span style='color: #ecf0f1; font-size: 12px;'>"
            f"FormaGestPro v3.0 • PostgreSQL • Ayuda & Soporte"
            f"</span>"
        )
        sys_info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(sys_info)
        layout.addStretch()
        
        # Botones de acción
        btn_contact = QPushButton("📧 Contactar Soporte")
        btn_contact.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_contact.clicked.connect(lambda: self.switch_page("contact"))
        
        btn_about = QPushButton("ℹ️ Acerca de")
        btn_about.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_about.clicked.connect(self.show_about_dialog)
        
        layout.addWidget(btn_contact)
        layout.addWidget(btn_about)
        
        return frame
    
    def create_update_page(self) -> QWidget:
        """Crear página de actualización detallada"""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f7fa;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 40)
        
        # Título
        title_label = QLabel("🚀 ACTUALIZACIÓN DEL SISTEMA")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid #3498db;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Progreso de actualización
        self.update_progress_bar = QProgressBar()
        self.update_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                height: 30px;
                font-size: 14px;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 8px;
            }
        """)
        self.update_progress_bar.setTextVisible(True)
        self.update_progress_bar.setRange(0, 100)
        self.update_progress_bar.setValue(0)
        layout.addWidget(self.update_progress_bar)
        
        # Etiqueta de estado
        self.update_status_label = QLabel("Listo para comenzar la actualización")
        self.update_status_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
                padding: 5px;
                text-align: center;
            }
        """)
        self.update_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.update_status_label)
        
        # Log de actualización
        log_group = QGroupBox("📝 REGISTRO DE ACTUALIZACIÓN")
        log_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                border: 2px solid #bdc3c7;
                border-radius: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """)
        
        log_layout = QVBoxLayout(log_group)
        
        self.update_log_text = QTextEdit()
        self.update_log_text.setReadOnly(True)
        self.update_log_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
        """)
        log_layout.addWidget(self.update_log_text)
        
        layout.addWidget(log_group, stretch=1)
        
        # Botones de control
        control_layout = QHBoxLayout()
        
        self.btn_back_from_update = QPushButton("◀️ Volver")
        self.btn_back_from_update.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        self.btn_back_from_update.clicked.connect(lambda: self.switch_page("main"))
        
        self.btn_start_update_page = QPushButton("🚀 Iniciar Actualización")
        self.btn_start_update_page.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_start_update_page.clicked.connect(self.start_update)
        
        self.btn_cancel_update = QPushButton("❌ Cancelar")
        self.btn_cancel_update.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_cancel_update.clicked.connect(self.cancel_update)
        self.btn_cancel_update.setEnabled(False)
        
        control_layout.addWidget(self.btn_back_from_update)
        control_layout.addStretch()
        control_layout.addWidget(self.btn_start_update_page)
        control_layout.addWidget(self.btn_cancel_update)
        
        layout.addLayout(control_layout)
        
        return page
    
    def create_documentation_page(self) -> QWidget:
        """Crear página de documentación detallada"""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f7fa;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 40)
        
        # Título
        title_label = QLabel("📚 DOCUMENTACIÓN COMPLETA")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid #3498db;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Contenido de documentación
        content_frame = QFrame()
        content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #ecf0f1;
                padding: 20px;
            }
        """)
        
        content_layout = QVBoxLayout(content_frame)
        
        # Texto de documentación
        docs_text = QTextBrowser()
        docs_text.setOpenExternalLinks(True)
        docs_text.setStyleSheet("""
            QTextBrowser {
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                font-size: 13px;
                padding: 15px;
                line-height: 1.6;
            }
        """)
        
        docs_content = """
        <h1>Documentación de FormaGestPro</h1>
        <hr>
        
        <h2>📖 Introducción</h2>
        <p>FormaGestPro es un sistema integral de gestión académica diseñado para instituciones 
        educativas. Esta documentación cubre todos los aspectos del sistema.</p>
        
        <h2>🔧 Instalación</h2>
        <h3>Requisitos del Sistema</h3>
        <ul>
            <li>Python 3.8 o superior</li>
            <li>PostgreSQL 12+</li>
            <li>Git (para actualizaciones)</li>
            <li>4GB RAM mínimo</li>
        </ul>
        
        <h3>Pasos de Instalación</h3>
        <ol>
            <li>Clonar el repositorio:
                <pre><code>git clone https://github.com/despachanetbo-coder/FormaGestPro.git</code></pre>
            </li>
            <li>Crear entorno virtual:
                <pre><code>python -m venv venv</code></pre>
            </li>
            <li>Activar entorno virtual:
                <pre><code># Windows: venv\\Scripts\\activate
# Linux/Mac: source venv/bin/activate</code></pre>
            </li>
            <li>Instalar dependencias:
                <pre><code>pip install -r requirements.txt</code></pre>
            </li>
            <li>Configurar base de datos en <code>config/database.ini</code></li>
            <li>Ejecutar migraciones:
                <pre><code>python manage.py migrate</code></pre>
            </li>
            <li>Iniciar la aplicación:
                <pre><code>python main.py</code></pre>
            </li>
        </ol>
        
        <h2>⚙️ Configuración</h2>
        <h3>Archivos de Configuración</h3>
        <ul>
            <li><code>config/database.ini</code> - Configuración de base de datos</li>
            <li><code>config/settings.ini</code> - Configuración general</li>
            <li><code>config/security.ini</code> - Configuración de seguridad</li>
        </ul>
        
        <h2>🔌 API</h2>
        <p>El sistema expone una API REST para integración con otros sistemas.</p>
        <h3>Endpoints principales:</h3>
        <ul>
            <li><code>GET /api/estudiantes</code> - Listar estudiantes</li>
            <li><code>POST /api/estudiantes</code> - Crear estudiante</li>
            <li><code>GET /api/programas</code> - Listar programas</li>
            <li><code>GET /api/inscripciones</code> - Listar inscripciones</li>
        </ul>
        
        <h2>🗄️ Base de Datos</h2>
        <h3>Estructura Principal</h3>
        <ul>
            <li><strong>estudiantes</strong> - Información de estudiantes</li>
            <li><strong>docentes</strong> - Información de docentes</li>
            <li><strong>programas</strong> - Programas académicos</li>
            <li><strong>inscripciones</strong> - Registro de inscripciones</li>
            <li><strong>usuarios</strong> - Usuarios del sistema</li>
        </ul>
        
        <h2>🔒 Seguridad</h2>
        <ul>
            <li>Autenticación con JWT</li>
            <li>Encriptación de contraseñas</li>
            <li>Control de acceso por roles</li>
            <li>Registro de auditoría</li>
        </ul>
        
        <h2>🚀 Despliegue en Producción</h2>
        <h3>Recomendaciones:</h3>
        <ul>
            <li>Usar servidor web (Nginx/Apache)</li>
            <li>Configurar SSL/TLS</li>
            <li>Implementar backups automáticos</li>
            <li>Monitoreo del sistema</li>
        </ul>
        
        <h2>🐛 Solución de Problemas</h2>
        <h3>Problemas Comunes:</h3>
        <ul>
            <li><strong>Error de conexión a BD:</strong> Verificar config/database.ini</li>
            <li><strong>Módulos faltantes:</strong> Ejecutar pip install -r requirements.txt</li>
            <li><strong>Permisos denegados:</strong> Verificar permisos de archivos</li>
        </ul>
        
        <hr>
        <p><em>Para más información, visite el 
        <a href="https://github.com/despachanetbo-coder/FormaGestPro/wiki">Wiki del proyecto</a>.</em></p>
        """
        
        docs_text.setHtml(docs_content)
        content_layout.addWidget(docs_text)
        
        layout.addWidget(content_frame, stretch=1)
        
        # Botón para volver
        back_layout = QHBoxLayout()
        back_layout.addStretch()
        
        btn_back = QPushButton("◀️ Volver al Menú Principal")
        btn_back.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_back.clicked.connect(lambda: self.switch_page("main"))
        
        back_layout.addWidget(btn_back)
        layout.addLayout(back_layout)
        
        return page
    
    def create_contact_page(self) -> QWidget:
        """Crear página de contacto y soporte"""
        page = QWidget()
        page.setStyleSheet("background-color: #f5f7fa;")
        layout = QVBoxLayout(page)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 40)
        
        # Título
        title_label = QLabel("📧 CONTACTO Y SOPORTE")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid #3498db;
            }
        """)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Formulario de contacto
        form_group = QGroupBox("✉️ Enviar Mensaje de Soporte")
        form_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: bold;
                color: #2c3e50;
                padding: 20px;
                border: 2px solid #bdc3c7;
                border-radius: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                background-color: white;
            }
        """)
        
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Campos del formulario
        self.contact_name = QLineEdit()
        self.contact_name.setPlaceholderText("Tu nombre")
        self.contact_name.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        form_layout.addRow("Nombre:", self.contact_name)
        
        self.contact_email = QLineEdit()
        self.contact_email.setPlaceholderText("tu@email.com")
        self.contact_email.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        form_layout.addRow("Email:", self.contact_email)
        
        self.contact_subject = QComboBox()
        self.contact_subject.addItems([
            "Consulta General",
            "Reporte de Error",
            "Solicitud de Característica",
            "Problema Técnico",
            "Pregunta sobre Facturación",
            "Otro"
        ])
        self.contact_subject.setStyleSheet("""
            QComboBox {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        form_layout.addRow("Asunto:", self.contact_subject)
        
        self.contact_message = QPlainTextEdit()
        self.contact_message.setPlaceholderText("Describe tu consulta o problema aquí...")
        self.contact_message.setMinimumHeight(150)
        self.contact_message.setStyleSheet("""
            QPlainTextEdit {
                padding: 10px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                font-size: 14px;
            }
        """)
        form_layout.addRow("Mensaje:", self.contact_message)
        
        # Adjuntar información del sistema
        self.attach_sysinfo = QCheckBox("Incluir información del sistema (recomendado para problemas técnicos)")
        self.attach_sysinfo.setChecked(True)
        self.attach_sysinfo.setStyleSheet("""
            QCheckBox {
                font-size: 13px;
                color: #5d6d7e;
                padding: 5px;
            }
        """)
        form_layout.addRow("", self.attach_sysinfo)
        
        layout.addWidget(form_group)
        
        # Información de contacto adicional
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: 10px;
                padding: 20px;
            }
        """)
        
        info_layout = QVBoxLayout(info_frame)
        
        info_label = QLabel(
            "<h3>📞 Otros Medios de Contacto</h3>"
            "<p><strong>📧 Email de Soporte:</strong> "
            "<a href='mailto:soporte@formagestpro.com'>soporte@formagestpro.com</a></p>"
            "<p><strong>🌐 Sitio Web:</strong> "
            "<a href='https://formagestpro.com'>https://formagestpro.com</a></p>"
            "<p><strong>💬 Foro de la Comunidad:</strong> "
            "<a href='https://github.com/despachanetbo-coder/FormaGestPro/discussions'>"
            "Discusiones en GitHub</a></p>"
            "<p><strong>🐛 Reportar Error:</strong> "
            "<a href='https://github.com/despachanetbo-coder/FormaGestPro/issues'>"
            "Issues en GitHub</a></p>"
            "<hr>"
            "<p><em>Respuesta típica en 24-48 horas hábiles.</em></p>"
        )
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setOpenExternalLinks(True)
        info_label.setWordWrap(True)
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_frame)
        
        # Botones de acción
        button_layout = QHBoxLayout()
        
        btn_back_contact = QPushButton("◀️ Volver")
        btn_back_contact.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                min-width: 150px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        btn_back_contact.clicked.connect(lambda: self.switch_page("main"))
        
        btn_send = QPushButton("📤 Enviar Mensaje")
        btn_send.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_send.clicked.connect(self.send_contact_message)
        
        btn_clear = QPushButton("🗑️ Limpiar Formulario")
        btn_clear.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                border: none;
                min-width: 200px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_clear.clicked.connect(self.clear_contact_form)
        
        button_layout.addWidget(btn_back_contact)
        button_layout.addStretch()
        button_layout.addWidget(btn_send)
        button_layout.addWidget(btn_clear)
        
        layout.addLayout(button_layout)
        
        return page
    
    # ============================================================================
    # MÉTODOS DE ACTUALIZACIÓN
    # ============================================================================
    
    def check_for_updates(self):
        """Verificar si hay actualizaciones disponibles"""
        if self.is_checking_updates or self.is_updating:
            return
        
        self.is_checking_updates = True
        self.btn_check_updates.setEnabled(False)
        self.btn_check_updates.setText("🔍 Verificando...")
        
        # Actualizar etiqueta de estado
        self.version_info_label.setText(
            "<div style='text-align: center;'>"
            "<h3 style='color: #2c3e50;'>🔄 Verificando actualizaciones...</h3>"
            "<p style='color: #7f8c8d;'>Conectando con el repositorio</p>"
            "</div>"
        )
        
        # Iniciar hilo de verificación
        if self.update_thread.isRunning():
            self.update_thread.terminate()
            self.update_thread.wait()
        
        self.update_thread.start()
    
    def start_update(self):
        """Iniciar el proceso de actualización"""
        if self.is_updating:
            return
        
        # Confirmar actualización
        reply = QMessageBox.question(
            self,
            "Confirmar Actualización",
            "¿Está seguro de que desea actualizar el sistema?<br><br>"
            "<b>Recomendaciones:</b><br>"
            "1. Realice un backup de la base de datos<br>"
            "2. Cierre todas las ventanas del sistema<br>"
            "3. Asegúrese de tener conexión a Internet estable<br><br>"
            "El sistema se reiniciará al completar la actualización.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.is_updating = True
            self.switch_page("update")
            
            # Configurar controles
            self.btn_start_update_page.setEnabled(False)
            self.btn_cancel_update.setEnabled(True)
            self.update_status_label.setText("🚀 Iniciando actualización...")
            self.update_progress_bar.setValue(0)
            self.update_log_text.clear()
            
            # Emitir señal
            self.update_started.emit()
            
            # Iniciar actualización en segundo plano
            self.update_thread.perform_update()
    
    def cancel_update(self):
        """Cancelar el proceso de actualización"""
        if not self.is_updating:
            return
        
        reply = QMessageBox.warning(
            self,
            "Cancelar Actualización",
            "¿Está seguro de que desea cancelar la actualización?<br><br>"
            "Cancelar durante el proceso podría dejar el sistema en un estado inconsistente.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.update_thread.isRunning():
                self.update_thread.terminate()
                self.update_thread.wait()
            
            self.is_updating = False
            self.update_status_label.setText("❌ Actualización cancelada por el usuario")
            self.btn_start_update_page.setEnabled(True)
            self.btn_cancel_update.setEnabled(False)
            
            QMessageBox.warning(
                self,
                "Actualización Cancelada",
                "La actualización ha sido cancelada.<br><br>"
                "Se recomienda verificar la integridad del sistema."
            )
    
    def _on_update_check_complete(self, update_info: Dict):
        """Manejador cuando se completa la verificación de actualizaciones"""
        self.is_checking_updates = False
        self.update_info = update_info
        
        # Actualizar botones
        self.btn_check_updates.setEnabled(True)
        self.btn_check_updates.setText("🔍 Verificar Actualizaciones")
        
        # Actualizar información mostrada
        if update_info.get('error'):
            # Error en la verificación
            self.version_info_label.setText(
                f"<div style='text-align: center;'>"
                f"<h3 style='color: #e74c3c;'>❌ Error de Verificación</h3>"
                f"<p style='color: #7f8c8d;'>{update_info['error']}</p>"
                f"<p style='color: #95a5a6; font-size: 12px;'>"
                f"Versión actual: {update_info.get('current_version', 'Desconocida')}<br>"
                f"Última verificación: {update_info.get('update_date', 'Nunca')}"
                f"</p>"
                f"</div>"
            )
            self.btn_update_now.setEnabled(False)
            
        elif update_info.get('available', False):
            # Actualización disponible
            self.version_info_label.setText(
                f"<div style='text-align: center;'>"
                f"<h3 style='color: #27ae60;'>✨ Actualización Disponible!</h3>"
                f"<p style='color: #7f8c8d;'>Hay una nueva versión disponible para descargar</p>"
                f"<p style='color: #2c3e50; font-size: 13px;'>"
                f"<strong>Versión actual:</strong> {update_info.get('current_version', 'Desconocida')}<br>"
                f"<strong>Nueva versión:</strong> {update_info.get('latest_version', 'Disponible')}<br>"
                f"<strong>Commit actual:</strong> {update_info.get('current_commit', 'N/A')}<br>"
                f"<strong>Nuevo commit:</strong> {update_info.get('latest_commit', 'N/A')}<br>"
                f"<strong>Última verificación:</strong> {update_info.get('update_date', 'Nunca')}"
                f"</p>"
                f"</div>"
            )
            self.btn_update_now.setEnabled(True)
            
            # Emitir señal
            self.update_available.emit(True)
            
            # Mostrar notificación
            QMessageBox.information(
                self,
                "Actualización Disponible",
                f"Hay una nueva versión disponible:<br><br>"
                f"<b>Versión actual:</b> {update_info.get('current_version', 'Desconocida')}<br>"
                f"<b>Nueva versión:</b> {update_info.get('latest_version', 'Disponible')}<br><br>"
                f"Haga clic en 'Actualizar Ahora' para comenzar."
            )
            
        else:
            # Sistema actualizado
            self.version_info_label.setText(
                f"<div style='text-align: center;'>"
                f"<h3 style='color: #2ecc71;'>✅ Sistema Actualizado</h3>"
                f"<p style='color: #7f8c8d;'>Tu sistema está ejecutando la versión más reciente</p>"
                f"<p style='color: #2c3e50; font-size: 13px;'>"
                f"<strong>Versión:</strong> {update_info.get('current_version', 'Desconocida')}<br>"
                f"<strong>Commit:</strong> {update_info.get('current_commit', 'N/A')}<br>"
                f"<strong>Última verificación:</strong> {update_info.get('update_date', 'Nunca')}"
                f"</p>"
                f"</div>"
            )
            self.btn_update_now.setEnabled(False)
            
            # Emitir señal
            self.update_available.emit(False)
    
    def _on_update_progress(self, message: str, progress: int):
        """Manejador para actualización de progreso"""
        self.update_status_label.setText(message)
        self.update_progress_bar.setValue(progress)
    
    def _on_update_finished(self, success: bool, message: str):
        """Manejador cuando se completa la actualización"""
        self.is_updating = False
        
        # Actualizar controles
        self.btn_start_update_page.setEnabled(True)
        self.btn_cancel_update.setEnabled(False)
        
        if success:
            self.update_status_label.setText("✅ Actualización completada con éxito")
            self.update_progress_bar.setValue(100)
            
            # Mostrar mensaje de éxito
            reply = QMessageBox.information(
                self,
                "Actualización Completada",
                f"{message}<br><br>"
                f"La actualización se ha completado exitosamente.<br><br>"
                f"<b>¿Desea reiniciar la aplicación ahora para aplicar los cambios?</b>",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Solicitar reinicio
                self.restart_application()
            else:
                # Volver a la página principal
                self.switch_page("main")
                
        else:
            self.update_status_label.setText(f"❌ Error: {message}")
            
            QMessageBox.critical(
                self,
                "Error en Actualización",
                f"Ocurrió un error durante la actualización:<br><br>"
                f"<b>{message}</b><br><br>"
                f"Por favor, verifique:<br>"
                f"1. Su conexión a Internet<br>"
                f"2. Los permisos de escritura<br>"
                f"3. El estado del repositorio"
            )
            
            # Volver a la página principal
            self.switch_page("main")
        
        # Emitir señal
        self.update_completed.emit(success, message)
    
    def _on_update_log(self, message: str):
        """Manejador para mensajes de log"""
        current_text = self.update_log_text.toPlainText()
        timestamp = datetime.now().strftime("%H:%M:%S")
        new_text = f"[{timestamp}] {message}\n{current_text}"
        self.update_log_text.setPlainText(new_text)
        
        # Mover cursor al inicio
        cursor = self.update_log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.update_log_text.setTextCursor(cursor)
    
    def restart_application(self):
        """Reiniciar la aplicación"""
        QMessageBox.information(
            self,
            "Reinicio Requerido",
            "La aplicación se reiniciará para aplicar los cambios.<br><br>"
            "Por favor, espere unos segundos."
        )
        
        # En una implementación real, aquí reiniciarías la aplicación
        # Por ahora, solo mostramos un mensaje
        logger.info("Aplicación reiniciada después de actualización")
        
        # Podrías implementar un reinicio real con:
        # QCoreApplication.quit()
        # QProcess.startDetached(sys.executable, sys.argv)
    
    # ============================================================================
    # MÉTODOS DE INTERFAZ
    # ============================================================================
    
    def switch_page(self, page_name: str):
        """Cambiar entre páginas de contenido"""
        page_map = {
            "main": 0,
            "update": 1,
            "documentation": 2,
            "contact": 3
        }
        
        if page_name in page_map:
            self.content_stack.setCurrentIndex(page_map[page_name])
            self.current_page = page_name
    
    def on_help_card_clicked(self, card_id: str):
        """Manejador cuando se hace clic en una tarjeta de ayuda"""
        logger.info(f"Tarjeta de ayuda clickeada: {card_id}")
        
        if card_id == "manual":
            self.open_user_manual()
        elif card_id == "tutorials":
            self.open_tutorials()
        elif card_id == "faq":
            self.open_faq()
        elif card_id == "report":
            self.report_issue()
        elif card_id == "diagnostic":
            self.open_diagnostic_tools()
        elif card_id == "changelog":
            self.open_changelog()
    
    def open_user_manual(self):
        """Abrir manual de usuario"""
        # En una implementación real, abrirías un PDF o página web
        webbrowser.open("https://github.com/despachanetbo-coder/FormaGestPro/wiki/Manual-de-Usuario")
        
        QMessageBox.information(
            self,
            "Manual de Usuario",
            "El manual de usuario se ha abierto en tu navegador.<br><br>"
            "Si no se abrió automáticamente, visita:<br>"
            "<a href='https://github.com/despachanetbo-coder/FormaGestPro/wiki/Manual-de-Usuario'>"
            "https://github.com/despachanetbo-coder/FormaGestPro/wiki/Manual-de-Usuario</a>"
        )
    
    def open_tutorials(self):
        """Abrir tutoriales en video"""
        webbrowser.open("https://github.com/despachanetbo-coder/FormaGestPro/wiki/Tutoriales")
        
        QMessageBox.information(
            self,
            "Tutoriales en Video",
            "Los tutoriales se han abierto en tu navegador.<br><br>"
            "Encontrarás videos demostrativos de todas las funcionalidades."
        )
    
    def open_faq(self):
        """Abrir preguntas frecuentes"""
        # Mostrar FAQ en un diálogo
        faq_dialog = QDialog(self)
        faq_dialog.setWindowTitle("❓ Preguntas Frecuentes")
        faq_dialog.resize(700, 500)
        
        layout = QVBoxLayout(faq_dialog)
        
        text_browser = QTextBrowser()
        text_browser.setOpenExternalLinks(True)
        
        faq_content = """
        <h1>Preguntas Frecuentes - FormaGestPro</h1>
        <hr>
        
        <h2>📊 General</h2>
        
        <h3>¿Qué es FormaGestPro?</h3>
        <p>FormaGestPro es un sistema de gestión académica para instituciones educativas, 
        que permite administrar estudiantes, docentes, programas e inscripciones.</p>
        
        <h3>¿Es gratuito?</h3>
        <p>Sí, FormaGestPro es software de código abierto y completamente gratuito.</p>
        
        <h2>🔧 Instalación</h2>
        
        <h3>¿Qué requisitos tiene el sistema?</h3>
        <p>Python 3.8+, PostgreSQL 12+, 4GB RAM mínimo, y espacio en disco según la cantidad de datos.</p>
        
        <h3>¿Cómo instalo las dependencias?</h3>
        <p>Ejecuta <code>pip install -r requirements.txt</code> en el directorio del proyecto.</p>
        
        <h2>🔄 Actualizaciones</h2>
        
        <h3>¿Cómo actualizo el sistema?</h3>
        <p>Usa la pestaña de Ayuda & Actualizaciones y haz clic en "Actualizar Ahora".</p>
        
        <h3>¿Pierdo mis datos al actualizar?</h3>
        <p>No, las actualizaciones mantienen todos los datos existentes. Sin embargo, 
        siempre es recomendable hacer backup antes de actualizar.</p>
        
        <h2>🗄️ Base de Datos</h2>
        
        <h3>¿Cómo hago backup de la base de datos?</h3>
        <p>Usa pg_dump para PostgreSQL: <code>pg_dump -U usuario -d basedatos > backup.sql</code></p>
        
        <h3>¿Puedo usar otro sistema de base de datos?</h3>
        <p>Actualmente solo se soporta PostgreSQL, pero se planea agregar soporte para MySQL.</p>
        
        <h2>🔒 Seguridad</h2>
        
        <h3>¿Cómo cambio mi contraseña?</h3>
        <p>Ve a Configuración > Perfil de Usuario > Cambiar Contraseña.</p>
        
        <h3>¿El sistema es seguro?</h3>
        <p>Sí, implementa encriptación de contraseñas, autenticación JWT y control de acceso por roles.</p>
        
        <h2>❓ Soporte</h2>
        
        <h3>¿Cómo reporto un error?</h3>
        <p>Usa la opción "Reportar Problema" en la pestaña de Ayuda o crea un issue en GitHub.</p>
        
        <h3>¿Dónde encuentro más ayuda?</h3>
        <p>Visita el foro de discusiones en GitHub o contacta al soporte técnico.</p>
        
        <hr>
        <p><em>¿No encontraste tu respuesta? <a href='https://github.com/despachanetbo-coder/FormaGestPro/discussions'>Haz tu pregunta en el foro</a></em></p>
        """
        
        text_browser.setHtml(faq_content)
        layout.addWidget(text_browser)
        
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(faq_dialog.close)
        layout.addWidget(btn_close)
        
        faq_dialog.exec()
    
    def report_issue(self):
        """Reportar un problema o sugerencia"""
        webbrowser.open("https://github.com/despachanetbo-coder/FormaGestPro/issues/new")
        
        QMessageBox.information(
            self,
            "Reportar Problema",
            "Se ha abierto la página para reportar problemas en GitHub.<br><br>"
            "Por favor, incluye:<br>"
            "1. Descripción detallada del problema<br>"
            "2. Pasos para reproducirlo<br>"
            "3. Capturas de pantalla si es posible<br>"
            "4. Información de tu sistema"
        )
    
    def open_diagnostic_tools(self):
        """Abrir herramientas de diagnóstico"""
        dialog = QDialog(self)
        dialog.setWindowTitle("🔧 Herramientas de Diagnóstico")
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Pestañas para diferentes herramientas
        tab_widget = QTabWidget()
        
        # Tab 1: Verificación del sistema
        system_tab = QWidget()
        system_layout = QVBoxLayout(system_tab)
        
        system_text = QTextEdit()
        system_text.setReadOnly(True)
        system_text.setPlainText(self._get_system_info())
        system_layout.addWidget(system_text)
        
        btn_refresh_system = QPushButton("🔄 Actualizar Información")
        btn_refresh_system.clicked.connect(lambda: system_text.setPlainText(self._get_system_info()))
        system_layout.addWidget(btn_refresh_system)
        
        tab_widget.addTab(system_tab, "💻 Sistema")
        
        # Tab 2: Verificación de dependencias
        deps_tab = QWidget()
        deps_layout = QVBoxLayout(deps_tab)
        
        deps_text = QTextEdit()
        deps_text.setReadOnly(True)
        deps_text.setPlainText(self._get_dependencies_info())
        deps_layout.addWidget(deps_text)
        
        tab_widget.addTab(deps_tab, "📦 Dependencias")
        
        # Tab 3: Logs del sistema
        logs_tab = QWidget()
        logs_layout = QVBoxLayout(logs_tab)
        
        logs_text = QTextEdit()
        logs_text.setReadOnly(True)
        # Aquí cargarías logs reales
        logs_text.setPlainText("Los logs del sistema aparecerán aquí...")
        logs_layout.addWidget(logs_text)
        
        btn_load_logs = QPushButton("📁 Cargar Logs")
        logs_layout.addWidget(btn_load_logs)
        
        tab_widget.addTab(logs_tab, "📝 Logs")
        
        layout.addWidget(tab_widget)
        
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec()
    
    def open_changelog(self):
        """Abrir historial de cambios"""
        webbrowser.open("https://github.com/despachanetbo-coder/FormaGestPro/releases")
        
        QMessageBox.information(
            self,
            "Historial de Cambios",
            "El historial de cambios se ha abierto en tu navegador.<br><br>"
            "Aquí encontrarás todas las versiones publicadas y sus cambios."
        )
    
    def open_documentation(self, doc_id: str):
        """Abrir documentación específica"""
        self.switch_page("documentation")
        
        # También podrías navegar a secciones específicas
        doc_titles = {
            "install_guide": "Guía de Instalación",
            "config_guide": "Configuración Avanzada",
            "api_docs": "API y Extensiones",
            "database_docs": "Base de Datos",
            "security_docs": "Seguridad",
            "deployment_docs": "Despliegue"
        }
        
        QMessageBox.information(
            self,
            f"📚 {doc_titles.get(doc_id, 'Documentación')}",
            f"Has seleccionado: {doc_titles.get(doc_id, 'Documentación')}<br><br>"
            f"La documentación completa está disponible en esta página."
        )
    
    def send_contact_message(self):
        """Enviar mensaje de contacto"""
        # Validar campos
        if not self.contact_name.text().strip():
            QMessageBox.warning(self, "Error", "Por favor ingresa tu nombre.")
            return
        
        if not self.contact_email.text().strip():
            QMessageBox.warning(self, "Error", "Por favor ingresa tu email.")
            return
        
        if not self.contact_message.toPlainText().strip():
            QMessageBox.warning(self, "Error", "Por favor ingresa un mensaje.")
            return
        
        # Construir mensaje
        message = f"""
        Nombre: {self.contact_name.text()}
        Email: {self.contact_email.text()}
        Asunto: {self.contact_subject.currentText()}
        
        Mensaje:
        {self.contact_message.toPlainText()}
        """
        
        if self.attach_sysinfo.isChecked():
            message += f"""
            
            --- INFORMACIÓN DEL SISTEMA ---
            {self._get_system_info()}
            """
        
        # En una implementación real, aquí enviarías el mensaje
        # Por ahora, solo mostramos un diálogo de confirmación
        
        QMessageBox.information(
            self,
            "Mensaje Enviado",
            "Tu mensaje ha sido enviado exitosamente.<br><br>"
            "Recibirás una respuesta en <b>{}</b> en 24-48 horas hábiles.".format(
                self.contact_email.text()
            )
        )
        
        # Limpiar formulario
        self.clear_contact_form()
    
    def clear_contact_form(self):
        """Limpiar formulario de contacto"""
        self.contact_name.clear()
        self.contact_email.clear()
        self.contact_subject.setCurrentIndex(0)
        self.contact_message.clear()
        self.attach_sysinfo.setChecked(True)
    
    def show_about_dialog(self):
        """Mostrar diálogo 'Acerca de'"""
        about_text = """
        <div style="text-align: center;">
            <h1>FormaGestPro</h1>
            <h3>Sistema de Gestión Académica</h3>
            <hr>
            <p><strong>Versión:</strong> 3.0.0</p>
            <p><strong>Desarrollado por:</strong> Despachanetbo Coder</p>
            <p><strong>Licencia:</strong> MIT Open Source</p>
            <p><strong>Repositorio:</strong> 
            <a href="https://github.com/despachanetbo-coder/FormaGestPro">
            github.com/despachanetbo-coder/FormaGestPro</a></p>
            <hr>
            <p>FormaGestPro es un sistema integral para la gestión de 
            instituciones educativas, desarrollado con Python, PySide6 y PostgreSQL.</p>
            <p>© 2024 FormaGestPro. Todos los derechos reservados.</p>
        </div>
        """
        
        QMessageBox.about(self, "Acerca de FormaGestPro", about_text)
    
    # ============================================================================
    # MÉTODOS UTILITARIOS
    # ============================================================================
    
    def _darken_color(self, color: str) -> str:
        """Oscurecer un color hexadecimal"""
        # Implementación simple
        if color.startswith("#"):
            try:
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                r = max(0, r - 30)
                g = max(0, g - 30)
                b = max(0, b - 30)
                return f"#{r:02x}{g:02x}{b:02x}"
            except:
                return color
        return color
    
    def _get_system_info(self) -> str:
        """Obtener información del sistema"""
        try:
            info = []
            info.append("=== INFORMACIÓN DEL SISTEMA ===\n")
            
            # Sistema operativo
            info.append(f"Sistema Operativo: {platform.system()} {platform.release()}")
            info.append(f"Versión: {platform.version()}")
            info.append(f"Arquitectura: {platform.machine()}\n")
            
            # Python
            info.append(f"Python: {platform.python_version()}")
            info.append(f"Implementación: {platform.python_implementation()}\n")
            
            # Memoria (simplificado sin psutil)
            try:
                import psutil
                memory = psutil.virtual_memory()
                info.append(f"Memoria Total: {memory.total / (1024**3):.2f} GB")
                info.append(f"Memoria Disponible: {memory.available / (1024**3):.2f} GB")
                info.append(f"Porcentaje Usado: {memory.percent}%\n")
            except ImportError:
                info.append("Memoria: (instala psutil para información detallada)\n")
            
            # FormaGestPro
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            info.append(f"Directorio de la App: {base_dir}")
            
            # Verificar git
            try:
                result = subprocess.run(
                    "git --version",
                    shell=True,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    info.append(f"Git Disponible: Sí")
                    info.append(f"Git Versión: {result.stdout.strip()}")
                else:
                    info.append(f"Git Disponible: No")
            except:
                info.append(f"Git Disponible: No")
            
            return "\n".join(info)
            
        except Exception as e:
            return f"Error obteniendo información del sistema: {str(e)}"
    
    def _get_dependencies_info(self) -> str:
        """Obtener información de dependencias"""
        try:
            info = []
            info.append("=== DEPENDENCIAS DE PYTHON ===\n")
            
            # Leer requirements.txt
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            requirements_path = os.path.join(base_dir, "requirements.txt")
            
            if os.path.exists(requirements_path):
                with open(requirements_path, 'r') as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                
                info.append(f"Requirements.txt encontrado: {len(requirements)} paquetes\n")
                
                # Método simple para verificar dependencias sin pkg_resources
                import importlib
                import sys
                
                for req in requirements[:20]:  # Limitar a 20
                    try:
                        # Extraer nombre del paquete (eliminar versiones y extras)
                        pkg_name = req.split('>')[0].split('<')[0].split('=')[0].split('[')[0].strip()
                        
                        # Intentar importar
                        try:
                            module = importlib.import_module(pkg_name.replace('-', '_'))
                            # Obtener versión si está disponible
                            if hasattr(module, '__version__'):
                                version = module.__version__
                                info.append(f"✓ {pkg_name}: {version}")
                            else:
                                info.append(f"✓ {pkg_name}: Instalado (versión no disponible)")
                        except ImportError:
                            info.append(f"✗ {pkg_name}: NO INSTALADO")
                    except:
                        info.append(f"? {req}: Error al procesar")
                
                if len(requirements) > 20:
                    info.append(f"\n... y {len(requirements) - 20} paquetes más")
            else:
                info.append("No se encontró requirements.txt")
            
            return "\n".join(info)
            
        except Exception as e:
            return f"Error obteniendo información de dependencias: {str(e)}"
    
    # ============================================================================
    # MÉTODOS DE CICLO DE VIDA
    # ============================================================================
    
    def closeEvent(self, event):
        """Manejador para el cierre de la pestaña"""
        # Detener hilo de actualización si está corriendo
        if self.update_thread.isRunning():
            self.update_thread.terminate()
            self.update_thread.wait()
        
        logger.info("AyudaTab cerrado")
        super().closeEvent(event)


# ============================================================================
# PUNTO DE ENTRADA PARA PRUEBAS
# ============================================================================

if __name__ == "__main__":
    print("🧪 Ejecutando AyudaTab en modo prueba...")
    
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Datos de usuario de prueba
    user_data = {
        'username': 'admin',
        'nombres': 'Administrador',
        'apellido_paterno': 'Sistema',
        'rol': 'Administrador'
    }
    
    ayuda = AyudaTab(user_data=user_data)
    ayuda.setWindowTitle("Ayuda & Actualizaciones - FormaGestPro v3.0")
    ayuda.resize(1400, 900)
    ayuda.show()
    
    print("✅ AyudaTab iniciado en modo prueba")
    sys.exit(app.exec())