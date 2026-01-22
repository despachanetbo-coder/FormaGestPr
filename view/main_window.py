# Archivo: view/main_window.py
import os
import sys
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QLabel, QMessageBox,
    QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QResizeEvent

# Importar MainTab y las pestañas concretas
from .tabs.base_tab import BaseTab
from .tabs.inicio_tab import InicioTab
from .tabs.resumen_tab import ResumenTab
from .tabs.ayuda_tab import AyudaTab

# Importar controladores
from controller.programa_controller import ProgramaController
from utils.unxx_converter import UNSXXConverter


class MainWindow(QMainWindow):
    """Ventana principal con pestañas que heredan de MainTab y sistema de overlays"""
    
    def __init__(self, 
                user_data: Optional[Dict[str, Any]] = None,
                base_qss: str = "view/styles/base.qss",
                color_qss: str = "view/styles/light.qss",
                enable_hot_reload: bool = False):
        super().__init__()
        
        # ✅ Almacenar datos del usuario
        self.user_data = user_data or {}
        
        self.base_qss_file = base_qss
        self.color_qss_file = color_qss
        self.enable_hot_reload = enable_hot_reload
        
        # Diccionario para almacenar referencias a las pestañas
        self.tabs_dict: Dict[int, BaseTab] = {}
        
        # Inicializar controladores
        self.programa_controller = ProgramaController()
        
        # Inicializar sistema de overlays
        self.setup_overlay_system()
        
        # Inicializar overlays (lazy initialization)
        self.overlay_programa = None
        self.overlay_estudiante = None
        self.overlay_docente = None
        
        self.init_ui()
        self.load_styles()

        if enable_hot_reload:
            self.setup_style_watcher()
        
    def setup_overlay_system(self):
        """Configurar sistema global de overlays"""
        # Widget oscurecedor
        self.overlay_darkener = QWidget(self)
        self.overlay_darkener.setObjectName("globalOverlayDarkener")
        self.overlay_darkener.setStyleSheet("""
            #globalOverlayDarkener {
                background-color: rgba(10, 31, 68, 180);
            }
        """)
        self.overlay_darkener.hide()
        self.overlay_darkener.lower()
        
        # Track overlays activos
        self.active_overlays = set()
        
    def init_ui(self) -> None:
        """Inicializar la interfaz de usuario con pestañas"""
        self.setWindowTitle("Sistema de Gestión Académica")
        self.setGeometry(100, 100, 1200, 800)
        
        # Crear widget de pestañas
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabWidget")
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tab_widget)
        
        # Configurar propiedades del widget de pestañas
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setMovable(True)
        self.tab_widget.setTabsClosable(False)
        
        # Crear las pestañas usando las clases específicas
        self._create_tabs()
        
    def _create_tabs(self) -> None:
        """Crear todas las pestañas de la aplicación"""
        
        # ✅ CAMBIO: Pasar user_data a las pestañas
        # Pestaña 1: Inicio
        inicio_tab = InicioTab(user_data=self.user_data)  # Pasar user_data
        self._add_tab_to_widget(inicio_tab, 0)
        
        # Pestaña 3: Análisis
        analisis_tab = self._create_basic_tab(
            "analisis_tab", 
            "📈 Análisis", 
            "Herramientas de análisis de datos",
            user_data=self.user_data  # Pasar user_data
        )
        self._add_tab_to_widget(analisis_tab, 1)
        
        # Pestaña 4: Reportes
        reportes_tab = ResumenTab(user_data=self.user_data)
        self._add_tab_to_widget(reportes_tab, 2)
        
        # Pestaña 5: Configuración
        config_tab = self._create_basic_tab(
            "config_tab", 
            "⚙️ Configuración", 
            "Aquí va la configuración de la aplicación",
            user_data=self.user_data  # Pasar user_data
        )
        self._add_tab_to_widget(config_tab, 3)
        
        # Pestaña 6: Ayuda
        ayuda_tab = AyudaTab(user_data=self.user_data)
        self._add_tab_to_widget(ayuda_tab, 4)

    def _add_tab_to_widget(self, tab: BaseTab, index: int) -> None:
        """Agregar una pestaña al widget y guardar referencia"""
        self.tab_widget.insertTab(index, tab, tab.get_tab_name())
        self.tabs_dict[index] = tab
        
        # Pasar referencia a MainWindow a la pestaña de inicio
        if isinstance(tab, InicioTab):
            tab.main_window = self
    
    def _create_basic_tab(self, tab_id: str, tab_name: str, content: str, user_data=None) -> BaseTab:
        """Crear una pestaña básica con contenido simple"""
        
        class BasicTab(BaseTab):
            def __init__(self, user_data=None):  # ✅ Agregar parámetro
                # ✅ Pasar user_data al constructor base
                super().__init__(tab_id=tab_id, tab_name=tab_name)
                self.user_data = user_data or {}  # ✅ Almacenar user_data
            
            def _init_ui(self):
                label = QLabel(content)
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                label.setWordWrap(True)
                self.add_widget(label, stretch=1)
        
        return BasicTab(user_data=user_data)  # ✅ Pasar user_data
    
    def _on_tab_changed(self, index: int) -> None:
        """Manejador cuando cambia la pestaña seleccionada"""
        # Notificar a la pestaña anterior
        if hasattr(self, 'previous_tab_index') and self.previous_tab_index in self.tabs_dict:
            old_tab = self.tabs_dict[self.previous_tab_index]
            try:
                old_tab.on_tab_deselected()
            except Exception as e:
                print(f"Error en on_tab_deselected: {e}")
        
        # Notificar a la nueva pestaña
        if index in self.tabs_dict:
            new_tab = self.tabs_dict[index]
            try:
                new_tab.on_tab_selected()
            except Exception as e:
                print(f"Error en on_tab_selected: {e}")
        
        # Guardar índice actual para la próxima vez
        self.previous_tab_index = index
    
    # ===== MÉTODOS DE OVERLAYS SIMPLIFICADOS =====
    
    def _init_overlay_programa(self):
        """Inicializar overlay de programa - REEMPLAZAR"""
        if self.overlay_programa is None:
            try:
                from .overlays.programa_overlay import ProgramaOverlay
                self.overlay_programa = ProgramaOverlay(self)
                # Conectar señales de datos
                self.overlay_programa.programa_guardado.connect(self._on_programa_guardado)
                self.overlay_programa.programa_actualizado.connect(self._on_programa_actualizado)
                self.overlay_programa.programa_eliminado.connect(self._on_programa_eliminado)
                # Conectar señal de cierre UNA VEZ
                self.overlay_programa.overlay_closed.connect(
                    lambda: self._on_overlay_closed(self.overlay_programa)
                )
                print("✅ ProgramaOverlay inicializado")
            except ImportError as e:
                print(f"❌ No se pudo importar ProgramaOverlay: {e}")
                self.overlay_programa = None

    def _init_overlay_estudiante(self):
        """Inicializar overlay de estudiante - REEMPLAZAR"""
        if self.overlay_estudiante is None:
            try:
                from .overlays.estudiante_overlay import EstudianteOverlay
                self.overlay_estudiante = EstudianteOverlay(self)
                # Conectar señales de datos
                self.overlay_estudiante.estudiante_creado.connect(self._on_estudiante_guardado)
                self.overlay_estudiante.estudiante_actualizado.connect(self._on_estudiante_actualizado)
                self.overlay_estudiante.estudiante_eliminado.connect(self._on_estudiante_eliminado)
                # Conectar señal de cierre UNA VEZ
                self.overlay_estudiante.overlay_closed.connect(
                    lambda: self._on_overlay_closed(self.overlay_estudiante)
                )
                print("✅ EstudianteOverlay inicializado")
            except ImportError as e:
                print(f"❌ No se pudo importar EstudianteOverlay: {e}")
                self.overlay_estudiante = None

    def _init_overlay_docente(self):
        """Inicializar overlay de docente - REEMPLAZAR"""
        if self.overlay_docente is None:
            try:
                from .overlays.docente_overlay import DocenteOverlay
                self.overlay_docente = DocenteOverlay(self)
                # Conectar señales de datos
                self.overlay_docente.docente_creado.connect(self._on_docente_guardado)
                self.overlay_docente.docente_actualizado.connect(self._on_docente_actualizado)
                self.overlay_docente.docente_eliminado.connect(self._on_docente_eliminado)
                # Conectar señal de cierre UNA VEZ
                self.overlay_docente.overlay_closed.connect(
                    lambda: self._on_overlay_closed(self.overlay_docente)
                )
                print("✅ DocenteOverlay inicializado")
            except ImportError as e:
                print(f"❌ No se pudo importar DocenteOverlay: {e}")
                self.overlay_docente = None

    def show_overlay(self, overlay_widget):
        """Mostrar cualquier overlay con oscurecimiento - REEMPLAZAR"""
        print(f"🔵 show_overlay() para {overlay_widget.__class__.__name__ if overlay_widget else 'None'}")

        if overlay_widget is None:
            print("❌ Error: Overlay no inicializado")
            return False

        # Ajustar tamaño al 95% de la ventana principal
        parent_size = self.size()
        overlay_width = int(parent_size.width() * 0.95)
        overlay_height = int(parent_size.height() * 0.95)

        # Calcular posición para centrar
        overlay_x = (parent_size.width() - overlay_width) // 2
        overlay_y = (parent_size.height() - overlay_height) // 2

        # Configurar geometría del overlay
        overlay_widget.setGeometry(overlay_x, overlay_y, overlay_width, overlay_height)

        # Agregar a overlays activos (SET evita duplicados)
        self.active_overlays.add(overlay_widget)
        print(f"   Overlays activos: {len(self.active_overlays)}")

        # Mostrar oscurecedor (siempre que haya al menos un overlay)
        self.overlay_darkener.setGeometry(self.rect())
        self.overlay_darkener.show()
        self.overlay_darkener.raise_()

        # Mostrar overlay
        overlay_widget.show()
        overlay_widget.raise_()

        print(f"✅ Overlay mostrado: {overlay_widget.__class__.__name__}")
        return True

    def _on_overlay_closed(self, overlay_widget):
        """Manejador cuando se cierra un overlay - VERSIÓN SIMPLE Y CORRECTA"""
        print(f"🔵 CERRANDO overlay: {overlay_widget.__class__.__name__ if overlay_widget else 'None'}")

        if not overlay_widget:
            return

        # 1. Ocultar el overlay (NO necesita geometría para hide)
        overlay_widget.hide()

        # 2. Remover de overlays activos (usar discard para evitar errores)
        self.active_overlays.discard(overlay_widget)

        # 3. Debug: mostrar estado
        print(f"   Overlays activos restantes: {len(self.active_overlays)}")

        # 4. Ocultar oscurecedor SOLO si no hay overlays activos
        if not self.active_overlays:
            # Ocultar inmediatamente
            self.overlay_darkener.hide()
            # Forzar actualización
            self.overlay_darkener.update()
            self.update()
            print("✅ Oscurecedor OCULTADO (no hay overlays)")
        else:
            print(f"⚠️  Oscurecedor MANTENIDO ({len(self.active_overlays)} overlay(s) activo(s))")

    def hide_overlay(self, overlay_widget):
        """Ocultar overlay específico - REEMPLAZAR (alias para compatibilidad)"""
        self._on_overlay_closed(overlay_widget)

    def close_all_overlays(self):
        """Cerrar todos los overlays activos - REEMPLAZAR"""
        print(f"🔵 close_all_overlays() - {len(self.active_overlays)} overlay(s) activo(s)")

        # Crear lista para evitar modificar el set durante la iteración
        overlays_to_close = list(self.active_overlays)

        for overlay in overlays_to_close:
            if overlay:
                overlay.hide()
                if overlay in self.active_overlays:
                    self.active_overlays.remove(overlay)

        # Ocultar oscurecedor
        self.overlay_darkener.hide()
        self.overlay_darkener.update()

        print("✅ Todos los overlays cerrados")

    def resizeEvent(self, event):
        """Manejar redimensionamiento de la ventana principal - REEMPLAZAR"""
        super().resizeEvent(event)

        # Actualizar tamaño del oscurecedor global
        self.overlay_darkener.setGeometry(self.rect())

        # Redimensionar overlays activos que estén visibles
        for overlay in self.active_overlays:
            if overlay and overlay.isVisible():
                parent_size = self.size()
                overlay_width = int(parent_size.width() * 0.95)
                overlay_height = int(parent_size.height() * 0.95)

                # Calcular posición para centrar
                overlay_x = (parent_size.width() - overlay_width) // 2
                overlay_y = (parent_size.height() - overlay_height) // 2

                overlay.setGeometry(overlay_x, overlay_y, overlay_width, overlay_height)
    
    # ===== MÉTODOS DE MENSAJES =====
    
    def mostrar_mensaje(self, mensaje: str, tipo: str = "info", duracion: int = 3000) -> None:
        """
        Mostrar un mensaje emergente

        Args:
            mensaje: Texto del mensaje
            tipo: Tipo de mensaje ("info", "exito", "error", "advertencia")
            duracion: Duración en milisegundos (0 para permanente)
        """
        # Mapear tipo a QMessageBox.Icon
        icon_map = {
            "info": QMessageBox.Icon.Information,
            "exito": QMessageBox.Icon.Information,
            "error": QMessageBox.Icon.Critical,
            "advertencia": QMessageBox.Icon.Warning
        }

        icon = icon_map.get(tipo, QMessageBox.Icon.Information)

        # Crear y mostrar mensaje
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setText(mensaje)
        msg_box.setWindowTitle(tipo.capitalize())

        # Configurar botones según tipo
        if tipo == "error":
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        else:
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)

        msg_box.exec()

        # También imprimir en consola
        icon_char = "✅" if tipo == "exito" else "❌" if tipo == "error" else "⚠️" if tipo == "advertencia" else "ℹ️"
        print(f"{icon_char} {mensaje}")
    
    # ===== MÉTODOS DE PROGRAMA =====
    
    def mostrar_nuevo_programa(self):
        """Mostrar overlay para crear nuevo programa"""
        self._init_overlay_programa()
        
        if not self.overlay_programa:
            self.mostrar_mensaje("Error al inicializar el overlay de programa", "error")
            return
            
        try:
            self.overlay_programa.clear_form()
            self.overlay_programa.set_titulo("🏛️ Nuevo Programa Académico - UNSXX")
            self.overlay_programa.modo = "nuevo"
            self.overlay_programa.programa_id = None
            self.overlay_programa.show_form()
            
            # Mostrar con oscurecimiento
            self.show_overlay(self.overlay_programa)
            
        except Exception as e:
            print(f"❌ Error al mostrar overlay de programa: {e}")
            self.mostrar_mensaje(f"Error al mostrar formulario: {str(e)}", "error")
        
    def mostrar_editar_programa(self, programa_id: int):
        """Mostrar overlay para editar programa existente"""
        self._init_overlay_programa()
        
        if not self.overlay_programa:
            self.mostrar_mensaje("Error al inicializar el overlay de programa", "error")
            return
            
        resultado = self.programa_controller.obtener_programa(programa_id)
        
        if resultado['success']:
            try:
                # Convertir datos estándar a UNSXX
                converter = UNSXXConverter()
                unsxx_data = converter.convertir_programa_a_unsxx(resultado['data'])
                unsxx_data['id'] = programa_id
                
                # Cargar datos en el overlay
                self.overlay_programa.show_form(
                    solo_lectura=False, 
                    datos=unsxx_data, 
                    modo="editar"
                )
                self.overlay_programa.set_titulo("🏛️ Editar Programa Académico - UNSXX")
                self.overlay_programa.modo = "editar"
                self.overlay_programa.programa_id = programa_id
                
                # Mostrar con oscurecimiento
                self.show_overlay(self.overlay_programa)
                
            except Exception as e:
                print(f"❌ Error al cargar datos en overlay: {e}")
                self.mostrar_mensaje(f"Error al cargar datos: {str(e)}", "error")
        else:
            print(f"❌ Error: {resultado['message']}")
            self.mostrar_mensaje(resultado['message'], "error")
    
    def _on_programa_guardado(self, unsxx_data: dict) -> None:
        """Manejador cuando se guarda un nuevo programa"""
        print("=" * 50)
        print("✅ _on_programa_guardado EJECUTADO en MainWindow!")
        
        if not unsxx_data:
            print("❌ Error: Datos vacíos recibidos")
            self.mostrar_mensaje("No se recibieron datos del formulario", "error")
            return
        
        print(f"Datos recibidos: {unsxx_data.get('codigo', 'Sin código')}")
        
        try:
            # 1. Convertir datos UNSXX a formato estándar
            converter = UNSXXConverter()
            programa_data = converter.convertir_unsxx_a_programa(unsxx_data)
            
            if not programa_data:
                print("❌ Error: No se pudieron convertir los datos")
                self.mostrar_mensaje("Error al procesar datos del programa", "error")
                return
            
            print(f"✅ Datos convertidos: {programa_data.get('codigo')}")
            
            # 2. Crear el programa
            resultado = self.programa_controller.crear_programa(programa_data)
            
            # 3. Mostrar resultado
            if resultado.get('success'):
                print(f"✅ Programa guardado exitosamente")
                self.mostrar_mensaje(
                    f"Programa '{programa_data.get('codigo')}' creado exitosamente", 
                    "exito"
                )
                
                # Actualizar lista si existe
                self.actualizar_lista_programas()
            else:
                print(f"❌ Error al guardar: {resultado.get('message')}")
                self.mostrar_mensaje(
                    f"Error al guardar programa: {resultado.get('message')}", 
                    "error"
                )
                
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
        
        print("=" * 50)
    
    def _on_programa_actualizado(self, unsxx_data: dict) -> None:
        """Manejador cuando se actualiza un programa existente"""
        print("=" * 50)
        print("✅ _on_programa_actualizado EJECUTADO en MainWindow!")
        
        if not unsxx_data:
            print("❌ Error: Datos vacíos recibidos")
            self.mostrar_mensaje("No se recibieron datos del formulario", "error")
            return
        
        programa_id = unsxx_data.get('id')
        if not programa_id:
            print("❌ Error: No se recibió ID del programa")
            self.mostrar_mensaje("Error: No se identificó el programa a actualizar", "error")
            return
        
        print(f"Actualizando programa ID: {programa_id}, Código: {unsxx_data.get('codigo', 'Sin código')}")
        
        try:
            # 1. Convertir datos UNSXX a formato estándar
            converter = UNSXXConverter()
            programa_data = converter.convertir_unsxx_a_programa(unsxx_data)
            
            if not programa_data:
                print("❌ Error: No se pudieron convertir los datos")
                self.mostrar_mensaje("Error al procesar datos del programa", "error")
                return
            
            # 2. Actualizar el programa
            resultado = self.programa_controller.actualizar_programa(programa_id, programa_data)
            
            # 3. Mostrar resultado
            if resultado.get('success'):
                print(f"✅ Programa actualizado exitosamente")
                self.mostrar_mensaje(
                    f"Programa '{programa_data.get('codigo')}' actualizado exitosamente", 
                    "exito"
                )
                
                # Actualizar lista si existe
                self.actualizar_lista_programas()
            else:
                print(f"❌ Error al actualizar: {resultado.get('message')}")
                self.mostrar_mensaje(
                    f"Error al actualizar programa: {resultado.get('message')}", 
                    "error"
                )
                
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            import traceback
            traceback.print_exc()
            self.mostrar_mensaje(f"Error inesperado: {str(e)}", "error")
        
        print("=" * 50)
    
    def _on_programa_eliminado(self, programa_id: int):
        """Eliminar un programa"""
        respuesta = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Está seguro que desea eliminar (cancelar) este programa?\n\n"
            "Esta acción cambiaría el estado del programa a 'CANCELADO'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if respuesta == QMessageBox.StandardButton.Yes:
            resultado = self.programa_controller.eliminar_programa(programa_id)
            
            if resultado['success']:
                print(f"✅ {resultado['message']}")
                self.actualizar_lista_programas()
                self.mostrar_mensaje("Programa eliminado (cancelado) exitosamente", tipo="exito")
            else:
                print(f"❌ Error: {resultado['message']}")
                self.mostrar_mensaje(resultado['message'], tipo="error")
    
    def activar_programa(self, programa_id: int):
        """Activar un programa previamente cancelado"""
        resultado = self.programa_controller.actualizar_programa(
            programa_id, 
            {'estado': 'ACTIVO'}
        )
        
        if resultado.get('success'):
            print(f"✅ {resultado.get('message', 'Programa activado')}")
            self.actualizar_lista_programas()
            self.mostrar_mensaje("Programa activado exitosamente", tipo="exito")
        else:
            print(f"❌ Error: {resultado.get('message', 'Error desconocido')}")
            self.mostrar_mensaje(resultado.get('message', 'Error al activar programa'), tipo="error")
    
    def buscar_programas(self, filtros: Optional[dict] = None):
        """Buscar programas con filtros"""
        if filtros is None:
            filtros = {}
        
        resultado = self.programa_controller.buscar_programas(filtros)
        
        if resultado['success']:
            # Actualizar la tabla/listado
            self._mostrar_programas_en_tabla(resultado['data'], resultado['metadata'])
        else:
            print(f"❌ Error en búsqueda: {resultado['message']}")
    
    def _mostrar_programas_en_tabla(self, programas: list, metadata: dict):
        """Mostrar programas en tabla/listado"""
        # Este método debe ser implementado según tu interfaz
        # Por ahora solo imprime un mensaje
        for programa in programas:
            print(f"📚 {programa['codigo']} - {programa['nombre']} ({programa['estado']})")
    
    def actualizar_lista_programas(self):
        """Actualizar la lista de programas después de cambios"""
        # Actualizar todas las pestañas que puedan tener listas de programas
        for index, tab in self.tabs_dict.items():
            if isinstance(tab, InicioTab):
                # Actualizar la pestaña de inicio si está mostrando programas
                if hasattr(tab, '_on_refresh'):
                    tab._on_refresh()
                break
    
    def mostrar_overlay_programa(self, programa_id: Optional[int] = None, modo: str = "nuevo") -> None:
        """Muestra el overlay de programa"""
        # Inicializar overlay si no existe
        self._init_overlay_programa()
        
        if not self.overlay_programa:
            self.mostrar_mensaje("Error al inicializar el overlay", "error")
            return
        
        # Limpiar formulario
        try:
            self.overlay_programa.clear_form()
        except AttributeError:
            print("❌ Error: Método clear_form no disponible")
            self.mostrar_mensaje("Error al limpiar formulario", "error")
            return
        
        # Configurar según el modo
        if programa_id is not None and modo == "editar":
            # Usar el método mejorado para obtener datos reales de la BD
            self.mostrar_editar_programa(programa_id)
        else:
            # Modo nuevo
            try:
                self.overlay_programa.modo = "nuevo"
                self.overlay_programa.programa_id = None
                self.overlay_programa.set_titulo("🏛️ Nuevo Programa Académico - UNSXX")
                self.overlay_programa.show_form()
                
                # Mostrar con oscurecimiento
                self.show_overlay(self.overlay_programa)
                
            except Exception as e:
                print(f"❌ Error al mostrar overlay: {e}")
                self.mostrar_mensaje(f"Error al mostrar formulario: {str(e)}", "error")
    
    # ===== MÉTODOS DE ESTUDIANTE =====
    
    def mostrar_nuevo_estudiante(self):
        """Mostrar overlay para crear nuevo estudiante"""
        self._init_overlay_estudiante()
        
        if not self.overlay_estudiante:
            self.mostrar_mensaje("Error al inicializar el overlay de estudiante", "error")
            return
            
        try:
            self.overlay_estudiante.set_modo("nuevo")
            self.overlay_estudiante.show_form()
            
            # Mostrar con oscurecimiento
            self.show_overlay(self.overlay_estudiante)
            
        except Exception as e:
            print(f"❌ Error al mostrar overlay de estudiante: {e}")
            self.mostrar_mensaje(f"Error al mostrar formulario: {str(e)}", "error")

    def mostrar_editar_estudiante(self, estudiante_id: int):
        """Mostrar overlay para editar estudiante existente"""
        self._init_overlay_estudiante()
        
        if not self.overlay_estudiante:
            self.mostrar_mensaje("Error al inicializar el overlay de estudiante", "error")
            return
            
        try:
            self.overlay_estudiante.set_modo("editar", estudiante_id)
            self.overlay_estudiante.show_form()
            
            # Mostrar con oscurecimiento
            self.show_overlay(self.overlay_estudiante)
            
        except Exception as e:
            print(f"❌ Error al mostrar overlay de estudiante: {e}")
            self.mostrar_mensaje(f"Error al mostrar formulario: {str(e)}", "error")

    def mostrar_ver_estudiante(self, estudiante_id: int):
        """Mostrar overlay para ver detalles de estudiante"""
        self._init_overlay_estudiante()
        
        if not self.overlay_estudiante:
            self.mostrar_mensaje("Error al inicializar el overlay de estudiante", "error")
            return
            
        try:
            self.overlay_estudiante.set_modo("visualizar", estudiante_id)
            self.overlay_estudiante.show_form()
            
            # Mostrar con oscurecimiento
            self.show_overlay(self.overlay_estudiante)
            
        except Exception as e:
            print(f"❌ Error al mostrar overlay de estudiante: {e}")
            self.mostrar_mensaje(f"Error al mostrar formulario: {str(e)}", "error")
    
    def _on_estudiante_guardado(self, estudiante_data: dict):
        """Manejador cuando se guarda un estudiante nuevo"""
        if not self.overlay_estudiante:
            return
        
        # Obtener datos del estudiante
        estudiante_id = estudiante_data.get('id') or estudiante_data.get('estudiante_id')
        nombres = estudiante_data.get('nombres', 'N/A')
        apellido_paterno = estudiante_data.get('apellido_paterno', '')
        
        print(f"✅ Estudiante creado: {nombres} {apellido_paterno} (ID: {estudiante_id})")
        
        # Actualizar la pestaña de inicio
        self.actualizar_lista_estudiantes()
        
        # Mostrar mensaje de éxito
        self.mostrar_mensaje(
            f"Estudiante {nombres} {apellido_paterno} creado exitosamente (ID: {estudiante_id})",
            tipo="exito"
        )
        
        # Opcional: Abrir en modo visualización después de 500ms
        if estudiante_id:
            QTimer.singleShot(500, lambda: self.mostrar_ver_estudiante(estudiante_id))

    def _on_estudiante_actualizado(self, estudiante_data: dict):
        """Manejador cuando se actualiza un estudiante"""
        if not self.overlay_estudiante:
            return
            
        print(f"✅ Estudiante actualizado: {estudiante_data.get('nombres', 'N/A')}")
        
        self.actualizar_lista_estudiantes()
        
        self.mostrar_mensaje(
            f"Estudiante {estudiante_data.get('nombres', 'N/A')} actualizado exitosamente",
            tipo="exito"
        )

    def _on_estudiante_eliminado(self, estudiante_id: int):
        """Manejador cuando se elimina un estudiante"""
        if not self.overlay_estudiante:
            return
            
        print(f"✅ Estudiante eliminado: ID {estudiante_id}")
        
        self.actualizar_lista_estudiantes()
        
        self.mostrar_mensaje(
            f"Estudiante ID {estudiante_id} eliminado exitosamente",
            tipo="exito"
        )

    def actualizar_lista_estudiantes(self):
        """Actualizar la lista de estudiantes después de cambios"""
        print("🔄 Actualizando lista de estudiantes...")
        # Actualizar todas las pestañas que puedan tener listas de estudiantes
        for index, tab in self.tabs_dict.items():
            if isinstance(tab, InicioTab):
                # Actualizar la pestaña de inicio
                if hasattr(tab, '_on_refresh'):
                    tab._on_refresh()
                break
    
    # ===== MÉTODOS DE DOCENTE =====
    
    def mostrar_nuevo_docente(self):
        """Mostrar overlay para crear nuevo docente"""
        self._init_overlay_docente()
        
        if not self.overlay_docente:
            self.mostrar_mensaje("Error al inicializar el overlay de docente", "error")
            return
            
        try:
            self.overlay_docente.show_form(modo="nuevo")
            
            # Mostrar con oscurecimiento
            self.show_overlay(self.overlay_docente)
            
        except Exception as e:
            print(f"❌ Error mostrando nuevo docente: {e}")
            self.mostrar_mensaje(f"Error al crear nuevo docente: {str(e)}", "error")
    
    def mostrar_editar_docente(self, docente_id: int):
        """Mostrar overlay para editar docente existente"""
        self._init_overlay_docente()
        
        if not self.overlay_docente:
            self.mostrar_mensaje("Error al inicializar el overlay de docente", "error")
            return
            
        try:
            self.overlay_docente.show_form(modo="editar", docente_id=docente_id)
            
            # Mostrar con oscurecimiento
            self.show_overlay(self.overlay_docente)
            
        except Exception as e:
            print(f"❌ Error editando docente: {e}")
            self.mostrar_mensaje(f"Error al editar docente: {str(e)}", "error")
    
    def mostrar_detalles_docente(self, docente_id: int):
        """Mostrar overlay para ver detalles de docente"""
        self._init_overlay_docente()
        
        if not self.overlay_docente:
            self.mostrar_mensaje("Error al inicializar el overlay de docente", "error")
            return
            
        try:
            self.overlay_docente.show_form(
                solo_lectura=True,
                modo="lectura",
                docente_id=docente_id
            )
            
            # Mostrar con oscurecimiento
            self.show_overlay(self.overlay_docente)
            
        except Exception as e:
            print(f"❌ Error viendo docente: {e}")
            self.mostrar_mensaje(f"Error al ver docente: {str(e)}", "error")
    
    def _on_docente_guardado(self, docente_data: dict):
        """Manejador cuando se guarda un docente"""
        if not self.overlay_docente:
            return
            
        print(f"✅ Docente guardado: {docente_data.get('nombres', 'N/A')} {docente_data.get('apellido_paterno', 'N/A')}")
        
        # Actualizar lista de docentes
        self.actualizar_lista_docentes()
        
        # Mostrar mensaje
        self.mostrar_mensaje(
            f"Docente {docente_data.get('nombres', 'N/A')} guardado exitosamente",
            tipo="exito"
        )
    
    def _on_docente_actualizado(self, docente_data: dict):
        """Manejador cuando se actualiza un docente"""
        if not docente_data:
            return

        print(f"✅ Docente actualizado: {docente_data.get('nombres', 'N/A')}")

        self.actualizar_lista_docentes()

        self.mostrar_mensaje(
            f"Docente {docente_data.get('nombres', 'N/A')} actualizado exitosamente",
            tipo="exito"
        )

    def _on_docente_eliminado(self, docente_id: int):
        """Manejador cuando se elimina un docente"""
        print(f"✅ Docente eliminado: ID {docente_id}")

        self.actualizar_lista_docentes()

        self.mostrar_mensaje(
            f"Docente ID {docente_id} eliminado exitosamente",
            tipo="exito"
        )
    
    def actualizar_lista_docentes(self):
        """Actualizar la lista de docentes después de cambios"""
        print("🔄 Actualizando lista de docentes...")
        # Actualizar todas las pestañas que puedan tener listas de docentes
        for index, tab in self.tabs_dict.items():
            if isinstance(tab, InicioTab):
                # Actualizar la pestaña de inicio
                if hasattr(tab, '_on_refresh'):
                    tab._on_refresh()
                break
    
    # --- Métodos de manejo de estilos ---
    
    def load_styles(self) -> None:
        """Cargar y combinar estilos desde archivos QSS"""
        try:
            base_styles = self._load_qss_file(self.base_qss_file)
            color_styles = self._load_qss_file(self.color_qss_file)
            combined_styles = base_styles + "\n" + color_styles
            
            self.setStyleSheet(combined_styles)
            
            # Aplicar estilos también a los overlays si existen
            overlays = [self.overlay_programa, self.overlay_estudiante, self.overlay_docente]
            for overlay in overlays:
                if overlay:
                    overlay.setStyleSheet(combined_styles)
            
            print(f"✅ Estilos cargados correctamente")
            print(f"   Base: {self.base_qss_file}")
            print(f"   Tema: {self.color_qss_file}")
            
        except Exception as e:
            print(f"❌ Error cargando estilos: {e}")
            self._apply_default_styles()
    
    def _load_qss_file(self, file_path: str) -> str:
        """Cargar contenido de un archivo QSS"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            else:
                print(f"⚠️ Archivo no encontrado: {file_path}")
                return ""
        except Exception as e:
            print(f"❌ Error leyendo {file_path}: {e}")
            return ""
    
    def set_color_theme(self, theme_name: str) -> bool:
        """Cambiar el tema de colores dinámicamente"""
        theme_file = f"view/styles/{theme_name}.qss"
        
        if os.path.exists(theme_file):
            self.color_qss_file = theme_file
            self.load_styles()
            return True
        else:
            print(f"❌ Archivo de tema no encontrado: {theme_file}")
            return False
    
    def reload_styles(self) -> None:
        """Recargar estilos desde archivos QSS"""
        self.load_styles()
    
    def setup_style_watcher(self) -> None:
        """Configurar recarga automática durante desarrollo"""
        self.reload_timer = QTimer()
        self.reload_timer.timeout.connect(self._check_styles_update)
        self.reload_timer.start(2000)
        
        self.base_qss_mtime = self._get_file_mtime(self.base_qss_file)
        self.color_qss_mtime = self._get_file_mtime(self.color_qss_file)
    
    def _get_file_mtime(self, file_path: str) -> float:
        """Obtener tiempo de modificación de un archivo"""
        if os.path.exists(file_path):
            return os.path.getmtime(file_path)
        return 0.0
    
    def _check_styles_update(self) -> None:
        """Verificar si los archivos QSS han cambiado"""
        base_changed = self._check_file_changed(self.base_qss_file, self.base_qss_mtime)
        color_changed = self._check_file_changed(self.color_qss_file, self.color_qss_mtime)
        
        if base_changed or color_changed:
            print("🔄 Recargando estilos...")
            self.load_styles()
    
    def _check_file_changed(self, file_path: str, last_mtime: float) -> bool:
        """Verificar si un archivo específico ha cambiado"""
        current_mtime = self._get_file_mtime(file_path)
        if current_mtime > last_mtime:
            if file_path == self.base_qss_file:
                self.base_qss_mtime = current_mtime
            else:
                self.color_qss_mtime = current_mtime
            return True
        return False
    
    def _apply_default_styles(self) -> None:
        """Aplicar estilos por defecto si hay error"""
        default_styles = """
        QMainWindow { background-color: #f0f0f0; }
        QTabWidget::pane { border: 1px solid #cccccc; background-color: white; }
        QTabBar::tab { padding: 8px 16px; background-color: #e8e8e8; }
        QTabBar::tab:selected { background-color: white; }
        """
        self.setStyleSheet(default_styles)
    
    def closeEvent(self, event):
        """Manejador para el cierre de la ventana - REEMPLAZAR"""
        if hasattr(self, 'reload_timer'):
            self.reload_timer.stop()

        # Cerrar todos los overlays activos
        self.close_all_overlays()

        print("Cerrando aplicación...")
        event.accept()
    
    def debug_overlay_state(self):
        """Mostrar estado actual para debug"""
        print("\n" + "="*50)
        print("DEBUG - ESTADO DE OVERLAYS:")
        print(f"Oscurecedor visible: {self.overlay_darkener.isVisible()}")
        print(f"Active overlays ({len(self.active_overlays)}):")
        for i, overlay in enumerate(self.active_overlays):
            print(f"  {i+1}. {overlay.__class__.__name__} - Visible: {overlay.isVisible()}")
        print("="*50 + "\n")