# view/overlays/base_overlay.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QMessageBox, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Signal,
    QSequentialAnimationGroup, QTimer, QSize
)
from PySide6.QtGui import QFont, QCursor, QColor
import logging

logger = logging.getLogger(__name__)

class BaseOverlay(QWidget):
    """Clase base para todos los overlays del sistema"""
    
    # Señales base
    overlay_closed = Signal()
    overlay_saved = Signal(object)
    overlay_cancelled = Signal()
    
    def __init__(self, parent=None, titulo="", ancho_porcentaje=95, alto_porcentaje=95):
        """
        Inicializa el overlay base
        
        Args:
            parent: Ventana padre
            titulo: Título del overlay
            ancho_porcentaje: Porcentaje del ancho de la ventana padre (0-100)
            alto_porcentaje: Porcentaje del alto de la ventana padre (0-100)
        """
        super().__init__(parent)
        self._closed = False  # Bandera para evitar múltiples cierres
        self._closing_in_progress = False  # Bandera para evitar cierre recursivo
        
        self.parent_widget = parent
        self.titulo = titulo
        self.ancho_porcentaje = ancho_porcentaje
        self.alto_porcentaje = alto_porcentaje
        
        # Configuración de la ventana
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        
        # Variables de estado
        self.solo_lectura = False
        self.modo = "nuevo"  # "nuevo", "editar", "lectura"
        
        # Widget oscurecedor
        self.darkener = None
        self.setup_darkener()
        
        # Configurar UI
        self.setup_ui()
        self.setup_animations()
        
        # Conectar botones base
        self.connect_signals()
        
        logger.debug(f"✅ BaseOverlay inicializado: {titulo}")
    
    def setup_darkener(self):
        """Configurar widget oscurecedor del fondo"""
        if self.parent_widget:
            self.darkener = QWidget(self.parent_widget)
            self.darkener.setObjectName("overlayDarkener")
            self.darkener.setStyleSheet("""
                #overlayDarkener {
                    background-color: rgba(10, 31, 68, 180);
                }
            """)
            self.darkener.hide()
            self.darkener.lower()
    
    def setup_ui(self):
        """Configura la interfaz base del overlay"""
        # Layout principal sin márgenes
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Contenedor principal (para bordes redondeados)
        self.main_container = QFrame()
        self.main_container.setObjectName("mainContainer")
        self.main_container.setStyleSheet("""
            #mainContainer {
                background-color: #f5f5f5;
                border: 3px solid #1a237e;
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(15, 15, 15, 15)
        container_layout.setSpacing(10)
        
        # Header con título y botón cerrar
        self.setup_header(container_layout)
        
        # Área de contenido (implementada por subclases)
        self.content_area = QFrame()
        self.content_area.setObjectName("contentArea")
        self.content_area.setStyleSheet("""
            #contentArea {
                background-color: transparent;
            }
        """)
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setSpacing(10)
        
        container_layout.addWidget(self.content_area, 1)
        
        # Footer con botones
        self.setup_footer(container_layout)
        
        # Agregar al layout principal
        main_layout.addWidget(self.main_container)
        
        # Aplicar estilos base
        self.apply_base_styles()
    
    def setup_header(self, parent_layout):
        """Configurar la cabecera del overlay"""
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_frame.setStyleSheet("""
            #headerFrame {
                background-color: white;
                border-bottom: 2px solid #1a237e;
                border-radius: 8px;
                padding: 10px;
            }
        """)
        header_frame.setMaximumHeight(70)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # Título
        self.title_label = QLabel(self.titulo)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("""
            #titleLabel {
                font-size: 22px;
                font-weight: bold;
                color: #1a237e;
                qproperty-alignment: 'AlignCenter';
            }
        """)
        
        # Botón cerrar (X)
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("btnClose")
        self.btn_close.setStyleSheet("""
            #btnClose {
                font-size: 20px;
                font-weight: bold;
                color: #7f8c8d;
                background: transparent;
                border: none;
                padding: 5px 15px;
                min-width: 30px;
                min-height: 30px;
                border-radius: 15px;
            }
            #btnClose:hover {
                color: #e74c3c;
                background-color: #f8f9fa;
            }
        """)
        self.btn_close.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_close.setFixedSize(40, 40)
        
        header_layout.addWidget(self.title_label, 1)
        header_layout.addWidget(self.btn_close)
        
        parent_layout.addWidget(header_frame)
    
    def setup_footer(self, parent_layout):
        """Configurar el pie del overlay con botones"""
        footer_frame = QFrame()
        footer_frame.setObjectName("footerFrame")
        footer_frame.setStyleSheet("""
            #footerFrame {
                background-color: transparent;
                border-top: 1px solid #e0e0e0;
                padding-top: 15px;
            }
        """)
        footer_frame.setMaximumHeight(100)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(0, 10, 0, 10)
        
        # Botón Cancelar
        self.btn_cancelar = QPushButton("❌ CANCELAR")
        self.btn_cancelar.setObjectName("btnCancelar")
        self.btn_cancelar.setStyleSheet("""
            #btnCancelar {
                background-color: #e74c3c;
                color: white;
                border: 2px solid #e74c3c;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 30px;
                border-radius: 6px;
                min-width: 150px;
            }
            #btnCancelar:hover {
                background-color: #c0392b;
                border-color: #c0392b;
            }
        """)
        self.btn_cancelar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_cancelar.setMinimumHeight(45)
        
        # Botón Guardar
        self.btn_guardar = QPushButton("💾 GUARDAR")
        self.btn_guardar.setObjectName("btnGuardar")
        self.btn_guardar.setStyleSheet("""
            #btnGuardar {
                background-color: #1a237e;
                color: white;
                border: 2px solid #1a237e;
                font-weight: bold;
                font-size: 14px;
                padding: 12px 30px;
                border-radius: 6px;
                min-width: 200px;
            }
            #btnGuardar:hover {
                background-color: #283593;
                border-color: #283593;
            }
            #btnGuardar:disabled {
                background-color: #bdc3c7;
                border-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        self.btn_guardar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_guardar.setMinimumHeight(45)
        
        footer_layout.addStretch()
        footer_layout.addWidget(self.btn_cancelar)
        footer_layout.addWidget(self.btn_guardar)
        footer_layout.addStretch()
        
        parent_layout.addWidget(footer_frame)
    
    def setup_animations(self):
        """Configurar animaciones para mostrar/ocultar"""
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
    
    def connect_signals(self):
        """Conectar señales base"""
        self.btn_close.clicked.connect(self.close_overlay)
        self.btn_cancelar.clicked.connect(self.close_overlay)
        self.btn_guardar.clicked.connect(self._on_guardar_clicked)
    
    def apply_base_styles(self):
        """Aplicar estilos CSS base a todo el overlay"""
        base_styles = """
        /* Estilos generales para overlays */
        BaseOverlay {
            background-color: transparent;
        }
        
        /* Labels especiales */
        .labelObligatorio {
            color: #c0392b;
            font-weight: bold;
            font-size: 12px;
        }
        
        .labelEstadistica {
            font-weight: bold;
            color: #2c3e50;
            padding: 5px;
            border-radius: 4px;
            background-color: #ecf0f1;
        }
        
        /* Campos deshabilitados */
        QComboBox:disabled, QLineEdit:disabled, QTextEdit:disabled,
        QSpinBox:disabled, QDoubleSpinBox:disabled, QDateEdit:disabled,
        QCheckBox:disabled {
            background-color: #f5f5f5;
            color: #666666;
            border: 1px solid #cccccc;
            height: 20px;
        }
        
        /* Campos de entrada */
        QLineEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {
            padding: 8px;
            border: 1px solid #bdc3c7;
            border-radius: 4px;
            background-color: white;
            font-size: 13px;
            max-height: 20px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
        QDateEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
            border: 2px solid #3498db;
            outline: none;
            height: 20px;
        }
        
        /* Tablas */
        QTableWidget {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            background-color: white;
            alternate-background-color: #f8f9fa;
        }
        
        QHeaderView::section {
            background-color: #3498db;
            color: white;
            padding: 8px;
            border: 1px solid #2980b9;
            font-weight: bold;
        }
        
        /* QTabWidget */
        QTabWidget::pane {
            border: 1px solid #bdc3c7;
            border-radius: 5px;
            background-color: white;
        }
        
        QTabBar::tab {
            background-color: #ecf0f1;
            color: #2c3e50;
            padding: 8px 16px;
            margin-right: 2px;
            border: 1px solid #bdc3c7;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        
        /* QGroupBox */
        QGroupBox {
            font-weight: bold;
            font-size: 14px;
            border: 2px solid #2c3e50;
            border-radius: 8px;
            margin-top: 12px;
            padding-top: 12px;
            background-color: #f8f9fa;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 8px 0 8px;
            color: #2c3e50;
            background-color: white;
        }
        
        /* Splitter */
        QSplitter::handle {
            background-color: #bdc3c7;
        }
        
        QSplitter::handle:hover {
            background-color: #3498db;
        }
        
        /* ScrollArea */
        QScrollArea {
            border: none;
            background-color: transparent;
        }
        
        QScrollBar:vertical {
            border: none;
            background-color: #f5f5f5;
            width: 10px;
            border-radius: 5px;
        }
        
        QScrollBar::handle:vertical {
            background-color: #bdc3c7;
            border-radius: 5px;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: #3498db;
        }
        """
        
        self.setStyleSheet(base_styles)
    
    def _on_guardar_clicked(self):
        """Manejador base para el botón guardar"""
        if self.solo_lectura:
            self.close_overlay()
            return
        
        try:
            # Validar formulario
            valido, errores = self.validar_formulario()
            if not valido:
                self.mostrar_mensaje("Validación", 
                                    "Por favor corrija los siguientes errores:\n\n• " + "\n• ".join(errores),
                                    "error")
                return
            
            # Obtener datos
            datos = self.obtener_datos()
            datos['modo'] = self.modo
            datos['solo_lectura'] = self.solo_lectura
            
            # Emitir señal
            self.overlay_saved.emit(datos)
            
            # Cerrar overlay si es modo nuevo
            if self.modo == "nuevo":
                self.close_overlay()
            
        except Exception as e:
            logger.error(f"Error en guardar: {e}")
            self.mostrar_mensaje("Error", f"No se pudo procesar la operación: {str(e)}", "error")
    
    def calcular_tamano(self):
        """Calcular tamaño basado en porcentaje de la ventana padre"""
        if self.parent_widget:
            parent_width = self.parent_widget.width()
            parent_height = self.parent_widget.height()
            
            ancho = int(parent_width * (self.ancho_porcentaje / 100))
            alto = int(parent_height * (self.alto_porcentaje / 100))
            
            # Tamaños mínimos y máximos
            ancho = max(600, min(ancho, 1400))
            alto = max(400, min(alto, 1000))
            
            return QSize(ancho, alto)
        else:
            return QSize(1200, 800)
    
    def show_form(self, solo_lectura=False):
        """Mostrar el overlay centrado con animación"""
        # Resetear banderas de cierre cuando se muestra
        self._closed = False
        self._closing_in_progress = False
        
        self.solo_lectura = solo_lectura
        
        # Calcular tamaño
        tamaño = self.calcular_tamano()
        self.setFixedSize(tamaño)
        
        # NO modificar el título aquí - ya fue establecido por la clase hija
        # Solo configurar el texto del botón según modo
        if solo_lectura:
            self.btn_guardar.setText("👈 VOLVER")
        elif self.modo == "editar":
            self.btn_guardar.setText("💾 ACTUALIZAR")
        else:
            self.btn_guardar.setText("💾 GUARDAR")
        
        # Habilitar/deshabilitar botón guardar según modo
        self.btn_guardar.setVisible(not solo_lectura)
        
        # Mostrar oscurecedor
        if self.darkener and self.parent_widget:
            self.darkener.setGeometry(self.parent_widget.rect())
            self.darkener.show()
            self.darkener.raise_()
        
        # Centrar
        self._centrar_en_padre()
        
        # Animación de fade in
        self.setWindowOpacity(0)
        self.show()
        self.raise_()
        
        self.fade_animation.setStartValue(0)
        self.fade_animation.setEndValue(1)
        self.fade_animation.start()
        
        logger.debug(f"✅ Overlay mostrado: {self.titulo}")
    
    def hide_form(self):
        """Ocultar el overlay con animación"""
        self.fade_animation.setStartValue(1)
        self.fade_animation.setEndValue(0)
        self.fade_animation.finished.connect(self._ocultar_completamente)
        self.fade_animation.start()
    
    def close_overlay(self):
        """Método público para cerrar el overlay - VERSIÓN CORREGIDA"""
        # Evitar cierre múltiple
        if self._closing_in_progress or self._closed:
            print(f"⚠️  BaseOverlay.close_overlay() - Ya en proceso de cierre, ignorando")
            return
        
        print(f"🔵 BaseOverlay.close_overlay() - Iniciando cierre controlado")
        self._closing_in_progress = True
        
        try:
            # Emitir señal UNA SOLA VEZ
            if not self._closed:
                self._closed = True
                self.overlay_closed.emit()
                print(f"✅ BaseOverlay.close_overlay() - Señal emitida")
            else:
                print(f"⚠️  BaseOverlay.close_overlay() - Ya se había emitido señal")
            
            # Cerrar ventana después de un pequeño delay
            QTimer.singleShot(10, self._close_window_safely)
            
        except Exception as e:
            print(f"❌ Error en close_overlay: {e}")
            self._closing_in_progress = False
    
    def _close_window_safely(self):
        """Cerrar ventana de forma segura"""
        try:
            print(f"🔵 BaseOverlay._close_window_safely() - Cerrando ventana")
            self.close()
            self._closing_in_progress = False
        except Exception as e:
            print(f"❌ Error cerrando ventana: {e}")
            self._closing_in_progress = False
    
    def closeEvent(self, event):
        """Manejador para el cierre de la ventana - VERSIÓN CORREGIDA"""
        print(f"🔵 BaseOverlay.closeEvent() - Procesando evento de cierre")
        
        # Solo emitir si no se ha emitido ya
        if not self._closed:
            self._closed = True
            print(f"✅ BaseOverlay.closeEvent() - Emitiendo señal")
            self.overlay_closed.emit()
        else:
            print(f"⚠️  BaseOverlay.closeEvent() - Señal ya emitida, ignorando")
        
        # Ocultar oscurecedor si existe
        if self.darkener:
            self.darkener.hide()
        
        # Aceptar evento
        event.accept()
        print(f"✅ BaseOverlay.closeEvent() - Evento aceptado")
    
    def _ocultar_completamente(self):
        """Completar la ocultación"""
        # Ocultar oscurecedor
        if self.darkener:
            self.darkener.hide()
        
        self.hide()
        self.fade_animation.finished.disconnect(self._ocultar_completamente)
    
    def _centrar_en_padre(self):
        """Centrar el overlay en la ventana padre"""
        if self.parent_widget:
            parent_rect = self.parent_widget.geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)
        else:
            # Centrar en pantalla
            screen = self.screen().availableGeometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
    
    def set_titulo(self, titulo):
        """Establecer el título del overlay"""
        self.titulo = titulo
        self.title_label.setText(titulo)
    
    def set_modo(self, modo):
        """Establecer modo de operación"""
        self.modo = modo
    
    def mostrar_mensaje(self, titulo, mensaje, tipo="info"):
        """Mostrar mensaje emergente"""
        iconos = {
            "info": QMessageBox.Icon.Information,
            "warning": QMessageBox.Icon.Warning,
            "error": QMessageBox.Icon.Critical,
            "success": QMessageBox.Icon.Information,
            "question": QMessageBox.Icon.Question
        }
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(titulo)
        msg_box.setText(mensaje)
        msg_box.setIcon(iconos.get(tipo, QMessageBox.Icon.Information))
        
        if tipo == "success":
            msg_box.setStyleSheet("QLabel { color: #27ae60; }")
        elif tipo == "error":
            msg_box.setStyleSheet("QLabel { color: #e74c3c; }")
        
        msg_box.exec()
    
    # ===== MÉTODOS ABSTRACTO QUE DEBEN SER IMPLEMENTADOS =====
    
    def validar_formulario(self):
        """Validar formulario - debe ser implementado por subclases"""
        raise NotImplementedError("El método validar_formulario debe ser implementado")
    
    def obtener_datos(self):
        """Obtener datos del formulario - debe ser implementado por subclases"""
        raise NotImplementedError("El método obtener_datos debe ser implementado")
    
    def clear_form(self):
        """Limpiar formulario - debe ser implementado por subclases"""
        raise NotImplementedError("El método clear_form debe ser implementado")
    
    def cargar_datos(self, datos):
        """Cargar datos en formulario - debe ser implementado por subclases"""
        raise NotImplementedError("El método cargar_datos debe ser implementado")
    
    def resizeEvent(self, event):
        """Manejador para redimensionamiento"""
        super().resizeEvent(event)
        if self.darkener and self.parent_widget:
            self.darkener.setGeometry(self.parent_widget.rect())