# Archivo: main.py (versión actualizada con verificación de programas)
import sys
import os
from PySide6.QtWidgets import QApplication
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,  # Cambiado a INFO para producción
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('formagestpro.log', mode='a', encoding='utf-8')  # Cambiado a append
    ]
)

# Asegurar que Python encuentre los módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from view.login_window import LoginWindow
from controller.main_controller import MainController

# Importar servicios de verificación
from service.programa_estado_service import ProgramaEstadoService
from utils.verificacion_inicio import ejecutar_verificacion_inicial
from utils.scheduler import ProgramaScheduler

logger = logging.getLogger(__name__)

class ApplicationManager:
    """Gestor principal de la aplicación"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = None
        self.main_controller = None
        self.scheduler = None
        
        # Configuración global
        self.app.setApplicationName("FormaGestPro")
        self.app.setOrganizationName("DespachaNet")
        
        # Ejecutar verificaciones al inicio (sin necesidad de login)
        self._ejecutar_verificaciones_iniciales()
    
    def _ejecutar_verificaciones_iniciales(self):
        """Ejecuta verificaciones automáticas al iniciar la aplicación"""
        try:
            logger.info("🚀 Iniciando verificaciones automáticas del sistema...")
            
            # Verificar programas que deben ser concluidos
            resultado = ejecutar_verificacion_inicial()
            
            if resultado.get('success'):
                if resultado.get('actualizados', 0) > 0:
                    logger.info(f"✅ {resultado.get('actualizados')} programas concluidos automáticamente")
                else:
                    logger.info("✅ No hay programas pendientes de concluir")
            else:
                logger.error(f"❌ Error en verificación inicial: {resultado.get('mensaje')}")
                
        except Exception as e:
            logger.error(f"Error ejecutando verificaciones iniciales: {e}")
    
    def _iniciar_scheduler(self):
        """Inicia el scheduler para verificaciones periódicas (solo después de login)"""
        try:
            # Iniciar scheduler para verificar cada hora
            self.scheduler = ProgramaScheduler(interval_minutos=60)
            self.scheduler.start()
            logger.info("🕒 Scheduler de verificaciones iniciado")
        except Exception as e:
            logger.error(f"Error iniciando scheduler: {e}")
    
    def show_login(self):
        """Mostrar ventana de login"""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_successful)
        self.login_window.show()
    
    def on_login_successful(self, user_data):
        """Manejador para login exitoso"""
        logger.info(f"✅ Login exitoso para: {user_data.get('username')}")
        
        # Crear y mostrar ventana principal
        self.main_controller = MainController(user_data=user_data)
        self.main_controller.show_window()
        
        # Iniciar verificaciones periódicas después del login
        self._iniciar_scheduler()
        
        # Conectar señal de cierre de aplicación
        self.app.aboutToQuit.connect(self._on_app_quit)
        
        # Cerrar ventana de login
        if self.login_window:
            self.login_window.close()
    
    def _on_app_quit(self):
        """Manejador cuando la aplicación se cierra"""
        logger.info("🛑 Cerrando aplicación...")
        
        # Detener scheduler si está activo
        if self.scheduler:
            self.scheduler.stop()
            logger.info("✅ Scheduler detenido correctamente")
    
    def run(self):
        """Ejecutar la aplicación"""
        self.show_login()
        return self.app.exec()

def main():
    """Punto de entrada principal de la aplicación"""
    try:
        manager = ApplicationManager()
        sys.exit(manager.run())
    except Exception as e:
        logger.critical(f"Error fatal en la aplicación: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()