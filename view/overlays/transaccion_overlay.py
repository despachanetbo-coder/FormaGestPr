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
    Overlay para gestionar transacciones financieras
    """
    
    # Señales específicas
    transaccion_creada = Signal(dict)      # Datos de la transacción creada
    transaccion_actualizada = Signal(dict) # Datos de la transacción actualizada
    transaccion_anulada = Signal(int)      # ID de transacción anulada
    documento_subido = Signal(dict)        # Documento subido
    
    def __init__(self, parent=None):
        """Inicializar overlay de transacción"""
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
        self.detalles_transaccion = []
        self.documentos_adjuntos = []
        
        # Ruta temporal para documentos
        self.documentos_temp = []
        
        # Configurar UI específica
        self.setup_transaccion_ui()
        
        # Configurar tamaño mínimo
        self.setMinimumSize(1000, 800)
        
        logger.debug("✅ TransaccionOverlay inicializado")
    
    def setup_transaccion_ui(self):
        """Configurar UI específica para transacción"""
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
        
        # ===== SECCIÓN 1: Información básica =====
        self.setup_info_basica_section(content_layout)
        
        # ===== SECCIÓN 2: Detalles de la transacción =====
        self.setup_detalles_section(content_layout)
        
        # ===== SECCIÓN 3: Documentos adjuntos =====
        self.setup_documentos_section(content_layout)
        
        # ===== SECCIÓN 4: Observaciones =====
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
    
    def setup_info_basica_section(self, parent_layout):
        """Configurar sección de información básica"""
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
        self.estudiante_label = QLabel("No seleccionado")
        self.estudiante_label.setStyleSheet("color: #7f8c8d;")
        
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
        """)
        self.btn_limpiar_estudiante.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_limpiar_estudiante.clicked.connect(self._limpiar_estudiante)
        self.btn_limpiar_estudiante.setVisible(False)
        
        estudiante_hbox.addWidget(self.estudiante_label, 1)
        estudiante_hbox.addWidget(self.btn_seleccionar_estudiante)
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
        """)
        self.btn_limpiar_programa.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_limpiar_programa.clicked.connect(self._limpiar_programa)
        self.btn_limpiar_programa.setVisible(False)
        
        programa_hbox.addWidget(self.programa_label, 1)
        programa_hbox.addWidget(self.btn_seleccionar_programa)
        programa_hbox.addWidget(self.btn_limpiar_programa)
        grid.addLayout(programa_hbox, 3, 1)
        
        parent_layout.addWidget(info_group)
    
    def setup_detalles_section(self, parent_layout):
        """Configurar sección de detalles de la transacción"""
        # Grupo de detalles
        detalles_group = QGroupBox("💵 Detalles del Pago")
        detalles_group.setObjectName("detallesGroup")
        
        grid = QGridLayout(detalles_group)
        grid.setContentsMargins(15, 20, 15, 15)
        grid.setSpacing(12)
        
        # Fila 1: Forma de pago
        grid.addWidget(QLabel("Forma de pago*:"), 0, 0)
        self.forma_pago_combo = QComboBox()
        for forma in FormaPago:
            self.forma_pago_combo.addItem(forma.value, forma.name)
        self.forma_pago_combo.setCurrentText("EFECTIVO")
        self.forma_pago_combo.currentTextChanged.connect(self._on_forma_pago_changed)
        grid.addWidget(self.forma_pago_combo, 0, 1)
        
        # Campos para transferencias
        self.transferencia_container = QWidget()
        transferencia_layout = QVBoxLayout(self.transferencia_container)
        transferencia_layout.setContentsMargins(0, 5, 0, 0)
        
        # Banco origen
        banco_layout = QHBoxLayout()
        banco_layout.addWidget(QLabel("Banco origen:"))
        self.banco_origen_input = QLineEdit()
        self.banco_origen_input.setPlaceholderText("Ej: Banco Unión")
        banco_layout.addWidget(self.banco_origen_input)
        transferencia_layout.addLayout(banco_layout)
        
        # Cuenta origen
        cuenta_layout = QHBoxLayout()
        cuenta_layout.addWidget(QLabel("Cuenta origen:"))
        self.cuenta_origen_input = QLineEdit()
        self.cuenta_origen_input.setPlaceholderText("Ej: 123456789")
        cuenta_layout.addWidget(self.cuenta_origen_input)
        transferencia_layout.addLayout(cuenta_layout)
        
        self.transferencia_container.hide()
        grid.addWidget(self.transferencia_container, 1, 0, 1, 2)
        
        # Fila 2: Número de comprobante
        grid.addWidget(QLabel("N° Comprobante:"), 2, 0)
        self.numero_comprobante_input = QLineEdit()
        self.numero_comprobante_input.setPlaceholderText("Opcional")
        grid.addWidget(self.numero_comprobante_input, 2, 1)
        
        # Fila 3: Monto total
        grid.addWidget(QLabel("Monto total*:"), 3, 0)
        monto_hbox = QHBoxLayout()
        self.monto_total_input = QDoubleSpinBox()
        self.monto_total_input.setRange(0, 1000000)
        self.monto_total_input.setValue(0.00)
        self.monto_total_input.setPrefix("$ ")
        self.monto_total_input.setDecimals(2)
        self.monto_total_input.setMaximumWidth(150)
        self.monto_total_input.valueChanged.connect(self._actualizar_total)
        
        self.monto_total_label = QLabel("$0.00")
        self.monto_total_label.setStyleSheet("font-weight: bold; color: #2c3e50; font-size: 14px;")
        
        monto_hbox.addWidget(self.monto_total_input)
        monto_hbox.addWidget(self.monto_total_label)
        monto_hbox.addStretch()
        grid.addLayout(monto_hbox, 3, 1)
        
        # Fila 4: Descuento
        grid.addWidget(QLabel("Descuento:"), 4, 0)
        descuento_hbox = QHBoxLayout()
        self.descuento_input = QDoubleSpinBox()
        self.descuento_input.setRange(0, 1000000)
        self.descuento_input.setValue(0.00)
        self.descuento_input.setPrefix("$ ")
        self.descuento_input.setDecimals(2)
        self.descuento_input.setMaximumWidth(150)
        self.descuento_input.valueChanged.connect(self._actualizar_total)
        
        self.descuento_label = QLabel("$0.00")
        self.descuento_label.setStyleSheet("color: #e74c3c;")
        
        descuento_hbox.addWidget(self.descuento_input)
        descuento_hbox.addWidget(self.descuento_label)
        descuento_hbox.addStretch()
        grid.addLayout(descuento_hbox, 4, 1)
        
        # Fila 5: Monto final
        grid.addWidget(QLabel("Monto final*:"), 5, 0)
        self.monto_final_label = QLabel("$0.00")
        self.monto_final_label.setStyleSheet("font-weight: bold; color: #27ae60; font-size: 16px;")
        grid.addWidget(self.monto_final_label, 5, 1)
        
        # Fila 6: Estado
        grid.addWidget(QLabel("Estado*:"), 6, 0)
        self.estado_combo = QComboBox()
        for estado in EstadoTransaccion:
            self.estado_combo.addItem(estado.value, estado.name)
        self.estado_combo.setCurrentText("REGISTRADO")
        grid.addWidget(self.estado_combo, 6, 1)
        
        parent_layout.addWidget(detalles_group)
    
    def setup_documentos_section(self, parent_layout):
        """Configurar sección de documentos adjuntos"""
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
        """Configurar sección de observaciones"""
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
        """Conectar señales específicas"""
        # Conectar cambios en montos
        self.monto_total_input.valueChanged.connect(self._actualizar_total)
        self.descuento_input.valueChanged.connect(self._actualizar_total)
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo",
                  estudiante_id=None, programa_id=None):
        """Mostrar el overlay con configuración específica"""
        self.solo_lectura = solo_lectura
        self.set_modo(modo)
        
        # Establecer IDs si se proporcionan
        if estudiante_id:
            self.estudiante_id = estudiante_id
            self._cargar_estudiante()
        if programa_id:
            self.programa_id = programa_id
            self._cargar_programa()
        
        if datos:
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
        if modo == "visualizar":
            self.btn_seleccionar_estudiante.setVisible(False)
            self.btn_seleccionar_programa.setVisible(False)
            self.btn_agregar_documento.setVisible(False)
            self.btn_eliminar_documento.setVisible(False)
            self.fecha_pago_input.setEnabled(False)
            self.forma_pago_combo.setEnabled(False)
            self.monto_total_input.setEnabled(False)
            self.descuento_input.setEnabled(False)
            self.estado_combo.setEnabled(False)
            self.observaciones_input.setEnabled(False)
        
        # Cargar documentos si ya hay transacción
        if self.transaccion_id:
            self._cargar_documentos()
        
        # Llamar al método base
        super().show_form(solo_lectura)
    
    def cargar_datos(self, datos):
        """Cargar datos de transacción existente"""
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
        
        # Montos
        if 'monto_total' in datos and datos['monto_total']:
            self.monto_total_input.setValue(float(datos['monto_total']))
        
        if 'descuento_total' in datos and datos['descuento_total']:
            self.descuento_input.setValue(float(datos['descuento_total']))
        
        if 'monto_final' in datos and datos['monto_final']:
            self._actualizar_total()  # Esto actualizará la etiqueta
        
        # Estado
        if 'estado' in datos and datos['estado']:
            index = self.estado_combo.findText(datos['estado'])
            if index >= 0:
                self.estado_combo.setCurrentIndex(index)
        
        # Observaciones
        if 'observaciones' in datos and datos['observaciones']:
            self.observaciones_input.setPlainText(datos['observaciones'])
    
    def _cargar_estudiante(self):
        """Cargar información del estudiante"""
        if not self.estudiante_id:
            return
        
        try:
            estudiante = EstudianteModel.obtener_estudiante_por_id(self.estudiante_id)
            if estudiante:
                nombre_completo = f"{estudiante['nombres']} {estudiante['apellido_paterno']}"
                if estudiante.get('apellido_materno'):
                    nombre_completo += f" {estudiante['apellido_materno']}"
                
                ci_completo = f"{estudiante['ci_numero']}-{estudiante['ci_expedicion']}"
                self.estudiante_label.setText(f"{nombre_completo} ({ci_completo})")
                self.btn_limpiar_estudiante.setVisible(True)
                
        except Exception as e:
            logger.error(f"Error cargando estudiante: {e}")
    
    def _cargar_programa(self):
        """Cargar información del programa"""
        if not self.programa_id:
            return
        
        try:
            resultado = ProgramaModel.obtener_programa(self.programa_id)
            if resultado.get('success'):
                programa = resultado['data']
                self.programa_label.setText(f"{programa['codigo']} - {programa['nombre']}")
                self.btn_limpiar_programa.setVisible(True)
                
        except Exception as e:
            logger.error(f"Error cargando programa: {e}")
    
    def _cargar_documentos(self):
        """Cargar documentos adjuntos de la transacción"""
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
    
    # ===== MÉTODOS DE VALIDACIÓN =====
    
    def validar_formulario(self):
        """Validar todos los campos del formulario"""
        errores = []
        
        # Validar fecha de pago
        fecha_pago = self.fecha_pago_input.date()
        if not fecha_pago.isValid():
            errores.append("La fecha de pago no es válida")
        
        # Validar monto total
        monto_total = self.monto_total_input.value()
        if monto_total <= 0:
            errores.append("El monto total debe ser mayor a 0")
        
        # Validar descuento
        descuento = self.descuento_input.value()
        if descuento < 0:
            errores.append("El descuento no puede ser negativo")
        
        # Validar monto final
        monto_final = monto_total - descuento
        if monto_final <= 0:
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
        """Obtener todos los datos del formulario"""
        datos = {
            'fecha_pago': self.fecha_pago_input.date().toString("yyyy-MM-dd"),
            'forma_pago': self.forma_pago_combo.currentText(),
            'monto_total': self.monto_total_input.value(),
            'descuento_total': self.descuento_input.value(),
            'monto_final': self.monto_total_input.value() - self.descuento_input.value(),
            'estado': self.estado_combo.currentText(),
            'numero_comprobante': self.numero_comprobante_input.text().strip() or None,
            'observaciones': self.observaciones_input.toPlainText().strip(),
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
    
    def clear_form(self):
        """Limpiar todos los campos del formulario"""
        self.transaccion_id = None
        self.estudiante_id = None
        self.programa_id = None
        self.detalles_transaccion = []
        self.documentos_adjuntos = []
        self.documentos_temp = []
        
        self.numero_transaccion_label.setText("(Generado automáticamente)")
        self.fecha_pago_input.setDate(QDate.currentDate())
        
        self.estudiante_label.setText("No seleccionado")
        self.btn_limpiar_estudiante.setVisible(False)
        
        self.programa_label.setText("No seleccionado")
        self.btn_limpiar_programa.setVisible(False)
        
        self.forma_pago_combo.setCurrentText("EFECTIVO")
        self.numero_comprobante_input.clear()
        self.banco_origen_input.clear()
        self.cuenta_origen_input.clear()
        self.transferencia_container.hide()
        
        self.monto_total_input.setValue(0.00)
        self.descuento_input.setValue(0.00)
        self._actualizar_total()
        
        self.estado_combo.setCurrentText("REGISTRADO")
        self.observaciones_input.clear()
        
        self.lista_documentos.clear()
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _seleccionar_estudiante(self):
        """Manejador para seleccionar estudiante"""
        # Aquí podrías abrir un diálogo para seleccionar estudiante
        # Por ahora, simularemos la selección
        from view.overlays.estudiante_overlay import EstudianteOverlay
        
        estudiante_overlay = EstudianteOverlay(self.parent())
        estudiante_overlay.estudiante_creado.connect(self._on_estudiante_seleccionado)
        estudiante_overlay.estudiante_actualizado.connect(self._on_estudiante_seleccionado)
        estudiante_overlay.show_form(solo_lectura=True, modo="seleccion")
    
    def _on_estudiante_seleccionado(self, datos_estudiante):
        """Manejador cuando se selecciona un estudiante"""
        if datos_estudiante and 'estudiante_id' in datos_estudiante:
            self.estudiante_id = datos_estudiante['estudiante_id']
            self._cargar_estudiante()
    
    def _limpiar_estudiante(self):
        """Limpiar selección de estudiante"""
        self.estudiante_id = None
        self.estudiante_label.setText("No seleccionado")
        self.btn_limpiar_estudiante.setVisible(False)
    
    def _seleccionar_programa(self):
        """Manejador para seleccionar programa"""
        # Aquí podrías abrir un diálogo para seleccionar programa
        # Por ahora, simularemos la selección
        from view.overlays.programa_overlay import ProgramaOverlay
        
        programa_overlay = ProgramaOverlay(self.parent())
        programa_overlay.programa_guardado.connect(self._on_programa_seleccionado)
        programa_overlay.programa_actualizado.connect(self._on_programa_seleccionado)
        programa_overlay.show_form(solo_lectura=True, modo="seleccion")
    
    def _on_programa_seleccionado(self, datos_programa):
        """Manejador cuando se selecciona un programa"""
        if datos_programa and 'id' in datos_programa:
            self.programa_id = datos_programa['id']
            self._cargar_programa()
    
    def _limpiar_programa(self):
        """Limpiar selección de programa"""
        self.programa_id = None
        self.programa_label.setText("No seleccionado")
        self.btn_limpiar_programa.setVisible(False)
    
    def _on_forma_pago_changed(self, forma_pago):
        """Manejador cuando cambia la forma de pago"""
        # Mostrar campos para transferencias si corresponde
        if forma_pago in ["TRANSFERENCIA", "DEPOSITO"]:
            self.transferencia_container.show()
        else:
            self.transferencia_container.hide()
    
    def _actualizar_total(self):
        """Actualizar montos calculados"""
        monto_total = self.monto_total_input.value()
        descuento = self.descuento_input.value()
        
        self.monto_total_label.setText(f"${monto_total:,.2f}")
        self.descuento_label.setText(f"${descuento:,.2f}")
        
        monto_final = monto_total - descuento
        if monto_final < 0:
            monto_final = 0
        
        self.monto_final_label.setText(f"${monto_final:,.2f}")
    
    def _agregar_documento(self):
        """Agregar documento adjunto"""
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
        """Eliminar documento seleccionado"""
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
        """Formatear tamaño de archivo para mostrar"""
        for unit in ['bytes', 'KB', 'MB', 'GB']:
            if bytes < 1024.0:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.1f} TB"