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
    QAbstractItemView, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem
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

# Importar estilos y utilidades
from utils.validators import Validators

from .base_overlay import BaseOverlay

# Configurar logger
logger = logging.getLogger(__name__)

class InscripcionOverlay(BaseOverlay):
    """Overlay para crear/editar/ver inscripciones de estudiantes a programas"""
    
    # Señales específicas
    inscripcion_creada = Signal(dict)
    inscripcion_actualizada = Signal(dict)
    inscripcion_cancelada = Signal(dict)
    
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
        
        # Configurar UI específica
        self.setup_ui_especifica()
        self.setup_conexiones_especificas()
        self.setup_validators()
        
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
        
        # Grupo: Buscar Estudiante
        grupo_buscar_estudiante = self.crear_grupo_buscar_estudiante()
        main_layout.addWidget(grupo_buscar_estudiante)
        
        # Grupo: Información del Estudiante (oculto inicialmente)
        self.grupo_info_estudiante = self.crear_grupo_info_estudiante()
        self.grupo_info_estudiante.setVisible(False)
        main_layout.addWidget(self.grupo_info_estudiante)
        
        # Grupo: Buscar Programa
        grupo_buscar_programa = self.crear_grupo_buscar_programa()
        main_layout.addWidget(grupo_buscar_programa)
        
        # Grupo: Información del Programa (oculto inicialmente)
        self.grupo_info_programa = self.crear_grupo_info_programa()
        self.grupo_info_programa.setVisible(False)
        main_layout.addWidget(self.grupo_info_programa)
        
        # Grupo: Detalles de la Inscripción
        self.grupo_detalles_inscripcion = self.crear_grupo_detalles_inscripcion()
        self.grupo_detalles_inscripcion.setVisible(False)
        main_layout.addWidget(self.grupo_detalles_inscripcion)
        
        # Grupo: Costos y Pagos
        self.grupo_costos_pagos = self.crear_grupo_costos_pagos()
        self.grupo_costos_pagos.setVisible(False)
        main_layout.addWidget(self.grupo_costos_pagos)
        
        # TabWidget para pestañas adicionales (solo visible en modo editar/lectura)
        self.tab_widget = QTabWidget()
        self.tab_widget.setVisible(False)
        
        # Pestaña: Historial de Pagos
        self.tab_pagos = self.crear_tab_pagos()
        self.tab_widget.addTab(self.tab_pagos, "💰 Historial de Pagos")
        
        # Pestaña: Documentos Adjuntos
        self.tab_documentos = self.crear_tab_documentos()
        self.tab_widget.addTab(self.tab_documentos, "📎 Documentos Adjuntos")
        
        main_layout.addWidget(self.tab_widget)
        
        # Espacio flexible
        main_layout.addStretch()
        
        scroll_widget.setWidget(main_widget)
        self.content_layout.addWidget(scroll_widget, 1)
    
    def crear_grupo_buscar_estudiante(self):
        """Crear grupo para buscar estudiante"""
        grupo = QGroupBox("🔍 BUSCAR ESTUDIANTE")
        
        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)
        
        # Explicación
        label_info = QLabel("Busque al estudiante por CI, nombres o apellidos:")
        label_info.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(label_info)
        
        # Layout para búsqueda
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        # Campo de búsqueda
        self.estudiante_search_input = QLineEdit()
        self.estudiante_search_input.setPlaceholderText("Ej: 1234567, Juan Pérez, o juan@email.com")
        self.estudiante_search_input.setMinimumHeight(35)
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
        
        # Lista de resultados (inicialmente oculta)
        self.estudiante_results_frame = QFrame()
        self.estudiante_results_frame.setVisible(False)
        self.estudiante_results_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
        """)
        
        results_layout = QVBoxLayout(self.estudiante_results_frame)
        results_layout.setContentsMargins(10, 10, 10, 10)
        
        results_title = QLabel("📋 Resultados de búsqueda:")
        results_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        results_layout.addWidget(results_title)
        
        # Tabla de resultados
        self.estudiante_results_table = QTableWidget()
        self.estudiante_results_table.setColumnCount(4)
        self.estudiante_results_table.setHorizontalHeaderLabels(["CI", "Nombre Completo", "Email", "Teléfono"])
        self.estudiante_results_table.horizontalHeader().setStretchLastSection(True)
        self.estudiante_results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.estudiante_results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.estudiante_results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.estudiante_results_table.setAlternatingRowColors(True)
        self.estudiante_results_table.setMinimumHeight(100)
        self.estudiante_results_table.setMaximumHeight(150)
        
        results_layout.addWidget(self.estudiante_results_table)
        
        layout.addWidget(self.estudiante_results_frame)
        
        # Label de estado
        self.estudiante_status_label = QLabel("")
        self.estudiante_status_label.setStyleSheet("""
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
        """)
        layout.addWidget(self.estudiante_status_label)
        
        return grupo
    
    def crear_grupo_info_estudiante(self):
        """Crear grupo para mostrar información del estudiante"""
        grupo = QGroupBox("👤 INFORMACIÓN DEL ESTUDIANTE")
        
        grid = QGridLayout(grupo)
        grid.setSpacing(10)
        grid.setContentsMargins(15, 20, 15, 15)
        
        # Fila 1: CI
        grid.addWidget(QLabel("CI:"), 0, 0)
        self.estudiante_ci_label = QLabel()
        self.estudiante_ci_label.setStyleSheet("font-weight: bold;")
        grid.addWidget(self.estudiante_ci_label, 0, 1)
        
        # Fila 2: Nombre Completo
        grid.addWidget(QLabel("Nombre Completo:"), 1, 0)
        self.estudiante_nombre_label = QLabel()
        self.estudiante_nombre_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        grid.addWidget(self.estudiante_nombre_label, 1, 1)
        
        # Fila 3: Email
        grid.addWidget(QLabel("Email:"), 2, 0)
        self.estudiante_email_label = QLabel()
        grid.addWidget(self.estudiante_email_label, 2, 1)
        
        # Fila 4: Teléfono
        grid.addWidget(QLabel("Teléfono:"), 3, 0)
        self.estudiante_telefono_label = QLabel()
        grid.addWidget(self.estudiante_telefono_label, 3, 1)
        
        # Fila 5: Profesión/Universidad
        grid.addWidget(QLabel("Profesión:"), 0, 2)
        self.estudiante_profesion_label = QLabel()
        grid.addWidget(self.estudiante_profesion_label, 0, 3)
        
        grid.addWidget(QLabel("Universidad:"), 1, 2)
        self.estudiante_universidad_label = QLabel()
        grid.addWidget(self.estudiante_universidad_label, 1, 3)
        
        # Botón para cambiar estudiante
        self.btn_cambiar_estudiante = QPushButton("🔄 Cambiar Estudiante")
        self.btn_cambiar_estudiante.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        grid.addWidget(self.btn_cambiar_estudiante, 4, 3)
        
        return grupo
    
    def crear_grupo_buscar_programa(self):
        """Crear grupo para buscar programa"""
        grupo = QGroupBox("📚 BUSCAR PROGRAMA ACADÉMICO")
        
        layout = QVBoxLayout(grupo)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 20, 15, 15)
        
        # Explicación
        label_info = QLabel("Busque el programa por código, nombre o estado:")
        label_info.setStyleSheet("color: #666; font-size: 12px;")
        layout.addWidget(label_info)
        
        # Layout para búsqueda
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)
        
        # Campo de búsqueda
        self.programa_search_input = QLineEdit()
        self.programa_search_input.setPlaceholderText("Ej: PROG-2024, Diplomado en IA, o EN_CURSO")
        self.programa_search_input.setMinimumHeight(35)
        self.programa_search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #9b59b6;
                border-radius: 6px;
                font-size: 13px;
            }
        """)
        search_layout.addWidget(self.programa_search_input, 1)
        
        # Botón buscar
        self.btn_buscar_programa = QPushButton("🔍 BUSCAR")
        self.btn_buscar_programa.setObjectName("btnBuscarPrograma")
        self.btn_buscar_programa.setMinimumHeight(35)
        self.btn_buscar_programa.setStyleSheet("""
            #btnBuscarPrograma {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 0 20px;
            }
            #btnBuscarPrograma:hover {
                background-color: #8e44ad;
            }
        """)
        search_layout.addWidget(self.btn_buscar_programa)
        
        layout.addLayout(search_layout)
        
        # Lista de resultados (inicialmente oculta)
        self.programa_results_frame = QFrame()
        self.programa_results_frame.setVisible(False)
        self.programa_results_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #ddd;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
        """)
        
        results_layout = QVBoxLayout(self.programa_results_frame)
        results_layout.setContentsMargins(10, 10, 10, 10)
        
        results_title = QLabel("📋 Programas disponibles:")
        results_title.setStyleSheet("font-weight: bold; color: #2c3e50;")
        results_layout.addWidget(results_title)
        
        # Tabla de resultados
        self.programa_results_table = QTableWidget()
        self.programa_results_table.setColumnCount(5)
        self.programa_results_table.setHorizontalHeaderLabels(["Código", "Nombre", "Estado", "Cupos", "Costo Total"])
        self.programa_results_table.horizontalHeader().setStretchLastSection(True)
        self.programa_results_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.programa_results_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.programa_results_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.programa_results_table.setAlternatingRowColors(True)
        self.programa_results_table.setMinimumHeight(150)
        self.programa_results_table.setMaximumHeight(250)
        
        results_layout.addWidget(self.programa_results_table)
        
        layout.addWidget(self.programa_results_frame)
        
        # Label de estado
        self.programa_status_label = QLabel("")
        self.programa_status_label.setStyleSheet("""
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
        """)
        layout.addWidget(self.programa_status_label)
        
        return grupo
    
    def crear_grupo_info_programa(self):
        """Crear grupo para mostrar información del programa"""
        grupo = QGroupBox("📊 INFORMACIÓN DEL PROGRAMA")
        
        grid = QGridLayout(grupo)
        grid.setSpacing(10)
        grid.setContentsMargins(15, 20, 15, 15)
        
        # Fila 1: Código y Nombre
        grid.addWidget(QLabel("Código:"), 0, 0)
        self.programa_codigo_label = QLabel()
        self.programa_codigo_label.setStyleSheet("font-weight: bold; color: #9b59b6;")
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
        
        # Fila 3: Cupos
        grid.addWidget(QLabel("Cupos:"), 2, 0)
        self.programa_cupos_label = QLabel()
        grid.addWidget(self.programa_cupos_label, 2, 1)
        
        # Fila 4: Estado
        grid.addWidget(QLabel("Estado:"), 2, 2)
        self.programa_estado_label = QLabel()
        self.programa_estado_label.setStyleSheet("font-weight: bold;")
        grid.addWidget(self.programa_estado_label, 2, 3)
        
        # Fila 5: Fechas
        grid.addWidget(QLabel("Fecha Inicio:"), 3, 0)
        self.programa_fecha_inicio_label = QLabel()
        grid.addWidget(self.programa_fecha_inicio_label, 3, 1)
        
        grid.addWidget(QLabel("Fecha Fin:"), 3, 2)
        self.programa_fecha_fin_label = QLabel()
        grid.addWidget(self.programa_fecha_fin_label, 3, 3)
        
        # Fila 6: Docente Coordinador
        grid.addWidget(QLabel("Docente Coordinador:"), 4, 0)
        self.programa_docente_label = QLabel()
        grid.addWidget(self.programa_docente_label, 4, 1, 1, 3)
        
        # Botón para cambiar programa
        self.btn_cambiar_programa = QPushButton("🔄 Cambiar Programa")
        self.btn_cambiar_programa.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        grid.addWidget(self.btn_cambiar_programa, 5, 3)
        
        return grupo
    
    def crear_grupo_detalles_inscripcion(self):
        """Crear grupo para detalles de la inscripción"""
        grupo = QGroupBox("📝 DETALLES DE LA INSCRIPCIÓN")
        
        grid = QGridLayout(grupo)
        grid.setSpacing(10)
        grid.setContentsMargins(15, 20, 15, 15)
        
        # Fila 1: Fecha de Inscripción
        grid.addWidget(QLabel("Fecha Inscripción:*"), 0, 0)
        self.fecha_inscripcion_date = QDateEdit()
        self.fecha_inscripcion_date.setCalendarPopup(True)
        self.fecha_inscripcion_date.setDate(QDate.currentDate())
        self.fecha_inscripcion_date.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inscripcion_date.setMinimumHeight(30)
        grid.addWidget(self.fecha_inscripcion_date, 0, 1)
        
        # Fila 2: Estado
        grid.addWidget(QLabel("Estado:*"), 1, 0)
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["PREINSCRITO", "INSCRITO", "EN_CURSO", "FINALIZADO", "CANCELADO"])
        self.estado_combo.setMinimumHeight(30)
        grid.addWidget(self.estado_combo, 1, 1)
        
        # Fila 3: Descuento
        grid.addWidget(QLabel("Descuento (%):"), 2, 0)
        self.descuento_spin = QDoubleSpinBox()
        self.descuento_spin.setRange(0, 100)
        self.descuento_spin.setDecimals(2)
        self.descuento_spin.setSuffix(" %")
        self.descuento_spin.setValue(0.0)
        self.descuento_spin.setMinimumHeight(30)
        grid.addWidget(self.descuento_spin, 2, 1)
        
        # Fila 4: Observaciones
        grid.addWidget(QLabel("Observaciones:"), 3, 0)
        self.observaciones_text = QTextEdit()
        self.observaciones_text.setMaximumHeight(100)
        self.observaciones_text.setPlaceholderText("Observaciones adicionales sobre la inscripción...")
        grid.addWidget(self.observaciones_text, 3, 1, 1, 3)
        
        return grupo
    
    def crear_grupo_costos_pagos(self):
        """Crear grupo para costos y pagos"""
        grupo = QGroupBox("💰 RESUMEN DE COSTOS Y PAGOS")
        
        layout = QVBoxLayout(grupo)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 20, 15, 15)
        
        # Grid para costos
        cost_grid = QGridLayout()
        cost_grid.setSpacing(10)
        
        # Costos del programa
        cost_grid.addWidget(QLabel("Costo Matrícula:"), 0, 0)
        self.costo_matricula_label = QLabel("0.00 Bs")
        self.costo_matricula_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        cost_grid.addWidget(self.costo_matricula_label, 0, 1)
        
        cost_grid.addWidget(QLabel("Costo Inscripción:"), 1, 0)
        self.costo_inscripcion_label = QLabel("0.00 Bs")
        self.costo_inscripcion_label.setStyleSheet("font-weight: bold; color: #27ae60;")
        cost_grid.addWidget(self.costo_inscripcion_label, 1, 1)
        
        cost_grid.addWidget(QLabel("Costo Total Programa:"), 2, 0)
        self.costo_total_label = QLabel("0.00 Bs")
        self.costo_total_label.setStyleSheet("font-weight: bold; color: #e74c3c; font-size: 14px;")
        cost_grid.addWidget(self.costo_total_label, 2, 1)
        
        cost_grid.addWidget(QLabel("Descuento Aplicado:"), 3, 0)
        self.descuento_aplicado_label = QLabel("0.00 Bs (0%)")
        self.descuento_aplicado_label.setStyleSheet("font-weight: bold; color: #3498db;")
        cost_grid.addWidget(self.descuento_aplicado_label, 3, 1)
        
        cost_grid.addWidget(QLabel("Costo Final:"), 4, 0)
        self.costo_final_label = QLabel("0.00 Bs")
        self.costo_final_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 16px; background-color: #ecf0f1; padding: 5px; border-radius: 4px;")
        cost_grid.addWidget(self.costo_final_label, 4, 1)
        
        layout.addLayout(cost_grid)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator)
        
        # Información de pago inicial
        payment_layout = QVBoxLayout()
        
        payment_title = QLabel("💳 PAGO INICIAL REQUERIDO")
        payment_title.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 13px;")
        payment_layout.addWidget(payment_title)
        
        self.pago_inicial_label = QLabel("0.00 Bs (Matrícula + Inscripción)")
        self.pago_inicial_label.setStyleSheet("font-weight: bold; color: #e74c3c; font-size: 14px; background-color: #f8d7da; padding: 8px; border-radius: 6px; border: 1px solid #f5c6cb;")
        payment_layout.addWidget(self.pago_inicial_label)
        
        layout.addLayout(payment_layout)
        
        # En modo edición/lectura, mostrar información de pagos realizados
        self.pagos_realizados_frame = QFrame()
        self.pagos_realizados_frame.setVisible(False)
        self.pagos_realizados_frame.setStyleSheet("""
            QFrame {
                background-color: #d5f4e6;
                border: 1px solid #c3e6cb;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        pagos_layout = QVBoxLayout(self.pagos_realizados_frame)
        
        pagos_title = QLabel("📊 PAGOS REALIZADOS")
        pagos_title.setStyleSheet("font-weight: bold; color: #155724;")
        pagos_layout.addWidget(pagos_title)
        
        pagos_grid = QGridLayout()
        
        pagos_grid.addWidget(QLabel("Total Pagado:"), 0, 0)
        self.total_pagado_label = QLabel("0.00 Bs")
        self.total_pagado_label.setStyleSheet("font-weight: bold; color: #155724;")
        pagos_grid.addWidget(self.total_pagado_label, 0, 1)
        
        pagos_grid.addWidget(QLabel("Saldo Pendiente:"), 1, 0)
        self.saldo_pendiente_label = QLabel("0.00 Bs")
        self.saldo_pendiente_label.setStyleSheet("font-weight: bold; color: #721c24;")
        pagos_grid.addWidget(self.saldo_pendiente_label, 1, 1)
        
        pagos_grid.addWidget(QLabel("Porcentaje Pagado:"), 2, 0)
        self.porcentaje_pagado_label = QLabel("0%")
        self.porcentaje_pagado_label.setStyleSheet("font-weight: bold; color: #004085;")
        pagos_grid.addWidget(self.porcentaje_pagado_label, 2, 1)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 4px;
            }
        """)
        pagos_grid.addWidget(self.progress_bar, 3, 0, 1, 2)
        
        pagos_layout.addLayout(pagos_grid)
        layout.addWidget(self.pagos_realizados_frame)
        
        return grupo
    
    def crear_tab_pagos(self):
        """Crear pestaña para historial de pagos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # Botón para registrar nuevo pago
        self.btn_nuevo_pago = QPushButton("➕ Registrar Nuevo Pago")
        self.btn_nuevo_pago.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        layout.addWidget(self.btn_nuevo_pago)
        
        # Tabla de pagos
        self.pagos_table = QTableWidget()
        self.pagos_table.setColumnCount(7)
        self.pagos_table.setHorizontalHeaderLabels(["ID", "Fecha", "Forma Pago", "Monto", "Comprobante", "Estado", "Observaciones"])
        self.pagos_table.horizontalHeader().setStretchLastSection(True)
        self.pagos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.pagos_table.setAlternatingRowColors(True)
        self.pagos_table.setSortingEnabled(True)
        
        layout.addWidget(self.pagos_table, 1)
        
        return tab
    
    def crear_tab_documentos(self):
        """Crear pestaña para documentos adjuntos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        
        # Botón para subir documentos
        self.btn_subir_documento = QPushButton("📤 Subir Documento")
        self.btn_subir_documento.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        layout.addWidget(self.btn_subir_documento)
        
        # Lista de documentos
        self.documentos_list = QListWidget()
        self.documentos_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #dee2e6;
            }
            QListWidget::item:selected {
                background-color: #e3f2fd;
            }
        """)
        
        layout.addWidget(self.documentos_list, 1)
        
        # Botones para documentos
        btn_doc_layout = QHBoxLayout()
        
        self.btn_ver_documento = QPushButton("👁️ Ver")
        self.btn_descargar_documento = QPushButton("⬇️ Descargar")
        self.btn_eliminar_documento = QPushButton("🗑️ Eliminar")
        
        for btn in [self.btn_ver_documento, self.btn_descargar_documento, self.btn_eliminar_documento]:
            btn.setEnabled(False)
            btn.setMinimumHeight(35)
            btn_doc_layout.addWidget(btn)
        
        layout.addLayout(btn_doc_layout)
        
        return tab
    
    def setup_validators(self):
        """Configurar validadores"""
        # Validar que solo números en CI si es necesario
        pass
    
    def setup_conexiones_especificas(self):
        """Configurar conexiones específicas"""
        # Botones de búsqueda
        self.btn_buscar_estudiante.clicked.connect(self.buscar_estudiante)
        self.btn_buscar_programa.clicked.connect(self.buscar_programa)
        
        # Botones de cambio
        self.btn_cambiar_estudiante.clicked.connect(self.cambiar_estudiante)
        self.btn_cambiar_programa.clicked.connect(self.cambiar_programa)
        
        # Tablas de selección
        self.estudiante_results_table.itemDoubleClicked.connect(self.seleccionar_estudiante)
        self.programa_results_table.itemDoubleClicked.connect(self.seleccionar_programa)
        
        # Cambios en formulario
        self.descuento_spin.valueChanged.connect(self.calcular_costos)
        
        # Botones de pestañas (solo en modo edición)
        self.btn_nuevo_pago.clicked.connect(self.registrar_nuevo_pago)
        self.btn_subir_documento.clicked.connect(self.subir_documento)
        
        # Documentos
        self.documentos_list.itemSelectionChanged.connect(self.habilitar_botones_documentos)
        self.btn_ver_documento.clicked.connect(self.ver_documento)
        self.btn_descargar_documento.clicked.connect(self.descargar_documento)
        self.btn_eliminar_documento.clicked.connect(self.eliminar_documento)
        
        # **AGREGAR SI NO ESTÁ EN BaseOverlay:**
        if hasattr(self, 'btn_guardar'):
            self.btn_guardar.clicked.connect(self.guardar_datos)
    
    # ===== MÉTODOS DE BÚSQUEDA =====
    
    def buscar_estudiante(self):
        """Buscar estudiante en la base de datos"""
        search_term = self.estudiante_search_input.text().strip()
        
        if not search_term:
            self.mostrar_mensaje("Advertencia", "Por favor ingrese un término de búsqueda", "warning")
            return
        
        try:
            # Limpiar resultados anteriores
            self.estudiante_results_table.setRowCount(0)
            self.estudiante_status_label.setText("🔍 Buscando estudiantes...")
            self.estudiante_status_label.setStyleSheet("color: #f39c12;")
            
            # Determinar tipo de búsqueda
            if search_term.isdigit() or '-' in search_term:
                # Búsqueda por CI
                if '-' in search_term:
                    partes = search_term.split('-')
                    ci_numero = partes[0].strip()
                    ci_expedicion = partes[1].strip() if len(partes) > 1 else None
                else:
                    ci_numero = search_term
                    ci_expedicion = None
                
                estudiantes = EstudianteModel.buscar_estudiantes(
                    ci_numero=ci_numero,
                    ci_expedicion=ci_expedicion,
                    nombre=None,
                    limit=10,
                    offset=0
                )
            else:
                # Búsqueda por nombre
                estudiantes = EstudianteModel.buscar_estudiantes(
                    ci_numero=None,
                    ci_expedicion=None,
                    nombre=search_term,
                    limit=10,
                    offset=0
                )
            
            if estudiantes:
                self.estudiante_results_table.setRowCount(len(estudiantes))
                
                for i, estudiante in enumerate(estudiantes):
                    # CI completo
                    ci_completo = f"{estudiante.get('ci_numero', '')}-{estudiante.get('ci_expedicion', '')}"
                    ci_item = QTableWidgetItem(ci_completo)
                    self.estudiante_results_table.setItem(i, 0, ci_item)
                    
                    # Nombre completo
                    nombre_completo = f"{estudiante.get('nombres', '')} {estudiante.get('apellido_paterno', '')} {estudiante.get('apellido_materno', '')}".strip()
                    self.estudiante_results_table.setItem(i, 1, QTableWidgetItem(nombre_completo))
                    
                    # Email
                    self.estudiante_results_table.setItem(i, 2, QTableWidgetItem(estudiante.get('email', '')))
                    
                    # Teléfono
                    self.estudiante_results_table.setItem(i, 3, QTableWidgetItem(estudiante.get('telefono', '')))
                    
                    # Guardar ID como dato oculto
                    if ci_item:
                        ci_item.setData(Qt.ItemDataRole.UserRole, estudiante.get('id'))
                
                self.estudiante_results_frame.setVisible(True)
                self.estudiante_status_label.setText(f"✅ Encontrados {len(estudiantes)} estudiantes")
                self.estudiante_status_label.setStyleSheet("color: #27ae60;")
                
            else:
                self.estudiante_results_frame.setVisible(False)
                self.estudiante_status_label.setText("❌ No se encontraron estudiantes con ese criterio")
                self.estudiante_status_label.setStyleSheet("color: #e74c3c;")
                
        except Exception as e:
            logger.error(f"Error buscando estudiante: {e}")
            self.estudiante_status_label.setText(f"❌ Error en la búsqueda: {str(e)}")
            self.estudiante_status_label.setStyleSheet("color: #e74c3c;")
    
    def buscar_programa(self):
        """Buscar programa en la base de datos"""
        search_term = self.programa_search_input.text().strip()
        
        if not search_term:
            self.mostrar_mensaje("Advertencia", "Por favor ingrese un término de búsqueda", "warning")
            return
        
        try:
            # Limpiar resultados anteriores
            self.programa_results_table.setRowCount(0)
            self.programa_status_label.setText("🔍 Buscando programas...")
            self.programa_status_label.setStyleSheet("color: #f39c12;")
            
            # Buscar programas (usar búsqueda por código o nombre)
            programas = ProgramaModel.buscar_programas(
                codigo=search_term if '-' in search_term else None,
                nombre=search_term if '-' not in search_term else None,
                estado=None,  # Buscar todos los estados
                limit=10,
                offset=0
            )
            
            if programas:
                self.programa_results_table.setRowCount(len(programas))
                
                for i, programa in enumerate(programas):
                    id_item = QTableWidgetItem(str(programa.get('id', '')))
                    self.programa_results_table.setItem(i, 0, id_item)
                    
                    # Código
                    codigo_item = QTableWidgetItem(programa.get('codigo', ''))
                    self.programa_results_table.setItem(i, 0, codigo_item)
                    
                    # Nombre
                    self.programa_results_table.setItem(i, 1, QTableWidgetItem(programa.get('nombre', '')))
                    
                    # Estado
                    estado = programa.get('estado', '')
                    estado_item = QTableWidgetItem(estado)
                    self.programa_results_table.setItem(i, 2, estado_item)
                    
                    from config.constants import EstadoPrograma
                    
                    # Color según estado
                    if estado_item:
                        if estado == EstadoPrograma.INSCRIPCIONES or estado == EstadoPrograma.EN_CURSO:
                            estado_item.setForeground(QBrush(QColor("#27ae60")))
                        elif estado == EstadoPrograma.PLANIFICADO:
                            estado_item.setForeground(QBrush(QColor("#f39c12")))
                        elif estado == EstadoPrograma.CANCELADO or estado == EstadoPrograma.CONCLUIDO:
                            estado_item.setForeground(QBrush(QColor("#95a5a6")))
                    
                    # Cupos
                    cupos_inscritos = programa.get('cupos_inscritos', 0)
                    cupos_maximos = programa.get('cupos_maximos', 0)
                    cupos_text = f"{cupos_inscritos}/{cupos_maximos}"
                    self.programa_results_table.setItem(i, 3, QTableWidgetItem(cupos_text))
                    
                    # Costo total
                    costo_total = programa.get('costo_total', 0)
                    self.programa_results_table.setItem(i, 4, QTableWidgetItem(f"{costo_total:.2f} Bs"))
                    
                    # Guardar ID como dato oculto
                    if codigo_item:
                        codigo_item.setData(Qt.ItemDataRole.UserRole, programa.get('id'))
                
                self.programa_results_frame.setVisible(True)
                self.programa_status_label.setText(f"✅ Encontrados {len(programas)} programas")
                self.programa_status_label.setStyleSheet("color: #27ae60;")
                
            else:
                self.programa_results_frame.setVisible(False)
                self.programa_status_label.setText("❌ No se encontraron programas con ese criterio")
                self.programa_status_label.setStyleSheet("color: #e74c3c;")
                
        except Exception as e:
            logger.error(f"Error buscando programa: {e}")
            self.programa_status_label.setText(f"❌ Error en la búsqueda: {str(e)}")
            self.programa_status_label.setStyleSheet("color: #e74c3c;")
    
    # ===== MÉTODOS DE SELECCIÓN =====
    
    def seleccionar_estudiante(self, item):
        """Seleccionar estudiante de la tabla de resultados"""
        row = item.row()
        estudiante_id_item = self.estudiante_results_table.item(row, 0)
        if estudiante_id_item:
            estudiante_id = estudiante_id_item.data(Qt.ItemDataRole.UserRole)
            if estudiante_id:
                self.cargar_estudiante(estudiante_id)
    
    def seleccionar_programa(self, item):
        """Seleccionar programa de la tabla de resultados"""
        row = item.row()
        programa_id_item = self.programa_results_table.item(row, 0)
        if programa_id_item:
            programa_id = programa_id_item.data(Qt.ItemDataRole.UserRole)
            if programa_id:
                self.cargar_programa(programa_id)
    
    def cargar_estudiante(self, estudiante_id: int):
        """Cargar información del estudiante seleccionado"""
        try:
            # Obtener datos completos del estudiante
            estudiante = EstudianteModel.buscar_estudiante_id(estudiante_id)
            
            if estudiante:
                self.estudiante_id = estudiante_id
                self.estudiante_data = estudiante
                
                # Actualizar interfaz
                ci_completo = f"{estudiante.get('ci_numero', '')}-{estudiante.get('ci_expedicion', '')}"
                self.estudiante_ci_label.setText(ci_completo)
                
                nombre_completo = f"{estudiante.get('nombres', '')} {estudiante.get('apellido_paterno', '')} {estudiante.get('apellido_materno', '')}".strip()
                self.estudiante_nombre_label.setText(nombre_completo)
                
                self.estudiante_email_label.setText(estudiante.get('email', 'No registrado'))
                self.estudiante_telefono_label.setText(estudiante.get('telefono', 'No registrado'))
                self.estudiante_profesion_label.setText(estudiante.get('profesion', 'No registrado'))
                self.estudiante_universidad_label.setText(estudiante.get('universidad', 'No registrado'))
                
                # Ocultar búsqueda y mostrar información
                self.estudiante_results_frame.setVisible(False)
                self.grupo_info_estudiante.setVisible(True)
                self.estudiante_encontrado = True
                self.estudiante_status_label.setText(f"✅ Estudiante seleccionado: {nombre_completo}")
                self.estudiante_status_label.setStyleSheet("color: #27ae60;")
                
                # Si ya tenemos programa, mostrar detalles de inscripción
                if self.programa_encontrado:
                    self.mostrar_detalles_inscripcion()
                    
            else:
                self.mostrar_mensaje("Error", "No se pudo cargar la información del estudiante", "error")
                
        except Exception as e:
            logger.error(f"Error cargando estudiante: {e}")
            self.mostrar_mensaje("Error", f"No se pudo cargar el estudiante: {str(e)}", "error")
    
    def cargar_programa(self, programa_id: int):
        """Cargar información del programa seleccionado"""
        try:
            # Obtener datos del programa
            resultado = ProgramaModel.obtener_programa(programa_id)
            
            if resultado.get('success') and resultado.get('data'):
                programa = resultado['data']
                self.programa_id = programa_id
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
                
                from config.constants import EstadoPrograma
                
                # Color según estado
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
                
                # **CORRECCIÓN: Manejar fechas correctamente**
                fecha_inicio = programa.get('fecha_inicio', '')
                fecha_fin = programa.get('fecha_fin', '')
                
                # Convertir datetime.date a string
                if fecha_inicio:
                    if hasattr(fecha_inicio, 'strftime'):
                        fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
                    else:
                        fecha_inicio_str = str(fecha_inicio)[:10]
                else:
                    fecha_inicio_str = 'No definida'
                
                if fecha_fin:
                    if hasattr(fecha_fin, 'strftime'):
                        fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
                    else:
                        fecha_fin_str = str(fecha_fin)[:10]
                else:
                    fecha_fin_str = 'No definida'
                    
                self.programa_fecha_inicio_label.setText(fecha_inicio_str)
                self.programa_fecha_fin_label.setText(fecha_fin_str)
                
                # Docente
                docente_id = programa.get('docente_coordinador_id')
                docente_nombre = "No asignado"
                
                if docente_id:
                    from model.docente_model import DocenteModel
                    docente = DocenteModel.obtener_docente_por_id(docente_id)
                    if docente:
                        docente_nombre = f"{docente.get('grado_academico', '')} {docente.get('nombres', '')} {docente.get('apellido_paterno', '')}".strip()
                
                self.programa_docente_label.setText(docente_nombre)
                
                # **CORRECCIÓN: Primero mostrar la información del programa**
                self.programa_results_frame.setVisible(False)
                self.grupo_info_programa.setVisible(True)
                
                # **CORRECCIÓN: Establecer programa_encontrado como True aquí**
                # El programa SÍ está encontrado y cargado, independientemente de la disponibilidad
                self.programa_encontrado = True
                
                self.programa_status_label.setText(f"✅ Programa seleccionado: {programa.get('codigo')}")
                self.programa_status_label.setStyleSheet("color: #27ae60;")
                
                # **VERIFICAR DISPONIBILIDAD (esto determinará si se puede crear la inscripción)**
                disponible = self.verificar_disponibilidad(programa_id)
                
                # **CORRECCIÓN: Establecer una variable separada para disponibilidad**
                self.programa_disponible = disponible
                
                # Actualizar costos
                self.actualizar_costos_programa()
                
                # Si ya tenemos estudiante, verificar si podemos mostrar detalles
                if self.estudiante_encontrado:
                    if disponible:
                        self.mostrar_detalles_inscripcion()
                    else:
                        # Programa encontrado pero no disponible
                        self.mostrar_mensaje(
                            "Programa no disponible",
                            "El programa seleccionado no está disponible para inscripción.\n"
                            "Verifique el estado y disponibilidad de cupos.",
                            "warning"
                        )
                
            else:
                mensaje = resultado.get('message', 'Error desconocido')
                self.mostrar_mensaje("Error", f"No se pudo cargar el programa: {mensaje}", "error")
                self.programa_encontrado = False
            
        except Exception as e:
            logger.error(f"Error cargando programa: {e}")
            self.mostrar_mensaje("Error", f"No se pudo cargar el programa: {str(e)}", "error")
            self.programa_encontrado = False
    
    def verificar_disponibilidad(self, programa_id: int):
        """Verificar disponibilidad de cupos en el programa"""
        try:
            disponibilidad = InscripcionModel.verificar_disponibilidad_programa(programa_id)
            
            if disponibilidad.get('success'):
                self.disponibilidad_data = disponibilidad['data']
                self.disponibilidad_verificada = disponibilidad['data']['disponible']
                
                # **CORRECCIÓN: Usar 'cupos_disponibles' en lugar de 'cupos_restantes'**
                cupos_disponibles = disponibilidad['data']['cupos_disponibles']
                
                # Mostrar mensaje apropiado
                if self.disponibilidad_verificada:
                    # Disponible
                    self.programa_status_label.setText(f"✅ {disponibilidad['data']['mensaje']}")
                    self.programa_status_label.setStyleSheet("color: #27ae60;")
                    
                    # Mostrar cupos disponibles
                    if cupos_disponibles == 9999:
                        mensaje_cupos = "Cupos ilimitados"
                    else:
                        mensaje_cupos = f"Cupos disponibles: {cupos_disponibles}"
                    
                    # Actualizar etiqueta de cupos con color
                    cupos_item = QTableWidgetItem(mensaje_cupos)
                    if cupos_disponibles == 9999:
                        cupos_item.setForeground(Qt.GlobalColor.green)
                    elif cupos_disponibles > 5:
                        cupos_item.setForeground(Qt.GlobalColor.darkGreen)
                    elif cupos_disponibles > 0:
                        cupos_item.setForeground(Qt.GlobalColor.darkYellow)
                    else:
                        cupos_item.setForeground(Qt.GlobalColor.red)
                        
                    # Buscar la fila del programa en la tabla y actualizar cupos
                    for row in range(self.programa_results_table.rowCount()):
                        id_item = self.programa_results_table.item(row, 0)
                        if id_item and id_item.data(Qt.ItemDataRole.UserRole) == programa_id:
                            self.programa_results_table.setItem(row, 4, cupos_item)
                            break
                        
                    return True
                else:
                    # No disponible
                    self.programa_status_label.setText(f"❌ {disponibilidad['data']['mensaje']}")
                    self.programa_status_label.setStyleSheet("color: #e74c3c;")
                    return False
            else:
                self.disponibilidad_verificada = False
                self.programa_status_label.setText("❌ No se pudo verificar disponibilidad")
                self.programa_status_label.setStyleSheet("color: #e74c3c;")
                return False
                
        except Exception as e:
            logger.error(f"Error verificando disponibilidad: {e}")
            self.disponibilidad_verificada = False
            self.programa_status_label.setText("❌ Error verificando disponibilidad")
            self.programa_status_label.setStyleSheet("color: #e74c3c;")
            return False
    
    def actualizar_costos_programa(self):
        """Actualizar los costos basados en el programa seleccionado"""
        if not self.programa_data:
            return
        
        try:
            costo_matricula = self.programa_data.get('costo_matricula', 0) or 0
            costo_inscripcion = self.programa_data.get('costo_inscripcion', 0) or 0
            costo_total = self.programa_data.get('costo_total', 0) or 0
            
            self.costo_matricula_label.setText(f"{costo_matricula:.2f} Bs")
            self.costo_inscripcion_label.setText(f"{costo_inscripcion:.2f} Bs")
            self.costo_total_label.setText(f"{costo_total:.2f} Bs")
            
            # Calcular pago inicial
            pago_inicial = costo_matricula + costo_inscripcion
            self.pago_inicial_label.setText(f"{pago_inicial:.2f} Bs (Matrícula + Inscripción)")
            
            # Calcular costo final con descuento
            self.calcular_costos()
            
        except Exception as e:
            logger.error(f"Error actualizando costos: {e}")
    
    def calcular_costos(self):
        """Calcular costos finales considerando descuento"""
        try:
            costo_total_str = self.costo_total_label.text().replace('Bs', '').strip()
            costo_total = float(costo_total_str) if costo_total_str else 0
            
            descuento_porcentaje = self.descuento_spin.value()
            
            if descuento_porcentaje > 0:
                descuento_monto = costo_total * (descuento_porcentaje / 100)
                costo_final = costo_total - descuento_monto
                
                self.descuento_aplicado_label.setText(f"{descuento_monto:.2f} Bs ({descuento_porcentaje:.2f}%)")
                self.costo_final_label.setText(f"{costo_final:.2f} Bs")
            else:
                self.descuento_aplicado_label.setText("0.00 Bs (0%)")
                self.costo_final_label.setText(f"{costo_total:.2f} Bs")
                
        except Exception as e:
            logger.error(f"Error calculando costos: {e}")
    
    # ===== MÉTODOS DE NAVEGACIÓN =====
    
    def cambiar_estudiante(self):
        """Volver a la búsqueda de estudiante"""
        self.estudiante_id = None
        self.estudiante_data = None
        self.estudiante_encontrado = False
        
        self.grupo_info_estudiante.setVisible(False)
        self.estudiante_results_frame.setVisible(False)
        self.estudiante_search_input.clear()
        self.estudiante_status_label.setText("")
        
        # Ocultar secciones dependientes
        self.grupo_detalles_inscripcion.setVisible(False)
        self.grupo_costos_pagos.setVisible(False)
    
    def cambiar_programa(self):
        """Volver a la búsqueda de programa"""
        self.programa_id = None
        self.programa_data = None
        self.programa_encontrado = False
        self.disponibilidad_verificada = False
        
        self.grupo_info_programa.setVisible(False)
        self.programa_results_frame.setVisible(False)
        self.programa_search_input.clear()
        self.programa_status_label.setText("")
        
        # Ocultar secciones dependientes
        self.grupo_detalles_inscripcion.setVisible(False)
        self.grupo_costos_pagos.setVisible(False)
    
    def mostrar_detalles_inscripcion(self):
        """Mostrar sección de detalles de inscripción"""
        if self.estudiante_encontrado and self.programa_encontrado and self.disponibilidad_verificada:
            # Mostrar grupo de detalles
            self.grupo_detalles_inscripcion.setVisible(True)
            
            # Mostrar grupo de costos
            self.grupo_costos_pagos.setVisible(True)
                
            # Si es modo edición o lectura, mostrar información de pagos
            if self.modo in ["editar", "lectura"]:
                self.pagos_realizados_frame.setVisible(True)
                self.cargar_informacion_pagos()
    
    # ===== IMPLEMENTACIÓN DE MÉTODOS BASE =====
    
    def validar_formulario(self):
        """Validar formulario de inscripción"""
        errores = []

        # Validar que se haya seleccionado estudiante
        if not self.estudiante_encontrado or not self.estudiante_id:
            errores.append("Debe seleccionar un estudiante")

        # Validar que se haya seleccionado programa
        if not self.programa_encontrado or not self.programa_id:
            errores.append("Debe seleccionar un programa académico")
        else:
            # **CORRECCIÓN: Verificar disponibilidad con la variable correcta**
            disponible = getattr(self, 'programa_disponible', False)

            if self.modo == "nuevo" and not disponible:
                errores.append("El programa no tiene cupos disponibles o no está disponible para inscripción")

            # También verificar estado del programa
            if hasattr(self, 'programa_data') and self.programa_data:
                programa = self.programa_data
                estado_programa = programa.get('estado', '')

                from config.constants import EstadoPrograma
                estados_validos = [EstadoPrograma.INSCRIPCIONES, EstadoPrograma.EN_CURSO]

                if estado_programa not in estados_validos:
                    errores.append(f"El programa no está disponible para inscripción. Estado actual: {estado_programa}")

        # Validar descuento
        descuento = self.descuento_spin.value()
        if descuento < 0 or descuento > 100:
            errores.append("El descuento debe estar entre 0% y 100%")

        # Validar fecha
        fecha_inscripcion = self.fecha_inscripcion_date.date()
        if not fecha_inscripcion.isValid():
            errores.append("Fecha de inscripción no válida")
        else:
            hoy = QDate.currentDate()
            if fecha_inscripcion > hoy:
                errores.append("La fecha de inscripción no puede ser futura")

        # Validar que no esté ya inscrito (solo para modo nuevo)
        if self.modo == "nuevo" and self.estudiante_id and self.programa_id:
            try:
                from config.database import Database
                connection = Database.get_connection()
                if connection:
                    cursor = connection.cursor()
                    query = """
                    SELECT 1 FROM inscripciones 
                    WHERE estudiante_id = %s AND programa_id = %s
                    AND estado IN ('INSCRITO', 'EN_CURSO', 'PREINSCRITO')
                    """
                    cursor.execute(query, (self.estudiante_id, self.programa_id))
                    ya_inscrito = cursor.fetchone()
                    cursor.close()
                    Database.return_connection(connection)

                    if ya_inscrito:
                        errores.append("El estudiante ya está inscrito en este programa")
            except Exception as e:
                logger.error(f"Error verificando inscripción existente: {e}")
                # No agregamos error para no bloquear por fallo en verificación

        logger.info(f"🔍 Validación completada. Errores encontrados: {len(errores)}")
        logger.info(f"   programa_encontrado: {self.programa_encontrado}")
        logger.info(f"   programa_id: {self.programa_id}")
        logger.info(f"   programa_disponible: {getattr(self, 'programa_disponible', 'No definido')}")
        logger.info(f"   estudiante_encontrado: {self.estudiante_encontrado}")
        logger.info(f"   estudiante_id: {self.estudiante_id}")

        return len(errores) == 0, errores
    
    def obtener_datos(self):
        """Obtener datos del formulario de inscripción"""
        fecha_inscripcion = self.fecha_inscripcion_date.date()

        datos = {
            'inscripcion_id': self.inscripcion_id,
            'estudiante_id': self.estudiante_id,
            'programa_id': self.programa_id,
            'fecha_inscripcion': fecha_inscripcion.toString('yyyy-MM-dd'),
            'estado': self.estado_combo.currentText(),
            'descuento_aplicado': self.descuento_spin.value(),
            'observaciones': self.observaciones_text.toPlainText().strip() or None,  # None si está vacío
            'estudiante_data': self.estudiante_data,
            'programa_data': self.programa_data
        }

        return datos
    
    def clear_form(self):
        """Limpiar formulario completo"""
        self.inscripcion_id = None
        self.estudiante_id = None
        self.programa_id = None
        self.original_data = {}
        
        # Limpiar búsqueda estudiante
        self.estudiante_search_input.clear()
        self.estudiante_results_table.setRowCount(0)
        self.estudiante_results_frame.setVisible(False)
        self.grupo_info_estudiante.setVisible(False)
        self.estudiante_status_label.setText("")
        self.estudiante_encontrado = False
        
        # Limpiar búsqueda programa
        self.programa_search_input.clear()
        self.programa_results_table.setRowCount(0)
        self.programa_results_frame.setVisible(False)
        self.grupo_info_programa.setVisible(False)
        self.programa_status_label.setText("")
        self.programa_encontrado = False
        
        # Limpiar detalles
        self.fecha_inscripcion_date.setDate(QDate.currentDate())
        self.estado_combo.setCurrentIndex(0)
        self.descuento_spin.setValue(0.0)
        self.observaciones_text.clear()
        
        # Ocultar grupos
        self.grupo_detalles_inscripcion.setVisible(False)
        self.grupo_costos_pagos.setVisible(False)
        
        # Limpiar costos
        self.costo_matricula_label.setText("0.00 Bs")
        self.costo_inscripcion_label.setText("0.00 Bs")
        self.costo_total_label.setText("0.00 Bs")
        self.descuento_aplicado_label.setText("0.00 Bs (0%)")
        self.costo_final_label.setText("0.00 Bs")
        self.pago_inicial_label.setText("0.00 Bs (Matrícula + Inscripción)")
        
        # Limpiar información de pagos
        self.pagos_realizados_frame.setVisible(False)
        self.total_pagado_label.setText("0.00 Bs")
        self.saldo_pendiente_label.setText("0.00 Bs")
        self.porcentaje_pagado_label.setText("0%")
        self.progress_bar.setValue(0)
        
        # Limpiar pestañas
        self.tab_widget.setVisible(False)
        self.pagos_table.setRowCount(0)
        self.documentos_list.clear()
    
    def cargar_datos(self, datos):
        """Cargar datos de inscripción existente"""
        self.inscripcion_id = datos.get('id')
        self.original_data = datos.copy()
        
        # Cargar estudiante
        estudiante_id = datos.get('estudiante_id')
        if estudiante_id:
            self.cargar_estudiante(estudiante_id)
        
        # Cargar programa
        programa_id = datos.get('programa_id')
        if programa_id:
            self.cargar_programa(programa_id)
        
        # Cargar detalles de inscripción
        fecha_inscripcion = datos.get('fecha_inscripcion')
        if fecha_inscripcion:
            try:
                qdate = QDate.fromString(fecha_inscripcion[:10], 'yyyy-MM-dd')
                if qdate.isValid():
                    self.fecha_inscripcion_date.setDate(qdate)
            except:
                pass
        
        estado = datos.get('estado', 'PREINSCRITO')
        index = self.estado_combo.findText(estado)
        if index >= 0:
            self.estado_combo.setCurrentIndex(index)
        
        descuento = datos.get('descuento_aplicado', 0)
        self.descuento_spin.setValue(float(descuento))
        
        observaciones = datos.get('observaciones', '')
        self.observaciones_text.setPlainText(observaciones)
        
        # Mostrar pestañas adicionales en modo edición/lectura
        if self.modo in ["editar", "lectura"]:
            self.tab_widget.setVisible(True)
            self.cargar_historial_pagos()
            self.cargar_documentos()
    
    def guardar_datos(self):
        """Guardar los datos de la inscripción (llamado por BaseOverlay)"""
        try:
            # **DIAGNÓSTICO**
            datos = self.obtener_datos()  # Obtener primero para diagnóstico
            self.diagnosticar_creacion(datos)
            
            # Validar formulario
            valido, errores = self.validar_formulario()
            
            if not valido:
                mensaje_error = "Por favor corrija los siguientes errores:\n\n- " + "\n- ".join(errores)
                self.mostrar_mensaje("Validación", mensaje_error, "warning")
                return
            
            # Obtener datos del formulario
            datos = self.obtener_datos()
            
            logger.info(f"🔵 Guardando inscripción - Modo: {self.modo}")
            logger.info(f"   Estudiante ID: {datos.get('estudiante_id')}")
            logger.info(f"   Programa ID: {datos.get('programa_id')}")
            logger.info(f"   Descuento: {datos.get('descuento_aplicado')}")
            logger.info(f"   Estado: {datos.get('estado')}")
            
            if self.modo == "nuevo":
                # **VERIFICAR DISPONIBILIDAD ANTES DE CREAR**
                try:
                    disponibilidad = InscripcionModel.verificar_disponibilidad_programa(datos['programa_id'])
                    
                    if not disponibilidad.get('success'):
                        self.mostrar_mensaje(
                            "Error de verificación", 
                            f"No se pudo verificar disponibilidad: {disponibilidad.get('message', 'Error desconocido')}", 
                            "error"
                        )
                        return
                    
                    if not disponibilidad['data']['disponible']:
                        self.mostrar_mensaje(
                            "Sin cupos disponibles", 
                            f"El programa no está disponible: {disponibilidad['data']['mensaje']}", 
                            "error"
                        )
                        return
                
                except Exception as e:
                    logger.error(f"Error verificando disponibilidad: {e}")
                    self.mostrar_mensaje(
                        "Error de sistema", 
                        f"No se pudo verificar disponibilidad del programa: {str(e)}", 
                        "error"
                    )
                    return
            
            if self.modo == "nuevo":
                # **CORRECCIÓN: Usar fecha_inscripcion de los datos obtenidos**
                fecha_inscripcion_str = datos.get('fecha_inscripcion')
                
                # Convertir string a date si es necesario
                fecha_inscripcion_date = None
                if fecha_inscripcion_str:
                    try:
                        from datetime import datetime
                        fecha_inscripcion_date = datetime.strptime(fecha_inscripcion_str, '%Y-%m-%d').date()
                    except Exception as e:
                        logger.warning(f"No se pudo parsear fecha {fecha_inscripcion_str}: {e}")
                        # Usar None para que el stored procedure use CURRENT_DATE
                    
                # **LLAMAR CORRECTAMENTE A InscripcionModel.crear_inscripcion**
                try:
                    resultado = InscripcionModel.crear_inscripcion(
                        estudiante_id=datos['estudiante_id'],
                        programa_id=datos['programa_id'],
                        descuento_aplicado=datos['descuento_aplicado'],
                        observaciones=datos['observaciones'] or None,
                        fecha_inscripcion=fecha_inscripcion_date  # Puede ser None
                    )
                    
                    logger.info(f"🔵 Resultado de crear_inscripcion: {resultado}")
                    
                    # Verificar resultado - manejar diferentes estructuras de respuesta
                    exito = False
                    mensaje_resultado = ""
                    datos_resultado = None
                    
                    if isinstance(resultado, dict):
                        if resultado.get('exito') is not None:
                            exito = resultado.get('exito', False)
                            mensaje_resultado = resultado.get('mensaje', '')
                            datos_resultado = resultado.get('data')
                        elif resultado.get('success') is not None:
                            exito = resultado.get('success', False)
                            mensaje_resultado = resultado.get('message', resultado.get('mensaje', ''))
                            datos_resultado = resultado.get('data')
                        else:
                            # Asumir éxito si no hay campo de error explícito
                            exito = True
                            mensaje_resultado = 'Inscripción creada exitosamente'
                            datos_resultado = resultado
                    else:
                        # Resultado no es un dict, asumir éxito
                        exito = True
                        mensaje_resultado = 'Inscripción creada exitosamente'
                        datos_resultado = resultado
                    
                    if exito:
                        mensaje_final = mensaje_resultado or 'Inscripción creada exitosamente.'
                        
                        # Emitir señal
                        if datos_resultado:
                            self.inscripcion_creada.emit(datos_resultado)
                        else:
                            self.inscripcion_creada.emit(datos)
                        
                        self.mostrar_mensaje("✅ Éxito", mensaje_final, "success")
                        
                        # Cerrar overlay después de 1 segundo
                        QTimer.singleShot(1000, self.close_overlay)
                    
                    else:
                        mensaje_error = mensaje_resultado or 'No se pudo crear la inscripción.'
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
                        nuevo_descuento=datos.get('descuento_aplicado'),
                        nuevas_observaciones=datos.get('observaciones') or None
                    )
                    
                    logger.info(f"🔵 Resultado de actualizar_inscripcion: {resultado}")
                    
                    # Verificar resultado - manejar diferentes estructuras
                    exito = False
                    mensaje_resultado = ""
                    
                    if isinstance(resultado, dict):
                        if resultado.get('exito') is not None:
                            exito = resultado.get('exito', False)
                            mensaje_resultado = resultado.get('mensaje', '')
                        elif resultado.get('success') is not None:
                            exito = resultado.get('success', False)
                            mensaje_resultado = resultado.get('message', resultado.get('mensaje', ''))
                        else:
                            exito = True
                            mensaje_resultado = 'Inscripción actualizada exitosamente'
                    else:
                        exito = True
                        mensaje_resultado = 'Inscripción actualizada exitosamente'
                    
                    if exito:
                        self.mostrar_mensaje("✅ Éxito", mensaje_resultado or "Inscripción actualizada exitosamente", "success")
                        self.inscripcion_actualizada.emit(datos)
                        QTimer.singleShot(1000, self.close_overlay)
                    else:
                        self.mostrar_mensaje("Error", mensaje_resultado or 'Error al actualizar', "error")
                    
                except Exception as e:
                    logger.error(f"Error actualizando inscripción: {e}", exc_info=True)
                    self.mostrar_mensaje("Error", f"Error al actualizar: {str(e)}", "error")
            
        except Exception as e:
            logger.error(f"Error general en guardar_datos: {e}", exc_info=True)
            self.mostrar_mensaje("Error", f"Error al guardar: {str(e)}", "error")
    
    def close_overlay(self):
        """Cerrar el overlay"""
        self.close()
        if hasattr(self, 'overlay_closed'):
            self.overlay_closed.emit()
    
    # ===== MÉTODOS ADICIONALES =====
    
    def cargar_informacion_pagos(self):
        """Cargar información de pagos realizados"""
        if not self.estudiante_id or not self.programa_id:
            return
        
        try:
            # Usar el modelo de estudiante para obtener información financiera
            pagos = EstudianteModel.obtener_pagos_estudiante_programa(
                estudiante_id=self.estudiante_id,
                programa_id=self.programa_id
            )
            
            if pagos:
                total_pagado = sum(pago.get('monto_final', 0) for pago in pagos)
            else:
                total_pagado = 0
            
            # Calcular saldo pendiente
            costo_final_str = self.costo_final_label.text().replace('Bs', '').strip()
            costo_final = float(costo_final_str) if costo_final_str else 0
            saldo_pendiente = max(0, costo_final - total_pagado)
            
            # Calcular porcentaje
            porcentaje = (total_pagado / costo_final * 100) if costo_final > 0 else 0
            
            # Actualizar interfaz
            self.total_pagado_label.setText(f"{total_pagado:.2f} Bs")
            self.saldo_pendiente_label.setText(f"{saldo_pendiente:.2f} Bs")
            self.porcentaje_pagado_label.setText(f"{porcentaje:.1f}%")
            self.progress_bar.setValue(int(porcentaje))
            
        except Exception as e:
            logger.error(f"Error cargando información de pagos: {e}")
    
    def cargar_historial_pagos(self):
        """Cargar historial de pagos en la tabla"""
        if not self.estudiante_id or not self.programa_id:
            return
        
        try:
            pagos = EstudianteModel.obtener_pagos_estudiante_programa(
                estudiante_id=self.estudiante_id,
                programa_id=self.programa_id
            )
            
            self.pagos_table.setRowCount(len(pagos))
            
            for i, pago in enumerate(pagos):
                # ID
                self.pagos_table.setItem(i, 0, QTableWidgetItem(str(pago.get('transaccion_id', ''))))
                
                # Fecha
                fecha = pago.get('fecha_pago', '')
                self.pagos_table.setItem(i, 1, QTableWidgetItem(fecha[:10] if fecha else ''))
                
                # Forma de pago
                self.pagos_table.setItem(i, 2, QTableWidgetItem(pago.get('forma_pago', '')))
                
                # Monto
                monto = pago.get('monto_final', 0)
                self.pagos_table.setItem(i, 3, QTableWidgetItem(f"{monto:.2f} Bs"))
                
                # Comprobante
                self.pagos_table.setItem(i, 4, QTableWidgetItem(pago.get('numero_comprobante', '')))
                
                # Estado
                estado = pago.get('estado_transaccion', '')
                estado_item = QTableWidgetItem(estado)
                self.pagos_table.setItem(i, 5, estado_item)
                
                # Color según estado
                if estado_item:
                    if estado == 'CONFIRMADO':
                        estado_item.setForeground(QBrush(QColor("#27ae60")))
                    elif estado == 'PENDIENTE':
                        estado_item.setForeground(QBrush(QColor("#f39c12")))
                    elif estado == 'ANULADO':
                        estado_item.setForeground(QBrush(QColor("#e74c3c")))
                
                # Observaciones
                self.pagos_table.setItem(i, 6, QTableWidgetItem(pago.get('observaciones', '')))
            
            self.pagos_table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error cargando historial de pagos: {e}")
    
    def cargar_documentos(self):
        """Cargar documentos adjuntos"""
        # TODO: Implementar carga de documentos desde base de datos
        self.documentos_list.clear()
    
    def registrar_nuevo_pago(self):
        """Registrar nuevo pago para la inscripción"""
        # TODO: Implementar diálogo para registrar nuevo pago
        self.mostrar_mensaje("Información", "Funcionalidad en desarrollo", "info")
    
    def subir_documento(self):
        """Subir nuevo documento"""
        # TODO: Implementar diálogo para subir documento
        self.mostrar_mensaje("Información", "Funcionalidad en desarrollo", "info")
    
    def habilitar_botones_documentos(self):
        """Habilitar/deshabilitar botones de documentos según selección"""
        seleccionado = self.documentos_list.currentItem() is not None
        self.btn_ver_documento.setEnabled(seleccionado)
        self.btn_descargar_documento.setEnabled(seleccionado)
        self.btn_eliminar_documento.setEnabled(seleccionado)
    
    def ver_documento(self):
        """Ver documento seleccionado"""
        # TODO: Implementar visualización de documento
        self.mostrar_mensaje("Información", "Funcionalidad en desarrollo", "info")
    
    def descargar_documento(self):
        """Descargar documento seleccionado"""
        # TODO: Implementar descarga de documento
        self.mostrar_mensaje("Información", "Funcionalidad en desarrollo", "info")
    
    def eliminar_documento(self):
        """Eliminar documento seleccionado"""
        # TODO: Implementar eliminación de documento
        self.mostrar_mensaje("Información", "Funcionalidad en desarrollo", "info")
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo", inscripcion_id=None,
                    estudiante_id: Optional[int] = None, programa_id: Optional[int] = None):
        """Mostrar overlay con configuración específica"""
        self.solo_lectura = solo_lectura
        self.modo = modo
        
        try:
            # Configurar título según modo
            titulo = ""
            if modo == "nuevo":
                titulo = "🎓 Nueva Inscripción"
            elif modo == "editar" and inscripcion_id:
                titulo = f"✏️ Editar Inscripción - ID: {inscripcion_id}"
            elif modo == "lectura" and inscripcion_id:
                titulo = f"👁️ Ver Inscripción - ID: {inscripcion_id}"
            else:
                titulo = "🎓 Gestión de Inscripción"
                
            self.set_titulo(titulo)
            
            # Cargar datos si se proporcionan
            if datos:
                self.cargar_datos(datos)
            elif inscripcion_id and not datos:
                # Cargar datos desde la base de datos
                self.cargar_datos_desde_db(inscripcion_id)
            elif modo == "nuevo":
                self.clear_form()
                
                # Si se proporcionan IDs de estudiante o programa, cargarlos automáticamente
                if estudiante_id:
                    self.cargar_estudiante(estudiante_id)
                
                if programa_id:
                    # Usar timer para cargar programa después de que la UI esté lista
                    QTimer.singleShot(100, lambda: self.cargar_programa(programa_id))
            
            # Configurar botones según modo
            if modo == "lectura" or solo_lectura:
                self.btn_guardar.setText("👈 VOLVER")
                self.btn_guardar.setVisible(False)
                self.btn_cancelar.setText("👈 CERRAR")
            elif modo == "editar":
                self.btn_guardar.setText("💾 ACTUALIZAR INSCRIPCIÓN")
                self.btn_guardar.setVisible(True)
            else:  # modo == "nuevo"
                self.btn_guardar.setText("💾 GUARDAR INSCRIPCIÓN")
                self.btn_guardar.setVisible(True)
                
            # Habilitar/deshabilitar controles según modo
            es_solo_lectura = solo_lectura or modo == "lectura"
            
            # Controles de búsqueda (siempre habilitados en modo nuevo)
            if modo == "nuevo":
                self.estudiante_search_input.setEnabled(True)
                self.btn_buscar_estudiante.setEnabled(True)
                self.programa_search_input.setEnabled(True)
                self.btn_buscar_programa.setEnabled(True)
            else:
                self.estudiante_search_input.setEnabled(False)
                self.btn_buscar_estudiante.setEnabled(False)
                self.programa_search_input.setEnabled(False)
                self.btn_buscar_programa.setEnabled(False)
            
            # Controles de formulario
            self.fecha_inscripcion_date.setEnabled(not es_solo_lectura)
            self.estado_combo.setEnabled(not es_solo_lectura)
            self.descuento_spin.setEnabled(not es_solo_lectura)
            self.observaciones_text.setReadOnly(es_solo_lectura)
            
            # Botones adicionales
            if modo == "nuevo":
                self.btn_cambiar_estudiante.setEnabled(True)
                self.btn_cambiar_programa.setEnabled(True)
            else:
                self.btn_cambiar_estudiante.setEnabled(False)
                self.btn_cambiar_programa.setEnabled(False)
            
            # Botones en pestañas
            self.btn_nuevo_pago.setEnabled(not es_solo_lectura)
            self.btn_subir_documento.setEnabled(not es_solo_lectura)
            
            # Llamar al método base
            super().show_form(es_solo_lectura)
            
            logger.info(f"✅ Overlay de inscripción mostrado - Modo: {modo}, ID: {self.inscripcion_id}, Estudiante ID: {estudiante_id}, Programa ID: {programa_id}")
            
        except Exception as e:
            logger.error(f"❌ Error en show_form: {e}")
            super().show_form(solo_lectura)
    
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
    
    def diagnosticar_creacion(self, datos):
        """Método de diagnóstico para creación de inscripción"""
        logger.info("🔍 DIAGNÓSTICO DE CREACIÓN DE INSCRIPCIÓN")
        logger.info(f"   Modo: {self.modo}")
        logger.info(f"   Estudiante ID: {datos.get('estudiante_id')}")
        logger.info(f"   Programa ID: {datos.get('programa_id')}")
        logger.info(f"   Descuento: {datos.get('descuento_aplicado')}")
        logger.info(f"   Observaciones: {datos.get('observaciones')}")
        logger.info(f"   Fecha inscripción: {datos.get('fecha_inscripcion')}")

        # Verificar datos del programa
        if hasattr(self, 'programa_data') and self.programa_data:
            programa = self.programa_data
            logger.info(f"   Programa cupos_maximos: {programa.get('cupos_maximos')}")
            logger.info(f"   Programa cupos_inscritos: {programa.get('cupos_inscritos')}")
            logger.info(f"   Programa estado: {programa.get('estado')}")

        # Verificar disponibilidad
        try:
            disponibilidad = InscripcionModel.verificar_disponibilidad_programa(datos['programa_id'])
            logger.info(f"   Disponibilidad: {disponibilidad}")
        except Exception as e:
            logger.error(f"   Error verificando disponibilidad: {e}")
    
    def diagnosticar_estado(self):
        """Mostrar estado actual del formulario"""
        estado = f"""
        🔍 DIAGNÓSTICO DE ESTADO - InscripcionOverlay
        ============================================
        Modo: {self.modo}

        ESTUDIANTE:
            Encontrado: {self.estudiante_encontrado}
            ID: {self.estudiante_id}
            Nombre: {getattr(self, 'estudiante_nombre_label', 'N/A').strip() if hasattr(self, 'estudiante_nombre_label') else 'N/A'}

        PROGRAMA:
            Encontrado: {self.programa_encontrado}
            ID: {self.programa_id}
            Código: {getattr(self, 'programa_codigo_label', 'N/A').strip() if hasattr(self, 'programa_codigo_label') else 'N/A'}
            Disponible: {getattr(self, 'programa_disponible', 'No definido')}
            Estado: {getattr(self, 'programa_estado_label', 'N/A').strip() if hasattr(self, 'programa_estado_label') else 'N/A'}

        INTERFAZ:
            Grupo info programa visible: {self.grupo_info_programa.isVisible() if hasattr(self, 'grupo_info_programa') else 'N/A'}
            Grupo detalles visible: {self.grupo_detalles_inscripcion.isVisible() if hasattr(self, 'grupo_detalles_inscripcion') else 'N/A'}
        """

        print(estado)
        logger.info(estado)