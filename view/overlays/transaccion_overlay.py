# view/overlays/transaccion_overlay.py
"""
Overlay para gestionar transacciones financieras.
Permite registrar pagos, gestionar documentos adjuntos y ver detalles.
"""

import os
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton,
    QFrame, QGroupBox, QScrollArea, QMessageBox, QSizePolicy,
    QSpacerItem, QTextEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QCheckBox, QDoubleSpinBox,
    QFileDialog, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QCursor, QColor, QIcon, QPixmap

from .base_overlay import BaseOverlay
from config.constants import AppConstants, Messages, FormaPago, EstadoTransaccion, TipoDocumento
from config.paths import Paths
from model.transaccion_model import TransaccionModel
from model.estudiante_model import EstudianteModel
from model.programa_model import ProgramaModel
from model.concepto_pago_model import ConceptoPagoModel
from utils.file_manager import FileManager

logger = logging.getLogger(__name__)

class TransaccionOverlay(BaseOverlay):
    """
    Overlay para gestionar transacciones financieras.
    
    Permite:
    - Registrar nuevas transacciones
    - Editar transacciones existentes
    - Gestionar documentos adjuntos
    - Visualizar detalles de transacciones
    - Asociar transacciones a estudiantes y programas
    """
    
    # ▓▒░░▒▓ Señales específicas ▓▒░░▒▓
    transaccion_creada = Signal(dict)      # Datos de la transacción creada
    transaccion_actualizada = Signal(dict) # Datos de la transacción actualizada
    transaccion_anulada = Signal(int)      # ID de transacción anulada
    documento_subido = Signal(dict)        # Documento subido
    
    # ▓▒░░▒▓ MÉTODOS DE INICIALIZACIÓN ▓▒░░▒▓
    
    def __init__(self, parent=None):
        """
        Inicializar overlay de transacción.
        
        Args:
            parent: Widget padre (opcional)
        """
        super().__init__(
            parent=parent,
            titulo="💰 Gestión de Transacción",
            ancho_porcentaje=AppConstants.OVERLAY_WIDTH_PERCENT,
            alto_porcentaje=AppConstants.OVERLAY_HEIGHT_PERCENT
        )
        
        # Datos de la transacción
        self.transaccion_id = None
        self.estudiante_id = None
        self.programa_id = None
        self.inscripcion_id = None
        self.detalles_transaccion = []
        self.documentos_adjuntos = []
        
        # Control para título
        self._titulo_actualizado = False
        
        # Variables para cache de datos
        self._estudiante_cache = None
        self._programa_cache = None
        
        # Ruta temporal para documentos
        self.documentos_temp = []
        
        # Configurar UI específica
        self.setup_transaccion_ui()
        
        # Configurar tamaño mínimo
        self.setMinimumSize(1000, 800)
        
        logger.debug("✅ TransaccionOverlay inicializado")
    
    def _previsualizar_numero_transaccion(self):
        """Previsualizar número de transacción basado en los datos actuales."""
        try:
            from datetime import datetime

            # Obtener datos actuales
            fecha_pago = self.fecha_pago_input.date().toPython()
            es_ingreso = True  # Por defecto asumimos ingreso

            # Determinar si es ingreso o egreso basado en monto
            total = self._calcular_total()
            es_ingreso = total >= 0  # Puedes ajustar esta lógica

            # Generar previsualización
            from model.transaccion_model import TransaccionModel

            numero_preview = TransaccionModel.generar_numero_transaccion(
                fecha_pago=fecha_pago,
                estudiante_id=self.estudiante_id,
                programa_id=self.programa_id,
                inscripcion_id=self.inscripcion_id,
                usuario_id=1,  # ID temporal para previsualización
                es_ingreso=es_ingreso
            )

            # Asegurar que numero_preview no sea None
            if numero_preview is None:
                numero_preview = "(Se generará al guardar)"

            # Actualizar label
            self.numero_transaccion_label.setText(str(numero_preview))
            self.numero_transaccion_label.setStyleSheet("font-weight: bold; color: #27ae60;")

        except Exception as e:
            logger.error(f"Error previsualizando número: {e}")
            self.numero_transaccion_label.setText("(Se generará al guardar)")
    
    def _calcular_total(self):
        """Calcular total actual del formulario."""
        subtotal = 0.0
        
        for row in range(self.tabla_detalles.rowCount()):
            # Obtener widgets con verificación de tipos
            widget_cant = self.tabla_detalles.cellWidget(row, 2)
            widget_precio = self.tabla_detalles.cellWidget(row, 3)
            
            # Verificar que sean QDoubleSpinBox antes de usar value()
            if (widget_cant and isinstance(widget_cant, QDoubleSpinBox) and
                widget_precio and isinstance(widget_precio, QDoubleSpinBox)):
                
                try:
                    subtotal += widget_cant.value() * widget_precio.value()
                except (AttributeError, TypeError) as e:
                    logger.warning(f"Error calculando subtotal fila {row}: {e}")
                    continue
                
        return subtotal - self.descuento_input.value()
    
    def _on_datos_cambiados(self):
        """Manejador cuando cambian datos que afectan el número de transacción."""
        # Actualizar previsualización cuando cambian datos relevantes
        self._previsualizar_numero_transaccion()
    
    def setup_transaccion_ui(self):
        """Configurar UI específica para transacción."""
        # Crear área de desplazamiento
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Widget contenedor del contenido
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # SECCIÓN 1: Información básica
        self.setup_info_basica_section(content_layout)
        
        # SECCIÓN 2: Detalles de la transacción 
        self.setup_detalles_section(content_layout)
        
        # SECCIÓN 3: Documentos adjuntos
        self.setup_documentos_section(content_layout)
        
        # SECCIÓN 4: Observaciones
        self.setup_observaciones_section(content_layout)
        
        # Configurar scroll area
        scroll_area.setWidget(content_widget)
        
        # Agregar al área de contenido principal
        self.content_layout.addWidget(scroll_area, 1)
        
        # Personalizar botones según modo
        self.btn_guardar.setText("💾 GUARDAR TRANSACCIÓN")
        self.btn_cancelar.setText("❌ CANCELAR")
        
        # Conectar señales específicas
        self.connect_signals_especificos()
        
        # Después de crear numero_transaccion_label, conectar señales
        self.fecha_pago_input.dateChanged.connect(self._on_datos_cambiados)
        
        # También conectar cuando cambia estudiante o programa
        if hasattr(self, 'btn_seleccionar_estudiante'):
            self.btn_seleccionar_estudiante.clicked.connect(
                lambda: QTimer.singleShot(100, self._on_datos_cambiados)
            )
        
        if hasattr(self, 'btn_seleccionar_programa'):
            self.btn_seleccionar_programa.clicked.connect(
                lambda: QTimer.singleShot(100, self._on_datos_cambiados)
            )
    
    # ▓▒░░▒▓ MÉTODOS DE CONFIGURACIÓN DE UI ▓▒░░▒▓
    
    def setup_info_basica_section(self, parent_layout):
        """
        Configurar sección de información básica.
        
        Args:
            parent_layout: Layout padre donde se agregará la sección
        """
        # Grupo de información básica
        info_group = QGroupBox("📋 Información de la Transacción")
        info_group.setObjectName("infoGroup")
        
        grid = QGridLayout(info_group)
        grid.setContentsMargins(15, 20, 15, 15)
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)
        
        # Fila 1: Número de transacción (generado automáticamente)
        grid.addWidget(QLabel("N° Transacción:"), 0, 0)
        self.numero_transaccion_label = QLabel("(Generado automáticamente)")
        self.numero_transaccion_label.setStyleSheet("font-weight: bold; color: #2c3e50;")
        grid.addWidget(self.numero_transaccion_label, 0, 1)
        
        # Agregar fila para tipo de operación (antes o después de fecha)
        grid.addWidget(QLabel("Tipo de operación*:"), 1, 0)  # Ajustar índices según posición
        self.tipo_operacion_combo = QComboBox()
        self.tipo_operacion_combo.addItem("Ingreso", "INGRESO")
        self.tipo_operacion_combo.addItem("Egreso", "EGRESO")
        self.tipo_operacion_combo.currentTextChanged.connect(self._on_datos_cambiados)
        grid.addWidget(self.tipo_operacion_combo, 1, 1)
        
        # Fila 2: Fecha de pago
        grid.addWidget(QLabel("Fecha de pago*:"), 1, 0)
        self.fecha_pago_input = QDateEdit()
        self.fecha_pago_input.setCalendarPopup(True)
        self.fecha_pago_input.setDate(QDate.currentDate())
        self.fecha_pago_input.setMaximumWidth(150)
        grid.addWidget(self.fecha_pago_input, 1, 1)
        
        # Fila 3: Estudiante (opcional)
        grid.addWidget(QLabel("Estudiante:"), 2, 0)
        estudiante_hbox = QHBoxLayout()
        
        # Inicializar el label sin texto fijo - se establecerá dinámicamente
        self.estudiante_label = QLabel()
        self.estudiante_label.setStyleSheet("color: #7f8c8d;")
        
        # Si ya hay un estudiante_id, mostrar información inmediatamente
        if self.estudiante_id:
            self.estudiante_label.setText("Cargando...")
        else:
            self.estudiante_label.setText("No seleccionado")
        
        self.btn_seleccionar_estudiante = QPushButton("👤 Seleccionar")
        self.btn_seleccionar_estudiante.setObjectName("btnSeleccionarEstudiante")
        self.btn_seleccionar_estudiante.setStyleSheet("""
            #btnSeleccionarEstudiante {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            #btnSeleccionarEstudiante:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_seleccionar_estudiante.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_seleccionar_estudiante.clicked.connect(self._seleccionar_estudiante)
        
        self.btn_detalle_estudiante = QPushButton("👁️ Ver")
        self.btn_detalle_estudiante.setObjectName("btnDetalleEstudiante")
        self.btn_detalle_estudiante.setStyleSheet("""
            #btnDetalleEstudiante {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            #btnDetalleEstudiante:hover {
                background-color: #8e44ad;
            }
            #btnDetalleEstudiante:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.btn_detalle_estudiante.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_detalle_estudiante.clicked.connect(self._mostrar_detalle_estudiante)
        self.btn_detalle_estudiante.setEnabled(False)
        
        self.btn_limpiar_estudiante = QPushButton("❌")
        self.btn_limpiar_estudiante.setObjectName("btnLimpiarEstudiante")
        self.btn_limpiar_estudiante.setStyleSheet("""
            #btnLimpiarEstudiante {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            #btnLimpiarEstudiante:hover {
                background-color: #c0392b;
            }
            #btnLimpiarEstudiante:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.btn_limpiar_estudiante.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_limpiar_estudiante.clicked.connect(self._limpiar_estudiante)
        self.btn_limpiar_estudiante.setVisible(False)
        
        estudiante_hbox.addWidget(self.estudiante_label, 1)
        estudiante_hbox.addWidget(self.btn_seleccionar_estudiante)
        estudiante_hbox.addWidget(self.btn_detalle_estudiante)
        estudiante_hbox.addWidget(self.btn_limpiar_estudiante)
        grid.addLayout(estudiante_hbox, 2, 1)
        
        # Fila 4: Programa (opcional)
        grid.addWidget(QLabel("Programa:"), 3, 0)
        programa_hbox = QHBoxLayout()
        self.programa_label = QLabel("No seleccionado")
        self.programa_label.setStyleSheet("color: #7f8c8d;")
        
        self.btn_seleccionar_programa = QPushButton("📚 Seleccionar")
        self.btn_seleccionar_programa.setObjectName("btnSeleccionarPrograma")
        self.btn_seleccionar_programa.setStyleSheet("""
            #btnSeleccionarPrograma {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            #btnSeleccionarPrograma:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_seleccionar_programa.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_seleccionar_programa.clicked.connect(self._seleccionar_programa)
        
        self.btn_detalle_programa = QPushButton("👁️ Ver")
        self.btn_detalle_programa.setObjectName("btnDetallePrograma")
        self.btn_detalle_programa.setStyleSheet("""
            #btnDetallePrograma {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            #btnDetallePrograma:hover {
                background-color: #8e44ad;
            }
            #btnDetallePrograma:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.btn_detalle_programa.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_detalle_programa.clicked.connect(self._mostrar_detalle_programa)
        self.btn_detalle_programa.setEnabled(False)
        
        self.btn_limpiar_programa = QPushButton("❌")
        self.btn_limpiar_programa.setObjectName("btnLimpiarPrograma")
        self.btn_limpiar_programa.setStyleSheet("""
            #btnLimpiarPrograma {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 6px 10px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            #btnLimpiarPrograma:hover {
                background-color: #c0392b;
            }
            #btnLimpiarPrograma:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        self.btn_limpiar_programa.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_limpiar_programa.clicked.connect(self._limpiar_programa)
        self.btn_limpiar_programa.setVisible(False)
        
        programa_hbox.addWidget(self.programa_label, 1)
        programa_hbox.addWidget(self.btn_seleccionar_programa)
        programa_hbox.addWidget(self.btn_detalle_programa)
        programa_hbox.addWidget(self.btn_limpiar_programa)
        grid.addLayout(programa_hbox, 3, 1)
        
        parent_layout.addWidget(info_group)
    
    def setup_detalles_section(self, parent_layout):
        """
        Configurar sección de detalles de la transacción.
        
        Incluye:
        - Forma de pago
        - Campos para transferencias
        - Número de comprobante
        - Estado
        - Tabla de conceptos de pago
        - Resumen de montos
        
        Args:
            parent_layout: Layout padre donde se agregará la sección
        """
        # Grupo de detalles
        detalles_group = QGroupBox("💵 Detalles del Pago")
        detalles_group.setObjectName("detallesGroup")
        
        main_layout = QVBoxLayout(detalles_group)
        main_layout.setContentsMargins(15, 20, 15, 15)
        main_layout.setSpacing(12)
        
        # SECCIÓN 1: Información de pago
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(10)
        
        # Fila 1: Forma de pago
        forma_pago_layout = QHBoxLayout()
        forma_pago_layout.addWidget(QLabel("Forma de pago*:"))
        self.forma_pago_combo = QComboBox()
        for forma in FormaPago:
            self.forma_pago_combo.addItem(forma.value, forma.name)
        self.forma_pago_combo.setCurrentText("EFECTIVO")
        self.forma_pago_combo.currentTextChanged.connect(self._on_forma_pago_changed)
        forma_pago_layout.addWidget(self.forma_pago_combo, 1)
        info_layout.addLayout(forma_pago_layout)
        
        # Campos para transferencias
        self.transferencia_container = QWidget()
        transferencia_layout = QVBoxLayout(self.transferencia_container)
        transferencia_layout.setContentsMargins(20, 10, 0, 10)
        transferencia_layout.setSpacing(8)
        
        # Banco origen
        banco_layout = QHBoxLayout()
        banco_layout.addWidget(QLabel("Banco origen:"))
        self.banco_origen_input = QLineEdit()
        self.banco_origen_input.setPlaceholderText("Ej: Banco Unión")
        banco_layout.addWidget(self.banco_origen_input, 1)
        transferencia_layout.addLayout(banco_layout)
        
        # Cuenta origen
        cuenta_layout = QHBoxLayout()
        cuenta_layout.addWidget(QLabel("Cuenta origen:"))
        self.cuenta_origen_input = QLineEdit()
        self.cuenta_origen_input.setPlaceholderText("Ej: 123456789")
        cuenta_layout.addWidget(self.cuenta_origen_input, 1)
        transferencia_layout.addLayout(cuenta_layout)
        
        self.transferencia_container.hide()
        info_layout.addWidget(self.transferencia_container)
        
        # Fila 2: Número de comprobante
        comprobante_layout = QHBoxLayout()
        comprobante_layout.addWidget(QLabel("N° Comprobante:"))
        self.numero_comprobante_input = QLabel("(Generado automáticamente)")
        comprobante_layout.addWidget(self.numero_comprobante_input, 1)
        info_layout.addLayout(comprobante_layout)
        
        # Fila 3: Estado
        estado_layout = QHBoxLayout()
        estado_layout.addWidget(QLabel("Estado*:"))
        self.estado_combo = QComboBox()
        for estado in EstadoTransaccion:
            self.estado_combo.addItem(estado.value, estado.name)
        self.estado_combo.setCurrentText("REGISTRADO")
        estado_layout.addWidget(self.estado_combo, 1)
        info_layout.addLayout(estado_layout)
        
        main_layout.addWidget(info_frame)
        
        # SECCIÓN 2: Detalles de conceptos
        conceptos_frame = QFrame()
        conceptos_frame.setFrameShape(QFrame.Shape.StyledPanel)
        conceptos_layout = QVBoxLayout(conceptos_frame)
        conceptos_layout.setContentsMargins(10, 10, 10, 10)
        conceptos_layout.setSpacing(10)
        
        # Encabezado
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("📋 Detalles de Conceptos"))
        header_layout.addStretch()
        
        self.btn_agregar_concepto = QPushButton("➕ Agregar Concepto")
        self.btn_agregar_concepto.setObjectName("btnAgregarConcepto")
        self.btn_agregar_concepto.setStyleSheet("""
            #btnAgregarConcepto {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                padding: 6px 12px;
                border-radius: 4px;
                border: none;
                font-size: 11px;
            }
            #btnAgregarConcepto:hover {
                background-color: #27ae60;
            }
        """)
        self.btn_agregar_concepto.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_agregar_concepto.clicked.connect(self._agregar_concepto)
        header_layout.addWidget(self.btn_agregar_concepto)
        
        conceptos_layout.addLayout(header_layout)
        
        # Tabla de detalles
        self.tabla_detalles = QTableWidget()
        self.tabla_detalles.setObjectName("tablaDetalles")
        self.tabla_detalles.setColumnCount(6)
        self.tabla_detalles.setHorizontalHeaderLabels([
            "Concepto", "Descripción", "Cantidad", "Precio Unitario", "Subtotal", ""
        ])
        self.tabla_detalles.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla_detalles.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.tabla_detalles.setColumnWidth(5, 40)
        self.tabla_detalles.setAlternatingRowColors(True)
        self.tabla_detalles.setMinimumHeight(150)
        
        conceptos_layout.addWidget(self.tabla_detalles)
        
        # Resumen de montos
        resumen_layout = QGridLayout()
        resumen_layout.setSpacing(10)
        
        # Subtotal
        resumen_layout.addWidget(QLabel("Subtotal:"), 0, 0)
        self.subtotal_label = QLabel("$0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        resumen_layout.addWidget(self.subtotal_label, 0, 1)
        
        # Descuento
        resumen_layout.addWidget(QLabel("Descuento:"), 1, 0)
        descuento_hbox = QHBoxLayout()
        self.descuento_input = QDoubleSpinBox()
        self.descuento_input.setRange(0, 1000000)
        self.descuento_input.setValue(0.00)
        self.descuento_input.setPrefix("$ ")
        self.descuento_input.setDecimals(2)
        self.descuento_input.setMaximumWidth(120)
        self.descuento_input.valueChanged.connect(self._actualizar_totales)
        descuento_hbox.addWidget(self.descuento_input)
        descuento_hbox.addStretch()
        resumen_layout.addLayout(descuento_hbox, 1, 1)
        
        # Total final
        resumen_layout.addWidget(QLabel("Total a pagar:"), 2, 0)
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-weight: bold; color: #27ae60; font-size: 16px;")
        resumen_layout.addWidget(self.total_label, 2, 1)
        
        conceptos_layout.addLayout(resumen_layout)
        
        main_layout.addWidget(conceptos_frame)
        
        parent_layout.addWidget(detalles_group)
    
    def setup_documentos_section(self, parent_layout):
        """
        Configurar sección de documentos adjuntos.
        
        Args:
            parent_layout: Layout padre donde se agregará la sección
        """
        # Grupo de documentos
        documentos_group = QGroupBox("📎 Documentos Adjuntos")
        documentos_group.setObjectName("documentosGroup")
        
        layout = QVBoxLayout(documentos_group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(12)
        
        # Lista de documentos
        self.lista_documentos = QListWidget()
        self.lista_documentos.setObjectName("listaDocumentos")
        self.lista_documentos.setMaximumHeight(150)
        self.lista_documentos.setAlternatingRowColors(True)
        
        # Botones para documentos
        documentos_buttons = QHBoxLayout()
        
        self.btn_agregar_documento = QPushButton("📁 Agregar Documento")
        self.btn_agregar_documento.setObjectName("btnAgregarDocumento")
        self.btn_agregar_documento.setStyleSheet("""
            #btnAgregarDocumento {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            #btnAgregarDocumento:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_agregar_documento.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_agregar_documento.clicked.connect(self._agregar_documento)
        
        self.btn_eliminar_documento = QPushButton("🗑️ Eliminar Seleccionado")
        self.btn_eliminar_documento.setObjectName("btnEliminarDocumento")
        self.btn_eliminar_documento.setStyleSheet("""
            #btnEliminarDocumento {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
                border: none;
            }
            #btnEliminarDocumento:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_eliminar_documento.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_eliminar_documento.clicked.connect(self._eliminar_documento_seleccionado)
        
        documentos_buttons.addWidget(self.btn_agregar_documento)
        documentos_buttons.addWidget(self.btn_eliminar_documento)
        documentos_buttons.addStretch()
        
        layout.addWidget(self.lista_documentos)
        layout.addLayout(documentos_buttons)
        
        parent_layout.addWidget(documentos_group)
    
    def setup_observaciones_section(self, parent_layout):
        """
        Configurar sección de observaciones.
        
        Args:
            parent_layout: Layout padre donde se agregará la sección
        """
        # Grupo de observaciones
        observaciones_group = QGroupBox("📝 Observaciones")
        observaciones_group.setObjectName("observacionesGroup")
        
        layout = QVBoxLayout(observaciones_group)
        layout.setContentsMargins(15, 20, 15, 15)
        layout.setSpacing(12)
        
        # Texto para observaciones
        self.observaciones_input = QTextEdit()
        self.observaciones_input.setPlaceholderText("Ingrese observaciones sobre la transacción...")
        self.observaciones_input.setMaximumHeight(100)
        
        layout.addWidget(self.observaciones_input)
        
        parent_layout.addWidget(observaciones_group)
    
    def connect_signals_especificos(self):
        """Conectar señales específicas de la transacción."""
        # Las señales de los widgets específicos se conectan en sus respectivos métodos
    
    # ▓▒░░▒▓ MÉTODOS DE CARGA DE DATOS ▓▒░░▒▓
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo",
                estudiante_id=None, programa_id=None, inscripcion_id=None):
        """
        Mostrar el overlay con configuración específica.
        
        Args:
            solo_lectura: Si es True, el formulario será de solo lectura
            datos: Datos de la transacción a cargar (para edición)
            modo: Modo de operación ("nuevo", "editar", "visualizar")
            estudiante_id: ID del estudiante asociado
            programa_id: ID del programa asociado
            inscripcion_id: ID de la inscripción asociada
        """
        self.solo_lectura = solo_lectura
        self.set_modo(modo)
        
        # Reiniciar bandera de título
        self._titulo_actualizado = False
        
        # Limpiar caches
        self._estudiante_cache = None
        self._programa_cache = None
        
        # Establecer IDs si se proporcionan
        if estudiante_id:
            self.estudiante_id = estudiante_id
            self._cargar_estudiante(force=True)
        if programa_id:
            self.programa_id = programa_id
            self._cargar_programa(force=True)
            
        # Si hay inscripción_id, obtener estudiante y programa
        if inscripcion_id:
            self.inscripcion_id = inscripcion_id
            # Usar un timer para cargar después de que la UI esté lista
            QTimer.singleShot(100, self._cargar_datos_inscripcion_diferido)
        elif datos:
            self.cargar_datos(datos)
        elif modo == "nuevo":
            self.clear_form()
            
        # Configurar botón de guardar según el modo
        if hasattr(self, 'btn_guardar'):
            if modo == "nuevo":
                self.btn_guardar.setText("💾 GUARDAR TRANSACCIÓN")
            elif modo == "editar":
                self.btn_guardar.setText("💾 ACTUALIZAR TRANSACCIÓN")
                
        # Configurar visibilidad de controles según modo
        self._configurar_controles_modo(modo)
        
        # Cargar documentos si ya hay transacción
        if self.transaccion_id:
            self._cargar_documentos()
            
        # Llamar al método base
        super().show_form(solo_lectura)
    
    def _cargar_datos_inscripcion_diferido(self):
        """Cargar datos de inscripción con un pequeño retraso para asegurar que la UI esté lista."""
        if self.inscripcion_id:
            self._cargar_datos_inscripcion()
    
    def cargar_datos(self, datos):
        """
        Cargar datos de transacción existente.
        
        Args:
            datos: Diccionario con datos de la transacción
        """
        self.transaccion_id = datos.get('id')
        
        # Número de transacción
        if 'numero_transaccion' in datos and datos['numero_transaccion']:
            self.numero_transaccion_label.setText(datos['numero_transaccion'])
        
        # Fecha de pago
        if 'fecha_pago' in datos and datos['fecha_pago']:
            fecha = QDate.fromString(str(datos['fecha_pago']), "yyyy-MM-dd")
            if fecha.isValid():
                self.fecha_pago_input.setDate(fecha)
        
        # Estudiante y programa
        if 'estudiante_id' in datos and datos['estudiante_id']:
            self.estudiante_id = datos['estudiante_id']
            self._cargar_estudiante()
        
        if 'programa_id' in datos and datos['programa_id']:
            self.programa_id = datos['programa_id']
            self._cargar_programa()
        
        # Detalles del pago
        if 'forma_pago' in datos and datos['forma_pago']:
            index = self.forma_pago_combo.findText(datos['forma_pago'])
            if index >= 0:
                self.forma_pago_combo.setCurrentIndex(index)
        
        if 'numero_comprobante' in datos and datos['numero_comprobante']:
            self.numero_comprobante_input.setText(datos['numero_comprobante'])
        
        if 'banco_origen' in datos and datos['banco_origen']:
            self.banco_origen_input.setText(datos['banco_origen'])
        
        if 'cuenta_origen' in datos and datos['cuenta_origen']:
            self.cuenta_origen_input.setText(datos['cuenta_origen'])
        
        # Estado
        if 'estado' in datos and datos['estado']:
            index = self.estado_combo.findText(datos['estado'])
            if index >= 0:
                self.estado_combo.setCurrentIndex(index)
        
        # Observaciones
        if 'observaciones' in datos and datos['observaciones']:
            self.observaciones_input.setPlainText(datos['observaciones'])
            
        # Cargar detalles si existen
        if 'detalles' in datos and datos['detalles']:
            self._cargar_detalles_tabla(datos['detalles'])
            
        # Actualizar totales
        self._actualizar_totales()
    
    def _cargar_detalles_tabla(self, detalles):
        """
        Cargar detalles en la tabla.
        
        Args:
            detalles: Lista de diccionarios con detalles de la transacción
        """
        try:
            # Limpiar tabla
            self.tabla_detalles.setRowCount(0)
            
            for detalle in detalles:
                self._agregar_detalle_a_tabla(detalle)
                
        except Exception as e:
            logger.error(f"Error cargando detalles en tabla: {e}")
    
    def _agregar_detalle_a_tabla(self, detalle):
        """
        Agregar un detalle a la tabla.
        
        Args:
            detalle: Diccionario con datos del detalle
        """
        try:
            row_position = self.tabla_detalles.rowCount()
            self.tabla_detalles.insertRow(row_position)
            
            # Obtener concepto
            concepto_id = detalle.get('concepto_pago_id')
            concepto_nombre = detalle.get('concepto_nombre', '')
            monto_base = detalle.get('precio_unitario', 0)
            
            # Combo para seleccionar concepto
            combo_concepto = QComboBox()
            combo_concepto.addItem("Seleccionar...", None)
            
            # Cargar conceptos disponibles
            conceptos = ConceptoPagoModel.obtener_conceptos_activos()
            selected_index = 0
            for i, concepto in enumerate(conceptos, start=1):
                descripcion = f"{concepto.get('nombre')} - ${concepto.get('monto_base', 0):.2f}"
                combo_concepto.addItem(descripcion, concepto.get('id'))
                
                if concepto.get('id') == concepto_id:
                    selected_index = i
            
            combo_concepto.setCurrentIndex(selected_index)
            combo_concepto.currentIndexChanged.connect(lambda idx, r=row_position: self._on_concepto_seleccionado(r))
            
            # Descripción
            desc_input = QLineEdit()
            desc_input.setText(detalle.get('descripcion', ''))
            
            # Cantidad
            cant_spin = QDoubleSpinBox()
            cant_spin.setRange(1, 100)
            cant_spin.setValue(detalle.get('cantidad', 1))
            cant_spin.setDecimals(0)
            cant_spin.valueChanged.connect(self._actualizar_totales)
            
            # Precio unitario
            precio_spin = QDoubleSpinBox()
            precio_spin.setRange(0, 100000)
            precio_spin.setValue(float(detalle.get('precio_unitario', 0)))
            precio_spin.setPrefix("$ ")
            precio_spin.setDecimals(2)
            precio_spin.valueChanged.connect(self._actualizar_totales)
            
            # Subtotal
            subtotal = detalle.get('cantidad', 1) * float(detalle.get('precio_unitario', 0))
            subtotal_label = QLabel(f"${subtotal:,.2f}")
            subtotal_label.setStyleSheet("font-weight: bold;")
            
            # Botón eliminar
            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setObjectName("btnEliminarConcepto")
            btn_eliminar.setStyleSheet("""
                #btnEliminarConcepto {
                    background-color: #e74c3c;
                    color: white;
                    font-weight: bold;
                    padding: 2px 8px;
                    border-radius: 3px;
                    border: none;
                    font-size: 10px;
                }
                #btnEliminarConcepto:hover {
                    background-color: #c0392b;
                }
            """)
            btn_eliminar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_eliminar.clicked.connect(lambda _, r=row_position: self._eliminar_concepto(r))
            
            # Agregar widgets a la tabla
            self.tabla_detalles.setCellWidget(row_position, 0, combo_concepto)
            self.tabla_detalles.setCellWidget(row_position, 1, desc_input)
            self.tabla_detalles.setCellWidget(row_position, 2, cant_spin)
            self.tabla_detalles.setCellWidget(row_position, 3, precio_spin)
            self.tabla_detalles.setCellWidget(row_position, 4, subtotal_label)
            self.tabla_detalles.setCellWidget(row_position, 5, btn_eliminar)
            
        except Exception as e:
            logger.error(f"Error agregando detalle a tabla: {e}")
    
    def _cargar_estudiante(self, force=False):
        """
        Cargar información del estudiante.
        
        Args:
            force: Si es True, forzar recarga ignorando cache
        """
        if not self.estudiante_id:
            if hasattr(self, 'estudiante_label'):
                self.estudiante_label.setText("No seleccionado")
            if hasattr(self, 'btn_limpiar_estudiante'):
                self.btn_limpiar_estudiante.setVisible(False)
            if hasattr(self, 'btn_detalle_estudiante'):
                self.btn_detalle_estudiante.setEnabled(False)
            return
        
        try:
            # Mostrar estado de carga
            if hasattr(self, 'estudiante_label'):
                self.estudiante_label.setText("Cargando...")
                self.estudiante_label.repaint()
            
            # Usar cache si existe y no se fuerza recarga
            if self._estudiante_cache and not force:
                estudiante = self._estudiante_cache
            else:
                resultado = EstudianteModel.obtener_estudiante_por_id(self.estudiante_id)
                logger.debug(f"Resultado estudiante: {resultado}")
                
                # Verificar el tipo de respuesta
                if isinstance(resultado, dict):
                    # La respuesta ya es un diccionario con los datos del estudiante
                    # No necesita envolverse en estructura {'success': True, 'data': ...}
                    if 'id' in resultado:
                        estudiante = resultado
                        self._estudiante_cache = estudiante  # Cachear
                    else:
                        # Podría ser una respuesta con estructura de error
                        error_msg = resultado.get('mensaje', 'Error desconocido') if resultado else 'Sin respuesta'
                        logger.error(f"Error cargando estudiante: {error_msg}")
                        if hasattr(self, 'estudiante_label'):
                            self.estudiante_label.setText(f"Error: {error_msg[:50]}")
                        if hasattr(self, 'btn_limpiar_estudiante'):
                            self.btn_limpiar_estudiante.setVisible(False)
                        if hasattr(self, 'btn_detalle_estudiante'):
                            self.btn_detalle_estudiante.setEnabled(False)
                        return
                else:
                    # Respuesta inesperada
                    logger.error(f"Respuesta inesperada de obtener_estudiante_por_id: {type(resultado)}")
                    if hasattr(self, 'estudiante_label'):
                        self.estudiante_label.setText("Error de datos")
                    if hasattr(self, 'btn_limpiar_estudiante'):
                        self.btn_limpiar_estudiante.setVisible(False)
                    if hasattr(self, 'btn_detalle_estudiante'):
                        self.btn_detalle_estudiante.setEnabled(False)
                    return
        
        except Exception as e:
            logger.error(f"Error cargando estudiante: {e}")
            if hasattr(self, 'estudiante_label'):
                self.estudiante_label.setText(f"Error: {str(e)[:50]}")
            if hasattr(self, 'btn_limpiar_estudiante'):
                self.btn_limpiar_estudiante.setVisible(False)
            if hasattr(self, 'btn_detalle_estudiante'):
                self.btn_detalle_estudiante.setEnabled(False)
            return
        
        # Procesar los datos del estudiante
        if estudiante and isinstance(estudiante, dict):
            try:
                # Formatear nombre completo
                nombre_completo = ""
                if 'nombres_completos' in estudiante:
                    nombre_completo = estudiante['nombres_completos']
                else:
                    # Construir nombre a partir de campos individuales
                    nombres = estudiante.get('nombres', '')
                    apellido_paterno = estudiante.get('apellido_paterno', '')
                    apellido_materno = estudiante.get('apellido_materno', '')
                    
                    nombre_completo = f"{nombres} {apellido_paterno}".strip()
                    if apellido_materno:
                        nombre_completo += f" {apellido_materno}"
                
                # Formatear CI
                ci_completo = ""
                if 'ci_completo' in estudiante:
                    ci_completo = estudiante['ci_completo']
                else:
                    ci_numero = estudiante.get('ci_numero', '')
                    ci_expedicion = estudiante.get('ci_expedicion', '')
                    if ci_numero and ci_expedicion:
                        ci_completo = f"{ci_numero}-{ci_expedicion}"
                    elif ci_numero:
                        ci_completo = ci_numero
                    else:
                        ci_completo = "Sin CI"
                
                # Actualizar label
                texto_estudiante = ""
                if nombre_completo and ci_completo:
                    texto_estudiante = f"{nombre_completo} ({ci_completo})"
                elif nombre_completo:
                    texto_estudiante = nombre_completo
                else:
                    texto_estudiante = f"Estudiante ID: {self.estudiante_id}"
                
                if hasattr(self, 'estudiante_label'):
                    self.estudiante_label.setText(texto_estudiante)
                
                # Actualizar botones
                if hasattr(self, 'btn_limpiar_estudiante'):
                    self.btn_limpiar_estudiante.setVisible(True)
                if hasattr(self, 'btn_detalle_estudiante'):
                    self.btn_detalle_estudiante.setEnabled(True)
                
                # Forzar actualización de la UI
                if hasattr(self, 'estudiante_label'):
                    self.estudiante_label.repaint()
                
                logger.debug(f"Estudiante cargado: {texto_estudiante}")
                
            except Exception as e:
                logger.error(f"Error procesando datos del estudiante: {e}")
                if hasattr(self, 'estudiante_label'):
                    self.estudiante_label.setText(f"Error procesando datos")
                if hasattr(self, 'btn_limpiar_estudiante'):
                    self.btn_limpiar_estudiante.setVisible(False)
                if hasattr(self, 'btn_detalle_estudiante'):
                    self.btn_detalle_estudiante.setEnabled(False)
    
    def _cargar_programa(self, force=False):
        """
        Cargar información del programa.
        
        Args:
            force: Si es True, forzar recarga ignorando cache
        """
        if not self.programa_id:
            return
        
        try:
            # Usar cache si existe y no se fuerza recarga
            if self._programa_cache and not force:
                programa = self._programa_cache
            else:
                resultado = ProgramaModel.obtener_programa(self.programa_id)
                logger.debug(f"Resultado programa: {resultado}")
                
                if resultado and 'success' in resultado and resultado['success']:
                    programa = resultado.get('data', {})
                    self._programa_cache = programa  # Cachear
                else:
                    logger.error(f"Error en respuesta de programa: {resultado}")
                    self.programa_label.setText(f"Error cargando programa ID: {self.programa_id}")
                    self.btn_limpiar_programa.setVisible(False)
                    self.btn_detalle_programa.setEnabled(False)
                    return
        except Exception as e:
            logger.error(f"Error cargando programa: {e}")
            self.programa_label.setText(f"Error: {str(e)[:50]}...")
            self.btn_limpiar_programa.setVisible(False)
            self.btn_detalle_programa.setEnabled(False)
            return
        
        if programa:
            # Formatear información del programa
            codigo = programa.get('codigo', 'N/A')
            nombre = programa.get('nombre', 'Programa no encontrado')
            costo_total = programa.get('costo_total', 0)
            
            # Actualizar label inmediatamente
            texto_programa = f"{codigo} - {nombre}"
            if costo_total > 0:
                texto_programa += f" (Costo total: ${costo_total:,.2f})"
                
            self.programa_label.setText(texto_programa)
            
            # Actualizar botones
            self.btn_limpiar_programa.setVisible(True)
            self.btn_detalle_programa.setEnabled(True)
            
            # Forzar actualización de la UI
            self.programa_label.repaint()
            
            # Actualizar título del overlay si no se hizo desde inscripción
            if not hasattr(self, '_titulo_actualizado') or not self._titulo_actualizado:
                self._actualizar_titulo_con_programa(programa)
                
            logger.debug(f"Programa cargado: {texto_programa}")
    
    def _actualizar_titulo_con_programa(self, programa):
        """
        Actualizar título del overlay con información del programa.
        
        Args:
            programa: Diccionario con datos del programa
        """
        try:
            if programa:
                codigo = programa.get('codigo', '')
                nombre = programa.get('nombre', '')
                
                # Obtener título actual
                current_title = self.windowTitle()
                
                # Agregar información del programa si no está ya incluida
                if codigo and codigo not in current_title:
                    programa_info = f" - Programa: {codigo}"
                    self.setWindowTitle(current_title + programa_info)
                    
                # Marcar como actualizado
                self._titulo_actualizado = True
                
        except Exception as e:
            logger.error(f"Error actualizando título: {e}")
    
    def _sugerir_monto_programa(self):
        """Sugerir monto basado en el programa."""
        if not self.programa_id:
            return
        
        try:
            resultado = ProgramaModel.obtener_programa(self.programa_id)
            
            if resultado and 'success' in resultado and resultado['success']:
                programa = resultado.get('data', {})
                
                # Sugerir monto basado en diferentes criterios
                sugerencia = 0
                
                # 1. Primero intentar con mensualidad
                costo_mensualidad = programa.get('costo_mensualidad', 0)
                if costo_mensualidad > 0:
                    sugerencia = float(costo_mensualidad)
                    
                # 2. Si no hay mensualidad, usar costo total
                elif sugerencia == 0:
                    costo_total = programa.get('costo_total', 0)
                    if costo_total > 0:
                        sugerencia = float(costo_total)
                        
                # 3. Si hay matrícula o inscripción, usar eso
                if sugerencia == 0:
                    costo_matricula = programa.get('costo_matricula', 0)
                    if costo_matricula > 0:
                        sugerencia = float(costo_matricula)
                    else:
                        costo_inscripcion = programa.get('costo_inscripcion', 0)
                        if costo_inscripcion > 0:
                            sugerencia = float(costo_inscripcion)
                            
                # Aplicar sugerencia si existe
                if sugerencia > 0:
                    # Buscar si ya hay conceptos en la tabla
                    if self.tabla_detalles.rowCount() == 0:
                        # Si no hay conceptos, agregar uno por defecto
                        self._agregar_conceptos_por_defecto()
                    else:
                        # Actualizar el precio del primer concepto
                        for row in range(self.tabla_detalles.rowCount()):
                            widget = self.tabla_detalles.cellWidget(row, 3)
                            # Verificar explícitamente si es un QDoubleSpinBox
                            if widget and isinstance(widget, QDoubleSpinBox):
                                try:
                                    widget.setValue(sugerencia)
                                    break
                                except Exception:
                                    # Si falla, continuar con el siguiente
                                    continue
                                
                    self._actualizar_totales()
                    
                    # Mostrar mensaje informativo
                    self.mostrar_mensaje(
                        "Sugerencia de monto",
                        f"Se ha sugerido un monto de ${sugerencia:,.2f} basado en el programa",
                        "info"
                    )
                    
        except Exception as e:
            logger.error(f"Error sugiriendo monto: {e}")
    
    def _cargar_datos_inscripcion(self):
        """Cargar datos de la inscripción."""
        if not self.inscripcion_id:
            return
        
        try:
            from model.inscripcion_model import InscripcionModel
            resultado = InscripcionModel.obtener_detalle_inscripcion(self.inscripcion_id)
            
            # Verificar estructura de respuesta
            logger.debug(f"Datos inscripción recibidos: {resultado}")
            
            if resultado and 'success' in resultado and resultado['success']:
                data = resultado.get('data', {})
                
                # Obtener datos del estudiante
                estudiante_data = data.get('estudiante', {})
                if estudiante_data and 'id' in estudiante_data:
                    self.estudiante_id = estudiante_data['id']
                    
                    # Actualizar cache con datos obtenidos
                    self._estudiante_cache = estudiante_data
                    
                    # Cargar estudiante inmediatamente (force=True para asegurar actualización)
                    self._cargar_estudiante(force=True)
                    
                    # Actualizar título del overlay con información del estudiante
                    if 'nombres_completos' in estudiante_data:
                        self.setWindowTitle(f"Nueva Transacción - {estudiante_data['nombres_completos']}")
                        
                # Obtener datos del programa
                programa_data = data.get('programa', {})
                if programa_data and 'id' in programa_data:
                    self.programa_id = programa_data['id']
                    
                    # Actualizar cache con datos obtenidos
                    self._programa_cache = programa_data
                    
                    # Cargar programa inmediatamente (force=True para asegurar actualización)
                    self._cargar_programa(force=True)
                    
                    # Actualizar título con saldo pendiente si existe
                    saldo = data.get('saldo', 0)
                    if saldo > 0:
                        current_title = self.windowTitle()
                        self.setWindowTitle(f"{current_title} (Saldo pendiente: {saldo:,.2f} Bs.)")
                        
                # Obtener datos de la inscripción
                inscripcion_data = data.get('inscripcion', {})
                if inscripcion_data:
                    # Aquí podrías usar otros datos de la inscripción si es necesario
                    pass
                
                # Agregar conceptos por defecto basados en el programa
                if self.programa_id:
                    # Usar un pequeño retraso para asegurar que la UI esté lista
                    QTimer.singleShot(200, self._agregar_conceptos_por_defecto)
                    
                # Sugerir monto basado en el programa
                QTimer.singleShot(300, self._sugerir_monto_programa)
                
            else:
                logger.error(f"Error en respuesta de inscripción: {resultado}")
                self.mostrar_mensaje(
                    "Error",
                    "No se pudieron cargar los datos de la inscripción",
                    "error"
                )
                
        except Exception as e:
            logger.error(f"Error cargando datos de inscripción: {e}")
            self.mostrar_mensaje(
                "Error",
                f"No se pudieron cargar los datos: {str(e)}",
                "error"
            )
    
    def _agregar_conceptos_por_defecto(self):
        """Agregar conceptos por defecto basados en el programa."""
        if not self.programa_id:
            return
        
        try:
            from model.programa_model import ProgramaModel
            resultado = ProgramaModel.obtener_programa(self.programa_id)
            
            if resultado and 'success' in resultado and resultado['success']:
                programa = resultado['data']
                
                # Agregar concepto de inscripción si aplica
                costo_inscripcion = programa.get('costo_inscripcion', 0)
                if costo_inscripcion > 0:
                    # Buscar concepto de inscripción
                    conceptos = ConceptoPagoModel.obtener_conceptos_activos()
                    concepto_inscripcion = None
                    for concepto in conceptos:
                        if concepto.get('tipo_concepto') == 'INSCRIPCION':
                            concepto_inscripcion = concepto
                            break
                    
                    if concepto_inscripcion:
                        self._agregar_concepto_fijo(concepto_inscripcion, "Inscripción al programa")
                
                # Agregar concepto de matrícula si aplica
                costo_matricula = programa.get('costo_matricula', 0)
                if costo_matricula > 0:
                    conceptos = ConceptoPagoModel.obtener_conceptos_activos()
                    concepto_matricula = None
                    for concepto in conceptos:
                        if concepto.get('tipo_concepto') == 'MATRICULA':
                            concepto_matricula = concepto
                            break
                    
                    if concepto_matricula:
                        self._agregar_concepto_fijo(concepto_matricula, "Matrícula del programa")
                        
        except Exception as e:
            logger.error(f"Error agregando conceptos por defecto: {e}")
    
    def _agregar_concepto_fijo(self, concepto_data, descripcion=""):
        """
        Agregar un concepto fijo a la tabla.
        
        Args:
            concepto_data: Diccionario con datos del concepto
            descripcion: Descripción personalizada (opcional)
        """
        try:
            row_position = self.tabla_detalles.rowCount()
            self.tabla_detalles.insertRow(row_position)
            
            # Combo para seleccionar concepto
            combo_concepto = QComboBox()
            combo_concepto.addItem(f"{concepto_data.get('nombre')} - ${concepto_data.get('monto_base', 0):.2f}", 
                                    concepto_data.get('id'))
            
            # Descripción
            desc_input = QLineEdit()
            desc_input.setText(descripcion or concepto_data.get('descripcion', ''))
            
            # Cantidad
            cant_spin = QDoubleSpinBox()
            cant_spin.setRange(1, 100)
            cant_spin.setValue(1)
            cant_spin.setDecimals(0)
            cant_spin.valueChanged.connect(self._actualizar_totales)
            
            # Precio unitario
            precio_spin = QDoubleSpinBox()
            precio_spin.setRange(0, 100000)
            precio_spin.setValue(float(concepto_data.get('monto_base', 0)))
            precio_spin.setPrefix("$ ")
            precio_spin.setDecimals(2)
            precio_spin.valueChanged.connect(self._actualizar_totales)
            
            # Subtotal
            subtotal = 1 * float(concepto_data.get('monto_base', 0))
            subtotal_label = QLabel(f"${subtotal:,.2f}")
            subtotal_label.setStyleSheet("font-weight: bold;")
            
            # Botón eliminar
            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setObjectName("btnEliminarConcepto")
            btn_eliminar.setStyleSheet("""
                #btnEliminarConcepto {
                    background-color: #e74c3c;
                    color: white;
                    font-weight: bold;
                    padding: 2px 8px;
                    border-radius: 3px;
                    border: none;
                    font-size: 10px;
                }
                #btnEliminarConcepto:hover {
                    background-color: #c0392b;
                }
            """)
            btn_eliminar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_eliminar.clicked.connect(lambda _, r=row_position: self._eliminar_concepto(r))
            
            # Agregar widgets a la tabla
            self.tabla_detalles.setCellWidget(row_position, 0, combo_concepto)
            self.tabla_detalles.setCellWidget(row_position, 1, desc_input)
            self.tabla_detalles.setCellWidget(row_position, 2, cant_spin)
            self.tabla_detalles.setCellWidget(row_position, 3, precio_spin)
            self.tabla_detalles.setCellWidget(row_position, 4, subtotal_label)
            self.tabla_detalles.setCellWidget(row_position, 5, btn_eliminar)
            
            # Actualizar totales
            self._actualizar_totales()
            
        except Exception as e:
            logger.error(f"Error agregando concepto fijo: {e}")
    
    def _cargar_documentos(self):
        """Cargar documentos adjuntos de la transacción."""
        if not self.transaccion_id:
            return
        
        try:
            documentos = TransaccionModel.obtener_documentos_respaldo(self.transaccion_id)
            self.lista_documentos.clear()
            self.documentos_adjuntos = documentos
            
            for doc in documentos:
                nombre = doc.get('nombre_original', 'Documento')
                tamaño = doc.get('tamano_bytes', 0)
                
                if tamaño > 0:
                    if tamaño < 1024:
                        tamaño_str = f"{tamaño} bytes"
                    elif tamaño < 1024 * 1024:
                        tamaño_str = f"{tamaño/1024:.1f} KB"
                    else:
                        tamaño_str = f"{tamaño/(1024*1024):.1f} MB"
                    
                    nombre = f"{nombre} ({tamaño_str})"
                
                item = QListWidgetItem(nombre)
                item.setData(Qt.ItemDataRole.UserRole, doc)
                self.lista_documentos.addItem(item)
                
        except Exception as e:
            logger.error(f"Error cargando documentos: {e}")
    
    # ▓▒░░▒▓ MÉTODOS DE VALIDACIÓN ▓▒░░▒▓
    
    def validar_formulario(self):
        """
        Validar todos los campos del formulario.
        
        Returns:
            Tuple (bool, list): (True si es válido, lista de errores)
        """
        errores = []
        
        # Validar fecha de pago
        fecha_pago = self.fecha_pago_input.date()
        if not fecha_pago.isValid():
            errores.append("La fecha de pago no es válida")
        
        # Validar que haya al menos un detalle
        detalles = self._obtener_detalles_transaccion()
        if not detalles:
            errores.append("Debe agregar al menos un concepto de pago")
        
        # Validar totales
        subtotal = 0.0
        for detalle in detalles:
            if detalle['subtotal'] <= 0:
                errores.append(f"El subtotal del concepto '{detalle['descripcion']}' debe ser mayor a 0")
            subtotal += detalle['subtotal']
        
        descuento = self.descuento_input.value()
        if descuento < 0:
            errores.append("El descuento no puede ser negativo")
        
        total = subtotal - descuento
        if total <= 0:
            errores.append("El monto final debe ser mayor a 0")
        
        # Validar forma de pago
        forma_pago = self.forma_pago_combo.currentText()
        if not forma_pago:
            errores.append("Debe seleccionar una forma de pago")
        
        # Si es transferencia, validar banco y cuenta
        if forma_pago in ["TRANSFERENCIA", "DEPOSITO"]:
            banco = self.banco_origen_input.text().strip()
            cuenta = self.cuenta_origen_input.text().strip()
            
            if not banco:
                errores.append("Debe especificar el banco de origen para transferencias")
            if not cuenta:
                errores.append("Debe especificar la cuenta de origen para transferencias")
        
        return len(errores) == 0, errores
    
    def obtener_datos(self):
        """
        Obtener todos los datos del formulario.
        
        Returns:
            Dict: Diccionario con todos los datos del formulario
        """
        # Obtener detalles de la tabla
        detalles = self._obtener_detalles_transaccion()
        
        # Calcular totales
        subtotal = sum(det['subtotal'] for det in detalles)
        descuento = self.descuento_input.value()
        total = subtotal - descuento
        
        datos = {
            'fecha_pago': self.fecha_pago_input.date().toString("yyyy-MM-dd"),
            'forma_pago': self.forma_pago_combo.currentText(),
            'monto_total': subtotal,
            'descuento_total': descuento,
            'monto_final': total,
            'estado': self.estado_combo.currentText(),
            'numero_comprobante': self.numero_comprobante_input.text().strip() or None,
            'observaciones': self.observaciones_input.toPlainText().strip(),
            'detalles': detalles,
            'modo': self.modo
        }
        
        # Agregar estudiante y programa si existen
        if self.estudiante_id:
            datos['estudiante_id'] = self.estudiante_id
        
        if self.programa_id:
            datos['programa_id'] = self.programa_id
        
        # Agregar datos de transferencia si corresponde
        forma_pago = self.forma_pago_combo.currentText()
        if forma_pago in ["TRANSFERENCIA", "DEPOSITO"]:
            datos['banco_origen'] = self.banco_origen_input.text().strip()
            datos['cuenta_origen'] = self.cuenta_origen_input.text().strip()
        
        # Agregar ID si existe
        if self.transaccion_id:
            datos['id'] = self.transaccion_id
        
        # Agregar documentos temporales
        if self.documentos_temp:
            datos['documentos_temp'] = self.documentos_temp
        
        return datos
    
    def _obtener_detalles_transaccion(self):
        """
        Obtener detalles de la transacción desde la tabla.
        
        Returns:
            List: Lista de diccionarios con detalles de la transacción
        """
        detalles = []
        
        for row in range(self.tabla_detalles.rowCount()):
            # Obtener widgets con verificación de tipos
            widget_combo = self.tabla_detalles.cellWidget(row, 0)
            widget_desc = self.tabla_detalles.cellWidget(row, 1)
            widget_cant = self.tabla_detalles.cellWidget(row, 2)
            widget_precio = self.tabla_detalles.cellWidget(row, 3)
            
            # Verificar que todos los widgets existen
            if not all([widget_combo, widget_desc, widget_cant, widget_precio]):
                continue
            
            # Verificar tipos específicos
            if (isinstance(widget_combo, QComboBox) and 
                isinstance(widget_desc, QLineEdit) and
                isinstance(widget_cant, QDoubleSpinBox) and
                isinstance(widget_precio, QDoubleSpinBox)):
                
                # Ahora podemos acceder a los métodos específicos
                concepto_id = widget_combo.currentData()
                if concepto_id:
                    try:
                        detalle = {
                            'concepto_pago_id': concepto_id,
                            'descripcion': widget_desc.text().strip(),
                            'cantidad': int(widget_cant.value()),
                            'precio_unitario': float(widget_precio.value()),
                            'subtotal': float(widget_cant.value() * widget_precio.value()),
                            'orden': row + 1
                        }
                        detalles.append(detalle)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error procesando fila {row}: {e}")
                        continue
                    
        return detalles
    
    def clear_form(self):
        """Limpiar todos los campos del formulario."""
        self.transaccion_id = None
        self.estudiante_id = None
        self.programa_id = None
        self.inscripcion_id = None
        self.detalles_transaccion = []
        self.documentos_adjuntos = []
        self.documentos_temp = []
        
        # Limpiar caches
        self._estudiante_cache = None
        self._programa_cache = None
        self._titulo_actualizado = False
        
        self.numero_transaccion_label.setText("(Generado automáticamente)")
        self.fecha_pago_input.setDate(QDate.currentDate())
        
        # Actualizar labels inmediatamente
        self.estudiante_label.setText("No seleccionado")
        self.btn_limpiar_estudiante.setVisible(False)
        
        self.programa_label.setText("No seleccionado")
        self.btn_limpiar_programa.setVisible(False)
        
        self.forma_pago_combo.setCurrentText("EFECTIVO")
        self.numero_comprobante_input.clear()
        self.banco_origen_input.clear()
        self.cuenta_origen_input.clear()
        self.transferencia_container.hide()
        
        # Limpiar tabla de detalles
        self.tabla_detalles.setRowCount(0)
        
        # Reiniciar valores de totales
        self.descuento_input.setValue(0.00)
        self._actualizar_totales()
        
        self.estado_combo.setCurrentText("REGISTRADO")
        self.observaciones_input.clear()
        
        self.lista_documentos.clear()
        
        # Restaurar título original
        self.setWindowTitle("💰 Gestión de Transacción")
    
    # ▓▒░░▒▓ MÉTODOS AUXILIARES ▓▒░░▒▓
    
    def _seleccionar_estudiante(self):
        """Manejador para seleccionar estudiante."""
        # Aquí podrías abrir un diálogo para seleccionar estudiante
        # Por ahora, simularemos la selección
        from view.overlays.estudiante_overlay import EstudianteOverlay
        
        estudiante_overlay = EstudianteOverlay(self.parent())
        estudiante_overlay.estudiante_creado.connect(self._on_estudiante_seleccionado)
        estudiante_overlay.estudiante_actualizado.connect(self._on_estudiante_seleccionado)
        estudiante_overlay.show_form(estudiante_id=self.estudiante_id, solo_lectura=True)
    
    @staticmethod
    def obtener_ultimo_numero_transaccion_dia(fecha_str=None):
        """
        Obtener el último número de transacción del día.
        
        Args:
            fecha_str: Fecha en formato YYYYMMDD (opcional, si es None usa hoy)
            
        Returns:
            str: Último número de transacción del día, o None si no hay
        """
        try:
            from config.database import Database
            from datetime import datetime, date
            
            # Si no se proporciona fecha, usar hoy
            if fecha_str is None:
                fecha_obj = date.today()
                fecha_str = fecha_obj.strftime("%Y%m%d")
            else:
                # Convertir string a fecha
                if len(fecha_str) == 8:  # YYYYMMDD
                    fecha_obj = datetime.strptime(fecha_str, "%Y%m%d").date()
                else:
                    fecha_obj = date.today()
                    fecha_str = fecha_obj.strftime("%Y%m%d")
            
            db = Database()
            conn = db.get_connection()
            if not conn:
                logger.error("Error al intentar realizar la conexión a la base de datos")
                return
            
            with conn.cursor() as cursor:
                # Buscar transacciones del día
                query = """
                    SELECT numero_transaccion 
                    FROM transacciones 
                    WHERE fecha_pago = %s 
                    AND numero_transaccion IS NOT NULL
                    ORDER BY id DESC 
                    LIMIT 1
                """
                cursor.execute(query, (fecha_obj,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    return result[0]
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"Error obteniendo último número de transacción: {e}")
            return None
    
    def _on_estudiante_seleccionado(self, datos_estudiante):
        """
        Manejador cuando se selecciona un estudiante.
        
        Args:
            datos_estudiante: Diccionario con datos del estudiante seleccionado
        """
        if datos_estudiante and 'estudiante_id' in datos_estudiante:
            self.estudiante_id = datos_estudiante['estudiante_id']
            self._cargar_estudiante()
    
    def _limpiar_estudiante(self):
        """Limpiar selección de estudiante."""
        self.estudiante_id = None
        self._estudiante_cache = None
        self.estudiante_label.setText("No seleccionado")
        self.btn_limpiar_estudiante.setVisible(False)
        self.btn_detalle_estudiante.setEnabled(False)
        self.estudiante_label.repaint()
    
    def _seleccionar_programa(self):
        """Manejador para seleccionar programa."""
        # Aquí podrías abrir un diálogo para seleccionar programa
        # Por ahora, simularemos la selección
        from view.overlays.programa_overlay import ProgramaOverlay
        
        programa_overlay = ProgramaOverlay(self.parent())
        programa_overlay.programa_guardado.connect(self._on_programa_seleccionado)
        programa_overlay.programa_actualizado.connect(self._on_programa_seleccionado)
        programa_overlay.show_form(solo_lectura=True, modo="seleccion")
    
    def _on_programa_seleccionado(self, datos_programa):
        """
        Manejador cuando se selecciona un programa.
        
        Args:
            datos_programa: Diccionario con datos del programa seleccionado
        """
        if datos_programa and 'id' in datos_programa:
            self.programa_id = datos_programa['id']
            self._cargar_programa()
    
    def _limpiar_programa(self):
        """Limpiar selección de programa."""
        self.programa_id = None
        self._programa_cache = None
        self.programa_label.setText("No seleccionado")
        self.btn_limpiar_programa.setVisible(False)
        self.btn_detalle_programa.setEnabled(False)
        self.programa_label.repaint()
    
    def _on_forma_pago_changed(self, forma_pago):
        """
        Manejador cuando cambia la forma de pago.
        
        Args:
            forma_pago: Nueva forma de pago seleccionada
        """
        # Mostrar campos para transferencias si corresponde
        if forma_pago in ["TRANSFERENCIA", "DEPOSITO"]:
            self.transferencia_container.show()
        else:
            self.transferencia_container.hide()
    
    def _actualizar_total(self):
        """Actualizar montos calculados (método antiguo - mantener por compatibilidad)."""
        # Este método ya no se usa, se reemplazó por _actualizar_totales()
        pass
    
    def _actualizar_totales(self):
        """Actualizar totales de la transacción."""
        subtotal = 0.0
        
        for row in range(self.tabla_detalles.rowCount()):
            # Obtener cantidad y precio
            widget_cant = self.tabla_detalles.cellWidget(row, 2)
            widget_precio = self.tabla_detalles.cellWidget(row, 3)
            widget_subtotal = self.tabla_detalles.cellWidget(row, 4)
            
            # Verificar que sean QDoubleSpinBox y QLabel
            if (widget_cant and isinstance(widget_cant, QDoubleSpinBox) and
                widget_precio and isinstance(widget_precio, QDoubleSpinBox)):
                
                cantidad = widget_cant.value()
                precio = widget_precio.value()
                row_subtotal = cantidad * precio
                
                # Actualizar subtotal en la fila si es un QLabel
                if widget_subtotal and isinstance(widget_subtotal, QLabel):
                    widget_subtotal.setText(f"${row_subtotal:,.2f}")
                    
                subtotal += row_subtotal
                
        # Aplicar descuento
        descuento = self.descuento_input.value()
        if descuento > subtotal:
            descuento = subtotal
            self.descuento_input.setValue(descuento)
            
        total = subtotal - descuento
        
        # Actualizar labels
        self.subtotal_label.setText(f"${subtotal:,.2f}")
        self.total_label.setText(f"${total:,.2f}")
    
    def _agregar_concepto(self):
        """Agregar un nuevo concepto a la tabla."""
        try:
            # Obtener conceptos disponibles
            conceptos = ConceptoPagoModel.obtener_conceptos_activos()
            if not conceptos:
                self.mostrar_mensaje("Información", "No hay conceptos de pago disponibles", "info")
                return
            
            row_position = self.tabla_detalles.rowCount()
            self.tabla_detalles.insertRow(row_position)
            
            # Combo para seleccionar concepto
            combo_concepto = QComboBox()
            combo_concepto.addItem("Seleccionar...", None)
            for concepto in conceptos:
                descripcion = f"{concepto.get('nombre')} - ${concepto.get('monto_base', 0):.2f}"
                combo_concepto.addItem(descripcion, concepto.get('id'))
            combo_concepto.currentIndexChanged.connect(lambda idx, r=row_position: self._on_concepto_seleccionado(r))
            
            # Descripción
            desc_input = QLineEdit()
            desc_input.setPlaceholderText("Descripción del concepto")
            
            # Cantidad
            cant_spin = QDoubleSpinBox()
            cant_spin.setRange(1, 100)
            cant_spin.setValue(1)
            cant_spin.setDecimals(0)
            cant_spin.valueChanged.connect(self._actualizar_totales)
            
            # Precio unitario
            precio_spin = QDoubleSpinBox()
            precio_spin.setRange(0, 100000)
            precio_spin.setValue(0.00)
            precio_spin.setPrefix("$ ")
            precio_spin.setDecimals(2)
            precio_spin.valueChanged.connect(self._actualizar_totales)
            
            # Subtotal
            subtotal_label = QLabel("$0.00")
            subtotal_label.setStyleSheet("font-weight: bold;")
            
            # Botón eliminar
            btn_eliminar = QPushButton("🗑️")
            btn_eliminar.setObjectName("btnEliminarConcepto")
            btn_eliminar.setStyleSheet("""
                #btnEliminarConcepto {
                    background-color: #e74c3c;
                    color: white;
                    font-weight: bold;
                    padding: 2px 8px;
                    border-radius: 3px;
                    border: none;
                    font-size: 10px;
                }
                #btnEliminarConcepto:hover {
                    background-color: #c0392b;
                }
            """)
            btn_eliminar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_eliminar.clicked.connect(lambda _, r=row_position: self._eliminar_concepto(r))
            
            # Agregar widgets a la tabla
            self.tabla_detalles.setCellWidget(row_position, 0, combo_concepto)
            self.tabla_detalles.setCellWidget(row_position, 1, desc_input)
            self.tabla_detalles.setCellWidget(row_position, 2, cant_spin)
            self.tabla_detalles.setCellWidget(row_position, 3, precio_spin)
            self.tabla_detalles.setCellWidget(row_position, 4, subtotal_label)
            self.tabla_detalles.setCellWidget(row_position, 5, btn_eliminar)
            
            # Actualizar totales
            self._actualizar_totales()
            
        except Exception as e:
            logger.error(f"Error agregando concepto: {e}")
            self.mostrar_mensaje("Error", f"No se pudo agregar concepto: {str(e)}", "error")
    
    def _on_concepto_seleccionado(self, row):
        """
        Cuando se selecciona un concepto.
        
        Args:
            row: Número de fila donde se seleccionó el concepto
        """
        widget_combo = self.tabla_detalles.cellWidget(row, 0)
        if widget_combo and isinstance(widget_combo, QComboBox):
            concepto_id = widget_combo.currentData()
            if concepto_id:
                try:
                    # Obtener información del concepto
                    conceptos = ConceptoPagoModel.obtener_conceptos_activos()
                    concepto_seleccionado = None
                    for concepto in conceptos:
                        if concepto.get('id') == concepto_id:
                            concepto_seleccionado = concepto
                            break
                        
                    if concepto_seleccionado:
                        # Establecer precio unitario
                        widget_precio = self.tabla_detalles.cellWidget(row, 3)
                        if widget_precio and isinstance(widget_precio, QDoubleSpinBox):
                            monto_base = float(concepto_seleccionado.get('monto_base', 0))
                            widget_precio.setValue(monto_base)
                            
                        # Establecer descripción si está vacía
                        widget_desc = self.tabla_detalles.cellWidget(row, 1)
                        if (widget_desc and isinstance(widget_desc, QLineEdit) and 
                            not widget_desc.text().strip()):
                            descripcion = concepto_seleccionado.get('descripcion', '')
                            widget_desc.setText(descripcion)
                            
                    self._actualizar_totales()
                except Exception as e:
                    logger.error(f"Error cargando concepto: {e}")
    
    def _eliminar_concepto(self, row):
        """
        Eliminar concepto de la tabla.
        
        Args:
            row: Número de fila a eliminar
        """
        self.tabla_detalles.removeRow(row)
        self._actualizar_totales()
    
    def _agregar_documento(self):
        """Agregar documento adjunto."""
        # Abrir diálogo de selección de archivos
        filtros = TipoDocumento.get_filters()
        archivos, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar Documentos",
            "",
            filtros
        )
        
        for archivo in archivos:
            if archivo:
                # Verificar tamaño máximo
                tamaño = os.path.getsize(archivo)
                if tamaño > AppConstants.MAX_FILE_SIZE_MB * 1024 * 1024:
                    self.mostrar_mensaje(
                        "Error",
                        f"El archivo {os.path.basename(archivo)} excede el tamaño máximo de {AppConstants.MAX_FILE_SIZE_MB}MB",
                        "error"
                    )
                    continue
                
                # Agregar a la lista temporal
                nombre = os.path.basename(archivo)
                item = QListWidgetItem(f"{nombre} ({self._formatear_tamaño(tamaño)})")
                item.setData(Qt.ItemDataRole.UserRole, archivo)
                self.lista_documentos.addItem(item)
                
                self.documentos_temp.append({
                    'ruta_original': archivo,
                    'nombre_original': nombre,
                    'tamaño': tamaño
                })
    
    def _eliminar_documento_seleccionado(self):
        """Eliminar documento seleccionado."""
        item = self.lista_documentos.currentItem()
        if not item:
            return
        
        row = self.lista_documentos.row(item)
        
        # Si es un documento temporal, eliminarlo de la lista
        if row < len(self.documentos_temp):
            self.documentos_temp.pop(row)
        
        # Si es un documento existente, marcarlo para eliminación
        else:
            doc_data = item.data(Qt.ItemDataRole.UserRole)
            if doc_data and 'id' in doc_data:
                # Aquí podrías marcar para eliminación en la base de datos
                pass
        
        self.lista_documentos.takeItem(row)
    
    def _formatear_tamaño(self, bytes):
        """
        Formatear tamaño de archivo para mostrar.
        
        Args:
            bytes: Tamaño en bytes
            
        Returns:
            str: Tamaño formateado (ej: "1.5 MB")
        """
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"
    
    def guardar_formulario(self):
        """Guardar la transacción - Versión completamente corregida"""
        try:
            # 1. Validar formulario
            valido, errores = self.validar_formulario()
            if not valido:
                self.mostrar_mensaje("Errores de validación", "\n".join(errores), "error")
                return
            
            # 2. Obtener datos del formulario
            datos = self.obtener_datos()
            
            # 3. Obtener usuario actual (debería venir de sesión)
            # Por ahora usar valor temporal - esto debería reemplazarse
            usuario_id = self._obtener_usuario_actual()
            
            # 4. Preparar detalles de manera más robusta
            detalles = self._preparar_detalles_completos()
            if not detalles:
                self.mostrar_mensaje("Error", "No hay detalles válidos para guardar", "error")
                return
            
            datos['detalles'] = detalles
            
            # 5. Calcular totales correctamente
            subtotal = sum(det['subtotal'] for det in detalles)
            descuento = self.descuento_input.value()
            total = subtotal - descuento
            
            datos['monto_total'] = subtotal
            datos['descuento_total'] = descuento
            datos['monto_final'] = total
            
            # 6. Generar número de comprobante si no existe
            if not datos.get('numero_comprobante') or datos['numero_comprobante'] == "(Generado automáticamente)":
                try:
                    fecha_pago = self.fecha_pago_input.date().toPython()
                    datos['numero_comprobante'] = self._generar_numero_comprobante_automatico(
                        fecha_pago, 
                        self.forma_pago_combo.currentText()
                    )
                except Exception as e:
                    logger.error(f"Error generando número de comprobante: {e}")
                    # Número temporal
                    datos['numero_comprobante'] = f"TEMP-{int(datetime.now().timestamp())}"
            
            # 7. Agregar usuario que registra
            datos['registrado_por'] = usuario_id
            
            # 8. Agregar documentos temporales
            if self.documentos_temp:
                datos['documentos_temp'] = self.documentos_temp
            
            # 9. Llamar al controlador
            from controller.transaccion_controller import TransaccionController
            controller = TransaccionController()
            
            logger.info(f"Enviando datos al controlador: {datos}")
            
            resultado = controller.crear_transaccion(datos, usuario_id)
            
            # 10. Manejar resultado
            if resultado.get('exito'):
                # Emitir señal
                self.transaccion_creada.emit({
                    'transaccion_id': resultado['transaccion_id'],
                    'numero_transaccion': resultado.get('numero_transaccion', datos.get('numero_comprobante')),
                    'fecha_pago': datos['fecha_pago'],
                    'monto_final': datos['monto_final'],
                    'estudiante_id': self.estudiante_id,
                    'programa_id': self.programa_id,
                    'inscripcion_id': self.inscripcion_id
                })
                
                # Mostrar mensaje de éxito
                QMessageBox.information(
                    self, 
                    "✅ Transacción Guardada",
                    f"Transacción guardada exitosamente.\n"
                    f"Número: {resultado.get('numero_transaccion', 'N/A')}\n"
                    f"Monto: ${datos['monto_final']:,.2f}\n"
                    f"Detalles: {resultado.get('detalles_insertados', 0)} conceptos"
                )
                
                # Cerrar después de éxito
                QTimer.singleShot(1500, self.close)
                
            else:
                mensaje_error = resultado.get('mensaje', 'Error desconocido al guardar')
                if 'errores' in resultado:
                    mensaje_error += f"\n\nErrores:\n• " + "\n• ".join(resultado['errores'])
                
                QMessageBox.critical(self, "❌ Error al Guardar", mensaje_error)
                
        except Exception as e:
            logger.error(f"Error crítico al guardar transacción: {e}", exc_info=True)
            QMessageBox.critical(
                self, 
                "❌ Error Crítico", 
                f"No se pudo guardar la transacción:\n\n{str(e)}\n\n"
                f"Por favor, verifique los datos e intente nuevamente."
            )
    
    def _preparar_detalles_completos(self):
        """Preparar detalles de manera más robusta"""
        detalles = []
        
        for row in range(self.tabla_detalles.rowCount()):
            try:
                # Obtener widgets con verificación
                widget_combo = self.tabla_detalles.cellWidget(row, 0)
                widget_desc = self.tabla_detalles.cellWidget(row, 1)
                widget_cant = self.tabla_detalles.cellWidget(row, 2)
                widget_precio = self.tabla_detalles.cellWidget(row, 3)
                
                # Verificar que todos existen y son del tipo correcto
                if not all([widget_combo, widget_desc, widget_cant, widget_precio]):
                    logger.warning(f"Fila {row}: Widgets incompletos")
                    continue
                
                if not isinstance(widget_combo, QComboBox):
                    continue
                
                # Obtener ID del concepto
                concepto_id = widget_combo.currentData()
                if not concepto_id:
                    logger.warning(f"Fila {row}: No hay concepto seleccionado")
                    continue
                
                # Obtener valores
                descripcion = widget_desc.text().strip() if isinstance(widget_desc, QLineEdit) else ""
                cantidad = widget_cant.value() if isinstance(widget_cant, QDoubleSpinBox) else 1
                precio_unitario = widget_precio.value() if isinstance(widget_precio, QDoubleSpinBox) else 0
                
                if cantidad <= 0 or precio_unitario <= 0:
                    logger.warning(f"Fila {row}: Cantidad o precio inválido")
                    continue
                
                subtotal = cantidad * precio_unitario
                
                # Crear detalle
                detalle = {
                    'concepto_pago_id': concepto_id,
                    'descripcion': descripcion or widget_combo.currentText().split(' - ')[0],
                    'cantidad': int(cantidad),
                    'precio_unitario': float(precio_unitario),
                    'subtotal': float(subtotal),
                    'orden': row + 1
                }
                
                detalles.append(detalle)
                
            except Exception as e:
                logger.error(f"Error procesando fila {row}: {e}")
                continue
            
        return detalles
    
    def _generar_numero_comprobante_automatico(self, fecha_pago, forma_pago):
        """Generar número de comprobante automático"""
        try:
            from model.transaccion_model import TransaccionModel
            
            numero = TransaccionModel.generar_numero_transaccion(
                fecha_pago=fecha_pago,
                estudiante_id=self.estudiante_id,
                programa_id=self.programa_id,
                inscripcion_id=self.inscripcion_id,
                usuario_id=self._obtener_usuario_actual(),
                es_ingreso=True
            )
            
            return numero
        except Exception as e:
            logger.error(f"Error generando número automático: {e}")
            # Fallback: fecha + timestamp
            return f"COMP-{fecha_pago.strftime('%Y%m%d')}-{int(datetime.now().timestamp())}"
    
    def _obtener_usuario_actual(self):
        """Obtener ID del usuario actual - método temporal"""
        # Esto debería obtener el usuario de la sesión
        # Por ahora retornar 1 (admin)
        return 1
    
    def _obtener_concepto_id_por_defecto(self) -> int:
        """
        Obtener ID de concepto de pago por defecto según el contexto.
        
        Returns:
            int: ID del concepto de pago por defecto
        """
        try:
            # Lógica para determinar concepto basado en contexto
            if self.programa_id:
                # Si hay programa, podría ser mensualidad
                return self._obtener_concepto_mensualidad()
            else:
                # Transacción general
                return self._obtener_concepto_general()
        except Exception:
            return 1  # ID por defecto
    
    def _obtener_concepto_mensualidad(self) -> int:
        """
        Obtener ID del concepto de mensualidad.
        
        Returns:
            int: ID del concepto de mensualidad
        """
        try:
            # Buscar concepto de tipo MENSUALIDAD
            conceptos = ConceptoPagoModel.obtener_conceptos_activos()
            for concepto in conceptos:
                if concepto.get('tipo_concepto') == 'MENSUALIDAD':
                    return concepto.get('id', 1)
        except Exception as e:
            logger.error(f"Error obteniendo concepto mensualidad: {e}")
            
        return 1  # ID por defecto
    
    def _obtener_concepto_general(self) -> int:
        """
        Obtener ID del concepto general.
        
        Returns:
            int: ID del concepto general
        """
        try:
            # Buscar concepto de tipo GENERAL
            conceptos = ConceptoPagoModel.obtener_conceptos_activos()
            for concepto in conceptos:
                if concepto.get('tipo_concepto') == 'GENERAL':
                    return concepto.get('id', 1)
        except Exception as e:
            logger.error(f"Error obteniendo concepto general: {e}")
            
        return 1  # ID por defecto
    
    def _generar_descripcion_transaccion(self) -> str:
        """
        Generar descripción apropiada para la transacción.
        
        Returns:
            str: Descripción de la transacción
        """
        descripcion = f"Pago {self.forma_pago_combo.currentText()}"
        
        if self.estudiante_id:
            descripcion += f" - Estudiante {self.estudiante_label.text()}"
            
        if self.programa_id:
            descripcion += f" - Programa {self.programa_label.text()}"
            
        return descripcion[:200]  # Limitar a 200 caracteres
    
    def _determinar_tipo_pago(self, datos: Dict[str, Any]) -> str:
        """
        Determinar tipo de pago basado en contexto.
        
        Args:
            datos: Datos de la transacción
            
        Returns:
            str: Tipo de pago
        """
        if not self.programa_id:
            return "OTROS"
        
        # Aquí podrías implementar lógica más compleja
        # Por ejemplo, basándote en el monto, descripción, etc.
        
        # Por ahora, determinar basado en concepto
        monto_total = datos.get('monto_total', 0)
        
        # Obtener información del programa para comparar
        try:
            from model.programa_model import ProgramaModel
            resultado = ProgramaModel.obtener_programa(self.programa_id)
            if resultado and 'success' in resultado and resultado['success']:
                data = resultado['data']
                costo_inscripcion = data.get('costo_inscripcion', 0)
                costo_matricula = data.get('costo_matricula', 0)
                costo_mensualidad = data.get('costo_mensualidad', 0)
                
                # Determinar tipo por proximidad al monto
                if abs(monto_total - costo_inscripcion) < 10:
                    return "INSCRIPCION"
                elif abs(monto_total - costo_matricula) < 10:
                    return "MATRICULA"
                elif abs(monto_total - costo_mensualidad) < 10:
                    return "MENSUALIDAD"
        except Exception as e:
            logger.error(f"Error determinando tipo de pago: {e}")
            
        # Por defecto
        return "MENSUALIDAD" if self.programa_id else "OTROS"
    
    def closeEvent(self, event):
        """
        Manejador para cuando se cierra el overlay.
        
        Args:
            event: Evento de cierre
        """
        # Limpiar archivos temporales si es necesario
        for doc in self.documentos_temp:
            try:
                if Path(doc['ruta_original']).exists():
                    # Solo eliminar si es un archivo temporal que creamos
                    # No eliminar el original del usuario
                    pass
            except:
                pass
            
        super().closeEvent(event)
    
    def _configurar_controles_modo(self, modo: str):
        """
        Configurar controles según el modo.
        
        Args:
            modo: Modo de operación ("nuevo", "editar", "visualizar")
        """
        # Deshabilitar selección de estudiante/programa en modo visualización
        solo_lectura = (modo == "visualizar")
        
        self.btn_seleccionar_estudiante.setEnabled(not solo_lectura)
        self.btn_seleccionar_programa.setEnabled(not solo_lectura)
        self.btn_agregar_documento.setEnabled(not solo_lectura)
        self.btn_eliminar_documento.setEnabled(not solo_lectura)
        self.btn_agregar_concepto.setEnabled(not solo_lectura)
        
        # Los botones de detalle siempre están habilitados si hay datos
        if self.estudiante_id:
            self.btn_detalle_estudiante.setEnabled(True)
        if self.programa_id:
            self.btn_detalle_programa.setEnabled(True)
        
        # Los botones de limpiar solo en modo edición
        if hasattr(self, 'btn_limpiar_estudiante'):
            self.btn_limpiar_estudiante.setEnabled(not solo_lectura and self.estudiante_id is not None)
        if hasattr(self, 'btn_limpiar_programa'):
            self.btn_limpiar_programa.setEnabled(not solo_lectura and self.programa_id is not None)
        
        self.fecha_pago_input.setEnabled(not solo_lectura)
        self.forma_pago_combo.setEnabled(not solo_lectura)
        self.descuento_input.setEnabled(not solo_lectura)
        self.estado_combo.setEnabled(not solo_lectura)
        self.observaciones_input.setEnabled(not solo_lectura)
        
        # Habilitar/deshabilitar controles en tabla de detalles
        for row in range(self.tabla_detalles.rowCount()):
            for col in range(5):  # Todas las columnas excepto la última (botón eliminar)
                widget = self.tabla_detalles.cellWidget(row, col)
                if widget:
                    widget.setEnabled(not solo_lectura)
    
    def _mostrar_detalle_estudiante(self):
        """Mostrar detalle del estudiante seleccionado."""
        if not self.estudiante_id:
            self.mostrar_mensaje("Información", "No hay estudiante seleccionado", "info")
            return
        
        try:
            from view.overlays.estudiante_overlay import EstudianteOverlay
            
            estudiante_overlay = EstudianteOverlay(self.parent())
            estudiante_overlay.estudiante_actualizado.connect(self._on_estudiante_actualizado)
            
            # Preparar datos del estudiante para pasar al overlay
            datos_estudiante = {'id': self.estudiante_id}
            
            # Llamar a show_form con los parámetros correctos
            # Primero intentar con el formato actual
            try:
                estudiante_overlay.show_form(
                    estudiante_id=self.estudiante_id,
                    datos_estudiante=datos_estudiante,
                    solo_lectura=True
                )
            except TypeError:
                # Si falla, intentar con el formato alternativo
                try:
                    estudiante_overlay.show_form(
                        estudiante_id=self.estudiante_id,
                        solo_lectura=True
                    )
                except TypeError:
                    # Último intento: solo pasar el modo
                    estudiante_overlay.show_form(
                        solo_lectura=True
                    )
        except Exception as e:
            logger.error(f"Error mostrando detalle de estudiante: {e}")
            self.mostrar_mensaje("Error", f"No se pudo mostrar el detalle: {str(e)}", "error")
    
    def _mostrar_detalle_programa(self):
        """Mostrar detalle del programa seleccionado."""
        if not self.programa_id:
            self.mostrar_mensaje("Información", "No hay programa seleccionado", "info")
            return
        
        try:
            from view.overlays.programa_overlay import ProgramaOverlay
            
            programa_overlay = ProgramaOverlay(self.parent())
            programa_overlay.programa_actualizado.connect(self._on_programa_actualizado)
            
            # Preparar datos del programa para pasar al overlay
            datos_programa = {'id': self.programa_id}
            
            # Llamar a show_form con los parámetros correctos
            # Primero intentar con el formato actual
            try:
                programa_overlay.show_form(
                    datos=datos_programa,
                    solo_lectura=True,
                    modo="visualizar"
                )
            except TypeError:
                # Si falla, intentar con el formato alternativo
                try:
                    programa_overlay.show_form(
                        datos=datos_programa,
                        solo_lectura=True,
                        modo="visualizar"
                    )
                except TypeError:
                    # Último intento: solo pasar el modo
                    programa_overlay.show_form(
                        solo_lectura=True,
                        modo="visualizar"
                    )
        except Exception as e:
            logger.error(f"Error mostrando detalle de programa: {e}")
            self.mostrar_mensaje("Error", f"No se pudo mostrar el detalle: {str(e)}", "error")
    
    def _on_estudiante_actualizado(self, datos_estudiante):
        """
        Cuando se actualiza un estudiante desde otro overlay.
        
        Args:
            datos_estudiante: Datos del estudiante actualizado
        """
        if datos_estudiante and 'estudiante_id' in datos_estudiante:
            if datos_estudiante['estudiante_id'] == self.estudiante_id:
                # Limpiar cache y recargar
                self._estudiante_cache = None
                self._cargar_estudiante(force=True)
    
    def _on_programa_actualizado(self, datos_programa):
        """
        Cuando se actualiza un programa desde otro overlay.
        
        Args:
            datos_programa: Datos del programa actualizado
        """
        if datos_programa and 'id' in datos_programa:
            if datos_programa['id'] == self.programa_id:
                # Limpiar cache y recargar
                self._programa_cache = None
                self._cargar_programa(force=True)
    