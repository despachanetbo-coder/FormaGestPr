# view/overlays/docente_overlay.py
"""
Overlay para gestión de docentes con funcionalidades CRUD,
carga de CV PDF y vista previa. Hereda de BaseOverlay.
"""
import os
import tempfile
import logging  # <-- AGREGAR ESTA LÍNEA
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QDateEdit, QTextEdit, QFrame, QScrollArea, QGridLayout,
    QFileDialog, QMessageBox, QGroupBox, QSizePolicy, QProgressBar,
    QSplitter, QCheckBox, QDoubleSpinBox, QSpinBox, QTabWidget, QTextBrowser
)
from PySide6.QtCore import Qt, QDate, QTimer, QSize, Signal
from PySide6.QtGui import (QFont, QPixmap, QIcon, QIntValidator, 
    QDoubleValidator, QImage, QPixmap, QImage)

# Importar modelo
from model.docente_model import DocenteModel

# Importar estilos y utilidades
from utils.validators import Validators

from .base_overlay import BaseOverlay

# Configurar logger
logger = logging.getLogger(__name__)  # <-- AGREGAR ESTO ANTES DE LA CLASE

class DocenteOverlay(BaseOverlay):
    """Overlay para crear/editar/ver docentes con vista previa de CV PDF"""
    
    EXPEDICIONES_CI = ["CB", "LP", "SC", "OR", "PT", "TJ", "PA", "BE", "CH"]
    GRADOS_ACADEMICOS = ["LIC.", "ING.", "M.Sc.", "Mg.", "MBA", "Ph.D.", "Dr."]
    
    # Señales especificas
    docente_creado = Signal(dict)
    docente_actualizado = Signal(dict)
    docente_eliminado = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent, "👨‍🏫 Gestión de Docente", 95, 95)
        
        # Variables específicas
        self.docente_id: Optional[int] = None
        self.original_data: Dict[str, Any] = {}
        self.pdf_path: Optional[str] = None
        self.cv_temp_path: Optional[str] = None
        
        # Variables para comparación
        self.original_ci: str = ""
        self.original_email: str = ""
        
        # Variables de estado
        self.cv_changed = False
        
        # Directorio para CVs
        self.cv_dir = "archivos/cv_docentes"
        os.makedirs(self.cv_dir, exist_ok=True)
        
        # Configurar UI específica
        self.setup_ui_especifica()
        self.setup_conexiones_especificas()
        self.setup_validators()
        
        logger.debug("✅ DocenteOverlay inicializado")
    
    def setup_ui_especifica(self):
        """Configurar la interfaz específica de docente"""
        # Limpiar layout de contenido base
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            widget = child.widget()
            if widget:
                widget.deleteLater()
        
        # Splitter para dos paneles
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")
        splitter.setChildrenCollapsible(False)
        
        # ===== PANEL IZQUIERDO: FORMULARIO =====
        scroll_formulario = QScrollArea()
        scroll_formulario.setWidgetResizable(True)
        scroll_formulario.setFrameShape(QFrame.Shape.NoFrame)
        
        widget_formulario = QWidget()
        layout_formulario = QVBoxLayout(widget_formulario)
        layout_formulario.setContentsMargins(5, 5, 10, 5)
        
        # Grupo: Datos Personales
        grupo_personales = self.crear_grupo_personales()
        layout_formulario.addWidget(grupo_personales)
        
        # Grupo: Datos Académicos
        grupo_academicos = self.crear_grupo_academicos()
        layout_formulario.addWidget(grupo_academicos)
        
        # Grupo: Contacto
        grupo_contacto = self.crear_grupo_contacto()
        layout_formulario.addWidget(grupo_contacto)
        
        layout_formulario.addStretch()
        
        scroll_formulario.setWidget(widget_formulario)
        
        # ===== PANEL DERECHO: VISTA PREVIA CV =====
        widget_preview = QWidget()
        layout_preview = QVBoxLayout(widget_preview)
        layout_preview.setContentsMargins(10, 5, 5, 5)
        
        # Grupo: Curriculum Vitae
        grupo_cv = self.crear_grupo_cv()
        layout_preview.addWidget(grupo_cv, 1)
        
        # Agregar al splitter
        splitter.addWidget(scroll_formulario)
        splitter.addWidget(widget_preview)
        
        # Configurar proporciones
        splitter.setSizes([600, 400])
        
        # Agregar splitter al layout de contenido
        self.content_layout.addWidget(splitter, 1)
    
    def crear_grupo_personales(self):
        """Crear grupo de datos personales"""
        grupo = QGroupBox("📋 DATOS PERSONALES")
        
        grid = QGridLayout(grupo)
        grid.setSpacing(10)
        grid.setContentsMargins(10, 15, 10, 10)
        
        # Fila 1: CI Número
        grid.addWidget(QLabel("CI Número:*"), 0, 0)
        self.ci_numero_input = QLineEdit()
        self.ci_numero_input.setPlaceholderText("Ej: 1234567")
        self.ci_numero_input.setMaxLength(15)
        grid.addWidget(self.ci_numero_input, 0, 1)
        
        # Fila 2: CI Expedición
        grid.addWidget(QLabel("Expedición CI:*"), 1, 0)
        self.ci_expedicion_combo = QComboBox()
        self.ci_expedicion_combo.addItems(self.EXPEDICIONES_CI)
        grid.addWidget(self.ci_expedicion_combo, 1, 1)
        
        # Fila 3: Nombres
        grid.addWidget(QLabel("Nombres:*"), 2, 0)
        self.nombres_input = QLineEdit()
        self.nombres_input.setPlaceholderText("Ej: Juan Carlos")
        grid.addWidget(self.nombres_input, 2, 1)
        
        # Fila 4: Apellido Paterno
        grid.addWidget(QLabel("Apellido Paterno:*"), 3, 0)
        self.apellido_paterno_input = QLineEdit()
        self.apellido_paterno_input.setPlaceholderText("Ej: Pérez")
        grid.addWidget(self.apellido_paterno_input, 3, 1)
        
        # Fila 5: Apellido Materno
        grid.addWidget(QLabel("Apellido Materno:"), 4, 0)
        self.apellido_materno_input = QLineEdit()
        self.apellido_materno_input.setPlaceholderText("Ej: López")
        grid.addWidget(self.apellido_materno_input, 4, 1)
        
        # Fila 6: Fecha Nacimiento
        grid.addWidget(QLabel("Fecha Nacimiento:"), 5, 0)
        self.fecha_nacimiento_date = QDateEdit()
        self.fecha_nacimiento_date.setCalendarPopup(True)
        self.fecha_nacimiento_date.setDate(QDate.currentDate().addYears(-30))
        self.fecha_nacimiento_date.setDisplayFormat("dd/MM/yyyy")
        grid.addWidget(self.fecha_nacimiento_date, 5, 1)
        
        return grupo
    
    def crear_grupo_academicos(self):
        """Crear grupo de datos académicos"""
        grupo = QGroupBox("🎓 DATOS ACADÉMICOS")
        
        grid = QGridLayout(grupo)
        grid.setSpacing(10)
        grid.setContentsMargins(10, 15, 10, 10)
        
        # Fila 1: Grado Académico
        grid.addWidget(QLabel("Grado Académico:"), 0, 0)
        self.grado_academico_combo = QComboBox()
        self.grado_academico_combo.addItems(self.GRADOS_ACADEMICOS)
        grid.addWidget(self.grado_academico_combo, 0, 1)
        
        # Fila 2: Título Profesional
        grid.addWidget(QLabel("Título Profesional:"), 1, 0)
        self.titulo_profesional_input = QLineEdit()
        self.titulo_profesional_input.setPlaceholderText("Ej: Ingeniero de Sistemas")
        grid.addWidget(self.titulo_profesional_input, 1, 1)
        
        # Fila 3: Especialidad
        grid.addWidget(QLabel("Especialidad:"), 2, 0)
        self.especialidad_input = QLineEdit()
        self.especialidad_input.setPlaceholderText("Ej: Inteligencia Artificial")
        grid.addWidget(self.especialidad_input, 2, 1)
        
        return grupo
    
    def crear_grupo_contacto(self):
        """Crear grupo de contacto"""
        grupo = QGroupBox("📞 INFORMACIÓN DE CONTACTO")
        
        grid = QGridLayout(grupo)
        grid.setSpacing(10)
        grid.setContentsMargins(10, 15, 10, 10)
        
        # Fila 1: Teléfono
        grid.addWidget(QLabel("Teléfono:"), 0, 0)
        self.telefono_input = QLineEdit()
        self.telefono_input.setPlaceholderText("Ej: 77712345")
        grid.addWidget(self.telefono_input, 0, 1)
        
        # Fila 2: Email
        grid.addWidget(QLabel("Email:"), 1, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Ej: docente@unsxx.edu.bo")
        grid.addWidget(self.email_input, 1, 1)
        
        # Fila 3: Honorario por Hora
        grid.addWidget(QLabel("Honorario/Hora (Bs):"), 2, 0)
        self.honorario_hora_spin = QDoubleSpinBox()
        self.honorario_hora_spin.setRange(0, 10000)
        self.honorario_hora_spin.setDecimals(2)
        self.honorario_hora_spin.setSuffix(" Bs")
        self.honorario_hora_spin.setValue(50.00)
        grid.addWidget(self.honorario_hora_spin, 2, 1)
        
        # Fila 4: Activo
        grid.addWidget(QLabel("Estado:"), 3, 0)
        self.activo_check = QCheckBox("Docente Activo")
        self.activo_check.setChecked(True)
        grid.addWidget(self.activo_check, 3, 1)
        
        return grupo
    
    def crear_grupo_cv(self):
        """Crear grupo de curriculum vitae con proporción de hoja carta"""
        grupo = QGroupBox("📄 CURRICULUM VITAE (PDF)")
        
        layout = QVBoxLayout(grupo)
        layout.setSpacing(15)
        
        # Botones para CV
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.btn_examinar_cv = QPushButton("📎 Examinar CV")
        self.btn_examinar_cv.setObjectName("btnExaminarCV")
        
        self.btn_ver_cv = QPushButton("👁️ Ver CV Completo")
        self.btn_ver_cv.setObjectName("btnVerCV")
        self.btn_ver_cv.setEnabled(False)
        
        self.btn_eliminar_cv = QPushButton("🗑️ Eliminar")
        self.btn_eliminar_cv.setObjectName("btnEliminarCV")
        self.btn_eliminar_cv.setEnabled(False)
        
        button_layout.addWidget(self.btn_examinar_cv)
        button_layout.addWidget(self.btn_ver_cv)
        button_layout.addWidget(self.btn_eliminar_cv)
        
        layout.addLayout(button_layout)
        
        # Ruta del CV
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Archivo:"))
        self.cv_path_label = QLabel("No se ha seleccionado archivo")
        self.cv_path_label.setWordWrap(True)
        self.cv_path_label.setMinimumHeight(45)
        self.cv_path_label.setStyleSheet("""
            padding: 8px;
            background-color: #f8f9fa;
            border-radius: 6px;
            border: 1px solid #dee2e6;
            font-size: 12px;
            color: #6c757d;
        """)
        path_layout.addWidget(self.cv_path_label, 1)
        layout.addLayout(path_layout)
        
        # Contenedor para la vista previa centrada
        preview_container = QWidget()
        preview_container_layout = QVBoxLayout(preview_container)
        preview_container_layout.setContentsMargins(0, 0, 0, 0)
        preview_container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Área de vista previa con proporción carta vertical
        preview_frame = QFrame()
        preview_frame.setObjectName("previewFrame")
        preview_frame.setMinimumSize(200, 280)  # Mínimo: 200x280 (1:1.4)
        preview_frame.setMaximumSize(300, 420)  # Máximo: 300x420 (1:1.4)
        preview_frame.setStyleSheet("""
                #previewFrame {
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 10px;
                min-width: 200px;
                max-width: 300px;
                min-height: 280px;
                max-height: 420px;
            }
        """)
        
        # Layout interno para el label de vista previa
        preview_inner_layout = QVBoxLayout(preview_frame)
        preview_inner_layout.setContentsMargins(5, 5, 5, 5)
        preview_inner_layout.setSpacing(0)
        
        self.preview_area = QLabel()
        self.preview_area.setObjectName("previewArea")
        self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_area.setScaledContents(True)
        self.preview_area.setStyleSheet("""
            #previewArea {
                background-color: transparent;
            }
        """)
        
        # Texto inicial
        self.preview_area.setText("📎 No hay CV cargado\n\nHaga clic en 'Examinar CV'\n📄 Se mostrará vista previa aquí")
        self.preview_area.setWordWrap(True)
        
        preview_inner_layout.addWidget(self.preview_area)
        
        # Agregar el frame al contenedor centrado
        preview_container_layout.addWidget(preview_frame)
        layout.addWidget(preview_container, 1)
        
        # Información del PDF
        self.pdf_info_label = QLabel("")
        self.pdf_info_label.setWordWrap(True)
        self.pdf_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_info_label.setStyleSheet("""
            font-size: 12px;
            color: #6c757d;
            padding: 8px;
        """)
        layout.addWidget(self.pdf_info_label)
        
        # Barra de progreso
        self.cv_progress_bar = QProgressBar()
        self.cv_progress_bar.setVisible(False)
        layout.addWidget(self.cv_progress_bar)

        return grupo
    
    def setup_validators(self):
        """Configurar validadores"""
        int_validator = QIntValidator(0, 999999999)
        self.ci_numero_input.setValidator(int_validator)
        
        phone_validator = QIntValidator(0, 99999999)
        self.telefono_input.setValidator(phone_validator)
    
    def setup_conexiones_especificas(self):
        """Configurar conexiones específicas"""
        # Botones CV
        self.btn_examinar_cv.clicked.connect(self.examinar_cv)
        self.btn_ver_cv.clicked.connect(self.ver_cv_completo)
        self.btn_eliminar_cv.clicked.connect(self.eliminar_cv)
        
        # Detectar cambios
        campos = [
            self.ci_numero_input, self.nombres_input, self.apellido_paterno_input,
            self.apellido_materno_input, self.titulo_profesional_input,
            self.especialidad_input, self.telefono_input, self.email_input
        ]
        
        # Conectar botón guardar
        if hasattr(self, 'btn_guardar'):
            self.btn_guardar.clicked.disconnect()  # Desconectar conexiones previas
            self.btn_guardar.clicked.connect(self._procesar_guardado)
        
        # Conectar botón cancelar
        if hasattr(self, 'btn_cancelar'):
            self.btn_cancelar.clicked.connect(self.close_overlay)
        
        # Detectar cambios
        campos = [
            self.ci_numero_input, self.nombres_input, self.apellido_paterno_input,
            self.apellido_materno_input, self.titulo_profesional_input,
            self.especialidad_input, self.telefono_input, self.email_input
        ]

        for campo in campos:
            campo.textChanged.connect(self._marcar_modificado)
    
    # ===== MÉTODOS AUXILIARES =====
    
    def _marcar_modificado(self):
        """Marcar que se han realizado cambios"""
        if self.modo != "lectura":
            pass  # Podrías implementar lógica de dirty tracking aquí
    
    def _procesar_guardado(self):
        """Procesar la acción de guardar/actualizar docente"""
        # Validar formulario
        valido, errores = self.validar_formulario()
        
        if not valido:
            mensaje = "Por favor corrija los siguientes errores:\n\n" + "\n".join(errores)
            self.mostrar_mensaje("Error de validación", mensaje, "error")
            return
        
        try:
            # Obtener datos del formulario
            datos = self.obtener_datos()
            
            # Determinar si es creación o actualización
            if self.modo == "nuevo":
                # Crear nuevo docente
                nuevo_id = DocenteModel.crear_docente(datos)
                if nuevo_id:
                    datos['id'] = nuevo_id
                    self.mostrar_mensaje("Éxito", "Docente creado exitosamente", "success")
                    self.docente_creado.emit(datos)
                    self.close_overlay()
                else:
                    self.mostrar_mensaje("Error", "No se pudo crear el docente", "error")
                
            elif self.modo == "editar" and self.docente_id:
                # Actualizar docente existente
                datos['id'] = self.docente_id
                if DocenteModel.actualizar_docente(self.docente_id, datos):
                    self.mostrar_mensaje("Éxito", "Docente actualizado exitosamente", "success")
                    self.docente_actualizado.emit(datos)
                    self.close_overlay()
                else:
                    self.mostrar_mensaje("Error", "No se pudo actualizar el docente", "error")
                
            elif self.modo == "lectura":
                # En modo lectura, solo cerrar
                self.close_overlay()
            
        except Exception as e:
            logger.error(f"Error procesando guardado: {e}")
            self.mostrar_mensaje("Error", f"Error al procesar: {str(e)}", "error")
    
    # ===== IMPLEMENTACIÓN DE MÉTODOS BASE =====
    
    def validar_formulario(self):
        """Validar formulario de docente"""
        errores = []
        
        # Validar campos obligatorios
        if not self.ci_numero_input.text().strip():
            errores.append("El CI Número es obligatorio")
        
        if not self.nombres_input.text().strip():
            errores.append("Los nombres son obligatorio")
        
        if not self.apellido_paterno_input.text().strip():
            errores.append("El apellido paterno es obligatorio")
        
        # Validar CI único (si es modo nuevo o CI cambió)
        ci_numero = self.ci_numero_input.text().strip()
        if ci_numero:
            if self.modo == "nuevo" or (self.modo == "editar" and ci_numero != self.original_ci):
                excluir_id = self.docente_id if self.docente_id else 0
                if DocenteModel.verificar_ci_existente(ci_numero, excluir_id):
                    errores.append(f"El CI {ci_numero} ya está registrado")
        
        # Validar email si se proporciona
        email = self.email_input.text().strip()
        if email:
            valido, mensaje = Validators.validar_email(email)
            if not valido:
                errores.append(f"Email: {mensaje}")
            
            # Validar email único
            if email != self.original_email:
                excluir_id = self.docente_id if self.docente_id else 0
                if DocenteModel.verificar_email_existente(email, excluir_id):
                    errores.append(f"El email {email} ya está registrado")
        
        return len(errores) == 0, errores
    
    def obtener_datos(self):
        """Obtener datos del formulario"""
        fecha_nac_str = None
        fecha_nacimiento = self.fecha_nacimiento_date.date()
        if fecha_nacimiento.isValid():
            fecha_nac_str = fecha_nacimiento.toString('yyyy-MM-dd')
        
        datos = {
            'id': self.docente_id,
            'ci_numero': self.ci_numero_input.text().strip(),
            'ci_expedicion': self.ci_expedicion_combo.currentText(),
            'nombres': self.nombres_input.text().strip(),
            'apellido_paterno': self.apellido_paterno_input.text().strip(),
            'apellido_materno': self.apellido_materno_input.text().strip(),
            'fecha_nacimiento': fecha_nac_str,
            'grado_academico': self.grado_academico_combo.currentText(),
            'titulo_profesional': self.titulo_profesional_input.text().strip(),
            'especialidad': self.especialidad_input.text().strip(),
            'telefono': self.telefono_input.text().strip(),
            'email': self.email_input.text().strip(),
            'curriculum_url': self.pdf_path if self.pdf_path else '',
            'honorario_hora': self.honorario_hora_spin.value(),
            'activo': self.activo_check.isChecked()
        }
        
        # Limpiar campos vacíos
        for key in datos:
            if datos[key] == '':
                datos[key] = None
        
        return datos
    
    def clear_form(self):
        """Limpiar formulario"""
        self.docente_id = None
        self.original_data = {}
        self.original_ci = ""
        self.original_email = ""
        self.ci_numero_input.clear()
        self.ci_expedicion_combo.setCurrentIndex(0)
        self.nombres_input.clear()
        self.apellido_paterno_input.clear()
        self.apellido_materno_input.clear()
        self.fecha_nacimiento_date.setDate(QDate.currentDate().addYears(-30))
        self.grado_academico_combo.setCurrentIndex(0)
        self.titulo_profesional_input.clear()
        self.especialidad_input.clear()
        self.telefono_input.clear()
        self.email_input.clear()
        self.honorario_hora_spin.setValue(50.00)
        self.activo_check.setChecked(True)
        
        # Limpiar CV
        self.pdf_path = None
        self.cv_path_label.setText("No se ha seleccionado archivo")
        self.btn_ver_cv.setEnabled(False)
        self.btn_eliminar_cv.setEnabled(False)
        self.preview_area.setText("📎 No hay CV cargado\n\nHaga clic en 'Examinar CV' para cargar un PDF\n\n📄 Se mostrará una vista previa aquí")
        self.pdf_info_label.setText("")
        self.cv_changed = False
    
    def cargar_datos(self, datos):
        """Cargar datos en el formulario"""
        self.docente_id = datos.get('id')
        self.original_data = datos.copy()
        
        # Guardar datos originales para comparación
        self.original_ci = datos.get('ci_numero', '')
        self.original_email = datos.get('email', '')
        
        # Campos básicos
        self.ci_numero_input.setText(datos.get('ci_numero', ''))
        
        expedicion = datos.get('ci_expedicion', '')
        if expedicion:
            index = self.ci_expedicion_combo.findText(expedicion)
            if index >= 0:
                self.ci_expedicion_combo.setCurrentIndex(index)
                
        self.nombres_input.setText(datos.get('nombres', ''))
        self.apellido_paterno_input.setText(datos.get('apellido_paterno', ''))
        self.apellido_materno_input.setText(datos.get('apellido_materno', ''))
        
        # Fecha de nacimiento - Manejar diferentes formatos
        fecha_nac = datos.get('fecha_nacimiento')
        if fecha_nac:
            try:
                # Intentar diferentes formatos de fecha
                if isinstance(fecha_nac, str):
                    # Intentar formato ISO (yyyy-MM-dd)
                    try:
                        qdate = QDate.fromString(fecha_nac, 'yyyy-MM-dd')
                        if qdate.isValid():
                            self.fecha_nacimiento_date.setDate(qdate)
                    except:
                        # Intentar formato con hora si está incluida
                        if ' ' in fecha_nac:
                            fecha_part = fecha_nac.split(' ')[0]
                            qdate = QDate.fromString(fecha_part, 'yyyy-MM-dd')
                            if qdate.isValid():
                                self.fecha_nacimiento_date.setDate(qdate)
                        else:
                            # Si no se puede parsear, usar fecha por defecto
                            logger.warning(f"No se pudo parsear fecha: {fecha_nac}")
                            self.fecha_nacimiento_date.setDate(QDate.currentDate().addYears(-30))
                else:
                    # Si no es string, usar fecha por defecto
                    self.fecha_nacimiento_date.setDate(QDate.currentDate().addYears(-30))
            except Exception as e:
                logger.error(f"Error cargando fecha: {e}")
                self.fecha_nacimiento_date.setDate(QDate.currentDate().addYears(-30))
        else:
            # Fecha por defecto si no hay fecha
            self.fecha_nacimiento_date.setDate(QDate.currentDate().addYears(-30))
            
        # Datos académicos
        grado = datos.get('grado_academico', '')
        if grado:
            index = self.grado_academico_combo.findText(grado)
            if index >= 0:
                self.grado_academico_combo.setCurrentIndex(index)
                
        self.titulo_profesional_input.setText(datos.get('titulo_profesional', ''))
        self.especialidad_input.setText(datos.get('especialidad', ''))
        
        # Contacto
        self.telefono_input.setText(datos.get('telefono', ''))
        self.email_input.setText(datos.get('email', ''))
        
        honorario = datos.get('honorario_hora', 0)
        self.honorario_hora_spin.setValue(float(honorario) if honorario else 0)
        
        activo = datos.get('activo', True)
        self.activo_check.setChecked(bool(activo))
        
        # CV
        cv_url = datos.get('curriculum_url', '')
        if cv_url and os.path.exists(cv_url):
            # Solo establecer la ruta, sin crear nuevo archivo
            self.pdf_path = cv_url
            filename = os.path.basename(cv_url)
            self.cv_path_label.setText(filename)
            self.btn_ver_cv.setEnabled(True)
            self.btn_eliminar_cv.setEnabled(True)
            
            # Cargar vista previa del archivo existente
            self.cargar_vista_previa_pdf(cv_url)
        else:
            # No hay CV o no existe
            self.pdf_path = None
            self.cv_path_label.setText("No se ha seleccionado archivo")
            self.btn_ver_cv.setEnabled(False)
            self.btn_eliminar_cv.setEnabled(False)
    
    # ===== MÉTODOS DE CV =====
    
    def examinar_cv(self):
        """Abrir diálogo para seleccionar PDF"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar Curriculum Vitae (PDF)",
            "",
            "Archivos PDF (*.pdf);;Todos los archivos (*.*)"
        )
        
        if file_path:
            self.cargar_cv(file_path)
    
    def cargar_cv(self, file_path):
        """Cargar nuevo CV - Solo cuando usuario selecciona archivo"""
        try:
            if not file_path.lower().endswith('.pdf'):
                self.mostrar_mensaje("Error", "Por favor seleccione un archivo PDF", "error")
                return

            # Verificar tamaño
            file_size = os.path.getsize(file_path)
            if file_size > 10 * 1024 * 1024:
                self.mostrar_mensaje("Error", "El archivo PDF no debe superar los 10MB", "error")
                return

            # ===== NUEVA LÓGICA: Nombre por año =====
            anyo_actual = datetime.now().strftime("%Y")
            ci_numero = self.ci_numero_input.text().strip() or "sin_ci"
            filename = f"CV_{ci_numero}_{anyo_actual}.pdf"
            dest_path = os.path.join(self.cv_dir, filename)

            # Si ya existe CV para este año, preguntar
            if os.path.exists(dest_path):
                respuesta = QMessageBox.question(
                    self,
                    "CV Existente",
                    f"Ya existe un CV para {ci_numero} del año {anyo_actual}.\n"
                    f"¿Desea reemplazarlo con el nuevo archivo?\n\n"
                    f"Archivo actual: {os.path.basename(dest_path)}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if respuesta == QMessageBox.StandardButton.No:
                    return  # Usuario canceló

            # Copiar archivo (sobreescribe si existe)
            import shutil
            shutil.copy2(file_path, dest_path)

            # Actualizar interfaz
            self.pdf_path = dest_path
            self.cv_path_label.setText(filename)
            self.btn_ver_cv.setEnabled(True)
            self.btn_eliminar_cv.setEnabled(True)
            self.cv_changed = True

            # Cargar vista previa
            self.cargar_vista_previa_pdf(dest_path)

            self.mostrar_mensaje("Éxito", "CV cargado correctamente", "success")

        except Exception as e:
            logger.error(f"Error cargando CV: {e}")
            self.mostrar_mensaje("Error", f"No se pudo cargar el CV: {str(e)}", "error")
    
    def cargar_vista_previa_pdf(self, pdf_path):
        """Generar vista previa del PDF con PyMuPDF manteniendo proporción carta"""
        try:
            if not pdf_path or not os.path.exists(pdf_path):
                self.preview_area.setText("❌ El archivo PDF no existe")
                self.pdf_info_label.setText("")
                return
            
            # Obtener información básica del archivo
            file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # Convertir a MB
            filename = os.path.basename(pdf_path)
            
            try:
                import fitz  # PyMuPDF
                
                # Abrir el PDF
                doc = fitz.open(pdf_path)
                
                if len(doc) == 0:
                    self.preview_area.setText("⚠️ PDF vacío o dañado")
                    self.pdf_info_label.setText(f"📄 {filename} | 📏 {file_size:.2f} MB")
                    doc.close()
                    return
                
                # Obtener la primera página
                page = doc.load_page(0)
                
                # Obtener las dimensiones del área de vista previa
                preview_width = self.preview_area.width() - 10  # Considerar márgenes
                preview_height = self.preview_area.height() - 10
                
                # Calcular proporción de la página del PDF
                page_width = page.rect.width
                page_height = page.rect.height
                page_ratio = page_width / page_height
                
                # Para hoja carta estándar (8.5x11 pulgadas), ratio es ~0.7727
                # Nuestro contenedor tiene 250x350 = ratio ~0.7143
                
                # Calcular dimensiones para mantener proporción de la página
                if page_ratio > 1:
                    # Página horizontal
                    display_width = min(preview_width, int(preview_height * page_ratio))
                    display_height = int(display_width / page_ratio)
                else:
                    # Página vertical (la mayoría de CVs)
                    display_height = min(preview_height, int(preview_width / page_ratio))
                    display_width = int(display_height * page_ratio)
                    
                # Asegurar que no sea demasiado pequeño
                if display_width < 50 or display_height < 50:
                    display_width = preview_width
                    display_height = preview_height
                    
                # Renderizar la página como imagen
                zoom_x = display_width / page_width
                zoom_y = display_height / page_height
                zoom = min(zoom_x, zoom_y, 2.0)  # Limitar zoom máximo
                
                matrix = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                
                # Convertir a QImage
                img_data = pix.samples
                qimage = QImage(img_data, pix.width, pix.height, 
                                pix.stride, QImage.Format.Format_RGB888)
                
                # Convertir QImage a QPixmap
                pixmap = QPixmap.fromImage(qimage)
                
                # Escalar manteniendo proporción para ajustarse al área
                scaled_pixmap = pixmap.scaled(
                    display_width, display_height,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                
                # Configurar el QLabel para mostrar la imagen
                self.preview_area.setPixmap(scaled_pixmap)
                self.preview_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Mostrar información del PDF
                num_pages = len(doc)
                orientation = "Horizontal" if page_ratio > 1 else "Vertical"
                
                self.pdf_info_label.setText(
                    f"📄 {filename}\n"
                    f"📏 {num_pages} páginas | {file_size:.2f} MB | {orientation}\n"
                    f"📐 {int(page_width)}x{int(page_height)} pt | Vista: {display_width}x{display_height} px"
                )
                
                # Cerrar el documento
                doc.close()
                
                logger.info(f"✅ Vista previa generada para {filename} ({display_width}x{display_height} px)")
                
            except ImportError:
                # PyMuPDF no está disponible
                self._mostrar_mensaje_sin_vista_previa(filename, file_size)
                
            except Exception as e:
                logger.error(f"Error generando vista previa con PyMuPDF: {e}")
                self._mostrar_mensaje_error_vista_previa(filename, file_size, str(e))
                
        except Exception as e:
            logger.error(f"Error en cargar_vista_previa_pdf: {e}")
            self.preview_area.setText("❌ Error al cargar vista previa del PDF")
            self.pdf_info_label.setText("")

    def _mostrar_mensaje_sin_vista_previa(self, filename, file_size):
        """Mostrar mensaje cuando no hay PyMuPDF"""
        texto = f"""📄 {filename}

        ✅ PDF cargado correctamente

        📏 Tamaño: {file_size:.2f} MB

        ⚠️ Haz clic en 'Ver CV Completo'
        para abrir el PDF externamente."""

        self.preview_area.setText(texto)
        self.pdf_info_label.setText("📦 PyMuPDF requerido para vista previa")
    
    def resizeEvent(self, event):
        """Manejador para redimensionamiento - actualizar vista previa si hay PDF cargado"""
        super().resizeEvent(event)
        
        # Si hay un PDF cargado, actualizar la vista previa
        if hasattr(self, 'pdf_path') and self.pdf_path and os.path.exists(self.pdf_path):
            # Usar QTimer para esperar a que se complete el redimensionamiento
            from PySide6.QtCore import QTimer
            QTimer.singleShot(100, lambda: self.cargar_vista_previa_pdf(self.pdf_path))
    
    def _mostrar_mensaje_error_vista_previa(self, filename, file_size, error_msg):
        """Mostrar mensaje de error en vista previa"""
        texto = f"""📄 {filename}
        
        ✅ PDF cargado
        
        📏 Tamaño: {file_size:.2f} MB
        
        ⚠️ Error en vista previa
        {error_msg[:50]}...
        
        👉 Haz clic en 'Ver CV Completo'"""
        
        self.preview_area.setText(texto)
        self.pdf_info_label.setText("❌ Error en vista previa")
    
    def ver_cv_completo(self):
        """Abrir PDF en visor externo"""
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            self.mostrar_mensaje("Error", "El archivo PDF no está disponible", "error")
            return
        
        try:
            import platform
            import subprocess
            
            system = platform.system()
            if system == 'Windows':
                os.startfile(self.pdf_path)
            elif system == 'Darwin':
                subprocess.run(['open', self.pdf_path])
            else:
                subprocess.run(['xdg-open', self.pdf_path])
                
        except Exception as e:
            logger.error(f"Error abriendo PDF: {e}")
            self.mostrar_mensaje("Error", f"No se pudo abrir el PDF: {str(e)}", "error")
    
    def eliminar_cv(self):
        """Eliminar CV asociado"""
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Está seguro que desea eliminar el CV del docente?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            if self.pdf_path and os.path.exists(self.pdf_path):
                try:
                    os.remove(self.pdf_path)
                    
                    # Limpiar interfaz
                    self.pdf_path = None
                    self.cv_path_label.setText("No se ha seleccionado archivo")
                    self.btn_ver_cv.setEnabled(False)
                    self.btn_eliminar_cv.setEnabled(False)
                    self.preview_area.setText("📎 No hay CV cargado\n\nHaga clic en 'Examinar CV' para cargar un PDF\n\n📄 Se mostrará una vista previa aquí")
                    self.pdf_info_label.setText("")
                    self.cv_changed = True
                    
                    self.mostrar_mensaje("Éxito", "CV eliminado correctamente", "success")
                    
                except Exception as e:
                    logger.error(f"Error eliminando CV: {e}")
                    self.mostrar_mensaje("Error", f"No se pudo eliminar el archivo: {str(e)}", "error")
    
    def show_form(self, solo_lectura=False, datos=None, modo="nuevo", docente_id=None):
        """Mostrar overlay con configuración específica"""
        self.solo_lectura = solo_lectura
        self.modo = modo
        
        try:
            # Si se pasa docente_id pero no datos, cargarlos desde la base de datos
            if docente_id and not datos:
                datos = self._obtener_datos_docente_db(docente_id)
                self.docente_id = docente_id
            elif docente_id and datos:
                self.docente_id = docente_id
            else:
                self.docente_id = datos.get('id') if datos else None
            
            if datos:
                self.cargar_datos(datos)
            elif modo == "nuevo":
                self.clear_form()
            
            # Configurar título
            titulo = ""
            if modo == "nuevo":
                titulo = "👨‍🏫 Nuevo Docente"
            elif modo == "editar" and self.docente_id:
                titulo = f"✏️ Editar Docente - ID: {self.docente_id}"
            elif modo == "lectura" and self.docente_id:
                titulo = f"👁️ Ver Docente - ID: {self.docente_id}"
            else:
                titulo = "👨‍🏫 Gestión de Docente"
                
            self.set_titulo(titulo)
            
            # Configurar botones según modo
            if modo == "lectura":
                self.btn_guardar.setText("👈 VOLVER")
                self.btn_guardar.setVisible(False)
                self.btn_cancelar.setText("👈 CERRAR")
            elif modo == "editar":
                self.btn_guardar.setText("💾 ACTUALIZAR DOCENTE")
                self.btn_guardar.setVisible(True)
            else:  # modo == "nuevo"
                self.btn_guardar.setText("💾 GUARDAR DOCENTE")
                self.btn_guardar.setVisible(True)
            
            # Re-conectar botón guardar con la lógica adecuada
            if hasattr(self, 'btn_guardar'):
                try:
                    self.btn_guardar.clicked.disconnect()
                except:
                    pass  # No importa si no estaba conectado
                
                if modo == "lectura":
                    self.btn_guardar.clicked.connect(self.close_overlay)
                else:
                    self.btn_guardar.clicked.connect(self._procesar_guardado)
            
            # Habilitar/deshabilitar campos
            es_solo_lectura = solo_lectura or modo == "lectura"
            campos = [
                self.ci_numero_input, self.ci_expedicion_combo, self.nombres_input,
                self.apellido_paterno_input, self.apellido_materno_input,
                self.fecha_nacimiento_date, self.grado_academico_combo,
                self.titulo_profesional_input, self.especialidad_input,
                self.telefono_input, self.email_input, self.honorario_hora_spin,
                self.activo_check, self.btn_examinar_cv
            ]
            
            for campo in campos:
                campo.setEnabled(not es_solo_lectura)
                if hasattr(campo, 'setReadOnly'):
                    campo.setReadOnly(es_solo_lectura)
            
            # Llamar al método base
            super().show_form(es_solo_lectura)
            
            logger.info(f"✅ Overlay de docente mostrado - Modo: {modo}, ID: {self.docente_id}")
            
        except Exception as e:
            logger.error(f"❌ Error en show_form: {e}")
            # Fallback: mostrar solo con datos mínimos
            super().show_form(solo_lectura)
    
    # Añadir este método auxiliar en la clase DocenteOverlay:
    def _obtener_datos_docente_db(self, docente_id: int) -> Optional[Dict]:
        """Obtener datos de docente desde la base de datos"""
        try:
            from model.docente_model import DocenteModel
            docente = DocenteModel.obtener_docente_por_id(docente_id)
            if docente:
                # Formatear datos para el overlay
                datos_formateados = {
                    'id': docente.get('id'),
                    'ci_numero': docente.get('ci_numero', ''),
                    'ci_expedicion': docente.get('ci_expedicion', ''),
                    'nombres': docente.get('nombres', ''),
                    'apellido_paterno': docente.get('apellido_paterno', ''),
                    'apellido_materno': docente.get('apellido_materno', ''),
                    'fecha_nacimiento': docente.get('fecha_nacimiento', ''),
                    'grado_academico': docente.get('grado_academico', ''),
                    'titulo_profesional': docente.get('titulo_profesional', ''),
                    'especialidad': docente.get('especialidad', ''),
                    'telefono': docente.get('telefono', ''),
                    'email': docente.get('email', ''),
                    'curriculum_url': docente.get('curriculum_url', ''),
                    'honorario_hora': float(docente.get('honorario_hora', 0.0)),
                    'activo': bool(docente.get('activo', True))
                }
                return datos_formateados
            return None
        except Exception as e:
            logger.error(f"Error obteniendo datos de docente: {e}")
            return None
    
