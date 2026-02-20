# -*- coding: utf-8 -*-
# Archivo view/overlays/transaccion_overlay.py
"""
Overlay para gestión de transacciones de pago
Permite crear, editar y visualizar transacciones con sus detalles
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QPushButton, QLabel, QComboBox, QLineEdit, QTextEdit,
    QDateEdit, QGroupBox, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QFrame, QSplitter, QTabWidget, 
    QCheckBox, QApplication, QDialog, QDialogButtonBox, 
    QScrollArea, QSizePolicy
)
from PySide6.QtCore import (
    Qt, Signal, Slot, QDate, QDateTime, QTimer, QSize
)
from PySide6.QtGui import (
    QFont, QColor, QIcon, QDoubleValidator, QIntValidator, 
    QRegularExpressionValidator
)
from PySide6.QtCore import QRegularExpression

from view.overlays.base_overlay import BaseOverlay
from config.constants import FormaPago, EstadoTransaccion, Messages
from model.inscripcion_model import InscripcionModel
from model.estudiante_model import EstudianteModel
from model.programa_model import ProgramaModel
from model.transaccion_model import TransaccionModel
from model.usuarios_model import UsuariosModel

import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class DetalleTransaccionDialog(QDialog):
    """Diálogo para agregar un detalle de transacción"""
    
    def __init__(self, parent=None, inscripcion_id=None, 
                datos_inscripcion=None, datos_programa=None):
        super().__init__(parent)
        
        self.inscripcion_id = inscripcion_id
        self.datos_inscripcion = datos_inscripcion or {}
        self.datos_programa = datos_programa or {}
        
        self.setWindowTitle("Agregar Concepto")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self.setup_ui()
        self.cargar_sugerencias()
    
    def setup_ui(self):
        """Configurar interfaz del diálogo"""
        layout = QVBoxLayout(self)

        # Formulario
        form_layout = QFormLayout()

        # Concepto
        self.cbo_concepto = QComboBox()
        self.cbo_concepto.addItem("Matrícula", "matricula")
        self.cbo_concepto.addItem("Mensualidad", "mensualidad")
        self.cbo_concepto.addItem("Inscripción", "inscripcion")
        self.cbo_concepto.addItem("Certificado", "certificado")
        self.cbo_concepto.addItem("Material", "material")
        self.cbo_concepto.addItem("Otro", "otro")
        self.cbo_concepto.currentIndexChanged.connect(self.on_concepto_changed)
        form_layout.addRow("Concepto:", self.cbo_concepto)

        # Descripción
        self.txt_descripcion = QLineEdit()
        self.txt_descripcion.setPlaceholderText("Descripción del concepto")
        form_layout.addRow("Descripción:", self.txt_descripcion)

        # Cantidad
        self.txt_cantidad = QLineEdit()
        self.txt_cantidad.setPlaceholderText("1")
        self.txt_cantidad.setText("1")
        int_validator = QIntValidator(1, 999)
        self.txt_cantidad.setValidator(int_validator)
        self.txt_cantidad.textChanged.connect(self.calcular_subtotal)
        form_layout.addRow("Cantidad:", self.txt_cantidad)

        # Precio Unitario
        self.txt_precio = QLineEdit()
        self.txt_precio.setPlaceholderText("0.00")
        self.txt_precio.setText("0.00")
        double_validator = QDoubleValidator(0.0, 999999.99, 2)
        double_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.txt_precio.setValidator(double_validator)
        self.txt_precio.textChanged.connect(self.calcular_subtotal)
        form_layout.addRow("Precio Unitario:", self.txt_precio)

        # Subtotal (solo lectura)
        self.lbl_subtotal = QLabel("Bs. 0.00")
        self.lbl_subtotal.setStyleSheet("font-weight: bold; color: #1a237e;")
        form_layout.addRow("Subtotal:", self.lbl_subtotal)

        layout.addLayout(form_layout)

        # Botones
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def cargar_sugerencias(self):
        """Cargar sugerencias basadas en la inscripción"""
        if self.datos_inscripcion:
            valor_final = self.datos_inscripcion.get('valor_final', 0)
            num_cuotas = self.datos_inscripcion.get('numero_cuotas', 1)
            
            if num_cuotas > 0:
                self.txt_precio.setText(f"{valor_final / num_cuotas:.2f}")
    
    def on_concepto_changed(self, index):
        """Manejar cambio de concepto"""
        concepto = self.cbo_concepto.currentData()
        
        if concepto == "matricula":
            self.txt_descripcion.setText("Matrícula de inscripción")
        elif concepto == "mensualidad":
            self.txt_descripcion.setText("Pago de mensualidad")
        elif concepto == "inscripcion":
            self.txt_descripcion.setText("Inscripción al programa")
        elif concepto == "certificado":
            self.txt_descripcion.setText("Certificado de participación")
            self.txt_precio.setText("150.00")
        elif concepto == "material":
            self.txt_descripcion.setText("Material de estudio")
    
    def calcular_subtotal(self):
        """Calcular subtotal"""
        try:
            cantidad = float(self.txt_cantidad.text() or "0")
            precio = float(self.txt_precio.text() or "0")
            subtotal = cantidad * precio
            self.lbl_subtotal.setText(f"Bs. {subtotal:,.2f}")
        except ValueError:
            self.lbl_subtotal.setText("Bs. 0.00")
    
    def obtener_detalle(self) -> Dict[str, Any]:
        """Obtener los datos del detalle"""
        try:
            cantidad = float(self.txt_cantidad.text() or "1")
            precio = float(self.txt_precio.text() or "0")
            subtotal = cantidad * precio
        except ValueError:
            cantidad = 1
            precio = 0
            subtotal = 0
            
        return {
            'concepto_pago_id': self.cbo_concepto.currentData(),
            'concepto_nombre': self.cbo_concepto.currentText(),
            'descripcion': self.txt_descripcion.text(),
            'cantidad': cantidad,
            'precio_unitario': precio,
            'subtotal': subtotal
        }


class TransaccionOverlay(BaseOverlay):
    """
    Overlay para gestión de transacciones de pago
    Soporta creación, edición, visualización y registro de detalles
    
    Flujo de trabajo:
    - Modo "nuevo": Se crea automáticamente una transacción con valores por defecto
    - Luego se trabaja siempre en modo edición sobre esa transacción
    """
    
    # Señales específicas
    transaccion_creada = Signal(dict)  # Emite datos de transacción creada
    transaccion_actualizada = Signal(dict)  # Emite datos de transacción actualizada
    transaccion_anulada = Signal(int)  # Emite ID de transacción anulada
    detalles_registrados = Signal(int)  # Emite ID de transacción cuando se registran detalles
    
    def __init__(self, parent=None, titulo="Registro de Transacción", 
                ancho_porcentaje=90, alto_porcentaje=90,
                inscripcion_id: int = None,  # type:ignore
                programa_id: int = None,  # type:ignore
                estudiante_id: int = None, # type:ignore
                modo: str = "nuevo"):  # "nuevo", "editar", "visualizar"
        """
        Inicializar overlay de transacción

        Args:
            parent: Widget padre
            titulo: Título del overlay
            ancho_porcentaje: Ancho relativo
            alto_porcentaje: Alto relativo
            inscripcion_id: ID de inscripción
            programa_id: ID de programa
            estudiante_id: ID de estudiante
            modo: "nuevo", "editar" o "visualizar"
        """
        super().__init__(parent, titulo, ancho_porcentaje, alto_porcentaje)

        logger.info(f"🔵 INICIALIZANDO TransaccionOverlay - inscripcion_id: {inscripcion_id}, modo: {modo}")

        # Datos de la transacción
        self.transaccion_id: Optional[int] = None
        self.inscripcion_id = inscripcion_id
        self.programa_id = programa_id
        self.estudiante_id = estudiante_id
        self.modo = modo
        
        self.datos_inscripcion: Optional[Dict] = None
        self.datos_programa: Optional[Dict] = None
        self.datos_estudiante: Optional[Dict] = None
        self.transaccion_guardada: bool = False
        
        # Detalles temporales
        self.detalles_temporales: List[Dict] = []
        self.proximo_orden: int = 1
        
        # Estado del overlay
        self.modo_detalles: bool = False
        
        # Configurar UI específica
        self.setup_transaccion_ui()
        
        # Si es modo nuevo, validar que tenemos los IDs necesarios
        if self.modo == "nuevo":
            if not all([self.inscripcion_id, self.programa_id, self.estudiante_id]):
                logger.error(f"Faltan parámetros obligatorios para modo nuevo: inscripcion={self.inscripcion_id}, programa={self.programa_id}, estudiante={self.estudiante_id}")
                # Podríamos lanzar una excepción o manejarlo en show_form
        
        logger.debug(f"✅ TransaccionOverlay inicializado en modo {modo} para inscripción {inscripcion_id}")
    
    def setup_transaccion_ui(self):
        """Configurar la interfaz específica de transacciones con scroll area"""
        logger.debug("🔄 Configurando UI de transacción")

        # Crear un widget contenedor para todo el contenido
        container_widget = QWidget()
        container_layout = QVBoxLayout(container_widget)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Crear Scroll Area principal
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f5f5f5;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #bdc3c7;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3498db;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        # ========== SECCIÓN SUPERIOR: DATOS DE LA TRANSACCIÓN ==========
        self.datos_frame = QFrame()
        self.datos_frame.setObjectName("datosFrame")
        self.datos_frame.setStyleSheet("""
            #datosFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }
            #datosFrame:hover {
                border: 1px solid #1a237e;
            }
        """)
        self.datos_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        datos_layout = QVBoxLayout(self.datos_frame)
        datos_layout.setContentsMargins(20, 20, 20, 20)
        datos_layout.setSpacing(15)

        # Título de sección con mejor estilo
        titulo_datos = QLabel("📋 DATOS DE LA TRANSACCIÓN")
        titulo_datos.setObjectName("tituloSeccion")
        titulo_datos.setStyleSheet("""
            #tituloSeccion {
                font-size: 18px;
                font-weight: bold;
                color: #1a237e;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #e8eaf6, stop:1 #c5cae9);
                padding: 12px 15px;
                border-radius: 8px;
                margin: 0px;
                border-left: 5px solid #1a237e;
            }
        """)
        titulo_datos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        datos_layout.addWidget(titulo_datos)

        # Grid para campos principales
        grid_datos = QGridLayout()
        grid_datos.setContentsMargins(10, 10, 10, 10)
        grid_datos.setSpacing(15)

        # Estilo para labels
        label_style = """
            QLabel {
                font-weight: 600;
                color: #2c3e50;
                font-size: 13px;
                padding: 5px;
                background-color: transparent;
            }
        """

        # Estilo para campos de entrada
        field_style = """
            QLineEdit, QDateEdit, QComboBox {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
                min-height: 20px;
            }
            QLineEdit:focus, QDateEdit:focus, QComboBox:focus {
                border: 2px solid #1a237e;
                background-color: #f8f9fa;
            }
            QLineEdit:read-only {
                background-color: #f5f5f5;
                color: #666;
                border: 1px solid #ddd;
            }
        """

        # Fila 0: Número de Transacción (solo lectura)
        lbl_numero = QLabel("N° Transacción:")
        lbl_numero.setMinimumWidth(150)
        lbl_numero.setStyleSheet(label_style)

        self.txt_numero_transaccion = QLineEdit()
        self.txt_numero_transaccion.setReadOnly(True)
        self.txt_numero_transaccion.setPlaceholderText("Se generará automáticamente")
        self.txt_numero_transaccion.setStyleSheet(field_style + "background-color: #f5f5f5;")
        self.txt_numero_transaccion.setMinimumHeight(40)
        grid_datos.addWidget(lbl_numero, 0, 0)
        grid_datos.addWidget(self.txt_numero_transaccion, 0, 1)

        # Fila 0: Fecha de Pago
        lbl_fecha = QLabel("Fecha Pago:")
        lbl_fecha.setStyleSheet(label_style)

        self.date_fecha_pago = QDateEdit()
        self.date_fecha_pago.setDate(QDate.currentDate())
        self.date_fecha_pago.setCalendarPopup(True)
        self.date_fecha_pago.setDisplayFormat("dd/MM/yyyy")
        self.date_fecha_pago.setStyleSheet(field_style)
        self.date_fecha_pago.setMinimumHeight(40)
        grid_datos.addWidget(lbl_fecha, 0, 2)
        grid_datos.addWidget(self.date_fecha_pago, 0, 3)

        # Fila 1: Estudiante
        lbl_estudiante = QLabel("Estudiante:")
        lbl_estudiante.setStyleSheet(label_style)

        self.lbl_estudiante_info = QLabel()
        self.lbl_estudiante_info.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-weight: 500;
                color: #2c3e50;
                min-height: 20px;
            }
        """)
        self.lbl_estudiante_info.setMinimumHeight(40)
        grid_datos.addWidget(lbl_estudiante, 1, 0)
        grid_datos.addWidget(self.lbl_estudiante_info, 1, 1, 1, 3)

        # Fila 2: Programa
        lbl_programa = QLabel("Programa:")
        lbl_programa.setStyleSheet(label_style)

        self.lbl_programa_info = QLabel()
        self.lbl_programa_info.setStyleSheet("""
            QLabel {
                background-color: #f8f9fa;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                font-weight: 500;
                color: #2c3e50;
                min-height: 20px;
            }
        """)
        self.lbl_programa_info.setMinimumHeight(40)
        grid_datos.addWidget(lbl_programa, 2, 0)
        grid_datos.addWidget(self.lbl_programa_info, 2, 1, 1, 3)

        # Fila 3: Monto Final (único monto visible para el usuario)
        lbl_monto_final = QLabel("Monto Final:")
        lbl_monto_final.setStyleSheet(label_style)

        self.lbl_monto_final = QLabel("Bs. 0.00")
        self.lbl_monto_final.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #e8f5e8, stop:1 #c8e6c9);
                padding: 12px;
                border: 2px solid #27ae60;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                color: #27ae60;
                min-height: 20px;
            }
        """)
        self.lbl_monto_final.setMinimumHeight(40)
        self.lbl_monto_final.setAlignment(Qt.AlignmentFlag.AlignCenter)
        grid_datos.addWidget(lbl_monto_final, 3, 0)
        grid_datos.addWidget(self.lbl_monto_final, 3, 1, 1, 3)

        datos_layout.addLayout(grid_datos)
        datos_layout.addStretch()

        # ========== SECCIÓN MEDIA: DATOS DE PAGO ==========
        self.pago_frame = QFrame()
        self.pago_frame.setObjectName("pagoFrame")
        self.pago_frame.setStyleSheet("""
            #pagoFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }
            #pagoFrame:hover {
                border: 1px solid #1a237e;
            }
        """)
        self.pago_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        pago_layout = QVBoxLayout(self.pago_frame)
        pago_layout.setContentsMargins(20, 20, 20, 20)
        pago_layout.setSpacing(15)

        # Título de sección
        titulo_pago = QLabel("💳 DATOS DEL PAGO")
        titulo_pago.setObjectName("tituloSeccion")
        titulo_pago.setStyleSheet("""
            #tituloSeccion {
                font-size: 18px;
                font-weight: bold;
                color: #1a237e;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #e8eaf6, stop:1 #c5cae9);
                padding: 12px 15px;
                border-radius: 8px;
                margin: 0px;
                border-left: 5px solid #1a237e;
            }
        """)
        titulo_pago.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pago_layout.addWidget(titulo_pago)

        # Grid para datos de pago
        grid_pago = QGridLayout()
        grid_pago.setContentsMargins(10, 10, 10, 10)
        grid_pago.setSpacing(15)

        # Forma de Pago
        lbl_forma_pago = QLabel("Forma de Pago:")
        lbl_forma_pago.setStyleSheet(label_style)

        self.cbo_forma_pago = QComboBox()
        self.cbo_forma_pago.setStyleSheet(field_style)
        self.cbo_forma_pago.setMinimumHeight(40)
        self._cargar_formas_pago()
        self.cbo_forma_pago.currentIndexChanged.connect(self._on_forma_pago_changed)
        grid_pago.addWidget(lbl_forma_pago, 0, 0)
        grid_pago.addWidget(self.cbo_forma_pago, 0, 1)

        # Estado
        lbl_estado = QLabel("Estado:")
        lbl_estado.setStyleSheet(label_style)

        self.cbo_estado = QComboBox()
        self.cbo_estado.setStyleSheet(field_style)
        self.cbo_estado.setMinimumHeight(40)
        self._cargar_estados()
        grid_pago.addWidget(lbl_estado, 0, 2)
        grid_pago.addWidget(self.cbo_estado, 0, 3)

        # Número de Comprobante
        lbl_comprobante = QLabel("N° Comprobante:")
        lbl_comprobante.setStyleSheet(label_style)

        self.txt_comprobante = QLineEdit()
        self.txt_comprobante.setPlaceholderText("Ingrese número de comprobante")
        self.txt_comprobante.setStyleSheet(field_style)
        self.txt_comprobante.setMinimumHeight(40)
        grid_pago.addWidget(lbl_comprobante, 1, 0)
        grid_pago.addWidget(self.txt_comprobante, 1, 1)

        # Banco Origen
        lbl_banco = QLabel("Banco Origen:")
        lbl_banco.setStyleSheet(label_style)

        self.txt_banco = QLineEdit()
        self.txt_banco.setPlaceholderText("Nombre del banco")
        self.txt_banco.setStyleSheet(field_style)
        self.txt_banco.setMinimumHeight(40)
        grid_pago.addWidget(lbl_banco, 1, 2)
        grid_pago.addWidget(self.txt_banco, 1, 3)

        # Cuenta Origen
        lbl_cuenta = QLabel("Cuenta Origen:")
        lbl_cuenta.setStyleSheet(label_style)

        self.txt_cuenta = QLineEdit()
        self.txt_cuenta.setPlaceholderText("Número de cuenta")
        self.txt_cuenta.setStyleSheet(field_style)
        self.txt_cuenta.setMinimumHeight(40)
        grid_pago.addWidget(lbl_cuenta, 2, 0)
        grid_pago.addWidget(self.txt_cuenta, 2, 1, 1, 3)

        pago_layout.addLayout(grid_pago)

        # Observaciones
        lbl_observaciones = QLabel("Observaciones:")
        lbl_observaciones.setStyleSheet(label_style)

        self.txt_observaciones = QTextEdit()
        self.txt_observaciones.setMaximumHeight(100)
        self.txt_observaciones.setMinimumHeight(60)
        self.txt_observaciones.setPlaceholderText("Observaciones adicionales...")
        self.txt_observaciones.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 2px solid #e0e0e0;
                border-radius: 6px;
                background-color: white;
                font-size: 13px;
            }
            QTextEdit:focus {
                border: 2px solid #1a237e;
            }
        """)
        pago_layout.addWidget(lbl_observaciones)
        pago_layout.addWidget(self.txt_observaciones)
        pago_layout.addStretch()

        # ========== SECCIÓN INFERIOR: DETALLES DE LA TRANSACCIÓN ==========
        self.detalles_frame = QFrame()
        self.detalles_frame.setObjectName("detallesFrame")
        self.detalles_frame.setStyleSheet("""
            #detallesFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
            }
            #detallesFrame:hover {
                border: 1px solid #1a237e;
            }
        """)
        self.detalles_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        detalles_layout = QVBoxLayout(self.detalles_frame)
        detalles_layout.setContentsMargins(20, 20, 20, 20)
        detalles_layout.setSpacing(15)

        # Título de sección con botón de agregar
        header_detalles = QHBoxLayout()
        header_detalles.setContentsMargins(0, 0, 0, 0)

        titulo_detalles = QLabel("📦 DETALLES DE LA TRANSACCIÓN")
        titulo_detalles.setObjectName("tituloSeccion")
        titulo_detalles.setStyleSheet("""
            #tituloSeccion {
                font-size: 18px;
                font-weight: bold;
                color: #1a237e;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                           stop:0 #e8eaf6, stop:1 #c5cae9);
                padding: 12px 15px;
                border-radius: 8px;
                margin: 0px;
                border-left: 5px solid #1a237e;
            }
        """)
        titulo_detalles.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.btn_agregar_detalle = QPushButton("➕ AGREGAR CONCEPTO")
        self.btn_agregar_detalle.setObjectName("btnAgregarDetalle")
        self.btn_agregar_detalle.setStyleSheet("""
            #btnAgregarDetalle {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 13px;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
                min-width: 180px;
                min-height: 40px;
            }
            #btnAgregarDetalle:hover {
                background-color: #2ecc71;
            }
            #btnAgregarDetalle:pressed {
                background-color: #229954;
            }
            #btnAgregarDetalle:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_agregar_detalle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_agregar_detalle.clicked.connect(self._agregar_detalle)

        header_detalles.addWidget(titulo_detalles, 1)
        header_detalles.addWidget(self.btn_agregar_detalle)

        detalles_layout.addLayout(header_detalles)

        # Tabla de detalles
        self.tabla_detalles = QTableWidget()
        self.tabla_detalles.setColumnCount(7)
        self.tabla_detalles.setHorizontalHeaderLabels([
            "Orden", "Concepto", "Descripción", "Cantidad", 
            "P. Unitario", "Subtotal", "Acciones"
        ])
        self.tabla_detalles.setColumnHidden(0, True)  # Ocultar columna orden

        # Configurar estilo de la tabla
        self.tabla_detalles.setStyleSheet("""
            QTableWidget {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1a237e;
            }
            QHeaderView::section {
                background-color: #1a237e;
                color: white;
                padding: 12px;
                border: none;
                font-weight: bold;
                font-size: 13px;
            }
        """)

        # Configurar expansión de columnas
        header = self.tabla_detalles.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_detalles.setAlternatingRowColors(True)
        self.tabla_detalles.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_detalles.setMinimumHeight(200)
        detalles_layout.addWidget(self.tabla_detalles)

        # Resumen de detalles
        resumen_detalles = QHBoxLayout()
        resumen_detalles.setContentsMargins(0, 10, 0, 10)

        self.lbl_total_detalles = QLabel("Total Detalles: Bs. 0.00")
        self.lbl_total_detalles.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #1a237e;
                padding: 10px 15px;
                background-color: #e8eaf6;
                border-radius: 6px;
            }
        """)

        self.lbl_saldo_pendiente = QLabel("Saldo Pendiente: Bs. 0.00")
        self.lbl_saldo_pendiente.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #e74c3c;
                padding: 10px 15px;
                background-color: #fdeded;
                border-radius: 6px;
                margin-left: 10px;
            }
        """)

        resumen_detalles.addStretch()
        resumen_detalles.addWidget(self.lbl_total_detalles)
        resumen_detalles.addWidget(self.lbl_saldo_pendiente)

        detalles_layout.addLayout(resumen_detalles)

        # Botones de acción
        botones_detalles = QHBoxLayout()
        botones_detalles.setContentsMargins(0, 10, 0, 0)

        button_style = """
            QPushButton {
                font-weight: bold;
                font-size: 14px;
                padding: 15px 25px;
                border-radius: 8px;
                border: none;
                min-width: 250px;
                min-height: 50px;
            }
            QPushButton:pressed {
                padding-top: 17px;
                padding-bottom: 13px;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """

        self.btn_guardar_transaccion = QPushButton("💾 GUARDAR CAMBIOS")
        self.btn_guardar_transaccion.setObjectName("btnGuardarTransaccion")
        self.btn_guardar_transaccion.setStyleSheet(button_style + """
            QPushButton {
                background-color: #3498db;
                color: white;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_guardar_transaccion.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_guardar_transaccion.clicked.connect(self._guardar_cambios)

        self.btn_finalizar = QPushButton("✅ FINALIZAR")
        self.btn_finalizar.setObjectName("btnFinalizar")
        self.btn_finalizar.setStyleSheet(button_style + """
            QPushButton {
                background-color: #27ae60;
                color: white;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        self.btn_finalizar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_finalizar.clicked.connect(self._finalizar)

        self.btn_ver_comprobante = QPushButton("🖨️ VER COMPROBANTE")
        self.btn_ver_comprobante.setObjectName("btnVerComprobante")
        self.btn_ver_comprobante.setStyleSheet(button_style + """
            QPushButton {
                background-color: #f39c12;
                color: white;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.btn_ver_comprobante.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ver_comprobante.clicked.connect(self._ver_comprobante)
        self.btn_ver_comprobante.setVisible(False)

        botones_detalles.addStretch()
        botones_detalles.addWidget(self.btn_guardar_transaccion)
        botones_detalles.addWidget(self.btn_finalizar)
        botones_detalles.addWidget(self.btn_ver_comprobante)
        botones_detalles.addStretch()

        detalles_layout.addLayout(botones_detalles)
        detalles_layout.addStretch()

        # Agregar todos los frames al contenedor
        container_layout.addWidget(self.datos_frame)
        container_layout.addWidget(self.pago_frame)
        container_layout.addWidget(self.detalles_frame)
        container_layout.addStretch()

        # Configurar el scroll area
        scroll_area.setWidget(container_widget)

        # Agregar scroll area al content_layout del BaseOverlay
        self.content_layout.addWidget(scroll_area)

        # Estado inicial de los botones
        self._actualizar_estado_botones()

        logger.debug("✅ UI de transacción configurada con scroll area")
    
    def _cargar_formas_pago(self):
        """Cargar formas de pago desde constantes"""
        self.cbo_forma_pago.clear()
        for forma in FormaPago:
            display = FormaPago.get_display_names().get(forma.value, forma.value)
            self.cbo_forma_pago.addItem(display, forma.value)
    
    def _cargar_estados(self):
        """Cargar estados de transacción desde constantes"""
        self.cbo_estado.clear()
        for estado in EstadoTransaccion:
            display = EstadoTransaccion.get_display_names().get(estado.value, estado.value)
            self.cbo_estado.addItem(display, estado.value)
    
    def _on_forma_pago_changed(self, index):
        """Manejar cambio de forma de pago"""
        forma_pago = self.cbo_forma_pago.currentData()
        es_transferencia = forma_pago == FormaPago.TRANSFERENCIA.value
        es_deposito = forma_pago == FormaPago.DEPOSITO.value
        requiere_comprobante = es_transferencia or es_deposito

        self.txt_comprobante.setVisible(requiere_comprobante)
        self.txt_banco.setVisible(es_transferencia)
        self.txt_cuenta.setVisible(es_transferencia)

        layout = self.pago_frame.layout()
        if layout:
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item is None:
                    continue
                sub_layout = item.layout()
                if sub_layout:
                    for j in range(sub_layout.count()):
                        sub_item = sub_layout.itemAt(j)
                        if sub_item is None:
                            continue
                        widget = sub_item.widget()
                        if widget and isinstance(widget, QLabel):
                            texto = widget.text()
                            if "Comprobante" in texto:
                                widget.setVisible(requiere_comprobante)
                            elif "Banco" in texto:
                                widget.setVisible(es_transferencia)
                            elif "Cuenta" in texto:
                                widget.setVisible(es_transferencia)
    
    def _actualizar_monto_final(self):
        """Actualizar monto final basado en los detalles"""
        total_detalles = sum(detalle.get('subtotal', 0) for detalle in self.detalles_temporales)
        self.lbl_monto_final.setText(f"Bs. {total_detalles:,.2f}")
        
        # Actualizar resumen
        self.lbl_total_detalles.setText(f"Total Detalles: Bs. {total_detalles:,.2f}")
        
        # Actualizar en la base de datos si hay transacción guardada
        if self.transaccion_id and not self.solo_lectura:
            self._actualizar_montos_transaccion(total_detalles)
    
    def _actualizar_montos_transaccion(self, monto_final: float):
        """Actualizar los montos de la transacción en la base de datos"""
        try:
            # Obtener datos actuales de la transacción
            if self.transaccion_id is None:
                logger.warning("No hay transacción activa para actualizar montos")
                return
            
            transaccion = TransaccionModel.obtener_por_id(self.transaccion_id)
            if transaccion and transaccion.get('success'):
                datos = transaccion.get('transaccion', {})
                
                # Actualizar montos (descuento se mantiene como 0)
                datos_actualizados = {
                    'id': self.transaccion_id,
                    'monto_total': monto_final,
                    'descuento_total': 0,
                    'monto_final': monto_final
                }
                
                # Actualizar en la base de datos
                resultado = TransaccionModel.actualizar(self.transaccion_id,datos_actualizados)
                if resultado.get('success'):
                    logger.info(f"Montos actualizados para transacción {self.transaccion_id}")
                else:
                    logger.error(f"Error actualizando montos: {resultado.get('error')}")
        except Exception as e:
            logger.error(f"Error al actualizar montos: {e}")
    
    def _agregar_detalle(self):
        """Abrir diálogo para agregar detalle de concepto y guardarlo en BD"""
        logger.debug("🔄 Abriendo diálogo para agregar detalle")
        dialog = DetalleTransaccionDialog(
            self,
            inscripcion_id=self.inscripcion_id,
            datos_inscripcion=self.datos_inscripcion,
            datos_programa=self.datos_programa
        )

        if dialog.exec() == QDialog.DialogCode.Accepted:
            detalle = dialog.obtener_detalle()

            # Si tenemos transacción_id, guardar en BD inmediatamente
            if self.transaccion_id:
                from model.detalle_transaccion_model import DetalleTransaccionModel

                # Mapeo actualizado con los IDs reales de conceptos_pago
                concepto_map = {
                    'matricula': 6,
                    'inscripcion': 7,
                    'mensualidad': 8,
                    'certificado': 9,
                    'material': 10,
                    'otro': 6  # Por defecto usar MATRICULA si no coincide
                }

                concepto_codigo = detalle['concepto_pago_id']
                concepto_id = concepto_map.get(concepto_codigo)

                if not concepto_id:
                    logger.error(f"❌ Concepto '{concepto_codigo}' no encontrado en mapeo")
                    self.mostrar_mensaje("Error", f"Concepto '{detalle['concepto_nombre']}' no configurado", "error")
                    return

                datos_bd = {
                    'transaccion_id': self.transaccion_id,
                    'concepto_pago_id': concepto_id,
                    'descripcion': detalle['descripcion'],
                    'cantidad': int(detalle['cantidad']),
                    'precio_unitario': detalle['precio_unitario'],
                    'subtotal': detalle['subtotal'],
                    'orden': self.proximo_orden
                }

                logger.info(f"📦 Guardando detalle en BD: {datos_bd}")
                resultado = DetalleTransaccionModel.crear(datos_bd)

                if resultado.get('success'):
                    detalle['id'] = resultado.get('id')
                    logger.info(f"✅ Detalle guardado en BD con ID: {resultado.get('id')}")
                else:
                    logger.error(f"❌ Error guardando detalle: {resultado.get('error')}")
                    self.mostrar_mensaje("Error", f"No se pudo guardar el detalle: {resultado.get('error')}", "error")
                    return

            detalle['orden'] = self.proximo_orden
            self.proximo_orden += 1
            self.detalles_temporales.append(detalle)
            self._refrescar_tabla_detalles()
            self._actualizar_monto_final()
            logger.info(f"✅ Detalle agregado: {detalle.get('descripcion')} - Bs. {detalle.get('subtotal')}")
    
    def _refrescar_tabla_detalles(self):
        """Actualizar la tabla con los detalles temporales"""
        self.tabla_detalles.setRowCount(len(self.detalles_temporales))
        
        for row, detalle in enumerate(self.detalles_temporales):
            # Orden (oculto)
            item_orden = QTableWidgetItem(str(detalle.get('orden', row + 1)))
            item_orden.setData(Qt.ItemDataRole.UserRole, detalle)
            self.tabla_detalles.setItem(row, 0, item_orden)
            
            # Concepto
            concepto = detalle.get('concepto_nombre', detalle.get('concepto_pago_id', ''))
            self.tabla_detalles.setItem(row, 1, QTableWidgetItem(str(concepto)))
            
            # Descripción
            self.tabla_detalles.setItem(row, 2, QTableWidgetItem(detalle.get('descripcion', '')))
            
            # Cantidad
            cantidad = detalle.get('cantidad', 1)
            self.tabla_detalles.setItem(row, 3, QTableWidgetItem(str(cantidad)))
            
            # Precio Unitario
            precio = detalle.get('precio_unitario', 0)
            self.tabla_detalles.setItem(row, 4, QTableWidgetItem(f"Bs. {precio:,.2f}"))
            
            # Subtotal
            subtotal = detalle.get('subtotal', 0)
            item_subtotal = QTableWidgetItem(f"Bs. {subtotal:,.2f}")
            item_subtotal.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tabla_detalles.setItem(row, 5, item_subtotal)
            
            # Botón Eliminar
            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setFixedSize(40, 30)
            btn_eliminar.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            btn_eliminar.clicked.connect(lambda checked, r=row: self._eliminar_detalle(r))
            self.tabla_detalles.setCellWidget(row, 6, btn_eliminar)
            
        # Ajustar columnas
        self.tabla_detalles.setColumnWidth(1, 150)
        self.tabla_detalles.setColumnWidth(2, 250)
        self.tabla_detalles.setColumnWidth(3, 80)
        self.tabla_detalles.setColumnWidth(4, 120)
        self.tabla_detalles.setColumnWidth(5, 120)
        self.tabla_detalles.setColumnWidth(6, 50)
    
    def _eliminar_detalle(self, row):
        """Eliminar un detalle de la lista temporal y de la BD"""
        if row < len(self.detalles_temporales):
            detalle = self.detalles_temporales.pop(row)

            # Si el detalle tiene ID, eliminar de la BD
            if detalle.get('id') and self.transaccion_id:
                from model.detalle_transaccion_model import DetalleTransaccionModel
                resultado = DetalleTransaccionModel.eliminar(detalle['id'])
                if resultado.get('success'):
                    logger.info(f"✅ Detalle {detalle['id']} eliminado de BD")
                else:
                    logger.error(f"❌ Error eliminando detalle de BD: {resultado.get('error')}")

            self._refrescar_tabla_detalles()
            self._actualizar_monto_final()
            logger.info(f"Detalle eliminado: {detalle.get('descripcion', '')}")
    
    def _guardar_cambios(self):
        """Guardar los cambios realizados en la transacción"""
        logger.info("💾 Intentando guardar cambios en transacción")

        if self.solo_lectura:
            logger.warning("Intento de guardar en modo solo lectura")
            return

        # Validar campos obligatorios
        valido, errores = self.validar_formulario()
        if not valido:
            logger.warning(f"Validación fallida: {errores}")
            self.mostrar_mensaje(
                "Validación",
                "Por favor corrija los siguientes errores:\n\n• " + "\n• ".join(errores),
                "error"
            )
            return

        # Obtener datos actualizados
        datos = self.obtener_datos()
        if not datos:
            logger.error("No se pudieron obtener los datos para guardar")
            self.mostrar_mensaje(
                "Error",
                "No se pudieron obtener los datos para guardar. Por favor intente nuevamente.",
                "error"
            )
            return

        if self.transaccion_id is None:
            logger.error("No hay transacción activa para guardar")
            self.mostrar_mensaje(
                "Error",
                "No hay una transacción activa para guardar. Por favor intente crear una nueva transacción.",
                "error"
            )
            return

        logger.info(f"Actualizando transacción ID: {self.transaccion_id} con datos: {datos}")

        # Actualizar en la base de datos
        resultado = TransaccionModel.actualizar(self.transaccion_id, datos)

        if resultado.get('success'):
            logger.info(f"✅ Cambios guardados correctamente para transacción {self.transaccion_id}")
            self.mostrar_mensaje("Éxito", "Cambios guardados correctamente", "success")
            self.transaccion_actualizada.emit(datos)

            # NO recargar la transacción aquí, solo actualizar campos específicos si es necesario
            # self._recargar_transaccion()  # <-- COMENTAR O ELIMINAR ESTA LÍNEA
        else:
            error_msg = resultado.get('error', 'Error desconocido')
            logger.error(f"❌ Error guardando cambios: {error_msg}")
            self.mostrar_mensaje(
                "Error",
                f"No se pudieron guardar los cambios: {error_msg}",
                "error"
            )
    
    def _finalizar(self):
        """Finalizar el registro de la transacción"""
        logger.info("🏁 Finalizando transacción")

        if not self.detalles_temporales:
            logger.warning("Intento de finalizar sin detalles")
            self.mostrar_mensaje(
                "Validación",
                "Debe agregar al menos un detalle a la transacción",
                "warning"
            )
            return

        # Guardar los detalles en la base de datos (ya están guardados individualmente)
        logger.info(f"Guardando {len(self.detalles_temporales)} detalles para transacción {self.transaccion_id}")

        # Actualizar montos finales en la transacción (por si acaso)
        total_detalles = sum(d.get('subtotal', 0) for d in self.detalles_temporales)
        if self.transaccion_id:
            datos_actualizacion = {
                'id': self.transaccion_id,
                'monto_total': total_detalles,
                'monto_final': total_detalles
            }
            TransaccionModel.actualizar(self.transaccion_id, datos_actualizacion)

        # Cambiar a modo visualización (esto mantiene los datos visibles pero no editables)
        self._activar_modo_visualizacion()

        # Emitir señal
        self.detalles_registrados.emit(self.transaccion_id)

        self.mostrar_mensaje(
            "Éxito",
            "Transacción finalizada correctamente. Ahora solo puede visualizarse.",
            "success"
        )
    
    def _guardar_detalles(self):
        """Guardar los detalles temporales en la base de datos"""
        # Aquí se implementaría el guardado de detalles
        # Por ahora solo registramos en log
        logger.info(f"Guardando {len(self.detalles_temporales)} detalles para transacción {self.transaccion_id}")
    
    def _ver_comprobante(self):
        """Generar y mostrar comprobante de la transacción"""
        logger.info("Solicitando ver comprobante")
        self.mostrar_mensaje(
            "Comprobante",
            "Funcionalidad de comprobante en desarrollo",
            "info"
        )
    
    def _recargar_transaccion(self):
        """Recargar los datos de la transacción desde la base de datos"""
        if not self.transaccion_id:
            logger.warning("Intento de recargar sin transacción_id")
            return

        logger.debug(f"Recargando datos de transacción {self.transaccion_id}")
        try:
            resultado = TransaccionModel.obtener_por_id(self.transaccion_id)
            if resultado.get('success'):
                transaccion = resultado.get('data', {})
                # No llamar a cargar_datos porque eso limpia el formulario
                # En su lugar, actualizar los campos específicos
                self._actualizar_campos_con_datos(transaccion)
                logger.info(f"Datos recargados para transacción {self.transaccion_id}")
            else:
                logger.error(f"Error recargando transacción: {resultado.get('error')}")
        except Exception as e:
            logger.error(f"Error recargando transacción: {e}")
    
    def _actualizar_campos_con_datos(self, transaccion: Dict):
        """Actualizar los campos del formulario con los datos de la transacción sin limpiar"""
        if transaccion.get('numero_transaccion'):
            self.txt_numero_transaccion.setText(transaccion['numero_transaccion'])

        # Actualizar fecha
        fecha_pago = transaccion.get('fecha_pago')
        if fecha_pago:
            if isinstance(fecha_pago, str):
                fecha = QDate.fromString(fecha_pago, "yyyy-MM-dd")
            else:
                fecha = QDate(fecha_pago.year, fecha_pago.month, fecha_pago.day)
            self.date_fecha_pago.setDate(fecha)

        # Actualizar forma de pago
        forma_pago = transaccion.get('forma_pago', 'EFECTIVO')
        index = self.cbo_forma_pago.findData(forma_pago)
        if index >= 0:
            self.cbo_forma_pago.setCurrentIndex(index)

        # Actualizar estado
        estado = transaccion.get('estado', 'REGISTRADO')
        index = self.cbo_estado.findData(estado)
        if index >= 0:
            self.cbo_estado.setCurrentIndex(index)

        # Actualizar otros campos
        self.txt_comprobante.setText(transaccion.get('numero_comprobante', ''))
        self.txt_banco.setText(transaccion.get('banco_origen', ''))
        self.txt_cuenta.setText(transaccion.get('cuenta_origen', ''))
        self.txt_observaciones.setPlainText(transaccion.get('observaciones', ''))

        # Actualizar monto final (aunque no debería cambiar)
        monto_final = float(transaccion.get('monto_final', 0))
        self.lbl_monto_final.setText(f"Bs. {monto_final:,.2f}")
    
    def _actualizar_estado_botones(self):
        """Actualizar estado de botones según modo"""
        if self.solo_lectura:
            self.btn_guardar_transaccion.setVisible(False)
            self.btn_finalizar.setVisible(False)
            self.btn_agregar_detalle.setEnabled(False)
            self.btn_ver_comprobante.setVisible(True)
            logger.debug("Botones configurados en modo solo lectura")
        else:
            self.btn_guardar_transaccion.setVisible(True)
            self.btn_finalizar.setVisible(True)
            self.btn_agregar_detalle.setEnabled(True)
            self.btn_ver_comprobante.setVisible(False)
            logger.debug("Botones configurados en modo edición")
    
    # ===== MÉTODOS PÚBLICOS =====
    
    def inicializar_nueva_transaccion(self, inscripcion_id: int, programa_id: int, estudiante_id: int) -> bool:
        """
        Inicializar una nueva transacción (crea el registro en la base de datos)
        """
        logger.info(f"🆕 Inicializando nueva transacción para inscripción {inscripcion_id}")
        
        try:
            usuario_id = 2  # TODO: Obtener de variable global
            fecha_actual = QDate.currentDate().toString("yyyy-MM-dd")
            
            # Ajustamos el diccionario eliminando 'inscripcion_id' que no existe en la tabla
            datos_nueva = {
                'numero_transaccion': None, 
                'estudiante_id': estudiante_id, # Esta columna SÍ existe
                'programa_id': programa_id,     # Esta columna SÍ existe
                'fecha_pago': fecha_actual,
                'fecha_registro': fecha_actual,
                'monto_total': 0.0,
                'descuento_total': 0.0,
                'monto_final': 0.0,
                'forma_pago': 'EFECTIVO',
                'estado': 'REGISTRADO',
                'numero_comprobante': None,
                'banco_origen': None,
                'cuenta_origen': None,
                'observaciones': f'Pago Inscripción #{inscripcion_id}', # Guardamos el ID en observaciones
                'registrado_por': usuario_id
            }
            
            logger.debug(f"Datos para nueva transacción: {datos_nueva}")
            
            # Crear transacción
            resultado = TransaccionModel.crear(datos_nueva)
            
            if resultado.get('success'):
                self.transaccion_id = resultado.get('id')
                logger.info(f"✅ Transacción creada con ID: {self.transaccion_id}")
                
                # Cargar datos de la inscripción para mostrar en UI
                self.cargar_datos_inscripcion(inscripcion_id)
                
                # Recargar transacción para obtener el número generado
                self._recargar_transaccion()
                
                # Habilitar botones
                self._actualizar_estado_botones()
                
                return True
            else:
                error_msg = resultado.get('error', 'Error desconocido')
                logger.error(f"Error creando transacción: {error_msg}")
                self.mostrar_mensaje(
                    "Error",
                    f"No se pudo crear la transacción: {error_msg}",
                    "error"
                )
                return False
                
        except Exception as e:
            logger.error(f"Error en inicializar_nueva_transaccion: {e}")
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje(
                "Error",
                f"Error al inicializar transacción: {str(e)}",
                "error"
            )
            return False
    
    def _actualizar_ids_inscripcion(self):
        """Actualizar la transacción con los IDs de estudiante y programa"""
        if not self.transaccion_id or not self.inscripcion_id:
            logger.warning(f"No se pueden actualizar IDs: transaccion_id={self.transaccion_id}, inscripcion_id={self.inscripcion_id}")
            return
        
        logger.debug(f"Actualizando IDs de transacción {self.transaccion_id} con datos de inscripción {self.inscripcion_id}")
        
        try:
            # Obtener datos de la inscripción si no están cargados
            if not self.datos_inscripcion:
                self.cargar_datos_inscripcion(self.inscripcion_id)
            
            if self.estudiante_id and self.programa_id:
                datos_actualizacion = {
                    'id': self.transaccion_id,
                    'estudiante_id': self.estudiante_id,
                    'programa_id': self.programa_id
                }
                
                logger.debug(f"Actualizando con datos: {datos_actualizacion}")
                
                resultado = TransaccionModel.actualizar(self.transaccion_id, datos_actualizacion)
                if resultado.get('success'):
                    logger.info(f"IDs actualizados en transacción {self.transaccion_id}")
                else:
                    logger.error(f"Error actualizando IDs: {resultado.get('error')}")
            else:
                logger.warning(f"No se pueden actualizar IDs: estudiante_id={self.estudiante_id}, programa_id={self.programa_id}")
                    
        except Exception as e:
            logger.error(f"Error actualizando IDs de inscripción: {e}")
    
    def show_form(self, solo_lectura: bool = False) -> None:
        """Mostrar el formulario - Override del método base"""
        self.solo_lectura = solo_lectura
        logger.info(f"🔵 Mostrando formulario - modo: {self.modo}, solo_lectura: {solo_lectura}, inscripcion_id: {self.inscripcion_id}")
    
        # Si es modo visualización, forzar solo_lectura=True
        if self.modo == "visualizar":
            self.solo_lectura = True
    
        # Si es modo edición y tenemos transacción_id, cargar los datos
        if self.modo in ["editar", "visualizar"] and self.transaccion_id:
            logger.info(f"📥 Modo {self.modo}: cargando datos de transacción {self.transaccion_id}")
            self._cargar_datos_transaccion()
            
            # Si es modo visualizar, activar modo visualización después de cargar
            if self.modo == "visualizar":
                self._activar_modo_visualizacion()
    
        # Usar el método show_form de BaseOverlay
        super().show_form(solo_lectura)
    
        # Si es modo nuevo y tenemos inscripción, crear la transacción automáticamente
        if self.modo == "nuevo" and all([self.inscripcion_id, self.programa_id, self.estudiante_id]):
            QTimer.singleShot(100, self._crear_transaccion_automatica)
    
    def _cargar_datos_transaccion(self) -> None:
        """Cargar los datos de la transacción desde la base de datos"""
        if not self.transaccion_id:
            logger.warning("No hay transacción_id para cargar")
            return

        try:
            # Obtener datos de la transacción
            resultado = TransaccionModel.obtener_por_id(self.transaccion_id)

            if resultado.get('success'):
                transaccion = resultado.get('data', {})
                logger.info(f"✅ Datos de transacción cargados: {transaccion}")

                # Cargar datos básicos
                if transaccion.get('numero_transaccion'):
                    self.txt_numero_transaccion.setText(transaccion['numero_transaccion'])

                # Manejar fecha correctamente
                fecha_pago = transaccion.get('fecha_pago')
                if fecha_pago:
                    if isinstance(fecha_pago, str):
                        # Si es string, convertir desde string
                        fecha = QDate.fromString(fecha_pago, "yyyy-MM-dd")
                    else:
                        # Si es date/datetime, crear QDate directamente
                        fecha = QDate(fecha_pago.year, fecha_pago.month, fecha_pago.day)
                    self.date_fecha_pago.setDate(fecha)

                # Datos de pago
                forma_pago = transaccion.get('forma_pago', 'EFECTIVO')
                index = self.cbo_forma_pago.findData(forma_pago)
                if index >= 0:
                    self.cbo_forma_pago.setCurrentIndex(index)

                estado = transaccion.get('estado', 'REGISTRADO')
                index = self.cbo_estado.findData(estado)
                if index >= 0:
                    self.cbo_estado.setCurrentIndex(index)

                self.txt_comprobante.setText(transaccion.get('numero_comprobante', ''))
                self.txt_banco.setText(transaccion.get('banco_origen', ''))
                self.txt_cuenta.setText(transaccion.get('cuenta_origen', ''))
                self.txt_observaciones.setPlainText(transaccion.get('observaciones', ''))

                # Monto final
                monto_final = float(transaccion.get('monto_final', 0))
                self.lbl_monto_final.setText(f"Bs. {monto_final:,.2f}")

                # ===== CARGAR DETALLES DESDE LA BD =====
                try:
                    from model.detalle_transaccion_model import DetalleTransaccionModel

                    # ===== MAPEO ACTUALIZADO CON LOS IDs REALES =====
                    # Basado en la consulta: 
                    # 6: MATRICULA, 7: INSCRIPCION, 8: MENSUALIDAD, 9: CERTIFICACION, 10: MATERIAL
                    concepto_map = {
                        6: 'matricula',
                        7: 'inscripcion',
                        8: 'mensualidad',
                        9: 'certificado',
                        10: 'material'
                    }

                    # Mapa para nombres de conceptos
                    nombre_concepto_map = {
                        6: 'Matrícula',
                        7: 'Inscripción',
                        8: 'Mensualidad',
                        9: 'Certificado',
                        10: 'Material'
                    }

                    resultado_detalles = DetalleTransaccionModel.listar_por_transaccion(self.transaccion_id)
                    if resultado_detalles.get('success'):
                        detalles_bd = resultado_detalles.get('data', [])

                        # Limpiar detalles temporales actuales
                        self.detalles_temporales = []
                        self.proximo_orden = 1

                        for detalle_bd in detalles_bd:
                            concepto_id = detalle_bd['concepto_pago_id']

                            detalle = {
                                'id': detalle_bd['id'],
                                'orden': detalle_bd['orden'],
                                'concepto_pago_id': concepto_map.get(concepto_id, 'otro'),
                                'concepto_nombre': detalle_bd.get('concepto_nombre', nombre_concepto_map.get(concepto_id, 'Otro')),
                                'descripcion': detalle_bd['descripcion'],
                                'cantidad': detalle_bd['cantidad'],
                                'precio_unitario': float(detalle_bd['precio_unitario']),
                                'subtotal': float(detalle_bd['subtotal'])
                            }
                            self.detalles_temporales.append(detalle)
                            if detalle_bd['orden'] >= self.proximo_orden:
                                self.proximo_orden = detalle_bd['orden'] + 1

                        self._refrescar_tabla_detalles()
                        logger.info(f"✅ {len(detalles_bd)} detalles cargados desde BD")

                        # Actualizar el total después de cargar detalles
                        total_cargado = sum(d.get('subtotal', 0) for d in self.detalles_temporales)
                        if abs(total_cargado - monto_final) > 0.01:
                            logger.warning(f"Diferencia entre monto_final ({monto_final}) y suma de detalles ({total_cargado})")

                except ImportError:
                    logger.warning("⚠️ DetalleTransaccionModel no disponible, no se pueden cargar detalles")
                except Exception as e:
                    logger.error(f"Error cargando detalles: {e}")

                # Cargar datos de estudiante
                if transaccion.get('estudiante_id'):
                    self.estudiante_id = transaccion['estudiante_id']

                    # Construir nombre completo del estudiante
                    nombre = transaccion.get('estudiante_nombre', '')
                    apellido_p = transaccion.get('estudiante_apellido_paterno', '')
                    apellido_m = transaccion.get('estudiante_apellido_materno', '')
                    nombre_completo = f"{nombre} {apellido_p} {apellido_m}".strip()

                    if nombre_completo:
                        ci = transaccion.get('estudiante_ci', '')
                        if ci:
                            self.lbl_estudiante_info.setText(f"{nombre_completo} ({ci})")
                        else:
                            self.lbl_estudiante_info.setText(f"{nombre_completo} (ID: {self.estudiante_id})")
                    else:
                        self.lbl_estudiante_info.setText(f"Estudiante ID: {self.estudiante_id}")

                # Cargar datos de programa
                if transaccion.get('programa_id'):
                    self.programa_id = transaccion['programa_id']

                    programa_nombre = transaccion.get('programa_nombre', '')
                    programa_codigo = transaccion.get('programa_codigo', '')

                    if programa_nombre and programa_codigo:
                        self.lbl_programa_info.setText(f"{programa_codigo} - {programa_nombre} (ID: {self.programa_id})")
                    elif programa_nombre:
                        self.lbl_programa_info.setText(f"{programa_nombre} (ID: {self.programa_id})")
                    else:
                        self.lbl_programa_info.setText(f"Programa ID: {self.programa_id}")

                self.transaccion_guardada = True

            else:
                error_msg = resultado.get('error', 'Error desconocido')
                logger.error(f"❌ Error cargando transacción {self.transaccion_id}: {error_msg}")
                self.mostrar_mensaje("Error", f"No se pudo cargar la transacción: {error_msg}", "error")

        except Exception as e:
            logger.error(f"Error en _cargar_datos_transaccion: {e}")
            import traceback
            traceback.print_exc()


    def _obtener_nombre_concepto(self, concepto_id: int) -> str:
        """Obtener nombre del concepto por su ID"""
        nombres = {
            6: 'Matrícula',
            7: 'Inscripción',
            8: 'Mensualidad',
            9: 'Certificado',
            10: 'Material'
        }
        return nombres.get(concepto_id, f'Concepto {concepto_id}')
    
    def _crear_transaccion_automatica(self) -> None:
        """Crear la transacción automáticamente al abrir el overlay"""
        logger.info("🔄 Ejecutando creación automática de transacción")
        
        # Llamamos al método de inicialización con los parámetros guardados en la instancia
        # Estos parámetros fueron recibidos en el __init__
        if not all([self.inscripcion_id, self.programa_id, self.estudiante_id]):
            logger.error("No se pueden crear transacción automática: faltan IDs obligatorios")
            self.mostrar_mensaje("Error", "Faltan datos obligatorios para crear la transacción automática", "error")
            return
        
        exito = self.inicializar_nueva_transaccion(
            self.inscripcion_id,  # type: ignore
            self.programa_id,  # type: ignore
            self.estudiante_id # type: ignore
        )
        if not exito:
            QTimer.singleShot(2000, self.close_overlay)
    
    def cargar_datos_inscripcion(self, inscripcion_id: int):
        """
        Cargar datos reales desde una inscripción para mostrar en la UI
        """
        logger.info(f"📚 Cargando datos de inscripción {inscripcion_id}")
        
        try:
            self.inscripcion_id = inscripcion_id
            from model.inscripcion_model import InscripcionModel

            # Obtener detalle completo de la inscripción
            resultado = InscripcionModel.obtener_detalle_inscripcion(inscripcion_id)
            
            # Validación robusta del resultado
            if resultado and isinstance(resultado, dict) and resultado.get('success') is not False:
                datos_inscripcion = resultado.get('inscripcion', {})
                datos_estudiante = resultado.get('estudiante', {})
                datos_programa = resultado.get('programa', {})
                
                self.datos_inscripcion = datos_inscripcion
                self.datos_estudiante = datos_estudiante
                self.datos_programa = datos_programa
                
                # Actualizar la interfaz de usuario (UI)
                # Nombre completo del estudiante
                nombres = datos_estudiante.get('nombres', '')
                paterno = datos_estudiante.get('paterno', '')
                materno = datos_estudiante.get('materno', '')
                nombre_completo = f"{nombres} {paterno} {materno}".strip()
                
                self.lbl_estudiante_info.setText(nombre_completo)
                
                # Nombre del programa
                nombre_prog = datos_programa.get('nombre', 'Programa no identificado')
                self.lbl_programa_info.setText(nombre_prog)
                
                logger.info(f"✅ UI actualizada: Estudiante='{nombre_completo}', Programa='{nombre_prog}'")
            else:
                msg_error = resultado.get('error', 'No se pudo obtener el detalle') if resultado else "Resultado nulo"
                logger.error(f"❌ Error obteniendo detalle de inscripción {inscripcion_id}: {msg_error}")
                
        except Exception as e:
            logger.error(f"Error crítico en cargar_datos_inscripcion: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def set_transaccion_id(self, transaccion_id: int):
        """Establecer ID de transacción para modo edición"""
        self.transaccion_id = transaccion_id
        logger.info(f"Transacción ID establecido: {transaccion_id}")
        # No cargar aquí porque show_form lo hará después
    
    # ===== MÉTODOS ABSTRACTOS IMPLEMENTADOS =====
    
    def validar_formulario(self) -> Tuple[bool, List[str]]:
        """
        Validar campos del formulario
        
        Returns:
            Tuple[bool, List[str]]: (válido, lista de errores)
        """
        errores = []
        
        # Validar estudiante
        if not self.estudiante_id and not self.lbl_estudiante_info.text():
            errores.append("Debe seleccionar un estudiante")
        
        # Validar programa
        if not self.programa_id and not self.lbl_programa_info.text():
            errores.append("Debe seleccionar un programa")
        
        # Validar que haya al menos un detalle
        if not self.detalles_temporales:
            errores.append("Debe agregar al menos un concepto a la transacción")
        
        # Validar campos según forma de pago
        forma_pago = self.cbo_forma_pago.currentData()
        
        if forma_pago == FormaPago.TRANSFERENCIA.value:
            if not self.txt_comprobante.text().strip():
                errores.append("El número de comprobante es obligatorio para transferencias")
            if not self.txt_banco.text().strip():
                errores.append("El banco de origen es obligatorio para transferencias")
        
        elif forma_pago == FormaPago.DEPOSITO.value:
            if not self.txt_comprobante.text().strip():
                errores.append("El número de comprobante es obligatorio para depósitos")
        
        logger.debug(f"Validación completada: {len(errores)} errores")
        return (len(errores) == 0, errores)
    
    def obtener_datos(self) -> Dict[str, Any]:
        """
        Obtener datos del formulario
        
        Returns:
            Dict con datos de la transacción
        """
        try:
            monto_final = sum(detalle.get('subtotal', 0) for detalle in self.detalles_temporales)
        except:
            monto_final = 0
        
        datos = {
            'id': self.transaccion_id,
            'estudiante_id': self.estudiante_id,
            'programa_id': self.programa_id,
            'fecha_pago': self.date_fecha_pago.date().toString("yyyy-MM-dd"),
            'monto_total': monto_final,
            'descuento_total': 0,
            'monto_final': monto_final,
            'forma_pago': self.cbo_forma_pago.currentData(),
            'estado': self.cbo_estado.currentData(),
            'numero_comprobante': self.txt_comprobante.text().strip() or None,
            'banco_origen': self.txt_banco.text().strip() or None,
            'cuenta_origen': self.txt_cuenta.text().strip() or None,
            'observaciones': self.txt_observaciones.toPlainText().strip() or None,
            'inscripcion_id': self.inscripcion_id
        }
        
        logger.debug(f"Datos obtenidos del formulario: {datos}")
        return datos
    
    def clear_form(self):
        """Limpiar el formulario"""
        logger.debug("Limpiando formulario")
        
        self.transaccion_id = None
        self.inscripcion_id = None
        self.estudiante_id = None
        self.programa_id = None
        self.datos_inscripcion = None
        self.detalles_temporales = []
        self.proximo_orden = 1
        self.modo_detalles = False
        
        self.txt_numero_transaccion.clear()
        self.date_fecha_pago.setDate(QDate.currentDate())
        self.lbl_estudiante_info.clear()
        self.lbl_programa_info.clear()
        self.lbl_monto_final.setText("Bs. 0.00")
        
        self.cbo_forma_pago.setCurrentIndex(0)
        self.cbo_estado.setCurrentIndex(0)
        self.txt_comprobante.clear()
        self.txt_banco.clear()
        self.txt_cuenta.clear()
        self.txt_observaciones.clear()
        
        self.tabla_detalles.setRowCount(0)
        self.lbl_total_detalles.setText("Total Detalles: Bs. 0.00")
        self.lbl_saldo_pendiente.setText("Saldo Pendiente: Bs. 0.00")
        
        # Resetear estado de botones
        self.btn_guardar_transaccion.setEnabled(True)
        self.btn_finalizar.setEnabled(True)
        self.btn_agregar_detalle.setEnabled(True)
        self.btn_ver_comprobante.setVisible(False)
        
        logger.debug("Formulario limpiado")
    
    def cargar_datos(self, datos: Dict[str, Any]):
        """
        Cargar datos en el formulario
        
        Args:
            datos: Diccionario con datos de la transacción
        """
        logger.info(f"Cargando datos en formulario: {datos}")
        self.clear_form()
        
        if not datos:
            logger.warning("No hay datos para cargar")
            return
        
        # Cargar IDs
        self.transaccion_id = datos.get('id')
        self.inscripcion_id = datos.get('inscripcion_id')
        self.estudiante_id = datos.get('estudiante_id')
        self.programa_id = datos.get('programa_id')
        
        # Datos básicos
        self.txt_numero_transaccion.setText(datos.get('numero_transaccion', ''))
        
        if datos.get('fecha_pago'):
            fecha = QDate.fromString(datos['fecha_pago'], "yyyy-MM-dd")
            self.date_fecha_pago.setDate(fecha)
        
        # Si tenemos IDs pero no información de estudiante/programa, cargarlos
        if self.inscripcion_id and not self.datos_inscripcion:
            self.cargar_datos_inscripcion(self.inscripcion_id)
        else:
            # Información de estudiante y programa (si viene en los datos)
            if datos.get('estudiante_nombre'):
                self.lbl_estudiante_info.setText(
                    f"{datos.get('estudiante_nombre', '')} "
                    f"{datos.get('estudiante_apellido', '')} "
                    f"(CI: {datos.get('estudiante_ci', '')})"
                )
            
            if datos.get('programa_nombre'):
                self.lbl_programa_info.setText(
                    f"{datos.get('programa_nombre', '')} "
                    f"[{datos.get('programa_codigo', '')}]"
                )
        
        # Datos de pago
        index = self.cbo_forma_pago.findData(datos.get('forma_pago'))
        if index >= 0:
            self.cbo_forma_pago.setCurrentIndex(index)
        
        index = self.cbo_estado.findData(datos.get('estado'))
        if index >= 0:
            self.cbo_estado.setCurrentIndex(index)
        
        self.txt_comprobante.setText(datos.get('numero_comprobante', ''))
        self.txt_banco.setText(datos.get('banco_origen', ''))
        self.txt_cuenta.setText(datos.get('cuenta_origen', ''))
        self.txt_observaciones.setText(datos.get('observaciones', ''))
        
        # Monto final (si viene en los datos)
        monto_final = float(datos.get('monto_final', 0))
        self.lbl_monto_final.setText(f"Bs. {monto_final:,.2f}")
        
        # Aquí se cargarían los detalles si vinieran en los datos
        
        # Si es solo lectura, ajustar estado
        if self.solo_lectura:
            self._activar_modo_visualizacion()
        
        logger.info(f"Datos cargados en formulario: {self.transaccion_id}")
    
    def mostrar_pregunta(self, titulo: str, mensaje: str) -> int:
        """Mostrar diálogo de confirmación"""
        logger.debug(f"Mostrando pregunta: {titulo} - {mensaje}")
        return QMessageBox.question(
            self,
            titulo,
            mensaje,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
    
    def _on_guardar_clicked(self):
        """Override del método base para guardar"""
        logger.debug("Método _on_guardar_clicked llamado")
        
        if self.solo_lectura:
            logger.info("Modo solo lectura, cerrando overlay")
            self.close_overlay()
            return
        
        # En este overlay, el guardado se maneja con _guardar_cambios
        self._guardar_cambios()
    
    def _activar_modo_visualizacion(self):
        """Activar modo de visualización (solo lectura)"""
        logger.info("Activando modo visualización")
        self.solo_lectura = True

        # Deshabilitar todos los campos de entrada
        self.date_fecha_pago.setEnabled(False)
        self.cbo_forma_pago.setEnabled(False)
        self.cbo_estado.setEnabled(False)
        self.txt_comprobante.setEnabled(False)
        self.txt_banco.setEnabled(False)
        self.txt_cuenta.setEnabled(False)
        self.txt_observaciones.setEnabled(False)

        # Deshabilitar botones de edición
        self.btn_agregar_detalle.setEnabled(False)
        self.btn_guardar_transaccion.setVisible(False)
        self.btn_finalizar.setVisible(False)

        # Mostrar botón de comprobante
        self.btn_ver_comprobante.setVisible(True)

        # Configurar tabla como solo lectura
        self.tabla_detalles.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabla_detalles.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.tabla_detalles.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        # Cambiar estilo visual para indicar modo lectura
        self.setStyleSheet("""
            QLineEdit:read-only, QDateEdit:read-only, QComboBox:disabled, QTextEdit:disabled {
                background-color: #f5f5f5;
                color: #2c3e50;
                border: 1px solid #bdc3c7;
            }
            QLabel {
                color: #2c3e50;
            }
        """)

        # Actualizar el título para indicar modo visualización
        titulo_actual = self.titulo
        if "VISUALIZACIÓN" not in titulo_actual:
            self.set_titulo(f"👁️ {titulo_actual} - MODO VISUALIZACIÓN")

        logger.info("Modo visualización activado - Transacción en solo lectura")
    