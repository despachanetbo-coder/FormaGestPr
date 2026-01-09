# Archivo: config/paths.py
"""
Configuración de rutas del sistema FormaGestPro
Maneja las rutas de directorios y archivos de la aplicación
"""

import os
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Paths:
    """Clase para gestionar rutas de la aplicación"""
    
    # Rutas base (se detectan automáticamente)
    BASE_DIR = None
    APP_DIR = None
    ARCHIVOS_DIR = None
    FOTOS_ESTUDIANTES_DIR = None
    CV_DOCENTES_DIR = None
    DOCUMENTOS_DIR = None
    RESPALDOS_DIR = None
    REPORTES_DIR = None
    BACKUP_DIR = None
    
    @classmethod
    def initialize(cls):
        """Inicializar las rutas de la aplicación"""
        try:
            # Detectar directorio base de la aplicación
            if getattr(sys, 'frozen', False):
                # Si la aplicación está congelada (ejecutable)
                cls.BASE_DIR = Path(sys.executable).parent
            else:
                # Si se ejecuta desde código fuente
                cls.BASE_DIR = Path(__file__).parent.parent
            
            # Crear estructura de directorios
            cls.APP_DIR = cls.BASE_DIR
            cls.ARCHIVOS_DIR = cls.APP_DIR / "archivos"
            cls.FOTOS_ESTUDIANTES_DIR = cls.ARCHIVOS_DIR / "estudiantes_fotos"
            cls.CV_DOCENTES_DIR = cls.ARCHIVOS_DIR / "cv_docentes"
            cls.DOCUMENTOS_DIR = cls.ARCHIVOS_DIR / "documentos"
            cls.RESPALDOS_DIR = cls.ARCHIVOS_DIR / "respaldos"
            cls.REPORTES_DIR = cls.ARCHIVOS_DIR / "reportes"
            cls.BACKUP_DIR = cls.ARCHIVOS_DIR / "backups"
            
            # Crear directorios si no existen
            cls._create_directories()
            
            logger.info("✅ Directorios de la aplicación inicializados")
            logger.info(f"   Base: {cls.BASE_DIR}")
            logger.info(f"   Archivos: {cls.ARCHIVOS_DIR}")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando directorios: {e}")
            raise
    
    @classmethod
    def _create_directories(cls):
        """Crear estructura de directorios si no existen"""
        directories = [
            cls.ARCHIVOS_DIR,
            cls.FOTOS_ESTUDIANTES_DIR,
            cls.CV_DOCENTES_DIR,
            cls.DOCUMENTOS_DIR,
            cls.RESPALDOS_DIR,  
            cls.REPORTES_DIR,
            cls.BACKUP_DIR
        ]
        
        for directory in directories:
            if directory is not None:
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    logger.debug(f"Directorio creado/verificado: {directory}")
                except Exception as e:
                    logger.error(f"Error creando directorio {directory}: {e}")
    
    @classmethod
    def get_foto_estudiante_path(cls, ci_numero: str, ci_expedicion: str, extension: str = "jpg") -> Path:
        """
        Obtener ruta completa para foto de estudiante
        
        Args:
            ci_numero: Número de CI
            ci_expedicion: Expedición del CI (ej: 'LP', 'CB')
            extension: Extensión del archivo (jpg, png, jpeg)
        
        Returns:
            Path: Ruta completa del archivo
        """
        from datetime import datetime
        año = datetime.now().year
        
        # Nombre del archivo: CI_NUMERO_EXPEDICION_AÑO.ext
        nombre_archivo = f"{ci_numero}_{ci_expedicion}_{año}.{extension.lower()}"
        if cls.FOTOS_ESTUDIANTES_DIR is None:
            raise RuntimeError("Paths not initialized. Call Paths.initialize() first.")
        return cls.FOTOS_ESTUDIANTES_DIR / nombre_archivo
    
    @classmethod
    def get_foto_estudiante_url(cls, ci_numero: str, ci_expedicion: str, extension: str = "jpg") -> str:
        """
        Obtener URL/path para almacenar en base de datos
        
        Args:
            ci_numero: Número de CI
            ci_expedicion: Expedición del CI
            extension: Extensión del archivo
        
        Returns:
            str: Path para almacenar en BD
        """
        path = cls.get_foto_estudiante_path(ci_numero, ci_expedicion, extension)
        return str(path)
    
    @classmethod
    def get_foto_estudiante_relativa(cls, ci_numero: str, ci_expedicion: str, extension: str = "jpg") -> str:
        """
        Obtener ruta relativa para foto de estudiante
        
        Args:
            ci_numero: Número de CI
            ci_expedicion: Expedición del CI
            extension: Extensión del archivo
        
        Returns:
            str: Ruta relativa (para mostrar en UI)
        """
        from datetime import datetime
        año = datetime.now().year
        return f"archivos/estudiantes_fotos/{ci_numero}_{ci_expedicion}_{año}.{extension.lower()}"
    
    @classmethod
    def get_documento_path(cls, tipo: str, referencia: str, extension: str) -> Path:
        """
        Obtener ruta para documento
        
        Args:
            tipo: Tipo de documento ('contrato', 'certificado', etc.)
            referencia: Referencia única (ID o código)
            extension: Extensión del archivo
        
        Returns:
            Path: Ruta completa
        """
        nombre_archivo = f"{tipo}_{referencia}.{extension.lower()}"
        if cls.DOCUMENTOS_DIR is None:
            raise RuntimeError("Paths not initialized. Call Paths.initialize() first.")
        return cls.DOCUMENTOS_DIR / nombre_archivo
    
    @classmethod
    def get_reporte_path(cls, nombre: str, extension: str = "pdf") -> Path:
        """
        Obtener ruta para reporte
        
        Args:
            nombre: Nombre del reporte
            extension: Extensión del archivo
        
        Returns:
            Path: Ruta completa
        """
        from datetime import datetime
        fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"reporte_{nombre}_{fecha}.{extension.lower()}"
        if cls.REPORTES_DIR is None:
            raise RuntimeError("Paths not initialized. Call Paths.initialize() first.")
        return cls.REPORTES_DIR / nombre_archivo
    
    @classmethod
    def get_backup_path(cls, nombre: str) -> Path:
        """
        Obtener ruta para backup
        
        Args:
            nombre: Nombre del backup
        
        Returns:
            Path: Ruta completa
        """
        from datetime import datetime
        if cls.BACKUP_DIR is None:
            raise RuntimeError("Paths not initialized. Call Paths.initialize() first.")
        fecha = datetime.now().strftime("%Y%m%d")
        nombre_archivo = f"backup_{nombre}_{fecha}.sql"
        return cls.BACKUP_DIR / nombre_archivo
    
    @classmethod
    def archivo_existe(cls, ruta_relativa: str) -> bool:
        """
        Verificar si un archivo existe
        
        Args:
            ruta_relativa: Ruta relativa del archivo
        
        Returns:
            bool: True si existe
        """
        if cls.BASE_DIR is None:
            raise RuntimeError("Paths not initialized. Call Paths.initialize() first.")
        ruta_completa = cls.BASE_DIR / ruta_relativa
        return ruta_completa.exists() and ruta_completa.is_file()
    
    @classmethod
    def obtener_ruta_absoluta(cls, ruta_relativa: str) -> str:
        """
        Obtener ruta absoluta a partir de ruta relativa
        
        Args:
            ruta_relativa: Ruta relativa
        
        Returns:
            str: Ruta absoluta
        """
        if cls.BASE_DIR is None:
            raise RuntimeError("Paths not initialized. Call Paths.initialize() first.")
        ruta_completa = cls.BASE_DIR / ruta_relativa
        return str(ruta_completa)
    
    @classmethod
    def obtener_ruta_relativa(cls, ruta_absoluta: str) -> str:
        """
        Obtener ruta relativa a partir de ruta absoluta
        
        Args:
            ruta_absoluta: Ruta absoluta
        
        Returns:
            str: Ruta relativa respecto al directorio base
        """
        ruta_absoluta_path = Path(ruta_absoluta)
        try:
            if cls.BASE_DIR is None:
                raise RuntimeError("Paths not initialized. Call Paths.initialize() first.")
            return str(ruta_absoluta_path.relative_to(cls.BASE_DIR))
        except ValueError:
            # Si no es subdirectorio del BASE_DIR, devolver la ruta absoluta
            return ruta_absoluta
    
    @classmethod
    def limpiar_nombre_archivo(cls, nombre: str) -> str:
        """
        Limpiar nombre de archivo para evitar problemas con el sistema
        
        Args:
            nombre: Nombre original
        
        Returns:
            str: Nombre limpio
        """
        # Caracteres prohibidos en Windows
        caracteres_prohibidos = ['<', '>', ':', '"', '|', '?', '*', '\\', '/']
        for char in caracteres_prohibidos:
            nombre = nombre.replace(char, '_')
        
        # Limitar longitud
        if len(nombre) > 255:
            nombre = nombre[:250]
        
        return nombre

# Inicializar rutas al importar
Paths.initialize()