# -*- coding: utf-8 -*-
# view/overlays/inscripcion_overlay.py
"""
Overlay inteligente para gestión de inscripciones estudiantiles a programas académicos.

Funcionalidades principales:
1. Si estudiante_id = None: Mostrar selector de estudiante (búsqueda por CI, nombre, apellidos)
2. Si programa_id = None: Mostrar selector de programa (programas disponibles)
3. Si ambos IDs existen pero no hay inscripción: Mostrar formulario de nueva inscripción
4. Si existe inscripción: Mostrar información y transacciones relacionadas
5. Si solo estudiante_id: Mostrar inscripciones existentes del estudiante

Hereda de BaseOverlay.
"""
import os
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDateEdit, QFrame, QScrollArea, QGridLayout,
    QMessageBox, QGroupBox, QSizePolicy, QSplitter, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QProgressBar, QRadioButton, QButtonGroup, QFormLayout
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QFont, QColor, QBrush, QPixmap, QIcon

# Importar modelos
from model.inscripcion_model import InscripcionModel
from model.estudiante_model import EstudianteModel
from model.programa_model import ProgramaModel
from model.transaccion_model import TransaccionModel

from .base_overlay import BaseOverlay
from view.overlays.transaccion_overlay import TransaccionOverlay

# Configurar logger
logger = logging.getLogger(__name__)

class InscripcionOverlay(BaseOverlay):
    """
    Overlay inteligente para la gestión de inscripciones estudiantiles.
    
    Maneja 5 modos principales:
    1. Selección de estudiante (cuando estudiante_id = None)
    2. Visualización de inscripciones del estudiante (cuando solo estudiante_id)
    3. Selección de programa (cuando programa_id = None)
    4. Nueva inscripción (cuando ambos IDs existen pero no hay inscripción)
    5. Visualización de inscripción (cuando existe inscripción_id)
    """
    
    # Señales específicas
    inscripcion_seleccionada = Signal(dict)
    inscripcion_creada = Signal(dict)
    inscripcion_actualizada = Signal(dict)
    estudiante_seleccionado = Signal(int)
    programa_seleccionado = Signal(int)
    
    # ===== MÉTODOS DE INICIALIZACIÓN =====
    
    def __init__(self, parent=None):
        super().__init__(parent, "🎓 Gestión de Inscripción", 95, 95)
        
        # Variables de estado
        self.inscripcion_id: Optional[int] = None
        self.estudiante_id: Optional[int] = None
        self.programa_id: Optional[int] = None
        
        # Listas de datos
        self.inscripciones: List[Dict] = []
        self.estudiantes_encontrados: List[Dict] = []
        self.programas_disponibles: List[Dict] = []
        
        # Widgets principales
        self.estudiante_id_label: Optional[QLabel] = None
        self.programa_id_label: Optional[QLabel] = None
        
        # Widgets para selección de estudiante
        self.seleccion_estudiante_frame: Optional[QFrame] = None
        self.busqueda_estudiante_input: Optional[QLineEdit] = None
        self.btn_buscar_estudiante: Optional[QPushButton] = None
        self.estudiantes_list_widget: Optional[QWidget] = None
        self.estudiantes_list_layout: Optional[QVBoxLayout] = None
        
        # Widgets para selección de programa
        self.seleccion_programa_frame: Optional[QFrame] = None
        self.programa_combo: Optional[QComboBox] = None
        self.btn_seleccionar_programa: Optional[QPushButton] = None
        
        # Widgets para formulario de nueva inscripción
        self.nueva_inscripcion_frame: Optional[QFrame] = None
        self.fecha_inscripcion_input: Optional[QDateEdit] = None
        self.valor_real_display: Optional[QLabel] = None  # Nuevo
        self.valor_final_input: Optional[QLineEdit] = None  # Cambiado de descuento_input
        self.observaciones_input: Optional[QTextEdit] = None
        self.btn_crear_inscripcion: Optional[QPushButton] = None
        
        # Widgets para listado de inscripciones
        self.inscripciones_container: Optional[QWidget] = None
        self.inscripciones_layout: Optional[QVBoxLayout] = None
        
        # Configurar UI
        self.setup_ui_especifica()
        self.setup_conexiones_especificas()
        
        logger.debug("✅ InscripcionOverlay inteligente inicializado")
    
    def setup_ui_especifica(self):
        """Configurar la interfaz completa con todos los modos"""
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
        scroll_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ===== SECCIÓN DE INFORMACIÓN BÁSICA =====
        info_group = QGroupBox("📋 INFORMACIÓN BÁSICA")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #3498db;
                border-radius: 8px;
                margin-top: 5px;
                padding-top: 12px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #2980b9;
                font-size: 14px;
            }
        """)
        
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(10)
        info_layout.setContentsMargins(15, 15, 15, 15)
        
        # Etiqueta para estudiante_id
        estudiante_label = QLabel("👤 ESTUDIANTE:")
        estudiante_label.setStyleSheet("""
            font-weight: bold; 
            color: #2c3e50; 
            font-size: 13px;
            padding: 5px 0px;
        """)
        info_layout.addWidget(estudiante_label, 0, 0)
        
        self.estudiante_id_label = QLabel("NO ESPECIFICADO")
        self.estudiante_id_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            padding: 8px 12px;
            background-color: white;
            border-radius: 6px;
            border: 1px solid #3498db;
            min-height: 35px;
        """)
        info_layout.addWidget(self.estudiante_id_label, 0, 1)
        
        # Etiqueta para programa_id
        programa_label = QLabel("📚 PROGRAMA:")
        programa_label.setStyleSheet("""
            font-weight: bold; 
            color: #2c3e50; 
            font-size: 13px;
            padding: 5px 0px;
        """)
        info_layout.addWidget(programa_label, 1, 0)
        
        self.programa_id_label = QLabel("NO ESPECIFICADO")
        self.programa_id_label.setStyleSheet("""
            font-size: 14px;
            font-weight: bold;
            padding: 8px 12px;
            background-color: white;
            border-radius: 6px;
            border: 1px solid #3498db;
            min-height: 35px;
        """)
        info_layout.addWidget(self.programa_id_label, 1, 1)
        
        main_layout.addWidget(info_group)
        
        # ===== SECCIÓN DE SELECCIÓN DE ESTUDIANTE =====
        self.seleccion_estudiante_frame = QFrame()
        self.seleccion_estudiante_frame.setObjectName("seleccionEstudianteFrame")
        self.seleccion_estudiante_frame.setStyleSheet("""
            #seleccionEstudianteFrame {
                background-color: #f0f8ff;
                border: 2px dashed #3498db;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        self.seleccion_estudiante_frame.setVisible(False)
        
        estudiante_layout = QVBoxLayout(self.seleccion_estudiante_frame)
        estudiante_layout.setSpacing(12)
        estudiante_layout.setContentsMargins(20, 15, 20, 15)
        
        # Título de la sección
        titulo_estudiante = QLabel("👤 SELECCIONAR ESTUDIANTE PARA INSCRIBIR")
        titulo_estudiante.setStyleSheet("""
            font-weight: bold;
            font-size: 15px;
            color: #2980b9;
            padding-bottom: 10px;
            border-bottom: 1px dashed #3498db;
        """)
        estudiante_layout.addWidget(titulo_estudiante)
        
        # Información
        info_estudiante = QLabel("Busque estudiante por CI, nombre o apellidos:")
        info_estudiante.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
            font-style: italic;
            margin-bottom: 10px;
        """)
        estudiante_layout.addWidget(info_estudiante)
        
        # Layout para búsqueda
        busqueda_layout = QHBoxLayout()
        busqueda_layout.setSpacing(10)
        
        # Campo de búsqueda
        self.busqueda_estudiante_input = QLineEdit()
        self.busqueda_estudiante_input.setPlaceholderText("Ej: 1234567, Juan, Pérez...")
        self.busqueda_estudiante_input.setMinimumHeight(40)
        self.busqueda_estudiante_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 8px 12px;
                background-color: white;
                border: 2px solid #3498db;
                border-radius: 6px;
            }
        """)
        busqueda_layout.addWidget(self.busqueda_estudiante_input, 1)
        
        # Botón para buscar
        self.btn_buscar_estudiante = QPushButton("🔍 BUSCAR")
        self.btn_buscar_estudiante.setMinimumHeight(40)
        self.btn_buscar_estudiante.setMinimumWidth(150)
        self.btn_buscar_estudiante.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #3498db, stop:1 #2980b9);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2980b9, stop:1 #1f618d);
            }
        """)
        busqueda_layout.addWidget(self.btn_buscar_estudiante)
        
        estudiante_layout.addLayout(busqueda_layout)
        
        # Contenedor para lista de estudiantes
        estudiantes_scroll = QScrollArea()
        estudiantes_scroll.setWidgetResizable(True)
        estudiantes_scroll.setFrameShape(QFrame.Shape.NoFrame)
        estudiantes_scroll.setMinimumHeight(200)
        
        self.estudiantes_list_widget = QWidget()
        self.estudiantes_list_layout = QVBoxLayout(self.estudiantes_list_widget)
        self.estudiantes_list_layout.setSpacing(10)
        self.estudiantes_list_layout.setContentsMargins(5, 5, 5, 5)
        self.estudiantes_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        estudiantes_scroll.setWidget(self.estudiantes_list_widget)
        estudiante_layout.addWidget(estudiantes_scroll, 1)
        
        main_layout.addWidget(self.seleccion_estudiante_frame)
        
        # ===== SECCIÓN DE SELECCIÓN DE PROGRAMA =====
        self.seleccion_programa_frame = QFrame()
        self.seleccion_programa_frame.setObjectName("seleccionProgramaFrame")
        self.seleccion_programa_frame.setStyleSheet("""
            #seleccionProgramaFrame {
                background-color: #f0f8ff;
                border: 2px dashed #27ae60;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        self.seleccion_programa_frame.setVisible(False)
        
        seleccion_layout = QVBoxLayout(self.seleccion_programa_frame)
        seleccion_layout.setSpacing(12)
        seleccion_layout.setContentsMargins(20, 15, 20, 15)
        
        # Título de la sección
        titulo_seleccion = QLabel("📚 SELECCIONAR PROGRAMA PARA INSCRIBIR")
        titulo_seleccion.setStyleSheet("""
            font-weight: bold;
            font-size: 15px;
            color: #27ae60;
            padding-bottom: 10px;
            border-bottom: 1px dashed #27ae60;
        """)
        seleccion_layout.addWidget(titulo_seleccion)
        
        # Información
        info_seleccion = QLabel("Seleccione un programa al que el estudiante NO esté inscrito:")
        info_seleccion.setStyleSheet("""
            color: #7f8c8d;
            font-size: 12px;
            font-style: italic;
            margin-bottom: 10px;
        """)
        seleccion_layout.addWidget(info_seleccion)
        
        # Layout para combobox y botón
        combo_layout = QHBoxLayout()
        combo_layout.setSpacing(10)
        
        # ComboBox para programas disponibles
        self.programa_combo = QComboBox()
        self.programa_combo.setMinimumHeight(40)
        self.programa_combo.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 8px 12px;
                background-color: white;
                border: 2px solid #27ae60;
                border-radius: 6px;
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
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #27ae60;
                selection-background-color: #27ae60;
                selection-color: white;
                font-size: 13px;
            }
        """)
        self.programa_combo.addItem("-- SELECCIONE UN PROGRAMA --", None)
        combo_layout.addWidget(self.programa_combo, 1)
        
        # Botón para seleccionar programa
        self.btn_seleccionar_programa = QPushButton("✅ SELECCIONAR")
        self.btn_seleccionar_programa.setMinimumHeight(40)
        self.btn_seleccionar_programa.setMinimumWidth(150)
        self.btn_seleccionar_programa.setEnabled(False)
        self.btn_seleccionar_programa.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #27ae60, stop:1 #219653);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #219653, stop:1 #1e8449);
            }
            QPushButton:disabled {
                background: #95a5a6;
                color: #ecf0f1;
            }
        """)
        combo_layout.addWidget(self.btn_seleccionar_programa)
        
        seleccion_layout.addLayout(combo_layout)
        main_layout.addWidget(self.seleccion_programa_frame)
        
        # ===== SECCIÓN DE NUEVA INSCRIPCIÓN =====
        self.nueva_inscripcion_frame = QFrame()
        self.nueva_inscripcion_frame.setObjectName("nuevaInscripcionFrame")
        self.nueva_inscripcion_frame.setStyleSheet("""
            #nuevaInscripcionFrame {
                background-color: #f0f8ff;
                border: 2px dashed #9b59b6;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        self.nueva_inscripcion_frame.setVisible(False)
        
        nueva_insc_layout = QVBoxLayout(self.nueva_inscripcion_frame)
        nueva_insc_layout.setSpacing(15)
        nueva_insc_layout.setContentsMargins(20, 15, 20, 15)
        
        # Título de la sección
        titulo_nueva = QLabel("➕ NUEVA INSCRIPCIÓN")
        titulo_nueva.setStyleSheet("""
            font-weight: bold;
            font-size: 15px;
            color: #9b59b6;
            padding-bottom: 10px;
            border-bottom: 1px dashed #9b59b6;
        """)
        nueva_insc_layout.addWidget(titulo_nueva)
        
        # Formulario de nueva inscripción
        form_layout = QGridLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(10, 10, 10, 10)
        
        # Fecha de inscripción
        fecha_label = QLabel("📅 FECHA DE INSCRIPCIÓN:")
        fecha_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        form_layout.addWidget(fecha_label, 0, 0)
        
        self.fecha_inscripcion_input = QDateEdit()
        self.fecha_inscripcion_input.setDate(QDate.currentDate())
        self.fecha_inscripcion_input.setCalendarPopup(True)
        self.fecha_inscripcion_input.setMinimumHeight(35)
        self.fecha_inscripcion_input.setStyleSheet("""
            QDateEdit {
                font-size: 13px;
                padding: 6px;
                background-color: white;
                border: 1px solid #9b59b6;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(self.fecha_inscripcion_input, 0, 1)
        
        # VALOR REAL DEL PROGRAMA (nuevo label no editable)
        valor_real_label = QLabel("💰 VALOR REAL DEL PROGRAMA:")
        valor_real_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        form_layout.addWidget(valor_real_label, 1, 0)
        
        self.valor_real_display = QLabel("0.00 Bs.")
        self.valor_real_display.setMinimumHeight(35)
        self.valor_real_display.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                padding: 6px 12px;
                background-color: #f0f0f0;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                color: #2c3e50;
            }
        """)
        form_layout.addWidget(self.valor_real_display, 1, 1)
        
        # VALOR FINAL (nuevo campo reemplazando descuento)
        valor_final_label = QLabel("💵 VALOR FINAL DE INSCRIPCIÓN:")
        valor_final_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        form_layout.addWidget(valor_final_label, 2, 0)

        self.valor_final_input = QLineEdit()
        self.valor_final_input.setPlaceholderText("Ingrese el valor final acordado")
        self.valor_final_input.setMinimumHeight(35)
        self.valor_final_input.setStyleSheet("""
            QLineEdit {
                font-size: 14px;
                padding: 6px 12px;
                background-color: white;
                border: 2px solid #9b59b6;
                border-radius: 4px;
                font-weight: bold;
            }
        """)
        form_layout.addWidget(self.valor_final_input, 2, 1)
        
        # Observaciones
        obs_label = QLabel("📝 OBSERVACIONES:")
        obs_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
        form_layout.addWidget(obs_label, 3, 0)
        
        self.observaciones_input = QTextEdit()
        self.observaciones_input.setMaximumHeight(100)
        self.observaciones_input.setStyleSheet("""
            QTextEdit {
                font-size: 13px;
                padding: 6px;
                background-color: white;
                border: 1px solid #9b59b6;
                border-radius: 4px;
            }
        """)
        form_layout.addWidget(self.observaciones_input, 3, 1, 1, 2)
        
        nueva_insc_layout.addLayout(form_layout)
        
        # Información adicional sobre formato de observaciones
        info_obs = QLabel("ℹ️ Si el valor final es menor al real, las observaciones deben incluir justificación")
        info_obs.setStyleSheet("""
            color: #e67e22;
            font-size: 11px;
            font-style: italic;
            padding: 5px;
            background-color: #fef5e7;
            border-radius: 4px;
        """)
        info_obs.setWordWrap(True)
        nueva_insc_layout.addWidget(info_obs)
        
        # Botón para crear inscripción
        self.btn_crear_inscripcion = QPushButton("✅ CREAR INSCRIPCIÓN")
        self.btn_crear_inscripcion.setMinimumHeight(45)
        self.btn_crear_inscripcion.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #9b59b6, stop:1 #8e44ad);
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
                padding: 0 30px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #8e44ad, stop:1 #7d3c98);
            }
        """)
        nueva_insc_layout.addWidget(self.btn_crear_inscripcion)
        
        main_layout.addWidget(self.nueva_inscripcion_frame)
        
        # ===== SECCIÓN DE LISTADO DE INSCRIPCIONES =====
        listado_group = QGroupBox("📊 INSCRIPCIONES RELACIONADAS")
        listado_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #e74c3c;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 12px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px 0 10px;
                color: #e74c3c;
                font-size: 14px;
            }
        """)
        
        listado_layout = QVBoxLayout(listado_group)
        listado_layout.setSpacing(10)
        listado_layout.setContentsMargins(15, 20, 15, 15)
        
        self.inscripciones_container = QWidget()
        self.inscripciones_layout = QVBoxLayout(self.inscripciones_container)
        self.inscripciones_layout.setSpacing(15)
        self.inscripciones_layout.setContentsMargins(5, 5, 5, 5)
        self.inscripciones_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        listado_layout.addWidget(self.inscripciones_container, 1)
        
        # Botón para refrescar
        refresh_btn = QPushButton("🔄 ACTUALIZAR LISTADO")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
                font-size: 13px;
                min-height: 40px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
                border: 1px solid #1f618d;
            }
        """)
        refresh_btn.clicked.connect(self.cargar_inscripciones)
        listado_layout.addWidget(refresh_btn)
        
        main_layout.addWidget(listado_group, 1)
        
        scroll_widget.setWidget(main_widget)
        self.content_layout.addWidget(scroll_widget, 1)
    
    def setup_conexiones_especificas(self):
        """Configurar conexiones específicas"""
        # Conexiones para búsqueda de estudiante
        if self.btn_buscar_estudiante:
            self.btn_buscar_estudiante.clicked.connect(self.buscar_estudiante)
            
        if self.busqueda_estudiante_input:
            self.busqueda_estudiante_input.returnPressed.connect(self.buscar_estudiante)
            # También conectar textChanged para búsqueda en tiempo real (opcional)
            # self.busqueda_estudiante_input.textChanged.connect(self.buscar_estudiante_automatico)
            
        # Conexiones para selección de programa
        if self.programa_combo:
            self.programa_combo.currentIndexChanged.connect(self.actualizar_boton_seleccion_programa)
            
        if self.btn_seleccionar_programa:
            self.btn_seleccionar_programa.clicked.connect(self.seleccionar_programa_desde_combo)
            
        # Conexiones para nueva inscripción
        if self.btn_crear_inscripcion:
            self.btn_crear_inscripcion.clicked.connect(self.crear_nueva_inscripcion)
            
        # Asegurar que los botones base tengan conexión
        if self.btn_cancelar:
            self.btn_cancelar.clicked.connect(self.close_overlay)
            
        # Nueva conexión para autocompletar observaciones
        if self.valor_final_input:
            self.valor_final_input.textChanged.connect(self.actualizar_observaciones_automaticas)
            
        # Debug: Verificar conexiones
        logger.debug("✅ Conexiones específicas configuradas")
    
    # ===== MÉTODOS PARA SELECCIÓN DE ESTUDIANTE =====
    
    def buscar_estudiante(self):
        """Buscar estudiantes según criterio ingresado"""
        try:
            criterio = self.busqueda_estudiante_input.text().strip()  # type: ignore
            if not criterio:
                self.mostrar_mensaje("Advertencia", "Ingrese un criterio de búsqueda", "warning")
                return
            
            # Limpiar lista anterior
            if self.estudiantes_list_layout:
                while self.estudiantes_list_layout.count():
                    child = self.estudiantes_list_layout.takeAt(0)
                    widget = child.widget()
                    if widget:
                        widget.deleteLater()
                        
            self.estudiantes_encontrados = []
            
            # Intentar buscar por diferentes criterios
            resultados = []
            
            # Si el criterio es numérico (posible CI)
            if criterio.isdigit():
                resultados = EstudianteModel.buscar_estudiantes(
                    ci_numero=criterio
                )
                
            # Si no hay resultados o es texto
            if not resultados:
                # Dividir por espacios para buscar nombre/apellidos
                partes = criterio.split()
                
                if len(partes) >= 2:
                    # Asumir que son nombre y apellido
                    nombre = ' '.join(partes[:-1])
                    apellido = partes[-1]
                    
                    # Buscar por nombre completo
                    from config.database import Database
                    connection = Database.get_connection()
                    if connection:
                        cursor = connection.cursor()
                        query = """
                        SELECT * FROM estudiantes 
                        WHERE (nombres ILIKE %s OR apellido_paterno ILIKE %s OR apellido_materno ILIKE %s)
                        OR (nombres ILIKE %s AND apellido_paterno ILIKE %s)
                        LIMIT 50
                        """
                        cursor.execute(query, (
                            f'%{criterio}%', f'%{criterio}%', f'%{criterio}%',
                            f'%{nombre}%', f'%{apellido}%'
                        ))
                        if not cursor:
                            logger.warning("No se pudo ejecutar la consulta de búsqueda de estudiantes")
                            self.mostrar_mensaje("Error", "Error al ejecutar la búsqueda de estudiantes", "error")
                            return
                        
                        resultados_raw = cursor.fetchall()
                        if resultados_raw:
                            column_names = [desc[0] for desc in cursor.description] # type: ignore
                            resultados = [dict(zip(column_names, row)) for row in resultados_raw]
                            
                        cursor.close()
                        Database.return_connection(connection)
                else:
                    # Búsqueda simple por cualquier campo
                    from config.database import Database
                    connection = Database.get_connection()
                    if connection:
                        cursor = connection.cursor()
                        query = """
                        SELECT * FROM estudiantes 
                        WHERE nombres ILIKE %s 
                        OR apellido_paterno ILIKE %s 
                        OR apellido_materno ILIKE %s
                        OR email ILIKE %s
                        OR telefono ILIKE %s
                        OR CONCAT(ci_numero, '-', ci_expedicion) ILIKE %s
                        LIMIT 50
                        """
                        cursor.execute(query, (
                            f'%{criterio}%', f'%{criterio}%', f'%{criterio}%',
                            f'%{criterio}%', f'%{criterio}%', f'%{criterio}%'
                        ))
                        if not cursor:
                            logger.warning("No se pudo ejecutar la consulta de búsqueda de estudiantes")
                            self.mostrar_mensaje("Error", "Error al ejecutar la búsqueda de estudiantes", "error")
                            return
                        
                        resultados_raw = cursor.fetchall()
                        if resultados_raw:
                            column_names = [desc[0] for desc in cursor.description] # type: ignore
                            resultados = [dict(zip(column_names, row)) for row in resultados_raw]
                            
                        cursor.close()
                        Database.return_connection(connection)
                        
            if not resultados:
                no_data_label = QLabel("❌ No se encontraron estudiantes")
                no_data_label.setStyleSheet("""
                    color: #7f8c8d;
                    font-size: 13px;
                    font-style: italic;
                    padding: 20px;
                    text-align: center;
                """)
                if self.estudiantes_list_layout:
                    self.estudiantes_list_layout.addWidget(no_data_label)
                return
            
            self.estudiantes_encontrados = resultados
            
            # Crear tarjetas para cada estudiante encontrado
            for estudiante in resultados:
                tarjeta = self.crear_tarjeta_estudiante(estudiante)
                if tarjeta and self.estudiantes_list_layout:
                    self.estudiantes_list_layout.addWidget(tarjeta)
                    
            logger.debug(f"✅ Estudiantes encontrados: {len(resultados)}")
            
        except Exception as e:
            logger.error(f"Error buscando estudiantes: {e}")
            self.mostrar_mensaje("Error", f"Error al buscar estudiantes: {str(e)}", "error")
    
    def crear_tarjeta_estudiante(self, estudiante: Dict) -> QFrame:
        """Crear tarjeta para mostrar información de un estudiante"""
        tarjeta_frame = QFrame()
        tarjeta_frame.setObjectName("tarjetaEstudiante")
        tarjeta_frame.setStyleSheet("""
            #tarjetaEstudiante {
                background-color: white;
                border: 1px solid #3498db;
                border-radius: 6px;
                margin: 5px 0px;
            }
            #tarjetaEstudiante:hover {
                background-color: #e3f2fd;
                border: 2px solid #2980b9;
            }
        """)
        
        layout = QVBoxLayout(tarjeta_frame)
        layout.setSpacing(8)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Información básica
        estudiante_id = estudiante.get('id', '')
        nombres = estudiante.get('nombres', '')
        apellido_p = estudiante.get('apellido_paterno', '')
        apellido_m = estudiante.get('apellido_materno', '')
        ci_num = estudiante.get('ci_numero', '')
        ci_exp = estudiante.get('ci_expedicion', '')
        
        nombre_completo = f"{nombres} {apellido_p} {apellido_m}".strip()
        ci_completo = f"{ci_num}-{ci_exp}" if ci_num and ci_exp else "Sin CI"
        
        # Título con ID y nombre
        titulo_label = QLabel(f"👤 ID: {estudiante_id} - {nombre_completo}")
        titulo_label.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #2c3e50;
        """)
        layout.addWidget(titulo_label)
        
        # Información detallada
        info_layout = QGridLayout()
        info_layout.setSpacing(5)
        
        # CI
        ci_label = QLabel("🪪 CI:")
        ci_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        info_layout.addWidget(ci_label, 0, 0)
        
        ci_value = QLabel(ci_completo)
        ci_value.setStyleSheet("font-size: 12px; font-weight: bold;")
        info_layout.addWidget(ci_value, 0, 1)
        
        # Email
        email = estudiante.get('email', '') or 'Sin email'
        email_label = QLabel("📧 Email:")
        email_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        info_layout.addWidget(email_label, 1, 0)
        
        email_value = QLabel(email)
        email_value.setStyleSheet("font-size: 12px;")
        email_value.setWordWrap(True)
        info_layout.addWidget(email_value, 1, 1)
        
        # Teléfono
        telefono = estudiante.get('telefono', '') or 'Sin teléfono'
        tel_label = QLabel("📞 Teléfono:")
        tel_label.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        info_layout.addWidget(tel_label, 2, 0)
        
        tel_value = QLabel(telefono)
        tel_value.setStyleSheet("font-size: 12px;")
        info_layout.addWidget(tel_value, 2, 1)
        
        layout.addLayout(info_layout)
        
        # Botón para seleccionar
        btn_seleccionar = QPushButton("✅ SELECCIONAR ESTE ESTUDIANTE")
        btn_seleccionar.setMinimumHeight(30)
        btn_seleccionar.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
                padding: 0 15px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)
        btn_seleccionar.clicked.connect(lambda checked, eid=estudiante_id: self.seleccionar_estudiante(eid))
        layout.addWidget(btn_seleccionar)
        
        return tarjeta_frame
    
    def seleccionar_estudiante(self, estudiante_id: int):
        """Seleccionar un estudiante de la lista"""
        self.estudiante_id = estudiante_id
        self.actualizar_interfaz_segun_contexto()
        self.cargar_inscripciones()
        self.estudiante_seleccionado.emit(estudiante_id)
    
    # ===== MÉTODOS PARA SELECCIÓN DE PROGRAMA =====
    
    def actualizar_boton_seleccion_programa(self):
        """Actualizar estado del botón de selección de programa"""
        if self.btn_seleccionar_programa and self.programa_combo:
            programa_id = self.programa_combo.currentData()
            self.btn_seleccionar_programa.setEnabled(programa_id is not None)
        else:
            if self.btn_seleccionar_programa:
                self.btn_seleccionar_programa.setEnabled(False)
    
    def seleccionar_programa_desde_combo(self):
        """Seleccionar programa desde el ComboBox"""
        if self.programa_combo:
            try:
                programa_id = self.programa_combo.currentData()
                if programa_id:
                    self.programa_id = programa_id
                    self.actualizar_interfaz_segun_contexto()
                    self.cargar_inscripciones()
                    self.programa_seleccionado.emit(programa_id)
            except Exception as e:
                logger.error(f"Error seleccionando programa: {e}")
                self.mostrar_mensaje("Error", "No se pudo seleccionar el programa", "error")
    
    def cargar_programas_disponibles(self):
        """Cargar programas disponibles para el estudiante"""
        try:
            if not self.estudiante_id or not self.programa_combo:
                return
            
            # Limpiar combobox
            self.programa_combo.clear()
            self.programa_combo.addItem("-- SELECCIONE UN PROGRAMA --", None)
            
            if self.btn_seleccionar_programa:
                self.btn_seleccionar_programa.setEnabled(False)
            
            # Obtener programas en estado activo
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return
            
            cursor = connection.cursor()
            query = """
            SELECT 
                p.id,
                p.codigo,
                p.nombre,
                p.estado,
                p.costo_total,
                p.cupos_maximos,
                p.cupos_inscritos,
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
            WHERE p.estado NOT IN ('CANCELADO', 'CONCLUIDO')
            AND p.estado IN ('PLANIFICADO', 'INSCRIPCIONES', 'EN_CURSO')
            ORDER BY p.estado, p.codigo
            """
            
            cursor.execute(query, (self.estudiante_id,))
            if not cursor:
                logger.warning("No se pudo ejecutar la consulta de programas disponibles")
                self.mostrar_mensaje("Error", "Error al cargar programas disponibles", "error")
                return
            
            resultados = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description] # type: ignore
            
            self.programas_disponibles = []
            
            for row in resultados:
                programa = dict(zip(column_names, row))
                # Solo programas no inscritos y con cupos
                if not programa.get('ya_inscrito', False) and programa.get('tiene_cupos', True):
                    self.programas_disponibles.append(programa)
            
            cursor.close()
            Database.return_connection(connection)
            
            if not self.programas_disponibles:
                self.programa_combo.addItem("⚠️ NO HAY PROGRAMAS DISPONIBLES", None)
                return
            
            # Agregar programas al combobox
            for programa in self.programas_disponibles:
                programa_id = programa.get('id')
                codigo = programa.get('codigo', '')
                nombre = programa.get('nombre', '')
                estado = programa.get('estado', '')
                costo = float(programa.get('costo_total', 0) or 0)
                
                texto = f"{codigo} - {nombre[:30]}{'...' if len(nombre) > 30 else ''} [{estado}] - {costo:.2f} Bs."
                self.programa_combo.addItem(texto, programa_id)
            
            logger.debug(f"✅ Programas disponibles cargados: {len(self.programas_disponibles)}")
            
        except Exception as e:
            logger.error(f"Error cargando programas disponibles: {e}")
            if self.programa_combo:
                self.programa_combo.addItem("❌ ERROR AL CARGAR PROGRAMAS", None)
    
    # ===== MÉTODOS PARA VALOR FINAL =====
    
    def actualizar_observaciones_automaticas(self):
        """Actualizar observaciones automáticamente según valor final"""
        try:
            if not self.valor_final_input or not self.observaciones_input:
                return
            
            valor_final_texto = self.valor_final_input.text().strip()
            if not valor_final_texto:
                return
            
            try:
                valor_final = float(valor_final_texto)
            except ValueError:
                return
            
            # Obtener valor real del programa
            valor_real = 0.0
            if self.programa_id:
                from model.inscripcion_model import InscripcionModel
                valor_real = InscripcionModel.obtener_valor_real_programa(self.programa_id)
            
            # Si el valor final es igual al real
            if abs(valor_final - valor_real) < 0.01:
                self.observaciones_input.setPlainText("No se aplicó ningún descuento")
            # Si el valor final es menor al real
            elif valor_final < valor_real and valor_final > 0:
                porcentaje = ((valor_real - valor_final) / valor_real) * 100
                texto_base = f"Se aplica un descuento de {porcentaje:.2f}% Justificación: "
                # Si ya hay texto, mantener la justificación existente
                texto_actual = self.observaciones_input.toPlainText()
                if texto_actual.startswith("Se aplica un descuento de"):
                    if "Justificación:" in texto_actual:
                        partes = texto_actual.split("Justificación:")
                        if len(partes) > 1:
                            texto_base += partes[1].strip()
                
                self.observaciones_input.setPlainText(texto_base)
            
        except Exception as e:
            logger.error(f"Error actualizando observaciones automáticas: {e}")
    
    def validar_observaciones(self) -> tuple[bool, str]:
        """Validar que las observaciones tengan el formato correcto"""
        try:
            if not self.valor_final_input or not self.observaciones_input:
                return False, "Campos de entrada no disponibles"
            
            valor_final_texto = self.valor_final_input.text().strip()
            if not valor_final_texto:
                return False, "Debe ingresar un valor final"
            
            try:
                valor_final = float(valor_final_texto)
            except ValueError:
                return False, "El valor final debe ser un número válido"
            
            if valor_final <= 0:
                return False, "El valor final debe ser mayor a 0"
            
            # Obtener valor real del programa
            valor_real = 0.0
            if self.programa_id:
                from model.inscripcion_model import InscripcionModel
                valor_real = InscripcionModel.obtener_valor_real_programa(self.programa_id)
            
            if valor_final > valor_real:
                return False, f"El valor final ({valor_final:.2f}) no puede ser mayor al valor real ({valor_real:.2f})"
            
            if not self.observaciones_input:
                return False, "Widget de observaciones no disponible"
            
            if not hasattr(self.observaciones_input, 'toPlainText'):
                return False, "Widget de observaciones no tiene método toPlainText"
            
            observaciones = self.observaciones_input.toPlainText().strip()
            
            # Si no hay descuento
            if abs(valor_final - valor_real) < 0.01:
                esperado = "No se aplicó ningún descuento"
                if esperado not in observaciones:
                    return False, f"Cuando no hay descuento, las observaciones deben contener: '{esperado}'"
                return True, ""
            
            # Si hay descuento
            porcentaje = ((valor_real - valor_final) / valor_real) * 100
            patron_esperado = f"Se aplica un descuento de {porcentaje:.2f}% Justificación:"
            
            if not observaciones.startswith(patron_esperado):
                return False, f"Las observaciones deben comenzar con: '{patron_esperado}'"
            
            # Verificar que haya justificación
            if "Justificación:" in observaciones:
                partes = observaciones.split("Justificación:")
                if len(partes) > 1 and partes[1].strip() == "":
                    return False, "Debe proporcionar una justificación para el descuento"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validando observaciones: {e}")
            return False, f"Error de validación: {str(e)}"
    
    # ===== MÉTODO PARA NUEVA INSCRIPCIÓN =====
    
    def crear_nueva_inscripcion(self):
        """Crear una nueva inscripción con validación de observaciones"""
        try:
            if not self.estudiante_id or not self.programa_id:
                self.mostrar_mensaje("Error", "Falta seleccionar estudiante o programa", "error")
                return
            
            # Validar observaciones
            valido, mensaje_error = self.validar_observaciones()
            if not valido:
                self.mostrar_mensaje("Error", mensaje_error, "error")
                return
            
            # Obtener datos del formulario
            if not self.fecha_inscripcion_input:
                self.mostrar_mensaje("Error", "El widget de fecha no está disponible", "error")
                return
            
            fecha_inscripcion = self.fecha_inscripcion_input.date().toString("yyyy-MM-dd")
            valor_final_texto = self.valor_final_input.text().strip() if self.valor_final_input else "0"
            observaciones = self.observaciones_input.toPlainText().strip() # type: ignore
            
            try:
                valor_final = float(valor_final_texto)
            except ValueError:
                self.mostrar_mensaje("Error", "El valor final debe ser un número válido", "error")
                return
            
            # Crear la inscripción
            from controller.inscripcion_controller import InscripcionController
            
            resultado = InscripcionController.procesar_inscripcion(
                estudiante_id=self.estudiante_id,
                programa_id=self.programa_id,
                valor_final=valor_final,
                observaciones=observaciones,
                es_retroactiva=False
            )
            
            if resultado.get('success'):
                self.inscripcion_id = resultado.get('id')
                self.mostrar_mensaje("Éxito", "Inscripción creada exitosamente", "success")
                self.actualizar_interfaz_segun_contexto()
                self.cargar_inscripciones()
                self.inscripcion_creada.emit(resultado)
            else:
                error_msg = resultado.get('message', 'Error desconocido')
                self.mostrar_mensaje("Error", f"No se pudo crear la inscripción: {error_msg}", "error")
                
        except Exception as e:
            logger.error(f"Error creando inscripción: {e}")
            self.mostrar_mensaje("Error", f"Error al crear inscripción: {str(e)}", "error")
    
    # ==== MÉTODOS PARA ACTUALIZAR INSCRIPCIÓN =====
    
    def actualizar_inscripcion(self, inscripcion_id: int, nuevas_observaciones: str):
        """Actualizar observaciones de una inscripción existente"""
        try:
            from controller.inscripcion_controller import InscripcionController
            
            resultado = InscripcionController.actualizar_inscripcion(
                inscripcion_id=inscripcion_id,
                nuevas_observaciones=nuevas_observaciones
            )
            
            if resultado.get('success'):
                self.mostrar_mensaje("Éxito", "Justificación guardada correctamente", "success")
                QTimer.singleShot(500, self.cargar_inscripciones)
            else:
                error_msg = resultado.get('message', 'Error desconocido')
                self.mostrar_mensaje("Error", f"No se pudo guardar: {error_msg}", "error")
                
        except Exception as e:
            logger.error(f"Error actualizando inscripción: {e}")
            self.mostrar_mensaje("Error", f"Error al actualizar: {str(e)}", "error")
    
    # ===== MÉTODOS PRINCIPALES DE GESTIÓN =====
    
    def actualizar_interfaz_segun_contexto(self):
        """Actualizar la interfaz según el contexto actual"""
        try:
            logger.debug(f"🔄 Actualizando interfaz - Est: {self.estudiante_id}, Prog: {self.programa_id}")

            # Actualizar etiquetas de información
            if self.estudiante_id:
                self.actualizar_info_estudiante()
            elif self.estudiante_id_label:
                self.estudiante_id_label.setText("NO ESPECIFICADO")

            if self.programa_id:
                self.actualizar_info_programa()
            elif self.programa_id_label:
                self.programa_id_label.setText("NO ESPECIFICADO")

            # Determinar qué secciones mostrar según el contexto
            # CASO 1: Si NO hay estudiante_id -> Mostrar selector de estudiante
            mostrar_seleccion_estudiante = (self.estudiante_id is None)

            # CASO 2: Si HAY estudiante_id pero NO hay programa_id -> Mostrar selector de programa
            if self.estudiante_id and not self.programa_id:
                mostrar_seleccion_programa = True
            else:
                mostrar_seleccion_programa = False

            # CASO 3: Si AMBOS IDs existen -> Verificar si hay inscripción
            existe_inscripcion = False
            mostrar_nueva_inscripcion = False

            if self.estudiante_id and self.programa_id:
                existe_inscripcion = self.verificar_existe_inscripcion()
                logger.debug(f"📊 Verificación de inscripción: existe={existe_inscripcion}")
                # Mostrar nueva inscripción solo si NO existe
                mostrar_nueva_inscripcion = not existe_inscripcion
                logger.debug(f"📊 Mostrar nueva inscripción: {mostrar_nueva_inscripcion}")

            # Mostrar/ocultar secciones
            if self.seleccion_estudiante_frame:
                self.seleccion_estudiante_frame.setVisible(mostrar_seleccion_estudiante)
                logger.debug(f"📌 Selección estudiante visible: {mostrar_seleccion_estudiante}")
                if mostrar_seleccion_estudiante and self.busqueda_estudiante_input:
                    self.busqueda_estudiante_input.setFocus()

            if self.seleccion_programa_frame:
                self.seleccion_programa_frame.setVisible(mostrar_seleccion_programa)
                logger.debug(f"📌 Selección programa visible: {mostrar_seleccion_programa}")
                if mostrar_seleccion_programa:
                    QTimer.singleShot(100, self.cargar_programas_disponibles)

            if self.nueva_inscripcion_frame:
                self.nueva_inscripcion_frame.setVisible(mostrar_nueva_inscripcion)
                logger.debug(f"📌 Nueva inscripción visible: {mostrar_nueva_inscripcion}")
                # Si se muestra el formulario, asegurar que el valor final esté sugerido
                if mostrar_nueva_inscripcion and self.valor_final_input:
                    # Disparar actualización de observaciones si hay valor
                    QTimer.singleShot(200, self.actualizar_observaciones_automaticas)

            if self.nueva_inscripcion_frame and mostrar_nueva_inscripcion:
                logger.debug(f"🔍 DEBUG - Frame nueva inscripción: visible={self.nueva_inscripcion_frame.isVisible()}, "
                            f"geometry={self.nueva_inscripcion_frame.geometry()}, "
                            f"size={self.nueva_inscripcion_frame.size()}")
                
                # Forzar actualización del layout
                self.nueva_inscripcion_frame.update()
                self.nueva_inscripcion_frame.repaint()
                
                # Verificar que los widgets hijos también sean visibles
                if self.fecha_inscripcion_input:
                    logger.debug(f"🔍 DEBUG - fecha_input visible: {self.fecha_inscripcion_input.isVisible()}")
                if self.valor_real_display:
                    logger.debug(f"🔍 DEBUG - valor_real visible: {self.valor_real_display.isVisible()}")
                if self.valor_final_input:
                    logger.debug(f"🔍 DEBUG - valor_final visible: {self.valor_final_input.isVisible()}")
                if self.observaciones_input:
                    logger.debug(f"🔍 DEBUG - observaciones visible: {self.observaciones_input.isVisible()}")
                if self.btn_crear_inscripcion:
                    logger.debug(f"🔍 DEBUG - btn_crear visible: {self.btn_crear_inscripcion.isVisible()}")

            logger.debug(f"✅ Interfaz actualizada - SelEst: {mostrar_seleccion_estudiante}, " 
                        f"SelProg: {mostrar_seleccion_programa}, Nueva: {mostrar_nueva_inscripcion}")

        except Exception as e:
            logger.error(f"Error actualizando interfaz: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def verificar_existe_inscripcion(self) -> bool:
        """Verificar si existe una inscripción para el estudiante y programa actual"""
        try:
            if not self.estudiante_id or not self.programa_id:
                return False
            
            inscripciones = InscripcionModel.obtener_programas_inscritos_estudiante(self.estudiante_id)
            
            for inscripcion in inscripciones:
                if inscripcion.get('programa_id') == self.programa_id:
                    self.inscripcion_id = inscripcion.get('id')
                    return True
            
            self.inscripcion_id = None
            return False
            
        except Exception as e:
            logger.error(f"Error verificando inscripción: {e}")
            return False
    
    def actualizar_info_estudiante(self):
        """Actualizar información del estudiante en la etiqueta"""
        try:
            if not self.estudiante_id:
                logger.error(f"Error pues no se encuentra Estudiante: {self.estudiante_id}")
                return
            
            estudiante = EstudianteModel.buscar_estudiante_id(self.estudiante_id)
            if estudiante:
                nombre = f"{estudiante.get('apellido_paterno', '')} {estudiante.get('apellido_materno', '')} {estudiante.get('nombres', '')}"
                ci_num = estudiante.get('ci_numero', '')
                ci_exp = estudiante.get('ci_expedicion', '')
                ci_completo = f"{ci_num}-{ci_exp}" if ci_num and ci_exp else "Sin CI"
                self.estudiante_id_label.setText(f"{self.estudiante_id} - {nombre.strip()} ({ci_completo})")  # type: ignore
            else:
                self.estudiante_id_label.setText(f"ID: {self.estudiante_id} (NO ENCONTRADO)")  # type: ignore
        except Exception as e:
            logger.error(f"Error actualizando info estudiante: {e}")
            self.estudiante_id_label.setText(f"ID: {self.estudiante_id}")  # type: ignore
    
    def actualizar_info_programa(self):
        """Actualizar información del programa en la etiqueta y valor real"""
        try:
            if not self.programa_id:
                if self.programa_id_label:
                    self.programa_id_label.setText("NO ESPECIFICADO")
                return
            
            # Intentar obtener del modelo primero
            resultado = ProgramaModel.obtener_programa(self.programa_id)
            
            if resultado.get('success') and resultado.get('data'):
                programa = resultado['data']
                codigo = programa.get('codigo', '')
                nombre = programa.get('nombre', '')
                costo = float(programa.get('costo_total', 0) or 0)
                
                texto = f"{self.programa_id} - {codigo} - {nombre} ({costo:.2f} Bs.)"
                if self.programa_id_label:
                    self.programa_id_label.setText(texto)
                
                # Actualizar valor real display
                if self.valor_real_display:
                    self.valor_real_display.setText(f"{costo:.2f} Bs.")
                    
                # Sugerir valor final igual al real
                if self.valor_final_input:
                    self.valor_final_input.setText(f"{costo:.2f}")
            else:
                # Si falla el modelo, intentar consulta directa
                from config.database import Database
                connection = Database.get_connection()
                if connection:
                    cursor = connection.cursor()
                    query = "SELECT id, codigo, nombre, costo_total FROM programas WHERE id = %s"
                    cursor.execute(query, (self.programa_id,))
                    resultado = cursor.fetchone()
                    
                    if resultado:
                        id_prog, codigo, nombre, costo = resultado
                        texto = f"{id_prog} - {codigo} - {nombre} ({float(costo or 0):.2f} Bs.)"
                        if self.programa_id_label:
                            self.programa_id_label.setText(texto)
                        
                        if self.valor_real_display:
                            self.valor_real_display.setText(f"{float(costo or 0):.2f} Bs.")
                        
                        if self.valor_final_input:
                            self.valor_final_input.setText(f"{float(costo or 0):.2f}")
                    else:
                        if self.programa_id_label:
                            self.programa_id_label.setText(f"ID: {self.programa_id} (NO ENCONTRADO)")
                            
                    cursor.close()
                    Database.return_connection(connection)
                else:
                    if self.programa_id_label:
                        self.programa_id_label.setText(f"ID: {self.programa_id}")
                        
        except Exception as e:
            logger.error(f"Error actualizando info programa: {e}")
            if self.programa_id_label:
                self.programa_id_label.setText(f"ID: {self.programa_id}")
    
    def cargar_inscripciones(self):
        """Cargar las inscripciones relacionadas según el contexto"""
        try:
            logger.debug(f"🔍 Cargando inscripciones - Est: {self.estudiante_id}, Prog: {self.programa_id}")
            
            # Limpiar contenedor
            if self.inscripciones_layout:
                while self.inscripciones_layout.count():
                    child = self.inscripciones_layout.takeAt(0)
                    widget = child.widget()
                    if widget:
                        widget.deleteLater()
            
            self.inscripciones = []
            
            # Actualizar interfaz según contexto
            self.actualizar_interfaz_segun_contexto()
            
            # Si no hay estudiante_id y no hay programa_id, mostrar mensaje
            if not self.estudiante_id and not self.programa_id:
                self.mostrar_mensaje_no_datos("Seleccione un estudiante o programa para ver inscripciones")
                return
            
            # Determinar qué consulta hacer
            inscripciones = []
            
            if self.estudiante_id and self.programa_id:
                # Caso 1: Ambos IDs - buscar inscripción específica
                logger.debug("🔍 Buscando inscripción específica estudiante-programa")
                todas_inscripciones = InscripcionModel.obtener_programas_inscritos_estudiante(self.estudiante_id)
                if todas_inscripciones:
                    inscripciones = [insc for insc in todas_inscripciones 
                                    if insc.get('programa_id') == self.programa_id]
                    logger.debug(f"✅ Encontradas {len(inscripciones)} inscripciones específicas")
                    
            elif self.estudiante_id:
                # Caso 2: Solo estudiante - todas sus inscripciones
                logger.debug("🔍 Buscando todas las inscripciones del estudiante")
                inscripciones = InscripcionModel.obtener_programas_inscritos_estudiante(self.estudiante_id)
                if inscripciones:
                    logger.debug(f"✅ Encontradas {len(inscripciones)} inscripciones del estudiante")
                    
            elif self.programa_id:
                # Caso 3: Solo programa - todos los estudiantes inscritos
                logger.debug("🔍 Buscando todas las inscripciones del programa")
                from config.database import Database
                connection = Database.get_connection()
                if connection:
                    cursor = connection.cursor()
                    
                    query = """
                    SELECT 
                        i.id,
                        i.estudiante_id,
                        i.programa_id,
                        i.fecha_inscripcion,
                        i.estado,
                        i.valor_final,
                        i.observaciones,
                        CONCAT(e.apellido_paterno, ' ', e.apellido_materno, ' ', e.nombres) as estudiante_nombre,
                        e.ci_numero,
                        e.ci_expedicion,
                        p.codigo as programa_codigo,
                        p.nombre as programa_nombre,
                        p.costo_total,
                        p.costo_matricula,
                        p.costo_inscripcion,
                        p.costo_mensualidad,
                        p.numero_cuotas
                    FROM inscripciones i
                    JOIN estudiantes e ON i.estudiante_id = e.id
                    JOIN programas p ON i.programa_id = p.id
                    WHERE i.programa_id = %s AND i.estado != 'RETIRADO'
                    ORDER BY i.fecha_inscripcion DESC
                    """
                    cursor.execute(query, (self.programa_id,))
                    if not cursor:
                        logger.warning("No se pudo ejecutar la consulta de inscripciones por programa")
                        self.mostrar_mensaje("Error", "Error al cargar inscripciones del programa", "error")
                        return
                    
                    resultados = cursor.fetchall()
                    
                    if resultados:
                        column_names = [desc[0] for desc in cursor.description] # type: ignore
                        for row in resultados:
                            inscripcion = dict(zip(column_names, row))
                            inscripciones.append(inscripcion)
                        logger.debug(f"✅ Encontradas {len(inscripciones)} inscripciones del programa")
                    
                    cursor.close()
                    Database.return_connection(connection)
            
            # Validar que todas las inscripciones tengan ID válido
            inscripciones_validas = []
            for inscripcion in inscripciones:
                insc_id = inscripcion.get('id')
                if insc_id and insc_id != '' and insc_id != 'None':
                    inscripciones_validas.append(inscripcion)
                else:
                    logger.warning(f"Inscripción sin ID válido: {inscripcion}")
                    
            self.inscripciones = inscripciones_validas
            
            # Mostrar resultados
            if not inscripciones:
                self.mostrar_mensaje_no_datos("No hay inscripciones relacionadas")
                return
            
            # Crear tarjetas para cada inscripción
            logger.debug(f"🎨 Creando {len(inscripciones)} tarjetas de inscripción")
            for inscripcion in inscripciones:
                tarjeta = self.crear_tarjeta_inscripcion(inscripcion)
                if tarjeta and self.inscripciones_layout:
                    self.inscripciones_layout.addWidget(tarjeta)
            
            logger.debug(f"✅ Inscripciones cargadas exitosamente: {len(inscripciones)}")
            
        except Exception as e:
            logger.error(f"❌ Error crítico cargando inscripciones: {e}")
            self.mostrar_mensaje_no_datos(f"Error al cargar inscripciones: {str(e)}")
    
    def mostrar_mensaje_no_datos(self, mensaje: str):
        """Mostrar mensaje cuando no hay datos"""
        try:
            if not self.inscripciones_layout:
                return
            
            no_data_frame = QFrame()
            no_data_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border: 2px dashed #bdc3c7;
                    border-radius: 8px;
                    padding: 30px;
                }
            """)
            
            no_data_layout = QVBoxLayout(no_data_frame)
            no_data_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            icon_label = QLabel("📭")
            icon_label.setStyleSheet("font-size: 40px;")
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data_layout.addWidget(icon_label)
            
            message_label = QLabel(mensaje)
            message_label.setStyleSheet("""
                color: #7f8c8d;
                font-size: 14px;
                font-weight: bold;
                text-align: center;
            """)
            no_data_layout.addWidget(message_label)
            
            self.inscripciones_layout.addWidget(no_data_frame)
            
        except Exception as e:
            logger.error(f"Error mostrando mensaje de no datos: {e}")
    
    # ===== MÉTODO PARA CREAR TARJETA DE INSCRIPCIÓN =====
    
    def crear_tarjeta_inscripcion(self, inscripcion: Dict) -> Optional[QFrame]:
        """Crear una tarjeta para mostrar una inscripción (actualizado para valor_final)"""
        try:
            # Validar que la inscripción tenga ID válido
            inscripcion_id = inscripcion.get('id')
            if not inscripcion_id or inscripcion_id == '' or inscripcion_id == 'None':
                logger.error(f"Inscripción sin ID válido: {inscripcion}")
                return None

            # Frame principal de la tarjeta
            tarjeta_frame = QFrame()
            tarjeta_frame.setObjectName("tarjetaInscripcion")
            tarjeta_frame.setStyleSheet("""
                #tarjetaInscripcion {
                    background-color: white;
                    border: 2px solid #3498db;
                    border-radius: 10px;
                    margin: 8px 5px;
                }
            """)

            # Layout principal
            main_layout = QVBoxLayout(tarjeta_frame)
            main_layout.setSpacing(12)
            main_layout.setContentsMargins(20, 15, 20, 15)

            # ===== ENCABEZADO =====
            header_frame = QFrame()
            header_frame.setStyleSheet("""
                QFrame {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #e3f2fd, stop:1 #bbdefb);
                    border-radius: 6px;
                    padding: 0px;
                }
            """)

            header_layout = QGridLayout(header_frame)
            header_layout.setSpacing(12)
            header_layout.setContentsMargins(15, 10, 15, 10)

            # Título de la inscripción
            titulo_label = QLabel(f"📋 INSCRIPCIÓN ID: {inscripcion_id}")
            titulo_label.setStyleSheet("""
                font-weight: bold;
                font-size: 16px;
                color: #2c3e50;
            """)
            header_layout.addWidget(titulo_label, 0, 0, 1, 4)

            # Información del estudiante
            estudiante_id = inscripcion.get('estudiante_id', '')
            estudiante_nombre = inscripcion.get('estudiante_nombre', '')
            ci_numero = inscripcion.get('ci_numero', '')
            ci_expedicion = inscripcion.get('ci_expedicion', '')

            est_label = QLabel("👤 ESTUDIANTE:")
            est_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            header_layout.addWidget(est_label, 1, 0)

            est_info = QLabel(f"{estudiante_id} - {estudiante_nombre} ({ci_numero}-{ci_expedicion})")
            est_info.setStyleSheet("font-size: 13px; padding: 6px; background-color: white; border-radius: 4px;")
            est_info.setWordWrap(True)
            header_layout.addWidget(est_info, 1, 1)

            # Información del programa
            programa_id = inscripcion.get('programa_id', '')
            programa_codigo = inscripcion.get('programa_codigo', '')
            programa_nombre = inscripcion.get('programa_nombre', '')

            prog_label = QLabel("📚 PROGRAMA:")
            prog_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            header_layout.addWidget(prog_label, 1, 2)

            prog_info = QLabel(f"{programa_id} - {programa_codigo} - {programa_nombre[:30]}{'...' if len(programa_nombre) > 30 else ''}")
            prog_info.setStyleSheet("font-size: 13px; padding: 6px; background-color: white; border-radius: 4px;")
            prog_info.setWordWrap(True)
            header_layout.addWidget(prog_info, 1, 3)

            main_layout.addWidget(header_frame)

            # ===== INFORMACIÓN DE LA INSCRIPCIÓN =====
            info_frame = QFrame()
            info_frame.setStyleSheet("""
                QFrame {
                    background-color: #f8f9fa;
                    border-radius: 6px;
                    padding: 0px;
                }
            """)

            info_layout = QGridLayout(info_frame)
            info_layout.setSpacing(10)
            info_layout.setContentsMargins(15, 12, 15, 12)

            # Fecha de inscripción
            fecha_insc = inscripcion.get('fecha_inscripcion', '')
            fecha_formateada = ""
            if fecha_insc:
                try:
                    if isinstance(fecha_insc, str):
                        fecha_formateada = datetime.strptime(fecha_insc[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
                    else:
                        fecha_formateada = fecha_insc.strftime('%d/%m/%Y')
                except:
                    fecha_formateada = str(fecha_insc)[:10]

            fecha_label = QLabel("📅 FECHA INSCRIPCIÓN:")
            fecha_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            info_layout.addWidget(fecha_label, 0, 0)

            fecha_info = QLabel(fecha_formateada)
            fecha_info.setStyleSheet("font-size: 13px; padding: 6px; background-color: white; border-radius: 4px;")
            info_layout.addWidget(fecha_info, 0, 1)

            # Valor Real
            valor_real = float(inscripcion.get('costo_total', 0) or 0)
            valor_real_label = QLabel("💰 VALOR REAL:")
            valor_real_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            info_layout.addWidget(valor_real_label, 0, 2)

            valor_real_info = QLabel(f"{valor_real:.2f} Bs.")
            valor_real_info.setStyleSheet("""
                font-size: 13px;
                padding: 6px;
                background-color: white;
                border-radius: 4px;
            """)
            info_layout.addWidget(valor_real_info, 0, 3)

            # Valor Final
            valor_final = float(inscripcion.get('valor_final', valor_real) or valor_real)
            valor_final_label = QLabel("💵 VALOR FINAL:")
            valor_final_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            info_layout.addWidget(valor_final_label, 1, 0)

            # Determinar si hay descuento para colorear
            hay_descuento = valor_final < valor_real - 0.01
            color_valor = "#e74c3c" if hay_descuento else "#27ae60"

            valor_final_info = QLabel(f"{valor_final:.2f} Bs.")
            valor_final_info.setStyleSheet(f"""
                font-size: 14px;
                font-weight: bold;
                color: {color_valor};
                padding: 6px;
                background-color: white;
                border-radius: 4px;
            """)
            info_layout.addWidget(valor_final_info, 1, 1)

            # Descuento implícito
            if hay_descuento and valor_real > 0:
                porcentaje = ((valor_real - valor_final) / valor_real) * 100
                descuento_label = QLabel("📉 DESCUENTO:")
                descuento_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
                info_layout.addWidget(descuento_label, 1, 2)

                descuento_info = QLabel(f"{porcentaje:.2f}%")
                descuento_info.setStyleSheet("""
                    font-size: 13px;
                    font-weight: bold;
                    color: #e67e22;
                    padding: 6px;
                    background-color: white;
                    border-radius: 4px;
                """)
                info_layout.addWidget(descuento_info, 1, 3)

            # Estado
            estado = inscripcion.get('estado', '')
            estado_label = QLabel("📊 ESTADO:")
            estado_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            info_layout.addWidget(estado_label, 2, 0)

            estado_combo = QComboBox()
            estados = ["PREINSCRITO", "INSCRITO", "EN_CURSO", "CONCLUIDO", "RETIRADO"]
            estado_combo.addItems(estados)

            index = estado_combo.findText(estado)
            if index >= 0:
                estado_combo.setCurrentIndex(index)

            estado_colors = {
                "PREINSCRITO": "#f39c12",
                "INSCRITO": "#3498db",
                "EN_CURSO": "#27ae60",
                "CONCLUIDO": "#9b59b6",
                "RETIRADO": "#e74c3c"
            }
            color = estado_colors.get(estado, "#7f8c8d")

            estado_combo.setStyleSheet(f"""
                QComboBox {{
                    font-size: 13px;
                    padding: 6px;
                    background-color: white;
                    border: 1px solid {color};
                    border-radius: 4px;
                    font-weight: bold;
                    color: {color};
                }}
                QComboBox::drop-down {{
                    border: none;
                }}
            """)
            estado_combo.setEnabled(False)
            info_layout.addWidget(estado_combo, 2, 1)

            # Observaciones
            observaciones = inscripcion.get('observaciones', '') or ''
            obs_label = QLabel("📝 OBSERVACIONES:")
            obs_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 12px;")
            info_layout.addWidget(obs_label, 2, 2)

            if hay_descuento and "Justificación:" in observaciones:
                partes = observaciones.split("Justificación:")
                if len(partes) > 1 and partes[1].strip() == "":
                    obs_edit = QTextEdit()
                    obs_edit.setPlainText(observaciones)
                    obs_edit.setMaximumHeight(60)
                    obs_edit.setStyleSheet("""
                        QTextEdit {
                            font-size: 12px;
                            padding: 4px;
                            background-color: #fff3cd;
                            border: 2px solid #ffc107;
                            border-radius: 4px;
                        }
                    """)

                    def guardar_justificacion(iid=inscripcion_id, obs_widget=obs_edit):
                        nuevas_obs = obs_widget.toPlainText().strip()
                        if "Justificación:" in nuevas_obs:
                            partes = nuevas_obs.split("Justificación:")
                            if len(partes) > 1 and partes[1].strip() != "":
                                self.actualizar_inscripcion(iid, nuevas_obs)

                    btn_guardar = QPushButton("💾 GUARDAR JUSTIFICACIÓN")
                    btn_guardar.setMinimumHeight(25)
                    btn_guardar.setStyleSheet("""
                        QPushButton {
                            background-color: #ffc107;
                            color: #2c3e50;
                            border: none;
                            border-radius: 4px;
                            font-weight: bold;
                            font-size: 10px;
                            padding: 4px 8px;
                        }
                        QPushButton:hover {
                            background-color: #e0a800;
                        }
                    """)
                    btn_guardar.clicked.connect(guardar_justificacion)

                    obs_container = QVBoxLayout()
                    obs_container.addWidget(obs_edit)
                    obs_container.addWidget(btn_guardar)

                    obs_widget_container = QWidget()
                    obs_widget_container.setLayout(obs_container)
                    info_layout.addWidget(obs_widget_container, 2, 3)
                else:
                    obs_info = QLineEdit(observaciones)
                    obs_info.setReadOnly(True)
                    obs_info.setStyleSheet("""
                        QLineEdit {
                            font-size: 12px;
                            padding: 4px;
                            background-color: white;
                            border: 1px solid #bdc3c7;
                            border-radius: 4px;
                        }
                    """)
                    info_layout.addWidget(obs_info, 2, 3)
            else:
                obs_info = QLineEdit(observaciones)
                obs_info.setReadOnly(True)
                obs_info.setStyleSheet("""
                    QLineEdit {
                        font-size: 12px;
                        padding: 4px;
                        background-color: white;
                        border: 1px solid #bdc3c7;
                        border-radius: 4px;
                    }
                """)
                info_layout.addWidget(obs_info, 2, 3)

            main_layout.addWidget(info_frame)

            # ===== TRANSACCIONES =====
            transacciones = []
            try:
                estudiante_id_tx = inscripcion.get('estudiante_id')
                programa_id_tx = inscripcion.get('programa_id')

                if estudiante_id_tx and programa_id_tx:
                    logger.debug(f"Buscando transacciones para estudiante={estudiante_id_tx}, programa={programa_id_tx}")
                    resultado_tx = TransaccionModel.obtener_por_inscripcion(
                        estudiante_id=estudiante_id_tx,
                        programa_id=programa_id_tx
                    )
                    if resultado_tx.get('success'):
                        transacciones = resultado_tx.get('data', [])
                        logger.info(f"✅ Encontradas {len(transacciones)} transacciones")
                    else:
                        logger.warning(f"Error obteniendo transacciones: {resultado_tx.get('error')}")
                else:
                    logger.warning(f"Inscripción sin estudiante_id o programa_id: est={estudiante_id_tx}, prog={programa_id_tx}")

            except Exception as e:
                logger.error(f"Error obteniendo transacciones: {e}")

            if transacciones:
                trans_header = QLabel("💳 TRANSACCIONES")
                trans_header.setStyleSheet("""
                    font-weight: bold;
                    font-size: 14px;
                    color: #2c3e50;
                    padding: 8px 0px;
                    border-bottom: 2px solid #27ae60;
                    margin-top: 5px;
                """)
                main_layout.addWidget(trans_header)

                trans_frame = QFrame()
                trans_frame.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border: 1px solid #ddd;
                        border-radius: 6px;
                        padding: 0px;
                    }
                """)

                trans_layout = QVBoxLayout(trans_frame)
                trans_layout.setContentsMargins(0, 0, 0, 0)
                trans_layout.setSpacing(0)

                # Header de la tabla
                header_widget = QWidget()
                header_widget.setStyleSheet("""
                    QWidget {
                        background-color: #2c3e50;
                        border-top-left-radius: 6px;
                        border-top-right-radius: 6px;
                    }
                """)

                header_layout_table = QHBoxLayout(header_widget)
                header_layout_table.setContentsMargins(12, 8, 12, 8)
                header_layout_table.setSpacing(0)

                headers = ["N° TRANSACCIÓN", "FECHA PAGO", "MONTO", "SALDO", ""]
                widths = [140, 100, 100, 100, 40]

                for i, header in enumerate(headers):
                    label = QLabel(header)
                    label.setStyleSheet("""
                        color: white;
                        font-weight: bold;
                        font-size: 11px;
                        padding: 4px;
                    """)
                    label.setFixedWidth(widths[i])
                    header_layout_table.addWidget(label)

                header_layout_table.addStretch()
                trans_layout.addWidget(header_widget)

                # Filas de transacciones
                saldo_acumulado = valor_final

                for j, transaccion in enumerate(transacciones):
                    if isinstance(transaccion, str):
                        logger.warning(f"Transacción recibida como string: {transaccion}")
                        continue
                    if not isinstance(transaccion, dict):
                        transaccion = dict(transaccion) if hasattr(transaccion, '__iter__') else {}

                    row_widget = QWidget()
                    row_widget.setStyleSheet("""
                        QWidget {
                            background-color: %s;
                            border-bottom: 1px solid #ecf0f1;
                        }
                    """ % ("#f8f9fa" if j % 2 == 0 else "white"))

                    row_layout = QHBoxLayout(row_widget)
                    row_layout.setContentsMargins(12, 8, 12, 8)
                    row_layout.setSpacing(0)

                    # Número de transacción
                    num_trans = transaccion.get('numero_transaccion', f"INS-{inscripcion_id}-T{j+1:02d}")
                    num_label = QLabel(num_trans)
                    num_label.setFixedWidth(140)
                    num_label.setStyleSheet("font-size: 11px;")
                    row_layout.addWidget(num_label)

                    # Fecha de pago
                    fecha_pago = transaccion.get('fecha_pago', '')
                    fecha_pago_formateada = ""
                    if fecha_pago:
                        try:
                            if isinstance(fecha_pago, str):
                                fecha_pago_formateada = datetime.strptime(fecha_pago[:10], '%Y-%m-%d').strftime('%d/%m/%Y')
                            else:
                                fecha_pago_formateada = fecha_pago.strftime('%d/%m/%Y')
                        except:
                            fecha_pago_formateada = str(fecha_pago)[:10]

                    fecha_label_row = QLabel(fecha_pago_formateada)
                    fecha_label_row.setFixedWidth(100)
                    fecha_label_row.setStyleSheet("font-size: 11px;")
                    row_layout.addWidget(fecha_label_row)

                    # Monto de transacción
                    monto_trans = float(transaccion.get('monto_final', 0) or 0)
                    monto_label_row = QLabel(f"{monto_trans:.2f} Bs.")
                    monto_label_row.setFixedWidth(100)
                    monto_label_row.setStyleSheet("""
                        font-size: 11px;
                        font-weight: bold;
                        color: #27ae60;
                    """)
                    row_layout.addWidget(monto_label_row)

                    # Saldo después de esta transacción
                    saldo_acumulado -= monto_trans
                    saldo_label_row = QLabel(f"{max(0, saldo_acumulado):.2f} Bs.")
                    saldo_label_row.setFixedWidth(100)
                    saldo_label_row.setStyleSheet("""
                        font-size: 11px;
                        font-weight: bold;
                        color: %s;
                    """ % ("#27ae60" if saldo_acumulado <= 0 else "#e74c3c"))
                    row_layout.addWidget(saldo_label_row)

                    # ===== BOTONES SEGÚN ESTADO =====
                    transaccion_id = transaccion.get('id')

                    if transaccion_id:
                        # Determinar si la transacción está finalizada (puedes ajustar esta condición)
                        # Por ejemplo, si ya tiene detalles o si su estado es diferente de REGISTRADO
                        estado_trans = transaccion.get('estado', 'REGISTRADO')
                        esta_finalizada = estado_trans in ['CONFIRMADO', 'COMPLETADO', 'ANULADO'] or monto_trans > 0

                        if esta_finalizada:
                            # Botón VER para transacciones finalizadas
                            btn_ver = QPushButton("👁️")
                            btn_ver.setFixedSize(30, 25)
                            btn_ver.setToolTip("Ver transacción")
                            btn_ver.setStyleSheet("""
                                QPushButton {
                                    background-color: #3498db;
                                    color: white;
                                    border: none;
                                    border-radius: 4px;
                                    font-weight: bold;
                                    font-size: 12px;
                                }
                                QPushButton:hover {
                                    background-color: #2980b9;
                                }
                            """)
                            btn_ver.clicked.connect(
                                lambda checked, 
                                tid=transaccion_id,
                                iid=inscripcion_id,
                                est=inscripcion.get('estudiante_id'),
                                prog=inscripcion.get('programa_id'): 
                                self.ver_transaccion(tid, iid, est, prog) # type: ignore
                            )
                            row_layout.addWidget(btn_ver)
                        else:
                            # Botón EDITAR para transacciones en edición
                            btn_editar = QPushButton("✏️")
                            btn_editar.setFixedSize(30, 25)
                            btn_editar.setToolTip("Editar transacción")
                            btn_editar.setStyleSheet("""
                                QPushButton {
                                    background-color: #27ae60;
                                    color: white;
                                    border: none;
                                    border-radius: 4px;
                                    font-weight: bold;
                                    font-size: 12px;
                                }
                                QPushButton:hover {
                                    background-color: #219653;
                                }
                            """)
                            btn_editar.clicked.connect(
                                lambda checked, 
                                tid=transaccion_id,
                                iid=inscripcion_id,
                                est=inscripcion.get('estudiante_id'),
                                prog=inscripcion.get('programa_id'): 
                                self.editar_transaccion(tid, iid, est, prog) # type: ignore
                            )
                            row_layout.addWidget(btn_editar)

                    row_layout.addStretch()
                    trans_layout.addWidget(row_widget)

                main_layout.addWidget(trans_frame)

                # Mostrar saldo final
                saldo_final = max(0, saldo_acumulado)
                saldo_frame = QFrame()
                saldo_frame.setStyleSheet("""
                    QFrame {
                        background-color: %s;
                        border-radius: 6px;
                        padding: 10px;
                        margin-top: 8px;
                    }
                """ % ("#eafaf1" if saldo_final == 0 else "#fdedec"))

                saldo_layout = QHBoxLayout(saldo_frame)

                saldo_text = QLabel("💰 SALDO FINAL:")
                saldo_text.setStyleSheet("font-weight: bold; font-size: 13px;")
                saldo_layout.addWidget(saldo_text)

                saldo_valor = QLabel(f"{saldo_final:.2f} Bs.")
                saldo_valor.setStyleSheet("""
                    font-weight: bold;
                    font-size: 15px;
                    color: %s;
                """ % ("#27ae60" if saldo_final == 0 else "#e74c3c"))
                saldo_layout.addWidget(saldo_valor)

                saldo_layout.addStretch()
                main_layout.addWidget(saldo_frame)

                # Botón para agregar transacción (solo si hay saldo pendiente)
                if saldo_final > 0:
                    btn_agregar = QPushButton("➕ AGREGAR TRANSACCIÓN")
                    btn_agregar.setMinimumHeight(35)
                    btn_agregar.setStyleSheet("""
                        QPushButton {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #27ae60, stop:1 #219653);
                            color: white;
                            border: none;
                            border-radius: 6px;
                            font-weight: bold;
                            font-size: 12px;
                            padding: 0 20px;
                            min-height: 35px;
                            margin-top: 8px;
                        }
                        QPushButton:hover {
                            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                stop:0 #219653, stop:1 #1e8449);
                        }
                    """)
                    btn_agregar.clicked.connect(lambda checked, iid=inscripcion_id: self.agregar_transaccion(iid))
                    main_layout.addWidget(btn_agregar)
            else:
                # Mostrar mensaje si no hay transacciones
                no_trans_frame = QFrame()
                no_trans_frame.setStyleSheet("""
                    QFrame {
                        background-color: #f8f9fa;
                        border: 2px dashed #bdc3c7;
                        border-radius: 6px;
                        padding: 20px;
                        margin-top: 5px;
                    }
                """)

                no_trans_layout = QVBoxLayout(no_trans_frame)
                no_trans_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                no_trans_label = QLabel("📭 No hay transacciones registradas")
                no_trans_label.setStyleSheet("""
                    color: #7f8c8d;
                    font-size: 13px;
                    font-style: italic;
                """)
                no_trans_layout.addWidget(no_trans_label)

                btn_agregar = QPushButton("➕ AGREGAR PRIMERA TRANSACCIÓN")
                btn_agregar.setMinimumHeight(35)
                btn_agregar.setStyleSheet("""
                    QPushButton {
                        background-color: #3498db;
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-weight: bold;
                        padding: 0 15px;
                        font-size: 12px;
                        margin-top: 10px;
                        min-height: 35px;
                    }
                    QPushButton:hover {
                        background-color: #2980b9;
                    }
                """)
                btn_agregar.clicked.connect(lambda checked, iid=inscripcion_id: self.agregar_transaccion(iid))
                no_trans_layout.addWidget(btn_agregar)

                main_layout.addWidget(no_trans_frame)

            # Ajustar ancho de la tarjeta
            tarjeta_frame.setMaximumWidth(int(self.width() * 0.9))

            return tarjeta_frame

        except Exception as e:
            logger.error(f"Error creando tarjeta de inscripción: {e}")
            return None
    
    def ver_transaccion(self, transaccion_id: int, inscripcion_id: int, 
                        estudiante_id: int, programa_id: int):
        """
        Abrir TransaccionOverlay en modo visualización para una transacción específica

        Args:
            transaccion_id: ID de la transacción a visualizar
            inscripcion_id: ID de la inscripción relacionada
            estudiante_id: ID del estudiante
            programa_id: ID del programa
        """
        try:
            logger.info(f"👁️ Visualizando transacción ID: {transaccion_id} para inscripción {inscripcion_id}")

            from view.overlays.transaccion_overlay import TransaccionOverlay

            # Crear overlay en modo visualización
            transaccion_overlay = TransaccionOverlay(
                self.window(),
                inscripcion_id=inscripcion_id,
                estudiante_id=estudiante_id,
                programa_id=programa_id,
                modo="visualizar"  # Nuevo modo
            )

            # Cargar los datos de la transacción existente
            transaccion_overlay.set_transaccion_id(transaccion_id)

            # Mostrar el overlay en modo solo lectura
            transaccion_overlay.show_form(solo_lectura=True)

            logger.info(f"✅ TransaccionOverlay en modo visualización iniciado para transacción {transaccion_id}")

        except Exception as e:
            logger.error(f"Error visualizando transacción {transaccion_id}: {e}")
            self.mostrar_mensaje("❌ Error", f"No se pudo abrir la visualización: {str(e)}", "error")
    
    # En inscripcion_overlay.py, donde se cargan las transacciones
    def cargar_transacciones_inscripcion(self, inscripcion_id: int):
        """Cargar transacciones de una inscripción"""
        try:
            from model.transaccion_model import TransaccionModel
            inscripcion_datos = InscripcionModel.obtener_detalle_inscripcion(inscripcion_id)
            
            estudiante_id_tx = inscripcion_datos.get('estudiante', {}).get('id')
            programa_id_tx = inscripcion_datos.get('programa', {}).get('id')
            
            resultado = TransaccionModel.obtener_por_inscripcion(estudiante_id=estudiante_id_tx, programa_id=programa_id_tx)
            
            if resultado.get('success'):
                transacciones = resultado.get('data', [])
                # Procesar transacciones...
                logger.info(f"Transacciones cargadas: {len(transacciones)}")
            else:
                logger.warning(f"No se pudieron cargar transacciones: {resultado.get('error')}")
                
        except Exception as e:
            logger.error(f"Error cargando transacciones: {e}")
    
    def agregar_transaccion(self, inscripcion_id: int):
        """Abrir diálogo para agregar transacción con registro automático"""
        try:
            # 1. Recuperar los IDs necesarios de la fuente de verdad (los widgets o datos originales)
            estudiante_id = None
            programa_id = None

            # Intentar obtener de los datos originales cargados en el overlay
            datos = getattr(self, '_datos_originales', {})
            if datos:
                # En tu estructura, los IDs suelen estar en el objeto 'inscripcion' o directamente
                insc_data = datos.get('inscripcion', {})
                estudiante_id = insc_data.get('estudiante_id') or datos.get('estudiante_id')
                programa_id = insc_data.get('programa_id') or datos.get('programa_id')

            # 2. Si no están en memoria, recuperarlos de la BD (Estructura confirmada por tus logs)
            if not estudiante_id or not programa_id:
                logger.info(f"🔍 Recuperando detalles para inscripción {inscripcion_id}...")
                from model.inscripcion_model import InscripcionModel
                res = InscripcionModel.obtener_detalle_inscripcion(inscripcion_id)
                
                if res and res.get('success') is not False:
                    estudiante_id = res.get('estudiante', {}).get('id')
                    programa_id = res.get('programa', {}).get('id')

            # 3. Validar y lanzar el TransaccionOverlay
            if estudiante_id and programa_id:
                from view.overlays.transaccion_overlay import TransaccionOverlay
                
                # Instanciar con los 3 IDs obligatorios
                transaccion_overlay = TransaccionOverlay(
                    self.window(),
                    inscripcion_id=int(inscripcion_id),
                    estudiante_id=int(estudiante_id),
                    programa_id=int(programa_id),
                    modo="nuevo"
                )
                
                # Conectar señal de éxito
                def on_creada(datos_tx):
                    self.mostrar_mensaje("✅ Éxito", "Transacción registrada correctamente", "success")
                    if hasattr(self, 'cargar_inscripciones'):
                        QTimer.singleShot(500, self.cargar_inscripciones)
                
                transaccion_overlay.transaccion_creada.connect(on_creada)
                transaccion_overlay.show_form(solo_lectura=False)
                
                logger.info(f"✅ TransaccionOverlay iniciado para Insc:{inscripcion_id}, Est:{estudiante_id}, Prog:{programa_id}")
            else:
                self.mostrar_mensaje("⚠️ Error", "No se pudieron localizar los IDs de estudiante o programa.", "error")

        except Exception as e:
            logger.error(f"Error en agregar_transaccion: {e}")
            self.mostrar_mensaje("❌ Error", f"No se pudo abrir el formulario: {str(e)}", "error")
    
    def editar_transaccion(self, transaccion_id: int, inscripcion_id: int, 
                            estudiante_id: int, programa_id: int):
        """
        Abrir TransaccionOverlay en modo edición para una transacción específica

        Args:
            transaccion_id: ID de la transacción a editar
            inscripcion_id: ID de la inscripción relacionada
            estudiante_id: ID del estudiante
            programa_id: ID del programa
        """
        try:
            logger.info(f"✏️ Editando transacción ID: {transaccion_id} para inscripción {inscripcion_id}")

            from view.overlays.transaccion_overlay import TransaccionOverlay

            # Crear overlay en modo edición
            transaccion_overlay = TransaccionOverlay(
                self.window(),
                inscripcion_id=inscripcion_id,
                estudiante_id=estudiante_id,
                programa_id=programa_id,
                modo="editar"  # Modo edición
            )

            # Cargar los datos de la transacción existente
            transaccion_overlay.set_transaccion_id(transaccion_id)

            # Conectar señal de éxito
            def on_actualizada(datos_tx):
                self.mostrar_mensaje("✅ Éxito", "Transacción actualizada correctamente", "success")
                # Recargar las inscripciones para mostrar los cambios
                if hasattr(self, 'cargar_inscripciones'):
                    QTimer.singleShot(500, self.cargar_inscripciones)

            transaccion_overlay.transaccion_actualizada.connect(on_actualizada)

            # Mostrar el overlay en modo edición (solo_lectura=False para permitir edición)
            transaccion_overlay.show_form(solo_lectura=False)

            logger.info(f"✅ TransaccionOverlay en modo edición iniciado para transacción {transaccion_id}")

        except Exception as e:
            logger.error(f"Error editando transacción {transaccion_id}: {e}")
            self.mostrar_mensaje("❌ Error", f"No se pudo abrir el editor: {str(e)}", "error")
    
    def _determinar_monto_sugerido(self, saldo_pendiente: float, costo_mensualidad: float,
                                    costo_matricula: float, costo_inscripcion: float,
                                    total_pagado: float) -> float:
        """
        Determinar monto sugerido inteligentemente basado en contexto
        
        Args:
            saldo_pendiente: Saldo pendiente de la inscripción
            costo_mensualidad: Costo de mensualidad del programa
            costo_matricula: Costo de matrícula
            costo_inscripcion: Costo de inscripción
            total_pagado: Total ya pagado
            
        Returns:
            Monto sugerido para la transacción
        """
        # Si no hay nada pagado, sugerir inscripción o matrícula
        if total_pagado == 0:
            if costo_inscripcion > 0:
                return float(costo_inscripcion)
            elif costo_matricula > 0:
                return float(costo_matricula)
        
        # Si ya se pagó inscripción/matrícula, sugerir mensualidad
        if costo_mensualidad > 0:
            # Si hay saldo pendiente menor que una mensualidad, sugerir el saldo completo
            if saldo_pendiente > 0 and saldo_pendiente < costo_mensualidad:
                return saldo_pendiente
            # Sino, sugerir la mensualidad
            return float(costo_mensualidad)
        
        # Si no hay mensualidad, sugerir el saldo pendiente completo o un monto razonable
        if saldo_pendiente > 0:
            # Si el saldo es muy grande, sugerir un pago parcial
            if saldo_pendiente > 1000:
                return 500.0  # Pago parcial sugerido
            return saldo_pendiente
        
        # Por defecto, sugerir 100 Bs.
        return 100.0
    
    def _construir_observaciones_transaccion(self, inscripcion_id: int, nombre_estudiante: str,
                                            descripcion_programa: str, monto_inscripcion: float,
                                            total_pagado: float, saldo_pendiente: float,
                                            monto_sugerido: float) -> str:
        """
        Construir observaciones detalladas para la transacción
        
        Args:
            Parámetros con información de la inscripción
            
        Returns:
            String con observaciones formateadas
        """
        from datetime import datetime
        
        observaciones = f"=== PAGO PARA INSCRIPCIÓN ===\n"
        observaciones += f"Inscripción ID: {inscripcion_id}\n"
        observaciones += f"Fecha sugerida: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        observaciones += f"\n--- DETALLES DEL ESTUDIANTE ---\n"
        observaciones += f"Estudiante: {nombre_estudiante}\n"
        observaciones += f"Programa: {descripcion_programa}\n"
        observaciones += f"\n--- RESUMEN FINANCIERO ---\n"
        observaciones += f"Total inscripción: {monto_inscripcion:.2f} Bs.\n"
        observaciones += f"Total pagado: {total_pagado:.2f} Bs.\n"
        observaciones += f"Saldo pendiente: {saldo_pendiente:.2f} Bs.\n"
        observaciones += f"Monto sugerido: {monto_sugerido:.2f} Bs.\n"
        observaciones += f"\n--- OBSERVACIONES ---\n"
        
        if saldo_pendiente <= 0:
            observaciones += "⚠️  La inscripción ya está pagada completamente.\n"
            observaciones += "Este pago es para conceptos adicionales."
        elif monto_sugerido >= saldo_pendiente:
            observaciones += "✅  Este pago cubrirá el saldo pendiente completo."
        else:
            observaciones += f"📊  Este pago cubrirá {monto_sugerido/saldo_pendiente*100:.1f}% del saldo pendiente."
            observaciones += f"\nSaldo restante después del pago: {saldo_pendiente - monto_sugerido:.2f} Bs."
            
        return observaciones
    
    def _sugerir_forma_pago(self, transaccion_overlay, monto_sugerido: float):
        """
        Sugerir forma de pago basada en el monto
        
        Args:
            transaccion_overlay: Instancia del overlay de transacción
            monto_sugerido: Monto sugerido para la transacción
        """
        if not hasattr(transaccion_overlay, 'forma_pago_combo'):
            return
        
        # Para montos pequeños, sugerir efectivo
        if monto_sugerido <= 500:
            # Buscar "EFECTIVO" en el combo
            index = transaccion_overlay.forma_pago_combo.findText("EFECTIVO")
            if index >= 0:
                transaccion_overlay.forma_pago_combo.setCurrentIndex(index)
        # Para montos grandes, sugerir transferencia
        elif monto_sugerido > 2000:
            index = transaccion_overlay.forma_pago_combo.findText("TRANSFERENCIA")
            if index >= 0:
                transaccion_overlay.forma_pago_combo.setCurrentIndex(index)
    
    # ===== MÉTODOS OVERRIDE DE BASE OVERLAY =====
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo", inscripcion_id=None,
                estudiante_id: Optional[int] = None, programa_id: Optional[int] = None,):
        """Mostrar overlay con configuración específica"""
        logger.debug(f"📋 show_form llamado - Est: {estudiante_id}, Prog: {programa_id}, Insc: {inscripcion_id}")
        
        # Limpiar estado anterior
        self.clear_form()
        
        self.solo_lectura = solo_lectura
        self.modo = modo
        
        # Configurar IDs según parámetros
        if estudiante_id is not None:
            try:
                self.estudiante_id = int(estudiante_id) if isinstance(estudiante_id, (int, str)) and str(estudiante_id).isdigit() else None
            except:
                self.estudiante_id = None
                
        if programa_id is not None:
            try:
                self.programa_id = int(programa_id) if isinstance(programa_id, (int, str)) and str(programa_id).isdigit() else None
            except:
                self.programa_id = None
                
        # Si hay inscripción_id, verificar si requiere completar justificación
        requiere_completar = False
        if inscripcion_id:
            try:
                inscripcion_id_int = int(inscripcion_id) if isinstance(inscripcion_id, (int, str)) and str(inscripcion_id).isdigit() else None
                if inscripcion_id_int:
                    from controller.inscripcion_controller import InscripcionController
                    resultado = InscripcionController.obtener_inscripcion_para_edicion(inscripcion_id_int)
                    
                    if resultado.get('success'):
                        data = resultado['data']
                        self.estudiante_id = data.get('estudiante_id')
                        self.programa_id = data.get('programa_id')
                        self.inscripcion_id = inscripcion_id_int
                        requiere_completar = data.get('requiere_completar', False)
                        
                        # Si requiere completar, mostrar en modo edición
                        if requiere_completar:
                            self.modo = "editar"
            except Exception as e:
                logger.error(f"Error cargando inscripción {inscripcion_id}: {e}")
                
        logger.debug(f"✅ Configurado - Est: {self.estudiante_id}, Prog: {self.programa_id}, Insc: {self.inscripcion_id}, Requiere completar: {requiere_completar}")
        
        # Configurar título según contexto
        titulo = "🎓 GESTIÓN DE INSCRIPCIONES"
        if requiere_completar:
            titulo = "✏️ COMPLETAR JUSTIFICACIÓN DE DESCUENTO"
        elif self.estudiante_id and self.programa_id:
            titulo = f"🎓 INSCRIPCIÓN - EST: {self.estudiante_id}, PROG: {self.programa_id}"
        elif self.estudiante_id:
            titulo = f"👤 INSCRIPCIONES DEL ESTUDIANTE {self.estudiante_id}"
        elif self.programa_id:
            titulo = f"📚 INSCRIPCIONES DEL PROGRAMA {self.programa_id}"
            
        self.set_titulo(titulo)
        
        # Ocultar botones base que no necesitamos
        self.btn_guardar.setVisible(False)
        self.btn_cancelar.setText("👈 CERRAR")
        
        # Actualizar interfaz según contexto
        self.actualizar_interfaz_segun_contexto()
        
        # Cargar inscripciones después de un pequeño delay
        QTimer.singleShot(150, self.cargar_inscripciones)
        
        # Llamar al método base
        super().show_form(solo_lectura)
    
    def close_overlay(self):
        """Cerrar el overlay"""
        self.close()
    
    def clear_form(self):
        """Limpiar formulario completo (actualizado)"""
        self.inscripcion_id = None
        self.estudiante_id = None
        self.programa_id = None
        self.inscripciones = []
        self.estudiantes_encontrados = []
        self.programas_disponibles = []
        
        if self.estudiante_id_label:
            self.estudiante_id_label.setText("NO ESPECIFICADO")
            
        if self.programa_id_label:
            self.programa_id_label.setText("NO ESPECIFICADO")
            
        if self.busqueda_estudiante_input:
            self.busqueda_estudiante_input.clear()
            
        if self.programa_combo:
            self.programa_combo.clear()
            self.programa_combo.addItem("-- SELECCIONE UN PROGRAMA --", None)
            
        if self.btn_seleccionar_programa:
            self.btn_seleccionar_programa.setEnabled(False)
            
        if self.seleccion_estudiante_frame:
            self.seleccion_estudiante_frame.setVisible(False)
            
        if self.seleccion_programa_frame:
            self.seleccion_programa_frame.setVisible(False)
            
        if self.nueva_inscripcion_frame:
            self.nueva_inscripcion_frame.setVisible(False)
            
        if self.valor_real_display:
            self.valor_real_display.setText("0.00 Bs.")
            
        if self.valor_final_input:
            self.valor_final_input.clear()
            
        if self.observaciones_input:
            self.observaciones_input.clear()
            
        if self.inscripciones_layout:
            while self.inscripciones_layout.count():
                child = self.inscripciones_layout.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()
                    
        if self.estudiantes_list_layout:
            while self.estudiantes_list_layout.count():
                child = self.estudiantes_list_layout.takeAt(0)
                widget = child.widget()
                if widget:
                    widget.deleteLater()
    
    def mostrar_mensaje(self, titulo: str, mensaje: str, tipo: str = "info"):
        """Mostrar mensaje al usuario"""
        icon = QMessageBox.Icon.Information
        
        if tipo == "warning":
            icon = QMessageBox.Icon.Warning
        elif tipo == "error":
            icon = QMessageBox.Icon.Critical
        elif tipo == "success":
            icon = QMessageBox.Icon.Information
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(icon)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def resizeEvent(self, event):
        """Ajustar el ancho de las tarjetas cuando cambia el tamaño de la ventana"""
        super().resizeEvent(event)
        # Actualizar el ancho máximo de las tarjetas existentes
        if self.inscripciones_layout:
            for i in range(self.inscripciones_layout.count()):
                item = self.inscripciones_layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and widget.objectName() == "tarjetaInscripcion":
                        widget.setMaximumWidth(int(self.width() * 0.9))
    