# Archivo: config/constants.py
"""
Constantes de la aplicación FormaGestPro
Valores fijos y enumeraciones para uso en toda la aplicación
"""

from enum import Enum

class ExpedicionCI(Enum):
    """Expediciones de Cédula de Identidad"""
    BE = "Beni"
    CH = "Chuquisaca"
    CB = "Cochabamba"
    LP = "La Paz"
    OR = "Oruro"
    PD = "Pando"
    PT = "Potosí"
    SC = "Santa Cruz"
    TJ = "Tarija"
    EX = "Extranjero"
    
    @classmethod
    def get_choices(cls):
        """Obtener lista de opciones para combobox"""
        return [(member.value, member.name) for member in cls]
    
    @classmethod
    def get_codes(cls):
        """Obtener lista de códigos"""
        return [member.name for member in cls]
    
    @classmethod
    def get_names(cls):
        """Obtener lista de nombres"""
        return [member.value for member in cls]

class EstadoPrograma(Enum):
    """Estados de programas académicos"""
    PLANIFICADO = "PLANIFICADO"
    INSCRIPCIONES = "INSCRIPCIONES"
    EN_CURSO = "EN_CURSO"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"
    
    @classmethod
    def get_display_names(cls):
        """Obtener nombres para mostrar en UI"""
        return {
            "PLANIFICADO": "PRE INSCRIPCION",
            "INSCRIPCIONES": "INSCRIPCIONES",
            "EN_CURSO": "INICIADO",
            "CONCLUIDO": "CONCLUIDO",
            "CANCELADO": "CANCELADO"
        }

class EstadoEstudiante(Enum):
    """Estados de estudiante"""
    ACTIVO = "ACTIVO"
    INACTIVO = "INACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    RETIRADO = "RETIRADO"
    
    @classmethod
    def get_colors(cls):
        """Obtener colores para cada estado"""
        return {
            "ACTIVO": "#27ae60",      # Verde
            "INACTIVO": "#e74c3c",    # Rojo
            "SUSPENDIDO": "#f39c12",  # Naranja
            "RETIRADO": "#7f8c8d"     # Gris
        }

class EstadoTransaccion(Enum):
    """Estados de transacciones de pago"""
    REGISTRADO = "REGISTRADO"
    CONFIRMADO = "CONFIRMADO"
    PENDIENTE = "PENDIENTE"
    ANULADO = "ANULADO"
    RECHAZADO = "RECHAZADO"
    
    @classmethod
    def get_display_names(cls):
        """Obtener nombres para mostrar en UI"""
        return {
            "REGISTRADO": "Registrado",
            "CONFIRMADO": "Confirmado",
            "PENDIENTE": "Pendiente",
            "ANULADO": "Anulado",
            "RECHAZADO": "Rechazado"
        }

class FormaPago(Enum):
    """Formas de pago"""
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"
    TARJETA = "TARJETA"
    DEPOSITO = "DEPOSITO"
    QR = "QR"
    
    @classmethod
    def get_display_names(cls):
        """Obtener nombres para mostrar"""
        return {
            "EFECTIVO": "💰 Efectivo",
            "TRANSFERENCIA": "🏦 Transferencia Bancaria",
            "TARJETA": "💳 Tarjeta de Crédito/Débito",
            "DEPOSITO": "🏧 Depósito Bancario",
            "QR": "📱 Pago QR"
        }

class TipoDocumento(Enum):
    """Tipos de documentos aceptados"""
    FOTO = ("Foto", ["jpg", "jpeg", "png"])
    PDF = ("Documento PDF", ["pdf"])
    WORD = ("Documento Word", ["doc", "docx"])
    EXCEL = ("Hoja de cálculo", ["xls", "xlsx"])
    
    def __init__(self, descripcion, extensiones):
        self.descripcion = descripcion
        self.extensiones = extensiones
    
    @classmethod
    def get_filters(cls):
        """Obtener filtros para diálogo de archivos"""
        filters = []
        for tipo in cls:
            filter_str = f"{tipo.descripcion} (*.{' *.'.join(tipo.extensiones)})"
            filters.append(filter_str)
        filters.append("Todos los archivos (*.*)")
        return ";;".join(filters)
    
    @classmethod
    def get_foto_filter(cls):
        """Obtener filtro específico para fotos"""
        tipos_foto = [tipo for tipo in cls if tipo.name == "FOTO"]
        if tipos_foto:
            tipo = tipos_foto[0]
            return f"{tipo.descripcion} (*.{' *.'.join(tipo.extensiones)})"
        return "Imágenes (*.jpg *.jpeg *.png)"

# Constantes de aplicación
class AppConstants:
    """Constantes generales de la aplicación"""
    
    # Nombres de la aplicación
    APP_NAME = "FormaGestPro"
    APP_VERSION = "1.0.0"
    APP_DESCRIPTION = "Sistema de Gestión Académica"
    
    # Configuración de UI
    DEFAULT_WINDOW_WIDTH = 1200
    DEFAULT_WINDOW_HEIGHT = 800
    OVERLAY_WIDTH_PERCENT = 95
    OVERLAY_HEIGHT_PERCENT = 95
    
    # Configuración de base de datos
    DB_HOST = "localhost"
    DB_PORT = 5432
    DB_NAME = "formagestpro_db"
    DB_USER = "postgres"
    DB_PASSWORD = "Despachanet"
    
    # Límites de validación
    MAX_NOMBRE_LENGTH = 100
    MAX_EMAIL_LENGTH = 100
    MAX_TELEFONO_LENGTH = 20
    MAX_DIRECCION_LENGTH = 500
    MAX_PROFESION_LENGTH = 100
    MAX_UNIVERSIDAD_LENGTH = 200
    
    # Formatos de fecha
    DATE_FORMAT = "%Y-%m-%d"
    DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
    DATE_DISPLAY_FORMAT = "%d/%m/%Y"
    
    # Configuración de archivos
    MAX_FILE_SIZE_MB = 5  # 5MB máximo por archivo
    DEFAULT_PHOTO_WIDTH = 300
    DEFAULT_PHOTO_HEIGHT = 300
    
    # Colores de la aplicación
    COLORS = {
        "primary": "#1976D2",
        "primary_dark": "#0D47A1",
        "primary_light": "#64B5F6",
        "secondary": "#FF4081",
        "success": "#4CAF50",
        "warning": "#FF9800",
        "error": "#F44336",
        "info": "#2196F3",
        "background": "#F5F5F5",
        "surface": "#FFFFFF",
        "text_primary": "#212121",
        "text_secondary": "#757575",
        "divider": "#BDBDBD"
    }

# Constantes para mensajes
class Messages:
    """Mensajes de la aplicación"""
    
    # Mensajes de éxito
    SUCCESS_CREATE = "Registro creado exitosamente"
    SUCCESS_UPDATE = "Registro actualizado exitosamente"
    SUCCESS_DELETE = "Registro eliminado exitosamente"
    SUCCESS_ACTIVATE = "Registro activado exitosamente"
    
    # Mensajes de error
    ERROR_REQUIRED_FIELD = "Este campo es obligatorio"
    ERROR_INVALID_EMAIL = "Email inválido"
    ERROR_INVALID_PHONE = "Teléfono inválido"
    ERROR_INVALID_DATE = "Fecha inválida"
    ERROR_INVALID_CI = "Número de CI inválido"
    ERROR_CI_EXISTS = "El número de CI ya está registrado"
    ERROR_EMAIL_EXISTS = "El email ya está registrado"
    ERROR_FILE_TOO_LARGE = "El archivo es demasiado grande"
    ERROR_FILE_TYPE = "Tipo de archivo no permitido"
    
    # Mensajes de confirmación
    CONFIRM_DELETE = "¿Está seguro que desea eliminar este registro?"
    CONFIRM_CANCEL = "¿Está seguro que desea cancelar los cambios?"
    
    # Mensajes de información
    INFO_NO_DATA = "No hay datos para mostrar"
    INFO_LOADING = "Cargando datos..."
    INFO_SAVING = "Guardando datos..."
    INFO_DELETING = "Eliminando registro..."

# Atajo para uso común
EXPEDICIONES_CI = ExpedicionCI.get_codes()
ESTADOS_PROGRAMA_DISPLAY = EstadoPrograma.get_display_names()
FORMAS_PAGO_DISPLAY = FormaPago.get_display_names()
APP_COLORS = AppConstants.COLORS