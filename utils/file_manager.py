# Archivo: utils/file_manager.py
"""
Utilidad para manejo de archivos y fotos en FormaGestPro
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QPixmap, QImage, QImageReader, QColor
from PySide6.QtCore import Qt
import logging

from config.paths import Paths
from config.constants import TipoDocumento, AppConstants, Messages

logger = logging.getLogger(__name__)

class FileManager:
    """Clase para manejar operaciones con archivos"""
    
    @staticmethod
    def seleccionar_imagen(parent_widget, titulo="Seleccionar imagen", directorio_inicial=""):
        """
        Abrir diálogo para seleccionar imagen
        
        Args:
            parent_widget: Widget padre
            titulo: Título del diálogo
            directorio_inicial: Directorio inicial
        
        Returns:
            str: Ruta del archivo seleccionado o cadena vacía
        """
        try:
            filtro = TipoDocumento.get_foto_filter()
            archivo, _ = QFileDialog.getOpenFileName(
                parent_widget,
                titulo,
                directorio_inicial,
                filtro
            )
            
            if archivo:
                # Validar tamaño del archivo
                if not FileManager.validar_tamano_archivo(archivo):
                    QMessageBox.warning(
                        parent_widget,
                        "Archivo muy grande",
                        f"El archivo excede el tamaño máximo de {AppConstants.MAX_FILE_SIZE_MB}MB"
                    )
                    return ""
                
                # Validar que sea una imagen válida
                if not FileManager.es_imagen_valida(archivo):
                    QMessageBox.warning(
                        parent_widget,
                        "Imagen inválida",
                        "El archivo seleccionado no es una imagen válida o está dañado"
                    )
                    return ""
                
                logger.info(f"Imagen seleccionada: {archivo}")
                return archivo
            
            return ""
            
        except Exception as e:
            logger.error(f"Error seleccionando imagen: {e}")
            QMessageBox.critical(
                parent_widget,
                "Error",
                f"No se pudo seleccionar la imagen: {str(e)}"
            )
            return ""
    
    @staticmethod
    def copiar_foto_estudiante(origen: str, ci_numero: str, ci_expedicion: str) -> Tuple[bool, str, str]:
        """
        Copiar foto de estudiante al directorio de fotos
        
        Args:
            origen: Ruta del archivo origen
            ci_numero: Número de CI del estudiante
            ci_expedicion: Expedición del CI
        
        Returns:
            Tuple[bool, str, str]: (éxito, mensaje, ruta_destino)
        """
        try:
            if not origen or not os.path.exists(origen):
                return False, "El archivo origen no existe", ""
            
            # Obtener extensión del archivo
            extension = Path(origen).suffix.lower().lstrip('.')
            if extension not in ['jpg', 'jpeg', 'png']:
                extension = 'jpg'  # Extensión por defecto
            
            # Generar ruta destino
            ruta_destino = Paths.get_foto_estudiante_path(ci_numero, ci_expedicion, extension)
            
            # Si ya existe una foto anterior, eliminarla
            if ruta_destino.exists():
                try:
                    ruta_destino.unlink()
                    logger.info(f"Foto anterior eliminada: {ruta_destino}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar foto anterior: {e}")
            
            # Copiar archivo
            shutil.copy2(origen, ruta_destino)
            
            # Obtener ruta para almacenar en BD
            ruta_bd = Paths.get_foto_estudiante_url(ci_numero, ci_expedicion, extension)
            
            logger.info(f"Foto copiada: {origen} -> {ruta_destino}")
            return True, "Foto guardada exitosamente", ruta_bd
            
        except Exception as e:
            logger.error(f"Error copiando foto: {e}")
            return False, f"Error al copiar foto: {str(e)}", ""
    
    @staticmethod
    def cargar_foto_estudiante(ruta_bd: str, ancho: Optional[int] = None, alto: Optional[int] = None) -> Optional[QPixmap]:
        """
        Cargar foto de estudiante desde ruta de BD
        
        Args:
            ruta_bd: Ruta almacenada en base de datos
            ancho: Ancho deseado (opcional)
            alto: Alto deseado (opcional)
        
        Returns:
            QPixmap: Imagen cargada o None
        """
        try:
            if not ruta_bd or ruta_bd.strip() == "":
                return None
            
            # Verificar si la ruta existe
            if not os.path.exists(ruta_bd):
                # Intentar con ruta relativa
                ruta_relativa = Paths.obtener_ruta_relativa(ruta_bd)
                ruta_absoluta = Paths.obtener_ruta_absoluta(ruta_relativa)
                
                if not os.path.exists(ruta_absoluta):
                    logger.warning(f"Foto no encontrada: {ruta_bd}")
                    return None
                
                ruta_bd = ruta_absoluta
            
            # Cargar imagen
            pixmap = QPixmap(ruta_bd)
            
            if pixmap.isNull():
                logger.error(f"No se pudo cargar la imagen: {ruta_bd}")
                return None
            
            # Redimensionar si se especifican dimensiones
            if ancho and alto:
                pixmap = pixmap.scaled(
                    ancho, alto,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            
            return pixmap
            
        except Exception as e:
            logger.error(f"Error cargando foto: {e}")
            return None
    
    @staticmethod
    def obtener_foto_por_defecto(tipo="estudiante") -> QPixmap:
        """
        Obtener foto por defecto
        
        Args:
            tipo: Tipo de foto ('estudiante' o 'docente')
        
        Returns:
            QPixmap: Foto por defecto
        """
        try:
            # Crear una imagen por defecto simple
            pixmap = QPixmap(AppConstants.DEFAULT_PHOTO_WIDTH, AppConstants.DEFAULT_PHOTO_HEIGHT)
            
            # Rellenar con color según tipo
            if tipo == "estudiante":
                color = QColor(Qt.GlobalColor.blue)
                texto = "FOTO\nESTUDIANTE"
            else:
                color = QColor(Qt.GlobalColor.green)
                texto = "FOTO\nDOCENTE"
            
            pixmap.fill(color.lighter(150))  # Ahora funciona correctamente [web:8]
            
            # Podrías añadir texto o icono aquí si lo deseas
            # Esta es una implementación básica
            
            return pixmap
            
        except Exception as e:
            logger.error(f"Error creando foto por defecto: {e}")
            # Devolver pixmap vacío como fallback
            return QPixmap(AppConstants.DEFAULT_PHOTO_WIDTH, AppConstants.DEFAULT_PHOTO_HEIGHT)
    
    @staticmethod
    def validar_tamano_archivo(ruta_archivo: str) -> bool:
        """
        Validar que el archivo no exceda el tamaño máximo
        
        Args:
            ruta_archivo: Ruta del archivo
        
        Returns:
            bool: True si el tamaño es válido
        """
        try:
            tamano_bytes = os.path.getsize(ruta_archivo)
            tamano_mb = tamano_bytes / (1024 * 1024)
            return tamano_mb <= AppConstants.MAX_FILE_SIZE_MB
        except Exception as e:
            logger.error(f"Error obteniendo tamaño de archivo: {e}")
            return False
    
    @staticmethod
    def es_imagen_valida(ruta_archivo: str) -> bool:
        """
        Verificar si un archivo es una imagen válida
        
        Args:
            ruta_archivo: Ruta del archivo
        
        Returns:
            bool: True si es una imagen válida
        """
        try:
            reader = QImageReader(ruta_archivo)
            return reader.canRead()
        except Exception as e:
            logger.error(f"Error verificando imagen: {e}")
            return False
    
    @staticmethod
    def eliminar_foto_estudiante(ci_numero: str, ci_expedicion: str) -> bool:
        """
        Eliminar foto de estudiante
        
        Args:
            ci_numero: Número de CI
            ci_expedicion: Expedición del CI
        
        Returns:
            bool: True si se eliminó exitosamente
        """
        try:
            # Buscar archivos con diferentes extensiones
            extensiones = ['jpg', 'jpeg', 'png']
            eliminado = False
            
            for extension in extensiones:
                ruta = Paths.get_foto_estudiante_path(ci_numero, ci_expedicion, extension)
                if ruta.exists():
                    ruta.unlink()
                    eliminado = True
                    logger.info(f"Foto eliminada: {ruta}")
            
            return eliminado
            
        except Exception as e:
            logger.error(f"Error eliminando foto: {e}")
            return False
    
    @staticmethod
    def obtener_informacion_archivo(ruta_archivo: str) -> Dict[str, Any]:
        """
        Obtener información de un archivo
        
        Args:
            ruta_archivo: Ruta del archivo
        
        Returns:
            Dict: Información del archivo
        """
        try:
            if not os.path.exists(ruta_archivo):
                return {}
            
            stats = os.stat(ruta_archivo)
            
            return {
                'nombre': Path(ruta_archivo).name,
                'ruta': ruta_archivo,
                'tamano_bytes': stats.st_size,
                'tamano_mb': stats.st_size / (1024 * 1024),
                'fecha_modificacion': stats.st_mtime,
                'extension': Path(ruta_archivo).suffix.lower().lstrip('.'),
                'existe': True
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información de archivo: {e}")
            return {}
    
    @staticmethod
    def redimensionar_imagen(ruta_origen: str, ruta_destino: str, 
                           ancho: int, alto: int, 
                           calidad: int = 85) -> bool:
        """
        Redimensionar una imagen
        
        Args:
            ruta_origen: Ruta de la imagen origen
            ruta_destino: Ruta de destino
            ancho: Nuevo ancho
            alto: Nuevo alto
            calidad: Calidad de compresión (0-100)
        
        Returns:
            bool: True si se redimensionó exitosamente
        """
        try:
            pixmap = QPixmap(ruta_origen)
            if pixmap.isNull():
                return False
            
            # Redimensionar manteniendo la relación de aspecto
            pixmap_redimensionada = pixmap.scaled(
                ancho, alto,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            
            # Guardar la imagen
            return pixmap_redimensionada.save(ruta_destino, quality=calidad)
            
        except Exception as e:
            logger.error(f"Error redimensionando imagen: {e}")
            return False