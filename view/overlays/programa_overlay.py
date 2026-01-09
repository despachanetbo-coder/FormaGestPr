# view/overlays/programa_overlay.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QSpinBox, QDoubleSpinBox, 
    QComboBox, QDateEdit, QGroupBox, QGridLayout, QFormLayout,
    QScrollArea, QFrame, QSizePolicy, QCheckBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QColor
from typing import List, Optional, Dict, Any, Tuple
import logging

# Importar modelo de docentes
from model.docente_model import DocenteModel
from .base_overlay import BaseOverlay

logger = logging.getLogger(__name__)

class ProgramaOverlay(BaseOverlay):
    """Overlay para crear/editar programas académicos con campos específicos de la tabla"""
    
    # Señales específicas de ProgramaOverlay
    programa_guardado = Signal(dict)
    programa_actualizado = Signal(dict)
    programa_eliminado = Signal(dict)
    
    # Sistema UNSXX
    NIVELES_ACADEMICOS = {
        "Diplomado": "DIP",
        "Especialidad": "ESP", 
        "Maestría": "MSC",
        "Doctorado": "PHD",
        "Certificación": "CER",
        "Curso": "CUR",
        "Taller": "TAL",
        "Pregrado": "PRE",
        "Capacitación": "CAP"
    }
    
    CARRERAS_UNSXX = [
        ("Bioquímica", "BIO"),
        ("Odontología", "ODO"),
        ("Enfermería", "ENF"),
        ("Medicina", "MED"),
        ("Laboratorio Clínico", "LBC"),
        ("Fisioterapia", "FIS"),
        ("Ing. Civil", "CIV"),
        ("Ing. Agronómica", "AGR"),
        ("Ing. Informática", "INF"),
        ("Ing. Mecánica", "MEC"),
        ("Ing. Minas", "MIN"),
        ("Ing. Electromecánica", "ELE"),
        ("Ciencias Educación", "EDU"),
        ("Contaduría Pública", "CON"),
        ("Derecho", "DER"),
        ("Comunicación", "COM"),
        ("Administración", "ADM"),
        ("Psicología", "PSI"),
        ("Salud Pública", "SAP"),
        ("Gestión Farmacia", "GFM")
    ]
    
    ROMAN_NUMERALS = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
        (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
        (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent, "🏛️ Programa Académico - UNSXX", 95, 95)
        
        # Variables específicas
        self.programa_id: Optional[int] = None
        self.codigo_construido = ""
        self.es_posgrado = False
        
        # Variables para control de descripción automática
        self.descripcion_automatica = True
        self.primer_cambio = True
        
        # Configurar UI específica
        self.setup_ui_especifica()
        self.setup_conexiones_especificas()
        self.setup_valores_predeterminados()
        
        # Aplicar estilos específicos
        self.apply_specific_styles()
        
        logger.debug("✅ ProgramaOverlay inicializado")
    
    def setup_ui_especifica(self):
        """Configurar la interfaz específica de programa académico"""
        # Limpiar layout de contenido base
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
        
        # Splitter para dos columnas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(5)
        
        # ===== COLUMNA IZQUIERDA =====
        scroll_izquierda = QScrollArea()
        scroll_izquierda.setWidgetResizable(True)
        scroll_izquierda.setFrameShape(QFrame.Shape.NoFrame)
        
        widget_izquierda = QWidget()
        layout_izquierda = QVBoxLayout(widget_izquierda)
        layout_izquierda.setContentsMargins(5, 5, 10, 5)
        
        # Grupo: Identificación UNSXX
        grupo_identificacion = self.crear_grupo_identificacion()
        layout_izquierda.addWidget(grupo_identificacion)
        
        # Grupo: Información del Programa (con campos de la tabla)
        grupo_programa = self.crear_grupo_programa()
        layout_izquierda.addWidget(grupo_programa)
        
        # Grupo: Estructura Académica
        grupo_estructura = self.crear_grupo_estructura()
        layout_izquierda.addWidget(grupo_estructura)
        
        # Grupo: Docente Coordinador
        grupo_docente = self.crear_grupo_docente()
        layout_izquierda.addWidget(grupo_docente)
        
        # Grupo: Cupos y Costos
        grupo_cupos_costos = self.crear_grupo_cupos_costos()
        layout_izquierda.addWidget(grupo_cupos_costos)
        
        # Grupo: Calendario Académico
        grupo_calendario = self.crear_grupo_calendario()
        layout_izquierda.addWidget(grupo_calendario)
        
        # Grupo: Promociones y Descuentos (nuevo campo de la tabla)
        grupo_promociones = self.crear_grupo_promociones()
        layout_izquierda.addWidget(grupo_promociones)
        
        layout_izquierda.addStretch()
        
        scroll_izquierda.setWidget(widget_izquierda)
        
        # ===== COLUMNA DERECHA =====
        widget_derecha = QWidget()
        layout_derecha = QVBoxLayout(widget_derecha)
        layout_derecha.setContentsMargins(10, 5, 5, 5)
        
        # Grupo: Resumen del Programa
        grupo_resumen = self.crear_grupo_resumen()
        layout_derecha.addWidget(grupo_resumen)
        
        # Pestañas para estudiantes y pagos
        tab_widget = QTabWidget()
        
        # Pestaña 1: Estudiantes inscritos
        tab_estudiantes = self.crear_tab_estudiantes()
        tab_widget.addTab(tab_estudiantes, "👥 Estudiantes")
        
        # Pestaña 2: Resumen de Pagos
        tab_pagos = self.crear_tab_pagos()
        tab_widget.addTab(tab_pagos, "💵 Pagos")
        
        layout_derecha.addWidget(tab_widget, 1)
        
        # Agregar al splitter
        splitter.addWidget(scroll_izquierda)
        splitter.addWidget(widget_derecha)
        
        # Configurar proporciones
        splitter.setSizes([500, 500])
        
        # Agregar splitter al layout de contenido
        self.content_layout.addWidget(splitter, 1)
    
    def crear_grupo_identificacion(self):
        """Crear grupo de identificación UNSXX"""
        grupo = QGroupBox("🏛️ IDENTIFICACIÓN UNSXX")
        grupo.setObjectName("grupoIdentificacion")
        
        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(12, 20, 12, 15)
        layout.setSpacing(12)
        
        # Código único (campo de la tabla)
        codigo_container = QVBoxLayout()
        codigo_label = QLabel("Código UNSXX:*")
        codigo_label.setProperty("class", "labelObligatorio")
        codigo_container.addWidget(codigo_label)
        
        self.codigo_generado_label = QLabel("Seleccione nivel y carrera")
        self.codigo_generado_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.codigo_generado_label.setMinimumHeight(40)
        codigo_container.addWidget(self.codigo_generado_label)
        
        # Campo oculto para el código
        self.codigo_hidden = QLineEdit()
        self.codigo_hidden.setVisible(False)
        codigo_container.addWidget(self.codigo_hidden)
        
        layout.addLayout(codigo_container)
        
        # Nivel y Carrera
        nivel_carrera_layout = QHBoxLayout()
        
        # Nivel Académico
        nivel_container = QVBoxLayout()
        nivel_label = QLabel("Nivel Académico:*")
        nivel_label.setProperty("class", "labelObligatorio")
        nivel_container.addWidget(nivel_label)
        
        self.nivel_combo = QComboBox()
        self.nivel_combo.addItems(list(self.NIVELES_ACADEMICOS.keys()))
        self.nivel_combo.currentTextChanged.connect(self._on_nivel_cambiado)
        nivel_container.addWidget(self.nivel_combo)
        nivel_carrera_layout.addLayout(nivel_container)
        
        # Carrera/Programa
        carrera_container = QVBoxLayout()
        carrera_label = QLabel("Carrera/Programa:*")
        carrera_label.setProperty("class", "labelObligatorio")
        carrera_container.addWidget(carrera_label)
        
        self.carrera_combo = QComboBox()
        for nombre, abrev in self.CARRERAS_UNSXX:
            self.carrera_combo.addItem(nombre, abrev)
        self.carrera_combo.currentIndexChanged.connect(self._actualizar_codigo)
        carrera_container.addWidget(self.carrera_combo)
        nivel_carrera_layout.addLayout(carrera_container)
        
        layout.addLayout(nivel_carrera_layout)
        
        # Año y Versión
        año_version_layout = QHBoxLayout()
        
        # Año
        año_container = QVBoxLayout()
        año_label = QLabel("Año Académico:*")
        año_label.setProperty("class", "labelObligatorio")
        año_container.addWidget(año_label)
        
        self.año_input = QSpinBox()
        self.año_input.setRange(2024, 2035)
        self.año_input.setValue(QDate.currentDate().year())
        self.año_input.valueChanged.connect(self._actualizar_codigo)
        año_container.addWidget(self.año_input)
        año_version_layout.addLayout(año_container)
        
        # Versión
        version_container = QVBoxLayout()
        version_label = QLabel("Versión:")
        version_container.addWidget(version_label)
        
        version_hbox = QHBoxLayout()
        self.version_spin = QSpinBox()
        self.version_spin.setRange(1, 20)
        self.version_spin.setValue(1)
        self.version_spin.valueChanged.connect(self._actualizar_version_romana)
        
        self.version_label = QLabel("I")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.version_label.setMinimumWidth(50)
        
        version_hbox.addWidget(self.version_spin)
        version_hbox.addWidget(self.version_label)
        version_container.addLayout(version_hbox)
        año_version_layout.addLayout(version_container)
        
        layout.addLayout(año_version_layout)
        
        return grupo
    
    def crear_grupo_programa(self):
        """Crear grupo de información del programa con campos de la tabla"""
        grupo = QGroupBox("📚 INFORMACIÓN DEL PROGRAMA")
        
        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(12, 20, 12, 15)
        layout.setSpacing(12)
        
        # Nombre oficial (campo de la tabla)
        nombre_container = QVBoxLayout()
        nombre_label = QLabel("Nombre Oficial:*")
        nombre_label.setProperty("class", "labelObligatorio")
        nombre_container.addWidget(nombre_label)
        
        nombre_hbox = QHBoxLayout()
        self.nombre_checkbox = QCheckBox("Habilitar nombre personalizado")
        self.nombre_checkbox.setChecked(True)
        
        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ej: Maestría en Enfermería - Modalidad Virtual UNSXX")
        nombre_hbox.addWidget(self.nombre_checkbox)
        nombre_hbox.addWidget(self.nombre_input, 1)
        
        nombre_container.addLayout(nombre_hbox)
        layout.addLayout(nombre_container)
        
        # Descripción con control de modo (campo de la tabla)
        desc_container = QVBoxLayout()
        desc_header = QHBoxLayout()
        
        desc_label = QLabel("Descripción del Programa:")
        desc_header.addWidget(desc_label)
        
        # Botón para controlar modo automático/manual
        self.btn_modo_descripcion = QPushButton("🔄 Auto")
        self.btn_modo_descripcion.setCheckable(True)
        self.btn_modo_descripcion.setChecked(True)
        self.btn_modo_descripcion.setToolTip("Alternar entre generación automática y edición manual")
        self.btn_modo_descripcion.setFixedWidth(80)
        self.btn_modo_descripcion.clicked.connect(self._alternar_modo_descripcion)
        desc_header.addWidget(self.btn_modo_descripcion)
        
        desc_header.addStretch()
        desc_container.addLayout(desc_header)
        
        # Usar QTextEdit para descripción larga (campo TEXT en la tabla)
        self.descripcion_input = QTextEdit()
        self.descripcion_input.setPlaceholderText("La descripción se genera automáticamente...")
        self.descripcion_input.setMaximumHeight(100)
        desc_container.addWidget(self.descripcion_input)
        layout.addLayout(desc_container)
        
        return grupo
    
    def crear_grupo_estructura(self):
        """Crear grupo de estructura académica con campos de la tabla"""
        grupo = QGroupBox("⏳ ESTRUCTURA ACADÉMICA")
        
        grid = QGridLayout(grupo)
        grid.setContentsMargins(12, 20, 12, 15)
        grid.setSpacing(12)
        
        # Fila 1 - Duración (meses) (campo de la tabla)
        grid.addWidget(QLabel("Duración (meses):*"), 0, 0)
        self.duracion_input = QSpinBox()
        self.duracion_input.setRange(1, 60)
        self.duracion_input.setValue(24)
        self.duracion_input.valueChanged.connect(self._actualizar_fecha_fin)
        grid.addWidget(self.duracion_input, 0, 1)
        
        # Carga Horaria (campo de la tabla)
        grid.addWidget(QLabel("Carga Horaria:*"), 0, 2)
        self.horas_input = QSpinBox()
        self.horas_input.setRange(40, 10000)
        self.horas_input.setValue(1200)
        grid.addWidget(self.horas_input, 0, 3)
        
        # Fila 2 - Estado (campo de la tabla)
        grid.addWidget(QLabel("Estado:*"), 1, 0)
        self.estado_input = QComboBox()
        self.estado_input.addItems(["PLANIFICADO", "INSCRIPCIONES", "EN_CURSO", "CONCLUIDO", "CANCELADO"])
        grid.addWidget(self.estado_input, 1, 1)
        
        return grupo
    
    def crear_grupo_promociones(self):
        """Crear grupo para promociones y descuentos (nuevos campos de la tabla)"""
        grupo = QGroupBox("🎁 PROMOCIONES Y DESCUENTOS")
        
        grid = QGridLayout(grupo)
        grid.setContentsMargins(12, 20, 12, 15)
        grid.setSpacing(12)
        
        # Descuento porcentual (campo de la tabla)
        grid.addWidget(QLabel("Descuento (%):"), 0, 0)
        self.descuento_input = QDoubleSpinBox()
        self.descuento_input.setRange(0, 100)
        self.descuento_input.setValue(0.0)
        self.descuento_input.setSuffix(" %")
        self.descuento_input.valueChanged.connect(self._actualizar_costos_con_descuento)
        grid.addWidget(self.descuento_input, 0, 1)
        
        # Descripción de la promoción (campo de la tabla)
        grid.addWidget(QLabel("Descripción promoción:"), 1, 0)
        self.promocion_desc_input = QLineEdit()
        self.promocion_desc_input.setPlaceholderText("Ej: Promoción especial por lanzamiento")
        grid.addWidget(self.promocion_desc_input, 1, 1)
        
        # Fecha válido hasta (campo de la tabla)
        grid.addWidget(QLabel("Válido hasta:"), 2, 0)
        self.promocion_valido_hasta_input = QDateEdit()
        self.promocion_valido_hasta_input.setCalendarPopup(True)
        self.promocion_valido_hasta_input.setDate(QDate.currentDate().addDays(30))
        grid.addWidget(self.promocion_valido_hasta_input, 2, 1)
        
        # Checkbox para habilitar promoción
        self.promocion_checkbox = QCheckBox("Habilitar promoción")
        self.promocion_checkbox.stateChanged.connect(self._habilitar_promocion)
        grid.addWidget(self.promocion_checkbox, 3, 0, 1, 2)
        
        return grupo
    
    def crear_grupo_docente(self):
        """Crear grupo de docente coordinador (campo de la tabla)"""
        grupo = QGroupBox("👨‍🏫 DOCENTE COORDINADOR")
        
        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(12, 20, 12, 15)
        layout.setSpacing(12)
        
        docente_label = QLabel("Docente Coordinador:")
        layout.addWidget(docente_label)
        
        self.docente_coordinador_combo = QComboBox()
        self.docente_coordinador_combo.addItem("-- Seleccionar Docente --", None)
        layout.addWidget(self.docente_coordinador_combo)
        
        return grupo
    
    def crear_grupo_cupos_costos(self):
        """Crear grupo de cupos y costos (campos de la tabla)"""
        grupo = QGroupBox("💰 CUPOS Y COSTOS (USD)")
        
        grid = QGridLayout(grupo)
        grid.setContentsMargins(12, 20, 12, 15)
        grid.setSpacing(12)
        
        # Fila 1 - Cupos (campos de la tabla)
        grid.addWidget(QLabel("Cupos máximos:*"), 0, 0)
        self.cupos_max_input = QSpinBox()
        self.cupos_max_input.setRange(1, 500)
        self.cupos_max_input.setValue(30)
        self.cupos_max_input.valueChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.cupos_max_input, 0, 1)
        
        grid.addWidget(QLabel("Cupos inscritos:*"), 0, 2)
        self.cupos_inscritos_input = QSpinBox()
        self.cupos_inscritos_input.setRange(0, 500)
        self.cupos_inscritos_input.setValue(0)
        self.cupos_inscritos_input.valueChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.cupos_inscritos_input, 0, 3)
        
        # Fila 2 - Costos principales (campos de la tabla)
        grid.addWidget(QLabel("Costo total:*"), 1, 0)
        self.costo_total_input = QDoubleSpinBox()
        self.costo_total_input.setRange(0, 50000)
        self.costo_total_input.setValue(5000.00)
        self.costo_total_input.setDecimals(2)
        self.costo_total_input.setPrefix("$ ")
        self.costo_total_input.valueChanged.connect(self._calcular_cuotas)
        grid.addWidget(self.costo_total_input, 1, 1)
        
        grid.addWidget(QLabel("Número de cuotas:*"), 1, 2)
        self.cuotas_input = QSpinBox()
        self.cuotas_input.setRange(1, 36)
        self.cuotas_input.setValue(10)
        self.cuotas_input.valueChanged.connect(self._calcular_cuotas)
        grid.addWidget(self.cuotas_input, 1, 3)
        
        # Fila 3 - Costos adicionales (campos de la tabla)
        grid.addWidget(QLabel("Costo matrícula:*"), 2, 0)
        self.costo_matricula_input = QDoubleSpinBox()
        self.costo_matricula_input.setRange(0, 5000)
        self.costo_matricula_input.setValue(200.00)
        self.costo_matricula_input.setDecimals(2)
        self.costo_matricula_input.setPrefix("$ ")
        self.costo_matricula_input.valueChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.costo_matricula_input, 2, 1)
        
        grid.addWidget(QLabel("Costo inscripción:*"), 2, 2)
        self.costo_inscripcion_input = QDoubleSpinBox()
        self.costo_inscripcion_input.setRange(0, 500)
        self.costo_inscripcion_input.setValue(50.00)
        self.costo_inscripcion_input.setDecimals(2)
        self.costo_inscripcion_input.setPrefix("$ ")
        self.costo_inscripcion_input.valueChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.costo_inscripcion_input, 2, 3)
        
        # Fila 4: Costo por cuota (calculado, campo de la tabla)
        grid.addWidget(QLabel("Costo mensualidad:*"), 3, 0)
        self.costo_cuota_label = QLabel("$500.00")
        self.costo_cuota_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.costo_cuota_label.setProperty("class", "costoMensualidad")
        grid.addWidget(self.costo_cuota_label, 3, 1, 1, 3)
        
        return grupo
    
    def crear_grupo_calendario(self):
        """Crear grupo de calendario académico (campos de la tabla)"""
        grupo = QGroupBox("📅 CALENDARIO ACADÉMICO")
        
        layout = QHBoxLayout(grupo)
        layout.setContentsMargins(12, 20, 12, 15)
        layout.setSpacing(12)
        
        # Fecha inicio (campo de la tabla)
        fecha_inicio_container = QVBoxLayout()
        fecha_inicio_label = QLabel("Fecha inicio:*")
        fecha_inicio_label.setProperty("class", "labelObligatorio")
        fecha_inicio_container.addWidget(fecha_inicio_label)
        
        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate().addDays(60))
        self.fecha_inicio_input.dateChanged.connect(self._actualizar_fecha_fin)
        fecha_inicio_container.addWidget(self.fecha_inicio_input)
        
        # Fecha fin (campo de la tabla)
        fecha_fin_container = QVBoxLayout()
        fecha_fin_container.addWidget(QLabel("Fecha fin estimada:"))
        
        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addDays(60 + 730))
        fecha_fin_container.addWidget(self.fecha_fin_input)
        
        layout.addLayout(fecha_inicio_container, 1)
        layout.addLayout(fecha_fin_container, 1)
        
        return grupo
    
    def crear_grupo_resumen(self):
        """Crear grupo de resumen del programa"""
        grupo = QGroupBox("📊 RESUMEN DEL PROGRAMA")
        
        grid = QGridLayout(grupo)
        grid.setContentsMargins(12, 20, 12, 15)
        grid.setSpacing(12)
        
        # Fila 1
        self.lbl_cupos_disponibles = QLabel("Cupos disponibles: 30")
        self.lbl_cupos_disponibles.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_cupos_disponibles, 0, 0)
        
        self.lbl_porcentaje_ocupacion = QLabel("Ocupación: 0%")
        self.lbl_porcentaje_ocupacion.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_porcentaje_ocupacion, 0, 1)
        
        # Fila 2
        self.lbl_ingresos_estimados = QLabel("Ingresos estimados: $0.00")
        self.lbl_ingresos_estimados.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_ingresos_estimados, 1, 0)
        
        self.lbl_ingresos_reales = QLabel("Ingresos reales: $0.00")
        self.lbl_ingresos_reales.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_ingresos_reales, 1, 1)
        
        # Fila 3
        self.lbl_saldo_pendiente = QLabel("Saldo pendiente: $0.00")
        self.lbl_saldo_pendiente.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_saldo_pendiente, 2, 0, 1, 2)
        
        # Fila 4 - Costo con descuento
        self.lbl_costo_con_descuento = QLabel("Costo con descuento: $5,000.00")
        self.lbl_costo_con_descuento.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_costo_con_descuento, 3, 0, 1, 2)
        
        return grupo
    
    def crear_tab_estudiantes(self):
        """Crear pestaña de estudiantes inscritos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de estudiantes
        self.tabla_estudiantes = QTableWidget()
        self.tabla_estudiantes.setColumnCount(5)
        self.tabla_estudiantes.setHorizontalHeaderLabels([
            "ID", "Estudiante", "Fecha Inscripción", "Estado", "Observaciones"
        ])
        self.tabla_estudiantes.horizontalHeader().setStretchLastSection(True)
        self.tabla_estudiantes.setAlternatingRowColors(True)
        
        layout.addWidget(self.tabla_estudiantes, 1)
        
        # Botones
        botones_layout = QHBoxLayout()
        btn_refrescar = QPushButton("🔄 Actualizar")
        btn_refrescar.clicked.connect(self._actualizar_lista_estudiantes)
        
        btn_inscribir = QPushButton("➕ Inscribir Estudiante")
        btn_inscribir.clicked.connect(self._inscribir_estudiante)
        
        botones_layout.addWidget(btn_refrescar)
        botones_layout.addStretch()
        botones_layout.addWidget(btn_inscribir)
        
        layout.addLayout(botones_layout)
        
        return tab
    
    def crear_tab_pagos(self):
        """Crear pestaña de resumen de pagos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Tabla de resumen de pagos
        self.tabla_resumen_pagos = QTableWidget()
        self.tabla_resumen_pagos.setColumnCount(6)
        self.tabla_resumen_pagos.setHorizontalHeaderLabels([
            "Estudiante", "Matrícula", "Inscripción", "Cuotas Pagadas", 
            "Total Pagado", "Saldo Pendiente"
        ])
        self.tabla_resumen_pagos.horizontalHeader().setStretchLastSection(True)
        self.tabla_resumen_pagos.setAlternatingRowColors(True)
        
        layout.addWidget(self.tabla_resumen_pagos, 1)
        
        # Totales generales
        grupo_totales = QGroupBox("💰 TOTALES GENERALES")
        grid_totales = QGridLayout(grupo_totales)
        
        self.lbl_total_matriculas = QLabel("Total matrículas: $0.00")
        self.lbl_total_inscripciones = QLabel("Total inscripciones: $0.00")
        self.lbl_total_cuotas = QLabel("Total cuotas: $0.00")
        self.lbl_total_general = QLabel("TOTAL INGRESOS: $0.00")
        self.lbl_total_general.setProperty("class", "labelTotalGeneral")
        
        grid_totales.addWidget(self.lbl_total_matriculas, 0, 0)
        grid_totales.addWidget(self.lbl_total_inscripciones, 0, 1)
        grid_totales.addWidget(self.lbl_total_cuotas, 1, 0)
        grid_totales.addWidget(self.lbl_total_general, 1, 1)
        
        layout.addWidget(grupo_totales)
        
        return tab
    
    def setup_conexiones_especificas(self):
        """Configurar conexiones específicas"""
        # Conectar señales para estadísticas
        self.cupos_max_input.valueChanged.connect(self._actualizar_estadisticas)
        self.cupos_inscritos_input.valueChanged.connect(self._actualizar_estadisticas)
        self.costo_total_input.valueChanged.connect(self._actualizar_estadisticas)
        self.costo_matricula_input.valueChanged.connect(self._actualizar_estadisticas)
        self.costo_inscripcion_input.valueChanged.connect(self._actualizar_estadisticas)
        
        # Conectar señales para actualización de descripción
        self.nivel_combo.currentTextChanged.connect(self._actualizar_descripcion)
        self.nombre_input.textChanged.connect(self._actualizar_descripcion)
        self.version_spin.valueChanged.connect(self._actualizar_descripcion)
        self.carrera_combo.currentTextChanged.connect(self._actualizar_descripcion)
        
        # Conectar para detección de edición manual
        self.descripcion_input.textChanged.connect(self._on_descripcion_editada)
        
        # Conectar descuentos
        self.descuento_input.valueChanged.connect(self._actualizar_costos_con_descuento)
        
        # Conectar botón guardar al método on_guardar
        if hasattr(self, 'btn_guardar'):
            self.btn_guardar.clicked.connect(self.on_guardar)
            
        # Conectar botón cancelar
        if hasattr(self, 'btn_cancelar'):
            self.btn_cancelar.clicked.connect(self.close_overlay)
    
    def setup_valores_predeterminados(self):
        """Configurar valores predeterminados"""
        self.nivel_combo.setCurrentText("Maestría")
        self.carrera_combo.setCurrentText("Ing. Informática")
        self._calcular_cuotas()
        self._actualizar_codigo()
        self._actualizar_estadisticas()
        self.nombre_input.setText("Maestría en Ingeniería Informática - Modalidad Virtual UNSXX")
        
        # Inicializar descripción automática
        self.primer_cambio = True
        self.descripcion_automatica = True
        self._actualizar_descripcion(forzar_actualizacion=True)
        
        # Inicializar promoción deshabilitada
        self._habilitar_promocion()
    
    def apply_specific_styles(self):
        """Aplicar estilos específicos para programa overlay"""
        specific_styles = """
        /* ===== ESTILOS PARA GRUPOS CON COLORES LLAMATIVOS ===== */
        
        /* Estilo base para todos los grupos */
        QGroupBox {
            border: 3px solid;
            border-radius: 10px;
            margin-top: 15px;
            padding-top: 18px;
            background-color: #ffffff;
            font-weight: bold;
            font-size: 14px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 4px 12px 4px 12px;
            font-weight: bold;
            font-size: 14px;
            border-radius: 5px;
            color: white;
        }
        
        /* 🌊 IDENTIFICACIÓN UNSXX - Azul vibrante */
        QGroupBox[title="🏛️ IDENTIFICACIÓN UNSXX"] {
            border-color: #3498db;
            background-color: #ebf5fb;
        }
        
        QGroupBox[title="🏛️ IDENTIFICACIÓN UNSXX"]::title {
            background-color: #2980b9;
        }
        
        /* 📚 INFORMACIÓN DEL PROGRAMA - Verde vibrante */
        QGroupBox[title="📚 INFORMACIÓN DEL PROGRAMA"] {
            border-color: #27ae60;
            background-color: #eafaf1;
        }
        
        QGroupBox[title="📚 INFORMACIÓN DEL PROGRAMA"]::title {
            background-color: #229954;
        }
        
        /* ⏳ ESTRUCTURA ACADÉMICA - Naranja vibrante */
        QGroupBox[title="⏳ ESTRUCTURA ACADÉMICA"] {
            border-color: #e67e22;
            background-color: #fef5e7;
        }
        
        QGroupBox[title="⏳ ESTRUCTURA ACADÉMICA"]::title {
            background-color: #d35400;
        }
        
        /* 🎁 PROMOCIONES Y DESCUENTOS - Rosa vibrante */
        QGroupBox[title="🎁 PROMOCIONES Y DESCUENTOS"] {
            border-color: #e91e63;
            background-color: #fce4ec;
        }
        
        QGroupBox[title="🎁 PROMOCIONES Y DESCUENTOS"]::title {
            background-color: #c2185b;
        }
        
        /* 👨‍🏫 DOCENTE COORDINADOR - Púrpura vibrante */
        QGroupBox[title="👨‍🏫 DOCENTE COORDINADOR"] {
            border-color: #8e44ad;
            background-color: #f4ecf7;
        }
        
        QGroupBox[title="👨‍🏫 DOCENTE COORDINADOR"]::title {
            background-color: #7d3c98;
        }
        
        /* 💰 CUPOS Y COSTOS - Rojo vibrante */
        QGroupBox[title="💰 CUPOS Y COSTOS (USD)"] {
            border-color: #e74c3c;
            background-color: #fdedec;
        }
        
        QGroupBox[title="💰 CUPOS Y COSTOS (USD)"]::title {
            background-color: #c0392b;
        }
        
        /* 📅 CALENDARIO ACADÉMICO - Turquesa vibrante */
        QGroupBox[title="📅 CALENDARIO ACADÉMICO"] {
            border-color: #1abc9c;
            background-color: #e8f8f5;
        }
        
        QGroupBox[title="📅 CALENDARIO ACADÉMICO"]::title {
            background-color: #16a085;
        }
        
        /* 📊 RESUMEN DEL PROGRAMA - Gris azulado vibrante */
        QGroupBox[title="📊 RESUMEN DEL PROGRAMA"] {
            border-color: #5d6d7e;
            background-color: #f4f6f7;
        }
        
        QGroupBox[title="📊 RESUMEN DEL PROGRAMA"]::title {
            background-color: #34495e;
        }
        
        /* 💰 TOTALES GENERALES - Dorado vibrante */
        QGroupBox[title="💰 TOTALES GENERALES"] {
            border-color: #f39c12;
            background-color: #fef9e7;
        }
        
        QGroupBox[title="💰 TOTALES GENERALES"]::title {
            background-color: #d68910;
        }
        
        /* ===== ESTILOS PARA COSTO MENSUALIDAD ===== */
        QLabel[class="costoMensualidad"] {
            font-weight: bold;
            font-size: 16px;
            color: #27ae60;
            background: linear-gradient(135deg, #e8f6f3 0%, #d5f4e6 100%);
            border: 2px solid #2ecc71;
            border-radius: 8px;
            padding: 10px;
            min-height: 40px;
        }
        """
        
        current_style = self.styleSheet()
        self.setStyleSheet(current_style + specific_styles)
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _on_nivel_cambiado(self, nivel_texto):
        """Manejador cuando cambia el nivel académico"""
        self.es_posgrado = nivel_texto in ["Maestría", "Doctorado", "Especialidad", "Diplomado"]
        self._actualizar_codigo()
        self._actualizar_descripcion()
    
    def _int_a_romano(self, num):
        """Convertir número entero a número romano"""
        result = ""
        for value, numeral in self.ROMAN_NUMERALS:
            while num >= value:
                result += numeral
                num -= value
        return result
    
    def _actualizar_version_romana(self):
        """Actualizar etiqueta de versión romana"""
        version_num = self.version_spin.value()
        version_romana = self._int_a_romano(version_num)
        self.version_label.setText(version_romana)
        self._actualizar_codigo()
        self._actualizar_descripcion()
    
    def _actualizar_codigo(self):
        """Actualizar código UNSXX generado"""
        try:
            if not self.nivel_combo.currentText() or not self.carrera_combo.currentText():
                self.codigo_construido = ""
                self.codigo_generado_label.setText("Seleccione nivel y carrera")
                self.codigo_hidden.clear()
                return
            
            nivel_abrev = self.NIVELES_ACADEMICOS.get(self.nivel_combo.currentText(), "XXX")
            carrera_abrev = self.carrera_combo.currentData() or "GEN"
            año = str(self.año_input.value())
            version_romana = self.version_label.text()
            
            self.codigo_construido = f"{nivel_abrev}-{carrera_abrev}-{año}-{version_romana}"
            
            if len(self.codigo_construido) > 20:
                año_corto = año[2:]
                self.codigo_construido = f"{nivel_abrev}-{carrera_abrev}-{año_corto}-{version_romana}"
            
            self.codigo_generado_label.setText(self.codigo_construido)
            self.codigo_hidden.setText(self.codigo_construido)
            
        except Exception as e:
            logger.error(f"Error actualizando código: {e}")
            self.codigo_construido = ""
            self.codigo_generado_label.setText("ERROR - Complete todos los campos")
            self.codigo_hidden.clear()
    
    def _actualizar_descripcion(self, forzar_actualizacion=False):
        """Actualizar automáticamente la descripción del programa
        
        Args:
            forzar_actualizacion: Si es True, actualiza incluso si fue editada manualmente
        """
        try:
            # Si la descripción fue editada manualmente y no forzamos actualización, no hacer nada
            if not self.descripcion_automatica and not forzar_actualizacion and not self.primer_cambio:
                return
                
            # Obtener valores actuales
            nivel = self.nivel_combo.currentText()
            carrera = self.carrera_combo.currentText()
            nombre = self.nombre_input.text().strip()
            version_romana = self.version_label.text()
            
            # Si no hay nivel seleccionado
            if not nivel:
                if self.primer_cambio:
                    self.descripcion_input.setPlainText("Seleccione un nivel académico")
                return
            
            # Obtener la descripción actual para comparar
            descripcion_actual = self.descripcion_input.toPlainText()
            
            # Construir nueva descripción
            nueva_descripcion = self._generar_descripcion_automatica(nivel, carrera, nombre, version_romana)
            
            # Solo actualizar si es diferente de la actual
            if nueva_descripcion != descripcion_actual:
                # Guardar posición del cursor si hay foco
                cursor = self.descripcion_input.textCursor()
                cursor_pos = cursor.position() if self.descripcion_input.hasFocus() else 0
                
                self.descripcion_input.setPlainText(nueva_descripcion)
                
                # Restaurar posición del cursor si estaba editando
                if cursor_pos > 0:
                    cursor.setPosition(min(cursor_pos, len(nueva_descripcion)))
                    self.descripcion_input.setTextCursor(cursor)
            
            # Marcar que ya hubo un cambio
            self.primer_cambio = False
            
        except Exception as e:
            logger.error(f"Error actualizando descripción: {e}")
    
    def _generar_descripcion_automatica(self, nivel, carrera, nombre, version_romana):
        """Generar descripción automática según las reglas"""
        
        # Caso 1: Solo nivel (sin nombre)
        if not nombre or nombre.isspace():
            if carrera and carrera != "-- Seleccionar --":
                return f"{nivel} en {carrera}: "
            else:
                return f"{nivel}: "
        
        # Caso 2: Con nombre completo
        # Verificar si el nivel ya está en el nombre
        nivel_lower = nivel.lower()
        nombre_lower = nombre.lower()
        
        if nivel_lower in nombre_lower:
            # El nivel ya está incluido, no duplicar
            if version_romana and version_romana != "I":
                return f"{nombre} - {version_romana} Versión"
            else:
                return nombre
        else:
            # Nivel no incluido, agregarlo
            if version_romana and version_romana != "I":
                return f"{nivel} en: {nombre} - {version_romana} Versión"
            else:
                return f"{nivel} en: {nombre}"
    
    def _alternar_modo_descripcion(self):
        """Alternar entre modo automático y manual de descripción"""
        if self.btn_modo_descripcion.isChecked():
            # Modo automático
            self.descripcion_automatica = True
            self.btn_modo_descripcion.setText("🔄 Auto")
            self._actualizar_descripcion(forzar_actualizacion=True)
        else:
            # Modo manual
            self.descripcion_automatica = False
            self.btn_modo_descripcion.setText("✏️ Manual")
    
    def _on_descripcion_editada(self):
        """Manejador cuando el usuario edita manualmente la descripción"""
        # Si el usuario comienza a editar manualmente, desactivar generación automática
        if self.descripcion_input.hasFocus():
            self.descripcion_automatica = False
            self.btn_modo_descripcion.setChecked(False)
            self.btn_modo_descripcion.setText("✏️ Manual")
    
    def _mapear_estado_a_db(self, estado_form):
        """Mapear el estado del formulario a valores válidos de la base de datos"""
        # Mapeo de estados del formulario a valores válidos del dominio d_estado_programa
        mapeo_estados = {
            # Estados actuales del ComboBox → Valores del dominio
            "PLANIFICADO": "PLANIFICADO",
            "INSCRIPCIONES": "INSCRIPCIONES",        # ¡Agrega esta línea!
            "PRE INSCRIPCIÓN": "INSCRIPCIONES",      # Mapear a INSCRIPCIONES
            "INSCRIPCIONES ABIERTAS": "INSCRIPCIONES", # Mapear a INSCRIPCIONES
            "EN CURSO": "EN_CURSO",
            "EN_CURSO": "EN_CURSO",                  # Para cuando uses EN_CURSO directamente
            "CANCELADO": "CANCELADO",
            "CONCLUIDO": "CONCLUIDO",
            "SUSPENDIDO": "CANCELADO"                # Mapear SUSPENDIDO a CANCELADO
        }
        
        # Buscar coincidencia exacta
        if estado_form in mapeo_estados:
            return mapeo_estados[estado_form]
        
        # Buscar coincidencia parcial (sin espacios, mayúsculas, etc.)
        estado_simplificado = estado_form.upper().replace(" ", "").replace("_", "")
        for key, value in mapeo_estados.items():
            key_simplificado = key.upper().replace(" ", "").replace("_", "")
            if estado_simplificado == key_simplificado:
                return value
        
        # Valor por defecto
        logger.warning(f"Estado no reconocido: '{estado_form}'. Usando 'PLANIFICADO' por defecto.")
        return "PLANIFICADO"
    
    def _actualizar_fecha_fin(self):
        """Actualizar fecha fin basada en duración"""
        fecha_inicio = self.fecha_inicio_input.date()
        meses_duracion = self.duracion_input.value()
        fecha_fin = fecha_inicio.addMonths(meses_duracion)
        self.fecha_fin_input.setDate(fecha_fin)
    
    def _calcular_cuotas(self):
        """Calcular costo por cuota"""
        try:
            costo_total = self.costo_total_input.value()
            numero_cuotas = self.cuotas_input.value()
            
            if numero_cuotas > 0:
                costo_cuota = costo_total / numero_cuotas
                self.costo_cuota_label.setText(f"${costo_cuota:,.2f}")
        except:
            self.costo_cuota_label.setText("$0.00")
    
    def _actualizar_costos_con_descuento(self):
        """Actualizar costos considerando el descuento"""
        try:
            costo_total = self.costo_total_input.value()
            descuento = self.descuento_input.value()
            
            if descuento > 0:
                costo_con_descuento = costo_total * (1 - descuento/100)
                self.lbl_costo_con_descuento.setText(f"Costo con descuento: ${costo_con_descuento:,.2f}")
                self._calcular_cuotas()
        except Exception as e:
            logger.error(f"Error actualizando costos con descuento: {e}")
    
    def _habilitar_promocion(self):
        """Habilitar o deshabilitar controles de promoción"""
        habilitado = self.promocion_checkbox.isChecked()
        self.descuento_input.setEnabled(habilitado)
        self.promocion_desc_input.setEnabled(habilitado)
        self.promocion_valido_hasta_input.setEnabled(habilitado)
        
        if not habilitado:
            self.descuento_input.setValue(0.0)
            self.promocion_desc_input.clear()
            self.promocion_valido_hasta_input.setDate(QDate.currentDate().addDays(30))
    
    def _actualizar_estadisticas(self):
        """Actualizar estadísticas del programa"""
        try:
            cupos_max = self.cupos_max_input.value()
            cupos_inscritos = self.cupos_inscritos_input.value()
            costo_total = self.costo_total_input.value()
            costo_matricula = self.costo_matricula_input.value()
            costo_inscripcion = self.costo_inscripcion_input.value()
            descuento = self.descuento_input.value()
            
            # Calcular cupos disponibles
            cupos_disponibles = max(0, cupos_max - cupos_inscritos)
            porcentaje_ocupacion = (cupos_inscritos / cupos_max * 100) if cupos_max > 0 else 0
            
            # Calcular costos con descuento
            costo_total_con_descuento = costo_total * (1 - descuento/100)
            
            # Calcular ingresos estimados y reales
            ingresos_estimados = cupos_max * costo_total_con_descuento
            ingresos_reales = cupos_inscritos * (costo_matricula + costo_inscripcion)
            saldo_pendiente = (cupos_inscritos * costo_total_con_descuento) - ingresos_reales
            
            # Actualizar labels
            self.lbl_cupos_disponibles.setText(f"Cupos disponibles: {cupos_disponibles}")
            self.lbl_porcentaje_ocupacion.setText(f"Ocupación: {porcentaje_ocupacion:.1f}%")
            self.lbl_ingresos_estimados.setText(f"Ingresos estimados: ${ingresos_estimados:,.2f}")
            self.lbl_ingresos_reales.setText(f"Ingresos reales: ${ingresos_reales:,.2f}")
            self.lbl_saldo_pendiente.setText(f"Saldo pendiente: ${saldo_pendiente:,.2f}")
            self.lbl_costo_con_descuento.setText(f"Costo con descuento: ${costo_total_con_descuento:,.2f}")
            
        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
    
    def _actualizar_lista_estudiantes(self):
        """Actualizar lista de estudiantes (simulada)"""
        self.tabla_estudiantes.setRowCount(0)
        # Datos de ejemplo
        pass
    
    def _inscribir_estudiante(self):
        """Mostrar diálogo para inscribir estudiante"""
        self.mostrar_mensaje("Inscribir Estudiante", 
                            "Esta función abriría un diálogo para inscribir un nuevo estudiante.", 
                            "info")
    
    def _actualizar_resumen_pagos(self):
        """Actualizar resumen de pagos (simulado)"""
        self.tabla_resumen_pagos.setRowCount(0)
        # Datos de ejemplo
        pass
    
    def _cargar_docentes_desde_db(self):
        """Cargar docentes desde la base de datos"""
        try:
            self.docente_coordinador_combo.clear()
            self.docente_coordinador_combo.addItem("-- Seleccionar Docente --", None)
            
            # Cargar docentes activos desde la base de datos
            docentes = DocenteModel.obtener_docentes_activos()
            
            if docentes:
                for docente in docentes:
                    nombre_completo = f"{docente.get('nombres', '')} {docente.get('apellido_paterno', '')}"
                    especialidad = docente.get('especialidad', '')
                    if especialidad:
                        display_text = f"{nombre_completo} ({especialidad})"
                    else:
                        display_text = nombre_completo
                    
                    self.docente_coordinador_combo.addItem(display_text, docente.get('id'))
            else:
                self.docente_coordinador_combo.addItem("-- No hay docentes disponibles --", None)
                logger.warning("No se encontraron docentes activos")
                
        except Exception as e:
            logger.error(f"Error cargando docentes: {e}")
            self.docente_coordinador_combo.addItem("-- Error cargando docentes --", None)
    
    # ===== IMPLEMENTACIÓN DE MÉTODOS BASE =====
    
    def validar_formulario(self):
        """Validar todos los campos del formulario"""
        errores = []
        
        # Validar código
        if not self.codigo_construido or 'ERROR' in self.codigo_construido:
            errores.append("El código UNSXX no es válido")
        elif not self.validar_codigo_unico(self.codigo_construido):
            errores.append(f"El código {self.codigo_construido} ya está registrado en el sistema")
            
        # Validar nombre
        nombre = self.nombre_input.text().strip()
        if not nombre:
            errores.append("Debe completar el nombre oficial del programa")
            
        # Validar duración
        if self.duracion_input.value() <= 0:
            errores.append("La duración en meses debe ser mayor a 0")
            
        # Validar horas
        if self.horas_input.value() <= 0:
            errores.append("Las horas totales deben ser mayores a 0")
            
        # Validar costo
        if self.costo_total_input.value() <= 0:
            errores.append("El costo total debe ser mayor a 0")
            
        # Validar cupos máximos vs inscritos
        if self.cupos_inscritos_input.value() > self.cupos_max_input.value():
            errores.append("Los cupos inscritos no pueden exceder los cupos máximos")
            
        # Validar número de cuotas
        if self.cuotas_input.value() <= 0:
            errores.append("El número de cuotas debe ser mayor a 0")
            
        return len(errores) == 0, errores
    
    def validar_codigo_unico(self, codigo: str) -> bool:
        """Validar si el código es único en la base de datos"""
        try:
            from model.programa_model import ProgramaModel
            
            # Asegurarnos de que codigo no sea None
            if not codigo:
                return False
            
            # Si estamos editando, excluir el ID actual
            excluir_id = self.programa_id if self.modo == "editar" and self.programa_id else None
            
            # Llamar al método corregido (ver cambios en modelo)
            return not ProgramaModel.verificar_codigo_existente(codigo, excluir_id)
        except Exception as e:
            logger.error(f"Error validando código único: {e}")
            return True  # Permitir continuar si hay error
    
    def obtener_datos(self):
        """Obtener todos los datos del formulario para la función PostgreSQL"""
        logger.debug("DEBUG - ProgramaOverlay.obtener_datos()")
        
        costo_total = float(self.costo_total_input.value())
        numero_cuotas = self.cuotas_input.value()
        descuento = float(self.descuento_input.value())
        
        # Calcular costo mensualidad (costo por cuota)
        if numero_cuotas > 0:
            costo_mensualidad = costo_total / numero_cuotas
        else:
            costo_mensualidad = 0
            
        docente_coordinador_id = None
        current_data = self.docente_coordinador_combo.currentData()
        if current_data:
            docente_coordinador_id = current_data
            
        nombre_oficial = self.nombre_input.text().strip() if self.nombre_checkbox.isChecked() else ""
        
        # IMPORTANTE: Obtener la descripción actual
        descripcion = self.descripcion_input.toPlainText().strip()
        
        # Preparar fechas
        fecha_inicio = self.fecha_inicio_input.date()
        fecha_fin = self.fecha_fin_input.date()
        
        # Convertir a string o None
        fecha_inicio_str = fecha_inicio.toString("yyyy-MM-dd") if fecha_inicio.isValid() else None
        fecha_fin_str = fecha_fin.toString("yyyy-MM-dd") if fecha_fin.isValid() else None
        
        # Datos de promoción
        promocion_valido_hasta = None
        if self.promocion_checkbox.isChecked():
            promocion_valido_hasta = self.promocion_valido_hasta_input.date()
            promocion_valido_hasta_str = promocion_valido_hasta.toString("yyyy-MM-dd") if promocion_valido_hasta.isValid() else None
        else:
            promocion_valido_hasta_str = None
        
            # Obtener estado del ComboBox y mapearlo a valor válido de BD
        estado_form = self.estado_input.currentText()
        estado_db = self._mapear_estado_a_db(estado_form)
            
        datos = {
            "codigo": self.codigo_construido,
            "nombre": nombre_oficial,
            "descripcion": descripcion,
            "duracion_meses": self.duracion_input.value(),
            "horas_totales": self.horas_input.value(),
            "costo_total": costo_total,
            "costo_matricula": float(self.costo_matricula_input.value()),
            "costo_inscripcion": float(self.costo_inscripcion_input.value()),
            "costo_mensualidad": round(costo_mensualidad, 2),
            "numero_cuotas": numero_cuotas,
            "cupos_maximos": self.cupos_max_input.value(),
            "cupos_inscritos": self.cupos_inscritos_input.value(),
            "estado": estado_db,
            "fecha_inicio": fecha_inicio_str,
            "fecha_fin": fecha_fin_str,
            "docente_coordinador_id": docente_coordinador_id,
            "promocion_descuento": descuento,
            "promocion_descripcion": self.promocion_desc_input.text().strip(),
            "promocion_valido_hasta": promocion_valido_hasta_str
        }
        
        logger.debug(f"DEBUG - ProgramaOverlay.obtener_datos() datos preparados: {datos}")
        
        return datos
    
    def clear_form(self):
        """Limpiar todos los campos del formulario"""
        self.programa_id = None
        self.nivel_combo.setCurrentIndex(0)
        self.carrera_combo.setCurrentIndex(0)
        self.año_input.setValue(QDate.currentDate().year())
        self.version_spin.setValue(1)
        self._actualizar_codigo()
        
        self.nombre_input.clear()
        self.nombre_checkbox.setChecked(True)
        
        # Resetear descripción automática
        self.descripcion_automatica = True
        self.primer_cambio = True
        self.btn_modo_descripcion.setChecked(True)
        self.btn_modo_descripcion.setText("🔄 Auto")
        self._actualizar_descripcion(forzar_actualizacion=True)
        
        self.duracion_input.setValue(24)
        self.horas_input.setValue(1200)
        self.estado_input.setCurrentText("PLANIFICADO")
        
        # Limpiar promociones
        self.promocion_checkbox.setChecked(False)
        self.descuento_input.setValue(0.0)
        self.promocion_desc_input.clear()
        self.promocion_valido_hasta_input.setDate(QDate.currentDate().addDays(30))
        self._habilitar_promocion()
        
        self.cupos_max_input.setValue(30)
        self.cupos_inscritos_input.setValue(0)
        self.costo_total_input.setValue(5000.00)
        self.costo_matricula_input.setValue(200.00)
        self.costo_inscripcion_input.setValue(50.00)
        self.cuotas_input.setValue(10)
        
        self.docente_coordinador_combo.setCurrentIndex(0)
        
        hoy = QDate.currentDate()
        self.fecha_inicio_input.setDate(hoy.addDays(60))
        self._actualizar_fecha_fin()
        
        self._calcular_cuotas()
        self._actualizar_estadisticas()
        
        if hasattr(self, 'tabla_estudiantes'):
            self.tabla_estudiantes.setRowCount(0)
        
        if hasattr(self, 'tabla_resumen_pagos'):
            self.tabla_resumen_pagos.setRowCount(0)
    
    def cargar_datos(self, datos):
        """Cargar datos en el formulario"""
        logger.debug(f"DEBUG - ProgramaOverlay.cargar_datos() datos recibidos: {datos}")
        self.programa_id = datos.get('id')
        
        # Establecer el código primero
        if 'codigo' in datos:
            self.codigo_hidden.setText(datos['codigo'])
            self.codigo_generado_label.setText(datos['codigo'])
            self.codigo_construido = datos['codigo']
        
        # Extraer componentes del código para nivel y carrera
        if 'codigo' in datos and datos['codigo']:
            codigo_parts = datos['codigo'].split('-')
            if len(codigo_parts) >= 2:
                nivel_abrev = codigo_parts[0]
                carrera_abrev = codigo_parts[1]
                
                # Buscar nivel por abreviatura
                for nivel, abrev in self.NIVELES_ACADEMICOS.items():
                    if abrev == nivel_abrev:
                        self.nivel_combo.setCurrentText(nivel)
                        break
                
                # Buscar carrera por abreviatura
                for i in range(self.carrera_combo.count()):
                    if self.carrera_combo.itemData(i) == carrera_abrev:
                        self.carrera_combo.setCurrentIndex(i)
                        break
        
        # Año y versión
        if 'codigo' in datos and datos['codigo']:
            codigo_parts = datos['codigo'].split('-')
            if len(codigo_parts) >= 4:
                try:
                    año = int(codigo_parts[2]) if len(codigo_parts[2]) == 4 else int("20" + codigo_parts[2])
                    self.año_input.setValue(año)
                except:
                    pass
        
        if 'nombre' in datos:
            self.nombre_input.setText(datos['nombre'])
            self.nombre_checkbox.setChecked(bool(datos['nombre']))
        
        # Cargar datos numéricos
        campos_numericos = [
            ('duracion_meses', self.duracion_input),
            ('horas_totales', self.horas_input),
            ('cupos_maximos', self.cupos_max_input),
            ('cupos_inscritos', self.cupos_inscritos_input),
            ('costo_total', self.costo_total_input),
            ('costo_matricula', self.costo_matricula_input),
            ('costo_inscripcion', self.costo_inscripcion_input),
            ('numero_cuotas', self.cuotas_input),
            ('promocion_descuento', self.descuento_input)
        ]
        
        for campo, widget in campos_numericos:
            if campo in datos and datos[campo] is not None:
                if isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(datos[campo]))
                else:
                    widget.setValue(int(datos[campo]))
        
        if 'estado' in datos:
            index = self.estado_input.findText(datos['estado'])
            if index >= 0:
                self.estado_input.setCurrentIndex(index)
        
        # Cargar descripción
        if 'descripcion' in datos and datos['descripcion']:
            self.descripcion_automatica = False
            self.btn_modo_descripcion.setChecked(False)
            self.btn_modo_descripcion.setText("✏️ Manual")
            self.descripcion_input.setPlainText(datos['descripcion'])
        else:
            # Si no hay descripción, generar automáticamente
            self.descripcion_automatica = True
            self.btn_modo_descripcion.setChecked(True)
            self.btn_modo_descripcion.setText("🔄 Auto")
            self._actualizar_descripcion(forzar_actualizacion=True)
        
        # Cargar promociones
        if 'promocion_descripcion' in datos and datos['promocion_descripcion']:
            self.promocion_checkbox.setChecked(True)
            self.promocion_desc_input.setText(datos['promocion_descripcion'])
        
        if 'promocion_valido_hasta' in datos and datos['promocion_valido_hasta']:
            fecha = QDate.fromString(str(datos['promocion_valido_hasta']), "yyyy-MM-dd")
            if fecha.isValid():
                self.promocion_valido_hasta_input.setDate(fecha)
        
        # Cargar docente coordinador
        if 'docente_coordinador_id' in datos and datos['docente_coordinador_id']:
            docente_id = datos['docente_coordinador_id']
            self._cargar_docentes_desde_db()
            
            # Esperar un momento para que se carguen los docentes
            QTimer.singleShot(100, lambda: self._seleccionar_docente(docente_id))
        
        if 'fecha_inicio' in datos and datos['fecha_inicio']:
            fecha_inicio = QDate.fromString(str(datos['fecha_inicio']), "yyyy-MM-dd")
            if fecha_inicio.isValid():
                self.fecha_inicio_input.setDate(fecha_inicio)
        
        if 'fecha_fin' in datos and datos['fecha_fin']:
            fecha_fin = QDate.fromString(str(datos['fecha_fin']), "yyyy-MM-dd")
            if fecha_fin.isValid():
                self.fecha_fin_input.setDate(fecha_fin)
        
        self._calcular_cuotas()
        self._actualizar_estadisticas()
        self._habilitar_promocion()
    
    def _seleccionar_docente(self, docente_id):
        """Seleccionar docente en el comboBox"""
        for i in range(self.docente_coordinador_combo.count()):
            if self.docente_coordinador_combo.itemData(i) == docente_id:
                self.docente_coordinador_combo.setCurrentIndex(i)
                break
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo"):
        """Mostrar el overlay con configuración específica"""
        self.solo_lectura = solo_lectura
        self.set_modo(modo)
        
        if datos:
            self.cargar_datos(datos)
        elif modo == "nuevo":
            self.clear_form()
        
        # Cargar docentes
        self._cargar_docentes_desde_db()
        
        # Configurar botón de guardar según el modo
        if hasattr(self, 'btn_guardar'):
            if modo == "nuevo":
                self.btn_guardar.setText("💾 GUARDAR PROGRAMA")
            elif modo == "editar":
                self.btn_guardar.setText("💾 ACTUALIZAR PROGRAMA")
        
        # Llamar al método base
        super().show_form(solo_lectura)
    
    def on_guardar(self):
        """Método sobrescrito para manejar el guardado con señales específicas"""
        valido, errores = self.validar_formulario()

        if not valido:
            errores_str = "\n".join(errores)
            QMessageBox.warning(self, "Error de validación", 
                                f"Por favor corrija los siguientes errores:\n\n{errores_str}")
            return

        try:
            # Importar modelo aquí para evitar dependencias circulares
            from model.programa_model import ProgramaModel

            datos = self.obtener_datos()
            

            # Agregar ID si estamos en modo edición
            if self.modo == "editar" and self.programa_id:
                datos['id'] = self.programa_id

            # LLAMAR AL MODELO DIRECTAMENTE
            if self.modo == "nuevo":
                # Crear nuevo programa
                resultado = ProgramaModel.crear_programa(datos)
                if resultado.get('success'):
                    self.programa_guardado.emit(resultado.get('data', datos))
                    QMessageBox.information(self, "Éxito", "Programa creado exitosamente")
                    self.close_overlay()
                else:
                    QMessageBox.critical(self, "Error", resultado.get('message', 'Error desconocido'))

            elif self.modo == "editar":
                # Actualizar programa existente                
                resultado = ProgramaModel.actualizar_programa(datos["id"], datos)
                if resultado.get('success'):
                    self.programa_actualizado.emit(resultado.get('data', datos))
                    QMessageBox.information(self, "Éxito", "Programa actualizado exitosamente")
                    self.close_overlay()
                else:
                    QMessageBox.critical(self, "Error", resultado.get('message', 'Error desconocido'))

            logger.info(f"✅ Programa {'creado' if self.modo == 'nuevo' else 'actualizado'}: {datos.get('codigo')}")

        except Exception as e:
            logger.error(f"❌ Error al guardar programa: {e}")
            QMessageBox.critical(self, "Error", 
                                f"Error al guardar el programa:\n\n{str(e)}")