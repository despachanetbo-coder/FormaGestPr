# utils/scheduler.py
from PySide6.QtCore import QTimer
from service.programa_estado_service import ProgramaEstadoService
import logging

logger = logging.getLogger(__name__)

class ProgramaScheduler:
    """Scheduler para tareas automáticas relacionadas con programas"""
    
    def __init__(self, interval_minutos=60):
        self.interval_minutos = interval_minutos
        self.timer = QTimer()
        self.timer.timeout.connect(self.verificar_estados)
    
    def start(self):
        """Inicia el timer para verificación periódica"""
        # Ejecutar primera verificación inmediatamente
        self.verificar_estados()
        
        # Configurar verificaciones periódicas
        self.timer.start(self.interval_minutos * 60 * 1000)  # Convertir a milisegundos
        logger.info(f"🕒 Scheduler iniciado - Verificará cada {self.interval_minutos} minutos")
    
    def stop(self):
        """Detiene el timer"""
        self.timer.stop()
        logger.info("🛑 Scheduler detenido")
    
    def verificar_estados(self):
        """Ejecuta la verificación de estados"""
        logger.debug("🔄 Ejecutando verificación programada de estados...")
        resultado = ProgramaEstadoService.verificar_y_actualizar_estados()
        
        if resultado.get('actualizados', 0) > 0:
            logger.info(f"📊 Verificación programada: {resultado.get('actualizados')} programas concluidos")