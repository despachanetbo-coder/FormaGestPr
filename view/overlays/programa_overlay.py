# view/overlays/programa_overlay.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QComboBox, QDateEdit, QGroupBox, QGridLayout,
    QScrollArea, QFrame, QSizePolicy, QCheckBox,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, 
    QSplitter, QTabWidget
)
from PySide6.QtCore import Qt, QDate, QTimer, Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator
from typing import List, Optional, Dict, Any, Tuple
import logging

# Importar modelo de docentes
from model.docente_model import DocenteModel
from .base_overlay import BaseOverlay

logger = logging.getLogger(__name__)

class ProgramaOverlay(BaseOverlay):
    """Overlay para crear/editar/ver programas académicos con campos específicos de la tabla"""
    
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
    
    # Números romanos del 1 al 20
    NUMEROS_ROMANOS = [
        "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
        "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent, "🏛️ Programa Académico - UNSXX", 95, 95)
        
        # Variables específicas
        self.programa_id: Optional[int] = None
        self.codigo_construido = ""
        self.es_posgrado = False
        self.solo_lectura = False
        self._cerrando = False
        
        # Variables para control de descripción automática
        self.descripcion_automatica = True
        self.primer_cambio = True
        
        # Configurar UI específica
        self.setup_ui_especifica()
        self.setup_conexiones_especificas()
        self.setup_valores_predeterminados()
        
        # Aplicar estilos específicos
        self.apply_specific_styles()
    
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

        # ===== COLUMNA IZQUIERDA (siempre visible) =====
        scroll_izquierda = QScrollArea()
        scroll_izquierda.setWidgetResizable(True)
        scroll_izquierda.setFrameShape(QFrame.Shape.NoFrame)

        widget_izquierda = QWidget()
        layout_izquierda = QVBoxLayout(widget_izquierda)
        layout_izquierda.setContentsMargins(5, 5, 10, 5)

        # Grupo: Identificación UNSXX
        grupo_identificacion = self.crear_grupo_identificacion()
        layout_izquierda.addWidget(grupo_identificacion)

        # Grupo: Información del Programa
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

        layout_izquierda.addStretch()

        scroll_izquierda.setWidget(widget_izquierda)
        splitter.addWidget(scroll_izquierda)

        # ===== COLUMNA DERECHA (solo visible en modo edición/visualización) =====
        self.widget_derecha = QWidget()
        layout_derecha = QVBoxLayout(self.widget_derecha)
        layout_derecha.setContentsMargins(10, 5, 5, 5)

        # Grupo: Resumen del Programa
        grupo_resumen = self.crear_grupo_resumen()
        layout_derecha.addWidget(grupo_resumen)

        scroll_derecha = QScrollArea()
        scroll_derecha.setWidgetResizable(True)
        

        # Pestañas para estudiantes y pagos
        tab_widget = QTabWidget()
        tab_widget.setMinimumHeight(400)

        # Pestaña 1: Estudiantes inscritos
        tab_estudiantes = self.crear_tab_estudiantes()
        tab_widget.addTab(tab_estudiantes, "👥 Estudiantes")

        # Pestaña 2: Resumen de Pagos
        tab_pagos = self.crear_tab_pagos()
        tab_widget.addTab(tab_pagos, "💵 Pagos")

        scroll_derecha.setWidget(tab_widget)

        layout_derecha.addWidget(scroll_derecha, 1)

        splitter.addWidget(self.widget_derecha)

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

        # === PRIMERA FILA: Código UNSXX ===
        codigo_fila = QHBoxLayout()

        codigo_label = QLabel("Código UNSXX:*")
        codigo_label.setProperty("class", "labelObligatorio")
        codigo_label.setFixedWidth(120)
        codigo_fila.addWidget(codigo_label)

        self.codigo_generado_label = QLabel("Seleccione nivel y carrera")
        self.codigo_generado_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.codigo_generado_label.setMinimumHeight(30)
        self.codigo_generado_label.setObjectName("codigoGeneradoLabel")
        self.codigo_generado_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        codigo_fila.addWidget(self.codigo_generado_label, 1)

        # Campo oculto para el código
        self.codigo_hidden = QLineEdit()
        self.codigo_hidden.setVisible(False)
        codigo_fila.addWidget(self.codigo_hidden)

        layout.addLayout(codigo_fila)

        # === SEGUNDA FILA: Nivel Académico y Carrera/Programa ===
        fila_nivel_carrera = QHBoxLayout()

        # Nivel Académico
        nivel_label = QLabel("Nivel Académico:*")
        nivel_label.setProperty("class", "labelObligatorio")
        nivel_label.setFixedWidth(120)
        fila_nivel_carrera.addWidget(nivel_label)

        self.nivel_combo = QComboBox()
        self.nivel_combo.addItems(list(self.NIVELES_ACADEMICOS.keys()))
        self.nivel_combo.currentTextChanged.connect(self._on_nivel_cambiado)
        self.nivel_combo.setMinimumWidth(200)
        fila_nivel_carrera.addWidget(self.nivel_combo)

        # Espacio entre campos
        fila_nivel_carrera.addSpacing(20)

        # Carrera/Programa
        carrera_label = QLabel("Carrera/Programa:*")
        carrera_label.setProperty("class", "labelObligatorio")
        carrera_label.setFixedWidth(120)
        fila_nivel_carrera.addWidget(carrera_label)

        self.carrera_combo = QComboBox()
        for nombre, abrev in self.CARRERAS_UNSXX:
            self.carrera_combo.addItem(nombre, abrev)
        self.carrera_combo.currentIndexChanged.connect(self._actualizar_codigo)
        self.carrera_combo.setMinimumWidth(200)
        fila_nivel_carrera.addWidget(self.carrera_combo)

        fila_nivel_carrera.addStretch()
        layout.addLayout(fila_nivel_carrera)

        # === TERCERA FILA: Año Académico y Versión ===
        fila_año_version = QHBoxLayout()

        # Año Académico
        año_label = QLabel("Año Académico:*")
        año_label.setProperty("class", "labelObligatorio")
        año_label.setFixedWidth(120)
        fila_año_version.addWidget(año_label)

        self.año_input = QLineEdit()
        self.año_input.setText(str(QDate.currentDate().year()))
        self.año_input.textChanged.connect(self._actualizar_codigo)
        validator_año = QIntValidator(2000, 2100, self)
        self.año_input.setValidator(validator_año)
        self.año_input.setFixedWidth(100)
        fila_año_version.addWidget(self.año_input)

        # Espacio entre campos
        fila_año_version.addSpacing(20)

        # Versión
        version_label = QLabel("Versión:")
        version_label.setFixedWidth(120)
        fila_año_version.addWidget(version_label)

        self.version_combo = QComboBox()
        self.version_combo.addItems(self.NUMEROS_ROMANOS)
        self.version_combo.setCurrentIndex(0)
        self.version_combo.currentIndexChanged.connect(self._on_version_cambiado)
        self.version_combo.setFixedWidth(100)
        fila_año_version.addWidget(self.version_combo)

        fila_año_version.addStretch()
        layout.addLayout(fila_año_version)

        return grupo

    def crear_grupo_programa(self):
        """Crear grupo de información del programa con campos de la tabla"""
        grupo = QGroupBox("📚 INFORMACIÓN DEL PROGRAMA")

        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(12, 20, 12, 15)
        layout.setSpacing(12)

        # === PRIMERA FILA: Nombre Oficial ===
        fila_nombre = QHBoxLayout()

        nombre_label = QLabel("Nombre Oficial:*")
        nombre_label.setProperty("class", "labelObligatorio")
        nombre_label.setFixedWidth(120)
        fila_nombre.addWidget(nombre_label)

        self.nombre_input = QLineEdit()
        self.nombre_input.setPlaceholderText("Ej: Maestría en Enfermería - Modalidad Virtual UNSXX")
        self.nombre_input.textChanged.connect(self._actualizar_descripcion)
        fila_nombre.addWidget(self.nombre_input, 1)

        layout.addLayout(fila_nombre)

        # === SEGUNDA FILA: Descripción del Programa ===
        fila_descripcion = QHBoxLayout()

        desc_label = QLabel("Descripción del Programa:")
        desc_label.setFixedWidth(120)
        fila_descripcion.addWidget(desc_label)

        self.descripcion_input = QLineEdit()
        self.descripcion_input.setPlaceholderText("La descripción se genera automáticamente...")
        self.descripcion_input.setMaximumHeight(35)
        self.descripcion_input.setReadOnly(True)  # Solo lectura para que sea automática
        fila_descripcion.addWidget(self.descripcion_input, 1)

        layout.addLayout(fila_descripcion)

        return grupo
    
    def crear_grupo_estructura(self):
        """Crear grupo de estructura académica con campos de la tabla"""
        grupo = QGroupBox("⏳ ESTRUCTURA ACADÉMICA")
        
        grid = QGridLayout(grupo)
        grid.setContentsMargins(12, 20, 12, 15)
        grid.setSpacing(12)
        
        # Fila 1 - Duración (meses) (campo de la tabla)
        grid.addWidget(QLabel("Duración (meses):*"), 0, 0)
        self.duracion_input = QLineEdit()
        self.duracion_input.setText("24")
        validator_duracion = QIntValidator(1, 60, self)
        self.duracion_input.setValidator(validator_duracion)
        self.duracion_input.textChanged.connect(self._actualizar_fecha_fin)
        grid.addWidget(self.duracion_input, 0, 1)
        
        # Carga Horaria (campo de la tabla)
        grid.addWidget(QLabel("Carga Horaria:*"), 0, 2)
        self.horas_input = QLineEdit()
        self.horas_input.setText("1200")
        validator_horas = QIntValidator(40, 10000, self)
        self.horas_input.setValidator(validator_horas)
        grid.addWidget(self.horas_input, 0, 3)
        
        # Fila 2 - Estado (campo de la tabla)
        grid.addWidget(QLabel("Estado:*"), 1, 0)
        self.estado_input = QComboBox()
        self.estado_input.addItems(["PLANIFICADO", "INSCRIPCIONES", "EN_CURSO", "CONCLUIDO", "CANCELADO"])
        grid.addWidget(self.estado_input, 1, 1)
        
        return grupo
    
    def crear_grupo_docente(self):
        """Crear grupo de docente coordinador (campo de la tabla)"""
        grupo = QGroupBox("👨‍🏫 DOCENTE COORDINADOR")

        layout = QVBoxLayout(grupo)
        layout.setContentsMargins(12, 20, 12, 15)
        layout.setSpacing(12)

        # === FILA: Docente Coordinador y ComboBox ===
        fila_docente = QHBoxLayout()

        docente_label = QLabel("Docente Coordinador:")
        docente_label.setFixedWidth(120)  # Mismo ancho que los otros labels
        fila_docente.addWidget(docente_label)

        self.docente_coordinador_combo = QComboBox()
        self.docente_coordinador_combo.addItem("-- Seleccionar Docente --", None)
        fila_docente.addWidget(self.docente_coordinador_combo, 1)  # El 1 permite que se expanda

        fila_docente.addStretch()

        layout.addLayout(fila_docente)

        return grupo
    
    def crear_grupo_cupos_costos(self):
        """Crear grupo de cupos y costos (campos de la tabla)"""
        grupo = QGroupBox("💰 CUPOS Y COSTOS (USD)")
        
        grid = QGridLayout(grupo)
        grid.setContentsMargins(12, 20, 12, 15)
        grid.setSpacing(12)
        
        # Fila 1 - Cupos (campos de la tabla)
        grid.addWidget(QLabel("Cupos máximos:*"), 0, 0)
        self.cupos_max_input = QLineEdit()
        self.cupos_max_input.setText("30")
        validator_cupos_max = QIntValidator(1, 500, self)
        self.cupos_max_input.setValidator(validator_cupos_max)
        self.cupos_max_input.textChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.cupos_max_input, 0, 1)
        
        grid.addWidget(QLabel("Cupos inscritos:*"), 0, 2)
        self.cupos_inscritos_input = QLineEdit()
        self.cupos_inscritos_input.setText("0")
        validator_cupos_inscritos = QIntValidator(0, 500, self)
        self.cupos_inscritos_input.setValidator(validator_cupos_inscritos)
        self.cupos_inscritos_input.textChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.cupos_inscritos_input, 0, 3)
        
        # Fila 2 - Costos principales (campos de la tabla)
        grid.addWidget(QLabel("Costo total:*"), 1, 0)
        self.costo_total_input = QLineEdit()
        self.costo_total_input.setText("5000.00")
        validator_costo_total = QDoubleValidator(0.0, 50000.0, 2, self)
        validator_costo_total.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.costo_total_input.setValidator(validator_costo_total)
        self.costo_total_input.textChanged.connect(self._calcular_cuotas)
        grid.addWidget(self.costo_total_input, 1, 1)
        
        grid.addWidget(QLabel("Número de cuotas:*"), 1, 2)
        self.cuotas_input = QLineEdit()
        self.cuotas_input.setText("10")
        validator_cuotas = QIntValidator(1, 36, self)
        self.cuotas_input.setValidator(validator_cuotas)
        self.cuotas_input.textChanged.connect(self._calcular_cuotas)
        grid.addWidget(self.cuotas_input, 1, 3)
        
        # Fila 3 - Costos adicionales (campos de la tabla)
        grid.addWidget(QLabel("Costo matrícula:*"), 2, 0)
        self.costo_matricula_input = QLineEdit()
        self.costo_matricula_input.setText("200.00")
        validator_matricula = QDoubleValidator(0.0, 5000.0, 2, self)
        validator_matricula.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.costo_matricula_input.setValidator(validator_matricula)
        self.costo_matricula_input.textChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.costo_matricula_input, 2, 1)
        
        grid.addWidget(QLabel("Costo inscripción:*"), 2, 2)
        self.costo_inscripcion_input = QLineEdit()
        self.costo_inscripcion_input.setText("50.00")
        validator_inscripcion = QDoubleValidator(0.0, 500.0, 2, self)
        validator_inscripcion.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.costo_inscripcion_input.setValidator(validator_inscripcion)
        self.costo_inscripcion_input.textChanged.connect(self._actualizar_estadisticas)
        grid.addWidget(self.costo_inscripcion_input, 2, 3)
        
        # Fila 4: Costo por cuota (calculado, campo de la tabla)
        grid.addWidget(QLabel("Costo mensualidad:*"), 3, 0)
        self.costo_cuota_label = QLabel("Bs. 500.00")
        self.costo_cuota_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.costo_cuota_label.setProperty("class", "costoMensualidad")
        grid.addWidget(self.costo_cuota_label, 3, 1, 1, 3)
        
        return grupo
    
    def crear_grupo_calendario(self):
        """Crear grupo de calendario académico (campos de la tabla)"""
        grupo = QGroupBox("📅 CALENDARIO ACADÉMICO")

        layout = QHBoxLayout(grupo)
        layout.setContentsMargins(12, 20, 12, 15)
        layout.setSpacing(20)  # Espacio entre los dos campos

        # === Fecha Inicio (con label arriba) ===
        fecha_inicio_container = QVBoxLayout()
        fecha_inicio_container.setSpacing(5)

        fecha_inicio_label = QLabel("Fecha inicio:*")
        fecha_inicio_label.setProperty("class", "labelObligatorio")
        fecha_inicio_container.addWidget(fecha_inicio_label)

        self.fecha_inicio_input = QDateEdit()
        self.fecha_inicio_input.setCalendarPopup(True)
        self.fecha_inicio_input.setDate(QDate.currentDate().addDays(60))
        self.fecha_inicio_input.dateChanged.connect(self._actualizar_fecha_fin)
        self.fecha_inicio_input.setMinimumWidth(150)
        fecha_inicio_container.addWidget(self.fecha_inicio_input)

        layout.addLayout(fecha_inicio_container)

        # === Fecha Fin (con label arriba) ===
        fecha_fin_container = QVBoxLayout()
        fecha_fin_container.setSpacing(5)

        fecha_fin_label = QLabel("Fecha fin estimada:")
        fecha_fin_container.addWidget(fecha_fin_label)

        self.fecha_fin_input = QDateEdit()
        self.fecha_fin_input.setCalendarPopup(True)
        self.fecha_fin_input.setDate(QDate.currentDate().addDays(60 + 730))
        self.fecha_fin_input.setMinimumWidth(150)
        fecha_fin_container.addWidget(self.fecha_fin_input)

        layout.addLayout(fecha_fin_container)

        layout.addStretch()  # Para mantener los campos alineados a la izquierda

        return grupo
    
    def crear_grupo_resumen(self):
        """Crear grupo de resumen del programa"""
        grupo = QGroupBox("📊 RESUMEN DEL PROGRAMA")

        grid = QGridLayout(grupo)
        grid.setContentsMargins(12, 20, 12, 15)
        grid.setSpacing(12)

        # Fila 1 - Cupos
        self.lbl_cupos_disponibles = QLabel("Cupos disponibles: 0")
        self.lbl_cupos_disponibles.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_cupos_disponibles, 0, 0)

        self.lbl_porcentaje_ocupacion = QLabel("Ocupación: 0.00%")
        self.lbl_porcentaje_ocupacion.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_porcentaje_ocupacion, 0, 1)

        # Fila 2 - Ingresos Estimados Totales
        self.lbl_ingresos_estimados = QLabel("Ingresos estimados: 0 Bs.")
        self.lbl_ingresos_estimados.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_ingresos_estimados, 1, 0, 1, 2)

        # Fila 3 - Detalle de Estimados
        self.lbl_estimado_matricula = QLabel("Estimado por Matrícula: 0 Bs.")
        self.lbl_estimado_matricula.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_estimado_matricula, 2, 0)

        self.lbl_estimado_inscripcion = QLabel("Estimado por Inscripción: 0 Bs.")
        self.lbl_estimado_inscripcion.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_estimado_inscripcion, 2, 1)

        # Fila 4 - Ingresos Reales Totales
        self.lbl_ingresos_reales = QLabel("Ingresos reales: 0 Bs.")
        self.lbl_ingresos_reales.setProperty("class", "labelEstadistica")
        self.lbl_ingresos_reales.setStyleSheet("font-weight: bold; color: #27ae60;")
        grid.addWidget(self.lbl_ingresos_reales, 3, 0, 1, 2)

        # Fila 5 - Detalle de Reales
        self.lbl_real_matricula = QLabel("Real Matrícula: 0 Bs.")
        self.lbl_real_matricula.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_real_matricula, 4, 0)

        self.lbl_real_inscripcion = QLabel("Real Inscripción: 0 Bs.")
        self.lbl_real_inscripcion.setProperty("class", "labelEstadistica")
        grid.addWidget(self.lbl_real_inscripcion, 4, 1)

        # Fila 6 - Saldo Pendiente
        self.lbl_saldo_pendiente = QLabel("Saldo pendiente: 0 Bs.")
        self.lbl_saldo_pendiente.setProperty("class", "labelEstadistica")
        self.lbl_saldo_pendiente.setStyleSheet("font-weight: bold; color: #e74c3c;")
        grid.addWidget(self.lbl_saldo_pendiente, 5, 0, 1, 2)

        return grupo
    
    def crear_tab_estudiantes(self):
        """Crear pestaña de estudiantes inscritos"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Tabla de estudiantes
        self.tabla_estudiantes = QTableWidget()
        self.tabla_estudiantes.setColumnCount(6)
        self.tabla_estudiantes.setHorizontalHeaderLabels([
            "ID", "Estudiante", "Fecha Inscripción", "Estado", "Observaciones", "Acciones"
        ])
        self.tabla_estudiantes.horizontalHeader().setStretchLastSection(False)
        self.tabla_estudiantes.setAlternatingRowColors(True)
        self.tabla_estudiantes.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.tabla_estudiantes, 1)

        # Botones
        botones_layout = QHBoxLayout()
        btn_refrescar = QPushButton("🔄 Actualizar")
        btn_refrescar.clicked.connect(self._actualizar_lista_estudiantes)
        btn_refrescar.setFixedHeight(35)

        btn_inscribir = QPushButton("➕ Inscribir Estudiante")
        # IMPORTANTE: Verificar que esta conexión existe
        btn_inscribir.clicked.connect(self._inscribir_estudiante)
        btn_inscribir.setFixedHeight(35)
        btn_inscribir.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 5px 15px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)

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
        grupo_totales.setStyleSheet("Margin-top: 8px; padding: 5px;")
        grid_totales = QGridLayout(grupo_totales)
        
        self.lbl_total_matriculas = QLabel("Total matrículas: Bs. 0.00")
        self.lbl_total_inscripciones = QLabel("Total inscripciones: Bs. 0.00")
        self.lbl_total_cuotas = QLabel("Total cuotas: Bs. 0.00")
        self.lbl_total_general = QLabel("TOTAL INGRESOS: Bs. 0.00")
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
        self.cupos_max_input.textChanged.connect(self._actualizar_estadisticas)
        self.cupos_inscritos_input.textChanged.connect(self._actualizar_estadisticas)
        self.costo_total_input.textChanged.connect(self._actualizar_estadisticas)
        self.costo_matricula_input.textChanged.connect(self._actualizar_estadisticas)
        self.costo_inscripcion_input.textChanged.connect(self._actualizar_estadisticas)
        
        # Conectar señales para actualización de descripción
        self.nivel_combo.currentTextChanged.connect(self._actualizar_descripcion)
        self.nombre_input.textChanged.connect(self._actualizar_descripcion)
        self.carrera_combo.currentTextChanged.connect(self._actualizar_descripcion)
        # La versión ya tiene su propia conexión en _on_version_cambiado
        
        # Conectar botón guardar al método on_guardar
        if hasattr(self, 'btn_guardar'):
            self.btn_guardar.clicked.connect(self.on_guardar)
            
        # Conectar botón cancelar/cerrar al método close_overlay
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
        QGroupBox#grupoIdentificacion {
            border-color: #3498db;
            background-color: #ebf5fb;
        }
        
        QGroupBox#grupoIdentificacion::title {
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
        
        /* ===== ESTILOS PARA MODO LECTURA ===== */
        QLabel#codigoGeneradoLabel[readonly="true"] {
            background-color: #f5f5f5;
            border: 1px solid #ccc;
            padding: 8px;
            border-radius: 4px;
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
    
    def _on_version_cambiado(self):
        """Manejador cuando cambia la versión - actualiza código y descripción"""
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
            
            # Obtener año
            año_text = self.año_input.text().strip()
            if not año_text:
                año = str(QDate.currentDate().year())
                self.año_input.setText(año)
            else:
                año = año_text
            
            version_romana = self.version_combo.currentText()
            
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
        """Actualizar automáticamente la descripción del programa"""
        try:
            # Obtener valores actuales
            nivel = self.nivel_combo.currentText()
            carrera = self.carrera_combo.currentText()
            nombre = self.nombre_input.text().strip()
            version_romana = self.version_combo.currentText()
            
            # Si no hay nivel seleccionado
            if not nivel:
                if self.primer_cambio:
                    self.descripcion_input.setText("Seleccione un nivel académico")
                return
            
            # Construir nueva descripción
            nueva_descripcion = self._generar_descripcion_automatica(nivel, carrera, nombre, version_romana)
            
            # Solo actualizar si es diferente de la actual
            if nueva_descripcion != self.descripcion_input.text():
                self.descripcion_input.setText(nueva_descripcion)
            
            # Marcar que ya hubo un cambio
            self.primer_cambio = False
            
        except Exception as e:
            logger.error(f"Error actualizando descripción: {e}")
    
    def _generar_descripcion_automatica(self, nivel, carrera, nombre, version_romana):
        """Generar descripción automática según las reglas"""
        
        # Caso 1: Solo nivel (sin nombre)
        if not nombre or nombre.isspace():
            if carrera and carrera != "-- Seleccionar --":
                return f"{nivel} en {carrera}"
            else:
                return f"{nivel}"
        
        # Caso 2: Con nombre completo
        nivel_lower = nivel.lower()
        nombre_lower = nombre.lower()
        
        # Verificar si la versión no es la predeterminada (I)
        sufijo_version = ""
        if version_romana and version_romana != "I":
            sufijo_version = f" {version_romana} Versión"
        
        if nivel_lower in nombre_lower:
            # El nivel ya está incluido, no duplicar
            return f"{nombre}{sufijo_version}"
        else:
            # Nivel no incluido, agregarlo
            return f"{nivel} en: {nombre}{sufijo_version}"
    
    def _mapear_estado_a_db(self, estado_form):
        """Mapear el estado del formulario a valores válidos de la base de datos"""
        mapeo_estados = {
            "PLANIFICADO": "PLANIFICADO",
            "INSCRIPCIONES": "INSCRIPCIONES",
            "PRE INSCRIPCIÓN": "INSCRIPCIONES",
            "INSCRIPCIONES ABIERTAS": "INSCRIPCIONES",
            "EN CURSO": "EN_CURSO",
            "EN_CURSO": "EN_CURSO",
            "CANCELADO": "CANCELADO",
            "CONCLUIDO": "CONCLUIDO",
            "SUSPENDIDO": "CANCELADO"
        }
        
        # Buscar coincidencia exacta
        if estado_form in mapeo_estados:
            return mapeo_estados[estado_form]
        
        # Buscar coincidencia parcial
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
        try:
            fecha_inicio = self.fecha_inicio_input.date()
            duracion_text = self.duracion_input.text().strip()
            if not duracion_text:
                meses_duracion = 24
                self.duracion_input.setText("24")
            else:
                meses_duracion = int(duracion_text)
                
            fecha_fin = fecha_inicio.addMonths(meses_duracion)
            self.fecha_fin_input.setDate(fecha_fin)
        except ValueError:
            pass
    
    def _calcular_cuotas(self):
        """Calcular costo por cuota"""
        try:
            # Obtener costo total
            costo_total_text = self.costo_total_input.text().strip()
            if not costo_total_text:
                costo_total = 5000.00
                self.costo_total_input.setText("5000.00")
            else:
                costo_total = float(costo_total_text)
            
            # Obtener número de cuotas
            cuotas_text = self.cuotas_input.text().strip()
            if not cuotas_text:
                numero_cuotas = 10
                self.cuotas_input.setText("10")
            else:
                numero_cuotas = int(cuotas_text)
            
            if numero_cuotas > 0:
                costo_cuota = costo_total / numero_cuotas
                self.costo_cuota_label.setText(f"Bs. {costo_cuota:,.2f}")
        except:
            self.costo_cuota_label.setText("Bs. 0.00")
    
    def _actualizar_estadisticas(self):
        """Actualizar estadísticas del programa con cálculos mejorados"""
        try:
            # Verificar si tenemos un ID de programa válido
            if not self.programa_id:
                return

            # Obtener valores de los campos
            cupos_max_text = self.cupos_max_input.text().strip()
            cupos_inscritos_text = self.cupos_inscritos_input.text().strip()
            costo_total_text = self.costo_total_input.text().strip()
            costo_matricula_text = self.costo_matricula_input.text().strip()
            costo_inscripcion_text = self.costo_inscripcion_input.text().strip()

            # Convertir valores
            cupos_max = int(cupos_max_text) if cupos_max_text else 0
            cupos_inscritos = int(cupos_inscritos_text) if cupos_inscritos_text else 0
            costo_total = float(costo_total_text) if costo_total_text else 0.0
            costo_matricula = float(costo_matricula_text) if costo_matricula_text else 0.0
            costo_inscripcion = float(costo_inscripcion_text) if costo_inscripcion_text else 0.0

            # Calcular cupos disponibles y ocupación
            cupos_disponibles = max(0, cupos_max - cupos_inscritos)
            porcentaje_ocupacion = (cupos_inscritos / cupos_max * 100) if cupos_max > 0 else 0

            # Calcular ingresos estimados
            ingresos_estimados_totales = cupos_inscritos * costo_total
            estimado_matricula = cupos_inscritos * costo_matricula
            estimado_inscripcion = cupos_inscritos * costo_inscripcion

            # Obtener ingresos reales desde la base de datos usando TransaccionModel
            ingresos_reales_totales = 0.0
            real_matricula = 0.0
            real_inscripcion = 0.0
            real_mensualidades = 0.0

            if self.programa_id:
                try:
                    from model.transaccion_model import TransaccionModel

                    # Obtener todos los totales reales de una sola vez
                    totales = TransaccionModel.obtener_totales_reales_programa(self.programa_id)

                    real_matricula = totales['matricula']
                    real_inscripcion = totales['inscripcion']
                    real_mensualidades = totales['mensualidad']
                    ingresos_reales_totales = totales['total']
                except Exception as e:
                    logger.error(f"Error obteniendo ingresos reales: {e}")
                    # En caso de error, no actualizar los valores reales
                    pass
                
            # Calcular saldo pendiente
            saldo_pendiente = ingresos_estimados_totales - ingresos_reales_totales

            # Actualizar labels con formato Bs.
            self.lbl_cupos_disponibles.setText(f"Cupos disponibles: {cupos_disponibles}")
            self.lbl_porcentaje_ocupacion.setText(f"Ocupación: {porcentaje_ocupacion:.2f}%")

            self.lbl_ingresos_estimados.setText(f"Ingresos estimados: {ingresos_estimados_totales:,.2f} Bs.")
            self.lbl_estimado_matricula.setText(f"Estimado por Matrícula: {estimado_matricula:,.2f} Bs.")
            self.lbl_estimado_inscripcion.setText(f"Estimado por Inscripción: {estimado_inscripcion:,.2f} Bs.")

            self.lbl_ingresos_reales.setText(f"Ingresos reales: {ingresos_reales_totales:,.2f} Bs.")
            self.lbl_real_matricula.setText(f"Real Matrícula: {real_matricula:,.2f} Bs.")
            self.lbl_real_inscripcion.setText(f"Real Inscripción: {real_inscripcion:,.2f} Bs.")

            self.lbl_saldo_pendiente.setText(f"Saldo pendiente: {saldo_pendiente:,.2f} Bs.")

        except Exception as e:
            logger.error(f"Error actualizando estadísticas: {e}")
    
    def _actualizar_lista_estudiantes(self):
        """Actualizar lista de estudiantes (simulada)"""
        self._cargar_estudiantes_inscritos()
    
    def _inscribir_estudiante(self):
        """Abrir diálogo para inscribir estudiante al programa actual"""
        if not self.programa_id:
            QMessageBox.warning(self, "Error", "Debe guardar el programa primero antes de inscribir estudiantes")
            return

        try:
            from view.overlays.inscripcion_overlay import InscripcionOverlay

            # Crear el overlay
            inscripcion_overlay = InscripcionOverlay(self)

            # Conectar señales
            inscripcion_overlay.inscripcion_creada.connect(self._on_inscripcion_guardada)

            # Mostrar el overlay
            inscripcion_overlay.show_form(
                solo_lectura=False,
                modo="nuevo",
                programa_id=self.programa_id
            )

        except ImportError as e:
            logger.error(f"Error importando InscripcionOverlay: {e}")
            QMessageBox.critical(self, "Error de Importación", 
                                f"No se pudo importar el módulo de inscripción:\n{str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado abriendo inscripción: {e}")
            QMessageBox.critical(self, "Error Inesperado", 
                                f"Error al abrir inscripción:\n{str(e)}")
    
    def _on_inscripcion_guardada(self, datos_inscripcion):
        """Manejador cuando se guarda una nueva inscripción"""
        # Verificar que la inscripción corresponde a este programa
        # El ID del programa puede venir en diferentes formatos
        programa_id_inscripcion = None

        if isinstance(datos_inscripcion, dict):
            # Si viene como diccionario plano
            programa_id_inscripcion = datos_inscripcion.get('programa_id')

            # Si viene anidado en 'data'
            if not programa_id_inscripcion and 'data' in datos_inscripcion:
                programa_id_inscripcion = datos_inscripcion['data'].get('programa_id')

        if programa_id_inscripcion == self.programa_id:
            try:
                from model.inscripcion_model import InscripcionModel

                # Obtener conteo actualizado de inscripciones
                inscripciones = InscripcionModel.obtener_inscripciones_por_programa(self.programa_id)

                if inscripciones is not None:
                    # Actualizar cupos inscritos
                    cupos_actuales = len(inscripciones)
                    self.cupos_inscritos_input.setText(str(cupos_actuales))

                    # Recargar tabla de estudiantes
                    self._cargar_estudiantes_inscritos()

                    # Actualizar estadísticas
                    self._actualizar_estadisticas()

                    # Mostrar mensaje de confirmación
                    QMessageBox.information(self, "✅ Éxito", 
                        f"Estudiante inscrito exitosamente.\n\n"
                        f"Cupos actuales: {cupos_actuales}")
                else:
                    logger.warning("No se pudo obtener el conteo de inscripciones")

            except Exception as e:
                logger.error(f"Error actualizando cupos después de inscripción: {e}")
    
    def _actualizar_resumen_pagos(self):
        """Actualizar resumen de pagos (simulado)"""
        self.tabla_resumen_pagos.setRowCount(0)
    
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
    
    def _seleccionar_docente(self, docente_id):
        """Seleccionar docente en el comboBox"""
        for i in range(self.docente_coordinador_combo.count()):
            if self.docente_coordinador_combo.itemData(i) == docente_id:
                self.docente_coordinador_combo.setCurrentIndex(i)
                break
    
    # ===== MÉTODOS PARA BLOQUEO DE CAMPOS EN MODO LECTURA =====
    
    def _bloquear_todos_los_campos(self, bloqueado=True):
        """Bloquear o desbloquear todos los campos del formulario"""
        
        # Lista de widgets editables
        widgets_editables = [
            self.nivel_combo,
            self.carrera_combo,
            self.año_input,
            self.version_combo,
            self.nombre_input,
            self.duracion_input,
            self.horas_input,
            self.estado_input,
            self.docente_coordinador_combo,
            self.cupos_max_input,
            self.cupos_inscritos_input,
            self.costo_total_input,
            self.cuotas_input,
            self.costo_matricula_input,
            self.costo_inscripcion_input,
            self.fecha_inicio_input,
            self.fecha_fin_input,
        ]
        
        # Agregar btn_guardar si existe
        if hasattr(self, 'btn_guardar') and self.btn_guardar is not None:
            widgets_editables.append(self.btn_guardar)
        
        # Aplicar bloqueo a widgets editables
        for widget in widgets_editables:
            if widget is not None:
                widget.setEnabled(not bloqueado)
        
        # ===== MANEJO DE BOTONES EN PESTAÑAS =====
        # Buscar el QTabWidget en la UI
        tab_widget = self.findChild(QTabWidget)
        if tab_widget is not None and tab_widget.count() > 0:
            # Obtener la pestaña de estudiantes (índice 0)
            tab_estudiantes = tab_widget.widget(0)
            if tab_estudiantes is not None:
                # Buscar TODOS los botones en la pestaña
                botones = tab_estudiantes.findChildren(QPushButton)
                
                for boton in botones:
                    if boton is not None:
                        # Botones que SIEMPRE deben estar habilitados
                        texto_boton = boton.text().upper()
                        
                        # Botón de INSCRIBIR - SIEMPRE habilitado
                        if "INSCRIBIR" in texto_boton:
                            boton.setEnabled(True)
                        
                        # Botón de ACTUALIZAR/REFRESCAR - SIEMPRE habilitado
                        elif "ACTUALIZAR" in texto_boton or "REFRESCAR" in texto_boton or "🔄" in boton.text():
                            boton.setEnabled(True)
                        
                        # Botón VER detalle - también puede ser útil mantenerlo habilitado
                        elif "VER" in texto_boton or "👁️" in boton.text():
                            boton.setEnabled(True)
                        
                        # Otros botones sí se bloquean según el modo
                        else:
                            boton.setEnabled(not bloqueado)
        
        # El botón cancelar/cerrar siempre debe estar habilitado
        if hasattr(self, 'btn_cancelar') and self.btn_cancelar is not None:
            self.btn_cancelar.setEnabled(True)
        
        # Configurar estilo para modo lectura
        if bloqueado:
            self.codigo_generado_label.setProperty("readonly", "true")
            self.codigo_generado_label.setStyleSheet("""
                QLabel#codigoGeneradoLabel[readonly="true"] {
                    background-color: #f5f5f5;
                    border: 1px solid #ccc;
                    padding: 8px;
                    border-radius: 4px;
                }
            """)
        else:
            self.codigo_generado_label.setProperty("readonly", "false")
            self.codigo_generado_label.setStyleSheet("")
    
    # ===== IMPLEMENTACIÓN DE MÉTODOS BASE =====
    
    def validar_formulario(self):
        """Validar todos los campos del formulario"""
        errores = []
        
        # Validar código
        if not self.codigo_construido or 'ERROR' in self.codigo_construido:
            errores.append("El código UNSXX no es válido")
        elif self.validar_codigo_unico(self.codigo_construido):
            if self.modo == "nuevo":
                errores.append(f"El código {self.codigo_construido} ya está registrado en el sistema")
            
        # Validar nombre
        nombre = self.nombre_input.text().strip()
        if not nombre:
            errores.append("Debe completar el nombre oficial del programa")
            
        # Validar duración
        duracion_text = self.duracion_input.text().strip()
        if not duracion_text:
            errores.append("Debe completar la duración en meses")
        else:
            try:
                duracion = int(duracion_text)
                if duracion <= 0:
                    errores.append("La duración en meses debe ser mayor a 0")
            except ValueError:
                errores.append("La duración debe ser un número válido")
            
        # Validar horas
        horas_text = self.horas_input.text().strip()
        if not horas_text:
            errores.append("Debe completar las horas totales")
        else:
            try:
                horas = int(horas_text)
                if horas <= 0:
                    errores.append("Las horas totales deben ser mayores a 0")
            except ValueError:
                errores.append("Las horas totales deben ser un número válido")
            
        # Validar costo
        costo_total_text = self.costo_total_input.text().strip()
        if not costo_total_text:
            errores.append("Debe completar el costo total")
        else:
            try:
                costo_total = float(costo_total_text)
                if costo_total <= 0:
                    errores.append("El costo total debe ser mayor a 0")
            except ValueError:
                errores.append("El costo total debe ser un número válido")
            
        # Validar cupos máximos vs inscritos
        cupos_max_text = self.cupos_max_input.text().strip()
        cupos_inscritos_text = self.cupos_inscritos_input.text().strip()
        
        if cupos_max_text and cupos_inscritos_text:
            try:
                cupos_max = int(cupos_max_text)
                cupos_inscritos = int(cupos_inscritos_text)
                if cupos_inscritos > cupos_max:
                    errores.append("Los cupos inscritos no pueden exceder los cupos máximos")
            except ValueError:
                errores.append("Los cupos deben ser números válidos")
            
        # Validar número de cuotas
        cuotas_text = self.cuotas_input.text().strip()
        if not cuotas_text:
            errores.append("Debe completar el número de cuotas")
        else:
            try:
                cuotas = int(cuotas_text)
                if cuotas <= 0:
                    errores.append("El número de cuotas debe ser mayor a 0")
            except ValueError:
                errores.append("El número de cuotas debe ser un número válido")
            
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
            
            # Llamar al método corregido
            return ProgramaModel.verificar_codigo_existente(codigo, excluir_id)
        except Exception as e:
            logger.error(f"Error validando código único: {e}")
            return False  # En caso de error, asumimos que no existe
    
    def obtener_datos(self):
        """Obtener todos los datos del formulario para la función PostgreSQL"""
        
        # Obtener valores de los campos de texto
        costo_total_text = self.costo_total_input.text().strip()
        numero_cuotas_text = self.cuotas_input.text().strip()
        
        # Convertir valores con valores por defecto si están vacíos
        costo_total = float(costo_total_text) if costo_total_text else 5000.00
        numero_cuotas = int(numero_cuotas_text) if numero_cuotas_text else 10
            
        # Calcular costo mensualidad (costo por cuota)
        if numero_cuotas > 0:
            costo_mensualidad = round(costo_total / numero_cuotas, 2)
        else:
            costo_mensualidad = 0.0
            
        docente_coordinador_id = None
        current_data = self.docente_coordinador_combo.currentData()
        if current_data:
            docente_coordinador_id = current_data
            
        nombre_oficial = self.nombre_input.text().strip()
        
        # IMPORTANTE: Obtener la descripción actual
        descripcion = self.descripcion_input.text().strip()
        
        # Preparar fechas
        fecha_inicio = self.fecha_inicio_input.date()
        fecha_fin = self.fecha_fin_input.date()
        
        # Convertir a string o None
        fecha_inicio_str = fecha_inicio.toString("yyyy-MM-dd") if fecha_inicio.isValid() else None
        fecha_fin_str = fecha_fin.toString("yyyy-MM-dd") if fecha_fin.isValid() else None
        
        # Obtener estado del ComboBox y mapearlo a valor válido de BD
        estado_form = self.estado_input.currentText()
        estado_db = self._mapear_estado_a_db(estado_form)
        
        # Convertir otros valores numéricos
        duracion_text = self.duracion_input.text().strip()
        horas_text = self.horas_input.text().strip()
        cupos_max_text = self.cupos_max_input.text().strip()
        cupos_inscritos_text = self.cupos_inscritos_input.text().strip()
        costo_matricula_text = self.costo_matricula_input.text().strip()
        costo_inscripcion_text = self.costo_inscripcion_input.text().strip()
        
        datos = {
            "codigo": self.codigo_construido,
            "nombre": nombre_oficial,
            "descripcion": descripcion,
            "duracion_meses": int(duracion_text),
            "horas_totales": int(horas_text),
            "costo_total": float(costo_total),
            "costo_matricula": float(costo_matricula_text),
            "costo_inscripcion": float(costo_inscripcion_text) if costo_inscripcion_text else 50.00,
            "costo_mensualidad": float(round(costo_mensualidad, 2)),
            "numero_cuotas": int(numero_cuotas),
            "cupos_maximos": int(cupos_max_text),
            "cupos_inscritos": int(cupos_inscritos_text) if cupos_inscritos_text else 0,
            "estado": estado_db,
            "fecha_inicio": fecha_inicio_str,
            "fecha_fin": fecha_fin_str,
            "docente_coordinador_id": docente_coordinador_id
        }
        
        return datos
    
    def clear_form(self):
        """Limpiar todos los campos del formulario"""
        self.programa_id = None
        self.nivel_combo.setCurrentIndex(0)
        self.carrera_combo.setCurrentIndex(0)
        self.año_input.setText(str(QDate.currentDate().year()))
        self.version_combo.setCurrentIndex(0)
        self._actualizar_codigo()
        
        self.nombre_input.clear()
        
        # Resetear descripción automática
        self.descripcion_automatica = True
        self.primer_cambio = True
        self._actualizar_descripcion(forzar_actualizacion=True)
        
        self.duracion_input.setText("24")
        self.horas_input.setText("1200")
        self.estado_input.setCurrentText("PLANIFICADO")
        
        self.cupos_max_input.setText("30")
        self.cupos_inscritos_input.setText("0")
        self.costo_total_input.setText("5000.00")
        self.costo_matricula_input.setText("200.00")
        self.costo_inscripcion_input.setText("50.00")
        self.cuotas_input.setText("10")
        
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
        self.programa_id = datos.get('id')
        
        # ANTES de cargar los datos, verificar si el programa debe concluirse
        if self.programa_id and self.modo != "nuevo":
            from service.programa_estado_service import ProgramaEstadoService

            # Verificar si este programa específico debe ser concluido
            resultado = ProgramaEstadoService.verificar_programa_especifico(self.programa_id)

            if resultado.get('actualizado'):
                # Si se actualizó, recargar los datos del programa
                from model.programa_model import ProgramaModel
                datos_actualizados = ProgramaModel.obtener_por_id(self.programa_id)
                if datos_actualizados:
                    datos = datos_actualizados
                    # Mostrar notificación al usuario
                    QMessageBox.information(
                        self, 
                        "ℹ️ Actualización Automática",
                        f"El programa ha sido concluido automáticamente porque su fecha de fin ({datos.get('fecha_fin')}) "
                        f"es anterior o igual a la fecha actual ({QDate.currentDate().toString('dd/MM/yyyy')})."
                    )

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
                    self.año_input.setText(str(año))

                    # Establecer versión romana
                    version_romana = codigo_parts[3]
                    index = self.version_combo.findText(version_romana)
                    if index >= 0:
                        self.version_combo.setCurrentIndex(index)
                except:
                    pass
                
        if 'nombre' in datos:
            self.nombre_input.setText(datos['nombre'])

        # Cargar datos numéricos como texto
        campos_numericos = [
            ('duracion_meses', self.duracion_input),
            ('horas_totales', self.horas_input),
            ('cupos_maximos', self.cupos_max_input),
            ('cupos_inscritos', self.cupos_inscritos_input),
            ('numero_cuotas', self.cuotas_input),
        ]

        for campo, widget in campos_numericos:
            if campo in datos and datos[campo] is not None:
                widget.setText(str(datos[campo]))

        # Cargar datos decimales como texto
        campos_decimales = [
            ('costo_total', self.costo_total_input),
            ('costo_matricula', self.costo_matricula_input),
            ('costo_inscripcion', self.costo_inscripcion_input)
        ]

        for campo, widget in campos_decimales:
            if campo in datos and datos[campo] is not None:
                widget.setText(str(datos[campo]))

        if 'estado' in datos:
            index = self.estado_input.findText(datos['estado'])
            if index >= 0:
                self.estado_input.setCurrentIndex(index)

        # Cargar descripción
        if 'descripcion' in datos and datos['descripcion']:
            self.descripcion_input.setText(datos['descripcion'])
        else:
            # Si no hay descripción, generar automáticamente
            self._actualizar_descripcion(forzar_actualizacion=True)

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

        # IMPORTANTE: Usar una bandera para evitar múltiples actualizaciones
        if hasattr(self, '_estadisticas_actualizadas'):
            return

        # Actualizar estadísticas solo si no es modo nuevo
        if self.modo != "nuevo":
            # Usar un solo timer con un tiempo razonable
            QTimer.singleShot(300, self._actualizar_estadisticas_unica)
            self._estadisticas_actualizadas = True
    
    def _actualizar_estadisticas_unica(self):
        """
        Versión única de actualización de estadísticas con control para evitar
        múltiples llamadas simultáneas.
        """
        # Verificar si ya hay una actualización en curso
        if hasattr(self, '_actualizando_estadisticas') and self._actualizando_estadisticas:
            return

        self._actualizando_estadisticas = True

        try:
            # Llamar al método original de actualización
            self._actualizar_estadisticas()
        finally:
            # Liberar la bandera después de un tiempo
            QTimer.singleShot(1000, lambda: setattr(self, '_actualizando_estadisticas', False))
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo"):
        """Mostrar el overlay con configuración específica"""
        self.solo_lectura = solo_lectura
    
        # IMPORTANTE: Si solo_lectura es True, forzar modo="ver"
        if solo_lectura:
            modo = "ver"
    
        self.set_modo(modo)
    
        # Mostrar/ocultar columna derecha según el modo
        if hasattr(self, 'widget_derecha'):
            if modo == "nuevo":
                self.widget_derecha.setVisible(False)
                splitter = self.findChild(QSplitter, "mainSplitter")
                if splitter:
                    splitter.setSizes([1000, 0])
            else:
                self.widget_derecha.setVisible(True)
                splitter = self.findChild(QSplitter, "mainSplitter")
                if splitter:
                    splitter.setSizes([500, 500])
        
        if datos:
            self.cargar_datos(datos)
            if self.programa_id:
                QTimer.singleShot(200, self._cargar_estudiantes_inscritos)
        elif modo == "nuevo":
            self.clear_form()
            
        # Cargar docentes
        self._cargar_docentes_desde_db()
        
        # Configurar botón de guardar según el modo
        if hasattr(self, 'btn_guardar') and self.btn_guardar is not None:
            try:
                self.btn_guardar.clicked.disconnect()
            except:
                pass
            
            if modo == "nuevo":
                self.btn_guardar.setText("💾 GUARDAR PROGRAMA")
                self.btn_guardar.clicked.connect(self.on_guardar)
                self.btn_guardar.setVisible(True)
            elif modo == "editar":
                self.btn_guardar.setText("💾 ACTUALIZAR PROGRAMA")
                self.btn_guardar.clicked.connect(self.on_guardar)
                self.btn_guardar.setVisible(True)
            elif modo == "ver" or solo_lectura:
                self.btn_guardar.setText("✅ CERRAR")
                self.btn_guardar.clicked.connect(self.close_overlay)
                self.btn_guardar.setVisible(True)
    
        # Configurar botón cancelar/cerrar
        if hasattr(self, 'btn_cancelar') and self.btn_cancelar is not None:
            try:
                self.btn_cancelar.clicked.disconnect()
            except:
                pass
            self.btn_cancelar.clicked.connect(self.close_overlay)
    
            if modo == "ver" or solo_lectura:
                self.btn_cancelar.setText("✕ CERRAR")
    
        # BLOQUEAR CAMPOS SI ES MODO LECTURA
        if solo_lectura or modo == "ver":
            self._bloquear_todos_los_campos(True)
        else:
            self._bloquear_todos_los_campos(False)
    
        # Resetear flag de cierre
        self._cerrando = False
    
        # Llamar al método base
        super().show_form(solo_lectura)
    
    def close_overlay(self):
        """Sobrescribir método close_overlay para asegurar cierre correcto"""
        # Verificar si ya estamos en proceso de cierre
        if hasattr(self, '_cerrando') and self._cerrando:
            return

        self._cerrando = True

        # Limpiar banderas
        if hasattr(self, '_estadisticas_actualizadas'):
            delattr(self, '_estadisticas_actualizadas')
        if hasattr(self, '_actualizando_estadisticas'):
            delattr(self, '_actualizando_estadisticas')

        # Llamar al método base
        super().close_overlay()

        # Limpiar datos después del cierre (solo si no es modo vista)
        if self.modo != "ver" and not self.solo_lectura:
            QTimer.singleShot(100, self.clear_form)

        # Resetear flag después de un tiempo
        QTimer.singleShot(500, lambda: setattr(self, '_cerrando', False))
    
    def on_guardar(self):
        """Método sobrescrito para manejar el guardado con señales específicas"""
        
        # Si es modo lectura, simplemente cerrar
        if self.solo_lectura or self.modo == "ver":
            self.close_overlay()
            return
        
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
                    programa_guardado = resultado.get('data', datos)
                    
                    # Emitir señal con los datos completos
                    self.programa_guardado.emit(programa_guardado)
                    
                    # Mostrar mensaje de éxito
                    QMessageBox.information(self, "✅ Éxito", 
                                            f"Programa creado exitosamente\n\nCódigo: {programa_guardado.get('codigo', 'N/A')}")
                    
                    # Cerrar este overlay
                    self.close_overlay()
                else:
                    QMessageBox.critical(self, "❌ Error", 
                                        resultado.get('message', 'Error desconocido al crear el programa'))
            
            elif self.modo == "editar":
                # Actualizar programa existente                
                resultado = ProgramaModel.actualizar_programa(datos["id"], datos)
                if resultado.get('success'):
                    programa_actualizado = resultado.get('data', datos)
                    
                    # Emitir señal
                    self.programa_actualizado.emit(programa_actualizado)
                    
                    # Mostrar mensaje de éxito
                    QMessageBox.information(self, "✅ Éxito", 
                                            f"Programa actualizado exitosamente\n\nCódigo: {programa_actualizado.get('codigo', 'N/A')}")
                    
                    # Cerrar este overlay
                    self.close_overlay()
                else:
                    QMessageBox.critical(self, "❌ Error", 
                                        resultado.get('message', 'Error desconocido al actualizar el programa'))
        
        except Exception as e:
            logger.error(f"Error al guardar programa: {e}")
            QMessageBox.critical(self, "❌ Error", 
                                f"Error al guardar el programa:\n\n{str(e)}")
    
    def _cargar_estudiantes_inscritos(self):
        """Cargar estudiantes inscritos en el programa desde la base de datos"""
        if not self.programa_id:
            return

        try:
            from model.inscripcion_model import InscripcionModel

            # Limpiar tabla
            self.tabla_estudiantes.setRowCount(0)

            # Obtener inscripciones del programa
            inscripciones = InscripcionModel.obtener_inscripciones_por_programa(self.programa_id)

            if not inscripciones:
                # Mostrar mensaje de que no hay estudiantes
                self.tabla_estudiantes.setRowCount(1)
                item = QTableWidgetItem("No hay estudiantes inscritos en este programa")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.tabla_estudiantes.setItem(0, 0, item)
                self.tabla_estudiantes.setSpan(0, 0, 1, 5)
                return

            # Configurar la tabla
            self.tabla_estudiantes.setColumnCount(6)  # Aumentamos a 6 columnas
            self.tabla_estudiantes.setHorizontalHeaderLabels([
                "ID Inscripción", "Estudiante", "Fecha Inscripción", 
                "Estado", "Observaciones", "Acciones"
            ])

            # Llenar tabla con datos
            for row, inscripcion in enumerate(inscripciones):
                self.tabla_estudiantes.insertRow(row)

                # ID Inscripción
                id_item = QTableWidgetItem(str(inscripcion.get('id', '')))
                id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                id_item.setData(Qt.ItemDataRole.UserRole, inscripcion.get('id'))  # Guardar ID
                self.tabla_estudiantes.setItem(row, 0, id_item)

                # Estudiante (nombre completo)
                estudiante_nombre = self._formatear_nombre_estudiante(inscripcion)
                nombre_item = QTableWidgetItem(estudiante_nombre)
                self.tabla_estudiantes.setItem(row, 1, nombre_item)

                # Fecha Inscripción
                fecha_insc = inscripcion.get('fecha_inscripcion', '')
                if fecha_insc:
                    try:
                        from datetime import datetime
                        fecha_obj = datetime.fromisoformat(str(fecha_insc))
                        fecha_str = fecha_obj.strftime("%d/%m/%Y")
                    except:
                        fecha_str = str(fecha_insc)
                else:
                    fecha_str = ''
                fecha_item = QTableWidgetItem(fecha_str)
                fecha_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla_estudiantes.setItem(row, 2, fecha_item)

                # Estado
                estado = inscripcion.get('estado', 'ACTIVO')
                estado_item = QTableWidgetItem(estado)
                estado_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                # Colorear según estado
                if estado == 'ACTIVO':
                    estado_item.setForeground(Qt.GlobalColor.darkGreen)
                elif estado == 'PENDIENTE':
                    estado_item.setForeground(Qt.GlobalColor.darkYellow)
                elif estado == 'CANCELADO':
                    estado_item.setForeground(Qt.GlobalColor.darkRed)
                elif estado == 'CONCLUIDO':
                    estado_item.setForeground(Qt.GlobalColor.darkBlue)

                self.tabla_estudiantes.setItem(row, 3, estado_item)

                # Observaciones
                observaciones = inscripcion.get('observaciones', '')
                obs_item = QTableWidgetItem(observaciones)
                self.tabla_estudiantes.setItem(row, 4, obs_item)

                # Botón Ver detalles (opcional)
                btn_ver = QPushButton("👁️ Ver")
                btn_ver.clicked.connect(lambda checked, i=inscripcion: self._ver_detalle_inscripcion(i))
                self.tabla_estudiantes.setCellWidget(row, 5, btn_ver)

            # Ajustar columnas
            self.tabla_estudiantes.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Columna estudiante se estira
            self.tabla_estudiantes.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # Columna observaciones se estira
            self.tabla_estudiantes.setColumnWidth(0, 100)  # ID
            self.tabla_estudiantes.setColumnWidth(2, 120)  # Fecha
            self.tabla_estudiantes.setColumnWidth(3, 100)  # Estado
            self.tabla_estudiantes.setColumnWidth(5, 80)   # Acciones

        except Exception as e:
            logger.error(f"Error cargando estudiantes inscritos: {e}")
            self.tabla_estudiantes.setRowCount(1)
            item = QTableWidgetItem(f"Error al cargar estudiantes: {str(e)}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabla_estudiantes.setItem(0, 0, item)
            self.tabla_estudiantes.setSpan(0, 0, 1, 5)
    
    def _formatear_nombre_estudiante(self, inscripcion):
        """Formatear nombre completo del estudiante"""
        try:
            # Intentar obtener datos del estudiante anidado
            estudiante = inscripcion.get('estudiante', {})
            if estudiante:
                nombres = estudiante.get('nombres', '')
                apellido_paterno = estudiante.get('apellido_paterno', '')
                apellido_materno = estudiante.get('apellido_materno', '')

                if apellido_materno:
                    return f"{apellido_paterno} {apellido_materno}, {nombres}".strip()
                else:
                    return f"{apellido_paterno}, {nombres}".strip()
            else:
                # Si no hay datos anidados, buscar directamente
                nombres = inscripcion.get('nombres', '')
                apellidos = inscripcion.get('apellidos', '')
                if nombres and apellidos:
                    return f"{apellidos}, {nombres}"
                elif nombres:
                    return nombres
                else:
                    return "Estudiante sin nombre"
        except Exception as e:
            logger.error(f"Error formateando nombre: {e}")
            return "Error en nombre"
    
    def _ver_detalle_inscripcion(self, inscripcion):
        """Ver detalles de una inscripción específica"""
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QTextEdit

        dialog = QDialog(self)
        dialog.setWindowTitle(f"Detalle de Inscripción #{inscripcion.get('id', 'N/A')}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)

        layout = QVBoxLayout(dialog)

        # Crear área de texto para mostrar detalles
        texto_detalle = QTextEdit()
        texto_detalle.setReadOnly(True)

        # Formatear detalles
        detalles = []
        detalles.append(f"🏷️ ID Inscripción: {inscripcion.get('id', 'N/A')}")
        detalles.append(f"👤 Estudiante: {self._formatear_nombre_estudiante(inscripcion)}")

        # Datos del estudiante si están disponibles
        estudiante = inscripcion.get('estudiante', {})
        if estudiante:
            detalles.append(f"📧 Email: {estudiante.get('email', 'No especificado')}")
            detalles.append(f"📱 Teléfono: {estudiante.get('telefono', 'No especificado')}")
            detalles.append(f"🆔 CI: {estudiante.get('ci', 'No especificado')}")

        detalles.append(f"📅 Fecha Inscripción: {inscripcion.get('fecha_inscripcion', 'No especificada')}")
        detalles.append(f"📊 Estado: {inscripcion.get('estado', 'No especificado')}")
        detalles.append(f"💬 Observaciones: {inscripcion.get('observaciones', 'Sin observaciones')}")

        texto_detalle.setText("\n".join(detalles))

        layout.addWidget(texto_detalle)

        # Botones
        btn_layout = QHBoxLayout()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(dialog.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cerrar)

        layout.addLayout(btn_layout)

        dialog.exec()