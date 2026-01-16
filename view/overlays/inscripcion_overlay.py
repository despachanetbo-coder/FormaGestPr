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
from model.transaccion_model import TransaccionModel

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
        
        # Listas para datos dinámicos
        self.programas_inscritos: List[Dict] = []
        self.estudiantes_inscritos: List[Dict] = []
        self.programas_disponibles: List[Dict] = []
        self.estudiantes_disponibles: List[Dict] = []
        
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
        
        # Splitter horizontal principal
        splitter_principal = QSplitter(Qt.Orientation.Horizontal)
        
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
        
        # Grupo: Información del Programa (cuando programa_id > 0)
        self.grupo_info_programa = self.crear_grupo_info_programa_completo()
        left_layout.addWidget(self.grupo_info_programa)
        
        left_layout.addStretch()
        
        # ===== PANEL DERECHO =====
        # Grupo: Programas Disponibles (cuando estudiante_id > 0)
        self.grupo_programas_disponibles = self.crear_grupo_programas_disponibles()
        right_layout.addWidget(self.grupo_programas_disponibles)
        
        # Grupo: Buscar Programa (cuando estudiante_id > 0 y no hay programa pre-seleccionado)
        self.grupo_buscar_programa = self.crear_grupo_buscar_programa_completo()
        right_layout.addWidget(self.grupo_buscar_programa)
        
        right_layout.addStretch()
        
        # Agregar contenedores al splitter
        splitter_principal.addWidget(left_container)
        splitter_principal.addWidget(right_container)
        splitter_principal.setSizes([400, 400])
        
        main_layout.addWidget(splitter_principal)
        
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
        formulario_layout.addWidget(self.grupo_formulario_inscripcion)
        
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
        
        main_layout.addWidget(self.seccion_formulario_frame)
        
        scroll_widget.setWidget(main_widget)
        self.content_layout.addWidget(scroll_widget, 1)
    
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
        self.programa_search_input.setMinimumHeight(35)
        search_layout.addWidget(self.programa_search_input, 1)
        
        # Botón buscar
        self.btn_buscar_programa = QPushButton("🔍 BUSCAR")
        self.btn_buscar_programa.setMinimumHeight(35)
        search_layout.addWidget(self.btn_buscar_programa)
        
        layout.addLayout(search_layout)
        
        return grupo
    
    def crear_item_programa_inscrito(self, programa_data: Dict):
        """Crear un item para mostrar un programa inscrito"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        
        # Encabezado del programa
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        header_layout = QGridLayout(header_frame)
        
        # Información del programa
        header_layout.addWidget(QLabel("<b>Código Programa:</b>"), 0, 0)
        codigo_label = QLabel(programa_data.get('codigo', ''))
        codigo_label.setStyleSheet("font-weight: bold; color: #2980b9;")
        header_layout.addWidget(codigo_label, 0, 1)
        
        header_layout.addWidget(QLabel("<b>Descripción:</b>"), 0, 2)
        desc_label = QLabel(programa_data.get('nombre', ''))
        desc_label.setStyleSheet("color: #2c3e50;")
        header_layout.addWidget(desc_label, 0, 3, 1, 2)
        
        # Estado y costo
        header_layout.addWidget(QLabel("<b>Estado Inscripción:</b>"), 1, 0)
        estado = programa_data.get('estado_inscripcion', '')
        estado_label = QLabel(estado)
        
        # Mapear estados a colores según tu dominio d_estado_academico
        if estado in ['INSCRITO', 'EN_CURSO']:
            estado_color = "#27ae60"
        elif estado == 'PREINSCRITO':
            estado_color = "#f39c12"
        elif estado == 'CONCLUIDO':
            estado_color = "#3498db"
        else:
            estado_color = "#7f8c8d"
            
        estado_label.setStyleSheet(f"font-weight: bold; color: {estado_color};")
        header_layout.addWidget(estado_label, 1, 1)
        
        header_layout.addWidget(QLabel("<b>Costo Total:</b>"), 1, 2)
        costo_total = programa_data.get('costo_con_descuento', 0) or 0
        descuento = programa_data.get('descuento_aplicado', 0) or 0
        
        if descuento > 0:
            costo_text = f"{costo_total:.2f} Bs (Descuento: {descuento}%)"
        else:
            costo_text = f"{costo_total:.2f} Bs"
            
        costo_label = QLabel(costo_text)
        costo_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        header_layout.addWidget(costo_label, 1, 3)
        
        header_layout.addWidget(QLabel("<b>Saldo Pendiente:</b>"), 1, 4)
        saldo_pendiente = programa_data.get('saldo_pendiente', 0) or 0
        saldo_label = QLabel(f"{saldo_pendiente:.2f} Bs")
        saldo_color = "#e74c3c" if saldo_pendiente > 0 else "#27ae60"
        saldo_label.setStyleSheet(f"font-weight: bold; color: {saldo_color};")
        header_layout.addWidget(saldo_label, 1, 5)
        
        layout.addWidget(header_frame)
        
        # Tabla de transacciones si existen
        transacciones = programa_data.get('transacciones', [])
        if transacciones:
            trans_label = QLabel("<b>📊 Historial de Transacciones:</b>")
            trans_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
            layout.addWidget(trans_label)
            
            trans_table = QTableWidget()
            trans_table.setColumnCount(7)
            trans_table.setHorizontalHeaderLabels(["N° Transacción", "Fecha", "Monto", "Forma Pago", "Comprobante", "Estado", "Documentos"])
            trans_table.horizontalHeader().setStretchLastSection(True)
            trans_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            trans_table.setAlternatingRowColors(True)
            trans_table.setMaximumHeight(150)
            
            trans_table.setRowCount(len(transacciones))
            
            for i, transaccion in enumerate(transacciones):
                # Número de transacción
                trans_table.setItem(i, 0, QTableWidgetItem(transaccion.get('numero_transaccion', '')))
                
                # Fecha
                fecha = transaccion.get('fecha_pago', '')
                trans_table.setItem(i, 1, QTableWidgetItem(str(fecha)[:10]))
                
                # Monto
                monto = transaccion.get('monto_final', 0)
                trans_table.setItem(i, 2, QTableWidgetItem(f"{monto:.2f} Bs"))
                
                # Forma de pago
                trans_table.setItem(i, 3, QTableWidgetItem(transaccion.get('forma_pago', '')))
                
                # Comprobante
                trans_table.setItem(i, 4, QTableWidgetItem(transaccion.get('numero_comprobante', '')))
                
                # Estado
                estado_trans = transaccion.get('estado', '')
                estado_item = QTableWidgetItem(estado_trans)
                if estado_trans == 'CONFIRMADO':
                    estado_item.setForeground(QBrush(QColor("#27ae60")))
                elif estado_trans == 'REGISTRADO':
                    estado_item.setForeground(QBrush(QColor("#f39c12")))
                else:
                    estado_item.setForeground(QBrush(QColor("#e74c3c")))
                trans_table.setItem(i, 5, estado_item)
                
                # Documentos
                num_docs = transaccion.get('numero_documentos', 0)
                docs_text = f"{num_docs} documento{'s' if num_docs != 1 else ''}"
                trans_table.setItem(i, 6, QTableWidgetItem(docs_text))
            
            # Ajustar tamaño de columnas
            trans_table.resizeColumnsToContents()
            layout.addWidget(trans_table)
        else:
            # Mostrar mensaje si no hay transacciones
            no_trans_label = QLabel("📭 No hay transacciones registradas para esta inscripción")
            no_trans_label.setStyleSheet("""
                color: #95a5a6;
                font-style: italic;
                font-size: 12px;
                padding: 10px;
                text-align: center;
                background-color: #f8f9fa;
                border-radius: 4px;
            """)
            layout.addWidget(no_trans_label)
        
        # Botón para realizar pago si hay saldo pendiente
        saldo_pendiente = programa_data.get('saldo_pendiente', 0)
        inscripcion_id = programa_data.get('inscripcion_id')
        
        if saldo_pendiente > 0 and inscripcion_id:
            btn_frame = QFrame()
            btn_layout = QHBoxLayout(btn_frame)
            btn_layout.addStretch()
            
            btn_realizar_pago = QPushButton("💰 REALIZAR PAGO")
            btn_realizar_pago.setMinimumHeight(35)
            btn_realizar_pago.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 20px;
                }
                QPushButton:hover {
                    background-color: #219653;
                }
            """)
            btn_realizar_pago.clicked.connect(lambda: self.realizar_pago_inscripcion(inscripcion_id))
            
            btn_layout.addWidget(btn_realizar_pago)
            layout.addWidget(btn_frame)
        
        return frame
    
    def crear_item_estudiante_inscrito(self, estudiante_data: Dict):
        """Crear un item para mostrar un estudiante inscrito"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 0px;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        
        # Encabezado del estudiante
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: #fff3cd;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        header_layout = QGridLayout(header_frame)
        
        # Información del estudiante
        header_layout.addWidget(QLabel("<b>Carnet:</b>"), 0, 0)
        ci_label = QLabel(f"{estudiante_data.get('ci_numero', '')}-{estudiante_data.get('ci_expedicion', '')}")
        ci_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(ci_label, 0, 1)
        
        header_layout.addWidget(QLabel("<b>Nombre Completo:</b>"), 0, 2)
        nombre_label = QLabel(f"{estudiante_data.get('nombres', '')} {estudiante_data.get('apellido_paterno', '')}")
        nombre_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(nombre_label, 0, 3, 1, 2)
        
        # Información de contacto
        header_layout.addWidget(QLabel("<b>Email:</b>"), 1, 0)
        email_label = QLabel(estudiante_data.get('email', ''))
        header_layout.addWidget(email_label, 1, 1)
        
        header_layout.addWidget(QLabel("<b>Teléfono:</b>"), 1, 2)
        telefono_label = QLabel(estudiante_data.get('telefono', ''))
        header_layout.addWidget(telefono_label, 1, 3)
        
        # Estado de inscripción y saldo
        header_layout.addWidget(QLabel("<b>Estado Inscripción:</b>"), 2, 0)
        estado_label = QLabel(estudiante_data.get('estado_inscripcion', ''))
        estado_color = "#27ae60" if estudiante_data.get('estado_inscripcion') in ['INSCRITO', 'EN_CURSO'] else "#f39c12"
        estado_label.setStyleSheet(f"font-weight: bold; color: {estado_color};")
        header_layout.addWidget(estado_label, 2, 1)
        
        header_layout.addWidget(QLabel("<b>Saldo Pendiente:</b>"), 2, 2)
        saldo_label = QLabel(f"{estudiante_data.get('saldo_pendiente', 0):.2f} Bs")
        saldo_color = "#e74c3c" if estudiante_data.get('saldo_pendiente', 0) > 0 else "#27ae60"
        saldo_label.setStyleSheet(f"font-weight: bold; color: {saldo_color};")
        header_layout.addWidget(saldo_label, 2, 3)
        
        layout.addWidget(header_frame)
        
        # Tabla de pagos (si existe información)
        if estudiante_data.get('pagos'):
            pagos_label = QLabel("<b>📊 Historial de Pagos:</b>")
            pagos_label.setStyleSheet("color: #2c3e50; font-size: 13px;")
            layout.addWidget(pagos_label)
            
            pagos_table = QTableWidget()
            pagos_table.setColumnCount(6)
            pagos_table.setHorizontalHeaderLabels(["Fecha", "Monto", "Forma Pago", "Comprobante", "Estado", "Documentos"])
            pagos_table.horizontalHeader().setStretchLastSection(True)
            pagos_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            pagos_table.setAlternatingRowColors(True)
            pagos_table.setMaximumHeight(150)
            
            layout.addWidget(pagos_table)
        
        # Botón para realizar transacción si hay saldo pendiente
        if estudiante_data.get('saldo_pendiente', 0) > 0:
            btn_frame = QFrame()
            btn_layout = QHBoxLayout(btn_frame)
            btn_layout.addStretch()
            
            btn_realizar_pago = QPushButton("💰 REALIZAR PAGO")
            btn_realizar_pago.setMinimumHeight(35)
            btn_realizar_pago.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-weight: bold;
                    padding: 0 20px;
                }
                QPushButton:hover {
                    background-color: #219653;
                }
            """)
            
            btn_layout.addWidget(btn_realizar_pago)
            layout.addWidget(btn_frame)
        
        return frame
    
    def crear_grupo_formulario_inscripcion(self):
        """Crear grupo para el formulario de inscripción/transacción"""
        grupo = QGroupBox("📋 DETALLES DE LA INSCRIPCIÓN")
        grupo.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #bdc3c7;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        
        grid = QGridLayout(grupo)
        grid.setSpacing(15)
        grid.setContentsMargins(15, 25, 15, 15)
        
        # Fila 1: Fecha y Estudiante
        grid.addWidget(QLabel("Fecha:"), 0, 0)
        self.fecha_inscripcion_date = QDateEdit()
        self.fecha_inscripcion_date.setCalendarPopup(True)
        self.fecha_inscripcion_date.setDate(QDate.currentDate())
        self.fecha_inscripcion_date.setDisplayFormat("dd/MM/yyyy")
        self.fecha_inscripcion_date.setMinimumHeight(35)
        grid.addWidget(self.fecha_inscripcion_date, 0, 1)
        
        grid.addWidget(QLabel("Estudiante:"), 0, 2)
        self.estudiante_nombre_form_label = QLabel()
        self.estudiante_nombre_form_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        grid.addWidget(self.estudiante_nombre_form_label, 0, 3)
        
        # Fila 2: Estado, Descuento y Monto
        grid.addWidget(QLabel("Estado:"), 1, 0)
        self.estado_inscripcion_combo = QComboBox()
        self.estado_inscripcion_combo.addItems(["PREINSCRITO", "INSCRITO", "EN_CURSO"])
        self.estado_inscripcion_combo.setMinimumHeight(35)
        grid.addWidget(self.estado_inscripcion_combo, 1, 1)
        
        grid.addWidget(QLabel("Descuento:"), 1, 2)
        descuento_layout = QHBoxLayout()
        self.descuento_spin = QDoubleSpinBox()
        self.descuento_spin.setRange(0, 100)
        self.descuento_spin.setDecimals(2)
        self.descuento_spin.setSuffix(" %")
        self.descuento_spin.setValue(0.0)
        self.descuento_spin.setMinimumHeight(35)
        descuento_layout.addWidget(self.descuento_spin)
        
        grid.addLayout(descuento_layout, 1, 3)
        
        # Fila 3: Código Transacción
        grid.addWidget(QLabel("Código Transacción:"), 2, 0)
        self.codigo_transaccion_label = QLabel("AUTOGENERADO")
        self.codigo_transaccion_label.setStyleSheet("""
            font-weight: bold;
            color: #9b59b6;
            background-color: #f5eef8;
            padding: 8px;
            border-radius: 4px;
        """)
        grid.addWidget(self.codigo_transaccion_label, 2, 1)
        
        # Fila 4: Fecha de Pago y Forma de Pago
        grid.addWidget(QLabel("Fecha de Pago:"), 3, 0)
        self.fecha_pago_date = QDateEdit()
        self.fecha_pago_date.setCalendarPopup(True)
        self.fecha_pago_date.setDate(QDate.currentDate())
        self.fecha_pago_date.setDisplayFormat("dd/MM/yyyy")
        self.fecha_pago_date.setMinimumHeight(35)
        grid.addWidget(self.fecha_pago_date, 3, 1)
        
        grid.addWidget(QLabel("Forma de Pago:"), 3, 2)
        from config.constants import FormaPago
        fp = FormaPago
        self.forma_pago_combo = QComboBox()
        self.forma_pago_combo.addItems([fp.EFECTIVO.value, fp.DEPOSITO.value, fp.TARJETA.value, fp.TRANSFERENCIA.value, fp.QR.value])
        self.forma_pago_combo.setMinimumHeight(35)
        grid.addWidget(self.forma_pago_combo, 3, 3)
        
        # Fila 5: Estado de Transacción y Origen
        grid.addWidget(QLabel("Estado Transacción:"), 4, 0)
        self.estado_transaccion_combo = QComboBox()
        self.estado_transaccion_combo.addItems(["PENDIENTE", "CONFIRMADO", "ANULADO"])
        self.estado_transaccion_combo.setMinimumHeight(35)
        grid.addWidget(self.estado_transaccion_combo, 4, 1)
        
        grid.addWidget(QLabel("Origen Transacción:"), 4, 2)
        self.origen_transaccion_input = QLineEdit()
        self.origen_transaccion_input.setPlaceholderText("Ej: Banco XYZ, Caja, etc.")
        self.origen_transaccion_input.setMinimumHeight(35)
        grid.addWidget(self.origen_transaccion_input, 4, 3)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        grid.addWidget(separator, 5, 0, 1, 4)
        
        # Sección: Documentos de respaldo
        documentos_frame = QFrame()
        documentos_frame.setStyleSheet("""
            QFrame {
                background-color: #e8f4fc;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        documentos_layout = QVBoxLayout(documentos_frame)
        
        documentos_title = QLabel("📎 DOCUMENTOS DE RESPALDO")
        documentos_title.setStyleSheet("font-weight: bold; color: #2980b9;")
        documentos_layout.addWidget(documentos_title)
        
        # Botón para agregar documento
        self.btn_agregar_documento = QPushButton("➕ AGREGAR DOCUMENTO")
        self.btn_agregar_documento.setMinimumHeight(35)
        self.btn_agregar_documento.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        documentos_layout.addWidget(self.btn_agregar_documento)
        
        # Lista de documentos
        self.documentos_list_widget = QListWidget()
        self.documentos_list_widget.setMaximumHeight(100)
        documentos_layout.addWidget(self.documentos_list_widget)
        
        grid.addWidget(documentos_frame, 6, 0, 1, 4)
        
        # Separador
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        grid.addWidget(separator2, 7, 0, 1, 4)
        
        # Sección: Detalles de transacción
        detalles_frame = QFrame()
        detalles_layout = QVBoxLayout(detalles_frame)
        
        detalles_title = QLabel("💰 DETALLES DE LA TRANSACCIÓN")
        detalles_title.setStyleSheet("font-weight: bold; color: #27ae60;")
        detalles_layout.addWidget(detalles_title)
        
        # Tabla de detalles
        self.detalles_table = QTableWidget()
        self.detalles_table.setColumnCount(5)
        self.detalles_table.setHorizontalHeaderLabels(["Concepto", "Descripción", "Cantidad", "Precio Unit.", "Subtotal"])
        self.detalles_table.horizontalHeader().setStretchLastSection(True)
        self.detalles_table.setMinimumHeight(150)
        self.detalles_table.setMaximumHeight(200)
        
        # Agregar fila vacía inicial
        self.detalles_table.setRowCount(1)
        
        detalles_layout.addWidget(self.detalles_table)
        
        # Botón para agregar detalle
        btn_agregar_detalle = QPushButton("➕ AGREGAR CONCEPTO")
        btn_agregar_detalle.setMinimumHeight(35)
        btn_agregar_detalle.setStyleSheet("""
            QPushButton {
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #27ae60;
            }
        """)
        detalles_layout.addWidget(btn_agregar_detalle)
        
        grid.addWidget(detalles_frame, 8, 0, 1, 4)
        
        # Fila: Total
        total_frame = QFrame()
        total_layout = QHBoxLayout(total_frame)
        total_layout.addStretch()
        
        total_label = QLabel("TOTAL:")
        total_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #2c3e50;")
        total_layout.addWidget(total_label)
        
        self.total_label = QLabel("0.00 Bs")
        self.total_label.setStyleSheet("""
            font-weight: bold;
            font-size: 18px;
            color: #e74c3c;
            background-color: #f9ebea;
            padding: 10px 20px;
            border-radius: 6px;
            min-width: 150px;
            text-align: center;
        """)
        total_layout.addWidget(self.total_label)
        
        grid.addWidget(total_frame, 9, 0, 1, 4)
        
        return grupo
    
    def setup_validators(self):
        """Configurar validadores"""
        # Validar que solo números en CI si es necesario
        pass
    
    def setup_conexiones_especificas(self):
        """Configurar conexiones específicas"""
        # Botones de búsqueda
        self.btn_buscar_estudiante.clicked.connect(self.buscar_estudiantes_disponibles)
        self.btn_buscar_programa.clicked.connect(self.buscar_programas_disponibles)
        
        # Botones de acción
        self.btn_realizar_inscripcion.clicked.connect(self.realizar_inscripcion)
        self.btn_cancelar_inscripcion.clicked.connect(self.cancelar_inscripcion)
        self.btn_agregar_documento.clicked.connect(self.agregar_documento)
        
        # Conexiones de tablas
        self.estudiantes_disponibles_table.itemDoubleClicked.connect(self.seleccionar_estudiante_desde_tabla)
        self.programas_disponibles_table.itemDoubleClicked.connect(self.seleccionar_programa_desde_tabla)
        
        # Cambios en formulario
        self.descuento_spin.valueChanged.connect(self.calcular_total)
        
        # **AGREGAR SI NO ESTÁ EN BaseOverlay:**
        if hasattr(self, 'btn_guardar'):
            self.btn_guardar.clicked.connect(self.guardar_datos)
    
    def configurar_interfaz_segun_contexto(self):
        """Configurar qué elementos mostrar según el contexto (estudiante_id o programa_id)"""
        # Limpiar listados anteriores
        self.limpiar_listados()
        
        logger.debug(f"Configurando interfaz con estudiante_id={self.estudiante_id} y programa_id={self.programa_id}")
        
        if self.estudiante_id and not self.programa_id:
            # Caso 1: Tenemos estudiante_id pero no programa_id
            self.grupo_info_estudiante.setVisible(True)
            self.grupo_buscar_estudiante.setVisible(False)
            self.grupo_info_programa.setVisible(False)
            self.grupo_programas_disponibles.setVisible(True)
            self.grupo_buscar_programa.setVisible(True)
            self.seccion_listado_frame.setVisible(True)
            self.seccion_formulario_frame.setVisible(False)
            
            # Configurar título
            self.titulo_listado_label.setText("🎓 PROGRAMAS INSCRITOS DEL ESTUDIANTE")
            
            # Cargar información del estudiante
            self.cargar_info_estudiante(self.estudiante_id)
            
            # Cargar programas inscritos del estudiante
            self.cargar_programas_inscritos_estudiante()
            
            # Cargar programas disponibles para el estudiante
            self.cargar_programas_disponibles_para_estudiante()
            
        elif self.programa_id and not self.estudiante_id:
            # Caso 2: Tenemos programa_id pero no estudiante_id
            self.grupo_info_estudiante.setVisible(False)
            self.grupo_buscar_estudiante.setVisible(True)
            self.grupo_info_programa.setVisible(True)
            self.grupo_programas_disponibles.setVisible(False)
            self.grupo_buscar_programa.setVisible(False)
            self.seccion_listado_frame.setVisible(True)
            self.seccion_formulario_frame.setVisible(False)
            
            # Configurar título
            self.titulo_listado_label.setText("👥 ESTUDIANTES INSCRITOS EN EL PROGRAMA")
            
            # Cargar información del programa
            self.cargar_info_programa(self.programa_id)
            
            # Cargar estudiantes inscritos en el programa
            self.cargar_estudiantes_inscritos_programa()
            
        elif self.estudiante_id and self.programa_id:
            # Caso 3: Tenemos ambos IDs (modo inscripción)
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
            
        else:
            # Caso 4: No tenemos ni estudiante_id ni programa_id
            self.grupo_info_estudiante.setVisible(False)
            self.grupo_buscar_estudiante.setVisible(False)
            self.grupo_info_programa.setVisible(False)
            self.grupo_programas_disponibles.setVisible(False)
            self.grupo_buscar_programa.setVisible(False)
            self.seccion_listado_frame.setVisible(False)
            self.seccion_formulario_frame.setVisible(False)
    
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
            
            # 1. Contar estudiantes inscritos (excluyendo RETIRADOS)
            query_inscritos = """
            SELECT COUNT(*) as total_inscritos
            FROM inscripciones 
            WHERE programa_id = %s 
            AND estado NOT IN ('RETIRADO')
            """
            cursor.execute(query_inscritos, (programa_id,))
            result_inscritos = cursor.fetchone()
            total_inscritos = result_inscritos[0] if result_inscritos else 0
            
            # 2. Calcular total recaudado de transacciones CONFIRMADAS
            query_recaudado = """
            SELECT COALESCE(SUM(t.monto_final), 0) as total_recaudado
            FROM transacciones t
            WHERE t.programa_id = %s 
            AND t.estado = 'CONFIRMADO'
            """
            cursor.execute(query_recaudado, (programa_id,))
            result_recaudado = cursor.fetchone()
            total_recaudado = float(result_recaudado[0]) if result_recaudado else 0.0
            
            # 3. Calcular promedio de pago por estudiante
            if total_inscritos > 0:
                promedio_pago = total_recaudado / total_inscritos
            else:
                promedio_pago = 0.0
            
            # 4. Obtener estudiantes con saldo pendiente
            query_pendientes = """
            SELECT COUNT(DISTINCT i.estudiante_id) as estudiantes_con_saldo
            FROM inscripciones i
            LEFT JOIN (
                SELECT estudiante_id, programa_id, SUM(monto_final) as total_pagado
                FROM transacciones 
                WHERE programa_id = %s AND estado = 'CONFIRMADO'
                GROUP BY estudiante_id, programa_id
            ) t ON i.estudiante_id = t.estudiante_id AND i.programa_id = t.programa_id
            WHERE i.programa_id = %s 
            AND i.estado NOT IN ('RETIRADO')
            AND (
                t.total_pagado IS NULL 
                OR t.total_pagado < (
                    -- Calcular costo total considerando descuentos
                    SELECT (p.costo_matricula + p.costo_inscripcion + (p.costo_mensualidad * p.numero_cuotas)) * 
                            (1 - COALESCE(i.descuento_aplicado, 0) / 100)
                    FROM programas p
                    WHERE p.id = i.programa_id
                )
            )
            """
            cursor.execute(query_pendientes, (programa_id, programa_id))
            result_pendientes = cursor.fetchone()
            estudiantes_con_saldo = result_pendientes[0] if result_pendientes else 0
            
            # 5. Calcular proyección de ingresos totales
            query_proyeccion = """
            SELECT COALESCE(SUM(
                (p.costo_matricula + p.costo_inscripcion + (p.costo_mensualidad * p.numero_cuotas)) * 
                (1 - COALESCE(i.descuento_aplicado, 0) / 100)
            ), 0) as proyeccion_total
            FROM inscripciones i
            JOIN programas p ON i.programa_id = p.id
            WHERE i.programa_id = %s 
            AND i.estado NOT IN ('RETIRADO')
            """
            cursor.execute(query_proyeccion, (programa_id,))
            result_proyeccion = cursor.fetchone()
            proyeccion_total = float(result_proyeccion[0]) if result_proyeccion else 0.0
            
            cursor.close()
            Database.return_connection(connection)
            
            # Actualizar interfaz con los datos calculados
            self.programa_inscritos_label.setText(f"{total_inscritos} estudiantes")
            
            # Mostrar recaudado con formato especial si hay datos
            if total_recaudado > 0:
                # Calcular porcentaje de recaudado vs proyección
                if proyeccion_total > 0:
                    porcentaje_recaudado = (total_recaudado / proyeccion_total) * 100
                    self.programa_recaudado_label.setText(
                        f"{total_recaudado:,.2f} Bs\n"
                        f"({porcentaje_recaudado:.1f}% de proyección)"
                    )
                    # Color según porcentaje
                    if porcentaje_recaudado >= 80:
                        self.programa_recaudado_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                    elif porcentaje_recaudado >= 50:
                        self.programa_recaudado_label.setStyleSheet("color: #f39c12; font-weight: bold;")
                    else:
                        self.programa_recaudado_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
                else:
                    self.programa_recaudado_label.setText(f"{total_recaudado:,.2f} Bs")
                    self.programa_recaudado_label.setStyleSheet("color: #27ae60; font-weight: bold;")
                
                # Agregar tooltip con información detallada
                tooltip_text = (
                    f"💰 <b>Resumen Financiero del Programa</b><br><br>"
                    f"<b>Total Recaudado:</b> {total_recaudado:,.2f} Bs<br>"
                    f"<b>Proyección Total:</b> {proyeccion_total:,.2f} Bs<br>"
                    f"<b>Promedio por Estudiante:</b> {promedio_pago:,.2f} Bs<br>"
                    f"<b>Estudiantes con Saldo:</b> {estudiantes_con_saldo}<br>"
                    f"<b>Saldo por Recaudar:</b> {proyeccion_total - total_recaudado:,.2f} Bs"
                )
                self.programa_recaudado_label.setToolTip(tooltip_text)
                
                # También agregar tooltip al label de inscritos
                inscritos_tooltip = (
                    f"👥 <b>Resumen de Inscritos</b><br><br>"
                    f"<b>Total Inscritos:</b> {total_inscritos}<br>"
                    f"<b>Cupos Disponibles:</b> {cupos_maximos - total_inscritos if cupos_maximos else '∞'}<br>"
                    f"<b>Porcentaje Ocupación:</b> {(total_inscritos/cupos_maximos*100):.1f}%<br>"
                    f"<b>Estudiantes con Saldo Pendiente:</b> {estudiantes_con_saldo}"
                )
                self.programa_inscritos_label.setToolTip(inscritos_tooltip)
            else:
                self.programa_recaudado_label.setText("0.00 Bs")
                self.programa_recaudado_label.setStyleSheet("color: #95a5a6; font-weight: bold;")
                self.programa_recaudado_label.setToolTip("No hay transacciones registradas para este programa")
            
        except Exception as e:
            logger.error(f"Error calculando resumen del programa: {e}")
            self.programa_inscritos_label.setText("Error cálculo")
            self.programa_recaudado_label.setText("Error cálculo")
            self.programa_inscritos_label.setToolTip(f"Error al calcular: {str(e)}")
            self.programa_recaudado_label.setToolTip(f"Error al calcular: {str(e)}")
    
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
            
            if not programas:
                # Mostrar mensaje si no hay programas
                no_data_label = QLabel("🎯 El estudiante no está inscrito en ningún programa")
                no_data_label.setStyleSheet("""
                    color: #7f8c8d;
                    font-style: italic;
                    font-size: 14px;
                    padding: 20px;
                    text-align: center;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    margin: 10px;
                """)
                self.listado_layout_container.addWidget(no_data_label)
            else:
                # Procesar cada programa inscrito
                for programa_data in programas:
                    try:
                        # Enriquecer datos con información de transacciones y cálculos
                        programa_enriquecido = self.enriquecer_datos_programa_inscrito(programa_data)
                        
                        # Crear widget para mostrar el programa
                        item_widget = self.crear_item_programa_inscrito(programa_enriquecido)
                        self.listado_layout_container.addWidget(item_widget)
                        
                    except Exception as e:
                        logger.error(f"Error procesando programa {programa_data.get('codigo', 'desconocido')}: {e}")
                        # Mostrar un item de error para este programa
                        error_widget = self.crear_item_error_programa(programa_data, str(e))
                        self.listado_layout_container.addWidget(error_widget)
            
            self.listado_layout_container.addStretch()
            
        except Exception as e:
            logger.error(f"Error cargando programas inscritos: {e}")
            self.mostrar_mensaje("Error", f"Error al cargar programas inscritos: {str(e)}", "error")
    
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
    
    def recargar_programa_inscrito(self, inscripcion_id: int):
        """Recargar un programa específico"""
        try:
            # Buscar y actualizar el widget específico
            for i in range(self.listado_layout_container.count()):
                widget = self.listado_layout_container.itemAt(i).widget()
                if widget and hasattr(widget, 'inscripcion_id') and widget.inscripcion_id == inscripcion_id:
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
                            self.listado_layout_container.insertWidget(i, nuevo_widget)
                            widget.deleteLater()
                    
                    break
                    
        except Exception as e:
            logger.error(f"Error recargando programa: {e}")
            self.mostrar_mensaje("Error", f"No se pudo recargar el programa: {str(e)}", "error")
    
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
            
            for estudiante in estudiantes_ejemplo:
                item_widget = self.crear_item_estudiante_inscrito(estudiante)
                self.listado_layout_container.addWidget(item_widget)
            
            self.listado_layout_container.addStretch()
            
        except Exception as e:
            logger.error(f"Error cargando estudiantes inscritos: {e}")
    
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
                
                self.programas_disponibles_table.setRowCount(len(programas_disponibles))
                
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
                    
                    # Botón Inscribir - CORRECCIÓN AQUÍ: pasar solo el ID
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
                            }
                            QPushButton:hover {
                                background-color: #2980b9;
                            }
                        """)
                        # CORRECCIÓN: Pasar solo el ID (entero) no el diccionario completo
                        btn_inscribir.clicked.connect(lambda checked, pid=programa_id: self.seleccionar_programa_para_inscribir(pid))
                        self.programas_disponibles_table.setCellWidget(i, 5, btn_inscribir)
                
            else:
                # No hay conexión a la base de datos
                self.programas_disponibles_table.setRowCount(0)
                
        except Exception as e:
            logger.error(f"Error cargando programas disponibles: {e}")
            self.mostrar_mensaje("Error", f"Error al cargar programas disponibles: {str(e)}", "error")
    
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
    
    def configurar_formulario_inscripcion(self):
        """Configurar el formulario de inscripción con los datos actuales"""
        if not self.estudiante_data or not self.programa_data:
            return
        
        # Configurar título del formulario
        estudiante_nombre = f"{self.estudiante_data.get('nombres', '')} {self.estudiante_data.get('apellido_paterno', '')}"
        programa_codigo = self.programa_data.get('codigo', '')
        self.titulo_formulario_label.setText(f"📝 INSCRIPCIÓN: {estudiante_nombre} → {programa_codigo}")
        
        # Establecer fecha actual
        self.fecha_inscripcion_date.setDate(QDate.currentDate())
        self.fecha_pago_date.setDate(QDate.currentDate())
        
        # Configurar estado inicial
        self.estado_inscripcion_combo.setCurrentText("PREINSCRITO")
        self.estado_transaccion_combo.setCurrentText("PENDIENTE")
        
        # Calcular total inicial
        self.calcular_total()
    
    def calcular_total(self):
        """Calcular el total de la transacción"""
        try:
            # TODO: Calcular basado en costo del programa y descuento
            costo_base = self.programa_data.get('costo_total', 0) if self.programa_data else 0
            descuento = self.descuento_spin.value()
            
            if descuento > 0:
                total = costo_base * (1 - descuento / 100)
            else:
                total = costo_base
            
            self.total_label.setText(f"{total:.2f} Bs")
        except Exception as e:
            logger.error(f"Error calculando total: {e}")
            self.total_label.setText("0.00 Bs")
    
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
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QDialogButtonBox
        
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
    
    # ===== MÉTODOS PARA CARGAR Y GUARDAR DATOS =====
    
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
    
    def close_overlay(self):
        """Cerrar el overlay"""
        self.close()
        if hasattr(self, 'overlay_closed'):
            self.overlay_closed.emit()
    
    # ===== MÉTODOS OVERRIDE DE BASE =====
    
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
        self.original_data = {}
        
        # Limpiar datos
        self.estudiante_data = None
        self.programa_data = None
        self.programas_inscritos = []
        self.estudiantes_inscritos = []
        self.programas_disponibles = []
        self.estudiantes_disponibles = []
        
        # Limpiar interfaz
        self.limpiar_listados()
        
        # Ocultar todas las secciones
        self.grupo_info_estudiante.setVisible(False)
        self.grupo_buscar_estudiante.setVisible(False)
        self.grupo_info_programa.setVisible(False)
        self.grupo_programas_disponibles.setVisible(False)
        self.grupo_buscar_programa.setVisible(False)
        self.seccion_listado_frame.setVisible(False)
        self.seccion_formulario_frame.setVisible(False)
        
        # Limpiar campos del formulario
        if hasattr(self, 'fecha_inscripcion_date'):
            self.fecha_inscripcion_date.setDate(QDate.currentDate())
        if hasattr(self, 'fecha_pago_date'):
            self.fecha_pago_date.setDate(QDate.currentDate())
        if hasattr(self, 'descuento_spin'):
            self.descuento_spin.setValue(0.0)
        if hasattr(self, 'estado_inscripcion_combo'):
            self.estado_inscripcion_combo.setCurrentIndex(0)
        if hasattr(self, 'estado_transaccion_combo'):
            self.estado_transaccion_combo.setCurrentIndex(0)
        if hasattr(self, 'forma_pago_combo'):
            self.forma_pago_combo.setCurrentIndex(0)
        if hasattr(self, 'origen_transaccion_input'):
            self.origen_transaccion_input.clear()
        if hasattr(self, 'total_label'):
            self.total_label.setText("0.00 Bs")
    
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
    
