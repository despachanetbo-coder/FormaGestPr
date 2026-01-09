"""
Archivo: view/tabs/inicio_tab.py
Descripción:Pestaña de inicio/dashboard principal de la aplicación.
Gestiona estudiantes, docentes y programas académicos con paginación,
búsqueda avanzada y operaciones CRUD.
Autor: Sistema FormaGestPro
Versión: 1.0.1 (Corregido errores de tipo y métodos)
"""

import logging
from typing import Optional, Dict, List, Any, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QAction
from PySide6.QtWidgets import (
    QLabel, QPushButton, QHBoxLayout, QVBoxLayout,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QGridLayout, QSizePolicy,
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
    Pestaña de inicio/dashboard principal que gestiona estudiantes,
    docentes y programas académicos con funcionalidades CRUD completas.
    
    Características:
    - Tres formularios de búsqueda independientes
    - Tabla dinámica con paginación
    - Botones de acción contextuales
    - Menú contextual
    - Overlay para detalles/edición
    """
    
    # Constantes de configuración
    PAGE_SIZE = 10  # Registros por página
    VIEW_TYPES = ["estudiantes", "docentes", "programas"]
    
    def __init__(self):
        """Inicializar la pestaña de inicio con configuración básica."""
        # Estado inicial
        self.current_view = "estudiantes"  # Vista activa
        self.main_window = None  # Referencia a MainWindow
        self.current_data = []  # Datos actuales en tabla
        self.current_filters = {}  # Filtros aplicados actualmente
        self.search_inputs = {}  # Referencias a inputs de búsqueda
        
        # Configuración de paginación
        self.current_page = 1
        self.total_pages = 1
        self.total_records = 0
        
        # Inicializar componentes de UI con tipos explícitos no-Optional
        self.table = QTableWidget()  # Ahora es explícito, no Optional
        self.detail_btn: QPushButton
        self.edit_btn: QPushButton
        self.delete_btn: QPushButton
        self.copy_btn: QPushButton
        self.export_btn: QPushButton
        self.refresh_btn: QPushButton
        self.report_btn: QPushButton
        self.contact_btn: QPushButton
        self.first_page_btn: QPushButton
        self.prev_page_btn: QPushButton
        self.next_page_btn: QPushButton
        self.last_page_btn: QPushButton
        self.page_label: QLabel
        
        # Inputs específicos para programas
        self.prog_input: QLineEdit
        self.prog_combo: QComboBox
        self.search_prog_btn: QPushButton
        self.all_prog_btn: QPushButton
        self.new_prog_btn: QPushButton
        
        # Llamar al constructor de la clase base
        super().__init__(
            tab_id="inicio_tab",
            tab_name="🏠 Gestión de Registros"
        )
        
        # Configurar el header específico para esta pestaña
        self.set_header_title("🏠 GESTIÓN DE REGISTROS")
        self.set_header_subtitle("Gestión de Estudiantes, Docentes y Programas Académicos")
        
        # En tu caso, podrías obtener el usuario real de tu sistema de autenticación
        # Por ahora usaré un usuario de ejemplo
        self.set_user_info("Administrador", "Admin")
    
    # =========================================================================
    # SECCIÓN 1: INICIALIZACIÓN Y CONFIGURACIÓN DE UI
    # =========================================================================
    
    def _init_ui(self) -> None:
        """
        Configurar la interfaz de usuario principal.
        Método requerido por BaseTab.
        """
        self.clear_content()
        #self._setup_title_section()
        self._setup_search_forms()
        self._setup_data_section()
        self._load_initial_data()
    
    def _setup_title_section(self) -> None:
        """Configurar sección de título y subtítulo."""
        # Título principal
        title = QLabel("🏠 GESTION DE REGISTROS")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1976D2; margin: 10px 0;")
        self.add_widget(title)
        
        # Subtítulo
        subtitle = QLabel("Gestión de Estudiantes, Docentes y Programas Académicos")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        self.add_widget(subtitle)
    
    def _setup_search_forms(self) -> None:
        """Configurar los tres formularios de búsqueda en una fila horizontal."""
        search_row = QHBoxLayout()
        
        # Formulario de estudiantes (4/12 del ancho)
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
        
        # Formulario de docentes (4/12 del ancho)
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
        
        # Formulario de programas (4/12 del ancho)
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
        left_panel.addWidget(self.table)  # self.table ya no es Optional
        left_panel.addLayout(self._setup_pagination_controls())
        
        # Separador vertical
        data_row.addLayout(left_panel, stretch=10)
        data_row.addWidget(self._create_vertical_separator())
        
        # Panel derecho: Botones de acción (2/12 del ancho)
        right_panel = self._setup_action_buttons()
        data_row.addLayout(right_panel, stretch=2)
        
        self.add_layout(data_row, stretch=1)
    
    def _setup_table_widget(self) -> None:
        """Configurar widget de tabla con comportamiento de selección."""
        # Configurar selección de filas completas
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
        """Configurar panel de botones de acción."""
        right_panel = QVBoxLayout()
        
        # Título de la sección
        action_title = QLabel("ACCIONES")
        action_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        action_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        action_title.setStyleSheet("color: #1976D2; margin-bottom: 10px;")
        right_panel.addWidget(action_title)
        
        # Crear y configurar botones
        buttons_config = [
            ("👁 Ver Detalles", self._on_view_details, False, "detail_btn"),
            ("✏️ Editar", self._on_edit, False, "edit_btn"),
            ("🗑 Eliminar", self._on_delete, False, "delete_btn"),
            ("📋 Copiar", self._on_copy, False, "copy_btn"),
            ("📤 Exportar", self._on_export, False, "export_btn"),
            ("🔄 Actualizar", self._on_refresh, True, "refresh_btn"),
            ("📊 Reporte", self._on_report, False, "report_btn"),
            ("📧 Contactar", self._on_contact, False, "contact_btn"),
        ]
        
        for text, slot, enabled, attr_name in buttons_config:
            button = QPushButton(text)
            button.clicked.connect(slot)
            button.setEnabled(enabled)
            setattr(self, attr_name, button)
            right_panel.addWidget(button)
        
        right_panel.addStretch(1)
        return right_panel
    
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
        """
        Crear un formulario de búsqueda genérico reutilizable.
        
        Args:
            title: Título del grupo
            label1: Etiqueta para el primer campo
            placeholder1: Placeholder para el primer campo
            expedicion_default: Valor por defecto para el combo de expedición
            label2: Etiqueta para el segundo campo
            placeholder2: Placeholder para el segundo campo
            expediciones: Lista de opciones para expedición
            search_slot: Función para búsqueda
            all_slot: Función para mostrar todos
            new_slot: Función para nuevo registro
        
        Returns:
            QGroupBox: Grupo con el formulario configurado
        """
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
        key = title.lower().replace(" ", "_")
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
        self.prog_combo.addItems(["Todos", "PRE INSCRIPCION", "INICIADO", "CANCELADO", "CONCLUIDO"])
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
                            expediciones: list, layout: QVBoxLayout) -> Tuple[QLineEdit, QComboBox]:
        """
        Crear campo para carnet/CI con combo de expedición.
        
        Returns:
            tuple: (input_field, combo_box)
        """
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
        """
        Configurar columnas de la tabla.
        
        Args:
            columns: Lista de nombres de columnas
            stretch_columns: Índices de columnas que deben estirarse
        """
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
        """Habilitar/deshabilitar botones según selección de tabla."""
        has_selection = len(self.table.selectionModel().selectedRows()) > 0
        
        # Habilitar botones de acción si hay selección
        action_buttons = [
            self.detail_btn, self.edit_btn, self.delete_btn,
            self.copy_btn, self.export_btn, self.report_btn, self.contact_btn
        ]
        
        for btn in action_buttons:
            if btn:  # Verificar que el botón existe
                btn.setEnabled(has_selection)
    
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
    
        # Acciones comunes
        add_menu_action("👁 Ver Detalles", self._on_view_details)
        add_menu_action("✏️ Editar", self._on_edit)
        add_menu_action("🗑 Eliminar", self._on_delete)
        
        # Acciones específicas por vista
        if self.current_view == "docentes":
            menu.addSeparator()
            add_menu_action("📋 Copiar", self._on_copy)
            add_menu_action("📧 Contactar", self._on_contact)
    
        menu.exec(self.table.viewport().mapToGlobal(position))
    
    # =========================================================================
    # SECCIÓN 5: OPERACIONES DE DATOS - ESTUDIANTES
    # =========================================================================
    
    def _load_estudiantes_page(self, offset: int) -> None:
        """
        Cargar página de estudiantes.
        
        Args:
            offset: Desplazamiento para paginación
        """
        try:
            # Obtener datos
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
    
    def _count_estudiantes(self) -> int:
        """Contar total de estudiantes."""
        query = "SELECT COUNT(*) FROM estudiantes"
        result = Database.execute_query(query, fetch_one=True)
        return result[0] if result else 0
    
    def _mostrar_estudiantes_en_tabla(self, estudiantes: List[Dict]) -> None:
        """
        Mostrar lista de estudiantes en la tabla.
        
        Args:
            estudiantes: Lista de diccionarios con datos de estudiantes
        """
        self.current_view = "estudiantes"
        self._configure_table_for_estudiantes()
        
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
        nombres = estudiante.get('nombres', '')
        apellido_paterno = estudiante.get('apellido_paterno', '')
        apellido_materno = estudiante.get('apellido_materno', '')
        nombre_completo = f"{nombres} {apellido_paterno} {apellido_materno}".strip()
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
            # Obtener filtros
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
        key = "🔍_buscar_estudiantes"
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
            
            # Buscar con filtros
            estudiantes = EstudianteModel.buscar_estudiantes_completo(
                ci_numero=filtros.get('ci_numero'),
                ci_expedicion=filtros.get('ci_expedicion'),
                nombres=filtros.get('nombres'),
                limit=self.PAGE_SIZE,
                offset=offset
            )
            
            # Contar con filtros
            if self.total_records == 0:
                self.total_records = self._count_estudiantes_filtrados(filtros)
                self.total_pages = max(1, (self.total_records + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
            
            self._mostrar_estudiantes_en_tabla(estudiantes)
            
        except Exception as e:
            logger.error(f"Error cargando estudiantes filtrados: {e}")
            raise
    
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
    # SECCIÓN 6: OPERACIONES DE DATOS - DOCENTES
    # =========================================================================
    
    def _load_docentes_page(self, offset: int) -> None:
        """Cargar página de docentes."""
        try:
            # Usar método optimizado del modelo
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
        nombres = docente.get('nombres', '')
        apellido_paterno = docente.get('apellido_paterno', '')
        apellido_materno = docente.get('apellido_materno', '')
        nombre_completo = f"{nombres} {apellido_paterno} {apellido_materno}".strip()
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
            # Obtener filtros
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
        key = "👨‍🏫_buscar_docentes"
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
    # SECCIÓN 7: OPERACIONES DE DATOS - PROGRAMAS
    # =========================================================================
    
    def _load_programas_page(self, offset: int) -> None:
        """Cargar página de programas."""
        try:
            # Ahora busca_programas() devuelve lista directa
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
            # Obtener y procesar filtros
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
    
    def _count_programas(self) -> int:
        """Contar total de programas."""
        query = "SELECT COUNT(*) FROM programas"
        result = Database.execute_query(query, fetch_one=True)
        return result[0] if result else 0
    
    def _mostrar_programas_en_tabla(self, programas: List[Dict]) -> None:
        """Mostrar programas en la tabla."""
        self.current_view = "programas"
        self._configure_table_for_programas()
        
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
    
    def _obtener_filtros_programas(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Obtener filtros del formulario de programas.
        
        Returns:
            tuple: (codigo, nombre, estado)
        """
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
        
        # Mapear estado de UI a estado de BD
        estado = None
        if estado_ui != "Todos":
            estado_map = {
                "PRE INSCRIPCION": "PLANIFICADO",
                "INICIADO": "EN_CURSO",
                "CANCELADO": "CANCELADO",
                "CONCLUIDO": "FINALIZADO"
            }
            estado = estado_map.get(estado_ui, estado_ui)
        
        return codigo, nombre, estado
    
    # =========================================================================
    # SECCIÓN 8: PAGINACIÓN
    # =========================================================================
    
    def _change_page(self, action: str) -> None:
        """
        Cambiar página actual según la acción.
        
        Args:
            action: "first", "prev", "next", "last"
        """
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
                if hasattr(self, 'current_filters') and self.current_filters.get('view') == 'estudiantes':
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
        # Verificar que los botones existen antes de usarlos
        if self.first_page_btn:
            self.first_page_btn.setEnabled(self.current_page > 1)
        if self.prev_page_btn:
            self.prev_page_btn.setEnabled(self.current_page > 1)
        if self.next_page_btn:
            self.next_page_btn.setEnabled(self.current_page < self.total_pages)
        if self.last_page_btn:
            self.last_page_btn.setEnabled(self.current_page < self.total_pages)
        
        if self.page_label:
            self.page_label.setText(f"Página {self.current_page} de {self.total_pages} (Total: {self.total_records})")
    
    def _actualizar_paginacion(self) -> None:
        """Alias para compatibilidad con código existente."""
        self._update_pagination_buttons()
    
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
            else:
                self._mostrar_info(
                    "Nuevo Estudiante",
                    "Funcionalidad para nuevo estudiante disponible.\n\n"
                    "La ventana principal debe tener el método 'mostrar_nuevo_estudiante()'."
                )
        else:
            self._mostrar_info(
                "Nuevo Estudiante",
                "No se puede acceder a la ventana principal."
            )
    
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
            else:
                self._mostrar_info(
                    "Nuevo Docente",
                    "Funcionalidad para nuevo docente disponible.\n\n"
                    "La ventana principal debe tener el método 'mostrar_nuevo_docente()'."
                )
        else:
            self._mostrar_info(
                "Nuevo Docente",
                "No se puede acceder a la ventana principal."
            )
    
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
        else:
            self._mostrar_info(
                "Nuevo Programa",
                "Funcionalidad para nuevo programa disponible.\n\n"
                "La ventana principal debe tener el método 'mostrar_overlay_programa()'."
            )
    
    # --- Botones de acción ---
    def _on_view_details(self) -> None:
        """Manejador: Ver detalles del registro seleccionado."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._mostrar_info("Ver Detalles", "Por favor, seleccione un registro de la tabla para ver detalles.")
            return
        
        try:
            registro_id = self._obtener_id_registro_seleccionado()
            if not registro_id:
                return
            
            if self.current_view == "estudiantes":
                # Abrir overlay de estudiante en modo visualizar
                main_window = self._get_main_window()
                if main_window:
                    metodo = getattr(main_window, 'mostrar_ver_estudiante', None)
                    if metodo and callable(metodo):
                        metodo(registro_id)
                    else:
                        self._mostrar_detalles_estudiante(current_row)
                else:
                    self._mostrar_detalles_estudiante(current_row)
            elif self.current_view == "docentes":
                self._abrir_docente_overlay(registro_id, modo="lectura")
            elif self.current_view == "programas":
                self._abrir_programa_overlay(registro_id, modo="lectura")
                
        except Exception as e:
            logger.error(f"Error viendo detalles: {e}")
            self._mostrar_error(f"Error al ver detalles: {str(e)}")
    
    def _on_edit(self) -> None:
        """Manejador: Editar registro seleccionado."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._mostrar_info("Editar", "Por favor, seleccione un registro de la tabla para editar.")
            return
        
        try:
            registro_id = self._obtener_id_registro_seleccionado()
            if not registro_id:
                return
            
            if self.current_view == "estudiantes":
                # Abrir overlay de estudiante en modo editar
                main_window = self._get_main_window()
                if main_window:
                    metodo = getattr(main_window, 'mostrar_editar_estudiante', None)
                    if metodo and callable(metodo):
                        metodo(registro_id)
                    else:
                        self._mostrar_info("Editar Estudiante", "Funcionalidad en desarrollo.")
                else:
                    self._mostrar_info("Editar Estudiante", "No se puede acceder a la ventana principal.")
            elif self.current_view == "docentes":
                self._abrir_docente_overlay(registro_id, modo="editar")
            elif self.current_view == "programas":
                self._abrir_programa_overlay(registro_id, modo="editar")
                
        except Exception as e:
            logger.error(f"Error editando registro: {e}")
            self._mostrar_error(f"Error al editar: {str(e)}")
    
    def _on_delete(self) -> None:
        """Manejador: Eliminar registro seleccionado."""
        current_row = self.table.currentRow()
        if current_row < 0:
            self._mostrar_info("Eliminar", "Por favor, seleccione un registro de la tabla para eliminar.")
            return
        
        try:
            registro_id = self._obtener_id_registro_seleccionado()
            if not registro_id:
                return
            
            if self.current_view == "estudiantes":
                self._eliminar_estudiante(registro_id)
            elif self.current_view == "docentes":
                self._eliminar_docente(registro_id)
            elif self.current_view == "programas":
                self._eliminar_programa(registro_id)
                
        except Exception as e:
            logger.error(f"Error eliminando registro: {e}")
            self._mostrar_error(f"Error al eliminar: {str(e)}")
    
    def _on_copy(self) -> None:
        """Manejador: Copiar registro."""
        self._mostrar_info("Copiar", "Funcionalidad de copiar en desarrollo.")
    
    def _on_export(self) -> None:
        """Manejador: Exportar datos."""
        self._mostrar_info("Exportar", "Funcionalidad de exportar en desarrollo.")
    
    def _on_refresh(self) -> None:
        """Manejador: Actualizar datos."""
        logger.debug("Actualizando datos...")
        self.current_page = 1
        self.total_records = 0
        self.total_pages = 1
        
        if hasattr(self, 'current_filters') and self.current_filters:
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
    
    def _on_report(self) -> None:
        """Manejador: Generar reporte."""
        self._mostrar_info("Reporte", "Funcionalidad de reporte en desarrollo.")
    
    def _on_contact(self) -> None:
        """Manejador: Contactar."""
        self._mostrar_info("Contactar", "Funcionalidad de contacto en desarrollo.")
    
    # =========================================================================
    # SECCIÓN 10: OPERACIONES CRUD ESPECÍFICAS
    # =========================================================================
    
    def _abrir_docente_overlay(self, docente_id: int, modo: str = "lectura") -> None:
        """
        Abrir overlay para mostrar/editar docente.
        
        Args:
            docente_id: ID del docente
            modo: "lectura" o "editar"
        """
        logger.debug(f"Abriendo overlay de docente (ID: {docente_id}, Modo: {modo})...")
        
        main_window = self._get_main_window()
        if not main_window:
            self._mostrar_info("Docente", f"No se puede abrir el overlay de docente (ID: {docente_id})")
            return
        
        # Intentar usar métodos de MainWindow - usando getattr para evitar errores
        if modo == "lectura":
            metodo = getattr(main_window, 'mostrar_detalles_docente', None)
            if metodo:
                metodo(docente_id)
            else:
                # Fallback: usar edición en modo lectura
                metodo_editar = getattr(main_window, 'mostrar_editar_docente', None)
                if metodo_editar:
                    metodo_editar(docente_id)
                else:
                    self._mostrar_detalles_docente_directo(docente_id, modo)
        elif modo == "editar":
            metodo_editar = getattr(main_window, 'mostrar_editar_docente', None)
            if metodo_editar:
                metodo_editar(docente_id)
            else:
                self._mostrar_info("Editar Docente", f"Editar docente ID: {docente_id}")
    
    def _mostrar_detalles_docente_directo(self, docente_id: int, modo: str) -> None:
        """Mostrar detalles del docente directamente (fallback)."""
        try:
            docente = DocenteModel.obtener_docente_por_id(docente_id)
            if not docente:
                self._mostrar_error(f"No se encontró el docente con ID {docente_id}")
                return
            
            detalles = f"""
            <h3>{'Detalles' if modo == 'lectura' else 'Editar'} Docente</h3>
            <table style='border-collapse: collapse; width: 100%;'>
                <tr><td><b>ID:</b></td><td>{docente.get('id', 'N/A')}</td></tr>
                <tr><td><b>Nombre:</b></td><td>{docente.get('nombre_completo', 'N/A')}</td></tr>
                <tr><td><b>Carnet:</b></td><td>{docente.get('ci_numero', 'N/A')}-{docente.get('ci_expedicion', 'N/A')}</td></tr>
                <tr><td><b>Email:</b></td><td>{docente.get('email', 'N/A')}</td></tr>
                <tr><td><b>Teléfono:</b></td><td>{docente.get('telefono', 'N/A')}</td></tr>
                <tr><td><b>Especialidad:</b></td><td>{docente.get('especialidad', 'N/A')}</td></tr>
                <tr><td><b>Título:</b></td><td>{docente.get('titulo_profesional', 'N/A')}</td></tr>
                <tr><td><b>Estado:</b></td><td>{'ACTIVO' if docente.get('activo') else 'INACTIVO'}</td></tr>
            </table>
            """
            
            QMessageBox.information(
                self,
                f"Docente - {'Detalles' if modo == 'lectura' else 'Editar'}",
                detalles
            )
            
        except Exception as e:
            logger.error(f"Error mostrando detalles docente: {e}")
            self._mostrar_error(f"Error al mostrar docente: {str(e)}")
    
    def _eliminar_docente(self, docente_id: int) -> None:
        """Eliminar un docente (eliminación lógica)."""
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro que desea eliminar al docente con ID {docente_id}?\n\n"
            "Esta acción desactivará al docente (eliminación lógica).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            try:
                resultado = DocenteModel.eliminar_docente(docente_id)
                if resultado.get('exito'):
                    self._mostrar_info("Docente eliminado", resultado.get('mensaje', 'Docente eliminado exitosamente.'))
                    self._on_refresh()
                else:
                    self._mostrar_error(resultado.get('mensaje', 'Error al eliminar docente.'))
            except Exception as e:
                logger.error(f"Error eliminando docente: {e}")
                self._mostrar_error(f"Error al eliminar docente: {str(e)}")
    
    def _eliminar_estudiante(self, estudiante_id: int) -> None:
        """Eliminar un estudiante."""
        self._mostrar_info(
            "Eliminar Estudiante",
            f"Funcionalidad para eliminar estudiante ID: {estudiante_id} en desarrollo."
        )
    
    def _eliminar_programa(self, programa_id: int) -> None:
        """Eliminar un programa."""
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            f"¿Está seguro que desea eliminar el programa con ID {programa_id}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            self._mostrar_info(
                "Programa eliminado",
                f"Programa ID: {programa_id} marcado como eliminado (solo simulación)."
            )
            # TODO: Implementar ProgramaModel.eliminar_programa(programa_id)
    
    # =========================================================================
    # SECCIÓN 11: VISTAS DE DETALLES
    # =========================================================================
    
    def _abrir_programa_overlay(self, programa_id: int, modo: str = "lectura") -> None:
        """
        Abrir overlay para mostrar/editar programa.
        
        Args:
            programa_id: ID del programa
            modo: "lectura", "editar" o "nuevo"
        """
        logger.debug(f"Abriendo overlay de programa (ID: {programa_id}, Modo: {modo})...")
        
        main_window = self._get_main_window()
        if not main_window:
            self._mostrar_info("Programa", 
                f"No se puede abrir el overlay de programa (ID: {programa_id})")
            return
        
        # Intentar usar métodos de MainWindow
        if modo == "lectura":
            metodo = getattr(main_window, 'mostrar_detalles_programa', None)
            if metodo:
                metodo(programa_id)
            else:
                # Fallback a overlay en modo lectura
                metodo_ver = getattr(main_window, 'mostrar_overlay_programa', None)
                if metodo_ver:
                    # Pasar parámetros para modo lectura
                    metodo_ver(programa_id=programa_id, modo="lectura")
                else:
                    self._mostrar_detalles_programa(programa_id, modo)
                    
        elif modo == "editar":
            metodo_editar = getattr(main_window, 'mostrar_editar_programa', None)
            if metodo_editar:
                metodo_editar(programa_id)
            else:
                # Fallback a mostrar_overlay_programa
                metodo_general = getattr(main_window, 'mostrar_overlay_programa', None)
                if metodo_general:
                    metodo_general(programa_id=programa_id, modo="editar")
                else:
                    self._mostrar_info("Editar Programa", 
                        f"Editar programa ID: {programa_id}")
                        
        elif modo == "nuevo":
            metodo_nuevo = getattr(main_window, 'mostrar_nuevo_programa', None)
            if metodo_nuevo:
                metodo_nuevo()
            else:
                metodo_general = getattr(main_window, 'mostrar_overlay_programa', None)
                if metodo_general:
                    metodo_general(modo="nuevo")
                else:
                    self._mostrar_info("Nuevo Programa", 
                        "Abrir formulario para nuevo programa")
    
    def _mostrar_detalles_programa(self, programa_id: int, modo: str) -> None:
        """Mostrar detalles de un programa en formato HTML."""
        try:
            # Importar aquí para evitar dependencia circular
            from model.programa_model import ProgramaModel
            resultado = ProgramaModel.obtener_programa(programa_id)
            
            if not resultado.get('success'):
                self._mostrar_error(f"No se encontró el programa con ID {programa_id}")
                return
            
            programa = resultado['data']
            
            detalles = f"""
            <h3>{'Detalles' if modo == 'lectura' else 'Editar'} Programa</h3>
            <table style='border-collapse: collapse; width: 100%;'>
                <tr><td><b>ID:</b></td><td>{programa.get('id', 'N/A')}</td></tr>
                <tr><td><b>Código:</b></td><td>{programa.get('codigo', 'N/A')}</td></tr>
                <tr><td><b>Nombre:</b></td><td>{programa.get('nombre', 'N/A')}</td></tr>
                <tr><td><b>Duración:</b></td><td>{programa.get('duracion_meses', 'N/A')} meses</td></tr>
                <tr><td><b>Horas totales:</b></td><td>{programa.get('horas_totales', 'N/A')}</td></tr>
                <tr><td><b>Costo total:</b></td><td>${programa.get('costo_total', 0):,.2f}</td></tr>
                <tr><td><b>Estado:</b></td><td>{programa.get('estado', 'N/A')}</td></tr>
                <tr><td><b>Fecha inicio:</b></td><td>{programa.get('fecha_inicio', 'N/A')}</td></tr>
                <tr><td><b>Fecha fin:</b></td><td>{programa.get('fecha_fin', 'N/A')}</td></tr>
                <tr><td><b>Cupos:</b></td><td>{programa.get('cupos_inscritos', 0)}/{programa.get('cupos_maximos', '∞')}</td></tr>
            </table>
            """
            
            QMessageBox.information(
                self,
                f"Programa - {'Detalles' if modo == 'lectura' else 'Editar'}",
                detalles
            )
            
        except Exception as e:
            logger.error(f"Error mostrando detalles programa: {e}")
            self._mostrar_error(f"Error al mostrar programa: {str(e)}")
    
    def _mostrar_detalles_estudiante(self, row: int) -> None:
        """Mostrar detalles de un estudiante en formato HTML."""
        try:
            detalles = self._obtener_detalles_fila(row, "estudiante")
            QMessageBox.information(self, "Detalles del Estudiante", detalles)
        except Exception as e:
            logger.error(f"Error mostrando detalles estudiante: {e}")
            self._mostrar_error(f"Error al mostrar detalles: {str(e)}")
    
    def _mostrar_detalles_docente(self, row: int) -> None:
        """Mostrar detalles de un docente en formato HTML."""
        try:
            detalles = self._obtener_detalles_fila(row, "docente")
            QMessageBox.information(self, "Detalles del Docente", detalles)
        except Exception as e:
            logger.error(f"Error mostrando detalles docente: {e}")
            self._mostrar_error(f"Error al mostrar detalles: {str(e)}")
    
    def _obtener_detalles_fila(self, row: int, tipo: str) -> str:
        """
        Obtener detalles de una fila en formato HTML.
        
        Args:
            row: Índice de la fila
            tipo: Tipo de registro
        
        Returns:
            str: HTML con detalles
        """
        try:
            # Obtener datos de la fila
            datos = []
            column_count = self.table.columnCount()
            for col in range(column_count):
                item = self.table.item(row, col)
                datos.append(item.text() if item else "N/A")
            
            # Generar HTML según tipo
            if tipo == "programa":
                return self._generar_html_programa(datos)
            elif tipo == "estudiante":
                return self._generar_html_estudiante(datos)
            elif tipo == "docente":
                return self._generar_html_docente(datos)
            else:
                return "<p>Tipo de registro no reconocido</p>"
                
        except Exception as e:
            logger.error(f"Error obteniendo detalles de fila: {e}")
            return f"<p>Error al obtener detalles: {str(e)}</p>"
    
    def _generar_html_programa(self, datos: list) -> str:
        """Generar HTML para detalles de programa."""
        return f"""
        <h3>Detalles del Programa</h3>
        <table style='border-collapse: collapse; width: 100%;'>
            <tr><td><b>ID:</b></td><td>{datos[0]}</td></tr>
            <tr><td><b>Código:</b></td><td>{datos[1]}</td></tr>
            <tr><td><b>Nombre:</b></td><td>{datos[2]}</td></tr>
            <tr><td><b>Duración:</b></td><td>{datos[3]} meses</td></tr>
            <tr><td><b>Horas totales:</b></td><td>{datos[4]} horas</td></tr>
            <tr><td><b>Estado:</b></td><td>{datos[5]}</td></tr>
            <tr><td><b>Costo total:</b></td><td>{datos[6]}</td></tr>
            <tr><td><b>Cupos:</b></td><td>{datos[7]}</td></tr>
            <tr><td><b>Fecha inicio:</b></td><td>{datos[8]}</td></tr>
            <tr><td><b>Fecha fin:</b></td><td>{datos[9]}</td></tr>
        </table>
        """
    
    def _generar_html_estudiante(self, datos: list) -> str:
        """Generar HTML para detalles de estudiante."""
        return f"""
        <h3>Detalles del Estudiante</h3>
        <table style='border-collapse: collapse; width: 100%;'>
            <tr><td><b>ID:</b></td><td>{datos[0]}</td></tr>
            <tr><td><b>Carnet:</b></td><td>{datos[1]}</td></tr>
            <tr><td><b>Nombre completo:</b></td><td>{datos[2]}</td></tr>
            <tr><td><b>Email:</b></td><td>{datos[3]}</td></tr>
            <tr><td><b>Teléfono:</b></td><td>{datos[4]}</td></tr>
            <tr><td><b>Estado:</b></td><td>{datos[5]}</td></tr>
            <tr><td><b>Fecha registro:</b></td><td>{datos[6]}</td></tr>
        </table>
        """
    
    def _generar_html_docente(self, datos: list) -> str:
        """Generar HTML para detalles de docente."""
        return f"""
        <h3>Detalles del Docente</h3>
        <table style='border-collapse: collapse; width: 100%;'>
            <tr><td><b>ID:</b></td><td>{datos[0]}</td></tr>
            <tr><td><b>Carnet:</b></td><td>{datos[1]}</td></tr>
            <tr><td><b>Nombre completo:</b></td><td>{datos[2]}</td></tr>
            <tr><td><b>Email:</b></td><td>{datos[3]}</td></tr>
            <tr><td><b>Teléfono:</b></td><td>{datos[4]}</td></tr>
            <tr><td><b>Especialidad:</b></td><td>{datos[5]}</td></tr>
            <tr><td><b>Título:</b></td><td>{datos[6]}</td></tr>
            <tr><td><b>Estado:</b></td><td>{datos[7]}</td></tr>
            <tr><td><b>Fecha registro:</b></td><td>{datos[8]}</td></tr>
        </table>
        """
    
    # =========================================================================
    # SECCIÓN 12: UTILIDADES Y MÉTODOS AUXILIARES
    # =========================================================================
    
    def _obtener_id_registro_seleccionado(self) -> Optional[int]:
        """
        Obtener ID del registro seleccionado en la tabla.
        
        Returns:
            ID del registro o None si no hay selección
        """
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
        """
        Configurar item en tabla con alineación opcional.
        
        Args:
            row: Fila
            col: Columna
            text: Texto a mostrar
            align_center: Alinear al centro
            align_right: Alinear a la derecha
        """
        item = QTableWidgetItem(text)
        if align_center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        elif align_right:
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, col, item)
    
    def _create_status_item(self, estado: str) -> QTableWidgetItem:
        """
        Crear item de estado con color según estado.
        
        Args:
            estado: Texto del estado
        
        Returns:
            QTableWidgetItem: Item configurado
        """
        item = QTableWidgetItem(estado)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Color según estado
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
    
    def _get_main_window(self):
        """
        Obtener referencia a la ventana principal.
        
        Returns:
            MainWindow: Instancia de MainWindow o None
        """
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
        
        logger.warning("No se pudo obtener referencia a la ventana principal")
        return None
    
    def _mostrar_error(self, mensaje: str) -> None:
        """Mostrar mensaje de error."""
        QMessageBox.critical(self, "Error", mensaje)
    
    def _mostrar_info(self, titulo: str, mensaje: str) -> None:
        """Mostrar mensaje informativo."""
        QMessageBox.information(self, titulo, mensaje)
    
    # =========================================================================
    # SECCIÓN 13: MÉTODOS DE COMPATIBILIDAD CON BASETAB
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