# view/login_window.py
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QFrame, QMessageBox,
    QCheckBox
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QCursor, QIcon
from controller.auth_controller import AuthController
import os

logger = logging.getLogger(__name__)

class LoginWindow(QWidget):
    """Ventana de inicio de sesión"""
    
    # Señal emitida cuando el login es exitoso
    login_successful = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Bandera para evitar múltiples intentos de login
        self.login_in_progress = False
        
        # Controlador de autenticación
        self.auth_controller = AuthController()
        
        # Configurar ventana
        self.setWindowTitle("FormaGestPro - Inicio de Sesión")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Tamaño fijo
        self.setFixedSize(500, 700)
        
        # Configurar UI
        self.setup_ui()
        self.apply_styles()
        
        # Conectar señales
        self.connect_signals()
        
        logger.debug("✅ LoginWindow inicializada")
    
    def setup_ui(self):
        """Configurar la interfaz de usuario"""
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(0)
        
        # Contenedor principal (para bordes redondeados)
        self.main_container = QFrame()
        self.main_container.setObjectName("loginContainer")
        
        container_layout = QVBoxLayout(self.main_container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(15)
        
        # Logo / Título
        self.setup_header(container_layout)
        
        # Formulario de login
        self.setup_form(container_layout)
        
        # Botones
        self.setup_buttons(container_layout)
        
        # Footer
        self.setup_footer(container_layout)
        
        # Agregar al layout principal
        main_layout.addWidget(self.main_container)
    
    def setup_header(self, parent_layout):
        """Configurar encabezado con logo/título"""
        # Título principal
        title_label = QLabel("FormaGestPro")
        title_label.setObjectName("mainTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Subtítulo
        subtitle_label = QLabel("Sistema de Gestión Académica")
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        parent_layout.addWidget(title_label)
        parent_layout.addWidget(subtitle_label)
        parent_layout.addSpacing(20)
    
    def setup_form(self, parent_layout):
        """Configurar formulario de login"""
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(15, 15, 15, 15)
        form_layout.setSpacing(20)
        
        # Campo Usuario
        user_layout = QVBoxLayout()
        user_layout.setSpacing(5)
        
        user_label = QLabel("Usuario:")
        user_label.setObjectName("fieldLabel")
        
        self.username_input = QLineEdit()
        self.username_input.setObjectName("usernameInput")
        self.username_input.setPlaceholderText("Ingrese su nombre de usuario")
        self.username_input.setMinimumHeight(40)
        
        # Icono de usuario
        user_icon = QLabel("👤")
        user_icon.setObjectName("fieldIcon")
        
        user_widget = QFrame()
        user_widget.setObjectName("fieldContainer")
        user_inner_layout = QHBoxLayout(user_widget)
        user_inner_layout.setContentsMargins(10, 0, 10, 0)
        user_inner_layout.addWidget(user_icon)
        user_inner_layout.addWidget(self.username_input)
        
        user_layout.addWidget(user_label)
        user_layout.addWidget(user_widget)
        
        # Campo Contraseña
        password_layout = QVBoxLayout()
        password_layout.setSpacing(5)
        
        password_label = QLabel("Contraseña:")
        password_label.setObjectName("fieldLabel")
        
        self.password_input = QLineEdit()
        self.password_input.setObjectName("passwordInput")
        self.password_input.setPlaceholderText("Ingrese su contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(40)
        
        # Icono de candado
        password_icon = QLabel("🔒")
        password_icon.setObjectName("fieldIcon")
        
        # Botón para mostrar/ocultar contraseña
        self.toggle_password_btn = QPushButton("👁️")
        self.toggle_password_btn.setObjectName("togglePasswordBtn")
        self.toggle_password_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.toggle_password_btn.setMaximumWidth(40)
        self.toggle_password_btn.setCheckable(True)
        
        password_widget = QFrame()
        password_widget.setObjectName("fieldContainer")
        password_inner_layout = QHBoxLayout(password_widget)
        password_inner_layout.setContentsMargins(10, 0, 10, 0)
        password_inner_layout.addWidget(password_icon)
        password_inner_layout.addWidget(self.password_input)
        password_inner_layout.addWidget(self.toggle_password_btn)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(password_widget)
        
        # Opciones adicionales
        options_layout = QHBoxLayout()
        
        self.remember_checkbox = QCheckBox("Recordarme")
        self.remember_checkbox.setObjectName("rememberCheckbox")
        
        self.forgot_password_btn = QPushButton("¿Olvidó su contraseña?")
        self.forgot_password_btn.setObjectName("forgotPasswordBtn")
        self.forgot_password_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        options_layout.addWidget(self.remember_checkbox)
        options_layout.addStretch()
        options_layout.addWidget(self.forgot_password_btn)
        
        # Agregar al formulario
        form_layout.addLayout(user_layout)
        form_layout.addLayout(password_layout)
        form_layout.addLayout(options_layout)
        
        parent_layout.addWidget(form_frame)
    
    def setup_buttons(self, parent_layout):
        """Configurar botones principales"""
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(10)
        
        # Botón Ingresar
        self.login_btn = QPushButton("🚪 INGRESAR")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setMinimumHeight(50)
        self.login_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        # Botón Salir
        self.exit_btn = QPushButton("❌ SALIR")
        self.exit_btn.setObjectName("exitButton")
        self.exit_btn.setMinimumHeight(40)
        self.exit_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
        buttons_layout.addWidget(self.login_btn)
        buttons_layout.addWidget(self.exit_btn)
        
        parent_layout.addLayout(buttons_layout)
    
    def setup_footer(self, parent_layout):
        """Configurar pie de página"""
        footer_label = QLabel("© 2024 DespachaNet - Todos los derechos reservados")
        footer_label.setObjectName("footerLabel")
        footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        parent_layout.addSpacing(20)
        parent_layout.addWidget(footer_label)
    
    def apply_styles(self):
        """Aplicar estilos CSS a la ventana de login"""
        styles = """
        /* Contenedor principal */
        #loginContainer {
            background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3498db,
                    stop:0.5 #2980b9,
                    stop:1 #2c3e50
                );
            border-radius: 20px;
            border: 3px solid #3949ab;
        }
        
        /* Títulos */
        #mainTitle {
            color: white;
            font-size: 32px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial, sans-serif;
        }
        
        #subtitle {
            color: #bbdefb;
            font-size: 16px;
            font-weight: normal;
        }
        
        /* Marco del formulario */
        #formFrame {
            background-color: rgba(255, 255, 255, 0.7);
            border-radius: 12px;
            border: 2px solid #5c6bc0;
        }
        
        /* Labels de campos */
        #fieldLabel {
            color: #1a237e;
            font-size: 14px;
            font-weight: bold;
            padding-left: 5px;
        }
        
        /* Contenedores de campos */
        #fieldContainer {
            background-color: white;
            border: 2px solid #c5cae9;
            border-radius: 8px;
        }
        
        #fieldContainer:hover {
            border-color: #3949ab;
        }
        
        /* Campos de entrada */
        #usernameInput, #passwordInput {
            background-color: transparent;
            border: none;
            font-size: 15px;
            color: #1a237e;
            selection-background-color: #3949ab;
            selection-color: white;
        }
        
        #usernameInput:focus, #passwordInput:focus {
            outline: none;
        }
        
        #usernameInput::placeholder, #passwordInput::placeholder {
            color: #9fa8da;
        }
        
        /* Iconos */
        #fieldIcon {
            font-size: 18px;
            color: #5c6bc0;
        }
        
        /* Botón mostrar/ocultar contraseña */
        #togglePasswordBtn {
            background-color: transparent;
            border: none;
            font-size: 16px;
            color: #5c6bc0;
            padding: 5px;
            border-radius: 5px;
        }
        
        #togglePasswordBtn:hover {
            background-color: #e8eaf6;
        }
        
        #togglePasswordBtn:checked {
            color: #3949ab;
        }
        
        /* Checkbox recordar */
        #rememberCheckbox {
            color: #3949ab;
            font-size: 14px;
        }
        
        #rememberCheckbox::indicator {
            width: 18px;
            height: 18px;
        }
        
        #rememberCheckbox::indicator:checked {
            background-color: #1a237e;
            border: 2px solid #1a237e;
            border-radius: 3px;
        }
        
        /* Botón olvidó contraseña */
        #forgotPasswordBtn {
            background-color: transparent;
            border: none;
            color: #3949ab;
            font-size: 12px;
            text-decoration: underline;
            padding: 0;
        }
        
        #forgotPasswordBtn:hover {
            color: #1a237e;
            text-decoration: none;
        }
        
        /* Botón ingresar */
        #loginButton {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #43a047, 
                stop:1 #2e7d32
            );
            color: white;
            font-size: 16px;
            font-weight: bold;
            border: none;
            border-radius: 8px;
            padding: 12px;
        }
        
        #loginButton:hover {
            background-color: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #388e3c, 
                stop:1 #1b5e20
            );
        }
        
        #loginButton:pressed {
            background-color: #1b5e20;
            padding-top: 13px;
            padding-bottom: 11px;
        }
        
        #loginButton:disabled {
            background-color: #c8e6c9;
            color: #81c784;
        }
        
        /* Botón salir */
        #exitButton {
            background-color: #e53935;
            color: #ffffff;
            font-size: 14px;
            font-weight: bold;
            border: 2px solid #e53935;
            border-radius: 8px;
            padding: 8px;
        }
        
        #exitButton:hover {
            background-color: #ffebee;
            color: #b71c1c;
        }
        
        #exitButton:pressed {
            background-color: #ffcdd2;
        }
        
        /* Footer */
        #footerLabel {
            color: #9fa8da;
            font-size: 11px;
            font-style: italic;
        }
        
        /* Mensajes de error */
        .error-message {
            color: #f44336;
            background-color: #ffebee;
            border: 1px solid #ffcdd2;
            border-radius: 5px;
            padding: 8px;
            font-size: 13px;
            text-align: center;
            margin-top: 5px;
        }
        """
        
        self.setStyleSheet(styles)
    
    def connect_signals(self):
        """Conectar todas las señales"""
        # Botones
        self.login_btn.clicked.connect(self.on_login_clicked)
        self.exit_btn.clicked.connect(self.close)
        self.toggle_password_btn.toggled.connect(self.toggle_password_visibility)
        self.forgot_password_btn.clicked.connect(self.on_forgot_password)
        
        # Enter para login
        self.username_input.returnPressed.connect(self.on_login_clicked)
        self.password_input.returnPressed.connect(self.on_login_clicked)
    
    def toggle_password_visibility(self, checked):
        """Mostrar/ocultar contraseña"""
        if checked:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("🙈")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("👁️")
    
    def on_login_clicked(self):
        """Manejador para el botón de login"""
        # Evitar múltiples intentos simultáneos
        if self.login_in_progress:
            return
        
        # Obtener credenciales
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        # Validaciones básicas
        if not username:
            self.show_error("Por favor ingrese su nombre de usuario")
            self.username_input.setFocus()
            return
        
        if not password:
            self.show_error("Por favor ingrese su contraseña")
            self.password_input.setFocus()
            return
        
        # Deshabilitar botón durante el login
        self.login_in_progress = True
        self.login_btn.setEnabled(False)
        self.login_btn.setText("🔐 AUTENTICANDO...")
        
        # Intentar autenticar
        try:
            resultado = self.auth_controller.authenticate(username, password)
            
            if resultado['success']:
                # Login exitoso
                logger.info(f"✅ Login exitoso para usuario: {username}")
                
                # Guardar preferencia de "recordarme" si está marcada
                if self.remember_checkbox.isChecked():
                    self.save_login_preferences(username)
                
                # Emitir señal con datos del usuario
                self.login_successful.emit(resultado['user_data'])
                
                # Cerrar ventana de login
                QTimer.singleShot(500, self.close)
            else:
                # Error en login
                self.show_error(resultado['message'])
                self.password_input.clear()
                self.password_input.setFocus()
                
        except Exception as e:
            logger.error(f"❌ Error durante autenticación: {e}")
            self.show_error(f"Error del sistema: {str(e)}")
            
        finally:
            # Restaurar estado del botón
            self.login_in_progress = False
            self.login_btn.setEnabled(True)
            self.login_btn.setText("🚪 INGRESAR")
    
    def on_forgot_password(self):
        """Manejador para olvidó contraseña"""
        QMessageBox.information(
            self,
            "Recuperar Contraseña",
            "Por favor contacte al administrador del sistema\n"
            "para restablecer su contraseña.\n\n"
            "Email: admin@despachanet.com\n"
            "Teléfono: +591 2 2777777",
            QMessageBox.StandardButton.Ok
        )
    
    def show_error(self, message):
        """Mostrar mensaje de error"""
        # Primero, limpiar errores anteriores
        self.clear_errors()
        
        # Crear label de error
        error_label = QLabel(message)
        error_label.setObjectName("errorLabel")
        error_label.setStyleSheet("""
            #errorLabel {
                color: #d32f2f;
                background-color: #ffebee;
                border: 1px solid #ef9a9a;
                border-radius: 5px;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
                text-align: center;
                margin-top: 10px;
            }
        """)
        
        # Insertar después del formulario
        layout = self.main_container.layout()
        form_index = -1
        if layout:
            form_frame = self.findChild(QFrame, "formFrame")
            if form_frame:
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() == form_frame:
                        form_index = i
                        break
        
        if form_index != -1 and isinstance(layout, QVBoxLayout):
            layout.insertWidget(form_index + 1, error_label)
    
    def clear_errors(self):
        """Limpiar mensajes de error anteriores"""
        layout = self.main_container.layout()
        if layout:
            for i in reversed(range(layout.count())):
                item = layout.itemAt(i)
                if item:
                    widget = item.widget()
                    if widget and widget.objectName() == "errorLabel":
                        widget.deleteLater()
    
    def save_login_preferences(self, username):
        """Guardar preferencias de login (para recordar usuario)"""
        # Aquí puedes implementar la lógica para guardar en archivo/configuración
        # Por ahora solo se guarda en memoria
        logger.debug(f"💾 Preferencia 'recordarme' guardada para: {username}")
    
    def load_saved_username(self):
        """Cargar usuario guardado si existe"""
        # Implementar si necesitas cargar usuario guardado
        pass
    
    def center_on_screen(self):
        """Centrar ventana en la pantalla"""
        screen_geometry = self.screen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)
    
    def show(self):
        """Mostrar ventana centrada"""
        self.center_on_screen()
        super().show()
    
    def mousePressEvent(self, event):
        """Permitir arrastrar la ventana sin bordes"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        """Mover ventana al arrastrar"""
        if event.buttons() == Qt.MouseButton.LeftButton and hasattr(self, 'drag_position'):
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()