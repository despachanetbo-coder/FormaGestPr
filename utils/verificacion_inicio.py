# utils/verificacion_inicio.py
"""
Script para ejecutar la verificación de estados al iniciar la aplicación
"""
import logging
from service.programa_estado_service import ProgramaEstadoService

logger = logging.getLogger(__name__)

def ejecutar_verificacion_inicial():
    """
    Ejecuta la verificación de estados al iniciar la aplicación
    """
    logger.info("🚀 Ejecutando verificación inicial de estados de programas...")
    
    resultado = ProgramaEstadoService.verificar_y_actualizar_estados()
    
    if resultado.get('success'):
        if resultado.get('actualizados', 0) > 0:
            logger.info(f"✅ Verificación inicial completada: {resultado.get('actualizados')} programas concluidos")
        else:
            logger.info("✅ Verificación inicial completada: No hay programas pendientes")
    else:
        logger.error(f"❌ Error en verificación inicial: {resultado.get('mensaje')}")
    
    return resultado