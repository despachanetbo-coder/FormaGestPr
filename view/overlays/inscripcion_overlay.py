# view/overlays/inscripcion_overlay.py
"""
Overlay para gestionar inscripciones de estudiantes a programas académicos.
Hereda de BaseOverlay.
"""
import os
import tempfile
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, List
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDateEdit, QTextEdit, QFrame, QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QGroupBox, QSizePolicy, QProgressBar,
    QSplitter, QCheckBox, QDoubleSpinBox, QSpinBox, QTabWidget, QTextBrowser,
    QTableWidget, QTableWidgetItem, QHeaderView, QStyledItemDelegate,
    QAbstractItemView, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem,
    QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt, QDate, QTimer, QSize, Signal, QEvent
from PySide6.QtGui import (
    QFont, QPixmap, QIcon, QIntValidator, QDoubleValidator, QImage, 
    QPixmap, QImage, QColor, QBrush
)

# Importar modelos
from model.inscripcion_model import InscripcionModel
from model.estudiante_model import EstudianteModel
from model.programa_model import ProgramaModel
from model.transaccion_model import TransaccionModel

# Importar estilos y utilidades
from utils.validators import Validators

from .base_overlay import BaseOverlay

# Configurar logger
logger = logging.getLogger(__name__)

class InscripcionOverlay(BaseOverlay):
    """
    Overlay para la gestión completa de inscripciones estudiantiles a programas académicos.
    
    Características principales:
    - Creación, edición y visualización de inscripciones
    - Gestión de transacciones asociadas a inscripciones
    - Manejo de documentos de respaldo
    - Flujo secuencial: inscripción → transacción → documentos
    """
    
    # Señales específicas
    inscripcion_creada = Signal(dict)
    inscripcion_actualizada = Signal(dict)
    inscripcion_cancelada = Signal(dict)
    
    # ===== MÉTODOS DE INICIALIZACIÓN =====
    
    def __init__(self, parent=None):
        super().__init__(parent, "🎓 Gestión de Inscripción", 95, 95)
        
        # Variables específicas
        self.inscripcion_id: Optional[int] = None
        self.estudiante_id: Optional[int] = None
        self.programa_id: Optional[int] = None
        self.original_data: Dict[str, Any] = {}
        
        # Variables de estado
        self.estudiante_encontrado = False
        self.programa_encontrado = False
        self.disponibilidad_verificada = False
        
        # Datos cache
        self.estudiante_data: Optional[Dict] = None
        self.programa_data: Optional[Dict] = None
        self.disponibilidad_data: Optional[Dict] = None
        
        # Listas para datos dinámicos
        self.programas_inscritos: List[Dict] = []
        self.estudiantes_inscritos: List[Dict] = []
        self.programas_disponibles: List[Dict] = []
        self.estudiantes_disponibles: List[Dict] = []
        
        # ATRIBUTOS NUEVOS QUE NECESITAMOS AGREGAR:
        self.splitter_principal: Optional[QSplitter] = None
        self.seccion_transaccion_frame: Optional[QFrame] = None
        self.transaccion_registrada = Signal(dict)  # Señal si no existe
        
        # Widgets del formulario nuevo que necesitamos declarar
        self.total_label: Optional[QLabel] = None
        self.resumen_total_label: Optional[QLabel] = None
        self.resumen_monto_label: Optional[QLabel] = None
        self.seccion_datos_basicos: Optional[QFrame] = None
        self.seccion_transaccion: Optional[QFrame] = None
        self.seccion_detalles_documentos: Optional[QFrame] = None
        self.seccion_resumen_acciones: Optional[QFrame] = None
        self.historial_table: Optional[QTableWidget] = None
        
        ## Configurar UI específica
        #self.setup_ui_especifica()
        #self.setup_conexiones_especificas()
        #self.setup_validators()
        
        logger.debug("✅ InscripcionOverlay inicializado")
    
    def setup_ui_especifica(self):
        """Configurar la interfaz específica de inscripción"""
        # Limpiar layout de contenido base
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
        
        # Widget principal con scroll
        scroll_widget = QScrollArea()
        scroll_widget.setWidgetResizable(True)
        scroll_widget.setFrameShape(QFrame.Shape.NoFrame)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Crear splitter principal
        self.splitter_principal = QSplitter(Qt.Orientation.Horizontal)
        
        # Contenedor izquierdo
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(10)
        
        # Contenedor derecho
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(10)
        
        # ===== PANEL IZQUIERDO =====
        # Grupo: Información del Estudiante (cuando estudiante_id > 0)
        self.grupo_info_estudiante = self.crear_grupo_info_estudiante_completo()
        left_layout.addWidget(self.grupo_info_estudiante)
        
        # Grupo: Buscar Estudiante (cuando programa_id > 0)
        self.grupo_buscar_estudiante = self.crear_grupo_buscar_estudiante_completo()
        left_layout.addWidget(self.grupo_buscar_estudiante)
        
        left_layout.addStretch()
        
        # ===== PANEL DERECHO =====
        # Grupo: Programas Disponibles (cuando estudiante_id > 0)
        self.grupo_programas_disponibles = self.crear_grupo_programas_disponibles()
        right_layout.addWidget(self.grupo_programas_disponibles)
        
        # Grupo: Buscar Programa (cuando estudiante_id > 0 y no hay programa pre-seleccionado)
        self.grupo_buscar_programa = self.crear_grupo_buscar_programa_completo()
        right_layout.addWidget(self.grupo_buscar_programa)
        
        # Grupo: Información del Programa (cuando programa_id > 0)
        self.grupo_info_programa = self.crear_grupo_info_programa_completo()
        left_layout.addWidget(self.grupo_info_programa)
        
        right_layout.addStretch()
        
        # Agregar contenedores al splitter
        self.splitter_principal.addWidget(left_container)
        self.splitter_principal.addWidget(right_container)

        # Configurar tamaños iniciales del splitter
        self.splitter_principal.setSizes([400, 400])
        
        main_layout.addWidget(self.splitter_principal, 1)
        
        # ===== SECCIÓN DE LISTADO DINÁMICO =====
        self.seccion_listado_frame = QFrame()
        self.seccion_listado_frame.setVisible(False)
        listado_layout = QVBoxLayout(self.seccion_listado_frame)
        listado_layout.setSpacing(10)
        
        # Título de la sección
        self.titulo_listado_label = QLabel()
        self.titulo_listado_label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 5px;
        """)
        listado_layout.addWidget(self.titulo_listado_label)
        
        # Contenedor scrollable para listados dinámicos
        self.listado_scroll = QScrollArea()
        self.listado_scroll.setWidgetResizable(True)
        self.listado_scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.listado_container = QWidget()
        self.listado_layout_container = QVBoxLayout(self.listado_container)
        self.listado_layout_container.setSpacing(15)
        
        self.listado_scroll.setWidget(self.listado_container)
        listado_layout.addWidget(self.listado_scroll, 1)
        
        main_layout.addWidget(self.seccion_listado_frame, 1)
        
        # ===== SECCIÓN DE FORMULARIO DE INSCRIPCIÓN =====
        self.seccion_formulario_frame = QFrame()
        self.seccion_formulario_frame.setVisible(False)
        self.seccion_formulario_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 2px solid #3498db;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        formulario_layout = QVBoxLayout(self.seccion_formulario_frame)
        
        # Título del formulario
        self.titulo_formulario_label = QLabel("📝 INSCRIPCIÓN A PROGRAMA")
        self.titulo_formulario_label.setStyleSheet("""
            font-weight: bold;
            font-size: 18px;
            color: #2980b9;
            margin-bottom: 15px;
        """)
        formulario_layout.addWidget(self.titulo_formulario_label)
        
        # Formulario de inscripción
        self.grupo_formulario_inscripcion = self.crear_grupo_formulario_inscripcion()
        formulario_layout.addWidget(self.grupo_formulario_inscripcion, 1)
        
        # Botones del formulario
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_realizar_inscripcion = QPushButton("✅ REALIZAR INSCRIPCIÓN")
        self.btn_realizar_inscripcion.setObjectName("btnRealizarInscripcion")
        self.btn_realizar_inscripcion.setMinimumHeight(40)
        self.btn_realizar_inscripcion.setStyleSheet("""
            #btnRealizarInscripcion {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 30px;
                font-size: 14px;
            }
            #btnRealizarInscripcion:hover {
                background-color: #219653;
            }
        """)
        
        self.btn_cancelar_inscripcion = QPushButton("❌ CANCELAR INSCRIPCIÓN")
        self.btn_cancelar_inscripcion.setMinimumHeight(40)
        self.btn_cancelar_inscripcion.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 30px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        btn_layout.addWidget(self.btn_realizar_inscripcion)
        btn_layout.addWidget(self.btn_cancelar_inscripcion)
        formulario_layout.addLayout(btn_layout)
        
        main_layout.addWidget(self.seccion_formulario_frame, 1)
        
            # ===== CREAR TABLA DE HISTORIAL DE TRANSACCIONES =====
        self.crear_historial_table()
        
        scroll_widget.setWidget(main_widget)
        self.content_layout.addWidget(scroll_widget, 1)
    
    # ===== MÉTODOS DE CREACIÓN DE COMPONENTES UI =====
    
    def crear_acciones_formulario(self):
        """Crear sección de botones de acción"""
        frame = QFrame()

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 15, 0, 0)

        # Botón Cancelar
        self.btn_cancelar_formulario = QPushButton("❌ CANCELAR")
        self.btn_cancelar_formulario.setMinimumHeight(45)
        self.btn_cancelar_formulario.setMinimumWidth(150)
        self.btn_cancelar_formulario.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        layout.addWidget(self.btn_cancelar_formulario)

        layout.addStretch()

        # Botón Registrar Transacción
        self.btn_registrar_transaccion = QPushButton("💰 REGISTRAR TRANSACCIÓN")
        self.btn_registrar_transaccion.setObjectName("btnRegistrarTransaccion")
        self.btn_registrar_transaccion.setMinimumHeight(45)
        self.btn_registrar_transaccion.setMinimumWidth(200)
        self.btn_registrar_transaccion.setEnabled(False)
        self.btn_registrar_transaccion.setStyleSheet("""
            #btnRegistrarTransaccion {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #219653);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 30px;
            }
            #btnRegistrarTransaccion:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #219653, stop:1 #1e8449);
            }
            #btnRegistrarTransaccion:disabled {
                background: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        layout.addWidget(self.btn_registrar_transaccion)

        return frame
    
    def crear_grupo_info_estudiante_completo(self):
        """Crear grupo completo para información del estudiante"""
        grupo = QGroupBox("👤 INFORMACIÓN DEL ESTUDIANTE")
        grupo.setObjectName("grupoInfoEstudiante")
        grupo.setVisible(False)
        
        grid = QGridLayout(grupo)
        grid.setSpacing(12)
        grid.setContentsMargins(15, 20, 15, 15)
        
        # Fila 1: CI y Nombre Completo
        grid.addWidget(QLabel("CI:"), 0, 0)
        self.estudiante_ci_label = QLabel()
        self.estudiante_ci_label.setStyleSheet("font-weight: bold;")
        grid.addWidget(self.estudiante_ci_label, 0, 1)
        
        grid.addWidget(QLabel("Nombre Completo:"), 0, 2)
        self.estudiante_nombre_label = QLabel()
        self.estudiante_nombre_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        grid.addWidget(self.estudiante_nombre_label, 0, 3)
        
        # Fila 2: Email y Teléfono
        grid.addWidget(QLabel("Email:"), 1, 0)
        self.estudiante_email_label = QLabel()
        self.estudiante_email_label.setStyleSheet("color: #3498db;")
        grid.addWidget(self.estudiante_email_label, 1, 1)
        
        grid.addWidget(QLabel("Teléfono:"), 1, 2)
        self.estudiante_telefono_label = QLabel()
        grid.addWidget(self.estudiante_telefono_label, 1, 3)
        
        # Fila 3: Profesión y Universidad
        grid.addWidget(QLabel("Profesión:"), 2, 0)
        self.estudiante_profesion_label = QLabel()
        grid.addWidget(self.estudiante_profesion_label, 2, 1)
        
        grid.addWidget(QLabel("Universidad:"), 2, 2)
        self.estudiante_universidad_label = QLabel()
        grid.addWidget(self.estudiante_universidad_label, 2, 3)
        
        # Fila 4: Dirección
        grid.addWidget(QLabel("Dirección:"), 3, 0)
        self.estudiante_direccion_label = QLabel()
        self.estudiante_direccion_label.setWordWrap(True)
        grid.addWidget(self.estudiante_direccion_label, 3, 1, 1, 3)
        
        return grupo
    
    def crear_grupo_buscar_estudiante_completo(self):
        """Crear grupo para buscar estudiante cuando programa_id > 0"""
        grupo = QGroupBox("🔍 BUSCAR ESTUDIANTE")
        grupo.setObjectName("grupoBuscarEstudiante")
        grupo.setVisible(False)
        
        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)
        
        # Explicación
        label_info = QLabel("Busque estudiantes que NO están inscritos en este programa:")
        label_info.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(label_info)
        
        # Layout para búsqueda
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        # Campo de búsqueda
        self.estudiante_search_input = QLineEdit()
        self.estudiante_search_input.setPlaceholderText("Ej: 1234567, Juan Pérez, o juan@email.com")
        self.estudiante_search_input.setMinimumHeight(30)
        self.estudiante_search_input.setMaximumHeight(40)
        self.estudiante_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #3498db;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        search_layout.addWidget(self.estudiante_search_input, 1)
        
        # Botón buscar
        self.btn_buscar_estudiante = QPushButton("🔍 BUSCAR")
        self.btn_buscar_estudiante.setObjectName("btnBuscarEstudiante")
        self.btn_buscar_estudiante.setMinimumHeight(35)
        self.btn_buscar_estudiante.setStyleSheet("""
            #btnBuscarEstudiante {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
            }
            #btnBuscarEstudiante:hover {
                background-color: #2980b9;
            }
        """)
        search_layout.addWidget(self.btn_buscar_estudiante)
        
        layout.addLayout(search_layout)
        
        # Tabla de resultados
        self.estudiantes_disponibles_table = QTableWidget()
        self.estudiantes_disponibles_table.setColumnCount(5)
        self.estudiantes_disponibles_table.setHorizontalHeaderLabels(["CI", "Nombre Completo", "Email", "Teléfono", "Acción"])
        self.estudiantes_disponibles_table.horizontalHeader().setStretchLastSection(True)
        self.estudiantes_disponibles_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.estudiantes_disponibles_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.estudiantes_disponibles_table.setAlternatingRowColors(True)
        self.estudiantes_disponibles_table.setMinimumHeight(200)
        
        layout.addWidget(self.estudiantes_disponibles_table, 1)
        
        # Label de estado
        self.estudiante_status_label = QLabel("")
        self.estudiante_status_label.setStyleSheet("""
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
        """)
        layout.addWidget(self.estudiante_status_label)
        
        return grupo
    
    def crear_grupo_info_programa_completo(self):
        """Crear grupo completo para información del programa"""
        grupo = QGroupBox("📊 INFORMACIÓN DEL PROGRAMA")
        grupo.setObjectName("grupoInfoPrograma")
        grupo.setVisible(False)
        
        grid = QGridLayout(grupo)
        grid.setSpacing(12)
        grid.setContentsMargins(15, 20, 15, 15)
        
        # Fila 1: Código y Nombre
        grid.addWidget(QLabel("Código:"), 0, 0)
        self.programa_codigo_label = QLabel()
        self.programa_codigo_label.setStyleSheet("font-weight: bold; color: #9b59b6; font-size: 14px;")
        grid.addWidget(self.programa_codigo_label, 0, 1)
        
        grid.addWidget(QLabel("Nombre:"), 0, 2)
        self.programa_nombre_label = QLabel()
        self.programa_nombre_label.setStyleSheet("font-weight: bold;")
        grid.addWidget(self.programa_nombre_label, 0, 3)
        
        # Fila 2: Duración y Horas
        grid.addWidget(QLabel("Duración:"), 1, 0)
        self.programa_duracion_label = QLabel()
        grid.addWidget(self.programa_duracion_label, 1, 1)
        
        grid.addWidget(QLabel("Horas Totales:"), 1, 2)
        self.programa_horas_label = QLabel()
        grid.addWidget(self.programa_horas_label, 1, 3)
        
        # Fila 3: Cupos y Estado
        grid.addWidget(QLabel("Cupos:"), 2, 0)
        self.programa_cupos_label = QLabel()
        grid.addWidget(self.programa_cupos_label, 2, 1)
        
        grid.addWidget(QLabel("Estado:"), 2, 2)
        self.programa_estado_label = QLabel()
        self.programa_estado_label.setStyleSheet("font-weight: bold;")
        grid.addWidget(self.programa_estado_label, 2, 3)
        
        # Fila 4: Costos
        grid.addWidget(QLabel("Matrícula:"), 3, 0)
        self.programa_matricula_label = QLabel()
        self.programa_matricula_label.setStyleSheet("color: #27ae60;")
        grid.addWidget(self.programa_matricula_label, 3, 1)
        
        grid.addWidget(QLabel("Inscripción:"), 3, 2)
        self.programa_costo_inscripcion_label = QLabel()
        self.programa_costo_inscripcion_label.setStyleSheet("color: #27ae60;")
        grid.addWidget(self.programa_costo_inscripcion_label, 3, 3)
        
        # Fila 5: Total y Docente
        grid.addWidget(QLabel("Total:"), 4, 0)
        self.programa_total_label = QLabel()
        self.programa_total_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        grid.addWidget(self.programa_total_label, 4, 1)
        
        grid.addWidget(QLabel("Docente:"), 4, 2)
        self.programa_docente_label = QLabel()
        grid.addWidget(self.programa_docente_label, 4, 3)
        
        # Fila 6: Resumen inscritos
        grid.addWidget(QLabel("Inscritos:"), 5, 0)
        self.programa_inscritos_label = QLabel()
        self.programa_inscritos_label.setStyleSheet("color: #2980b9; font-weight: bold;")
        grid.addWidget(self.programa_inscritos_label, 5, 1)
        
        grid.addWidget(QLabel("Recaudado:"), 5, 2)
        self.programa_recaudado_label = QLabel()
        self.programa_recaudado_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        grid.addWidget(self.programa_recaudado_label, 5, 3)
        
        return grupo
    
    def crear_grupo_programas_disponibles(self):
        """Crear grupo para mostrar programas disponibles cuando estudiante_id > 0"""
        grupo = QGroupBox("📚 PROGRAMAS DISPONIBLES")
        grupo.setObjectName("grupoProgramasDisponibles")
        grupo.setVisible(False)
        
        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)
        
        # Explicación
        label_info = QLabel("Programas en estado ACTIVO e INSCRIPCIONES a los que el estudiante NO está inscrito:")
        label_info.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(label_info)
        
        # Tabla de programas disponibles
        self.programas_disponibles_table = QTableWidget()
        self.programas_disponibles_table.setColumnCount(6)
        self.programas_disponibles_table.setHorizontalHeaderLabels(["Código", "Nombre", "Estado", "Cupos", "Costo", "Inscribir"])
        self.programas_disponibles_table.horizontalHeader().setStretchLastSection(True)
        self.programas_disponibles_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.programas_disponibles_table.setAlternatingRowColors(True)
        self.programas_disponibles_table.setMinimumHeight(300)
        
        layout.addWidget(self.programas_disponibles_table, 1)
        
        return grupo
    
    def crear_grupo_buscar_programa_completo(self):
        """Crear grupo para buscar programa cuando no hay programa pre-seleccionado"""
        grupo = QGroupBox("🔍 BUSCAR PROGRAMA")
        grupo.setObjectName("grupoBuscarPrograma")
        grupo.setVisible(False)
        
        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)
        
        # Layout para búsqueda
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        # Campo de búsqueda
        self.programa_search_input = QLineEdit()
        self.programa_search_input.setPlaceholderText("Buscar por código o nombre...")
        self.programa_search_input.setMinimumHeight(30)
        self.programa_search_input.setMaximumHeight(40)
        search_layout.addWidget(self.programa_search_input, 1)
        
        # Botón buscar
        self.btn_buscar_programa = QPushButton("🔍 BUSCAR")
        self.btn_buscar_programa.setMinimumHeight(35)
        search_layout.addWidget(self.btn_buscar_programa)
        
        layout.addLayout(search_layout)
        
        return grupo
    
    def crear_item_programa_inscrito(self, programa_data: Dict):
        """Crear un item para mostrar un programa inscrito"""
        # Contenedor principal
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        main_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin: 10px 5px;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border: 2px solid #2980b9;
            }
        """)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 15, 20, 15)
        
        # ===== ENCABEZADO DEL PROGRAMA =====
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-radius: 8px;
                padding: 0px;
            }
        """)
        header_layout = QGridLayout(header_frame)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        # Código del programa
        codigo_label = QLabel("🎓 CÓDIGO:")
        codigo_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(codigo_label, 0, 0)
        
        codigo_value = QLabel(programa_data.get('codigo', 'N/A'))
        codigo_value.setStyleSheet("""
            font-weight: bold;
            font-size: 15px;
            color: #2980b9;
            padding: 3px 10px;
            background-color: white;
            border-radius: 4px;
        """)
        header_layout.addWidget(codigo_value, 0, 1)
        
        # Nombre del programa
        nombre_label = QLabel("📚 PROGRAMA:")
        nombre_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(nombre_label, 0, 2)
        
        nombre_value = QLabel(programa_data.get('nombre', 'N/A'))
        nombre_value.setStyleSheet("""
            font-weight: bold;
            color: #2c3e50;
            font-size: 14px;
            padding: 3px 10px;
            background-color: white;
            border-radius: 4px;
        """)
        nombre_value.setWordWrap(True)
        header_layout.addWidget(nombre_value, 0, 3, 1, 2)
        
        # Estado de inscripción
        estado_label = QLabel("📊 ESTADO:")
        estado_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(estado_label, 1, 0)
        
        estado_value = programa_data.get('estado_inscripcion', 'N/A')
        estado_text = QLabel(estado_value)
        
        # Mapear estados a colores
        estado_colors = {
            'INSCRITO': "#27ae60",
            'EN_CURSO': "#27ae60",
            'PREINSCRITO': "#f39c12",
            'CONCLUIDO': "#3498db",
            'RETIRADO': "#e74c3c"
        }
        estado_color = estado_colors.get(estado_value, "#7f8c8d")
        
        estado_text.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: white;
            background-color: {estado_color};
            padding: 5px 15px;
            border-radius: 15px;
            min-width: 100px;
            text-align: center;
        """)
        header_layout.addWidget(estado_text, 1, 1)
        
        # Costo total
        costo_label = QLabel("💰 COSTO TOTAL:")
        costo_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(costo_label, 1, 2)
        
        costo_total = programa_data.get('costo_con_descuento', 0) or 0
        descuento = programa_data.get('descuento_aplicado', 0) or 0
        
        if descuento > 0:
            costo_text = f"<span style='font-weight:bold; color:#e74c3c;'>{costo_total:.2f}</span> Bs <span style='color:#27ae60;'>({descuento}% desc.)</span>"
        else:
            costo_text = f"<span style='font-weight:bold; color:#e74c3c;'>{costo_total:.2f}</span> Bs"
            
        costo_value = QLabel(costo_text)
        costo_value.setStyleSheet("background-color: white; padding: 5px 10px; border-radius: 4px;")
        header_layout.addWidget(costo_value, 1, 3)
        
        main_layout.addWidget(header_frame)
        
        # ===== INFORMACIÓN FINANCIERA =====
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 12, 15, 12)
        
        # Total pagado
        total_pagado = programa_data.get('total_pagado', 0)
        porcentaje_pagado = programa_data.get('porcentaje_pagado', 0)
        
        pagado_label = QLabel("✅ PAGADO:")
        pagado_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        info_layout.addWidget(pagado_label, 0, 0)
        
        pagado_text = QLabel(f"{total_pagado:.2f} Bs ({porcentaje_pagado:.1f}%)")
        pagado_text.setStyleSheet("font-weight: bold; color: #27ae60;")
        info_layout.addWidget(pagado_text, 0, 1)
        
        # Saldo pendiente
        saldo_label = QLabel("📉 SALDO PENDIENTE:")
        saldo_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        info_layout.addWidget(saldo_label, 0, 2)
        
        saldo_pendiente = programa_data.get('saldo_pendiente', 0) or 0
        saldo_text = QLabel(f"{saldo_pendiente:.2f} Bs")
        saldo_text.setStyleSheet("font-weight: bold; color: #e74c3c;")
        info_layout.addWidget(saldo_text, 0, 3)
        
        # Fecha de inscripción
        fecha_label = QLabel("📅 FECHA INSCRIPCIÓN:")
        fecha_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        info_layout.addWidget(fecha_label, 1, 0)
        
        fecha_insc = programa_data.get('fecha_inscripcion', '')
        fecha_text = QLabel(str(fecha_insc)[:10] if fecha_insc else "N/A")
        info_layout.addWidget(fecha_text, 1, 1)
        
        # Próximo vencimiento (si aplica)
        proxima_cuota = programa_data.get('proxima_cuota')
        if proxima_cuota:
            vencimiento_label = QLabel("⏰ PRÓXIMO VENCIMIENTO:")
            vencimiento_label.setStyleSheet("font-weight: bold; color: #f39c12;")
            info_layout.addWidget(vencimiento_label, 1, 2)
            
            vencimiento_text = QLabel(f"Cuota {proxima_cuota.get('numero', '?')}: {proxima_cuota.get('vencimiento', 'N/A')}")
            vencimiento_text.setStyleSheet("font-weight: bold; color: #f39c12;")
            info_layout.addWidget(vencimiento_text, 1, 3)
            
        main_layout.addWidget(info_frame)
        
        # ===== HISTORIAL DE TRANSACCIONES =====
        transacciones = programa_data.get('transacciones', [])
        if transacciones:
            # Encabezado de transacciones
            trans_header = QLabel("📊 HISTORIAL DE TRANSACCIONES")
            trans_header.setStyleSheet("""
                font-weight: bold;
                font-size: 13px;
                color: #2c3e50;
                padding: 8px 0px;
                border-bottom: 2px solid #3498db;
            """)
            main_layout.addWidget(trans_header)
            
            # Tabla de transacciones
            trans_table = QTableWidget()
            trans_table.setColumnCount(7)
            trans_table.setHorizontalHeaderLabels(["N°", "Fecha", "Monto", "Forma Pago", "Comprobante", "Estado", "Docs"])
            trans_table.horizontalHeader().setStretchLastSection(True)
            trans_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            trans_table.setAlternatingRowColors(True)
            trans_table.setMinimumHeight(120)
            trans_table.setMaximumHeight(200)
            
            # Configurar ancho de columnas
            header = trans_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
            
            trans_table.setColumnWidth(0, 80)  # N°
            trans_table.setColumnWidth(1, 100)  # Fecha
            trans_table.setColumnWidth(2, 100)  # Monto
            trans_table.setColumnWidth(3, 120)  # Forma Pago
            trans_table.setColumnWidth(4, 150)  # Comprobante
            trans_table.setColumnWidth(5, 100)  # Estado
            trans_table.setColumnWidth(6, 60)   # Docs
            
            trans_table.setRowCount(len(transacciones))
            
            for i, transaccion in enumerate(transacciones):
                # Número de transacción
                trans_table.setItem(i, 0, QTableWidgetItem(transaccion.get('numero_transaccion', f"TRX-{transaccion.get('id', '?')}")))
                
                # Fecha
                fecha = transaccion.get('fecha_pago', '')
                trans_table.setItem(i, 1, QTableWidgetItem(str(fecha)[:10] if fecha else ''))
                
                # Monto
                monto = transaccion.get('monto_final', 0)
                monto_item = QTableWidgetItem(f"{monto:.2f} Bs")
                trans_table.setItem(i, 2, monto_item)
                
                # Forma de pago
                trans_table.setItem(i, 3, QTableWidgetItem(transaccion.get('forma_pago', '')))
                
                # Comprobante
                comprobante = transaccion.get('numero_comprobante', '') or ''
                trans_table.setItem(i, 4, QTableWidgetItem(comprobante[:20] + "..." if len(comprobante) > 20 else comprobante))
                
                # Estado
                estado_trans = transaccion.get('estado', '')
                estado_item = QTableWidgetItem(estado_trans)
                estado_colors_trans = {
                    'CONFIRMADO': QColor("#27ae60"),
                    'PENDIENTE': QColor("#f39c12"),
                    'ANULADO': QColor("#e74c3c")
                }
                estado_color_trans = estado_colors_trans.get(estado_trans, QColor("#7f8c8d"))
                estado_item.setForeground(QBrush(estado_color_trans))
                trans_table.setItem(i, 5, estado_item)
                
                # Documentos
                num_docs = transaccion.get('numero_documentos', 0)
                docs_item = QTableWidgetItem(f"{num_docs} 📎")
                docs_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                trans_table.setItem(i, 6, docs_item)
                
            main_layout.addWidget(trans_table)
        else:
            # Mostrar mensaje si no hay transacciones
            no_trans_frame = QFrame()
            no_trans_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 15px;
                }
            """)
            no_trans_layout = QVBoxLayout(no_trans_frame)
            
            no_trans_label = QLabel("📭 No hay transacciones registradas para esta inscripción")
            no_trans_label.setStyleSheet("""
                color: #95a5a6;
                font-style: italic;
                font-size: 13px;
                text-align: center;
            """)
            no_trans_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_trans_layout.addWidget(no_trans_label)
            
            main_layout.addWidget(no_trans_frame)
            
        # ===== BOTONES DE ACCIÓN =====
        saldo_pendiente = programa_data.get('saldo_pendiente', 0)
        inscripcion_id = programa_data.get('inscripcion_id')

        if saldo_pendiente > 0 and inscripcion_id:
            btn_frame = QFrame()
            btn_layout = QHBoxLayout(btn_frame)

            # Agregar información de saldo
            saldo_info = QLabel(f"💰 Saldo pendiente: <span style='color:#e74c3c; font-weight:bold;'>{saldo_pendiente:.2f} Bs</span>")
            saldo_info.setStyleSheet("font-size: 14px;")
            btn_layout.addWidget(saldo_info)

            btn_layout.addStretch()

            # Botón realizar pago - CORRECCIÓN: Conexión correcta
            btn_realizar_pago = QPushButton("💰 REALIZAR PAGO")
            btn_realizar_pago.setObjectName(f"btnPago_{inscripcion_id}")
            btn_realizar_pago.setMinimumHeight(40)
            btn_realizar_pago.setMinimumWidth(150)
            btn_realizar_pago.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #219653);
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #219653, stop:1 #1e8449);
                    border: 2px solid #145a32;
                }
                QPushButton:pressed {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #1e8449, stop:1 #196f3d);
                }
            """)

            # CORRECCIÓN: Usar functools.partial para pasar parámetros correctamente
            from functools import partial
            btn_realizar_pago.clicked.connect(
                partial(self.realizar_pago_inscripcion, inscripcion_id)
            )

            btn_layout.addWidget(btn_realizar_pago)
            main_layout.addWidget(btn_frame)
            
        # Ajustar tamaño mínimo del item
        main_frame.setMinimumHeight(300 if transacciones else 200)
        
        return main_frame
    
    def crear_grupo_formulario_inscripcion(self):
        """Crear grupo para el formulario de inscripción/transacción - VERSIÓN CORREGIDA"""
        grupo = QGroupBox("📋 FORMULARIO DE INSCRIPCIÓN")
        grupo.setObjectName("formularioInscripcion")
        grupo.setStyleSheet("""
            #formularioInscripcion {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: white;
            }
            #formularioInscripcion::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2980b9;
            }
        """)

        # Layout principal del grupo - USAR QVBoxLayout para organización vertical
        grupo_layout = QVBoxLayout(grupo)
        grupo_layout.setSpacing(20)
        grupo_layout.setContentsMargins(20, 25, 20, 20)

        # === SECCIÓN 1: DATOS BÁSICOS DE INSCRIPCIÓN ===
        self.seccion_datos_basicos = self.crear_seccion_datos_basicos()
        grupo_layout.addWidget(self.seccion_datos_basicos)

        # Separador 1
        separador1 = self.crear_separador("👇 PASO 2: REGISTRAR TRANSACCIÓN")
        grupo_layout.addWidget(separador1)

        # === SECCIÓN 2: REGISTRO DE TRANSACCIÓN ===
        # CORRECCIÓN: Crear frame de transacción correctamente
        self.seccion_transaccion_frame = QFrame()
        self.seccion_transaccion_frame.setObjectName("seccionTransaccionFrame")
        self.seccion_transaccion_frame.setVisible(False)
        transaccion_layout = QVBoxLayout(self.seccion_transaccion_frame)
        transaccion_layout.setContentsMargins(0, 0, 0, 0)

        # Agregar contenido de transacción
        transaccion_content = self.crear_seccion_transaccion()
        transaccion_layout.addWidget(transaccion_content)

        grupo_layout.addWidget(self.seccion_transaccion_frame)

        # Separador 2
        separador2 = self.crear_separador("👇 PASO 3: DETALLES Y DOCUMENTOS")
        grupo_layout.addWidget(separador2)

        # === SECCIÓN 3: DETALLES Y DOCUMENTOS ===
        # CORRECCIÓN: Crear frame de detalles correctamente
        self.seccion_detalles_documentos_frame = QFrame()
        self.seccion_detalles_documentos_frame.setVisible(False)
        detalles_layout = QVBoxLayout(self.seccion_detalles_documentos_frame)
        detalles_layout.setContentsMargins(0, 0, 0, 0)

        detalles_content = self.crear_seccion_detalles_documentos()
        detalles_layout.addWidget(detalles_content)

        grupo_layout.addWidget(self.seccion_detalles_documentos_frame)

        # Separador 3
        separador3 = self.crear_separador("👇 RESUMEN Y ACCIONES")
        grupo_layout.addWidget(separador3)

        # === SECCIÓN 4: RESUMEN Y BOTONES ===
        # CORRECCIÓN: Crear sección de resumen
        self.seccion_resumen_frame = QFrame()
        resumen_layout = QVBoxLayout(self.seccion_resumen_frame)
        resumen_layout.setContentsMargins(0, 0, 0, 0)

        # Resumen financiero
        resumen_financiero = self.crear_resumen_financiero()
        resumen_layout.addWidget(resumen_financiero)

        # Botones de acción
        acciones_frame = self.crear_acciones_formulario()
        resumen_layout.addWidget(acciones_frame)

        grupo_layout.addWidget(self.seccion_resumen_frame)

        # Espaciador final
        grupo_layout.addStretch()

        return grupo
    
    def crear_resumen_financiero(self):
        """Crear sección de resumen financiero"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #ddd;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Labels de resumen
        total_label = QLabel("💰 TOTAL A PAGAR:")
        total_label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
        """)
        layout.addWidget(total_label)
        
        self.resumen_monto_label = QLabel("0.00 Bs")
        self.resumen_monto_label.setStyleSheet("""
            font-weight: bold;
            font-size: 20px;
            color: #e74c3c;
            padding: 8px 15px;
            background-color: white;
            border-radius: 6px;
            border: 2px solid #e74c3c;
            min-width: 150px;
            text-align: center;
        """)
        layout.addWidget(self.resumen_monto_label)
        
        layout.addStretch()
        
        return frame
    
    def crear_seccion_datos_basicos(self):
        """Crear sección de datos básicos de la inscripción"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4fc;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Título
        titulo = QLabel("🎯 DATOS BÁSICOS DE LA INSCRIPCIÓN")
        titulo.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #2980b9;
            padding-bottom: 10px;
            border-bottom: 2px solid #3498db;
        """)
        layout.addWidget(titulo)
        
        # Grid para información
        info_grid = QGridLayout()
        info_grid.setSpacing(15)
        info_grid.setVerticalSpacing(20)
        
        # Fila 1: Estudiante
        lbl_estudiante = QLabel("👤 ESTUDIANTE:")
        lbl_estudiante.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        info_grid.addWidget(lbl_estudiante, 0, 0)
        
        self.estudiante_nombre_form_label = QLabel()
        self.estudiante_nombre_form_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #2c3e50;
            padding: 8px 12px;
            background-color: white;
            border-radius: 6px;
            border: 1px solid #bdc3c7;
        """)
        info_grid.addWidget(self.estudiante_nombre_form_label, 0, 1, 1, 3)
        
        # Fila 2: Programa
        lbl_programa = QLabel("📚 PROGRAMA:")
        lbl_programa.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        info_grid.addWidget(lbl_programa, 1, 0)
        
        self.programa_nombre_form_label = QLabel()
        self.programa_nombre_form_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #2c3e50;
            padding: 8px 12px;
            background-color: white;
            border-radius: 6px;
            border: 1px solid #bdc3c7;
        """)
        info_grid.addWidget(self.programa_nombre_form_label, 1, 1, 1, 3)
        
        # Fila 3: Fecha y Estado
        lbl_fecha = QLabel("📅 FECHA INSCRIPCIÓN:")
        lbl_fecha.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        info_grid.addWidget(lbl_fecha, 2, 0)
        
        self.fecha_inscripcion_date = QDateEdit()
        self.fecha_inscripcion_date.setCalendarPopup(True)
        self.fecha_inscripcion_date.setDate(QDate.currentDate())
        self.fecha_inscripcion_date.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inscripcion_date.setMinimumHeight(30)
        self.fecha_inscripcion_date.setStyleSheet("""
            QDateEdit {
                font-size: 13px;
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QDateEdit::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 25px;
                border-left-width: 1px;
                border-left-color: darkgray;
                border-left-style: solid;
                border-top-right-radius: 3px;
                border-bottom-right-radius: 3px;
            }
        """)
        info_grid.addWidget(self.fecha_inscripcion_date, 2, 1)
        
        lbl_estado = QLabel("📊 ESTADO:")
        lbl_estado.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        info_grid.addWidget(lbl_estado, 2, 2)
        
        self.estado_inscripcion_combo = QComboBox()
        self.estado_inscripcion_combo.addItems(["PREINSCRITO", "INSCRITO", "EN_CURSO"])
        self.estado_inscripcion_combo.setMinimumHeight(30)
        self.estado_inscripcion_combo.setStyleSheet("""
            QComboBox {
                font-size: 13px;
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #2c3e50;
                margin-right: 10px;
            }
        """)
        info_grid.addWidget(self.estado_inscripcion_combo, 2, 3)
        
        # Fila 4: Descuento y Costo
        lbl_descuento = QLabel("🎁 DESCUENTO APLICADO:")
        lbl_descuento.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        info_grid.addWidget(lbl_descuento, 3, 0)
        
        self.descuento_spin = QDoubleSpinBox()
        self.descuento_spin.setRange(0, 100)
        self.descuento_spin.setDecimals(2)
        self.descuento_spin.setSuffix(" %")
        self.descuento_spin.setValue(0.0)
        self.descuento_spin.setMinimumHeight(30)
        self.descuento_spin.setMaximumHeight(40)
        self.descuento_spin.setStyleSheet("""
            QDoubleSpinBox {
                font-size: 13px;
                padding: 8px;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                background-color: white;
            }
        """)
        info_grid.addWidget(self.descuento_spin, 3, 1)
        
        lbl_costo = QLabel("💰 COSTO TOTAL:")
        lbl_costo.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        info_grid.addWidget(lbl_costo, 3, 2)
        
        self.costo_total_label = QLabel("0.00 Bs")
        self.costo_total_label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #e74c3c;
            padding: 10px 15px;
            background-color: white;
            border-radius: 6px;
            border: 2px solid #e74c3c;
            min-width: 150px;
            text-align: center;
        """)
        info_grid.addWidget(self.costo_total_label, 3, 3)
        
        layout.addLayout(info_grid)
        
        # Botón para registrar inscripción
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_registrar_inscripcion = QPushButton("✅ REGISTRAR INSCRIPCIÓN")
        self.btn_registrar_inscripcion.setObjectName("btnRegistrarInscripcion")
        self.btn_registrar_inscripcion.setMinimumHeight(45)
        self.btn_registrar_inscripcion.setMinimumWidth(250)
        self.btn_registrar_inscripcion.setStyleSheet("""
            #btnRegistrarInscripcion {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #219653);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 30px;
            }
            #btnRegistrarInscripcion:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #219653, stop:1 #1e8449);
                border: 2px solid #145a32;
            }
            #btnRegistrarInscripcion:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e8449, stop:1 #196f3d);
            }
            #btnRegistrarInscripcion:disabled {
                background: #95a5a6;
                color: #ecf0f1;
            }
        """)
        btn_layout.addWidget(self.btn_registrar_inscripcion)
        
        layout.addLayout(btn_layout)
        
        # Label para mostrar ID de inscripción
        self.inscripcion_id_label = QLabel("📋 ID de inscripción: <span style='color:#7f8c8d; font-style:italic;'>No registrado</span>")
        self.inscripcion_id_label.setStyleSheet("""
            font-size: 13px;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 6px;
            text-align: center;
            margin-top: 10px;
        """)
        self.inscripcion_id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.inscripcion_id_label)
        
        # Establecer altura mínima para esta sección
        frame.setMinimumHeight(350)
        
        return frame
    
    def crear_seccion_transaccion(self):
        """Crear sección para registrar transacción"""
        frame = QFrame()
        frame.setObjectName("seccionTransaccion")
        frame.setStyleSheet("""
            #seccionTransaccion {
                background-color: #f0f8ff;
                border: 2px dashed #3498db;
                border-radius: 10px;
                padding: 0px;
            }
        """)
        frame.setVisible(False)

        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 15, 20, 15)

        # Título
        titulo = QLabel("💰 REGISTRAR TRANSACCIÓN")
        titulo.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #2980b9;
            padding-bottom: 10px;
            border-bottom: 2px dashed #3498db;
        """)
        layout.addWidget(titulo)

        # Grid para datos de transacción
        transaccion_grid = QGridLayout()
        transaccion_grid.setSpacing(12)
        transaccion_grid.setVerticalSpacing(15)

        # Fila 1: Código y Fecha
        lbl_codigo = QLabel("🔢 CÓDIGO TRANSACCIÓN:")
        lbl_codigo.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        transaccion_grid.addWidget(lbl_codigo, 0, 0)

        self.codigo_transaccion_label = QLabel("AUTOGENERADO")
        self.codigo_transaccion_label.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #9b59b6;
            padding: 10px;
            background-color: #f5eef8;
            border-radius: 6px;
            border: 1px solid #9b59b6;
            min-width: 200px;
        """)
        transaccion_grid.addWidget(self.codigo_transaccion_label, 0, 1)

        lbl_fecha_pago = QLabel("📅 FECHA DE PAGO:")
        lbl_fecha_pago.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        transaccion_grid.addWidget(lbl_fecha_pago, 0, 2)

        self.fecha_pago_date = QDateEdit()
        self.fecha_pago_date.setCalendarPopup(True)
        self.fecha_pago_date.setDate(QDate.currentDate())
        self.fecha_pago_date.setDisplayFormat("dd/MM/yyyy")
        self.fecha_pago_date.setMinimumHeight(30)
        transaccion_grid.addWidget(self.fecha_pago_date, 0, 3)

        # Fila 2: Forma de Pago y Origen
        lbl_forma_pago = QLabel("💳 FORMA DE PAGO:")
        lbl_forma_pago.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        transaccion_grid.addWidget(lbl_forma_pago, 1, 0)

        from config.constants import FormaPago
        fp = FormaPago
        self.forma_pago_combo = QComboBox()
        self.forma_pago_combo.addItems([fp.EFECTIVO.value, fp.DEPOSITO.value, fp.TARJETA.value, fp.TRANSFERENCIA.value, fp.QR.value])
        self.forma_pago_combo.setMinimumHeight(30)
        transaccion_grid.addWidget(self.forma_pago_combo, 1, 1)

        lbl_origen = QLabel("🏦 ORIGEN/REFERENCIA:")
        lbl_origen.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        transaccion_grid.addWidget(lbl_origen, 1, 2)

        self.origen_transaccion_input = QLineEdit()
        self.origen_transaccion_input.setPlaceholderText("Ej: Banco XYZ, Caja, Nro de depósito...")
        self.origen_transaccion_input.setMinimumHeight(30)
        self.origen_transaccion_input.setMaximumHeight(40)
        transaccion_grid.addWidget(self.origen_transaccion_input, 1, 3)

        # Fila 3: Estado y Monto
        lbl_estado_trans = QLabel("📊 ESTADO TRANSACCIÓN:")
        lbl_estado_trans.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        transaccion_grid.addWidget(lbl_estado_trans, 2, 0)

        self.estado_transaccion_combo = QComboBox()
        self.estado_transaccion_combo.addItems(["PENDIENTE", "CONFIRMADO", "ANULADO"])
        self.estado_transaccion_combo.setMinimumHeight(30)
        self.estado_transaccion_combo.setCurrentText("CONFIRMADO")
        transaccion_grid.addWidget(self.estado_transaccion_combo, 2, 1)

        lbl_monto = QLabel("💰 MONTO A PAGAR:")
        lbl_monto.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        transaccion_grid.addWidget(lbl_monto, 2, 2)

        self.monto_pago_input = QLineEdit()
        self.monto_pago_input.setPlaceholderText("Ej: 1000.00")
        self.monto_pago_input.setMinimumHeight(30)
        self.monto_pago_input.setMaximumHeight(40)
        self.monto_pago_input.setValidator(QDoubleValidator(0.0, 9999999.99, 2))
        transaccion_grid.addWidget(self.monto_pago_input, 2, 3)

        layout.addLayout(transaccion_grid)

        # Establecer altura mínima para esta sección
        frame.setMinimumHeight(250)

        return frame
    
    def crear_separador(self, texto: str):
        """Crear separador con texto"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                padding: 5px 0px;
            }
        """)

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 5, 0, 5)

        # Línea izquierda
        linea1 = QFrame()
        linea1.setFrameShape(QFrame.Shape.HLine)
        linea1.setFrameShadow(QFrame.Shadow.Sunken)
        linea1.setStyleSheet("border: 1px solid #bdc3c7;")
        layout.addWidget(linea1)

        # Texto
        label = QLabel(texto)
        label.setStyleSheet("""
            font-weight: bold;
            color: #7f8c8d;
            font-size: 12px;
            padding: 0 15px;
        """)
        layout.addWidget(label)

        # Línea derecha
        linea2 = QFrame()
        linea2.setFrameShape(QFrame.Shape.HLine)
        linea2.setFrameShadow(QFrame.Shadow.Sunken)
        linea2.setStyleSheet("border: 1px solid #bdc3c7;")
        layout.addWidget(linea2)

        return frame
    
    # ===== MÉTODOS DE CONFIGURACIÓN =====
    
    def setup_validators(self):
        """Configurar validadores"""
        # Validar que solo números en CI si es necesario
        pass
    
    def setup_conexiones_especificas(self):
        """Configurar conexiones específicas - VERSIÓN CORREGIDA"""
        # Botones de búsqueda
        if hasattr(self, 'btn_buscar_estudiante'):
            self.btn_buscar_estudiante.clicked.connect(self.buscar_estudiantes_disponibles)
            
        if hasattr(self, 'btn_buscar_programa'):
            self.btn_buscar_programa.clicked.connect(self.buscar_programas_disponibles)
            
        # Botones de acción principal
        if hasattr(self, 'btn_realizar_inscripcion'):
            self.btn_realizar_inscripcion.clicked.connect(self.realizar_inscripcion)
            
        if hasattr(self, 'btn_cancelar_inscripcion'):
            self.btn_cancelar_inscripcion.clicked.connect(self.cancelar_inscripcion)
            
        # Botones del formulario de inscripción
        if hasattr(self, 'btn_registrar_inscripcion'):
            self.btn_registrar_inscripcion.clicked.connect(self.registrar_inscripcion)
            
        if hasattr(self, 'btn_registrar_transaccion'):
            self.btn_registrar_transaccion.clicked.connect(self.registrar_transaccion)
            
        if hasattr(self, 'btn_agregar_detalle'):
            self.btn_agregar_detalle.clicked.connect(self.agregar_detalle_transaccion)
            
        if hasattr(self, 'btn_eliminar_detalle'):
            self.btn_eliminar_detalle.clicked.connect(self.eliminar_detalle_seleccionado)
            
        if hasattr(self, 'btn_agregar_documento'):
            self.btn_agregar_documento.clicked.connect(self.agregar_documento_transaccion)
            
        if hasattr(self, 'btn_ver_documento'):
            self.btn_ver_documento.clicked.connect(self.ver_documento_seleccionado)
            
        if hasattr(self, 'btn_eliminar_documento'):
            self.btn_eliminar_documento.clicked.connect(self.eliminar_documento_seleccionado)
            
        if hasattr(self, 'btn_cancelar_formulario'):
            self.btn_cancelar_formulario.clicked.connect(self.cancelar_formulario_inscripcion)
            
        # Conexiones de selección en listas/tablas
        if hasattr(self, 'estudiantes_disponibles_table'):
            self.estudiantes_disponibles_table.itemDoubleClicked.connect(
                self.seleccionar_estudiante_desde_tabla
            )
            
        if hasattr(self, 'programas_disponibles_table'):
            self.programas_disponibles_table.itemDoubleClicked.connect(
                self.seleccionar_programa_desde_tabla
            )
            
        if hasattr(self, 'detalles_table'):
            self.detalles_table.itemSelectionChanged.connect(self.actualizar_botones_detalles)
            
        if hasattr(self, 'documentos_list_widget'):
            self.documentos_list_widget.itemSelectionChanged.connect(
                self.actualizar_botones_documentos
            )
            
        # Cambios en valores
        if hasattr(self, 'descuento_spin'):
            self.descuento_spin.valueChanged.connect(self.calcular_costo_total)
            
        # Conexión para mostrar/ocultar secciones basado en inscripcion_id
        QTimer.singleShot(100, self.actualizar_estado_formulario)
    
    # ===== MÉTODOS DE CONFIGURACIÓN DE INTERFAZ =====
    
    def configurar_interfaz_segun_contexto(self):
        """Configurar qué elementos mostrar según el contexto - VERSIÓN CORREGIDA"""
        # Limpiar listados anteriores
        self.limpiar_listados()
        
        logger.debug(f"Configurando interfaz con estudiante_id={self.estudiante_id} y programa_id={self.programa_id}")
        
        # Verificar que los widgets existan
        if not hasattr(self, 'grupo_info_estudiante'):
            logger.error("Widgets de interfaz no inicializados")
            return
        
        # CASO 1: Tenemos estudiante_id pero no programa_id
        if self.estudiante_id and not self.programa_id:
            self.grupo_info_estudiante.setVisible(True)
            self.grupo_buscar_estudiante.setVisible(False)
            self.grupo_info_programa.setVisible(False)
            self.grupo_programas_disponibles.setVisible(True)
            self.grupo_buscar_programa.setVisible(True)
            self.seccion_listado_frame.setVisible(True)
            self.seccion_formulario_frame.setVisible(False)
            
            # Configurar título
            if hasattr(self, 'titulo_listado_label'):
                self.titulo_listado_label.setText("🎓 PROGRAMAS INSCRITOS DEL ESTUDIANTE")
                
            # Cargar información
            self.cargar_info_estudiante(self.estudiante_id)
            self.cargar_programas_inscritos_estudiante()
            self.cargar_programas_disponibles_para_estudiante()
            
        # CASO 2: Tenemos programa_id pero no estudiante_id
        elif self.programa_id and not self.estudiante_id:
            self.grupo_info_estudiante.setVisible(False)
            self.grupo_buscar_estudiante.setVisible(True)
            self.grupo_info_programa.setVisible(True)
            self.grupo_programas_disponibles.setVisible(False)
            self.grupo_buscar_programa.setVisible(False)
            self.seccion_listado_frame.setVisible(True)
            self.seccion_formulario_frame.setVisible(False)
            
            # Configurar título
            if hasattr(self, 'titulo_listado_label'):
                self.titulo_listado_label.setText("👥 ESTUDIANTES INSCRITOS EN EL PROGRAMA")
                
            # Cargar información
            self.cargar_info_programa(self.programa_id)
            self.cargar_estudiantes_inscritos_programa()
            
        # CASO 3: Tenemos ambos IDs (modo inscripción)
        elif self.estudiante_id and self.programa_id:
            self.grupo_info_estudiante.setVisible(True)
            self.grupo_buscar_estudiante.setVisible(False)
            self.grupo_info_programa.setVisible(True)
            self.grupo_programas_disponibles.setVisible(False)
            self.grupo_buscar_programa.setVisible(False)
            self.seccion_listado_frame.setVisible(False)
            self.seccion_formulario_frame.setVisible(True)
            
            # Cargar información de ambos
            self.cargar_info_estudiante(self.estudiante_id)
            self.cargar_info_programa(self.programa_id)
            
            # Configurar formulario
            self.configurar_formulario_inscripcion()
            
        # CASO 4: No tenemos ni estudiante_id ni programa_id
        else:
            self.grupo_info_estudiante.setVisible(False)
            self.grupo_buscar_estudiante.setVisible(False)
            self.grupo_info_programa.setVisible(False)
            self.grupo_programas_disponibles.setVisible(False)
            self.grupo_buscar_programa.setVisible(False)
            self.seccion_listado_frame.setVisible(False)
            self.seccion_formulario_frame.setVisible(False)
    
    def actualizar_estado_formulario(self):
        """Actualizar la visibilidad de las secciones según el estado - VERSIÓN CORREGIDA"""
        # Determinar qué secciones mostrar
        tiene_inscripcion = bool(self.inscripcion_id)
        tiene_estudiante_programa = bool(self.estudiante_id and self.programa_id)

        if tiene_inscripcion:
            # Ya tenemos inscripción registrada: mostrar TODAS las secciones
            self.seccion_transaccion_frame.setVisible(True)
            self.seccion_detalles_documentos_frame.setVisible(True)

            # Actualizar label de ID
            self.inscripcion_id_label.setText(f"✅ ID de inscripción: <b>{self.inscripcion_id}</b>")
            self.inscripcion_id_label.setStyleSheet("""
                color: #27ae60;
                font-weight: bold;
                padding: 10px;
                background-color: #eafaf1;
                border-radius: 6px;
                border: 1px solid #27ae60;
            """)

            # Deshabilitar botón de registrar inscripción
            self.btn_registrar_inscripcion.setEnabled(False)
            self.btn_registrar_inscripcion.setText("✅ INSCRIPCIÓN REGISTRADA")
            self.btn_registrar_inscripcion.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    padding: 0 20px;
                    opacity: 0.8;
                }
            """)

            # Habilitar botón de registrar transacción
            self.btn_registrar_transaccion.setEnabled(True)

            # Cargar historial de transacciones existentes
            self.cargar_historial_transacciones()

        elif tiene_estudiante_programa and not tiene_inscripcion:
            # Tenemos estudiante y programa pero no inscripción: mostrar solo datos básicos
            self.seccion_transaccion_frame.setVisible(False)
            self.seccion_detalles_documentos_frame.setVisible(False)

            # Actualizar label de ID
            self.inscripcion_id_label.setText("📋 ID de inscripción: <span style='color:#7f8c8d; font-style:italic;'>No registrado</span>")
            self.inscripcion_id_label.setStyleSheet("""
                font-size: 13px;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                text-align: center;
            """)

            # Habilitar botón de registrar inscripción
            self.btn_registrar_inscripcion.setEnabled(True)
            self.btn_registrar_inscripcion.setText("✅ REGISTRAR INSCRIPCIÓN")
            self.btn_registrar_inscripcion.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #27ae60, stop:1 #219653);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 0 30px;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #219653, stop:1 #1e8449);
                }
            """)

            # Deshabilitar secciones de transacción
            self.btn_registrar_transaccion.setEnabled(False)

        else:
            # No hay suficiente información: ocultar todo
            self.seccion_transaccion_frame.setVisible(False)
            self.seccion_detalles_documentos_frame.setVisible(False)
            self.btn_registrar_inscripcion.setEnabled(False)
            self.btn_registrar_transaccion.setEnabled(False)
    
    # ===== MÉTODOS DE CARGA DE DATOS =====
    
    def cargar_info_estudiante(self, estudiante_id: int):
        """Cargar información del estudiante en el panel izquierdo"""
        try:
            estudiante = EstudianteModel.buscar_estudiante_id(estudiante_id)
            if estudiante:
                self.estudiante_data = estudiante
                
                # Actualizar interfaz
                ci_completo = f"{estudiante.get('ci_numero', '')}-{estudiante.get('ci_expedicion', '')}"
                self.estudiante_ci_label.setText(ci_completo)
                
                nombre_completo = f"{estudiante.get('nombres', '')} {estudiante.get('apellido_paterno', '')} {estudiante.get('apellido_materno', '')}".strip()
                self.estudiante_nombre_label.setText(nombre_completo)
                self.estudiante_nombre_form_label.setText(nombre_completo)
                
                self.estudiante_email_label.setText(estudiante.get('email', 'No registrado'))
                self.estudiante_telefono_label.setText(estudiante.get('telefono', 'No registrado'))
                self.estudiante_profesion_label.setText(estudiante.get('profesion', 'No registrado'))
                self.estudiante_universidad_label.setText(estudiante.get('universidad', 'No registrado'))
                self.estudiante_direccion_label.setText(estudiante.get('direccion', 'No registrada'))
                
        except Exception as e:
            logger.error(f"Error cargando información del estudiante: {e}")
    
    def cargar_info_programa(self, programa_id: int):
        """Cargar información del programa en el panel derecho"""
        try:
            resultado = ProgramaModel.obtener_programa(programa_id)
            if resultado.get('success') and resultado.get('data'):
                programa = resultado['data']
                self.programa_data = programa
                
                # Actualizar interfaz
                self.programa_codigo_label.setText(programa.get('codigo', ''))
                self.programa_nombre_label.setText(programa.get('nombre', ''))
                self.programa_duracion_label.setText(f"{programa.get('duracion_meses', 0)} meses")
                self.programa_horas_label.setText(f"{programa.get('horas_totales', 0)} horas")
                
                cupos_inscritos = programa.get('cupos_inscritos', 0)
                cupos_maximos = programa.get('cupos_maximos', 0)
                cupos_text = f"{cupos_inscritos}/{cupos_maximos if cupos_maximos else '∞'}"
                self.programa_cupos_label.setText(cupos_text)
                
                estado = programa.get('estado', '')
                self.programa_estado_label.setText(estado)
                
                # Color según estado
                from config.constants import EstadoPrograma
                if estado == EstadoPrograma.EN_CURSO:
                    self.programa_estado_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                elif estado == EstadoPrograma.INSCRIPCIONES:
                    self.programa_estado_label.setStyleSheet("color: #2980b9; font-weight: bold;")
                elif estado == EstadoPrograma.PLANIFICADO:
                    self.programa_estado_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                elif estado == EstadoPrograma.CONCLUIDO:
                    self.programa_estado_label.setStyleSheet("color: #95a5a6; font-weight: bold;")
                else:
                    self.programa_estado_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                
                # Costos
                self.programa_matricula_label.setText(f"{programa.get('costo_matricula', 0):.2f} Bs")
                self.programa_costo_inscripcion_label.setText(f"{programa.get('costo_inscripcion', 0):.2f} Bs")
                self.programa_total_label.setText(f"{programa.get('costo_total', 0):.2f} Bs")
                
                # Docente
                docente_id = programa.get('docente_coordinador_id')
                docente_nombre = "No asignado"
                
                if docente_id:
                    from model.docente_model import DocenteModel
                    docente = DocenteModel.obtener_docente_por_id(docente_id)
                    if docente:
                        docente_nombre = f"{docente.get('grado_academico', '')} {docente.get('nombres', '')} {docente.get('apellido_paterno', '')}".strip()
                
                self.programa_docente_label.setText(docente_nombre)
                
                # IMPLEMENTACIÓN DEL TODO: Cargar resumen de inscritos y recaudado
                self.calcular_resumen_programa(programa_id)
                
        except Exception as e:
            logger.error(f"Error cargando información del programa: {e}")
            self.mostrar_mensaje("Error", f"Error al cargar información del programa: {str(e)}", "error")
    
    def cargar_programas_inscritos_estudiante(self):
        """Cargar los programas en los que el estudiante está inscrito"""
        try:
            # Limpiar listado anterior
            while self.listado_layout_container.count():
                child = self.listado_layout_container.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()

            # Obtener programas inscritos del estudiante desde la base de datos
            from model.inscripcion_model import InscripcionModel
            if not self.estudiante_id:
                return

            programas = InscripcionModel.obtener_programas_inscritos_estudiante(self.estudiante_id)

            # Factor dinámico basado en cantidad de programas
            factor = len(programas) if programas else 1

            if not programas:
                # Mostrar mensaje si no hay programas
                no_data_frame = QFrame()
                no_data_frame.setStyleSheet("""
                    QFrame {
                        background-color: #f8f9fa;
                        border: 2px dashed #bdc3c7;
                        border-radius: 10px;
                        padding: 40px;
                    }
                """)
                no_data_frame.setMinimumHeight(200)
                no_data_frame.setMaximumHeight(300)

                no_data_layout = QVBoxLayout(no_data_frame)
                no_data_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                icon_label = QLabel("🎯")
                icon_label.setStyleSheet("font-size: 50px;")
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                no_data_layout.addWidget(icon_label)

                message_label = QLabel("El estudiante no está inscrito en ningún programa")
                message_label.setStyleSheet("""
                    color: #7f8c8d;
                    font-size: 16px;
                    font-weight: bold;
                    text-align: center;
                """)
                no_data_layout.addWidget(message_label)

                sub_message = QLabel("Puede inscribirlo a un programa de la lista 'PROGRAMAS DISPONIBLES'")
                sub_message.setStyleSheet("""
                    color: #95a5a6;
                    font-style: italic;
                    font-size: 13px;
                    text-align: center;
                """)
                no_data_layout.addWidget(sub_message)

                self.listado_layout_container.addWidget(no_data_frame)

                # Altura para mensaje vacío
                altura_recomendada = 200
            else:
                # Crear un widget contenedor con scroll propio para los programas
                programas_container = QWidget()
                programas_layout = QVBoxLayout(programas_container)
                programas_layout.setSpacing(15)
                programas_layout.setContentsMargins(5, 5, 5, 5)

                # Procesar cada programa inscrito
                for programa_data in programas:
                    try:
                        # Enriquecer datos con información de transacciones y cálculos
                        programa_enriquecido = self.enriquecer_datos_programa_inscrito(programa_data)

                        # Crear widget para mostrar el programa
                        item_widget = self.crear_item_programa_inscrito(programa_enriquecido)
                        programas_layout.addWidget(item_widget)

                    except Exception as e:
                        logger.error(f"Error procesando programa {programa_data.get('codigo', 'desconocido')}: {e}")
                        # Mostrar un item de error para este programa
                        error_widget = self.crear_item_error_programa(programa_data, str(e))
                        programas_layout.addWidget(error_widget)

                programas_layout.addStretch()

                # Agregar el contenedor al scroll principal
                self.listado_layout_container.addWidget(programas_container)

                # Calcular altura dinámica basada en cantidad de programas
                # Cada programa ocupa aproximadamente 320-350px
                altura_por_programa = 320
                altura_minima_base = 150
                altura_maxima = 800  # No más de 800px

                altura_recomendada = min(
                    altura_maxima, 
                    max(altura_minima_base, factor * altura_por_programa)
                )

                # Establecer altura mínima y máxima
                programas_container.setMinimumHeight(altura_recomendada)

            # Ajustar el QScrollArea para mostrar todos los items
            self.listado_scroll.setMinimumHeight(altura_recomendada + 50)  # +50px para bordes y margenes
            self.listado_scroll.setMaximumHeight(altura_recomendada + 100)

            logger.debug(f"✅ Programas cargados: {factor}, Altura configurada: {altura_recomendada}px")

        except Exception as e:
            logger.error(f"Error cargando programas inscritos: {e}")
            self.mostrar_mensaje("Error", f"Error al cargar programas inscritos: {str(e)}", "error")
    
    def cargar_estudiantes_inscritos_programa(self):
        """Cargar los estudiantes inscritos en el programa"""
        try:
            # Limpiar listado anterior
            while self.listado_layout_container.count():
                child = self.listado_layout_container.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()

            # TODO: Obtener estudiantes inscritos en el programa desde la base de datos
            # Por ahora, datos de ejemplo
            estudiantes_ejemplo = [
                {
                    'ci_numero': '1234567',
                    'ci_expedicion': 'LP',
                    'nombres': 'Juan Carlos',
                    'apellido_paterno': 'Pérez',
                    'email': 'juan@email.com',
                    'telefono': '77777777',
                    'estado_inscripcion': 'INSCRITO',
                    'saldo_pendiente': 300.00,
                    'pagos': [
                        {'fecha': '2024-01-20', 'monto': 700.00, 'forma_pago': 'TARJETA', 
                        'comprobante': 'TARJ-001', 'estado': 'CONFIRMADO'}
                    ]
                },
                {
                    'ci_numero': '7654321',
                    'ci_expedicion': 'SC',
                    'nombres': 'María Fernanda',
                    'apellido_paterno': 'Gómez',
                    'email': 'maria@email.com',
                    'telefono': '78888888',
                    'estado_inscripcion': 'PREINSCRITO',
                    'saldo_pendiente': 1200.00,
                    'pagos': []
                }
            ]

            factor = len(estudiantes_ejemplo)

            for estudiante in estudiantes_ejemplo:
                item_widget = self.crear_item_estudiante_inscrito(estudiante)
                self.listado_layout_container.addWidget(item_widget)

            self.listado_layout_container.addStretch()

            # Calcular altura dinámica basada en cantidad de estudiantes
            # Cada estudiante ocupa aproximadamente 250px
            altura_por_estudiante = 250
            altura_minima_base = 150
            altura_maxima = 600

            altura_recomendada = min(
                altura_maxima,
                max(altura_minima_base, factor * altura_por_estudiante)
            )

            # Ajustar el QScrollArea
            self.listado_scroll.setMinimumHeight(altura_recomendada + 50)
            self.listado_scroll.setMaximumHeight(altura_recomendada + 100)

            logger.debug(f"✅ Estudiantes cargados: {factor}, Altura configurada: {altura_recomendada}px")

        except Exception as e:
            logger.error(f"Error cargando estudiantes inscritos: {e}")
    
    def crear_item_estudiante_inscrito(self, estudiante_data: Dict):
        """Crear un item para mostrar un estudiante inscrito en el programa"""
        # Contenedor principal
        main_frame = QFrame()
        main_frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        main_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #2980b9;
                border-radius: 10px;
                margin: 10px 5px;
            }
            QFrame:hover {
                background-color: #f8f9fa;
                border: 2px solid #2980b9;
            }
        """)
        
        main_layout = QVBoxLayout(main_frame)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 15, 20, 15)
        
        # ===== ENCABEZADO DEL ESTUDIANTE =====
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e3f2fd, stop:1 #bbdefb);
                border-radius: 8px;
                padding: 0px;
            }
        """)
        header_layout = QGridLayout(header_frame)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(15, 12, 15, 12)
        
        # CI del estudiante
        ci_label = QLabel("👤 CI:")
        ci_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(ci_label, 0, 0)
        
        ci_value = QLabel(f"{estudiante_data.get('ci_numero', 'N/A')}-{estudiante_data.get('ci_expedicion', '')}")
        ci_value.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #2980b9;
            padding: 3px 10px;
            background-color: white;
            border-radius: 4px;
        """)
        header_layout.addWidget(ci_value, 0, 1)
        
        # Nombre del estudiante
        nombre_label = QLabel("📚 ESTUDIANTE:")
        nombre_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(nombre_label, 0, 2)
        
        nombre_value = QLabel(f"{estudiante_data.get('nombres', '')} {estudiante_data.get('apellido_paterno', '')}")
        nombre_value.setStyleSheet("""
            font-weight: bold;
            color: #2c3e50;
            font-size: 13px;
            padding: 3px 10px;
            background-color: white;
            border-radius: 4px;
        """)
        nombre_value.setWordWrap(True)
        header_layout.addWidget(nombre_value, 0, 3, 1, 2)
        
        # Email
        email_label = QLabel("📧 EMAIL:")
        email_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(email_label, 1, 0)
        
        email_value = QLabel(estudiante_data.get('email', 'N/A'))
        email_value.setStyleSheet("color: #3498db; font-size: 12px;")
        header_layout.addWidget(email_value, 1, 1)
        
        # Teléfono
        telefono_label = QLabel("📞 TELÉFONO:")
        telefono_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(telefono_label, 1, 2)
        
        telefono_value = QLabel(estudiante_data.get('telefono', 'N/A'))
        header_layout.addWidget(telefono_value, 1, 3)
        
        # Estado de inscripción
        estado_label = QLabel("📊 ESTADO:")
        estado_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(estado_label, 1, 4)
        
        estado_value = estudiante_data.get('estado_inscripcion', 'N/A')
        estado_text = QLabel(estado_value)
        
        # Mapear estados a colores
        estado_colors = {
            'INSCRITO': "#27ae60",
            'PREINSCRITO': "#f39c12",
            'EN_CURSO': "#2980b9",
            'RETIRADO': "#e74c3c"
        }
        estado_color = estado_colors.get(estado_value, "#7f8c8d")
        
        estado_text.setStyleSheet(f"""
            font-weight: bold;
            font-size: 12px;
            color: white;
            background-color: {estado_color};
            padding: 4px 12px;
            border-radius: 12px;
            min-width: 80px;
            text-align: center;
        """)
        header_layout.addWidget(estado_text, 1, 4)
        
        main_layout.addWidget(header_frame)
        
        # ===== INFORMACIÓN FINANCIERA =====
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        info_layout = QGridLayout(info_frame)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 12, 15, 12)
        
        # Saldo pendiente
        saldo_label = QLabel("💰 SALDO PENDIENTE:")
        saldo_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        info_layout.addWidget(saldo_label, 0, 0)
        
        saldo_pendiente = estudiante_data.get('saldo_pendiente', 0) or 0
        saldo_text = QLabel(f"{saldo_pendiente:.2f} Bs")
        saldo_text.setStyleSheet("font-weight: bold; color: #e74c3c;")
        info_layout.addWidget(saldo_text, 0, 1)
        
        main_layout.addWidget(info_frame)
        
        # ===== HISTÓRICO DE PAGOS =====
        pagos = estudiante_data.get('pagos', [])
        if pagos:
            pagos_header = QLabel("📊 ÚLTIMOS PAGOS")
            pagos_header.setStyleSheet("""
                font-weight: bold;
                font-size: 12px;
                color: #2c3e50;
                padding: 8px 0px;
                border-bottom: 1px solid #3498db;
            """)
            main_layout.addWidget(pagos_header)
            
            # Tabla de pagos
            pagos_table = QTableWidget()
            pagos_table.setColumnCount(5)
            pagos_table.setHorizontalHeaderLabels(["Fecha", "Monto", "Forma", "Comprobante", "Estado"])
            pagos_table.horizontalHeader().setStretchLastSection(True)
            pagos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            pagos_table.setAlternatingRowColors(True)
            pagos_table.setMaximumHeight(120)
            
            pagos_table.setRowCount(len(pagos))
            
            for i, pago in enumerate(pagos):
                pagos_table.setItem(i, 0, QTableWidgetItem(pago.get('fecha', '')))
                pagos_table.setItem(i, 1, QTableWidgetItem(f"{pago.get('monto', 0):.2f}"))
                pagos_table.setItem(i, 2, QTableWidgetItem(pago.get('forma_pago', '')))
                pagos_table.setItem(i, 3, QTableWidgetItem(pago.get('comprobante', '')[:15]))
                
                estado_item = QTableWidgetItem(pago.get('estado', ''))
                if pago.get('estado') == 'CONFIRMADO':
                    estado_item.setForeground(QBrush(QColor("#27ae60")))
                pagos_table.setItem(i, 4, estado_item)
            
            main_layout.addWidget(pagos_table)
        
        return main_frame
    
    def cargar_programas_disponibles_para_estudiante(self):
        """Cargar programas disponibles para el estudiante (no inscritos)"""
        try:
            self.programas_disponibles_table.setRowCount(0)

            # Obtener programas en estado INSCRIPCIONES o EN_CURSO
            from config.database import Database
            connection = Database.get_connection()
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT 
                    p.id,
                    p.codigo,
                    p.nombre,
                    p.estado,
                    p.cupos_maximos,
                    p.cupos_inscritos,
                    p.costo_total,
                    p.costo_matricula,
                    p.costo_inscripcion,
                    p.costo_mensualidad,
                    p.numero_cuotas,
                    CASE 
                        WHEN p.cupos_maximos IS NULL THEN TRUE
                        WHEN p.cupos_inscritos < p.cupos_maximos THEN TRUE
                        ELSE FALSE
                    END as tiene_cupos,
                    CASE 
                        WHEN EXISTS (
                            SELECT 1 FROM inscripciones i 
                            WHERE i.estudiante_id = %s 
                            AND i.programa_id = p.id
                            AND i.estado NOT IN ('RETIRADO')
                        ) THEN TRUE
                        ELSE FALSE
                    END as ya_inscrito
                FROM programas p
                WHERE p.estado IN ('INSCRIPCIONES', 'EN_CURSO')
                AND p.estado != 'CANCELADO'
                ORDER BY p.estado, p.codigo
                """

                cursor.execute(query, (self.estudiante_id,))
                resultados = cursor.fetchall()
                cursor.close()
                Database.return_connection(connection)

                # Filtrar solo programas no inscritos y con cupos
                programas_disponibles = []
                column_names = [desc[0] for desc in cursor.description]

                for row in resultados:
                    programa = dict(zip(column_names, row))
                    # Solo mostrar programas no inscritos y con cupos disponibles
                    if not programa.get('ya_inscrito', False) and programa.get('tiene_cupos', True):
                        programas_disponibles.append(programa)

                factor = len(programas_disponibles)

                # Configurar altura de la tabla dinámicamente
                altura_por_fila = 40  # Altura aproximada por fila
                altura_minima_tabla = 150
                altura_maxima_tabla = 400

                altura_tabla = min(
                    altura_maxima_tabla,
                    max(altura_minima_tabla, factor * altura_por_fila + 40)  # +40px para encabezado
                )

                self.programas_disponibles_table.setMinimumHeight(altura_tabla)
                self.programas_disponibles_table.setMaximumHeight(altura_tabla + 50)

                self.programas_disponibles_table.setRowCount(factor)

                for i, programa in enumerate(programas_disponibles):
                    # Código
                    codigo_item = QTableWidgetItem(programa['codigo'])
                    self.programas_disponibles_table.setItem(i, 0, codigo_item)

                    # Nombre
                    nombre_item = QTableWidgetItem(programa['nombre'])
                    nombre_item.setToolTip(programa['nombre'])
                    self.programas_disponibles_table.setItem(i, 1, nombre_item)

                    # Estado
                    estado = programa['estado']
                    estado_item = QTableWidgetItem(estado)
                    estado_color = "#27ae60" if estado == 'EN_CURSO' else "#2980b9"
                    estado_item.setForeground(QBrush(QColor(estado_color)))
                    self.programas_disponibles_table.setItem(i, 2, estado_item)

                    # Cupos
                    cupos_max = programa.get('cupos_maximos', '∞')
                    cupos_ins = programa.get('cupos_inscritos', 0)
                    cupos_text = f"{cupos_ins}/{cupos_max if cupos_max else '∞'}"
                    self.programas_disponibles_table.setItem(i, 3, QTableWidgetItem(cupos_text))

                    # Costo
                    costo_total = programa.get('costo_total', 0)
                    self.programas_disponibles_table.setItem(i, 4, QTableWidgetItem(f"{costo_total:.2f} Bs"))

                    # Botón Inscribir
                    programa_id = programa.get('id')
                    if programa_id:  # Asegurar que tenemos un ID válido
                        btn_inscribir = QPushButton("📝 INSCRIBIR")
                        btn_inscribir.setStyleSheet("""
                            QPushButton {
                                background-color: #3498db;
                                color: white;
                                border: none;
                                border-radius: 4px;
                                padding: 5px 10px;
                                font-size: 11px;
                                min-width: 80px;
                            }
                            QPushButton:hover {
                                background-color: #2980b9;
                            }
                        """)
                        # CORRECCIÓN: Pasar solo el ID (entero) no el diccionario completo
                        btn_inscribir.clicked.connect(lambda checked, pid=programa_id: self.seleccionar_programa_para_inscribir(pid))
                        self.programas_disponibles_table.setCellWidget(i, 5, btn_inscribir)

                logger.debug(f"✅ Programas disponibles cargados: {factor}, Altura tabla: {altura_tabla}px")

            else:
                # No hay conexión a la base de datos
                self.programas_disponibles_table.setRowCount(0)

        except Exception as e:
            logger.error(f"Error cargando programas disponibles: {e}")
            self.mostrar_mensaje("Error", f"Error al cargar programas disponibles: {str(e)}", "error")
    
    def cargar_datos_inscripcion_existente(self):
        """Cargar datos de una inscripción existente"""
        try:
            if not self.inscripcion_id:
                return
            
            # Obtener datos de la inscripción
            from config.database import Database
            connection = Database.get_connection()
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT fecha_inscripcion, estado, descuento_aplicado, observaciones
                FROM inscripciones WHERE id = %s
                """
                cursor.execute(query, (self.inscripcion_id,))
                result = cursor.fetchone()
                cursor.close()
                Database.return_connection(connection)
                
                if result:
                    # Configurar fecha
                    fecha = result[0]
                    if fecha:
                        qdate = QDate.fromString(str(fecha)[:10], 'yyyy-MM-dd')
                        if qdate.isValid():
                            self.fecha_inscripcion_date.setDate(qdate)
                    
                    # Configurar estado
                    estado = result[1]
                    if estado:
                        index = self.estado_inscripcion_combo.findText(estado)
                        if index >= 0:
                            self.estado_inscripcion_combo.setCurrentIndex(index)
                    
                    # Configurar descuento
                    descuento = result[2]
                    if descuento:
                        self.descuento_spin.setValue(float(descuento))
                    
        except Exception as e:
            logger.error(f"Error cargando datos de inscripción: {e}")
    
    def crear_historial_table(self):
        """Crear tabla para mostrar historial de transacciones - VERSIÓN CORREGIDA"""
        try:
            self.historial_table = QTableWidget()
            self.historial_table.setObjectName("historialTable")
            self.historial_table.setColumnCount(7)
            self.historial_table.setHorizontalHeaderLabels([
                "ID", "Fecha", "Monto", "Forma Pago", "Estado", "Documentos", "Acción"
            ])

            # Configurar header
            header = self.historial_table.horizontalHeader()
            header.setStretchLastSection(True)

            # Configurar modos de redimensionamiento
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Fecha
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Monto
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Forma Pago
            header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Estado
            header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Documentos
            header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # Acción

            # Configurar tabla
            self.historial_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            self.historial_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.historial_table.setAlternatingRowColors(True)
            self.historial_table.setMinimumHeight(150)
            self.historial_table.setMaximumHeight(300)

            # Estilo
            self.historial_table.setStyleSheet("""
                #historialTable {
                    font-size: 12px;
                    background-color: white;
                    alternate-background-color: #f8f9fa;
                    gridline-color: #ecf0f1;
                }
                #historialTable::item {
                    padding: 5px;
                }
                #historialTable QHeaderView::section {
                    background-color: #2c3e50;
                    color: white;
                    padding: 8px;
                    font-weight: bold;
                    border: none;
                }
                #historialTable::item:selected {
                    background-color: #3498db;
                    color: white;
                }
            """)

            logger.debug("✅ Tabla de historial creada correctamente")

        except Exception as e:
            logger.error(f"Error creando tabla de historial: {e}")
            # Crear tabla simple como fallback
            self.historial_table = QTableWidget()
            self.historial_table.setColumnCount(7)
            self.historial_table.setHorizontalHeaderLabels([
                "ID", "Fecha", "Monto", "Forma Pago", "Estado", "Documentos", "Acción"
            ])
    
    def cargar_historial_transacciones(self):
        """Cargar historial de transacciones de la inscripción"""
        try:
            if not self.inscripcion_id:
                return
            
            # Limpiar tabla
            self.historial_table.setRowCount(0)
            
            # Obtener transacciones de la inscripción
            transacciones = TransaccionModel.obtener_transacciones_inscripcion(self.inscripcion_id)
            
            if transacciones:
                self.historial_table.setRowCount(len(transacciones))
                
                for i, transaccion in enumerate(transacciones):
                    # ID
                    self.historial_table.setItem(i, 0, QTableWidgetItem(str(transaccion.get('id', ''))))
                    
                    # Fecha
                    fecha = transaccion.get('fecha_pago', '')
                    self.historial_table.setItem(i, 1, QTableWidgetItem(str(fecha)[:10] if fecha else ''))
                    
                    # Monto
                    monto = transaccion.get('monto_final', 0)
                    self.historial_table.setItem(i, 2, QTableWidgetItem(f"{monto:.2f} Bs"))
                    
                    # Forma de pago
                    self.historial_table.setItem(i, 3, QTableWidgetItem(transaccion.get('forma_pago', '')))
                    
                    # Estado
                    estado = transaccion.get('estado', '')
                    estado_item = QTableWidgetItem(estado)
                    if estado == 'CONFIRMADO':
                        estado_item.setForeground(QBrush(QColor("#27ae60")))
                    elif estado == 'PENDIENTE':
                        estado_item.setForeground(QBrush(QColor("#f39c12")))
                    else:
                        estado_item.setForeground(QBrush(QColor("#e74c3c")))
                    self.historial_table.setItem(i, 4, estado_item)
                    
                    # Documentos
                    num_docs = transaccion.get('numero_documentos', 0)
                    self.historial_table.setItem(i, 5, QTableWidgetItem(f"{num_docs} doc(s)"))
                    
                    # Botón ver detalles
                    btn_ver = QPushButton("👁️ VER")
                    btn_ver.setStyleSheet("""
                        QPushButton {
                            background-color: #3498db;
                            color: white;
                            border: none;
                            border-radius: 4px;
                            padding: 3px 8px;
                            font-size: 11px;
                        }
                        QPushButton:hover {
                            background-color: #2980b9;
                        }
                    """)
                    transaccion_id = transaccion.get('id')
                    if transaccion_id:
                        btn_ver.clicked.connect(lambda checked, tid=transaccion_id: 
                                                self.ver_detalles_transaccion(tid))
                    self.historial_table.setCellWidget(i, 6, btn_ver)
                    
        except Exception as e:
            logger.error(f"Error cargando historial de transacciones: {e}")
    
    # ===== MÉTODOS DE BÚSQUEDA =====
    
    def buscar_estudiantes_disponibles(self):
        """Buscar estudiantes no inscritos en el programa actual"""
        search_term = self.estudiante_search_input.text().strip()
        
        if not search_term:
            self.mostrar_mensaje("Advertencia", "Ingrese un término de búsqueda", "warning")
            return
        
        try:
            self.estudiantes_disponibles_table.setRowCount(0)
            self.estudiante_status_label.setText("🔍 Buscando estudiantes...")
            self.estudiante_status_label.setStyleSheet("color: #f39c12;")
            
            # TODO: Implementar búsqueda real de estudiantes no inscritos en este programa
            # Por ahora, datos de ejemplo
            estudiantes_ejemplo = [
                {
                    'id': 3,
                    'ci_numero': '8888888',
                    'ci_expedicion': 'CB',
                    'nombres': 'Carlos Andrés',
                    'apellido_paterno': 'Rodríguez',
                    'email': 'carlos@email.com',
                    'telefono': '79999999'
                },
                {
                    'id': 4,
                    'ci_numero': '9999999',
                    'ci_expedicion': 'PT',
                    'nombres': 'Ana Lucía',
                    'apellido_paterno': 'Torrez',
                    'email': 'ana@email.com',
                    'telefono': '71111111'
                }
            ]
            
            self.estudiantes_disponibles_table.setRowCount(len(estudiantes_ejemplo))
            
            for i, estudiante in enumerate(estudiantes_ejemplo):
                # CI
                ci_completo = f"{estudiante['ci_numero']}-{estudiante['ci_expedicion']}"
                ci_item = QTableWidgetItem(ci_completo)
                self.estudiantes_disponibles_table.setItem(i, 0, ci_item)
                
                # Nombre
                nombre_completo = f"{estudiante['nombres']} {estudiante['apellido_paterno']}"
                self.estudiantes_disponibles_table.setItem(i, 1, QTableWidgetItem(nombre_completo))
                
                # Email
                self.estudiantes_disponibles_table.setItem(i, 2, QTableWidgetItem(estudiante['email']))
                
                # Teléfono
                self.estudiantes_disponibles_table.setItem(i, 3, QTableWidgetItem(estudiante['telefono']))
                
                # Botón Inscribir
                btn_inscribir = QPushButton("📝 INSCRIBIR")
                btn_inscribir.setStyleSheet("""
                    QPushButton {
                        background-color: #27ae60;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        padding: 5px 10px;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background-color: #219653;
                    }
                """)
                btn_inscribir.clicked.connect(lambda checked, e=estudiante: self.seleccionar_estudiante_para_inscribir(e))
                self.estudiantes_disponibles_table.setCellWidget(i, 4, btn_inscribir)
            
            self.estudiante_status_label.setText(f"✅ Encontrados {len(estudiantes_ejemplo)} estudiantes")
            self.estudiante_status_label.setStyleSheet("color: #27ae60;")
            
        except Exception as e:
            logger.error(f"Error buscando estudiantes: {e}")
            self.estudiante_status_label.setText(f"❌ Error: {str(e)}")
            self.estudiante_status_label.setStyleSheet("color: #e74c3c;")
    
    def buscar_programas_disponibles(self):
        """Buscar programas disponibles"""
        search_term = self.programa_search_input.text().strip()
        
        if not search_term:
            self.mostrar_mensaje("Advertencia", "Ingrese un término de búsqueda", "warning")
            return
        
        # Por ahora, solo mostrar mensaje
        self.mostrar_mensaje("Información", "Búsqueda de programas implementada en cargar_programas_disponibles_para_estudiante()", "info")
    
    # ===== MÉTODOS DE SELECCIÓN =====
    
    def seleccionar_estudiante_desde_tabla(self, item):
        """Seleccionar estudiante desde la tabla"""
        row = item.row()
        estudiante_id_item = self.estudiantes_disponibles_table.item(row, 0)
        # TODO: Obtener ID real del estudiante
        if estudiante_id_item:
            # Por ahora, simular selección
            estudiante_ejemplo = {
                'id': 3,
                'ci_numero': '8888888',
                'ci_expedicion': 'CB',
                'nombres': 'Carlos Andrés',
                'apellido_paterno': 'Rodríguez'
            }
            self.seleccionar_estudiante_para_inscribir(estudiante_ejemplo)
    
    def seleccionar_programa_desde_tabla(self, item):
        """Seleccionar programa desde la tabla"""
        row = item.row()
        programa_id_item = self.programas_disponibles_table.item(row, 0)
        # TODO: Obtener ID real del programa
        if programa_id_item:
            # Por ahora, simular selección
            programa_ejemplo_id = 1  # ID de ejemplo
            self.seleccionar_programa_para_inscribir(programa_ejemplo_id)
    
    def seleccionar_estudiante_para_inscribir(self, estudiante_data):
        """Seleccionar estudiante para inscribir en el programa actual"""
        self.estudiante_id = estudiante_data.get('id')
        self.estudiante_data = estudiante_data
        
        # Actualizar interfaz para modo inscripción
        self.configurar_interfaz_segun_contexto()
    
    def seleccionar_programa_para_inscribir(self, programa_id: int):
        """Seleccionar programa para inscribir al estudiante actual"""
        try:
            # Cargar información del programa
            resultado = ProgramaModel.obtener_programa(programa_id)
            if resultado.get('success') and resultado.get('data'):
                self.programa_id = programa_id
                self.programa_data = resultado['data']
                
                # Actualizar interfaz para modo inscripción
                self.configurar_interfaz_segun_contexto()
            else:
                mensaje = resultado.get('message', 'Error desconocido')
                self.mostrar_mensaje("Error", f"No se pudo cargar el programa: {mensaje}", "error")
                
        except Exception as e:
            logger.error(f"Error seleccionando programa: {e}")
            self.mostrar_mensaje("Error", f"Error al seleccionar programa: {str(e)}", "error")
    
    # ===== MÉTODOS DE INSCRIPCIÓN (FLUJO PRINCIPAL) =====
    
    def registrar_inscripcion(self):
        """Registrar la inscripción en la base de datos"""
        try:
            # Validar datos básicos
            if not self.estudiante_id or not self.programa_id:
                self.mostrar_mensaje("Error", "Seleccione estudiante y programa", "error")
                return
            
            # Obtener la fecha del QDateEdit y convertirla a string en formato 'yyyy-MM-dd'
            qdate = self.fecha_inscripcion_date.date()
            fecha_str = qdate.toString('yyyy-MM-dd')  # Formato compatible con PostgreSQL
            
            # Preparar datos
            datos = {
                'estudiante_id': self.estudiante_id,
                'programa_id': self.programa_id,
                'fecha_inscripcion': self.fecha_inscripcion_date.date().toString('yyyy-MM-dd'),
                'estado': self.estado_inscripcion_combo.currentText(),
                'descuento_aplicado': self.descuento_spin.value(),
                'observaciones': None  # Puedes agregar campo para observaciones
            }
            
            # Llamar al modelo para crear inscripción
            resultado = InscripcionModel.crear_inscripcion(
                estudiante_id=datos['estudiante_id'],
                programa_id=datos['programa_id'],
                descuento_aplicado=datos['descuento_aplicado'],
                observaciones=datos['observaciones'],
                fecha_inscripcion=datos['fecha_inscripcion']
            )
            
            if resultado.get('exito', False) or resultado.get('success', False):
                # Obtener el ID de la inscripción creada
                self.inscripcion_id = resultado.get('inscripcion_id') or resultado.get('id')
                
                if not self.inscripcion_id:
                    # Intentar obtener el ID de otra forma
                    self.inscripcion_id = self.obtener_ultimo_id_inscripcion()
                    
                if self.inscripcion_id:
                    # Actualizar interfaz para mostrar secciones de transacción
                    self.actualizar_estado_formulario()
                    
                    # Actualizar título del formulario
                    self.titulo_formulario_label.setText(
                        f"✅ INSCRIPCIÓN REGISTRADA - ID: {self.inscripcion_id}"
                    )
                    
                    # Emitir señal
                    self.inscripcion_creada.emit(datos)
                    
                    self.mostrar_mensaje("✅ Éxito", 
                        f"Inscripción registrada exitosamente\nID: {self.inscripcion_id}", 
                        "success")
                else:
                    self.mostrar_mensaje("Advertencia", 
                        "Inscripción registrada pero no se pudo obtener el ID", 
                        "warning")
            else:
                mensaje_error = resultado.get('mensaje', resultado.get('message', 'Error desconocido'))
                self.mostrar_mensaje("Error", f"No se pudo registrar la inscripción: {mensaje_error}", "error")
                
        except Exception as e:
            logger.error(f"Error registrando inscripción: {e}", exc_info=True)
            self.mostrar_mensaje("Error", f"Error al registrar inscripción: {str(e)}", "error")
    
    def configurar_formulario_inscripcion(self):
        """Configurar el formulario de inscripción con los datos actuales - VERSIÓN CORREGIDA"""
        if not self.estudiante_data or not self.programa_data:
            logger.warning("Faltan datos para configurar formulario")
            return
        
        # Asegurar que los widgets existan
        if not hasattr(self, 'estudiante_nombre_form_label') or not hasattr(self, 'programa_nombre_form_label'):
            logger.error("Widgets del formulario no inicializados")
            return
        
        # Configurar información básica
        estudiante_nombre = f"{self.estudiante_data.get('nombres', '')} {self.estudiante_data.get('apellido_paterno', '')}"
        self.estudiante_nombre_form_label.setText(estudiante_nombre.strip() or "No disponible")
        
        programa_nombre = self.programa_data.get('nombre', 'No disponible')
        self.programa_nombre_form_label.setText(programa_nombre)
        
        # Calcular costo inicial
        self.calcular_costo_total()
        
        # Actualizar visibilidad según si ya hay inscripción
        self.actualizar_estado_formulario()
        
        # Si ya tenemos inscripción_id (modo edición/lectura), cargar datos adicionales
        if self.inscripcion_id:
            self.cargar_datos_inscripcion_existente()
        
        # Asegurar que el formulario sea visible
        self.seccion_formulario_frame.setVisible(True)

    def cancelar_formulario_inscripcion(self):
        """Cancelar el proceso de inscripción y volver al listado"""
        if self.estudiante_id and self.programa_id:
            # Si ya hay inscripción registrada, preguntar confirmación
            if self.inscripcion_id:
                respuesta = QMessageBox.question(
                    self,
                    "Cancelar Inscripción",
                    "¿Está seguro de cancelar esta inscripción?\n\nSe perderán los datos no guardados de la transacción.",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if respuesta != QMessageBox.StandardButton.Yes:
                    return

            # Regresar al modo de visualización del estudiante
            self.programa_id = None
            self.configurar_interfaz_segun_contexto()
    
    def obtener_ultimo_id_inscripcion(self):
        """Obtener el último ID de inscripción del estudiante/programa"""
        try:
            from config.database import Database
            connection = Database.get_connection()
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT id FROM inscripciones 
                WHERE estudiante_id = %s AND programa_id = %s 
                ORDER BY fecha_inscripcion DESC LIMIT 1
                """
                cursor.execute(query, (self.estudiante_id, self.programa_id))
                result = cursor.fetchone()
                cursor.close()
                Database.return_connection(connection)
                
                return result[0] if result else None
        except Exception as e:
            logger.error(f"Error obteniendo último ID: {e}")
            return None
    
    # ===== MÉTODOS DE TRANSACCIÓN (FLUJO SECUNDARIO) =====
    
    def registrar_transaccion(self):
        """Registrar la transacción en la base de datos"""
        try:
            # Validar datos básicos
            if not self.inscripcion_id:
                self.mostrar_mensaje("Error", "Primero debe registrar la inscripción", "error")
                return

            # Asegurar que tenemos estudiante_id y programa_id
            if not self.estudiante_id or not self.programa_id:
                self.mostrar_mensaje("Error", "Falta información del estudiante o programa", "error")
                return

            # Validar monto
            monto_text = self.monto_pago_input.text().strip()
            if not monto_text:
                self.mostrar_mensaje("Error", "Ingrese el monto de la transacción", "error")
                return

            try:
                monto = float(monto_text)
                if monto <= 0:
                    self.mostrar_mensaje("Error", "El monto debe ser mayor a 0", "error")
                    return
            except ValueError:
                self.mostrar_mensaje("Error", "Monto inválido. Use formato: 1000.00", "error")
                return
            
            # Obtener datos de la transacción
            fecha_pago = self.fecha_pago_date.date().toString('yyyy-MM-dd')
            forma_pago = self.forma_pago_combo.currentText()
            origen = self.origen_transaccion_input.text().strip() or None
            estado = self.estado_transaccion_combo.currentText()
            
            # Preparar detalles de la transacción
            detalles_transaccion = []
            for row in range(self.detalles_table.rowCount()):
                try:
                    # Obtener concepto del combobox
                    concepto_widget = self.detalles_table.cellWidget(row, 0)
                    if concepto_widget and isinstance(concepto_widget, QComboBox):
                        concepto = concepto_widget.currentText()
                    else:
                        concepto = ""
                    
                    # Obtener descripción
                    desc_item = self.detalles_table.item(row, 1)
                    descripcion = desc_item.text() if desc_item else ""
                    
                    # Obtener cantidad
                    cantidad_item = self.detalles_table.item(row, 2)
                    cantidad = float(cantidad_item.text() or 1) if cantidad_item else 1
                    
                    # Obtener precio unitario
                    precio_item = self.detalles_table.item(row, 3)
                    precio_unitario = float(precio_item.text() or 0) if precio_item else 0
                    
                    # Obtener subtotal
                    subtotal_item = self.detalles_table.item(row, 4)
                    subtotal = float(subtotal_item.text() or 0) if subtotal_item else cantidad * precio_unitario
                    
                    # Validar que tenga datos mínimos
                    if concepto and precio_unitario > 0:
                        detalle = {
                            'concepto': concepto,
                            'descripcion': descripcion,
                            'cantidad': cantidad,
                            'precio_unitario': precio_unitario,
                            'subtotal': subtotal
                        }
                        detalles_transaccion.append(detalle)
                        
                except Exception as e:
                    logger.error(f"Error procesando detalle fila {row}: {e}")
                    
            # Si no hay detalles, crear uno automático
            if not detalles_transaccion:
                detalle_auto = {
                    'concepto': 'PAGO GENERAL',
                    'descripcion': f'Pago {forma_pago.lower()} - {origen or "Sin referencia"}',
                    'cantidad': 1,
                    'precio_unitario': monto,
                    'subtotal': monto
                }
                detalles_transaccion.append(detalle_auto)
                
            # Obtener documentos adjuntos
            documentos = []
            for i in range(self.documentos_list_widget.count()):
                item = self.documentos_list_widget.item(i)
                file_path = item.data(Qt.ItemDataRole.UserRole)
                file_name = item.text().replace("📄 ", "")
                
                if file_path and Path(file_path).exists():
                    documentos.append({
                        'nombre': file_name,
                        'ruta': file_path,
                        'tipo': Path(file_path).suffix.lower()
                    })
                    
            # Mostrar resumen antes de registrar
            resumen = self.mostrar_resumen_transaccion(
                monto, fecha_pago, forma_pago, estado, 
                len(detalles_transaccion), len(documentos)
            )
            
            if not resumen:
                return  # Usuario canceló
            
            # Registrar transacción usando el modelo
            resultado = TransaccionModel.crear_transaccion_completa(
                inscripcion_id=self.inscripcion_id,
                estudiante_id=self.estudiante_id,  # Ya aseguramos que no es None
                programa_id=self.programa_id,      # Ya aseguramos que no es None
                monto_final=monto,
                forma_pago=forma_pago,
                origen=origen,
                estado=estado,
                fecha_pago=fecha_pago,
                detalles=detalles_transaccion,
                documentos=documentos
            )
            
            if resultado.get('exito', False) or resultado.get('success', False):
                transaccion_id = resultado.get('transaccion_id') or resultado.get('id')
                
                mensaje = f"""
                ✅ Transacción registrada exitosamente
                
                ID Transacción: {transaccion_id}
                Monto: {monto:.2f} Bs
                Fecha: {fecha_pago}
                Estado: {estado}
                """
                
                self.mostrar_mensaje("Éxito", mensaje, "success")
                
                # Actualizar interfaz
                self.limpiar_formulario_transaccion()
                self.cargar_historial_transacciones()
                
                # Emitir señal si existe
                if hasattr(self, 'transaccion_registrada'):
                    self.transaccion_registrada.emit({
                        'transaccion_id': transaccion_id,
                        'inscripcion_id': self.inscripcion_id,
                        'monto': monto,
                        'estado': estado
                    })
                    
                # O usar la señal existente inscripcion_actualizada
                self.inscripcion_actualizada.emit({
                    'inscripcion_id': self.inscripcion_id,
                    'transaccion_registrada': True
                })
                    
            else:
                mensaje_error = resultado.get('mensaje', resultado.get('message', 'Error desconocido'))
                self.mostrar_mensaje("Error", f"No se pudo registrar la transacción: {mensaje_error}", "error")
                
        except Exception as e:
            logger.error(f"Error registrando transacción: {e}", exc_info=True)
            self.mostrar_mensaje("Error", f"Error al registrar transacción: {str(e)}", "error")
    
    def realizar_pago_inscripcion(self, inscripcion_id: int):
        """Abrir diálogo para realizar pago de una inscripción"""
        try:
            # Obtener datos de la inscripción
            from config.database import Database
            connection = Database.get_connection()
            if connection:
                cursor = connection.cursor()
                query = """
                SELECT 
                    i.id as inscripcion_id,
                    i.estudiante_id, 
                    i.programa_id,
                    i.descuento_aplicado,
                    CONCAT(e.nombres, ' ', e.apellido_paterno) as estudiante_nombre,
                    p.codigo, 
                    p.nombre as programa_nombre,
                    p.costo_total,
                    p.costo_matricula,
                    p.costo_inscripcion,
                    p.costo_mensualidad,
                    p.numero_cuotas
                FROM inscripciones i
                JOIN estudiantes e ON i.estudiante_id = e.id
                JOIN programas p ON i.programa_id = p.id
                WHERE i.id = %s
                """
                cursor.execute(query, (inscripcion_id,))
                result = cursor.fetchone()
                cursor.close()
                Database.return_connection(connection)
                
                if result:
                    column_names = [desc[0] for desc in cursor.description]
                    datos = dict(zip(column_names, result))
                    
                    # Calcular saldo pendiente
                    costo_matricula = datos.get('costo_matricula', 0) or 0
                    costo_inscripcion = datos.get('costo_inscripcion', 0) or 0
                    costo_mensualidad = datos.get('costo_mensualidad', 0) or 0
                    numero_cuotas = datos.get('numero_cuotas', 1) or 1
                    
                    costo_total = costo_matricula + costo_inscripcion + (costo_mensualidad * numero_cuotas)
                    descuento = datos.get('descuento_aplicado', 0) or 0
                    costo_con_descuento = costo_total * (1 - descuento / 100)
                    
                    # Obtener total pagado
                    transacciones = TransaccionModel.obtener_transacciones_inscripcion(inscripcion_id)
                    total_pagado = 0
                    for transaccion in transacciones:
                        if transaccion.get('estado') == 'CONFIRMADO':
                            total_pagado += transaccion.get('monto_final', 0)
                    
                    saldo_pendiente = max(0, costo_con_descuento - total_pagado)
                    
                    if saldo_pendiente <= 0:
                        self.mostrar_mensaje("Información", "Esta inscripción no tiene saldo pendiente", "info")
                        return
                    
                    # Mostrar diálogo simple de pago
                    self.mostrar_dialogo_pago(inscripcion_id, datos, saldo_pendiente)
                    
                else:
                    self.mostrar_mensaje("Error", "No se encontró la inscripción", "error")
                    
        except Exception as e:
            logger.error(f"Error preparando pago: {e}")
            self.mostrar_mensaje("Error", f"Error al preparar pago: {str(e)}", "error")
    
    def mostrar_dialogo_pago(self, inscripcion_id: int, datos: Dict, saldo_pendiente: float):
        """Mostrar diálogo simple para registrar pago"""
        dialog = QDialog(self)
        dialog.setWindowTitle("💰 Registrar Pago")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Información
        estudiante_nombre = datos.get('estudiante_nombre', '')
        programa_nombre = datos.get('programa_nombre', '')
        
        info_label = QLabel(f"""
        <b>Estudiante:</b> {estudiante_nombre}<br>
        <b>Programa:</b> {programa_nombre}<br>
        <b>Saldo pendiente:</b> {saldo_pendiente:.2f} Bs
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Forma de pago
        layout.addWidget(QLabel("Forma de pago:"))
        forma_pago_combo = QComboBox()
        forma_pago_combo.addItems(["EFECTIVO", "TRANSFERENCIA", "TARJETA", "DEPOSITO", "QR"])
        layout.addWidget(forma_pago_combo)
        
        # Monto
        layout.addWidget(QLabel(f"Monto (máximo: {saldo_pendiente:.2f} Bs):"))
        monto_input = QLineEdit()
        monto_input.setPlaceholderText(f"Ej: {saldo_pendiente:.2f}")
        monto_input.setText(f"{saldo_pendiente:.2f}")
        layout.addWidget(monto_input)
        
        # Comprobante
        layout.addWidget(QLabel("Número de comprobante:"))
        comprobante_input = QLineEdit()
        comprobante_input.setPlaceholderText("Opcional")
        layout.addWidget(comprobante_input)
        
        # Botones
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Procesar pago
            self.procesar_pago(
                inscripcion_id=inscripcion_id,
                forma_pago=forma_pago_combo.currentText(),
                monto=float(monto_input.text()),
                comprobante=comprobante_input.text() or None,
                datos=datos
            )
    
    def procesar_pago(self, inscripcion_id: int, forma_pago: str, monto: float, 
                        comprobante: Optional[str], datos: Dict):
        """Procesar el pago registrado"""
        try:
            # Convertir None a string vacío si es necesario
            comprobante_str = comprobante or ""
            
            # Aquí iría la lógica para guardar en la base de datos
            # Por ahora solo mostramos un mensaje
            self.mostrar_mensaje(
                "Pago registrado", 
                f"Se registró pago de {monto:.2f} Bs por {forma_pago}\n"
                f"Comprobante: {comprobante_str or 'No especificado'}", 
                "success"
            )
            
            # Recargar datos para actualizar la interfaz
            if self.estudiante_id:
                self.cargar_programas_inscritos_estudiante()
            
        except Exception as e:
            logger.error(f"Error procesando pago: {e}")
            self.mostrar_mensaje("Error", f"Error al procesar pago: {str(e)}", "error")
    
    # ===== MÉTODOS DE GESTIÓN DE DETALLES =====
    
    def agregar_detalle_transaccion(self):
        """Agregar un detalle a la tabla de detalles de transacción"""
        try:
            row_count = self.detalles_table.rowCount()
            self.detalles_table.insertRow(row_count)
            
            # Crear combobox para concepto
            concepto_combo = QComboBox()
            concepto_combo.addItems(["MATRÍCULA", "INSCRIPCIÓN", "MENSUALIDAD", "MATERIAL", "OTROS"])
            self.detalles_table.setCellWidget(row_count, 0, concepto_combo)
            
            # Descripción
            desc_item = QTableWidgetItem("")
            self.detalles_table.setItem(row_count, 1, desc_item)
            
            # Cantidad (por defecto 1)
            cantidad_item = QTableWidgetItem("1")
            self.detalles_table.setItem(row_count, 2, cantidad_item)
            
            # Precio unitario
            precio_item = QTableWidgetItem("0.00")
            self.detalles_table.setItem(row_count, 3, precio_item)
            
            # Subtotal (se calculará automáticamente)
            subtotal_item = QTableWidgetItem("0.00")
            subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.detalles_table.setItem(row_count, 4, subtotal_item)
            
            # Conectar señal para calcular subtotal automáticamente
            self.detalles_table.itemChanged.connect(self.calcular_subtotal_fila)
            
        except Exception as e:
            logger.error(f"Error agregando detalle: {e}")
    
    def calcular_subtotal_fila(self, item):
        """Calcular subtotal cuando cambian cantidad o precio"""
        try:
            row = item.row()
            col = item.column()
            
            # Solo recalcular si es cantidad (2) o precio (3)
            if col in [2, 3]:
                cantidad_item = self.detalles_table.item(row, 2)
                precio_item = self.detalles_table.item(row, 3)
                
                if cantidad_item and precio_item:
                    try:
                        cantidad = float(cantidad_item.text() or 0)
                        precio = float(precio_item.text() or 0)
                        subtotal = cantidad * precio
                        
                        # Actualizar subtotal
                        subtotal_item = self.detalles_table.item(row, 4)
                        if not subtotal_item:
                            subtotal_item = QTableWidgetItem()
                            subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                            self.detalles_table.setItem(row, 4, subtotal_item)
                            
                        subtotal_item.setText(f"{subtotal:.2f}")
                        
                    except ValueError:
                        pass
                    
        except Exception as e:
            logger.error(f"Error calculando subtotal: {e}")
    
    def eliminar_detalle_seleccionado(self):
        """Eliminar el detalle seleccionado de la tabla"""
        try:
            selected_rows = self.detalles_table.selectionModel().selectedRows()
            
            if not selected_rows:
                self.mostrar_mensaje("Información", "Seleccione una fila para eliminar", "info")
                return
            
            # Ordenar filas en orden descendente para eliminar correctamente
            rows_to_delete = sorted([row.row() for row in selected_rows], reverse=True)
            
            for row in rows_to_delete:
                self.detalles_table.removeRow(row)
                
            self.mostrar_mensaje("Éxito", f"Se eliminaron {len(rows_to_delete)} detalle(s)", "success")
            
        except Exception as e:
            logger.error(f"Error eliminando detalle: {e}")
            self.mostrar_mensaje("Error", f"No se pudo eliminar: {str(e)}", "error")
    
    def actualizar_botones_detalles(self):
        """Actualizar estado de los botones de detalles según selección"""
        try:
            selected_rows = self.detalles_table.selectionModel().selectedRows()
            has_selection = len(selected_rows) > 0
            self.btn_eliminar_detalle.setEnabled(has_selection)
        except Exception as e:
            logger.error(f"Error actualizando botones detalles: {e}")
    
    def crear_seccion_detalles_documentos(self):
        """Crear sección combinada de detalles y documentos"""
        frame = QFrame()
        frame.setObjectName("seccionDetallesDocumentos")
        frame.setStyleSheet("""
            #seccionDetallesDocumentos {
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter horizontal para dividir detalles y documentos
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #bdc3c7;
                width: 3px;
            }
        """)
        
        # Panel izquierdo: Detalles
        detalles_panel = self.crear_panel_detalles()
        splitter.addWidget(detalles_panel)
        
        # Panel derecho: Documentos
        documentos_panel = self.crear_panel_documentos()
        splitter.addWidget(documentos_panel)
        
        # Configurar proporciones del splitter
        splitter.setStretchFactor(0, 2)  # Detalles ocupa más espacio
        splitter.setStretchFactor(1, 1)  # Documentos ocupa menos espacio
        
        layout.addWidget(splitter)
        
        # Establecer altura mínima para esta sección
        frame.setMinimumHeight(300)
        
        return frame

    def crear_panel_detalles(self):
        """Crear panel para detalles de transacción"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border-right: 1px solid #ddd;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        titulo = QLabel("📊 DETALLES DE LA TRANSACCIÓN")
        titulo.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #27ae60;
            padding-bottom: 10px;
            border-bottom: 1px solid #27ae60;
        """)
        layout.addWidget(titulo)
        
        # Tabla de detalles
        self.detalles_table = QTableWidget()
        self.detalles_table.setObjectName("detallesTable")
        self.detalles_table.setColumnCount(5)
        self.detalles_table.setHorizontalHeaderLabels(["Concepto", "Descripción", "Cantidad", "Precio Unit.", "Subtotal"])
        
        # Configurar header
        header = self.detalles_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.detalles_table.setStyleSheet("""
            #detallesTable {
                font-size: 12px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #ecf0f1;
            }
            #detallesTable::item {
                padding: 5px;
            }
            #detallesTable QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 8px;
                font-weight: bold;
                border: none;
            }
        """)
        
        self.detalles_table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed)
        self.detalles_table.setAlternatingRowColors(True)
        self.detalles_table.setMinimumHeight(200)
        layout.addWidget(self.detalles_table)
        
        # Botones para detalles
        btn_layout = QHBoxLayout()
        
        self.btn_agregar_detalle = QPushButton("➕ AGREGAR CONCEPTO")
        self.btn_agregar_detalle.setMinimumHeight(35)
        self.btn_agregar_detalle.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        btn_layout.addWidget(self.btn_agregar_detalle)
        
        self.btn_eliminar_detalle = QPushButton("🗑️ ELIMINAR")
        self.btn_eliminar_detalle.setMinimumHeight(35)
        self.btn_eliminar_detalle.setEnabled(False)
        self.btn_eliminar_detalle.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        btn_layout.addWidget(self.btn_eliminar_detalle)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        return panel

    def crear_panel_documentos(self):
        """Crear panel para documentos de respaldo"""
        panel = QFrame()
        panel.setStyleSheet("""
            QFrame {
                background-color: #fff;
                border-left: 1px solid #ddd;
                border-radius: 0px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Título
        titulo = QLabel("📎 DOCUMENTOS DE RESPALDO")
        titulo.setStyleSheet("""
            font-weight: bold;
            font-size: 14px;
            color: #f39c12;
            padding-bottom: 10px;
            border-bottom: 1px solid #f39c12;
        """)
        layout.addWidget(titulo)
        
        # Lista de documentos
        self.documentos_list_widget = QListWidget()
        self.documentos_list_widget.setStyleSheet("""
            QListWidget {
                font-size: 12px;
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 5px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #ecf0f1;
            }
            QListWidget::item:selected {
                background-color: #3498db;
                color: white;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        self.documentos_list_widget.setMinimumHeight(150)
        layout.addWidget(self.documentos_list_widget)
        
        # Botones para documentos
        btn_layout = QHBoxLayout()
        
        self.btn_agregar_documento = QPushButton("➕ AGREGAR")
        self.btn_agregar_documento.setMinimumHeight(35)
        self.btn_agregar_documento.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        btn_layout.addWidget(self.btn_agregar_documento)
        
        self.btn_ver_documento = QPushButton("👁️ VER")
        self.btn_ver_documento.setMinimumHeight(35)
        self.btn_ver_documento.setEnabled(False)
        self.btn_ver_documento.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        btn_layout.addWidget(self.btn_ver_documento)
        
        self.btn_eliminar_documento = QPushButton("🗑️ ELIMINAR")
        self.btn_eliminar_documento.setMinimumHeight(35)
        self.btn_eliminar_documento.setEnabled(False)
        self.btn_eliminar_documento.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 15px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        btn_layout.addWidget(self.btn_eliminar_documento)
        
        layout.addLayout(btn_layout)
        
        # Info sobre documentos
        info_label = QLabel("Formatos aceptados: PDF, JPG, PNG, DOC, XLS\nTamaño máximo: 10MB por archivo")
        info_label.setStyleSheet("""
            font-size: 10px;
            color: #7f8c8d;
            font-style: italic;
            padding-top: 10px;
            border-top: 1px dashed #ddd;
        """)
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        return panel

    def crear_seccion_resumen_acciones(self):
        """Crear sección de resumen y botones de acción"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 15, 20, 15)
        
        # Resumen financiero
        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 2px solid #2c3e50;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        resumen_layout = QHBoxLayout(resumen_frame)
        resumen_layout.setContentsMargins(20, 15, 20, 15)
        
        # Labels de resumen
        self.resumen_total_label = QLabel("TOTAL A PAGAR:")
        self.resumen_total_label.setStyleSheet("""
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
        """)
        resumen_layout.addWidget(self.resumen_total_label)
        
        self.resumen_monto_label = QLabel("0.00 Bs")
        self.resumen_monto_label.setStyleSheet("""
            font-weight: bold;
            font-size: 22px;
            color: #e74c3c;
            padding: 10px 20px;
            background-color: #f9ebea;
            border-radius: 6px;
            min-width: 200px;
            text-align: center;
        """)
        resumen_layout.addWidget(self.resumen_monto_label)
        
        resumen_layout.addStretch()
        
        layout.addWidget(resumen_frame)
        
        # Botones de acción
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # Botón Cancelar
        self.btn_cancelar_formulario = QPushButton("❌ CANCELAR")
        self.btn_cancelar_formulario.setMinimumHeight(45)
        self.btn_cancelar_formulario.setMinimumWidth(150)
        self.btn_cancelar_formulario.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        btn_layout.addWidget(self.btn_cancelar_formulario)
        
        # Botón Registrar Transacción
        self.btn_registrar_transaccion = QPushButton("💰 REGISTRAR TRANSACCIÓN")
        self.btn_registrar_transaccion.setObjectName("btnRegistrarTransaccion")
        self.btn_registrar_transaccion.setMinimumHeight(45)
        self.btn_registrar_transaccion.setMinimumWidth(200)
        self.btn_registrar_transaccion.setStyleSheet("""
            #btnRegistrarTransaccion {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 30px;
            }
            #btnRegistrarTransaccion:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
            }
            #btnRegistrarTransaccion:disabled {
                background: #95a5a6;
                color: #ecf0f1;
            }
        """)
        btn_layout.addWidget(self.btn_registrar_transaccion)
        
        layout.addLayout(btn_layout)
        
        # Establecer altura mínima para esta sección
        frame.setMinimumHeight(150)
        
        return frame
    
    # ===== MÉTODOS DE GESTIÓN DE DOCUMENTOS =====
    
    def agregar_documento_transaccion(self):
        """Agregar un documento a la transacción"""
        try:
            # Abrir selector de archivos
            file_dialog = QFileDialog(self)
            file_dialog.setWindowTitle("Seleccionar Documento de Respaldo")
            file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
            file_dialog.setNameFilter("Documentos (*.pdf *.jpg *.jpeg *.png *.doc *.docx *.xls *.xlsx)")
            
            if file_dialog.exec():
                files = file_dialog.selectedFiles()
                for file_path in files:
                    file_name = Path(file_path).name
                    item = QListWidgetItem(f"📄 {file_name}")
                    item.setData(Qt.ItemDataRole.UserRole, file_path)  # Guardar ruta completa
                    self.documentos_list_widget.addItem(item)
                    
        except Exception as e:
            logger.error(f"Error agregando documento: {e}")
            self.mostrar_mensaje("Error", f"No se pudo agregar el documento: {str(e)}", "error")
    
    def ver_documento_seleccionado(self):
        """Ver el documento seleccionado"""
        try:
            selected_items = self.documentos_list_widget.selectedItems()
            
            if not selected_items:
                self.mostrar_mensaje("Información", "Seleccione un documento para ver", "info")
                return
            
            item = selected_items[0]
            file_path = item.data(Qt.ItemDataRole.UserRole)
            
            if not file_path or not Path(file_path).exists():
                self.mostrar_mensaje("Error", "El archivo no existe o no está disponible", "error")
                return
            
            # Intentar abrir el documento con el visor predeterminado del sistema
            import os
            import platform
            import subprocess
            
            system = platform.system()
            
            try:
                if system == "Windows":
                    os.startfile(file_path)
                elif system == "Darwin":  # macOS
                    subprocess.call(("open", file_path))
                else:  # Linux y otros
                    subprocess.call(("xdg-open", file_path))
                    
                self.mostrar_mensaje("Información", f"Abriendo documento: {Path(file_path).name}", "info")
                
            except Exception as e:
                logger.error(f"Error abriendo documento: {e}")
                
                # Mostrar información del archivo en un diálogo
                from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
                
                dialog = QDialog(self)
                dialog.setWindowTitle("📄 Información del Documento")
                dialog.setMinimumWidth(400)
                
                layout = QVBoxLayout(dialog)
                
                info_text = f"""
                <h3>Documento Seleccionado</h3>
                <p><b>Nombre:</b> {Path(file_path).name}</p>
                <p><b>Ruta:</b> {file_path}</p>
                <p><b>Tamaño:</b> {Path(file_path).stat().st_size / 1024:.1f} KB</p>
                <p><b>Última modificación:</b> {datetime.fromtimestamp(Path(file_path).stat().st_mtime).strftime('%d/%m/%Y %H:%M')}</p>
                <hr>
                <p><i>No se pudo abrir automáticamente. Puede abrirlo manualmente desde la ubicación mostrada.</i></p>
                """
                
                label = QLabel(info_text)
                label.setWordWrap(True)
                layout.addWidget(label)
                
                buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                dialog.exec()
                
        except Exception as e:
            logger.error(f"Error mostrando documento: {e}")
            self.mostrar_mensaje("Error", f"No se pudo abrir el documento: {str(e)}", "error")
    
    def eliminar_documento_seleccionado(self):
        """Eliminar el documento seleccionado de la lista"""
        try:
            selected_items = self.documentos_list_widget.selectedItems()
            
            if not selected_items:
                self.mostrar_mensaje("Información", "Seleccione un documento para eliminar", "info")
                return
            
            item = selected_items[0]
            file_path = item.data(Qt.ItemDataRole.UserRole)
            file_name = item.text()
            
            # Preguntar confirmación
            from PySide6.QtWidgets import QMessageBox
            respuesta = QMessageBox.question(
                self,
                "Confirmar eliminación",
                f"¿Está seguro de eliminar el documento:\n{file_name}?\n\nNota: Esto solo lo elimina de la lista, no del sistema de archivos.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if respuesta == QMessageBox.StandardButton.Yes:
                row = self.documentos_list_widget.row(item)
                self.documentos_list_widget.takeItem(row)
                self.mostrar_mensaje("Éxito", f"Documento eliminado de la lista", "success")
                
        except Exception as e:
            logger.error(f"Error eliminando documento: {e}")
            self.mostrar_mensaje("Error", f"No se pudo eliminar el documento: {str(e)}", "error")
    
    def actualizar_botones_documentos(self):
        """Actualizar estado de los botones de documentos según selección"""
        try:
            selected_items = self.documentos_list_widget.selectedItems()
            has_selection = len(selected_items) > 0
            self.btn_ver_documento.setEnabled(has_selection)
            self.btn_eliminar_documento.setEnabled(has_selection)
        except Exception as e:
            logger.error(f"Error actualizando botones documentos: {e}")
    
    # ===== MÉTODOS DE CÁLCULO =====
    
    def calcular_costo_total(self):
        """Calcular el costo total considerando descuento - VERSIÓN CORREGIDA"""
        try:
            if not self.programa_data:
                self.costo_total_label.setText("0.00 Bs")
                self.resumen_monto_label.setText("0.00 Bs")
                return

            # Obtener costos del programa
            costo_matricula = float(self.programa_data.get('costo_matricula', 0) or 0)
            costo_inscripcion = float(self.programa_data.get('costo_inscripcion', 0) or 0)
            costo_mensualidad = float(self.programa_data.get('costo_mensualidad', 0) or 0)
            numero_cuotas = int(self.programa_data.get('numero_cuotas', 1) or 1)

            # Calcular costo base
            costo_base = costo_matricula + costo_inscripcion + (costo_mensualidad * numero_cuotas)

            # Aplicar descuento
            descuento = self.descuento_spin.value() if hasattr(self, 'descuento_spin') else 0

            if descuento > 0:
                total = costo_base * (1 - descuento / 100)
            else:
                total = costo_base

            # Formatear y mostrar
            total_text = f"{total:.2f} Bs"
            self.costo_total_label.setText(total_text)
            self.resumen_monto_label.setText(total_text)

            # Actualizar también el monto sugerido en la transacción
            if hasattr(self, 'monto_pago_input') and self.monto_pago_input:
                self.monto_pago_input.setText(f"{total:.2f}")

        except Exception as e:
            logger.error(f"Error calculando costo total: {e}")
            self.costo_total_label.setText("0.00 Bs")
            self.resumen_monto_label.setText("0.00 Bs")
    
    def calcular_resumen_programa(self, programa_id: int):
        """Calcular resumen de inscritos y recaudado del programa"""
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                self.programa_inscritos_label.setText("Error conexión")
                self.programa_recaudado_label.setText("Error conexión")
                return

            cursor = connection.cursor()

            # 1. Obtener cupos máximos del programa
            query_cupos = """
            SELECT cupos_maximos FROM programas WHERE id = %s
            """
            cursor.execute(query_cupos, (programa_id,))
            result_cupos = cursor.fetchone()
            cupos_maximos = result_cupos[0] if result_cupos else None

            # 2. Contar estudiantes inscritos (excluyendo RETIRADOS)
            query_inscritos = """
            SELECT COUNT(*) as total_inscritos
            FROM inscripciones 
            WHERE programa_id = %s 
            AND estado NOT IN ('RETIRADO')
            """
            cursor.execute(query_inscritos, (programa_id,))
            result_inscritos = cursor.fetchone()
            total_inscritos = result_inscritos[0] if result_inscritos else 0

            # 3. Calcular total recaudado de transacciones CONFIRMADAS
            query_recaudado = """
            SELECT COALESCE(SUM(t.monto_final), 0) as total_recaudado
            FROM transacciones t
            WHERE t.programa_id = %s 
            AND t.estado = 'CONFIRMADO'
            """
            cursor.execute(query_recaudado, (programa_id,))
            result_recaudado = cursor.fetchone()
            total_recaudado = float(result_recaudado[0]) if result_recaudado else 0.0

            # ... resto del código ...

            # Actualizar interfaz con los datos calculados
            self.programa_inscritos_label.setText(f"{total_inscritos} estudiantes")

            # Calcular porcentaje de ocupación si hay cupos definidos
            if cupos_maximos and cupos_maximos > 0:
                porcentaje_ocupacion = (total_inscritos / cupos_maximos) * 100
                ocupacion_text = f"{total_inscritos}/{cupos_maximos} ({porcentaje_ocupacion:.1f}%)"
                self.programa_inscritos_label.setText(ocupacion_text)

                # Agregar tooltip con información detallada
                inscritos_tooltip = (
                    f"👥 <b>Resumen de Inscritos</b><br><br>"
                    f"<b>Total Inscritos:</b> {total_inscritos}<br>"
                    f"<b>Cupos Disponibles:</b> {cupos_maximos - total_inscritos}<br>"
                    f"<b>Porcentaje Ocupación:</b> {porcentaje_ocupacion:.1f}%<br>"
                    f"<b>Estudiantes con Saldo Pendiente:</b> {estudiantes_con_saldo}"
                )
                self.programa_inscritos_label.setToolTip(inscritos_tooltip)
            else:
                self.programa_inscritos_label.setText(f"{total_inscritos} estudiantes")
                self.programa_recaudado_label.setText("0.00 Bs")
                self.programa_recaudado_label.setStyleSheet("color: #95a5a6; font-weight: bold;")
                self.programa_recaudado_label.setToolTip("No hay transacciones registradas para este programa")
            
        except Exception as e:
            logger.error(f"Error calculando resumen del programa: {e}")
            self.programa_inscritos_label.setText("Error cálculo")
            self.programa_recaudado_label.setText("Error cálculo")
            self.programa_inscritos_label.setToolTip(f"Error al calcular: {str(e)}")
            self.programa_recaudado_label.setToolTip(f"Error al calcular: {str(e)}")
    
    def calcular_recaudado_programa(self, programa_id: int):
        """Calcular el total recaudado por un programa"""
        try:
            from config.database import Database
            connection = Database.get_connection()
            if connection:
                cursor = connection.cursor()
                
                # Contar estudiantes inscritos (no retirados)
                query_inscritos = """
                SELECT COUNT(*) as total_inscritos
                FROM inscripciones 
                WHERE programa_id = %s AND estado NOT IN ('RETIRADO')
                """
                cursor.execute(query_inscritos, (programa_id,))
                result_inscritos = cursor.fetchone()
                total_inscritos = result_inscritos[0] if result_inscritos else 0
                
                # Calcular total recaudado (suma de transacciones confirmadas)
                query_recaudado = """
                SELECT COALESCE(SUM(t.monto_final), 0) as total_recaudado
                FROM transacciones t
                JOIN inscripciones i ON t.estudiante_id = i.estudiante_id AND t.programa_id = i.programa_id
                WHERE i.programa_id = %s AND t.estado = 'CONFIRMADO'
                """
                cursor.execute(query_recaudado, (programa_id,))
                result_recaudado = cursor.fetchone()
                total_recaudado = result_recaudado[0] if result_recaudado else 0
                
                cursor.close()
                Database.return_connection(connection)
                
                # Actualizar interfaz
                self.programa_inscritos_label.setText(f"{total_inscritos} estudiantes")
                self.programa_recaudado_label.setText(f"{total_recaudado:.2f} Bs")
                
        except Exception as e:
            logger.error(f"Error calculando recaudado: {e}")
            self.programa_inscritos_label.setText("Error")
            self.programa_recaudado_label.setText("Error")
    
    def calcular_fecha_vencimiento_cuota(self, programa_data: Dict, numero_cuota: int) -> Optional[str]:
        """Calcular fecha de vencimiento de una cuota"""
        try:
            fecha_inicio = programa_data.get('fecha_inscripcion')
            if not fecha_inicio:
                return None
            
            from datetime import datetime, timedelta
            # Convertir a datetime si es string
            if isinstance(fecha_inicio, str):
                fecha_inicio = datetime.strptime(fecha_inicio[:10], '%Y-%m-%d')
            
            # Calcular fecha de vencimiento (1 mes por cuota después de la inscripción)
            fecha_vencimiento = fecha_inicio + timedelta(days=30 * numero_cuota)
            return fecha_vencimiento.strftime('%d/%m/%Y')
            
        except Exception:
            return None
    
    # ===== MÉTODOS DE ENRIQUECIMIENTO DE DATOS =====
    
    def enriquecer_datos_programa_inscrito(self, programa_data: Dict) -> Dict:
        """Enriquecer datos del programa inscrito con información financiera"""
        try:
            inscripcion_id = programa_data.get('inscripcion_id')
            estudiante_id = self.estudiante_id
            programa_id = programa_data.get('programa_id')
            
            if not all([inscripcion_id, estudiante_id, programa_id]):
                return programa_data
            
            # 1. Obtener transacciones relacionadas a esta inscripción
            if not inscripcion_id:
                return programa_data
            transacciones = TransaccionModel.obtener_transacciones_inscripcion(inscripcion_id)
            
            # 2. Obtener detalles de las transacciones para mostrar conceptos
            transacciones_con_detalles = []
            for transaccion in transacciones:
                transaccion_id = transaccion.get('id')
                if transaccion_id:
                    detalles = TransaccionModel.obtener_detalles_transaccion(transaccion_id)
                    transaccion['detalles'] = detalles
                transacciones_con_detalles.append(transaccion)
            
            # 3. Calcular total pagado (solo transacciones confirmadas)
            total_pagado = 0
            for transaccion in transacciones:
                if transaccion.get('estado') == 'CONFIRMADO':
                    total_pagado += transaccion.get('monto_final', 0)
            
            # 4. Calcular costo total del programa según estructura
            costo_matricula = programa_data.get('costo_matricula', 0) or 0
            costo_inscripcion = programa_data.get('costo_inscripcion', 0) or 0
            costo_mensualidad = programa_data.get('costo_mensualidad', 0) or 0
            numero_cuotas = programa_data.get('numero_cuotas', 1) or 1
            
            # Costo total del programa (matrícula + inscripción + (mensualidad * cuotas))
            costo_total_calculado = costo_matricula + costo_inscripcion + (costo_mensualidad * numero_cuotas)
            
            # 5. Aplicar descuento si existe
            descuento = programa_data.get('descuento_aplicado', 0) or 0
            costo_con_descuento = costo_total_calculado * (1 - descuento / 100)
            
            # 6. Calcular saldo pendiente
            saldo_pendiente = max(0, costo_con_descuento - total_pagado)
            
            # 7. Calcular porcentaje pagado
            porcentaje_pagado = (total_pagado / costo_con_descuento * 100) if costo_con_descuento > 0 else 0
            
            # 8. Determinar estado financiero
            estado_financiero = "PAGADO" if saldo_pendiente == 0 else "PENDIENTE"
            
            # 9. Calcular fecha del último pago
            ultimo_pago = None
            if transacciones:
                # Ordenar por fecha descendente y tomar la más reciente confirmada
                transacciones_confirmadas = [t for t in transacciones if t.get('estado') == 'CONFIRMADO']
                if transacciones_confirmadas:
                    transacciones_confirmadas.sort(key=lambda x: x.get('fecha_pago', ''), reverse=True)
                    ultimo_pago = transacciones_confirmadas[0].get('fecha_pago')
            
            # 10. Calcular próxima cuota pendiente (si aplica)
            proxima_cuota = None
            if numero_cuotas > 1 and saldo_pendiente > 0:
                # Simplificación: asumir cuotas mensuales
                cuotas_pagadas = int(total_pagado / costo_mensualidad) if costo_mensualidad > 0 else 0
                cuota_actual = cuotas_pagadas + 1
                if cuota_actual <= numero_cuotas:
                    proxima_cuota = {
                        'numero': cuota_actual,
                        'monto': costo_mensualidad,
                        'vencimiento': self.calcular_fecha_vencimiento_cuota(programa_data, cuota_actual)
                    }
            
            # Agregar datos enriquecidos
            programa_data['transacciones'] = transacciones_con_detalles
            programa_data['total_pagado'] = total_pagado
            programa_data['saldo_pendiente'] = saldo_pendiente
            programa_data['costo_con_descuento'] = costo_con_descuento
            programa_data['costo_matricula'] = costo_matricula
            programa_data['costo_inscripcion'] = costo_inscripcion
            programa_data['costo_mensualidad'] = costo_mensualidad
            programa_data['numero_cuotas'] = numero_cuotas
            programa_data['porcentaje_pagado'] = porcentaje_pagado
            programa_data['estado_financiero'] = estado_financiero
            programa_data['ultimo_pago'] = ultimo_pago
            programa_data['proxima_cuota'] = proxima_cuota
            
            return programa_data
            
        except Exception as e:
            logger.error(f"Error enriqueciendo datos del programa inscrito: {e}")
            # Devolver datos básicos si hay error
            return programa_data
    
    def enriquecer_datos_programa(self, programa_data: Dict) -> Dict:
        """Enriquecer datos del programa con información de pagos"""
        try:
            inscripcion_id = programa_data.get('inscripcion_id')
            estudiante_id = self.estudiante_id
            programa_id = programa_data.get('programa_id')
            
            if not inscripcion_id or not estudiante_id or not programa_id:
                return programa_data
            
            # Obtener transacciones relacionadas a esta inscripción
            transacciones = TransaccionModel.obtener_transacciones_inscripcion(inscripcion_id)
            
            # Calcular total pagado (solo transacciones confirmadas)
            total_pagado = 0
            for transaccion in transacciones:
                if transaccion.get('estado') == 'CONFIRMADO':
                    total_pagado += transaccion.get('monto_final', 0)
            
            # Calcular costo total considerando estructura del programa
            costo_matricula = programa_data.get('costo_matricula', 0) or 0
            costo_inscripcion = programa_data.get('costo_inscripcion', 0) or 0
            costo_mensualidad = programa_data.get('costo_mensualidad', 0) or 0
            numero_cuotas = programa_data.get('numero_cuotas', 1) or 1
            
            # Costo total del programa (matrícula + inscripción + (mensualidad * cuotas))
            costo_total_calculado = costo_matricula + costo_inscripcion + (costo_mensualidad * numero_cuotas)
            
            # Aplicar descuento si existe
            descuento = programa_data.get('descuento_aplicado', 0) or 0
            costo_con_descuento = costo_total_calculado * (1 - descuento / 100)
            
            # Calcular saldo pendiente
            saldo_pendiente = max(0, costo_con_descuento - total_pagado)
            
            # Agregar datos enriquecidos
            programa_data['transacciones'] = transacciones
            programa_data['total_pagado'] = total_pagado
            programa_data['saldo_pendiente'] = saldo_pendiente
            programa_data['costo_con_descuento'] = costo_con_descuento
            programa_data['costo_matricula'] = costo_matricula
            programa_data['costo_inscripcion'] = costo_inscripcion
            programa_data['costo_mensualidad'] = costo_mensualidad
            programa_data['numero_cuotas'] = numero_cuotas
            
            return programa_data
            
        except Exception as e:
            logger.error(f"Error enriqueciendo datos del programa: {e}")
            return programa_data
    
    def enriquecer_datos_estudiante(self, estudiante_data: Dict) -> Dict:
        """Enriquecer datos del estudiante con información de pagos"""
        try:
            inscripcion_id = estudiante_data.get('inscripcion_id')
            programa_id = self.programa_id
            
            if not inscripcion_id or not programa_id:
                return estudiante_data
            
            # Obtener información del programa
            resultado = ProgramaModel.obtener_programa(programa_id)
            if resultado.get('success') and resultado.get('data'):
                programa = resultado['data']
                
                costo_matricula = programa.get('costo_matricula', 0) or 0
                costo_inscripcion = programa.get('costo_inscripcion', 0) or 0
                costo_mensualidad = programa.get('costo_mensualidad', 0) or 0
                numero_cuotas = programa.get('numero_cuotas', 1) or 1
                
                costo_total = costo_matricula + costo_inscripcion + (costo_mensualidad * numero_cuotas)
            else:
                costo_total = 0
            
            # Obtener descuento aplicado a esta inscripción
            from config.database import Database
            connection = Database.get_connection()
            if connection:
                cursor = connection.cursor()
                query = "SELECT descuento_aplicado FROM inscripciones WHERE id = %s"
                cursor.execute(query, (inscripcion_id,))
                descuento_result = cursor.fetchone()
                descuento = descuento_result[0] if descuento_result else 0
                cursor.close()
                Database.return_connection(connection)
            else:
                descuento = 0
            
            # Calcular costo con descuento
            costo_con_descuento = costo_total * (1 - descuento / 100)
            
            # Obtener transacciones de esta inscripción
            transacciones = TransaccionModel.obtener_transacciones_inscripcion(inscripcion_id)
            
            # Calcular total pagado (solo transacciones confirmadas)
            total_pagado = 0
            for transaccion in transacciones:
                if transaccion.get('estado') == 'CONFIRMADO':
                    total_pagado += transaccion.get('monto_final', 0)
            
            saldo_pendiente = max(0, costo_con_descuento - total_pagado)
            
            # Agregar datos enriquecidos
            estudiante_data['transacciones'] = transacciones
            estudiante_data['total_pagado'] = total_pagado
            estudiante_data['saldo_pendiente'] = saldo_pendiente
            estudiante_data['descuento_aplicado'] = descuento
            estudiante_data['costo_total_programa'] = costo_total
            estudiante_data['costo_con_descuento'] = costo_con_descuento
            
            return estudiante_data
            
        except Exception as e:
            logger.error(f"Error enriqueciendo datos del estudiante: {e}")
            return estudiante_data
    
    # ===== MÉTODOS DE RESPUESTA A EVENTOS =====
    
    def realizar_inscripcion(self):
        """Realizar la inscripción"""
        # TODO: Implementar lógica de inscripción
        self.mostrar_mensaje("Información", "Funcionalidad en desarrollo", "info")
    
    def cancelar_inscripcion(self):
        """Cancelar la inscripción"""
        self.close_overlay()
    
    def agregar_documento(self):
        """Agregar documento de respaldo"""
        # TODO: Implementar selector de archivos
        self.mostrar_mensaje("Información", "Funcionalidad en desarrollo", "info")
    
    # ===== MÉTODOS DE LIMPIEZA =====
    
    def limpiar_listados(self):
        """Limpiar todos los listados dinámicos"""
        while self.listado_layout_container.count():
            child = self.listado_layout_container.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
        
        self.programas_disponibles_table.setRowCount(0)
        self.estudiantes_disponibles_table.setRowCount(0)
        self.documentos_list_widget.clear()
        self.detalles_table.setRowCount(1)
    
    def limpiar_formulario_transaccion(self):
        """Limpiar el formulario de transacción después de registrar"""
        try:
            # Restaurar valores predeterminados
            self.fecha_pago_date.setDate(QDate.currentDate())
            self.monto_pago_input.clear()
            self.origen_transaccion_input.clear()
            self.estado_transaccion_combo.setCurrentText("CONFIRMADO")
            
            # Limpiar detalles
            self.detalles_table.setRowCount(0)
            
            # Limpiar documentos
            self.documentos_list_widget.clear()
            
            # Actualizar monto sugerido basado en el costo total
            self.monto_pago_input.setText(self.costo_total_label.text().replace(" Bs", ""))
            
        except Exception as e:
            logger.error(f"Error limpiando formulario transacción: {e}")
    
    # ===== MÉTODOS DE VALIDACIÓN Y RESPUESTA =====
    
    def mostrar_resumen_transaccion(self, monto: float, fecha: str, forma_pago: str, 
                                    estado: str, num_detalles: int, num_documentos: int):
        """Mostrar resumen de la transacción antes de registrar"""
        try:
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle("📋 Resumen de Transacción")
            dialog.setMinimumWidth(450)
            
            layout = QVBoxLayout(dialog)
            
            # Crear texto del resumen
            resumen_text = f"""
            <h3>Resumen de la Transacción</h3>
            <p><b>Estudiante:</b> {self.estudiante_data.get('nombres', '')} {self.estudiante_data.get('apellido_paterno', '')}</p>
            <p><b>Programa:</b> {self.programa_data.get('nombre', '')}</p>
            <hr>
            <p><b>📅 Fecha de Pago:</b> {fecha}</p>
            <p><b>💰 Monto:</b> {monto:.2f} Bs</p>
            <p><b>💳 Forma de Pago:</b> {forma_pago}</p>
            <p><b>📊 Estado:</b> {estado}</p>
            <hr>
            <p><b>📝 Detalles:</b> {num_detalles} concepto(s)</p>
            <p><b>📎 Documentos:</b> {num_documentos} archivo(s)</p>
            <hr>
            <p style='color: #e74c3c;'><b>⚠️ ¿Confirma que desea registrar esta transacción?</b></p>
            <p><i>Esta acción no se puede deshacer.</i></p>
            """
            
            label = QLabel(resumen_text)
            label.setWordWrap(True)
            layout.addWidget(label)
            
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                        QDialogButtonBox.StandardButton.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            return dialog.exec() == QDialog.DialogCode.Accepted
        
        except Exception as e:
            logger.error(f"Error mostrando resumen: {e}")
            return True  # Continuar sin resumen si hay error
    
    def ver_detalles_transaccion(self, transaccion_id: int):
        """Ver detalles de una transacción específica"""
        try:
            # Obtener detalles de la transacción
            detalles = TransaccionModel.obtener_detalles_transaccion(transaccion_id)
            
            # Mostrar en un diálogo o ventana
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"📊 Detalles de Transacción ID: {transaccion_id}")
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout(dialog)
            
            if detalles:
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                
                texto = "<h3>Detalles de la Transacción</h3><br>"
                for detalle in detalles:
                    texto += f"<b>Concepto:</b> {detalle.get('concepto', '')}<br>"
                    texto += f"<b>Descripción:</b> {detalle.get('descripcion', '')}<br>"
                    texto += f"<b>Cantidad:</b> {detalle.get('cantidad', 0)}<br>"
                    texto += f"<b>Precio:</b> {detalle.get('precio_unitario', 0):.2f} Bs<br>"
                    texto += f"<b>Subtotal:</b> {detalle.get('subtotal', 0):.2f} Bs<br>"
                    texto += "<hr>"
                    
                text_edit.setHtml(texto)
                layout.addWidget(text_edit)
            else:
                layout.addWidget(QLabel("No hay detalles registrados para esta transacción"))
                
            buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Error mostrando detalles de transacción: {e}")
            self.mostrar_mensaje("Error", f"No se pudieron cargar los detalles: {str(e)}", "error")
    
    # ===== MÉTODOS DE MANEJO DE ERRORES =====
    
    def crear_item_error_programa(self, programa_data: Dict, error_msg: str):
        """Crear un item de error para programas que no se pudieron cargar"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #fdedec;
                border: 1px solid #f5c6cb;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        
        # Encabezado con icono de error
        header_layout = QHBoxLayout()
        
        error_icon = QLabel("⚠️")
        error_icon.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(error_icon)
        
        codigo_label = QLabel(f"<b>{programa_data.get('codigo', 'Programa desconocido')}</b>")
        codigo_label.setStyleSheet("color: #721c24; font-size: 14px;")
        header_layout.addWidget(codigo_label)
        
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Mensaje de error
        error_label = QLabel(f"Error al cargar información: {error_msg[:100]}...")
        error_label.setStyleSheet("color: #856404; font-size: 12px;")
        error_label.setWordWrap(True)
        layout.addWidget(error_label)
        
        # Información básica disponible
        info_label = QLabel(f"Nombre: {programa_data.get('nombre', 'No disponible')}")
        info_label.setStyleSheet("color: #6c757d; font-size: 11px;")
        layout.addWidget(info_label)
        
        # Botón para reintentar
        btn_reintentar = QPushButton("🔄 Reintentar Carga")
        btn_reintentar.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        btn_reintentar.clicked.connect(lambda: self.recargar_programa_inscrito(programa_data.get('inscripcion_id')))
        layout.addWidget(btn_reintentar)
        
        return frame
    
    def recargar_programa_inscrito(self, inscripcion_id: Optional[int]):
        """Recargar un programa específico"""
        try:
            if not inscripcion_id:
                return

            # Buscar y actualizar el widget específico
            for i in range(self.listado_layout_container.count()):
                item = self.listado_layout_container.itemAt(i)
                if not item:
                    continue

                widget = item.widget()
                if not widget:
                    continue
                
                # Buscar el label que contiene el código del programa para identificar el widget
                # Buscamos dentro del widget por el código del programa
                found_widget = False

                # Método 1: Buscar por el texto del código del programa
                # Asumiendo que el widget contiene un QLabel con el código
                for child in widget.findChildren(QLabel):
                    child_text = child.text()
                    # Verificar si este label contiene información del programa que estamos buscando
                    if child_text and str(inscripcion_id) in child_text:
                        found_widget = True
                        break
                    
                # Método alternativo: Verificar si el widget tiene propiedad dinámica
                widget_id = widget.property("inscripcion_id")
                if widget_id and widget_id == inscripcion_id:
                    found_widget = True

                if found_widget:
                    # Obtener datos actualizados
                    from config.database import Database
                    connection = Database.get_connection()
                    if connection:
                        cursor = connection.cursor()
                        query = """
                        SELECT 
                            i.id as inscripcion_id,
                            p.id as programa_id,
                            p.codigo,
                            p.nombre,
                            p.costo_total,
                            p.costo_matricula,
                            p.costo_inscripcion,
                            p.costo_mensualidad,
                            p.numero_cuotas,
                            i.estado as estado_inscripcion,
                            i.fecha_inscripcion,
                            i.descuento_aplicado
                        FROM inscripciones i
                        JOIN programas p ON i.programa_id = p.id
                        WHERE i.id = %s
                        """
                        cursor.execute(query, (inscripcion_id,))
                        result = cursor.fetchone()
                        cursor.close()
                        Database.return_connection(connection)

                        if result:
                            column_names = [desc[0] for desc in cursor.description]
                            programa_data = dict(zip(column_names, result))
                            programa_enriquecido = self.enriquecer_datos_programa_inscrito(programa_data)

                            # Reemplazar widget
                            nuevo_widget = self.crear_item_programa_inscrito(programa_enriquecido)

                            # Agregar propiedad al widget para identificarlo luego
                            nuevo_widget.setProperty("inscripcion_id", inscripcion_id)

                            self.listado_layout_container.insertWidget(i, nuevo_widget)
                            widget.deleteLater()

                    break

        except Exception as e:
            logger.error(f"Error recargando programa: {e}")
            self.mostrar_mensaje("Error", f"No se pudo recargar el programa: {str(e)}", "error")
    
    # ===== MÉTODOS OVERRIDE DE BASE OVERLAY =====
    
    def guardar_datos(self):
        """Guardar los datos de la inscripción (llamado por BaseOverlay)"""
        try:
            # Obtener datos del formulario
            datos = self.obtener_datos()
            
            # Validar formulario
            valido, errores = self.validar_formulario()
            
            if not valido:
                mensaje_error = "Por favor corrija los siguientes errores:\n\n- " + "\n- ".join(errores)
                self.mostrar_mensaje("Validación", mensaje_error, "warning")
                return
            
            logger.info(f"🔵 Guardando inscripción - Modo: {self.modo}")
            logger.info(f"   Estudiante ID: {datos.get('estudiante_id')}")
            logger.info(f"   Programa ID: {datos.get('programa_id')}")
            
            if self.modo == "nuevo":
                # **LLAMAR A InscripcionModel.crear_inscripcion**
                try:
                    resultado = InscripcionModel.crear_inscripcion(
                        estudiante_id=datos['estudiante_id'],
                        programa_id=datos['programa_id'],
                        descuento_aplicado=datos.get('descuento', 0),
                        observaciones=None,  # Puedes agregar campo para observaciones
                        fecha_inscripcion=datos.get('fecha_inscripcion')
                    )
                    
                    logger.info(f"🔵 Resultado de crear_inscripcion: {resultado}")
                    
                    if resultado.get('exito', False) or resultado.get('success', False):
                        mensaje = resultado.get('mensaje', resultado.get('message', 'Inscripción creada exitosamente'))
                        self.mostrar_mensaje("✅ Éxito", mensaje, "success")
                        self.inscripcion_creada.emit(datos)
                        QTimer.singleShot(1000, self.close_overlay)
                    else:
                        mensaje_error = resultado.get('mensaje', resultado.get('message', 'No se pudo crear la inscripción'))
                        self.mostrar_mensaje("Error", mensaje_error, "error")
                    
                except Exception as e:
                    logger.error(f"Error en modelo al crear inscripción: {e}", exc_info=True)
                    self.mostrar_mensaje(
                        "Error del sistema", 
                        f"No se pudo crear la inscripción. Error: {str(e)}", 
                        "error"
                    )
                
            elif self.modo == "editar":
                # **CORRECCIÓN: Llamar correctamente a InscripcionModel.actualizar_inscripcion**
                if self.inscripcion_id is None:
                    self.mostrar_mensaje("Error", "ID de inscripción no disponible", "error")
                    return
                
                try:
                    resultado = InscripcionModel.actualizar_inscripcion(
                        inscripcion_id=self.inscripcion_id,
                        nuevo_estado=datos.get('estado'),
                        nuevo_descuento=datos.get('descuento'),
                        nuevas_observaciones=None  # Puedes agregar campo para observaciones
                    )
                    
                    logger.info(f"🔵 Resultado de actualizar_inscripcion: {resultado}")
                    
                    if resultado.get('exito', False) or resultado.get('success', False):
                        mensaje = resultado.get('mensaje', resultado.get('message', 'Inscripción actualizada exitosamente'))
                        self.mostrar_mensaje("✅ Éxito", mensaje, "success")
                        self.inscripcion_actualizada.emit(datos)
                        QTimer.singleShot(1000, self.close_overlay)
                    else:
                        mensaje_error = resultado.get('mensaje', resultado.get('message', 'Error al actualizar'))
                        self.mostrar_mensaje("Error", mensaje_error, "error")
                    
                except Exception as e:
                    logger.error(f"Error actualizando inscripción: {e}", exc_info=True)
                    self.mostrar_mensaje("Error", f"Error al actualizar: {str(e)}", "error")
            
        except Exception as e:
            logger.error(f"Error general en guardar_datos: {e}", exc_info=True)
            self.mostrar_mensaje("Error", f"Error al guardar: {str(e)}", "error")
    
    def cargar_datos_desde_db(self, inscripcion_id: int):
        """Cargar datos de inscripción desde la base de datos"""
        try:
            # Obtener datos completos de la inscripción
            from config.database import Database
            connection = Database.get_connection()
            if connection:
                cursor = connection.cursor()
                
                # Consulta para obtener datos completos de la inscripción
                query = """
                SELECT 
                    i.id, i.estudiante_id, i.programa_id, i.fecha_inscripcion,
                    i.estado, i.descuento_aplicado, i.observaciones,
                    e.ci_numero, e.ci_expedicion, e.nombres, e.apellido_paterno,
                    e.apellido_materno, e.email, e.telefono,
                    p.codigo, p.nombre, p.costo_total, p.costo_matricula,
                    p.costo_inscripcion, p.estado as programa_estado
                FROM inscripciones i
                JOIN estudiantes e ON i.estudiante_id = e.id
                JOIN programas p ON i.programa_id = p.id
                WHERE i.id = %s
                """
                
                cursor.execute(query, (inscripcion_id,))
                result = cursor.fetchone()
                
                cursor.close()
                Database.return_connection(connection)
                
                if result:
                    # Convertir a diccionario
                    column_names = [desc[0] for desc in cursor.description]
                    datos = dict(zip(column_names, result))
                    
                    # Cargar en el formulario
                    self.cargar_datos(datos)
                else:
                    self.mostrar_mensaje("Error", "No se encontró la inscripción", "error")
                    self.close_overlay()
                    
        except Exception as e:
            logger.error(f"Error cargando datos desde DB: {e}")
            self.mostrar_mensaje("Error", f"No se pudieron cargar los datos: {str(e)}", "error")
    
    def cargar_datos(self, datos):
        """Cargar datos de inscripción existente"""
        self.inscripcion_id = datos.get('id')
        self.original_data = datos.copy()
        
        # Cargar estudiante
        estudiante_id = datos.get('estudiante_id')
        if estudiante_id:
            self.estudiante_id = estudiante_id
            self.cargar_info_estudiante(estudiante_id)
        
        # Cargar programa
        programa_id = datos.get('programa_id')
        if programa_id:
            self.programa_id = programa_id
            self.cargar_info_programa(programa_id)
        
        # Cargar detalles de inscripción si existen en los datos
        fecha_inscripcion = datos.get('fecha_inscripcion')
        if fecha_inscripcion and hasattr(self, 'fecha_inscripcion_date'):
            try:
                qdate = QDate.fromString(fecha_inscripcion[:10], 'yyyy-MM-dd')
                if qdate.isValid():
                    self.fecha_inscripcion_date.setDate(qdate)
            except:
                pass
        
        # Si tenemos ambos IDs, mostrar formulario de inscripción
        if self.estudiante_id and self.programa_id:
            self.configurar_interfaz_segun_contexto()
    
    def validar_formulario(self):
        """Validar formulario de inscripción"""
        errores = []
        
        # Validaciones básicas dependiendo del modo
        if self.estudiante_id and self.programa_id:
            # Modo inscripción: validar formulario completo
            if not self.fecha_inscripcion_date.date().isValid():
                errores.append("Fecha de inscripción no válida")
            
            if self.descuento_spin.value() < 0 or self.descuento_spin.value() > 100:
                errores.append("Descuento debe estar entre 0% y 100%")
        
        return len(errores) == 0, errores
    
    def obtener_datos(self):
        """Obtener datos del formulario"""
        datos = {
            'estudiante_id': self.estudiante_id,
            'programa_id': self.programa_id,
            'fecha_inscripcion': self.fecha_inscripcion_date.date().toString('yyyy-MM-dd'),
            'estado': self.estado_inscripcion_combo.currentText(),
            'descuento': self.descuento_spin.value(),
            'estudiante_data': self.estudiante_data,
            'programa_data': self.programa_data
        }
        
        return datos
    
    def clear_form(self):
        """Limpiar formulario completo"""
        # self.inscripcion_id = None
        # self.estudiante_id = None
        # self.programa_id = None
        # self.original_data = {}

        # Limpiar datos
        self.estudiante_data = None
        self.programa_data = None
        self.programas_inscritos = []
        self.estudiantes_inscritos = []
        self.programas_disponibles = []
        self.estudiantes_disponibles = []

        # Limpiar interfaz solo si los widgets existen
        if hasattr(self, 'listado_layout_container'):
            self.limpiar_listados()
            
        # Ocultar secciones solo si existen
        grupos_para_ocultar = [
            'grupo_info_estudiante',
            'grupo_buscar_estudiante', 
            'grupo_info_programa',
            'grupo_programas_disponibles',
            'grupo_buscar_programa',
            'seccion_listado_frame',
            'seccion_formulario_frame'
        ]
        
        for grupo in grupos_para_ocultar:
            if hasattr(self, grupo):
                widget = getattr(self, grupo)
                if widget:
                    widget.setVisible(False)
        
        # Limpiar campos solo si existen
        campos_a_limpiar = [
            ('fecha_inscripcion_date', lambda x: x.setDate(QDate.currentDate())),
            ('fecha_pago_date', lambda x: x.setDate(QDate.currentDate())),
            ('descuento_spin', lambda x: x.setValue(0.0)),
            ('estado_inscripcion_combo', lambda x: x.setCurrentIndex(0) if x.count() > 0 else None),
            ('estado_transaccion_combo', lambda x: x.setCurrentIndex(0) if x.count() > 0 else None),
            ('forma_pago_combo', lambda x: x.setCurrentIndex(0) if x.count() > 0 else None),
            ('origen_transaccion_input', lambda x: x.clear()),
            ('monto_pago_input', lambda x: x.clear()),
            ('costo_total_label', lambda x: x.setText("0.00 Bs")),
            ('resumen_monto_label', lambda x: x.setText("0.00 Bs")),
            ('inscripcion_id_label', lambda x: x.setText("📋 ID de inscripción: <span style='color:#7f8c8d; font-style:italic;'>No registrado</span>"))
        ]
        
        for campo_nombre, accion in campos_a_limpiar:
            if hasattr(self, campo_nombre):
                widget = getattr(self, campo_nombre)
                if widget:
                    try:
                        accion(widget)
                    except Exception as e:
                        logger.warning(f"No se pudo limpiar {campo_nombre}: {e}")
        
        # Limpiar tablas y listas
        tablas_a_limpiar = [
            'detalles_table',
            'documentos_list_widget', 
            'historial_table'  # Agregado para prevenir error futuro
        ]
        
        for tabla in tablas_a_limpiar:
            if hasattr(self, tabla):
                widget = getattr(self, tabla)
                if widget:
                    if tabla == 'detalles_table' or tabla == 'historial_table':
                        widget.setRowCount(0)
                    elif tabla == 'documentos_list_widget':
                        widget.clear()
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo", inscripcion_id=None,
                estudiante_id: Optional[int] = None, programa_id: Optional[int] = None):
        """Mostrar overlay con configuración específica"""
        self.solo_lectura = solo_lectura
        self.modo = modo
        
        # Configurar IDs según parámetros
        if estudiante_id:
            self.estudiante_id = estudiante_id
        
        if programa_id:
            self.programa_id = programa_id
        
        logger.debug(f"Mostrando formulario - Modo: {modo}, Estudiante ID: {self.estudiante_id}, Programa ID: {self.programa_id}, Inscripción ID: {inscripcion_id}")
        
        # Configurar título según modo
        titulo = ""
        if modo == "nuevo":
            if self.estudiante_id and self.programa_id:
                titulo = "🎓 Nueva Inscripción"
            elif self.estudiante_id:
                titulo = "👤 Gestión del Estudiante"
            elif self.programa_id:
                titulo = "📚 Gestión del Programa"
            else:
                titulo = "🎓 Gestión de Inscripciones"
        elif modo == "editar" and inscripcion_id:
            titulo = f"✏️ Editar Inscripción - ID: {inscripcion_id}"
        elif modo == "lectura" and inscripcion_id:
            titulo = f"👁️ Ver Inscripción - ID: {inscripcion_id}"
        
        self.set_titulo(titulo)
        
        # **IMPORTANTE: Asegurar que la UI está configurada antes de cargar datos**
        if not hasattr(self, 'splitter_principal') or self.splitter_principal is None:
            logger.warning("UI no está configurada, llamando a setup_ui_especifica")
            self.setup_ui_especifica()
            self.setup_conexiones_especificas()

        # Cargar datos si se proporcionan
        if datos:
            self.cargar_datos(datos)
        elif inscripcion_id and not datos:
            self.cargar_datos_desde_db(inscripcion_id)
        else:
            self.clear_form()
            self.configurar_interfaz_segun_contexto()
        
        # Configurar botones base según modo
        if modo == "lectura" or solo_lectura:
            self.btn_guardar.setText("👈 VOLVER")
            self.btn_guardar.setVisible(False)
            self.btn_cancelar.setText("👈 CERRAR")
        elif modo == "editer":
            self.btn_guardar.setText("💾 ACTUALIZAR")
            self.btn_guardar.setVisible(True)
        else:
            self.btn_guardar.setText("💾 GUARDAR")
            self.btn_guardar.setVisible(False)  # Ocultamos porque tenemos nuestros propios botones
        
        # Llamar al método base
        super().show_form(solo_lectura)
        
        logger.info(f"✅ Overlay mostrado - Modo: {modo}, Est: {self.estudiante_id}, Prog: {self.programa_id}")
    
    def close_overlay(self):
        """Cerrar el overlay"""
        self.close()
        if hasattr(self, 'overlay_closed'):
            self.overlay_closed.emit()
    
    # ===== MÉTODOS DEPRECADOS / MANTENIMIENTO =====
    
    def calcular_total(self):
        """Calcular el total de la transacción (método antiguo)"""
        try:
            # TODO: Calcular basado en costo del programa y descuento
            costo_base = self.programa_data.get('costo_total', 0) if self.programa_data else 0
            descuento = self.descuento_spin.value()
            
            if descuento > 0:
                total = costo_base * (1 - descuento / 100)
            else:
                total = costo_base
            
            # Actualizar ambos labels si existen
            if hasattr(self, 'costo_total_label') and self.costo_total_label:
                self.costo_total_label.setText(f"{total:.2f} Bs")
                
            if hasattr(self, 'resumen_monto_label') and self.resumen_monto_label:
                self.resumen_monto_label.setText(f"{total:.2f} Bs")
                
        except Exception as e:
            logger.error(f"Error calculando total: {e}")
            if hasattr(self, 'costo_total_label') and self.costo_total_label:
                self.costo_total_label.setText("0.00 Bs")
