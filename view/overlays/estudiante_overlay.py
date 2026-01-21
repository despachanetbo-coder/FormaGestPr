# Archivo: view/overlays/estudiante_overlay.py
"""
Overlay para gestión de estudiantes (crear, editar, visualizar)
"""

import os
import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QPushButton,
    QFrame, QGroupBox, QScrollArea, QMessageBox, QSizePolicy,
    QSpacerItem, QTextEdit, QFileDialog, QDialog
)
from PySide6.QtCore import (
    Qt, Signal, QDate, QSize, QTimer, QPropertyAnimation,
    QEasingCurve
)
from PySide6.QtGui import (
    QFont, QPixmap, QPainter, QBrush, QColor, QPen,
    QCursor, QImage, QImageReader
)

# Importar componentes base y utilidades
from .base_overlay import BaseOverlay
from config.paths import Paths
from config.constants import ExpedicionCI, AppConstants, Messages
from utils.file_manager import FileManager
from model.estudiante_model import EstudianteModel
from controller.estudiante_controller import EstudianteController

logger = logging.getLogger(__name__)

class EstudianteOverlay(BaseOverlay):
    """
    Overlay para gestión de estudiantes
    """
    
    # Señales específicas
    estudiante_creado = Signal(dict)  # Datos del estudiante creado
    estudiante_actualizado = Signal(dict)  # Datos del estudiante actualizado
    estudiante_eliminado = Signal(int)  # ID del estudiante eliminado
    programa_inscrito = Signal(dict)  # Datos de inscripción a programa
    pago_registrado = Signal(dict)  # Datos de pago registrado
    apertura_visualizacion = Signal(int)  # ID del estudiante para visualizar
    
    def __init__(self, parent=None):
        """Inicializar overlay de estudiante"""
        super().__init__(
            parent=parent,
            titulo="👨‍🎓 Gestión de Estudiante",
            ancho_porcentaje=AppConstants.OVERLAY_WIDTH_PERCENT,
            alto_porcentaje=AppConstants.OVERLAY_HEIGHT_PERCENT
        )
        
        # Datos del estudiante
        self.estudiante_id = None
        self.datos_originales = {}
        self.foto_temp_path = None  # Ruta temporal de la foto seleccionada
        
        # Control de botones de visualización
        self.botones_visualizacion_creados = False
        self.botones_container = None
        
        # Configurar UI específica
        self.setup_estudiante_ui()
        
        # Configurar tamaño mínimo
        self.setMinimumSize(800, 600)
        
        logger.debug("✅ EstudianteOverlay inicializado")
    
    def setup_estudiante_ui(self):
        """Configurar UI específica para estudiante"""
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
        
        # ===== FILA 1: Datos Personales + Fotografía =====
        fila1_layout = QHBoxLayout()
        fila1_layout.setSpacing(20)
        fila1_layout.setContentsMargins(0, 0, 0, 0)
        
        # Contenedor para datos personales (70% del ancho)
        datos_container = QWidget()
        datos_container_layout = QVBoxLayout(datos_container)
        datos_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sección de datos personales
        self.setup_datos_personales_section(datos_container_layout)
        
        # Contenedor para foto (30% del ancho)
        foto_container = QWidget()
        foto_container_layout = QVBoxLayout(foto_container)
        foto_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sección de foto
        self.setup_foto_section(foto_container_layout)
        
        # Agregar a la fila 1
        fila1_layout.addWidget(datos_container, stretch=7)  # 70%
        fila1_layout.addWidget(foto_container, stretch=3)   # 30%
        
        content_layout.addLayout(fila1_layout)
        
        # ===== FILA 2: Contacto + Información Académica =====
        fila2_layout = QHBoxLayout()
        fila2_layout.setSpacing(20)
        fila2_layout.setContentsMargins(0, 0, 0, 0)
        
        # Contenedor para contacto (50% del ancho)
        contacto_container = QWidget()
        contacto_container_layout = QVBoxLayout(contacto_container)
        contacto_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sección de contacto
        self.setup_contacto_section(contacto_container_layout)
        
        # Contenedor para información académica (50% del ancho)
        academica_container = QWidget()
        academica_container_layout = QVBoxLayout(academica_container)
        academica_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sección de información académica/profesional
        self.setup_info_academica_section(academica_container_layout)
        
        # Agregar a la fila 2
        fila2_layout.addWidget(contacto_container, stretch=5)  # 50%
        fila2_layout.addWidget(academica_container, stretch=5)  # 50%
        
        content_layout.addLayout(fila2_layout)
        
        # Espaciador
        content_layout.addStretch()
        
        # Configurar scroll area
        scroll_area.setWidget(content_widget)
        
        # Agregar al área de contenido principal
        self.content_layout.addWidget(scroll_area)
        
        # Personalizar botones según modo
        self.btn_guardar.setText("💾 GUARDAR ESTUDIANTE")
        self.btn_cancelar.setText("❌ CANCELAR")
        
        # Asegurar que el botón cancelar esté conectado
        if hasattr(self, 'btn_cancelar'):
            self.btn_cancelar.clicked.connect(self.close_overlay)
    
    def setup_foto_section(self, parent_layout):
        """Configurar sección de fotografía"""
        # Grupo de foto
        foto_group = QGroupBox("📷 Fotografía del Estudiante")
        foto_group.setObjectName("fotoGroup")
        
        foto_layout = QVBoxLayout(foto_group)
        foto_layout.setSpacing(10)
        
        # Contenedor para foto y botones
        foto_container = QWidget()
        foto_container_layout = QHBoxLayout(foto_container)
        foto_container_layout.setSpacing(20)
        
        # Frame para mostrar la foto
        self.foto_frame = QFrame()
        self.foto_frame.setObjectName("fotoFrame")
        self.foto_frame.setFixedSize(206, 206)
        self.foto_frame.setStyleSheet("""
            #fotoFrame {
                background-color: #ecf0f1;
                border: 3px solid #3498db;
                border-radius: 8px;
            }
        """)
        
        # Label para la foto
        self.foto_label = QLabel()
        self.foto_label.setObjectName("fotoLabel")
        self.foto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.foto_label.setFixedSize(194, 194)
        self.foto_label.setStyleSheet("""
            #fotoLabel {
                border-radius: 5px;
            }
        """)
        
        # Crear layout para el frame y centrar el label
        frame_layout = QVBoxLayout(self.foto_frame)
        frame_layout.setContentsMargins(3, 3, 3, 3)
        frame_layout.addWidget(self.foto_label)
        
        # Cargar foto por defecto
        self.cargar_foto_por_defecto()
        
        # Contenedor para botones de foto
        foto_buttons_container = QWidget()
        foto_buttons_layout = QVBoxLayout(foto_buttons_container)
        foto_buttons_layout.setSpacing(10)
        
        # Botón para cambiar foto
        self.btn_cambiar_foto = QPushButton("📁 Cambiar\nFoto")
        self.btn_cambiar_foto.setObjectName("btnCambiarFoto")
        self.btn_cambiar_foto.setStyleSheet("""
            #btnCambiarFoto {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                border: none;
                min-height: 45px;
            }
            #btnCambiarFoto:hover {
                background-color: #2980b9;
            }
        """)
        self.btn_cambiar_foto.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cambiar_foto.clicked.connect(self._on_cambiar_foto)
        
        # Botón para eliminar foto
        self.btn_eliminar_foto = QPushButton("🗑️ Eliminar\nFoto")
        self.btn_eliminar_foto.setObjectName("btnEliminarFoto")
        self.btn_eliminar_foto.setStyleSheet("""
            #btnEliminarFoto {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                padding: 12px;
                border-radius: 6px;
                border: none;
                min-height: 45px;
            }
            #btnEliminarFoto:hover {
                background-color: #c0392b;
            }
        """)
        self.btn_eliminar_foto.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_eliminar_foto.clicked.connect(self._on_eliminar_foto)
        
        # Información de la foto
        self.foto_info_label = QLabel("Tamaño máximo: 5MB\nFormatos: JPG, JPEG, PNG")
        self.foto_info_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        self.foto_info_label.setWordWrap(True)
        
        # Agregar botones al layout
        foto_buttons_layout.addWidget(self.btn_cambiar_foto)
        foto_buttons_layout.addWidget(self.btn_eliminar_foto)
        foto_buttons_layout.addWidget(self.foto_info_label)
        foto_buttons_layout.addStretch()
        
        # Agregar al contenedor principal
        foto_container_layout.addWidget(self.foto_frame)
        foto_container_layout.addWidget(foto_buttons_container)
        foto_container_layout.addStretch()
        
        # Agregar al layout del grupo
        foto_layout.addWidget(foto_container)
        
        # Agregar al layout padre
        parent_layout.addWidget(foto_group)
    
    def setup_datos_personales_section(self, parent_layout):
        """Configurar sección de datos personales"""
        # Grupo de datos personales
        datos_group = QGroupBox("👤 Datos Personales")
        datos_group.setObjectName("datosGroup")
        
        datos_layout = QGridLayout(datos_group)
        datos_layout.setSpacing(15)
        datos_layout.setColumnStretch(1, 1)
        
        # Fila 1: CI Número y Expedición
        datos_layout.addWidget(QLabel("CI Número*:"), 0, 0)
        self.ci_input = QLineEdit()
        self.ci_input.setPlaceholderText("Ej: 1234567")
        self.ci_input.setMaximumWidth(200)
        datos_layout.addWidget(self.ci_input, 0, 1)
        
        datos_layout.addWidget(QLabel("Expedición*:"), 0, 2)
        self.expedicion_combo = QComboBox()
        self.expedicion_combo.addItems(ExpedicionCI.get_codes())
        self.expedicion_combo.setCurrentText("LP")  # Valor por defecto
        self.expedicion_combo.setMaximumWidth(100)
        datos_layout.addWidget(self.expedicion_combo, 0, 3)
        
        # Fila 2: Nombres
        datos_layout.addWidget(QLabel("Nombres*:"), 1, 0)
        self.nombres_input = QLineEdit()
        self.nombres_input.setPlaceholderText("Ej: Juan Carlos")
        datos_layout.addWidget(self.nombres_input, 1, 1, 1, 3)
        
        # Fila 3: Apellido Paterno
        datos_layout.addWidget(QLabel("Apellido Paterno*:"), 2, 0)
        self.apellido_paterno_input = QLineEdit()
        self.apellido_paterno_input.setPlaceholderText("Ej: Pérez")
        datos_layout.addWidget(self.apellido_paterno_input, 2, 1, 1, 3)
        
        # Fila 4: Apellido Materno
        datos_layout.addWidget(QLabel("Apellido Materno:"), 3, 0)
        self.apellido_materno_input = QLineEdit()
        self.apellido_materno_input.setPlaceholderText("Ej: González")
        datos_layout.addWidget(self.apellido_materno_input, 3, 1, 1, 3)
        
        # Fila 5: Fecha de Nacimiento
        datos_layout.addWidget(QLabel("Fecha Nacimiento:"), 4, 0)
        self.fecha_nacimiento_input = QDateEdit()
        self.fecha_nacimiento_input.setCalendarPopup(True)
        self.fecha_nacimiento_input.setDate(QDate.currentDate().addYears(-20))  # 20 años por defecto
        self.fecha_nacimiento_input.setMaximumWidth(150)
        datos_layout.addWidget(self.fecha_nacimiento_input, 4, 1)
        
        # Espaciador
        datos_layout.addWidget(QLabel(""), 4, 2, 1, 2)
        
        parent_layout.addWidget(datos_group)
    
    def setup_contacto_section(self, parent_layout):
        """Configurar sección de contacto"""
        # Grupo de contacto
        contacto_group = QGroupBox("📞 Información de Contacto")
        contacto_group.setObjectName("contactoGroup")
        
        contacto_layout = QGridLayout(contacto_group)
        contacto_layout.setSpacing(15)
        contacto_layout.setColumnStretch(1, 1)
        
        # Fila 1: Teléfono
        contacto_layout.addWidget(QLabel("Teléfono:"), 0, 0)
        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("Ej: 77712345")
        self.telefono_input.setMaximumWidth(200)
        contacto_layout.addWidget(self.telefono_input, 0, 1)
        
        # Fila 2: Email
        contacto_layout.addWidget(QLabel("Email:"), 1, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ej: estudiante@email.com")
        contacto_layout.addWidget(self.email_input, 1, 1, 1, 3)
        
        # Fila 3: Dirección
        contacto_layout.addWidget(QLabel("Dirección:"), 2, 0)
        self.direccion_input = QTextEdit()
        self.direccion_input.setMaximumHeight(40)
        self.direccion_input.setPlaceholderText("Ingrese la dirección completa...")
        contacto_layout.addWidget(self.direccion_input, 2, 1, 1, 3)
        
        parent_layout.addWidget(contacto_group)
    
    def setup_info_academica_section(self, parent_layout):
        """Configurar sección de información académica/profesional"""
        # Grupo de información académica
        academica_group = QGroupBox("🎓 Información Académica/Profesional")
        academica_group.setObjectName("academicaGroup")
        
        academica_layout = QGridLayout(academica_group)
        academica_layout.setSpacing(15)
        academica_layout.setColumnStretch(1, 1)
        
        # Fila 1: Profesión
        academica_layout.addWidget(QLabel("Profesión:"), 0, 0)
        self.profesion_input = QLineEdit()
        self.profesion_input.setPlaceholderText("Ej: Licenciado en Administración de Empresas")
        academica_layout.addWidget(self.profesion_input, 0, 1, 1, 3)
        
        # Fila 2: Universidad
        academica_layout.addWidget(QLabel("Universidad:"), 1, 0)
        self.universidad_input = QLineEdit()
        self.universidad_input.setPlaceholderText("Ej: Universidad Autónoma Tomás Frías")
        academica_layout.addWidget(self.universidad_input, 1, 1, 1, 3)
        
        # Fila 3: Estado
        academica_layout.addWidget(QLabel("Estado:"), 2, 0)
        self.estado_combo = QComboBox()
        self.estado_combo.addItems(["ACTIVO", "INACTIVO"])
        self.estado_combo.setCurrentText("ACTIVO")
        self.estado_combo.setMaximumWidth(150)
        academica_layout.addWidget(self.estado_combo, 2, 1)
        
        # Espaciador para completar la fila
        academica_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum), 2, 2, 1, 2)
        
        parent_layout.addWidget(academica_group)
    
    def cargar_foto_por_defecto(self):
        """Cargar foto por defecto en el label"""
        pixmap = FileManager.obtener_foto_por_defecto("estudiante")
        self.foto_label.setPixmap(pixmap)
    
    def cargar_foto_estudiante(self, ruta_bd: str):
        """
        Cargar foto de estudiante desde ruta de BD
        
        Args:
            ruta_bd: Ruta almacenada en base de datos
        """
        if not ruta_bd or ruta_bd.strip() == "":
            self.cargar_foto_por_defecto()
            return
        
        pixmap = FileManager.cargar_foto_estudiante(
            ruta_bd, 
            self.foto_label.width(),
            self.foto_label.height()
        )
        
        if pixmap:
            self.foto_label.setPixmap(pixmap)
        else:
            self.cargar_foto_por_defecto()
    
    def _on_cambiar_foto(self):
        """Manejador para cambiar foto"""
        # Abrir diálogo para seleccionar imagen
        archivo = FileManager.seleccionar_imagen(self, "Seleccionar foto de estudiante")
        
        if archivo:
            # Cargar la imagen seleccionada temporalmente
            pixmap = QPixmap(archivo)
            if not pixmap.isNull():
                # Redimensionar para mostrar en el preview
                pixmap = pixmap.scaled(
                    self.foto_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.foto_label.setPixmap(pixmap)
                self.foto_temp_path = archivo
                
                logger.info(f"Foto seleccionada: {archivo}")
    
    def _on_eliminar_foto(self):
        """Manejador para eliminar foto"""
        respuesta = QMessageBox.question(
            self,
            "Eliminar foto",
            "¿Está seguro que desea eliminar la foto del estudiante?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            self.cargar_foto_por_defecto()
            self.foto_temp_path = None
            
            # Si estamos editando un estudiante, marcar para eliminar la foto existente
            if self.estudiante_id:
                self.foto_a_eliminar = True
    
    def set_modo(self, modo: str, estudiante_id: Optional [int] = None):
        """
        Establecer modo de operación
        
        Args:
            modo: 'nuevo', 'editar', 'visualizar'
            estudiante_id: ID del estudiante (para editar/visualizar)
        """
        # Limpiar botones de visualización previos si existen
        self.eliminar_botones_visualizacion()

        self.modo = modo
        self.estudiante_id = estudiante_id
        
        # Configurar título según modo
        if modo == "nuevo":
            self.set_titulo("👨‍🎓 Nuevo Estudiante - Registro")
            self.clear_form()
            self.habilitar_campos(True)
            self.btn_guardar.setText("💾 GUARDAR ESTUDIANTE")
            self.btn_cancelar.setText("❌ CANCELAR REGISTRO")
            
        elif modo == "editar" and estudiante_id:
            self.set_titulo(f"👨‍🎓 Editar Estudiante - ID: {estudiante_id}")
            self.cargar_datos_estudiante(estudiante_id)
            self.habilitar_campos(True)
            self.btn_guardar.setText("💾 ACTUALIZAR ESTUDIANTE")
            self.btn_cancelar.setText("❌ CANCELAR CAMBIOS")
            
        elif modo == "visualizar" and estudiante_id:
            self.set_titulo(f"👁️ Ver Estudiante - ID: {estudiante_id}")
            self.cargar_datos_estudiante(estudiante_id)
            self.habilitar_campos(False)
            self.btn_guardar.setVisible(False)
            self.btn_cancelar.setText("👈 CERRAR VENTANA")
            
            # Agregar botones adicionales para modo visualización
            self.setup_botones_visualizacion()
    
    def eliminar_botones_visualizacion(self):
        """Eliminar botones de visualización si existen"""
        if self.botones_container:
            # Eliminar el widget contenedor del layout
            self.content_layout.removeWidget(self.botones_container)
            # Eliminar el widget
            self.botones_container.deleteLater()
            self.botones_container = None
        
        self.botones_visualizacion_creados = False
        logger.debug("✅ Botones de visualización eliminados")
    
    def setup_botones_visualizacion(self):
        """Configurar botones adicionales para modo visualización"""
        # Si ya se crearon, no crear de nuevo
        if self.botones_visualizacion_creados and self.botones_container:
            logger.debug("✅ Botones de visualización ya existen, omitiendo creación")
            return
        
        # Marcar que se crearán
        self.botones_visualizacion_creados = True
        
        # Crear layout horizontal para botones adicionales
        botones_layout = QHBoxLayout()
        botones_layout.setSpacing(10)
        
        # Botón: Ver estado de inscripción
        btn_ver_inscripciones = QPushButton("📚 Ver Inscripciones")
        btn_ver_inscripciones.setObjectName("btnVerInscripciones")
        btn_ver_inscripciones.setStyleSheet("""
            #btnVerInscripciones {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            #btnVerInscripciones:hover {
                background-color: #2980b9;
            }
        """)
        btn_ver_inscripciones.clicked.connect(self._on_ver_inscripciones)
        
        # Botón: Ver historial de pagos
        btn_ver_pagos = QPushButton("💰 Ver Historial de Pagos")
        btn_ver_pagos.setObjectName("btnVerPagos")
        btn_ver_pagos.setStyleSheet("""
            #btnVerPagos {
                background-color: #2ecc71;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            #btnVerPagos:hover {
                background-color: #27ae60;
            }
        """)
        btn_ver_pagos.clicked.connect(self._on_ver_pagos)
        
        # Botón: Editar estudiante
        btn_editar = QPushButton("✏️ Editar Estudiante")
        btn_editar.setObjectName("btnEditar")
        btn_editar.setStyleSheet("""
            #btnEditar {
                background-color: #f39c12;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                border: none;
            }
            #btnEditar:hover {
                background-color: #d35400;
            }
        """)
        btn_editar.clicked.connect(self._on_editar_desde_visualizacion)
        
        # Agregar botones al layout
        botones_layout.addWidget(btn_ver_inscripciones)
        botones_layout.addWidget(btn_ver_pagos)
        botones_layout.addWidget(btn_editar)
        botones_layout.addStretch()
        
        # Crear widget contenedor
        self.botones_container = QWidget()
        self.botones_container.setObjectName("botonesVisualizacionContainer")
        self.botones_container.setLayout(botones_layout)
        
        # Insertar antes del footer (penúltima posición)
        footer_index = self.content_layout.count() - 1
        self.content_layout.insertWidget(footer_index, self.botones_container)
        
        logger.debug("✅ Botones de visualización creados")
    
    def habilitar_campos(self, habilitar: bool):
        """Habilitar o deshabilitar todos los campos del formulario"""
        campos = [
            self.ci_input, self.expedicion_combo,
            self.nombres_input, self.apellido_paterno_input,
            self.apellido_materno_input, self.fecha_nacimiento_input,
            self.telefono_input, self.email_input,
            self.direccion_input, self.profesion_input,
            self.universidad_input, self.estado_combo,
            self.btn_cambiar_foto, self.btn_eliminar_foto
        ]
        
        for campo in campos:
            campo.setEnabled(habilitar)
    
    def cargar_datos_estudiante(self, estudiante_id: int):
        """
        Cargar datos del estudiante en el formulario
        
        Args:
            estudiante_id: ID del estudiante
        """
        try:
            # Obtener datos del estudiante
            estudiante = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
            
            if not estudiante:
                self.mostrar_mensaje("Error", f"No se encontró el estudiante con ID {estudiante_id}", "error")
                return
            
            # Guardar datos originales
            self.datos_originales = estudiante.copy()
            
            # Cargar datos en los campos
            self.ci_input.setText(estudiante.get('ci_numero', ''))
            
            expedicion = estudiante.get('ci_expedicion', 'LP')
            if expedicion in ExpedicionCI.get_codes():
                self.expedicion_combo.setCurrentText(expedicion)
            
            self.nombres_input.setText(estudiante.get('nombres', ''))
            self.apellido_paterno_input.setText(estudiante.get('apellido_paterno', ''))
            self.apellido_materno_input.setText(estudiante.get('apellido_materno', ''))
            
            # Fecha de nacimiento
            fecha_nacimiento = estudiante.get('fecha_nacimiento')
            if fecha_nacimiento:
                if isinstance(fecha_nacimiento, str):
                    fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                if isinstance(fecha_nacimiento, date):
                    qdate = QDate(fecha_nacimiento.year, fecha_nacimiento.month, fecha_nacimiento.day)
                    self.fecha_nacimiento_input.setDate(qdate)
            
            # Contacto
            self.telefono_input.setText(estudiante.get('telefono', ''))
            self.email_input.setText(estudiante.get('email', ''))
            self.direccion_input.setPlainText(estudiante.get('direccion', ''))
            
            # Información académica
            self.profesion_input.setText(estudiante.get('profesion', ''))
            self.universidad_input.setText(estudiante.get('universidad', ''))
            
            # Estado
            estado = "ACTIVO" if estudiante.get('activo', True) else "INACTIVO"
            self.estado_combo.setCurrentText(estado)
            
            # Cargar foto
            fotografia_url = estudiante.get('fotografia_url', '')
            if fotografia_url:
                self.cargar_foto_estudiante(fotografia_url)
            else:
                self.cargar_foto_por_defecto()
            
            logger.info(f"Datos del estudiante {estudiante_id} cargados en formulario")
            
        except Exception as e:
            logger.error(f"Error cargando datos del estudiante: {e}")
            self.mostrar_mensaje("Error", f"No se pudieron cargar los datos: {str(e)}", "error")
    
    def clear_form(self):
        """Limpiar todos los campos del formulario"""
        self.ci_input.clear()
        self.expedicion_combo.setCurrentText("LP")
        self.nombres_input.clear()
        self.apellido_paterno_input.clear()
        self.apellido_materno_input.clear()
        
        # Fecha por defecto: 20 años atrás
        fecha_default = QDate.currentDate().addYears(-20)
        self.fecha_nacimiento_input.setDate(fecha_default)
        
        self.telefono_input.clear()
        self.email_input.clear()
        self.direccion_input.clear()
        self.profesion_input.clear()
        self.universidad_input.clear()
        self.estado_combo.setCurrentText("ACTIVO")
        
        self.cargar_foto_por_defecto()
        self.foto_temp_path = None
        
        # Resetear estudiante_id y datos
        self.estudiante_id = None
        self.datos_originales = {}
        
        # Eliminar botones de visualización si existen
        self.eliminar_botones_visualizacion()
        
        # Restaurar visibilidad del botón guardar
        self.btn_guardar.setVisible(True)
    
    def validar_formulario(self):
        """
        Validar todos los campos del formulario
        
        Returns:
            tuple: (valido, lista_errores)
        """
        errores = []
        
        # Validar CI
        ci_numero = self.ci_input.text().strip()
        if not ci_numero:
            errores.append("El número de CI es obligatorio")
        elif not ci_numero.isdigit():
            errores.append("El CI debe contener solo números")
        elif len(ci_numero) < 5 or len(ci_numero) > 15:
            errores.append("El CI debe tener entre 5 y 15 dígitos")
        
        # Validar expedición
        expedicion = self.expedicion_combo.currentText()
        if not expedicion or expedicion not in ExpedicionCI.get_codes():
            errores.append("La expedición del CI es inválida")
        
        # Validar nombres
        nombres = self.nombres_input.text().strip()
        if not nombres:
            errores.append("Los nombres son obligatorios")
        elif len(nombres) < 2:
            errores.append("Los nombres deben tener al menos 2 caracteres")
        
        # Validar apellido paterno
        apellido_paterno = self.apellido_paterno_input.text().strip()
        if not apellido_paterno:
            errores.append("El apellido paterno es obligatorio")
        elif len(apellido_paterno) < 2:
            errores.append("El apellido paterno debe tener al menos 2 caracteres")
        
        # Validar email si se proporciona
        email = self.email_input.text().strip()
        if email:
            if '@' not in email or '.' not in email:
                errores.append("El formato del email no es válido")
            elif len(email) > AppConstants.MAX_EMAIL_LENGTH:
                errores.append(f"El email no puede exceder {AppConstants.MAX_EMAIL_LENGTH} caracteres")
        
        # Validar teléfono si se proporciona
        telefono = self.telefono_input.text().strip()
        if telefono:
            if len(telefono) > AppConstants.MAX_TELEFONO_LENGTH:
                errores.append(f"El teléfono no puede exceder {AppConstants.MAX_TELEFONO_LENGTH} caracteres")
        
        # Validar fecha de nacimiento
        fecha_nacimiento = self.fecha_nacimiento_input.date()
        hoy = QDate.currentDate()
        edad = hoy.year() - fecha_nacimiento.year()
        
        if edad < 16:
            errores.append("El estudiante debe tener al menos 16 años")
        elif edad > 120:
            errores.append("La edad no es válida")
        
        logger.info(f"DEBUG - Validación final: valido={len(errores) == 0}, errores={errores}")
        return len(errores) == 0, errores
    
    def obtener_datos(self):
        """
        Obtener datos del formulario
        
        Returns:
            dict: Datos del estudiante
        """
        datos = {
            'ci_numero': self.ci_input.text().strip(),
            'ci_expedicion': self.expedicion_combo.currentText(),
            'nombres': self.nombres_input.text().strip(),
            'apellido_paterno': self.apellido_paterno_input.text().strip(),
            'apellido_materno': self.apellido_materno_input.text().strip(),
            'telefono': self.telefono_input.text().strip(),
            'email': self.email_input.text().strip(),
            'direccion': self.direccion_input.toPlainText().strip(),
            'profesion': self.profesion_input.text().strip(),
            'universidad': self.universidad_input.text().strip(),
            'activo': self.estado_combo.currentText() == "ACTIVO"
        }
        
        # Fecha de nacimiento
        fecha_qdate = self.fecha_nacimiento_input.date()
        datos['fecha_nacimiento'] = fecha_qdate.toString(Qt.DateFormat.ISODate)
        
        logger.info(f"DEBUG - Datos completos: {datos}")
        
        # Manejo de foto
        datos['foto_temp_path'] = self.foto_temp_path
        datos['foto_a_eliminar'] = getattr(self, 'foto_a_eliminar', False)
        
        # Información adicional
        datos['modo'] = self.modo
        datos['estudiante_id'] = self.estudiante_id
        
        return datos
    
    def _on_guardar_clicked(self):
        """Manejador para guardar estudiante"""
        logger.info("=" * 80)
        logger.info("DEBUG - _on_guardar_clicked: Iniciando guardado de estudiante")
        
        # En modo visualización, cerrar overlay
        if self.modo == "visualizar":
            self.close_overlay()
            return
        
        # Validar formulario
        logger.info("DEBUG - Validando formulario...")
        valido, errores = self.validar_formulario()
        logger.info(f"DEBUG - Validación: valido={valido}, errores={errores}")
        
        if not valido:
            mensaje = "Por favor corrija los siguientes errores:\n\n• " + "\n• ".join(errores)
            self.mostrar_mensaje("Validación", mensaje, "error")
            return
        
        # Obtener datos del formulario
        logger.info("DEBUG - Obteniendo datos del formulario...")
        datos = self.obtener_datos()
        logger.info(f"DEBUG - Datos obtenidos: {datos}")
        
        try:
            resultado = None
            
            if self.modo == "nuevo":
                logger.info("DEBUG - Modo NUEVO, llamando a crear_estudiante...")
                # Crear nuevo estudiante
                resultado = self.crear_estudiante(datos)
                
                if resultado['success']:
                    estudiante_id = resultado['data']['id']
                    # Emitir señal con el ID del nuevo estudiante
                    self.estudiante_creado.emit({'estudiante_id': estudiante_id, 'datos': resultado['data']})
                    self.mostrar_mensaje("Éxito", "Estudiante creado exitosamente (ID: {estudiante_id})", "success")
                    
                    # Cerrar overlay después de guardar
                    self.close_overlay()
                else:
                    self.mostrar_mensaje("Error", resultado.get('message', 'Error desconocido'), "error")
            elif self.modo == "editar":
                logger.info("DEBUG - Modo EDITAR, llamando a actualizar_estudiante...")
                # Actualizar estudiante existente
                resultado = self.actualizar_estudiante(datos)
                
                if resultado['success']:
                    estudiante_id = self.estudiante_id
                    # Emitir señal con el ID del estudiante actualizado
                    self.estudiante_actualizado.emit({'estudiante_id': estudiante_id, 'datos': resultado['data']})
                    self.mostrar_mensaje("Éxito", "Estudiante actualizado exitosamente (ID: {estudiante_id})", "success")
                    
                    # Cerrar overlay después de guardar
                    self.close_overlay()
        except Exception as e:
            logger.error(f"Error guardando estudiante: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.mostrar_mensaje("Error", f"No se pudo guardar el estudiante: {str(e)}", "error")
    
    def crear_estudiante(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo estudiante
        
        Args:
            datos: Datos del estudiante
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            # 1. Primero copiar la foto si existe
            ruta_foto = None
            if datos.get('foto_temp_path'):
                ci_numero = datos['ci_numero']
                ci_expedicion = datos['ci_expedicion']
                
                # Copiar foto al directorio de fotos
                exito, mensaje, ruta_foto = FileManager.copiar_foto_estudiante(
                    datos['foto_temp_path'],
                    ci_numero,
                    ci_expedicion
                )
                
                if exito:
                    logger.info(f"✅ Foto copiada exitosamente: {ruta_foto}")
                else:
                    logger.warning(f"❌ No se pudo copiar la foto: {mensaje}")
                    ruta_foto = None
            
            # 2. Preparar datos para la base de datos
            datos_bd = {
                'ci_numero': datos['ci_numero'],
                'ci_expedicion': datos['ci_expedicion'],
                'nombres': datos['nombres'],
                'apellido_paterno': datos['apellido_paterno'],
                'apellido_materno': datos.get('apellido_materno', ''),
                'fecha_nacimiento': datos['fecha_nacimiento'],
                'telefono': datos.get('telefono', ''),
                'email': datos.get('email', ''),
                'direccion': datos.get('direccion', ''),
                'profesion': datos.get('profesion', ''),
                'universidad': datos.get('universidad', ''),
                'activo': datos.get('activo', True)
            }
            
            # 3. Agregar ruta de foto si existe
            if ruta_foto:
                datos_bd['fotografia_url'] = ruta_foto
                logger.info(f"DEBUG - Añadiendo ruta de foto a datos: {ruta_foto}")
            else:
                logger.info("DEBUG - No hay ruta de foto para añadir")
            
            # 4. Usar el controlador para crear el estudiante
            resultado = EstudianteController.crear_estudiante(datos_bd)
            
            if resultado['success']:
                estudiante_id = resultado['data']['id']
                logger.info(f"✅ Estudiante creado en BD - ID: {estudiante_id}")
                
                # 5. Si la foto se copió pero no se pudo incluir en la creación,
                # intentar actualizar como fallback
                if ruta_foto and not datos_bd.get('fotografia_url'):
                    EstudianteModel.actualizar_estudiante(estudiante_id, {'fotografia_url': ruta_foto})
                
                resultado['data']['estudiante_id'] = estudiante_id
                
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Error creando estudiante: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'message': f"Error al crear estudiante: {str(e)}"
            }
    
    def actualizar_estudiante(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar estudiante existente
        
        Args:
            datos: Datos del estudiante
        
        Returns:
            dict: Resultado de la operación
        """
        try:
            estudiante_id = self.estudiante_id
            
            # Preparar datos para actualizar
            datos_actualizar = {
                'ci_numero': datos['ci_numero'],
                'ci_expedicion': datos['ci_expedicion'],
                'nombres': datos['nombres'],
                'apellido_paterno': datos['apellido_paterno'],
                'apellido_materno': datos['apellido_materno'],
                'fecha_nacimiento': datos['fecha_nacimiento'],
                'telefono': datos['telefono'],
                'email': datos['email'],
                'direccion': datos['direccion'],
                'profesion': datos['profesion'],
                'universidad': datos['universidad'],
                'activo': datos['activo']
            }
            
            # Manejar foto
            if datos.get('foto_a_eliminar', False):
                # Eliminar foto existente
                ci_numero = datos['ci_numero']
                ci_expedicion = datos['ci_expedicion']
                FileManager.eliminar_foto_estudiante(ci_numero, ci_expedicion)
                datos_actualizar['fotografia_url'] = None
                
            elif datos.get('foto_temp_path'):
                # Copiar nueva foto
                ci_numero = datos['ci_numero']
                ci_expedicion = datos['ci_expedicion']
                
                exito, mensaje, ruta_foto = FileManager.copiar_foto_estudiante(
                    datos['foto_temp_path'],
                    ci_numero,
                    ci_expedicion
                )
                
                if exito:
                    datos_actualizar['fotografia_url'] = ruta_foto
                else:
                    logger.warning(f"No se pudo actualizar la foto: {mensaje}")
            
            # Usar el controlador para actualizar
            if not estudiante_id:
                raise ValueError("ID del estudiante no proporcionado para actualización")
            resultado = EstudianteController.actualizar_estudiante(estudiante_id, datos_actualizar)
            
            if resultado['success']:
                resultado['data']['estudiante_id'] = estudiante_id
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error actualizando estudiante: {e}")
            return {
                'success': False,
                'message': f"Error al actualizar estudiante: {str(e)}"
            }
    
    def _on_ver_inscripciones(self):
        """Manejador simplificado para ver inscripciones del estudiante"""
        if not self.estudiante_id:
            self.mostrar_mensaje("Error", "No hay estudiante seleccionado", "error")
            return
        
        try:
            # OPCIÓN MÁS SIMPLE: Usar self como parent (debería funcionar)
            # Los overlays son widgets modales/dialogos, pueden tener self como parent
            from view.overlays.inscripcion_overlay import InscripcionOverlay
            
            # Crear el overlay usando self como parent
            inscripcion_overlay = InscripcionOverlay(self)
            
            # Configurar
            inscripcion_overlay.show_form(
                solo_lectura=False,
                modo="nuevo",
                estudiante_id=self.estudiante_id
            )
            
            # Ocultar este overlay
            self.hide()
            
            # Conectar para volver cuando se cierre el overlay de inscripciones
            def volver_a_estudiante():
                self.show()
                if inscripcion_overlay:
                    try:
                        inscripcion_overlay.deleteLater()
                    except:
                        pass
                    
            # Usar la señal si existe, si no usar destroyed
            if hasattr(inscripcion_overlay, 'overlay_closed'):
                inscripcion_overlay.overlay_closed.connect(volver_a_estudiante)
            else:
                inscripcion_overlay.destroyed.connect(lambda: self.show())
            
            # Mostrar el nuevo overlay
            inscripcion_overlay.show()
            
            logger.debug(f"✅ InscripcionOverlay mostrado para estudiante {self.estudiante_id}")
            
        except Exception as e:
            logger.error(f"Error al mostrar inscripciones: {e}", exc_info=True)
            self.mostrar_mensaje("Error", f"Error al abrir inscripciones: {str(e)[:100]}", "error")
    
    def _get_main_window(self):
        """Obtener la ventana principal (main window)"""
        # Buscar recursivamente el widget principal
        parent = self.parent()
        while parent and not hasattr(parent, 'is_main_window'):
            parent = parent.parent()
            
        return parent if parent else None
    
    def _on_ver_pagos(self):
        """Manejador para ver historial de pagos"""
        if not self.estudiante_id:
            return
        
        self.mostrar_mensaje(
            "Historial de Pagos", 
            f"Funcionalidad para ver historial de pagos del estudiante ID: {self.estudiante_id}\n\n"
            "Esta funcionalidad estará disponible en futuras actualizaciones.",
            "info"
        )
    
    def _on_editar_desde_visualizacion(self):
        """Manejador para cambiar a modo edición desde visualización"""
        if not self.estudiante_id:
            return
        
        self.set_modo("editar", self.estudiante_id)
    
    def show_form(self, solo_lectura=False, datos_estudiante=None, estudiante_id=None):
        """Mostrar el overlay"""
        # Configurar según modo
        if self.modo == "visualizar":
            self.solo_lectura = True
            self.set_titulo(f"👁️ Ver Estudiante - ID: {self.estudiante_id}")
            self.habilitar_campos(False)
            self.btn_guardar.setVisible(False)
            self.btn_cancelar.setText("👈 CERRAR VENTANA")
        else:
            self.solo_lectura = solo_lectura
        
        # Llamar al método base
        super().show_form(solo_lectura)
    
    def close_overlay(self):
        """Cerrar el overlay y limpiar recursos"""
        # Eliminar botones de visualización
        self.eliminar_botones_visualizacion()
        
        # Resetear variables
        self.estudiante_id = None
        self.datos_originales = {}
        self.foto_temp_path = None
        self.botones_visualizacion_creados = False
        self.botones_container = None
        
        # Llamar al método base
        super().close_overlay()