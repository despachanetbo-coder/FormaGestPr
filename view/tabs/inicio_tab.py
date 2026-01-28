# Archivo: view/tabs/inicio_tab.py
# -*- coding: utf-8 -*-
"""
Descripción: Pestaña de inicio/dashboard principal de la aplicación.
Gestiona estudiantes, docentes y programas académicos con botones de acción
contextuales, paginación y operaciones CRUD mejoradas.
Autor: Sistema FormaGestPro
Versión: 2.0.0 (Rediseñada con botones contextuales)
"""

import logging
from typing import Optional, Dict, List, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction
from PySide6.QtWidgets import (
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QGridLayout,
    QFrame, QMessageBox, QMenu, QWidget, QAbstractItemView
)

from .base_tab import BaseTab
from model.programa_model import ProgramaModel
from model.docente_model import DocenteModel
from model.estudiante_model import EstudianteModel
from config.database import Database

# Configurar logging
logger = logging.getLogger(__name__)


class InicioTab(BaseTab):
    """
    Pestaña de inicio/dashboard principal con botones de acción contextuales.
    
    Características:
    - Tres formularios de búsqueda independientes
    - Tabla dinámica con paginación
    - Botones de acción específicos por vista (estudiantes, docentes, programas)
    - Menú contextual adaptativo
    - Acceso rápido a InscripcionOverlay con parámetros pre-cargados
    """
    
    # Constantes de configuración
    PAGE_SIZE = 10  # Registros por página
    VIEW_TYPES = ["estudiantes", "docentes", "programas"]
    
    def __init__(self, user_data=None, parent=None):
        """Inicializar la pestaña de inicio con configuración básica."""
        super().__init__(
            tab_id="inicio_tab", 
            tab_name="🏠 Inicio",
            parent=parent
        )
        
        self.user_data = user_data or {}
        
        # Estado inicial
        self.current_view = "estudiantes"  # Vista activa
        self.main_window = None
        self.current_data = []
        self.current_filters = {}
        self.search_inputs = {}
        
        # Configuración de paginación
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        # Inicializar componentes
        self.table = QTableWidget()
        self.action_buttons_container = QVBoxLayout()  # Inicializar como QVBoxLayout
        
        # Configurar el header
        self.set_header_title("🏠 GESTIÓN DE REGISTROS")
        self.set_header_subtitle("Gestión de Estudiantes, Docentes y Programas Académicos")
        
        nombre_usuario = self._get_user_display_name()
        rol_usuario = self.user_data.get('rol', 'Usuario')
        self.set_user_info(nombre_usuario, rol_usuario)
        
        self._init_ui()
    
    def _get_user_display_name(self) -> str:
        """Obtener nombre de usuario para mostrar."""
        return f"{self.user_data.get('nombres', 'Usuario')} {self.user_data.get('apellido_paterno', '')}"
    
    # =========================================================================
    # SECCIÓN 1: INICIALIZACIÓN Y CONFIGURACIÓN DE UI
    # =========================================================================
    
    def _init_ui(self) -> None:
        """Configurar la interfaz de usuario principal."""
        self.clear_content()
        self._setup_search_forms()
        self._setup_data_section()
        self._load_initial_data()
    
    def _setup_search_forms(self) -> None:
        """Configurar los tres formularios de búsqueda en una fila horizontal."""
        search_row = QHBoxLayout()
        
        # Formulario de estudiantes
        estudiantes_box = self._create_search_form(
            "🔍 BUSCAR ESTUDIANTES",
            "Carnet:", "Ej: 1234567", "BE",
            "Nombre:", "Ej: Juan Pérez",
            ["BE", "CB", "CH", "LP", "OR", "PD", "PT", "SC", "TJ", "EX"],
            self._on_search_estudiantes,
            self._on_show_all_estudiantes,
            self._on_new_estudiante
        )
        search_row.addWidget(estudiantes_box, stretch=4)
        
        # Separador visual
        search_row.addWidget(self._create_vertical_separator())
        
        # Formulario de docentes
        docentes_box = self._create_search_form(
            "👨‍🏫 BUSCAR DOCENTES",
            "Carnet:", "Ej: 8765432", "CB",
            "Nombre:", "Ej: María López",
            ["BE", "CB", "CH", "LP", "OR", "PD", "PT", "SC", "TJ", "EX"],
            self._on_search_docentes,
            self._on_show_all_docentes,
            self._on_new_docente
        )
        search_row.addWidget(docentes_box, stretch=4)
        
        # Separador visual
        search_row.addWidget(self._create_vertical_separator())
        
        # Formulario de programas
        programas_box = self._create_programas_form()
        search_row.addWidget(programas_box, stretch=4)
        
        self.add_layout(search_row)
        self.add_spacing(20)
    
    def _setup_data_section(self) -> None:
        """Configurar sección de datos (tabla + botones de acción)."""
        data_row = QHBoxLayout()
        
        # Panel izquierdo: Tabla y paginación (10/12 del ancho)
        left_panel = QVBoxLayout()
        self._setup_table_widget()
        left_panel.addWidget(self.table)
        left_panel.addLayout(self._setup_pagination_controls())
        
        # Separador vertical
        data_row.addLayout(left_panel, stretch=10)
        data_row.addWidget(self._create_vertical_separator())
        
        # Panel derecho: Botones de acción contextuales (2/12 del ancho)
        right_panel = self._setup_action_buttons()
        data_row.addLayout(right_panel, stretch=2)
        
        self.add_layout(data_row, stretch=1)
    
    def _setup_table_widget(self) -> None:
        """Configurar widget de tabla con comportamiento de selección."""
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Conectar señales
        self.table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self.table.doubleClicked.connect(self._on_table_double_click)
        
        # Configurar menú contextual
        self._setup_context_menu()
    
    def _setup_pagination_controls(self) -> QHBoxLayout:
        """Configurar controles de paginación."""
        pagination = QHBoxLayout()
        
        # Crear botones
        self.first_page_btn = QPushButton("⏮ Primera")
        self.prev_page_btn = QPushButton("◀ Anterior")
        self.page_label = QLabel("Página 1 de 1")
        self.next_page_btn = QPushButton("Siguiente ▶")
        self.last_page_btn = QPushButton("Última ⏭")
        
        # Conectar botones
        self.first_page_btn.clicked.connect(lambda: self._change_page("first"))
        self.prev_page_btn.clicked.connect(lambda: self._change_page("prev"))
        self.next_page_btn.clicked.connect(lambda: self._change_page("next"))
        self.last_page_btn.clicked.connect(lambda: self._change_page("last"))
        
        # Agregar al layout
        pagination.addWidget(self.first_page_btn)
        pagination.addWidget(self.prev_page_btn)
        pagination.addStretch(1)
        pagination.addWidget(self.page_label)
        pagination.addStretch(1)
        pagination.addWidget(self.next_page_btn)
        pagination.addWidget(self.last_page_btn)
        
        return pagination
    
    def _setup_action_buttons(self) -> QVBoxLayout:
        """Configurar panel de botones de acción personalizados por vista."""
        right_panel = QVBoxLayout()
        
        # Título de la sección
        action_title = QLabel("ACCIONES")
        action_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        action_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_title.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        right_panel.addWidget(action_title)
        
        # Crear contenedor para botones (se actualizará dinámicamente)
        self.action_buttons_container = QVBoxLayout()
        right_panel.addLayout(self.action_buttons_container)
        
        right_panel.addStretch(1)
        
        # Configurar botones iniciales (para estudiantes por defecto)
        self._setup_action_buttons_for_estudiantes()
        
        return right_panel
    
    def _setup_action_buttons_for_estudiantes(self):
        """Configurar botones específicos para vista de estudiantes."""
        self._clear_action_buttons()
        
        # Botones para estudiantes
        buttons_config = [
            ("👤 Ver Perfil", self._on_view_details, False, "btn_view_profile"),
            ("📋 Historial Académico", self._on_view_student_history, False, "btn_history"),
            ("🎓 Nueva Inscripción", self._on_new_enrollment_student, False, "btn_new_enrollment"),
            ("💰 Ver Pagos", self._on_view_student_payments, False, "btn_view_payments"),
            ("✏️ Editar", self._on_edit, False, "btn_edit"),
            ("🗑️ Desactivar", self._on_deactivate_student, False, "btn_deactivate"),
            ("📧 Enviar Email", self._on_email_student, False, "btn_email"),
            ("🔄 Actualizar Lista", self._on_refresh, True, "btn_refresh")
        ]
        
        for text, slot, enabled, btn_id in buttons_config:
            button = QPushButton(text)
            button.clicked.connect(slot)
            button.setEnabled(enabled)
            button.setObjectName(btn_id)
            button.setMinimumHeight(35)
            self.action_buttons_container.addWidget(button)
    
    def _setup_action_buttons_for_docentes(self):
        """Configurar botones específicos para vista de docentes."""
        self._clear_action_buttons()
        
        # Botones para docentes
        buttons_config = [
            ("👨‍🏫 Ver Perfil", self._on_view_details, False, "btn_view_docente"),
            ("📄 Ver CV", self._on_view_docente_cv, False, "btn_view_cv"),
            ("✏️ Editar", self._on_edit, False, "btn_edit_docente"),
            ("🗑️ Desactivar", self._on_deactivate_docente, False, "btn_deactivate_docente"),
            ("📚 Asignar a Programa", self._on_assign_docente_program, False, "btn_assign"),
            ("🔄 Actualizar Lista", self._on_refresh, True, "btn_refresh_docente")
        ]
        
        for text, slot, enabled, btn_id in buttons_config:
            button = QPushButton(text)
            button.clicked.connect(slot)
            button.setEnabled(enabled)
            button.setObjectName(btn_id)
            button.setMinimumHeight(35)
            self.action_buttons_container.addWidget(button)
    
    def _setup_action_buttons_for_programas(self):
        """Configurar botones específicos para vista de programas."""
        self._clear_action_buttons()
        
        # Botones para programas
        buttons_config = [
            ("📚 Ver Detalles", self._on_view_details, False, "btn_view_program"),
            ("👥 Ver Inscritos", self._on_view_program_enrolled, False, "btn_view_enrolled"),
            ("🎓 Nueva Inscripción", self._on_new_enrollment_program, False, "btn_new_enrollment_program"),
            ("💰 Ver Pagos", self._on_view_program_payments, False, "btn_payments"),
            ("✏️ Editar", self._on_edit, False, "btn_edit_program"),
            ("📊 Estadísticas", self._on_program_stats, False, "btn_stats"),
            ("🗑️ Cancelar", self._on_cancel_program, False, "btn_cancel"),
            ("🔄 Actualizar Lista", self._on_refresh, True, "btn_refresh_program")
        ]
        
        for text, slot, enabled, btn_id in buttons_config:
            button = QPushButton(text)
            button.clicked.connect(slot)
            button.setEnabled(enabled)
            button.setObjectName(btn_id)
            button.setMinimumHeight(35)
            self.action_buttons_container.addWidget(button)
    
    def _clear_action_buttons(self):
        """Limpiar todos los botones de acción existentes."""
        if self.action_buttons_container:
            while self.action_buttons_container.count():
                item = self.action_buttons_container.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
    
    def _update_action_buttons_based_on_view(self):
        """Actualizar botones de acción según la vista actual."""
        if self.current_view == "estudiantes":
            self._setup_action_buttons_for_estudiantes()
        elif self.current_view == "docentes":
            self._setup_action_buttons_for_docentes()
        elif self.current_view == "programas":
            self._setup_action_buttons_for_programas()
        
        # Actualizar estado de botones según selección
        self._on_table_selection_changed()
    
    def _load_initial_data(self) -> None:
        """Cargar datos iniciales al iniciar la pestaña."""
        self._configure_table_for_estudiantes()
        self._load_estudiantes_page(0)
    
    # =========================================================================
    # SECCIÓN 2: CREACIÓN DE COMPONENTES DE UI
    # =========================================================================
    
    def _create_search_form(self, title: str, label1: str, placeholder1: str,
        expedicion_default: str, label2: str, placeholder2: str,
        expediciones: list, search_slot, all_slot, new_slot) -> QGroupBox:
        """Crear un formulario de búsqueda genérico reutilizable."""
        box = QGroupBox(title)
        box.setStyleSheet(self._get_groupbox_style("#1976D2"))
        
        layout = QVBoxLayout(box)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)
        
        # Campo 1: Carnet/CI
        input1, combo = self._create_carnet_field(
            label1, placeholder1, expedicion_default, expediciones, layout
        )
        
        # Campo 2: Nombre
        input2 = self._create_text_field(label2, placeholder2, layout)
        
        # Botones
        self._create_form_buttons(layout, search_slot, all_slot, new_slot)
        
        # Almacenar referencias
        key = title.lower().replace(" ", "_").replace("🔍_", "").replace("👨‍🏫_", "").replace("🎓_", "")
        self.search_inputs.update({
            f"{key}_input1": input1,
            f"{key}_combo": combo,
            f"{key}_input2": input2
        })
        
        return box
    
    def _create_programas_form(self) -> QGroupBox:
        """Crear formulario específico para búsqueda de programas."""
        box = QGroupBox("🎓 BUSCAR PROGRAMAS")
        box.setStyleSheet(self._get_groupbox_style("#388E3C"))
        
        layout = QVBoxLayout(box)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(10)
        
        # Campo: Programa
        row1 = QHBoxLayout()
        lbl1 = QLabel("Programa:")
        lbl1.setFixedWidth(70)
        self.prog_input = QLineEdit()
        self.prog_input.setPlaceholderText("Ej: Ingeniería o INF-101")
        self.prog_input.returnPressed.connect(self._on_search_programas)
        row1.addWidget(lbl1)
        row1.addWidget(self.prog_input)
        layout.addLayout(row1)
        
        # Combo: Estado
        row2 = QHBoxLayout()
        lbl2 = QLabel("Estado:")
        lbl2.setFixedWidth(70)
        self.prog_combo = QComboBox()
        self.prog_combo.addItems(["Todos", "PLANIFICADO", "EN_CURSO", "FINALIZADO", "CANCELADO"])
        row2.addWidget(lbl2)
        row2.addWidget(self.prog_combo)
        layout.addLayout(row2)
        
        # Botones
        btn_layout = QHBoxLayout()
        
        self.search_prog_btn = QPushButton("🔎 Buscar")
        self.all_prog_btn = QPushButton("📚 Todos")
        self.new_prog_btn = QPushButton("➕ Nuevo")
        
        # Aplicar estilo
        btn_style = self._get_button_style("#388E3C")
        for btn in [self.search_prog_btn, self.all_prog_btn, self.new_prog_btn]:
            btn.setStyleSheet(btn_style)
        
        # Conectar
        self.search_prog_btn.clicked.connect(self._on_search_programas)
        self.all_prog_btn.clicked.connect(self._on_show_all_programas)
        self.new_prog_btn.clicked.connect(self._on_nuevo_programa)
        
        btn_layout.addWidget(self.search_prog_btn)
        btn_layout.addWidget(self.all_prog_btn)
        btn_layout.addWidget(self.new_prog_btn)
        layout.addLayout(btn_layout)
        
        return box
    
    def _create_carnet_field(self, label: str, placeholder: str, default: str,
                            expediciones: list, layout: QVBoxLayout) -> tuple:
        """Crear campo para carnet/CI con combo de expedición."""
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(60)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        
        combo = QComboBox()
        combo.setMaximumWidth(80)
        combo.addItems(expediciones)
        combo.setCurrentText(default)
        
        row.addWidget(lbl)
        row.addWidget(input_field, 1)
        row.addWidget(combo)
        layout.addLayout(row)
        
        return input_field, combo
    
    def _create_text_field(self, label: str, placeholder: str,
        layout: QVBoxLayout) -> QLineEdit:
        """Crear campo de texto simple."""
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setFixedWidth(60)
        
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        
        row.addWidget(lbl)
        row.addWidget(input_field, 1)
        layout.addLayout(row)
        
        return input_field
    
    def _create_form_buttons(self, layout: QVBoxLayout, search_slot,
                            all_slot, new_slot) -> None:
        """Crear botones para formulario."""
        btn_layout = QHBoxLayout()
        
        btn_search = QPushButton("🔎 Buscar")
        btn_all = QPushButton("👥 Todos")
        btn_new = QPushButton("➕ Nuevo")
        
        # Aplicar estilo
        btn_style = self._get_button_style("#1976D2")
        for btn in [btn_search, btn_all, btn_new]:
            btn.setStyleSheet(btn_style)
        
        # Conectar
        btn_search.clicked.connect(search_slot)
        btn_all.clicked.connect(all_slot)
        btn_new.clicked.connect(new_slot)
        
        btn_layout.addWidget(btn_search)
        btn_layout.addWidget(btn_all)
        btn_layout.addWidget(btn_new)
        layout.addLayout(btn_layout)
    
    def _create_vertical_separator(self) -> QFrame:
        """Crear separador vertical."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("background-color: #E0E0E0;")
        return sep
    
    def _get_groupbox_style(self, color: str) -> str:
        """Obtener estilo CSS para QGroupBox."""
        return f"""
            QGroupBox {{
                font-weight: bold;
                border: 2px solid {color};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: #F8F9FA;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 10px 0 10px;
                color: {color};
            }}
        """
    
    def _get_button_style(self, hover_color: str) -> str:
        """Obtener estilo CSS para botones."""
        return f"""
            QPushButton {{
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {hover_color}20;
            }}
        """
    
    # =========================================================================
    # SECCIÓN 3: CONFIGURACIÓN DE TABLA
    # =========================================================================
    
    def _configure_table_for_estudiantes(self) -> None:
        """Configurar tabla para mostrar estudiantes."""
        columnas = [
            "ID", "CARNET", "NOMBRE COMPLETO", "EMAIL",
            "TELÉFONO", "ESTADO", "FECHA REGISTRO"
        ]
        self._setup_table_columns(columnas, [2])
    
    def _configure_table_for_docentes(self) -> None:
        """Configurar tabla para mostrar docentes."""
        columnas = [
            "ID", "CARNET", "NOMBRE COMPLETO", "EMAIL",
            "TELÉFONO", "ESPECIALIDAD", "TITULO", "ESTADO", "FECHA REGISTRO"
        ]
        self._setup_table_columns(columnas, [2])
    
    def _configure_table_for_programas(self) -> None:
        """Configurar tabla para mostrar programas."""
        columnas = [
            "ID", "CÓDIGO", "NOMBRE", "DURACIÓN (meses)",
            "HORAS", "ESTADO", "COSTO TOTAL", "CUPOS",
            "FECHA INICIO", "FECHA FIN"
        ]
        self._setup_table_columns(columnas, [2])
    
    def _setup_table_columns(self, columns: list, stretch_columns: list) -> None:
        """Configurar columnas de la tabla."""
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        header = self.table.horizontalHeader()
        for i in range(len(columns)):
            if i in stretch_columns:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        self.table.setRowCount(0)
        self.current_data = []
    
    # =========================================================================
    # SECCIÓN 4: MANEJO DE EVENTOS Y SELECCIÓN
    # =========================================================================
    
    def _on_table_selection_changed(self) -> None:
        """Habilitar/deshabilitar botones según selección de tabla y vista actual."""
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        
        if not self.action_buttons_container:
            return
        
        # Mapeo de botones por vista (excluyendo botón de actualizar)
        button_configs = {
            "estudiantes": [
                "btn_view_profile", "btn_history", "btn_new_enrollment",
                "btn_view_payments", "btn_edit", "btn_deactivate",
                "btn_email"
            ],
            "docentes": [
                "btn_view_docente", "btn_view_cv", "btn_edit_docente",
                "btn_deactivate_docente", "btn_assign"
            ],
            "programas": [
                "btn_view_program", "btn_view_enrolled", "btn_new_enrollment_program",
                "btn_payments", "btn_edit_program", "btn_stats",
                "btn_cancel"
            ]
        }
        
        # Obtener botones específicos para la vista actual
        if self.current_view in button_configs:
            button_names = button_configs[self.current_view]
            for btn_name in button_names:
                # Buscar botón por nombre de objeto
                for i in range(self.action_buttons_container.count()):
                    widget = self.action_buttons_container.itemAt(i).widget()
                    if widget and widget.objectName() == btn_name:
                        widget.setEnabled(has_selection)
                        break
        
        # Botón de actualizar siempre habilitado
        for i in range(self.action_buttons_container.count()):
            widget = self.action_buttons_container.itemAt(i).widget()
            if widget and widget.objectName() in ["btn_refresh", "btn_refresh_docente", "btn_refresh_program"]:
                widget.setEnabled(True)
                break
    
    def _on_table_double_click(self, index) -> None:
        """Manejador para doble clic en tabla (ver detalles)."""
        self._on_view_details()
    
    def _setup_context_menu(self) -> None:
        """Configurar menú contextual para la tabla."""
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
    
    def _show_context_menu(self, position) -> None:
        """Mostrar menú contextual en la tabla."""
        index = self.table.indexAt(position)
        if not index.isValid():
            return
    
        menu = QMenu(self)
        
        # Función auxiliar para crear acciones
        def add_menu_action(text, slot):
            action = QAction(text, self)
            action.triggered.connect(slot)
            menu.addAction(action)
            return action
        
        # Acciones según vista actual
        if self.current_view == "estudiantes":
            add_menu_action("👤 Ver Perfil", self._on_view_details)
            add_menu_action("📋 Historial Académico", self._on_view_student_history)
            add_menu_action("🎓 Nueva Inscripción", self._on_new_enrollment_student)
            add_menu_action("💰 Ver Pagos", self._on_view_student_payments)
            menu.addSeparator()
            add_menu_action("✏️ Editar", self._on_edit)
            add_menu_action("🗑️ Desactivar", self._on_deactivate_student)
            menu.addSeparator()
            add_menu_action("📧 Enviar Email", self._on_email_student)
            
        elif self.current_view == "docentes":
            add_menu_action("👨‍🏫 Ver Perfil", self._on_view_details)
            add_menu_action("📄 Ver CV", self._on_view_docente_cv)
            menu.addSeparator()
            add_menu_action("✏️ Editar", self._on_edit)
            add_menu_action("🗑️ Desactivar", self._on_deactivate_docente)
            menu.addSeparator()
            add_menu_action("📚 Asignar a Programa", self._on_assign_docente_program)
            
        elif self.current_view == "programas":
            add_menu_action("📚 Ver Detalles", self._on_view_details)
            add_menu_action("👥 Ver Inscritos", self._on_view_program_enrolled)
            add_menu_action("🎓 Nueva Inscripción", self._on_new_enrollment_program)
            add_menu_action("💰 Ver Pagos", self._on_view_program_payments)
            menu.addSeparator()
            add_menu_action("✏️ Editar", self._on_edit)
            add_menu_action("📊 Estadísticas", self._on_program_stats)
            add_menu_action("🗑️ Cancelar", self._on_cancel_program)
    
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    # =========================================================================
    # SECCIÓN 5: MÉTODOS BASE (MANTENER PARA COMPATIBILIDAD)
    # =========================================================================
    
    def _on_view_details(self) -> None:
        """Manejador base: Ver detalles del registro seleccionado."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._mostrar_info("Ver Detalles", "Por favor, seleccione un registro de la tabla para ver detalles.")
            return

        try:
            registro_id = self._obtener_id_registro_seleccionado()
            if not registro_id:
                return

            # Redirigir según vista actual
            if self.current_view == "estudiantes":
                # Para estudiantes, mostrar el historial académico completo
                main_window = self._get_main_window()
                if main_window:
                    try:
                        from view.overlays.inscripcion_overlay import InscripcionOverlay
                        overlay = InscripcionOverlay(main_window)

                        overlay.show_form(
                            solo_lectura=False,
                            modo="historial",
                            estudiante_id=registro_id,
                            programa_id=None
                        )

                        overlay.inscripcion_creada.connect(lambda: self._on_refresh())
                        overlay.inscripcion_actualizada.connect(lambda: self._on_refresh())
                        overlay.overlay_closed.connect(lambda: overlay.deleteLater())

                    except ImportError as e:
                        logger.error(f"No se pudo importar InscripcionOverlay: {e}")
                        # Fallback al método anterior
                        self._abrir_estudiante_overlay(registro_id, "lectura")
                else:
                    self._abrir_estudiante_overlay(registro_id, "lectura")

            elif self.current_view == "docentes":
                self._abrir_docente_overlay(registro_id, "lectura")
            elif self.current_view == "programas":
                self._abrir_programa_overlay(registro_id, "lectura")

        except Exception as e:
            logger.error(f"Error viendo detalles: {e}")
            self._mostrar_error(f"Error al ver detalles: {str(e)}")
    
    def _on_edit(self) -> None:
        """Manejador base: Editar registro seleccionado."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._mostrar_info("Editar", "Por favor, seleccione un registro de la tabla para editar.")
            return
        
        try:
            registro_id = self._obtener_id_registro_seleccionado()
            if not registro_id:
                return
            
            # Redirigir según vista actual
            if self.current_view == "estudiantes":
                self._abrir_estudiante_overlay(registro_id, "editar")
            elif self.current_view == "docentes":
                self._abrir_docente_overlay(registro_id, "editar")
            elif self.current_view == "programas":
                self._abrir_programa_overlay(registro_id, "editar")
                
        except Exception as e:
            logger.error(f"Error editando registro: {e}")
            self._mostrar_error(f"Error al editar: {str(e)}")
    
    def _on_refresh(self) -> None:
        """Manejador: Actualizar datos."""
        logger.debug("Actualizando datos...")
        self.current_page = 1
        self.total_records = 0
        self.total_pages = 1
        
        if self.current_filters:
            # Recargar con filtros activos
            self._load_current_page()
        else:
            # Recargar sin filtros
            if self.current_view == "estudiantes":
                self._load_estudiantes_page(0)
            elif self.current_view == "docentes":
                self._load_docentes_page(0)
            elif self.current_view == "programas":
                self._load_programas_page(0)
    
    # =========================================================================
    # SECCIÓN 6: OPERACIONES DE DATOS - ESTUDIANTES
    # =========================================================================
    
    def _load_estudiantes_page(self, offset: int) -> None:
        """Cargar página de estudiantes."""
        try:
            estudiantes = EstudianteModel.buscar_estudiantes_completo(
                limit=self.PAGE_SIZE,
                offset=offset
            )
            
            # Contar total
            self.total_records = EstudianteModel.contar_estudiantes()
            self.total_pages = max(1, (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
            
            self._mostrar_estudiantes_en_tabla(estudiantes)
            
        except Exception as e:
            logger.error(f"Error cargando página de estudiantes: {e}")
            self._mostrar_error(f"Error al cargar estudiantes: {str(e)}")
    
    def _mostrar_estudiantes_en_tabla(self, estudiantes: List[Dict]) -> None:
        """Mostrar lista de estudiantes en la tabla."""
        self.current_view = "estudiantes"
        self._configure_table_for_estudiantes()
        self._update_action_buttons_based_on_view()
        
        if not estudiantes:
            logger.info("No hay estudiantes para mostrar")
            return
        
        self.table.setRowCount(len(estudiantes))
        
        for row, estudiante in enumerate(estudiantes):
            self._agregar_fila_estudiante(row, estudiante)
        
        self._actualizar_paginacion()
        logger.info(f"{len(estudiantes)} estudiantes mostrados")
    
    def _agregar_fila_estudiante(self, row: int, estudiante: Dict) -> None:
        """Agregar una fila de estudiante a la tabla."""
        # ID
        self._set_table_item(row, 0, str(estudiante.get('id', '')), align_center=True)
        
        # Carnet
        ci_numero = estudiante.get('ci_numero', '')
        ci_expedicion = estudiante.get('ci_expedicion', '')
        carnet = f"{ci_numero}-{ci_expedicion}" if ci_numero and ci_expedicion else f"{ci_numero}"
        self._set_table_item(row, 1, carnet)
        
        # Nombre completo
        nombre_completo = f"{estudiante.get('nombres', '')} {estudiante.get('apellido_paterno', '')} {estudiante.get('apellido_materno', '')}".strip()
        self._set_table_item(row, 2, nombre_completo)
        
        # Email y Teléfono
        self._set_table_item(row, 3, estudiante.get('email', ''))
        self._set_table_item(row, 4, estudiante.get('telefono', ''))
        
        # Estado
        estado = "ACTIVO" if estudiante.get('activo', True) else "INACTIVO"
        estado_item = self._create_status_item(estado)
        self.table.setItem(row, 5, estado_item)
        
        # Fecha registro
        fecha_registro = estudiante.get('fecha_registro', '')
        self._set_table_item(row, 6, str(fecha_registro), align_center=True)
    
    def _buscar_estudiantes_filtrados(self) -> None:
        """Buscar estudiantes con filtros del formulario."""
        try:
            filtros = self._obtener_filtros_estudiantes()
            
            # Reiniciar paginación
            self.current_page = 1
            self.total_records = 0
            self.total_pages = 1
            
            # Guardar filtros para paginación
            self.current_filters = {**filtros, 'view': 'estudiantes'}
            
            # Cargar primera página con filtros
            self._load_estudiantes_filtrados_page(0)
            
        except Exception as e:
            logger.error(f"Error buscando estudiantes filtrados: {e}")
            self._mostrar_error(f"Error al buscar estudiantes: {str(e)}")
    
    def _obtener_filtros_estudiantes(self) -> Dict:
        """Obtener filtros del formulario de estudiantes."""
        key = "buscar_estudiantes"
        ci_input = self.search_inputs.get(f"{key}_input1")
        expedicion_combo = self.search_inputs.get(f"{key}_combo")
        nombre_input = self.search_inputs.get(f"{key}_input2")
        
        ci_text = ci_input.text().strip() if ci_input else ""
        expedicion = expedicion_combo.currentText() if expedicion_combo else "Todos"
        nombre_text = nombre_input.text().strip() if nombre_input else ""
        
        return {
            'ci_numero': ci_text if ci_text else None,
            'ci_expedicion': expedicion if expedicion != "Todos" else None,
            'nombres': nombre_text if nombre_text else None
        }
    
    def _load_estudiantes_filtrados_page(self, offset: int) -> None:
        """Cargar página de estudiantes con filtros aplicados."""
        try:
            filtros = self.current_filters
            
            estudiantes = EstudianteModel.buscar_estudiantes_completo(
                ci_numero=filtros.get('ci_numero'),
                ci_expedicion=filtros.get('ci_expedicion'),
                nombres=filtros.get('nombres'),
                limit=self.PAGE_SIZE,
                offset=offset
            )
            
            if self.total_records == 0:
                self.total_records = self._count_estudiantes_filtrados(filtros)
                self.total_pages = max(1, (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
            
            self._mostrar_estudiantes_en_tabla(estudiantes)
            
        except Exception as e:
            logger.error(f"Error cargando estudiantes filtrados: {e}")
            raise
    
    # =========================================================================
    # SECCIÓN 7: OPERACIONES DE DATOS - DOCENTES
    # =========================================================================
    
    def _load_docentes_page(self, offset: int) -> None:
        """Cargar página de docentes."""
        try:
            docentes = DocenteModel.obtener_todos_docentes(
                limit=self.PAGE_SIZE,
                offset=offset
            )
            
            # Contar total
            if self.total_records == 0:
                self.total_records = DocenteModel.contar_docentes()
                self.total_pages = max(1, (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
            
            self._mostrar_docentes_en_tabla(docentes)
            
        except Exception as e:
            logger.error(f"Error cargando página de docentes: {e}")
            self._mostrar_error(f"Error al cargar docentes: {str(e)}")
    
    def _mostrar_docentes_en_tabla(self, docentes: List[Dict]) -> None:
        """Mostrar docentes en la tabla."""
        self.current_view = "docentes"
        self._configure_table_for_docentes()
        self._update_action_buttons_based_on_view()
        
        if not docentes:
            logger.info("No hay docentes para mostrar")
            return
        
        self.table.setRowCount(len(docentes))
        
        for row, docente in enumerate(docentes):
            self._agregar_fila_docente(row, docente)
        
        self._actualizar_paginacion()
        logger.info(f"{len(docentes)} docentes mostrados")
    
    def _agregar_fila_docente(self, row: int, docente: Dict) -> None:
        """Agregar una fila de docente a la tabla."""
        # ID y Carnet
        self._set_table_item(row, 0, str(docente.get('id', '')), align_center=True)
        ci_numero = docente.get('ci_numero', '')
        ci_expedicion = docente.get('ci_expedicion', '')
        carnet = f"{ci_numero}-{ci_expedicion}" if ci_numero and ci_expedicion else f"{ci_numero}"
        self._set_table_item(row, 1, carnet)
        
        # Nombre completo
        nombre_completo = f"{docente.get('nombres', '')} {docente.get('apellido_paterno', '')} {docente.get('apellido_materno', '')}".strip()
        self._set_table_item(row, 2, nombre_completo)
        
        # Contacto
        self._set_table_item(row, 3, docente.get('email', ''))
        self._set_table_item(row, 4, docente.get('telefono', ''))
        
        # Información profesional
        self._set_table_item(row, 5, docente.get('especialidad', ''))
        self._set_table_item(row, 6, docente.get('titulo_profesional', ''))
        
        # Estado
        estado = "ACTIVO" if docente.get('activo', True) else "INACTIVO"
        estado_item = self._create_status_item(estado)
        self.table.setItem(row, 7, estado_item)
        
        # Fecha registro
        fecha_registro = docente.get('fecha_registro', '')
        self._set_table_item(row, 8, str(fecha_registro), align_center=True)
    
    def _buscar_docentes_filtrados(self) -> None:
        """Buscar docentes con filtros del formulario."""
        try:
            filtros = self._obtener_filtros_docentes()
            
            # Buscar docentes
            docentes = DocenteModel.buscar_docentes_completo(
                ci_numero=filtros.get('ci_numero'),
                ci_expedicion=filtros.get('ci_expedicion'),
                nombres=filtros.get('nombres'),
                limit=100
            )
            
            # Mostrar resultados
            if docentes:
                self._mostrar_docentes_en_tabla(docentes)
                logger.info(f"{len(docentes)} docentes encontrados")
            else:
                self._mostrar_info("Búsqueda de Docentes", 
                    "No se encontraron docentes con los criterios especificados.")
            
        except Exception as e:
            logger.error(f"Error buscando docentes: {e}")
            self._mostrar_error(f"Error al buscar docentes: {str(e)}")
    
    def _obtener_filtros_docentes(self) -> Dict:
        """Obtener filtros del formulario de docentes."""
        key = "buscar_docentes"
        ci_input = self.search_inputs.get(f"{key}_input1")
        expedicion_combo = self.search_inputs.get(f"{key}_combo")
        nombre_input = self.search_inputs.get(f"{key}_input2")
        
        ci_text = ci_input.text().strip() if ci_input else ""
        expedicion = expedicion_combo.currentText() if expedicion_combo else "Todos"
        nombre_text = nombre_input.text().strip() if nombre_input else ""
        
        return {
            'ci_numero': ci_text if ci_text else None,
            'ci_expedicion': expedicion if expedicion != "Todos" else None,
            'nombres': nombre_text if nombre_text else None
        }
    
    # =========================================================================
    # SECCIÓN 8: OPERACIONES DE DATOS - PROGRAMAS
    # =========================================================================
    
    def _load_programas_page(self, offset: int) -> None:
        """Cargar página de programas."""
        try:
            programas = ProgramaModel.buscar_programas(
                limit=self.PAGE_SIZE,
                offset=offset
            )

            # Contar total para paginación
            if self.total_records == 0:
                self.total_records = ProgramaModel.contar_programas()
                self.total_pages = max(1, (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE)

            self._mostrar_programas_en_tabla(programas)

        except Exception as e:
            logger.error(f"Error cargando página de programas: {e}")
            self._mostrar_error(f"Error al cargar programas: {str(e)}")

    def _buscar_programas_filtrados(self) -> None:
        """Buscar programas con filtros del formulario."""
        try:
            codigo, nombre, estado = self._obtener_filtros_programas()

            # Buscar programas con filtros
            programas = ProgramaModel.buscar_programas(
                codigo=codigo,
                nombre=nombre,
                estado=estado,
                limit=100
            )

            # Mostrar resultados
            if programas:
                self._mostrar_programas_en_tabla(programas)
                logger.info(f"{len(programas)} programas encontrados")
            else:
                self._mostrar_info("Búsqueda de Programas",
                    "No se encontraron programas con los criterios especificados.")

        except Exception as e:
            logger.error(f"Error buscando programas: {e}")
            self._mostrar_error(f"Error al buscar programas: {str(e)}")
    
    def _mostrar_programas_en_tabla(self, programas: List[Dict]) -> None:
        """Mostrar programas en la tabla."""
        self.current_view = "programas"
        self._configure_table_for_programas()
        self._update_action_buttons_based_on_view()
        
        if not programas:
            logger.info("No hay programas para mostrar")
            return
        
        self.table.setRowCount(len(programas))
        
        for row, programa in enumerate(programas):
            self._agregar_fila_programa(row, programa)
        
        self._actualizar_paginacion()
        logger.info(f"{len(programas)} programas mostrados")
    
    def _agregar_fila_programa(self, row: int, programa: Dict) -> None:
        """Agregar una fila de programa a la tabla."""
        # ID y Código
        self._set_table_item(row, 0, str(programa.get('id', '')), align_center=True)
        self._set_table_item(row, 1, programa.get('codigo', ''))
        
        # Nombre
        self._set_table_item(row, 2, programa.get('nombre', ''))
        
        # Duración y Horas
        duracion = programa.get('duracion_meses', '')
        horas = programa.get('horas_totales', '')
        self._set_table_item(row, 3, str(duracion) if duracion is not None else '', align_center=True)
        self._set_table_item(row, 4, str(horas) if horas is not None else '', align_center=True)
        
        # Estado
        estado = programa.get('estado', '')
        estado_item = self._create_status_item(estado)
        self.table.setItem(row, 5, estado_item)
        
        # Costo y Cupos
        costo = programa.get('costo_total', 0)
        costo_text = f"${costo:,.2f}" if costo else "$0.00"
        self._set_table_item(row, 6, costo_text, align_right=True)
        
        cupos_max = programa.get('cupos_maximos', '')
        cupos_ins = programa.get('cupos_inscritos', 0)
        cupos_text = f"{cupos_ins}/{cupos_max}" if cupos_max else f"{cupos_ins}/∞"
        self._set_table_item(row, 7, cupos_text, align_center=True)
        
        # Fechas
        fecha_inicio = programa.get('fecha_inicio', '')
        fecha_fin = programa.get('fecha_fin', '')
        self._set_table_item(row, 8, str(fecha_inicio) if fecha_inicio else '', align_center=True)
        self._set_table_item(row, 9, str(fecha_fin) if fecha_fin else '', align_center=True)
    
    def _obtener_filtros_programas(self) -> tuple:
        """Obtener filtros del formulario de programas."""
        texto = self.prog_input.text().strip() if self.prog_input else ""
        estado_ui = self.prog_combo.currentText() if self.prog_combo else "Todos"
        
        # Determinar tipo de búsqueda por texto
        codigo = None
        nombre = None
        if texto:
            if '-' in texto or len(texto) <= 10:
                codigo = texto
            else:
                nombre = texto
        
        # Estado
        estado = None
        if estado_ui != "Todos":
            estado = estado_ui
        
        return codigo, nombre, estado
    
    # =========================================================================
    # SECCIÓN 9: MANEJADORES DE EVENTOS PRINCIPALES
    # =========================================================================
    
    # --- Estudiantes ---
    def _on_search_estudiantes(self) -> None:
        """Manejador: Buscar estudiantes con filtros."""
        logger.debug("Buscando estudiantes con filtros...")
        self._buscar_estudiantes_filtrados()
    
    def _on_show_all_estudiantes(self) -> None:
        """Manejador: Mostrar todos los estudiantes."""
        logger.debug("Mostrando todos los estudiantes...")
        self.current_page = 1
        self.total_records = 0
        self.total_pages = 1
        self.current_filters = {}
        self._load_estudiantes_page(0)
    
    def _on_new_estudiante(self) -> None:
        """Manejador: Nuevo estudiante."""
        logger.debug("Abriendo formulario para nuevo estudiante...")
        main_window = self._get_main_window()
        if main_window:
            metodo = getattr(main_window, 'mostrar_nuevo_estudiante', None)
            if metodo:
                metodo()
    
    # --- Docentes ---
    def _on_search_docentes(self) -> None:
        """Manejador: Buscar docentes con filtros."""
        logger.debug("Buscando docentes con filtros...")
        self._buscar_docentes_filtrados()
    
    def _on_show_all_docentes(self) -> None:
        """Manejador: Mostrar todos los docentes."""
        logger.debug("Mostrando todos los docentes...")
        self.current_page = 1
        self.total_records = 0
        self.total_pages = 1
        self._load_docentes_page(0)
    
    def _on_new_docente(self) -> None:
        """Manejador: Nuevo docente."""
        logger.debug("Abriendo overlay para nuevo docente...")
        main_window = self._get_main_window()
        if main_window:
            metodo = getattr(main_window, 'mostrar_nuevo_docente', None)
            if metodo and callable(metodo):
                metodo()
    
    # --- Programas ---
    def _on_search_programas(self) -> None:
        """Manejador: Buscar programas con filtros."""
        logger.debug("Buscando programas con filtros...")
        self._buscar_programas_filtrados()
    
    def _on_show_all_programas(self) -> None:
        """Manejador: Mostrar todos los programas."""
        logger.debug("Mostrando todos los programas...")
        self.current_page = 1
        self.total_records = 0
        self.total_pages = 1
        self._load_programas_page(0)
    
    def _on_nuevo_programa(self) -> None:
        """Manejador: Nuevo programa."""
        logger.debug("Abriendo overlay para nuevo programa...")
        main_window = self._get_main_window()
        if main_window and hasattr(main_window, 'mostrar_overlay_programa'):
            main_window.mostrar_overlay_programa()
    
    # =========================================================================
    # SECCIÓN 10: MÉTODOS ESPECÍFICOS PARA ESTUDIANTES
    # =========================================================================
    
    def _on_view_student_history(self):
        """Ver historial académico del estudiante (inscripciones y pagos)."""
        estudiante_id = self._obtener_id_registro_seleccionado()
        if not estudiante_id:
            self._mostrar_info("Historial Académico", "Por favor, seleccione un estudiante de la tabla.")
            return

        main_window = self._get_main_window()
        if main_window:
            try:
                from view.overlays.inscripcion_overlay import InscripcionOverlay
                overlay = InscripcionOverlay(main_window)

                # Configurar overlay para mostrar todas las inscripciones del estudiante
                overlay.show_form(
                    solo_lectura=True,  # Permitir agregar transacciones si es necesario
                    modo="historial",
                    estudiante_id=estudiante_id,
                    programa_id=None  # Mostrar TODAS las inscripciones
                )

                # Conectar señales para refrescar datos después de acciones
                overlay.inscripcion_creada.connect(lambda: self._on_refresh())
                overlay.inscripcion_actualizada.connect(lambda: self._on_refresh())

                # Manejar cierre del overlay
                overlay.overlay_closed.connect(lambda: overlay.deleteLater())

            except ImportError as e:
                logger.error(f"No se pudo importar InscripcionOverlay: {e}")
                self._mostrar_info(
                    "Historial Académico",
                    f"Funcionalidad no disponible temporalmente. Error: {e}"
                )
        else:
            self._mostrar_error("No se pudo obtener la ventana principal.")
    
    def _on_new_enrollment_student(self):
        """Nueva inscripción para el estudiante seleccionado."""
        estudiante_id = self._obtener_id_registro_seleccionado()
        if not estudiante_id:
            return
        
        main_window = self._get_main_window()
        if main_window:
            try:
                from view.overlays.inscripcion_overlay import InscripcionOverlay
                overlay = InscripcionOverlay(main_window)
                overlay.show_form(
                    modo="nuevo",
                    estudiante_id=estudiante_id
                )
                
                overlay.inscripcion_creada.connect(lambda: self._on_refresh())
                overlay.overlay_closed.connect(lambda: overlay.deleteLater())
                
            except ImportError as e:
                logger.error(f"No se pudo importar InscripcionOverlay: {e}")
                self._mostrar_info(
                    "Nueva Inscripción",
                    f"Funcionalidad para nueva inscripción del estudiante ID: {estudiante_id}"
                )
    
    def _on_view_student_payments(self):
        """Ver pagos del estudiante (alternativa al historial académico)."""
        estudiante_id = self._obtener_id_registro_seleccionado()
        if not estudiante_id:
            self._mostrar_info("Ver Pagos", "Por favor, seleccione un estudiante de la tabla.")
            return

        # Opción 1: Usar InscripcionOverlay enfocado en pagos
        main_window = self._get_main_window()
        if main_window:
            try:
                from view.overlays.inscripcion_overlay import InscripcionOverlay
                overlay = InscripcionOverlay(main_window)

                overlay.show_form(
                    solo_lectura=False,
                    modo="pagos",
                    estudiante_id=estudiante_id,
                    programa_id=None
                )

                overlay.inscripcion_creada.connect(lambda: self._on_refresh())
                overlay.inscripcion_actualizada.connect(lambda: self._on_refresh())
                overlay.overlay_closed.connect(lambda: overlay.deleteLater())

            except ImportError as e:
                logger.error(f"No se pudo importar InscripcionOverlay: {e}")
                # Fallback al método original
                self._ver_pagos_estudiante_fallback(estudiante_id)
        else:
            self._ver_pagos_estudiante_fallback(estudiante_id)

    def _ver_pagos_estudiante_fallback(self, estudiante_id: int):
        """Método fallback para ver pagos del estudiante (sin InscripcionOverlay)."""
        try:
            pagos = EstudianteModel.obtener_pagos_estudiante_programa(estudiante_id)

            if pagos:
                detalles = f"<h3>💰 Historial de Pagos</h3>"
                detalles += f"<p><b>Total de transacciones: {len(pagos)}</b></p>"
                detalles += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
                detalles += "<tr><th>Fecha</th><th>Forma Pago</th><th>Monto</th><th>Comprobante</th><th>Programa</th><th>Estado</th></tr>"

                total_pagado = 0
                for pago in pagos:
                    monto = pago.get('monto_final', 0)
                    total_pagado += monto
                    detalles += f"""
                    <tr>
                        <td>{pago.get('fecha_pago', '')[:10]}</td>
                        <td>{pago.get('forma_pago', '')}</td>
                        <td>${monto:,.2f}</td>
                        <td>{pago.get('numero_comprobante', '')}</td>
                        <td>{pago.get('programa_nombre', '')}</td>
                        <td>{pago.get('estado_transaccion', '')}</td>
                    </tr>
                    """
                detalles += f"</table><p><b>Total pagado: ${total_pagado:,.2f}</b></p>"
            else:
                detalles = "<p>No se encontraron pagos para este estudiante.</p>"

            QMessageBox.information(self, "Historial de Pagos", detalles)

        except Exception as e:
            logger.error(f"Error obteniendo pagos: {e}")
            self._mostrar_error(f"Error al obtener pagos: {str(e)}")
    
    def _on_deactivate_student(self):
        """Desactivar estudiante (eliminación lógica)."""
        estudiante_id = self._obtener_id_registro_seleccionado()
        if not estudiante_id:
            return
        
        respuesta = QMessageBox.question(
            self,
            "Confirmar desactivación",
            f"¿Está seguro que desea desactivar al estudiante?\n\n"
            f"El estudiante será marcado como inactivo, pero sus datos se mantendrán en el sistema.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultado = EstudianteModel.eliminar_estudiante(estudiante_id)
                
                if resultado.get('exito'):
                    self._mostrar_info("Estudiante Desactivado", 
                        resultado.get('mensaje', 'Estudiante desactivado exitosamente.'))
                    self._on_refresh()
                else:
                    self._mostrar_error(resultado.get('mensaje', 'Error al desactivar estudiante.'))
                    
            except Exception as e:
                logger.error(f"Error desactivando estudiante: {e}")
                self._mostrar_error(f"Error al desactivar estudiante: {str(e)}")
    
    def _on_email_student(self):
        """Enviar email al estudiante."""
        estudiante_id = self._obtener_id_registro_seleccionado()
        if not estudiante_id:
            return
        
        try:
            estudiante = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
            
            if estudiante:
                email = estudiante.get('email', '')
                nombre = f"{estudiante.get('nombres', '')} {estudiante.get('apellido_paterno', '')}"
                
                if email:
                    self._mostrar_info(
                        "Enviar Email",
                        f"Preparando email para: {nombre}\nEmail: {email}\n\n"
                        "Funcionalidad de envío de email en desarrollo."
                    )
                else:
                    self._mostrar_info(
                        "Enviar Email",
                        f"El estudiante {nombre} no tiene email registrado."
                    )
            
        except Exception as e:
            logger.error(f"Error obteniendo email estudiante: {e}")
            self._mostrar_error(f"Error al obtener información del estudiante: {str(e)}")
    
    # =========================================================================
    # SECCIÓN 11: MÉTODOS ESPECÍFICOS PARA DOCENTES
    # =========================================================================
    
    def _on_view_docente_cv(self):
        """Ver CV del docente."""
        docente_id = self._obtener_id_registro_seleccionado()
        if not docente_id:
            return
        
        try:
            docente = DocenteModel.obtener_docente_por_id(docente_id)
            
            if docente:
                cv_url = docente.get('curriculum_url')
                if cv_url:
                    import os
                    if os.path.exists(cv_url):
                        import platform
                        import subprocess
                        
                        system = platform.system()
                        try:
                            if system == 'Windows':
                                os.startfile(cv_url)
                            elif system == 'Darwin':
                                subprocess.run(['open', cv_url])
                            else:
                                subprocess.run(['xdg-open', cv_url])
                        except Exception as e:
                            self._mostrar_info(
                                "Ver CV",
                                f"CV encontrado en: {cv_url}\n\n"
                                f"No se pudo abrir automáticamente. Por favor, ábralo manualmente."
                            )
                    else:
                        self._mostrar_info(
                            "Ver CV",
                            "El docente tiene un CV registrado, pero el archivo no se encuentra en la ruta especificada."
                        )
                else:
                    self._mostrar_info(
                        "Ver CV",
                        "El docente no tiene un CV registrado en el sistema."
                    )
            
        except Exception as e:
            logger.error(f"Error obteniendo CV docente: {e}")
            self._mostrar_error(f"Error al obtener CV: {str(e)}")
    
    def _on_deactivate_docente(self):
        """Desactivar docente."""
        docente_id = self._obtener_id_registro_seleccionado()
        if not docente_id:
            return
        
        respuesta = QMessageBox.question(
            self,
            "Confirmar desactivación",
            f"¿Está seguro que desea desactivar al docente?\n\n"
            f"El docente será marcado como inactivo (eliminación lógica).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultado = DocenteModel.eliminar_docente(docente_id)
                if resultado.get('exito'):
                    self._mostrar_info("Docente desactivado", resultado.get('mensaje', 'Docente desactivado exitosamente.'))
                    self._on_refresh()
                else:
                    self._mostrar_error(resultado.get('mensaje', 'Error al desactivar docente.'))
            except Exception as e:
                logger.error(f"Error desactivando docente: {e}")
                self._mostrar_error(f"Error al desactivar docente: {str(e)}")
    
    def _on_assign_docente_program(self):
        """Asignar docente a programa."""
        docente_id = self._obtener_id_registro_seleccionado()
        if not docente_id:
            return
        
        self._mostrar_info(
            "Asignar a Programa",
            f"Funcionalidad para asignar docente ID: {docente_id} a un programa en desarrollo."
        )
    
    # =========================================================================
    # SECCIÓN 12: MÉTODOS ESPECÍFICOS PARA PROGRAMAS
    # =========================================================================
    
    def _on_view_program_enrolled(self):
        """Ver estudiantes inscritos en el programa."""
        programa_id = self._obtener_id_registro_seleccionado()
        if not programa_id:
            return
        
        try:
            resultado = ProgramaModel.obtener_programa(programa_id)
            
            if not resultado.get('success'):
                self._mostrar_error("No se pudo obtener información del programa.")
                return
            
            programa = resultado['data']
            
            # Obtener inscripciones del programa
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                self._mostrar_error("Error de conexión a la base de datos.")
                return
            
            cursor = connection.cursor()
            query = """
            SELECT 
                e.id, e.ci_numero, e.ci_expedicion, e.nombres, 
                e.apellido_paterno, e.apellido_materno, e.email,
                i.fecha_inscripcion, i.estado, i.descuento_aplicado
            FROM inscripciones i
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE i.programa_id = %s
            ORDER BY i.fecha_inscripcion DESC
            """
            
            cursor.execute(query, (programa_id,))
            estudiantes = cursor.fetchall()
            cursor.close()
            Database.return_connection(connection)
            
            detalles = f"<h3>👥 Estudiantes Inscritos</h3>"
            detalles += f"<p><b>Programa:</b> {programa.get('nombre', '')} ({programa.get('codigo', '')})</p>"
            detalles += f"<p><b>Cupos:</b> {programa.get('cupos_inscritos', 0)}/{programa.get('cupos_maximos', '∞')} inscritos</p>"
            
            if estudiantes:
                detalles += f"<p><b>Total de inscritos: {len(estudiantes)}</b></p>"
                detalles += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
                detalles += "<tr><th>CI</th><th>Nombre</th><th>Email</th><th>Fecha Inscripción</th><th>Estado</th><th>Descuento</th></tr>"
                
                for estudiante in estudiantes:
                    nombre_completo = f"{estudiante[3]} {estudiante[4]} {estudiante[5]}"
                    ci_completo = f"{estudiante[1]}-{estudiante[2]}"
                    descuento = f"{estudiante[9]:.0f}%" if estudiante[9] else "0%"
                    
                    detalles += f"""
                    <tr>
                        <td>{ci_completo}</td>
                        <td>{nombre_completo}</td>
                        <td>{estudiante[6]}</td>
                        <td>{estudiante[7]}</td>
                        <td>{estudiante[8]}</td>
                        <td>{descuento}</td>
                    </tr>
                    """
                detalles += "</table>"
            else:
                detalles += "<p>No hay estudiantes inscritos en este programa.</p>"
            
            QMessageBox.information(self, "Estudiantes Inscritos", detalles)
            
        except Exception as e:
            logger.error(f"Error obteniendo estudiantes inscritos: {e}")
            self._mostrar_error(f"Error al obtener estudiantes inscritos: {str(e)}")
    
    def _on_new_enrollment_program(self):
        """Nueva inscripción en el programa seleccionado."""
        programa_id = self._obtener_id_registro_seleccionado()
        if not programa_id:
            return
        
        main_window = self._get_main_window()
        if main_window:
            try:
                from view.overlays.inscripcion_overlay import InscripcionOverlay
                overlay = InscripcionOverlay(main_window)
                overlay.show_form(
                    modo="nuevo",
                    programa_id=programa_id
                )
                
                overlay.inscripcion_creada.connect(lambda: self._on_refresh())
                overlay.overlay_closed.connect(lambda: overlay.deleteLater())
                
            except ImportError as e:
                logger.error(f"No se pudo importar InscripcionOverlay: {e}")
                self._mostrar_info(
                    "Nueva Inscripción",
                    f"Funcionalidad para nueva inscripción en programa ID: {programa_id}"
                )
    
    def _on_view_program_payments(self):
        """Ver pagos del programa."""
        programa_id = self._obtener_id_registro_seleccionado()
        if not programa_id:
            return
        
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                self._mostrar_error("Error de conexión a la base de datos.")
                return
            
            cursor = connection.cursor()
            query = """
            SELECT 
                t.fecha_pago, t.forma_pago, t.monto_final, t.numero_comprobante,
                t.estado, e.nombres, e.apellido_paterno, e.apellido_materno
            FROM transacciones t
            JOIN estudiantes e ON t.estudiante_id = e.id
            WHERE t.programa_id = %s
            ORDER BY t.fecha_pago DESC
            LIMIT 50
            """
            
            cursor.execute(query, (programa_id,))
            pagos = cursor.fetchall()
            cursor.close()
            Database.return_connection(connection)
            
            detalles = f"<h3>💰 Pagos del Programa</h3>"
            
            if pagos:
                detalles += f"<p><b>Total de transacciones: {len(pagos)}</b></p>"
                detalles += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
                detalles += "<tr><th>Fecha</th><th>Estudiante</th><th>Forma Pago</th><th>Monto</th><th>Comprobante</th><th>Estado</th></tr>"
                
                total_recaudado = 0
                for pago in pagos:
                    monto = pago[2] or 0
                    total_recaudado += monto
                    nombre_estudiante = f"{pago[5]} {pago[6]} {pago[7]}"
                    
                    detalles += f"""
                    <tr>
                        <td>{pago[0]}</td>
                        <td>{nombre_estudiante}</td>
                        <td>{pago[1]}</td>
                        <td>${monto:,.2f}</td>
                        <td>{pago[3]}</td>
                        <td>{pago[4]}</td>
                    </tr>
                    """
                detalles += f"</table><p><b>Total recaudado: ${total_recaudado:,.2f}</b></p>"
            else:
                detalles += "<p>No se encontraron pagos para este programa.</p>"
            
            QMessageBox.information(self, "Pagos del Programa", detalles)
            
        except Exception as e:
            logger.error(f"Error obteniendo pagos del programa: {e}")
            self._mostrar_error(f"Error al obtener pagos: {str(e)}")
    
    def _on_program_stats(self):
        """Ver estadísticas del programa."""
        programa_id = self._obtener_id_registro_seleccionado()
        if not programa_id:
            return
        
        try:
            resultado = ProgramaModel.obtener_programa(programa_id)
            
            if resultado.get('success'):
                programa = resultado['data']
                
                detalles = f"<h3>📊 Estadísticas del Programa</h3>"
                detalles += f"<p><b>Programa:</b> {programa.get('nombre', '')} ({programa.get('codigo', '')})</p>"
                detalles += f"<p><b>Estado:</b> {programa.get('estado', '')}</p>"
                detalles += f"<p><b>Cupos:</b> {programa.get('cupos_inscritos', 0)}/{programa.get('cupos_maximos', '∞')}</p>"
                detalles += f"<p><b>Duración:</b> {programa.get('duracion_meses', 0)} meses</p>"
                detalles += f"<p><b>Horas totales:</b> {programa.get('horas_totales', 0)} horas</p>"
                detalles += f"<p><b>Costo total:</b> ${programa.get('costo_total', 0):,.2f}</p>"
                detalles += f"<p><b>Fecha inicio:</b> {programa.get('fecha_inicio', 'No definida')}</p>"
                detalles += f"<p><b>Fecha fin:</b> {programa.get('fecha_fin', 'No definida')}</p>"
                
                QMessageBox.information(self, "Estadísticas del Programa", detalles)
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            self._mostrar_error(f"Error al obtener estadísticas: {str(e)}")
    
    def _on_cancel_program(self):
        """Cancelar programa."""
        programa_id = self._obtener_id_registro_seleccionado()
        if not programa_id:
            return
        
        respuesta = QMessageBox.question(
            self,
            "Confirmar Cancelación",
            f"¿Está seguro que desea cancelar el programa?\n\n"
            f"Esta acción cambiará el estado del programa a 'CANCELADO'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultado = ProgramaModel.eliminar_programa(programa_id)
                
                if resultado.get('exito'):
                    self._mostrar_info("Programa Cancelado", resultado.get('mensaje', 'Programa cancelado exitosamente.'))
                    self._on_refresh()
                else:
                    self._mostrar_error(resultado.get('mensaje', 'Error al cancelar programa.'))
                    
            except Exception as e:
                logger.error(f"Error cancelando programa: {e}")
                self._mostrar_error(f"Error al cancelar programa: {str(e)}")
    
    # =========================================================================
    # SECCIÓN 13: PAGINACIÓN
    # =========================================================================
    
    def _change_page(self, action: str) -> None:
        """Cambiar página actual según la acción."""
        old_page = self.current_page
        
        if action == "first":
            self.current_page = 1
        elif action == "prev" and self.current_page > 1:
            self.current_page -= 1
        elif action == "next" and self.current_page < self.total_pages:
            self.current_page += 1
        elif action == "last":
            self.current_page = self.total_pages
        
        if self.current_page != old_page:
            logger.info(f"Cambiando a página {self.current_page}/{self.total_pages}")
            self._load_current_page()
            self._update_pagination_buttons()
    
    def _load_current_page(self) -> None:
        """Cargar datos para la página actual."""
        offset = (self.current_page - 1) * self.PAGE_SIZE
        
        try:
            if self.current_view == "estudiantes":
                if self.current_filters.get('view') == 'estudiantes':
                    self._load_estudiantes_filtrados_page(offset)
                else:
                    self._load_estudiantes_page(offset)
            elif self.current_view == "docentes":
                self._load_docentes_page(offset)
            elif self.current_view == "programas":
                self._load_programas_page(offset)
        except Exception as e:
            logger.error(f"Error cargando página {self.current_page}: {e}")
            self._mostrar_error(f"Error al cargar datos: {str(e)}")
    
    def _update_pagination_buttons(self) -> None:
        """Actualizar estado de botones de paginación."""
        self.first_page_btn.setEnabled(self.current_page > 1)
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        self.last_page_btn.setEnabled(self.current_page < self.total_pages)
        
        self.page_label.setText(f"Página {self.current_page} de {self.total_pages} (Total: {self.total_records})")
    
    def _actualizar_paginacion(self) -> None:
        """Alias para compatibilidad con código existente."""
        self._update_pagination_buttons()
    
    # =========================================================================
    # SECCIÓN 14: UTILIDADES Y MÉTODOS AUXILIARES
    # =========================================================================
    
    def _obtener_id_registro_seleccionado(self) -> Optional[int]:
        """Obtener ID del registro seleccionado en la tabla."""
        current_row = self.table.currentRow()
        if current_row < 0:
            return None
        
        id_item = self.table.item(current_row, 0)
        if not id_item:
            return None
        
        try:
            return int(id_item.text())
        except (ValueError, TypeError):
            logger.error(f"ID inválido: {id_item.text()}")
            return None
    
    def _set_table_item(self, row: int, col: int, text: str,
        align_center: bool = False, align_right: bool = False) -> None:
        """Configurar item en tabla con alineación opcional."""
        item = QTableWidgetItem(text)
        if align_center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        elif align_right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, col, item)
    
    def _create_status_item(self, estado: str) -> QTableWidgetItem:
        """Crear item de estado con color según estado."""
        item = QTableWidgetItem(estado)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        estado_upper = estado.upper()
        if "ACTIVO" in estado_upper or "EN_CURSO" in estado_upper:
            item.setForeground(Qt.GlobalColor.green)
        elif "INACTIVO" in estado_upper or "CANCELADO" in estado_upper:
            item.setForeground(Qt.GlobalColor.red)
        elif "PLANIFICADO" in estado_upper:
            item.setForeground(Qt.GlobalColor.blue)
        elif "FINALIZADO" in estado_upper:
            item.setForeground(Qt.GlobalColor.darkGray)
        
        return item
    
    def _abrir_estudiante_overlay(self, estudiante_id: int, modo: str):
        """Abrir overlay de estudiante."""
        main_window = self._get_main_window()
        if not main_window:
            return
        
        if modo == "lectura":
            metodo = getattr(main_window, 'mostrar_ver_estudiante', None)
            if metodo:
                metodo(estudiante_id)
        elif modo == "editar":
            metodo = getattr(main_window, 'mostrar_editar_estudiante', None)
            if metodo:
                metodo(estudiante_id)
    
    def _abrir_docente_overlay(self, docente_id: int, modo: str):
        """Abrir overlay de docente."""
        main_window = self._get_main_window()
        if not main_window:
            return
        
        if modo == "lectura":
            metodo = getattr(main_window, 'mostrar_detalles_docente', None)
            if metodo:
                metodo(docente_id)
        elif modo == "editar":
            metodo = getattr(main_window, 'mostrar_editar_docente', None)
            if metodo:
                metodo(docente_id)
    
    def _abrir_programa_overlay(self, programa_id: int, modo: str):
        """Abrir overlay de programa."""
        main_window = self._get_main_window()
        if not main_window:
            return
        
        if modo == "lectura":
            metodo = getattr(main_window, 'mostrar_detalles_programa', None)
            if metodo:
                metodo(programa_id)
            else:
                metodo = getattr(main_window, 'mostrar_overlay_programa', None)
                if metodo:
                    metodo(programa_id=programa_id, modo="lectura")
        elif modo == "editar":
            metodo = getattr(main_window, 'mostrar_editar_programa', None)
            if metodo:
                metodo(programa_id)
            else:
                metodo = getattr(main_window, 'mostrar_overlay_programa', None)
                if metodo:
                    metodo(programa_id=programa_id, modo="editar")
    
    def _get_main_window(self):
        """Obtener referencia a la ventana principal."""
        if self.main_window:
            return self.main_window
        
        try:
            from ..main_window import MainWindow
            parent = self.window()
            if isinstance(parent, MainWindow):
                self.main_window = parent
                return parent
        except ImportError:
            logger.warning("No se pudo importar MainWindow")
        
        return None
    
    def _mostrar_error(self, mensaje: str) -> None:
        """Mostrar mensaje de error."""
        QMessageBox.critical(self, "Error", mensaje)
    
    def _mostrar_info(self, titulo: str, mensaje: str) -> None:
        """Mostrar mensaje informativo."""
        QMessageBox.information(self, titulo, mensaje)
    
    def _count_estudiantes_filtrados(self, filtros: Dict) -> int:
        """Contar estudiantes con filtros aplicados."""
        query = "SELECT COUNT(*) FROM estudiantes WHERE 1=1"
        params = []
        
        if filtros.get('ci_numero'):
            query += " AND ci_numero ILIKE %s"
            params.append(f"%{filtros['ci_numero']}%")
        
        if filtros.get('ci_expedicion'):
            query += " AND ci_expedicion = %s"
            params.append(filtros['ci_expedicion'])
        
        if filtros.get('nombres'):
            query += " AND nombres ILIKE %s"
            params.append(f"%{filtros['nombres']}%")
        
        result = Database.execute_query(query, tuple(params), fetch_one=True)
        return result[0] if result else 0
    
    # =========================================================================
    # SECCIÓN 15: MÉTODOS DE COMPATIBILIDAD CON BASETAB
    # =========================================================================
    
    def refresh(self) -> None:
        """Método para compatibilidad con BaseTab."""
        logger.debug("Refrescando datos de inicio...")
        self._on_refresh()
    
    def on_tab_selected(self) -> None:
        """Método llamado cuando se selecciona la pestaña."""
        super().on_tab_selected()
        logger.debug(f"Pestaña '{self.tab_name}' seleccionada")
        self.refresh()