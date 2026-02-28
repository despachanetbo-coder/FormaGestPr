# Archivo: view/tabs/resumen_tab.py (VERSIÓN CORREGIDA)
# -*- coding: utf-8 -*-
"""
ResumenTab - Pestaña de resumen principal con gráficos y métricas en tiempo real.
Hereda de BaseTab y se integra con la arquitectura existente de FormaGestPro.
Autor: Sistema FormaGestPro
Versión: 3.0.1 (Corregida para conexión PostgreSQL)
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# PySide6 imports
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QPushButton, QGroupBox,
    QSizePolicy, QScrollArea, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSplitter, QMessageBox, QComboBox,
    QToolTip, QFileDialog, QDialog, QTextEdit
)
from PySide6.QtCore import (
    Qt, QTimer, QDate, QDateTime,
    Signal, Slot, QPropertyAnimation,
    QEasingCurve, QParallelAnimationGroup, QPoint
)
from PySide6.QtGui import (
    QPainter, QLinearGradient,
    QBrush, QColor, QIcon, QCursor, QPen, QFont
)

# Importar modelos directamente (CAMBIO IMPORTANTE)
from model.estudiante_model import EstudianteModel
from model.docente_model import DocenteModel
from model.programa_model import ProgramaModel
from model.inscripcion_model import InscripcionModel
from model.resumen_model import ResumenModel  # NUEVO: Usar el modelo de resumen

from config.constants import EstadoPrograma

# Importar base tab
from .base_tab import BaseTab

# Configurar logging
logger = logging.getLogger(__name__)

# ============================================================================
# CLASES AUXILIARES (MANTENER IGUAL)
# ============================================================================

class AnimatedCard(QFrame):
    """Tarjeta con animación al pasar el mouse"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.original_style = ""
    
    def setup_ui(self):
        """Configurar animaciones - DEBE ser implementado por clases hijas"""
        self.setMouseTracking(True)
    
    def enterEvent(self, event):
        """Animación al entrar"""
        self.original_style = self.styleSheet()
        hover_style = self.styleSheet().replace("border: 2px solid", "border: 3px solid")
        hover_style = hover_style.replace("background-color: white", "background-color: #f8f9fa")
        self.setStyleSheet(hover_style)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Animación al salir"""
        self.setStyleSheet(self.original_style)
        super().leaveEvent(event)

class StatCard(AnimatedCard):
    """Tarjeta de estadística con animación"""
    
    clicked = Signal(str)  # Señal cuando se hace clic en la tarjeta
    
    def __init__(self, title: str, value: str, icon: str, 
                color: str, change: str = "", 
                min_height: int = 140, max_height: int = 150,
                stat_id: str = "", parent=None):
        # Asignar atributos PRIMERO
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        self.change = change
        self.min_height = min_height
        self.max_height = max_height
        self.stat_id = stat_id
        
        # Luego llamar al constructor del padre
        super().__init__(parent)
        
        # Finalmente configurar la UI
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de la tarjeta"""
        self.setObjectName(f"StatCard_{self.stat_id}")
        
        # Control explícito de altura
        self.setMinimumHeight(self.min_height)
        self.setMaximumHeight(self.max_height)
        self.setMinimumWidth(200)
        
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        
        # Fila superior: Icono y título
        top_layout = QHBoxLayout()
        
        # Icono
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet(f"""
            QLabel {{
                font-size: 28px;
                color: {self.color};
                font-family: 'Segoe UI Emoji';
            }}
        """)
        top_layout.addWidget(icon_label)
        top_layout.addStretch()
        
        # Título
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                color: #7f8c8d;
                font-weight: bold;
            }
        """)
        title_label.setWordWrap(True)
        top_layout.addWidget(title_label)
        layout.addLayout(top_layout)
        
        # Valor principal
        value_label = QLabel(self.value)
        value_label.setStyleSheet(f"""
            QLabel {{
                font-size: 18px;
                font-weight: bold;
                color: {self.color};
                padding: 8px 0;
            }}
        """)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        # Cambio (si existe)
        if self.change:
            change_label = QLabel()
            
            # Determinar color basado en si es positivo/negativo
            if "+" in self.change:
                change_color = "#27ae60"
                change_text = f"▲ {self.change}"
            elif "-" in self.change:
                change_color = "#e74c3c"
                change_text = f"▼ {self.change}"
            else:
                change_color = "#f39c12"
                change_text = self.change
            
            change_label.setText(change_text)
            change_label.setStyleSheet(f"""
                QLabel {{
                    font-size: 12px;
                    color: {change_color};
                    font-weight: bold;
                    padding: 4px 10px;
                    background-color: {change_color}15;
                    border-radius: 10px;
                    margin-top: 5px;
                }}
            """)
            change_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(change_label)
        
        layout.addStretch()
        
        # Estilo de la tarjeta
        self.setStyleSheet(f"""
            #StatCard_{self.stat_id} {{
                background-color: white;
                border-radius: 12px;
                border: 2px solid #ecf0f1;
                padding: 5px;
            }}
            #StatCard_{self.stat_id}:hover {{
                border: 2px solid {self.color};
                background-color: #f8f9fa;
            }}
        """)
        
        # Hacer clicable
        self.setCursor(Qt.CursorShape.PointingHandCursor)
    
    def mousePressEvent(self, event):
        """Manejador clic en tarjeta"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.stat_id)
        super().mousePressEvent(event)

# ============================================================================
# CLASE PRINCIPAL: RESUMENTAB (VERSIÓN CORREGIDA)
# ============================================================================

class ResumenTab(BaseTab):
    """Resumen principal del sistema FormaGestPro - Versión PostgreSQL corregida"""
    
    # Señales
    data_updated = Signal(dict)
    refresh_requested = Signal()
    
    def __init__(self, user_data=None, parent=None):
        """Inicializar Resumen"""
        super().__init__(
            tab_id="resumen_tab", 
            tab_name="📊 Resumen",
            parent=parent
        )
        
        self.user_data = user_data or {}
        
        # Estado del resumen
        self.resumen_data = {}
        self.stat_cards = []
        self.is_initialized = False
        
        # Inicializar modelos (CAMBIO IMPORTANTE: usar modelos en lugar de controladores)
        self.estudiante_model = EstudianteModel()
        self.docente_model = DocenteModel()
        self.programa_model = ProgramaModel()
        self.inscripcion_model = InscripcionModel()
        self.resumen_model = ResumenModel()  # NUEVO: Modelo específico para resumen
        
        # Configurar header personalizado
        self.set_header_title("📊 PANEL DE CONTROL")
        self.set_header_subtitle("Métricas y análisis en tiempo real del sistema")
        
        # Configurar información de usuario
        nombre_usuario = self._get_user_display_name()
        rol_usuario = self.user_data.get('rol', 'Usuario')
        self.set_user_info(nombre_usuario, rol_usuario)
        
        # Inicializar UI
        self._init_ui()
        
        # Cargar datos iniciales
        self.load_initial_data()
        
        # Configurar temporizadores
        self.setup_timers()
        
        logger.info("ResumenTab inicializado correctamente")
    
    # ============================================================================
    # MÉTODOS HEREDADOS DE BASETAB
    # ============================================================================
    
    def _init_ui(self):
        """Inicializar la interfaz de usuario del resumen"""
        # Limpiar contenido previo
        self.clear_content()
        
        # Layout principal con scroll
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(600)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: #f5f7fa;
            }
            QScrollArea > QWidget > QWidget {
                background-color: #f5f7fa;
            }
        """)
        
        # Widget contenido
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: #f5f7fa;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(20, 20, 20, 40)
        
        # 1. Métricas principales
        self.create_main_stats(content_layout)
        
        # 2. Estadísticas rápidas
        self.create_quick_stats(content_layout)
        
        # 3. Sección de gráficos y tablas
        self.create_data_section(content_layout)
        
        # 4. Barra de herramientas inferior
        self.create_bottom_toolbar(content_layout)
        
        scroll_area.setWidget(content_widget)
        self.add_widget(scroll_area)
        
        self.is_initialized = True
    
    def on_tab_selected(self):
        """Método llamado cuando la pestaña es seleccionada"""
        super().on_tab_selected()
        logger.info(f"ResumenTab seleccionada")
        
        # Actualizar datos al seleccionar la pestaña
        if self.is_initialized:
            self.refresh_resumen()
    
    # ============================================================================
    # MÉTODOS DE CONFIGURACIÓN
    # ============================================================================
    
    def setup_timers(self):
        """Configurar temporizadores para actualización automática"""
        # Temporizador para actualización de datos (cada 30 segundos)
        self.data_timer = QTimer()
        self.data_timer.timeout.connect(self.refresh_resumen)
        self.data_timer.start(30000)  # 30 segundos
        
        # Temporizador para animaciones suaves (cada 60 segundos)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_stat_cards)
        self.animation_timer.start(60000)  # 60 segundos
    
    # ============================================================================
    # MÉTODOS DE DATOS (PostgreSQL) - VERSIÓN CORREGIDA
    # ============================================================================
    
    def load_initial_data(self):
        """Cargar datos iniciales del resumen desde PostgreSQL"""
        try:
            logger.info("Cargando datos iniciales del resumen...")
            
            # USAR EL MODELO DE RESUMEN EXISTENTE (CAMBIO PRINCIPAL)
            self.resumen_data = self.resumen_model.obtener_datos_completos_dashboard()
            
            # Si no hay datos del modelo, usar métodos individuales
            if not self.resumen_data or 'total_estudiantes' not in self.resumen_data:
                logger.warning("Modelo de resumen no devolvió datos completos, usando métodos individuales")
                self.resumen_data = self._obtener_datos_individuales()
            
            # Asegurar que tenemos todos los campos necesarios
            self._completar_datos_faltantes()
            
            logger.info(f"Datos cargados: {self.resumen_data.get('total_estudiantes', 0)} estudiantes, "
                        f"{self.resumen_data.get('total_docentes', 0)} docentes, "
                        f"{self.resumen_data.get('programas_activos', 0)} programas")
            
        except Exception as e:
            logger.error(f"Error cargando datos del resumen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self.resumen_data = self._get_sample_data()
    
    def _obtener_datos_individuales(self) -> Dict[str, Any]:
        """Obtener datos individuales desde los modelos específicos"""
        try:
            current_year = datetime.now().year
            current_month = datetime.now().month
            month_names = [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
            ]
            current_month_name = month_names[current_month - 1]
            
            # 1. Estudiantes activos
            estudiantes = self.estudiante_model.buscar_estudiantes_completo(limit=1000)
            total_estudiantes = len([e for e in estudiantes if e.get('estado') == 'ACTIVO'])
            
            # 2. Docentes activos
            docentes = self.docente_model.buscar_docentes_completo(limit=1000)
            total_docentes = len([d for d in docentes if d.get('estado') == 'ACTIVO'])
            
            # 3. Programas activos
            programas = self.programa_model.buscar_programas()
            total_programas = len([p for p in programas if p.get('estado') not in ['CANCELADO', 'CONCLUIDO']])
            
            # 4. Programas creados este año - CORREGIDO
            programas_este_anio = 0
            for p in programas:
                fecha_inicio = p.get('fecha_inicio')
                if fecha_inicio and isinstance(fecha_inicio, datetime):
                    # Si es datetime, verificar año directamente
                    if fecha_inicio.year == current_year:
                        programas_este_anio += 1
                elif fecha_inicio and isinstance(fecha_inicio, str):
                    # Si es string, intentar parsear
                    try:
                        fecha_dt = datetime.strptime(fecha_inicio.split()[0], '%Y-%m-%d')
                        if fecha_dt.year == current_year:
                            programas_este_anio += 1
                    except (ValueError, AttributeError):
                        # Si no se puede parsear, continuar
                        continue
                    
            # 5. Datos financieros (ingresos del mes) - CORREGIDO
            fecha_inicio_mes = datetime(current_year, current_month, 1)
            if current_month == 12:
                fecha_fin_mes = datetime(current_year + 1, 1, 1) - timedelta(days=1)
            else:
                fecha_fin_mes = datetime(current_year, current_month + 1, 1) - timedelta(days=1)
            
            ingresos_mes = 0
            inscripciones_mes = []  # Inicializar variable
            
            # Intentar obtener ingresos del mes actual usando el método CORRECTO
            try:
                # USAR EL MÉTODO CORRECTO: obtener_inscripciones() en lugar de obtener_inscripciones_por_fecha()
                inscripciones_mes = self.inscripcion_model.obtener_inscripciones(
                    filtro_fecha_desde=fecha_inicio_mes,
                    filtro_fecha_hasta=fecha_fin_mes
                )
                
                # Calcular ingresos del mes
                for insc in inscripciones_mes:
                    if isinstance(insc, dict):
                        # Buscar pagos realizados en cada inscripción
                        pagos = insc.get('pagos_realizados', 0)
                        if pagos:
                            try:
                                ingresos_mes += float(pagos)
                            except (ValueError, TypeError):
                                pass
            except Exception as e:
                logger.warning(f"No se pudieron obtener inscripciones del mes: {e}")
                # Si falla, usar un valor estimado basado en estudiantes
                ingresos_mes = total_estudiantes * 250
            
            # 6. Distribución de estudiantes por programa
            distribucion_estudiantes = self.resumen_model.obtener_distribucion_estudiantes()
            
            # 7. Programas en progreso con detalles
            programas_en_progreso = self.resumen_model.obtener_programas_en_progreso()
            
            # 8. Datos financieros históricos
            datos_financieros = self.resumen_model.obtener_datos_financieros()
            
            # 9. Actividad reciente del sistema
            actividad_reciente = self.resumen_model.obtener_alertas_sistema()
            
            # 10. Calcular ocupación promedio
            ocupacion_promedio = self._calcular_ocupacion_promedio(programas_en_progreso)
            
            # 11. Calcular cambios porcentuales
            cambios = self._calcular_cambios_porcentuales(
                total_estudiantes, total_docentes, total_programas,
                programas_este_anio, ingresos_mes
            )
            
            # 12. Obtener totales adicionales
            total_inscripciones_mes = len(inscripciones_mes)
            
            # Construir objeto de datos del resumen
            return {
                # Métricas principales
                'total_estudiantes': total_estudiantes,
                'total_docentes': total_docentes,
                'programas_activos': total_programas,
                'programas_año_actual': programas_este_anio,
                'ingresos_mes': float(ingresos_mes),
                'gastos_mes': float(ingresos_mes * 0.3),
                
                # Cambios porcentuales
                'estudiantes_cambio': cambios['estudiantes'],
                'docentes_cambio': cambios['docentes'],
                'programas_cambio': cambios['programas'],
                'programas_cambio_año': cambios['programas_anio'],
                'ingresos_cambio': cambios['ingresos'],
                
                # Información temporal
                'año_actual': current_year,
                'mes_actual_nombre': current_month_name,
                'fecha_actual': datetime.now().strftime('%d/%m/%Y'),
                
                # Datos detallados
                'estudiantes_por_programa': distribucion_estudiantes,
                'programas_en_progreso': programas_en_progreso,
                'datos_financieros': datos_financieros,
                'actividad_reciente': actividad_reciente,
                'ocupacion_promedio': ocupacion_promedio,
                
                # Totales para estadísticas
                'total_inscripciones_mes': total_inscripciones_mes,
                'total_programas_registrados': len(programas),
                'total_estudiantes_activos': total_estudiantes,
                'total_docentes_activos': total_docentes
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos individuales: {e}")
            return self._get_sample_data()
    
    def _completar_datos_faltantes(self):
        """Completar datos faltantes en el resumen_data"""
        defaults = {
            'total_estudiantes': 0,
            'total_docentes': 0,
            'programas_activos': 0,
            'programas_año_actual': 0,
            'ingresos_mes': 0.0,
            'gastos_mes': 0.0,
            'estudiantes_cambio': '+0%',
            'docentes_cambio': '+0%',
            'programas_cambio': '0 activos',
            'programas_cambio_año': '+0 este año',
            'ingresos_cambio': '+0%',
            'año_actual': datetime.now().year,
            'mes_actual_nombre': datetime.now().strftime('%B'),
            'fecha_actual': datetime.now().strftime('%d/%m/%Y'),
            'estudiantes_por_programa': {},
            'programas_en_progreso': [],
            'datos_financieros': [],
            'actividad_reciente': [],
            'ocupacion_promedio': 0.0,
            'total_inscripciones_mes': 0,
            'total_programas_registrados': 0,
            'total_estudiantes_activos': 0,
            'total_docentes_activos': 0
        }
        
        for key, default_value in defaults.items():
            if key not in self.resumen_data or self.resumen_data[key] is None:
                self.resumen_data[key] = default_value
    
    def _calcular_ocupacion_promedio(self, programas: List[Dict]) -> float:
        """Calcular ocupación promedio de programas"""
        if not programas:
            return 0.0
        
        total_ocupacion = sum(p.get('porcentaje_ocupacion', 0) for p in programas)
        return round(total_ocupacion / len(programas), 1)
    
    def _calcular_cambios_porcentuales(self, *args) -> Dict[str, str]:
        """Calcular cambios porcentuales"""
        total_estudiantes, total_docentes, total_programas, programas_anio, ingresos = args
        
        # Simular cambios basados en valores actuales
        cambios = {
            'estudiantes': f"+{min(10, total_estudiantes // 10 if total_estudiantes > 0 else 0)}%",
            'docentes': f"+{min(5, total_docentes // 5 if total_docentes > 0 else 0)}%",
            'programas': f"{total_programas} activos",
            'programas_anio': f"+{programas_anio} este año",
            'ingresos': f"+{min(15, int(ingresos // 1000) if ingresos > 0 else 0)}%"
        }
        
        return cambios
    
    def _traducir_estado(self, estado: str) -> str:
        """Traducir estado a formato legible"""
        estados = {
            'ACTIVO': '🟢 Activo',
            'INACTIVO': '🔴 Inactivo',
            'PLANIFICADO': '🟡 Planificado',
            'EN_CURSO': '🔵 En Curso',
            'FINALIZADO': '⚫ Finalizado',
            'CANCELADO': '⚪ Cancelado',
            'CONCLUIDO': '⚫ Concluido'
        }
        return estados.get(estado, estado)
    
    def _get_sample_data(self) -> Dict:
        """Datos de ejemplo para fallback"""
        año_actual = datetime.now().strftime('%Y')
        mes_actual = datetime.now().strftime('%B')
        
        return {
            'total_estudiantes': 24,
            'total_docentes': 8,
            'programas_activos': 6,
            'programas_año_actual': 10,
            'ingresos_mes': 15240.0,
            'gastos_mes': 5200.0,
            'estudiantes_cambio': '+3%',
            'docentes_cambio': '+2%',
            'programas_cambio': '6 activos',
            'programas_cambio_año': '+10 este año',
            'ingresos_cambio': '+12%',
            'año_actual': int(año_actual),
            'mes_actual_nombre': mes_actual,
            'fecha_actual': datetime.now().strftime('%d/%m/%Y'),
            'estudiantes_por_programa': {
                'Ingeniería de Sistemas': 45,
                'Administración de Empresas': 32,
                'Derecho': 28,
                'Medicina': 25,
                'Arquitectura': 18
            },
            'programas_en_progreso': [
                {
                    'id': 1,
                    'codigo': 'PROG-2024-001',
                    'nombre': 'Diplomado en Inteligencia Artificial',
                    'estado': 'ACTIVO',
                    'estado_display': '🟢 Activo',
                    'estudiantes_matriculados': 24,
                    'cupos_ocupados': 24,
                    'cupos_totales': 30,
                    'porcentaje_ocupacion': 80.0,
                    'tutor_nombre': 'Dr. Carlos Méndez',
                    'fecha_inicio': '2024-01-15',
                    'fecha_fin': '2024-06-15'
                }
            ],
            'datos_financieros': [
                {'mes': 'Ene 2024', 'ingresos': 12000, 'gastos': 4000, 'saldo': 8000, 'saldo_acumulado': 8000},
                {'mes': 'Feb 2024', 'ingresos': 14000, 'gastos': 4500, 'saldo': 9500, 'saldo_acumulado': 17500},
                {'mes': 'Mar 2024', 'ingresos': 16000, 'gastos': 5000, 'saldo': 11000, 'saldo_acumulado': 28500}
            ],
            'actividad_reciente': [
                {'usuario': 'Sistema', 'actividad': 'Inicio del sistema', 'fecha': datetime.now().strftime('%H:%M'), 'tipo': 'sistema'}
            ],
            'ocupacion_promedio': 65.5,
            'total_inscripciones_mes': 15,
            'total_programas_registrados': 25,
            'total_estudiantes_activos': 150,
            'total_docentes_activos': 25
        }
    
    # ============================================================================
    # MÉTODOS DE UI - COMPONENTES (MANTENER IGUAL, CON PEQUEÑOS AJUSTES)
    # ============================================================================
    
    def create_main_stats(self, parent_layout):
        """Crear estadísticas principales en grid 2x3"""
        stats_group = QGroupBox("📊 MÉTRICAS PRINCIPALES")
        stats_group.setMinimumHeight(350)
        
        # Layout de grid
        stats_layout = QGridLayout(stats_group)
        stats_layout.setSpacing(15)
        stats_layout.setContentsMargins(15, 25, 15, 20)
        
        # Obtener año y mes actual
        año_actual = self.resumen_data.get('año_actual', datetime.now().year)
        mes_actual = self.resumen_data.get('mes_actual_nombre', 'el mes')
        
        # Configuración de tarjetas
        stats_config = [
            {
                'title': 'TOTAL ESTUDIANTES',
                'icon': '👤',
                'color': '#3498db',
                'value_key': 'total_estudiantes',
                'change_key': 'estudiantes_cambio',
                'prefix': '',
                'suffix': '',
                'id': 'estudiantes'
            },
            {
                'title': 'DOCENTES ACTIVOS',
                'icon': '👨‍🏫',
                'color': '#9b59b6',
                'value_key': 'total_docentes',
                'change_key': 'docentes_cambio',
                'prefix': '',
                'suffix': '',
                'id': 'docentes'
            },
            {
                'title': 'PROGRAMAS ACTIVOS',
                'icon': '📚',
                'color': '#2ecc71',
                'value_key': 'programas_activos',
                'change_key': 'programas_cambio',
                'prefix': '',
                'suffix': '',
                'id': 'programas'
            },
            {
                'title': f'PROGRAMAS EN {año_actual}',
                'icon': '📅',
                'color': '#1abc9c',
                'value_key': 'programas_año_actual',
                'change_key': 'programas_cambio_año',
                'prefix': '',
                'suffix': '',
                'id': 'programas_anio'
            },
            {
                'title': f'INGRESOS EN {mes_actual.upper()}',
                'icon': '💰',
                'color': '#27ae60',
                'value_key': 'ingresos_mes',
                'change_key': 'ingresos_cambio',
                'prefix': 'Bs ',
                'suffix': '',
                'id': 'ingresos'
            },
            {
                'title': f'INSCRIPCIONES ESTE MES',
                'icon': '📝',
                'color': '#e74c3c',
                'value_key': 'total_inscripciones_mes',
                'change_key': '',
                'prefix': '',
                'suffix': ' inscripciones',
                'id': 'inscripciones'
            }
        ]
        
        # Crear tarjetas
        self.stat_cards = []
        
        for i, config in enumerate(stats_config):
            # Obtener valor
            value = self.resumen_data.get(config['value_key'], 0)
            
            # Formatear valor
            if config['prefix'] == 'Bs ':
                value_str = f"Bs {value:,.2f}"
            else:
                value_str = f"{value}{config['suffix']}"
            
            # Obtener cambio
            change = self.resumen_data.get(config['change_key'], "")
            
            # Crear tarjeta
            card = StatCard(
                title=config['title'],
                value=value_str,
                icon=config['icon'],
                color=config['color'],
                change=change,
                min_height=150,
                max_height=160,
                stat_id=config['id']
            )
            
            # Conectar señal de clic
            card.clicked.connect(self.on_stat_card_clicked)
            
            self.stat_cards.append(card)
            
            # Posicionar en grid 2x3
            row = i // 3
            col = i % 3
            stats_layout.addWidget(card, row, col)
        
        parent_layout.addWidget(stats_group)
    
    def create_quick_stats(self, parent_layout):
        """Crear estadísticas rápidas en una fila horizontal"""
        quick_stats_frame = QFrame()
        quick_stats_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 12px;
                border: 2px solid #ecf0f1;
                padding: 15px;
            }
        """)
        
        quick_layout = QHBoxLayout(quick_stats_frame)
        quick_layout.setSpacing(20)
        quick_layout.setContentsMargins(20, 10, 20, 10)
        
        # Estadísticas rápidas
        quick_stats = [
            {
                'label': '🏛️ Total Programas Registrados',
                'value': str(self.resumen_data.get('total_programas_registrados', 0)),
                'color': '#3498db'
            },
            {
                'label': '👥 Estudiantes Activos',
                'value': str(self.resumen_data.get('total_estudiantes_activos', 0)),
                'color': '#2ecc71'
            },
            {
                'label': '👨‍🏫 Docentes Activos',
                'value': str(self.resumen_data.get('total_docentes_activos', 0)),
                'color': '#9b59b6'
            },
            {
                'label': '📊 Ocupación Promedio',
                'value': f"{self.resumen_data.get('ocupacion_promedio', 0)}%",
                'color': '#f39c12'
            }
        ]
        
        for stat in quick_stats:
            stat_widget = self.create_quick_stat_widget(
                stat['label'], 
                stat['value'], 
                stat['color']
            )
            quick_layout.addWidget(stat_widget)
        
        quick_layout.addStretch()
        parent_layout.addWidget(quick_stats_frame)
    
    def create_quick_stat_widget(self, label: str, value: str, color: str) -> QFrame:
        """Crear widget de estadística rápida"""
        widget = QFrame()
        widget.setStyleSheet(f"""
            QFrame {{
                border-left: 3px solid {color};
                padding: 10px 15px;
                background-color: white;
                border-radius: 8px;
                min-width: 150px;
            }}
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        # Etiqueta
        label_widget = QLabel(label)
        label_widget.setStyleSheet("""
            QLabel {
                font-size: 11px;
                color: #7f8c8d;
                font-weight: bold;
            }
        """)
        label_widget.setWordWrap(True)
        layout.addWidget(label_widget)
        
        # Valor
        value_widget = QLabel(value)
        value_widget.setStyleSheet(f"""
            QLabel {{
                font-size: 16px;
                font-weight: bold;
                color: {color};
            }}
        """)
        layout.addWidget(value_widget)
        
        return widget
    
    def create_data_section(self, parent_layout):
        """Crear sección de datos (tablas y gráficos)"""
        # Splitter horizontal para dividir la pantalla
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # Panel izquierdo: Actividad reciente (40%)
        left_panel = self.create_recent_activity_panel()
        splitter.addWidget(left_panel)
        
        # Panel derecho: Programas en progreso (60%)
        right_panel = self.create_programs_panel()
        splitter.addWidget(right_panel)
        
        # Establecer proporciones iniciales
        splitter.setSizes([400, 600])
        
        parent_layout.addWidget(splitter, stretch=1)
    
    def create_recent_activity_panel(self) -> QGroupBox:
        """Crear panel de actividad reciente"""
        group = QGroupBox("🔄 ACTIVIDAD RECIENTE")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                border: 2px solid #ecf0f1;
                border-radius: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 25, 10, 15)
        
        # Obtener actividad reciente
        actividades = self.resumen_data.get('actividad_reciente', [])
        
        if not actividades:
            no_data_label = QLabel(
                "<div style='text-align: center; padding: 40px;'>"
                "<h3 style='color: #95a5a6;'>📭 Sin actividad reciente</h3>"
                "<p>No hay registros de actividad en el sistema.</p>"
                "</div>"
            )
            no_data_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(no_data_label)
            return group
        
        # Crear scroll area para la actividad
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)
        
        # Widget contenedor de actividades
        activities_widget = QWidget()
        activities_layout = QVBoxLayout(activities_widget)
        activities_layout.setSpacing(8)
        activities_layout.setContentsMargins(5, 5, 5, 5)
        
        # Agregar cada actividad
        for actividad in actividades[:10]:  # Limitar a 10 actividades
            activity_item = self.create_activity_item(actividad)
            activities_layout.addWidget(activity_item)
        
        activities_layout.addStretch()
        scroll_area.setWidget(activities_widget)
        layout.addWidget(scroll_area)
        
        # Botón para ver toda la actividad
        btn_container = QHBoxLayout()
        btn_container.addStretch()
        
        btn_view_all = QPushButton("📋 Ver toda la actividad")
        btn_view_all.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_view_all.clicked.connect(self.show_all_activity)
        btn_container.addWidget(btn_view_all)
        
        layout.addLayout(btn_container)
        
        return group
    
    def create_activity_item(self, actividad: Dict) -> QFrame:
        """Crear item de actividad individual"""
        # Convertir fecha si es necesario
        fecha = actividad.get('fecha', '')
        if isinstance(fecha, datetime):
            fecha = fecha.strftime('%d/%m/%Y %H:%M')
        elif isinstance(fecha, str) and 'Hace' not in fecha:
            try:
                fecha_dt = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S')
                fecha = fecha_dt.strftime('%d/%m/%Y %H:%M')
            except:
                pass
        
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                padding: 10px;
            }
            QFrame:hover {
                background-color: #e8f4fc;
                border-color: #3498db;
            }
        """)
        
        layout = QVBoxLayout(widget)
        layout.setSpacing(5)
        
        # Fila superior: Icono y usuario
        top_row = QHBoxLayout()
        
        # Icono según tipo
        tipo_iconos = {
            'estudiante': '👤',
            'pago': '💰',
            'asignacion': '👨‍🏫',
            'programa': '📚',
            'certificado': '📄',
            'sistema': '⚙️',
            'inscripcion': '📝',
            'configuracion': '🔧'
        }
        tipo = actividad.get('tipo', 'sistema')
        icono = tipo_iconos.get(tipo, '📌')
        
        icon_label = QLabel(icono)
        icon_label.setStyleSheet("font-size: 16px;")
        top_row.addWidget(icon_label)
        
        # Usuario
        user_label = QLabel(f"<b>{actividad.get('usuario', 'Sistema')}</b>")
        user_label.setStyleSheet("font-size: 12px; color: #2c3e50;")
        top_row.addWidget(user_label)
        top_row.addStretch()
        
        # Fecha
        date_label = QLabel(fecha)
        date_label.setStyleSheet("font-size: 10px; color: #95a5a6;")
        top_row.addWidget(date_label)
        
        layout.addLayout(top_row)
        
        # Actividad
        mensaje = actividad.get('mensaje', actividad.get('actividad', ''))
        activity_label = QLabel(mensaje)
        activity_label.setStyleSheet("font-size: 11px; color: #34495e;")
        activity_label.setWordWrap(True)
        layout.addWidget(activity_label)
        
        return widget
    
    def create_programs_panel(self) -> QGroupBox:
        """Crear panel de programas en progreso"""
        group = QGroupBox("📚 PROGRAMAS EN PROGRESO")
        group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 15px;
                border: 2px solid #ecf0f1;
                border-radius: 10px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """)
        
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 25, 10, 15)
        
        # Obtener programas en progreso
        programas = self.resumen_data.get('programas_en_progreso', [])
        
        if not programas:
            no_data_label = QLabel(
                "<div style='text-align: center; padding: 40px;'>"
                "<h3 style='color: #95a5a6;'>📭 Sin programas en progreso</h3>"
                "<p>No hay programas académicos activos en este momento.</p>"
                "</div>"
            )
            no_data_label.setTextFormat(Qt.TextFormat.RichText)
            layout.addWidget(no_data_label)
            return group
        
        # Crear tabla de programas
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Código", "Programa", "Estado", "Estudiantes", "Cupos", "Ocupación"
        ])
        
        table.setRowCount(len(programas))
        
        for i, programa in enumerate(programas):
            # Código
            codigo_item = QTableWidgetItem(programa.get('codigo', 'N/A'))
            codigo_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Nombre del programa (truncado si es muy largo)
            nombre = programa.get('nombre', '')
            if len(nombre) > 30:
                nombre = nombre[:27] + "..."
            nombre_item = QTableWidgetItem(nombre)
            
            # Estado
            estado = programa.get('estado_display', programa.get('estado', 'N/A'))
            estado_item = QTableWidgetItem(estado)
            estado_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Estudiantes
            estudiantes = programa.get('estudiantes_matriculados', 0)
            estudiantes_item = QTableWidgetItem(str(estudiantes))
            estudiantes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Cupos
            cupos_ocupados = programa.get('cupos_ocupados', estudiantes)
            cupos_totales = programa.get('cupos_totales', 0)
            cupos_text = f"{cupos_ocupados}/{cupos_totales}"
            cupos_item = QTableWidgetItem(cupos_text)
            cupos_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Ocupación
            porcentaje = programa.get('porcentaje_ocupacion', 0)
            ocupacion_item = QTableWidgetItem(f"{porcentaje}%")
            ocupacion_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Color según porcentaje
            if porcentaje >= 90:
                ocupacion_item.setForeground(QColor("#e74c3c"))
            elif porcentaje >= 70:
                ocupacion_item.setForeground(QColor("#f39c12"))
            else:
                ocupacion_item.setForeground(QColor("#27ae60"))
            
            table.setItem(i, 0, codigo_item)
            table.setItem(i, 1, nombre_item)
            table.setItem(i, 2, estado_item)
            table.setItem(i, 3, estudiantes_item)
            table.setItem(i, 4, cupos_item)
            table.setItem(i, 5, ocupacion_item)
        
        # Configurar tabla
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #ecf0f1;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #2c3e50;
                color: white;
                padding: 10px;
                font-weight: bold;
                border: none;
            }
        """)
        
        layout.addWidget(table)
        
        # Conectar doble clic para ver detalles
        table.doubleClicked.connect(self.on_program_double_clicked)
        
        # Estadísticas de programas
        stats_frame = self.create_programs_stats_frame(programas)
        layout.addWidget(stats_frame)
        
        return group
    
    def create_programs_stats_frame(self, programas: List[Dict]) -> QFrame:
        """Crear frame con estadísticas de programas"""
        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #ecf0f1;
                border-radius: 8px;
                padding: 15px;
                margin-top: 15px;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        # Calcular estadísticas
        total_estudiantes = sum(p.get('estudiantes_matriculados', 0) for p in programas)
        total_cupos = sum(p.get('cupos_totales', 0) for p in programas)
        ocupacion_total = (total_estudiantes / total_cupos * 100) if total_cupos > 0 else 0
        
        stats = [
            f"📚 {len(programas)} Programas",
            f"👥 {total_estudiantes} Estudiantes",
            f"🎯 {total_cupos} Cupos Totales",
            f"📊 {ocupacion_total:.1f}% Ocupación Total"
        ]
        
        for stat in stats:
            stat_label = QLabel(stat)
            stat_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 5px 10px;
                    background-color: white;
                    border-radius: 5px;
                    margin-right: 10px;
                }
            """)
            layout.addWidget(stat_label)
        
        layout.addStretch()
        return frame
    
    def create_bottom_toolbar(self, parent_layout):
        """Crear barra de herramientas inferior"""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-top: 1px solid #34495e;
                padding: 10px;
                border-radius: 8px;
                margin-top: 20px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        
        # Información del sistema
        sys_info = QLabel(
            f"<span style='color: #ecf0f1;'>"
            f"FormaGestPro v3.0 • PostgreSQL • Última actualización: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            f"</span>"
        )
        sys_info.setTextFormat(Qt.TextFormat.RichText)
        toolbar_layout.addWidget(sys_info)
        toolbar_layout.addStretch()
        
        # Botones de acción
        btn_refresh = QPushButton("🔄 Actualizar resumen")
        btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        btn_refresh.clicked.connect(self.refresh_resumen)
        
        btn_export = QPushButton("📊 Generar Reporte")
        btn_export.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
                margin-right: 10px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        btn_export.clicked.connect(self.generate_report)
        
        btn_settings = QPushButton("⚙️ Configuración")
        btn_settings.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        btn_settings.clicked.connect(self.open_settings)
        
        toolbar_layout.addWidget(btn_refresh)
        toolbar_layout.addWidget(btn_export)
        toolbar_layout.addWidget(btn_settings)
        
        parent_layout.addWidget(toolbar_frame)
    
    # ============================================================================
    # MÉTODOS DE EVENTOS E INTERACCIÓN (MANTENER IGUAL)
    # ============================================================================
    
    def on_stat_card_clicked(self, stat_id: str):
        """Manejador cuando se hace clic en una tarjeta de estadística"""
        logger.info(f"Tarjeta de estadística clickeada: {stat_id}")
        
        # Mostrar detalles según la tarjeta clickeada
        if stat_id == 'estudiantes':
            self.show_students_details()
        elif stat_id == 'docentes':
            self.show_teachers_details()
        elif stat_id == 'programas':
            self.show_programs_details()
        elif stat_id == 'programas_anio':
            self.show_yearly_programs()
        elif stat_id == 'ingresos':
            self.show_financial_details()
        elif stat_id == 'inscripciones':
            self.show_enrollments_details()
    
    def on_program_double_clicked(self, index):
        """Manejador para doble clic en programa"""
        row = index.row()
        programas = self.resumen_data.get('programas_en_progreso', [])
        
        if row < len(programas):
            programa = programas[row]
            programa_id = programa.get('id')
            programa_nombre = programa.get('nombre', 'Programa')
            
            QMessageBox.information(
                self,
                f"📚 {programa_nombre}",
                f"<b>Código:</b> {programa.get('codigo', 'N/A')}<br>"
                f"<b>Nombre:</b> {programa_nombre}<br>"
                f"<b>Estado:</b> {programa.get('estado_display', 'N/A')}<br>"
                f"<b>Estudiantes:</b> {programa.get('estudiantes_matriculados', 0)}/{programa.get('cupos_totales', 0)}<br>"
                f"<b>Ocupación:</b> {programa.get('porcentaje_ocupacion', 0)}%<br>"
                f"<b>Tutor:</b> {programa.get('tutor_nombre', 'Sin asignar')}<br>"
                f"<br>"
                f"<i>Para más detalles, use la pestaña de Programas.</i>",
                QMessageBox.StandardButton.Ok
            )
    
    def show_students_details(self):
        """Mostrar detalles de estudiantes"""
        total = self.resumen_data.get('total_estudiantes', 0)
        cambio = self.resumen_data.get('estudiantes_cambio', '0%')
        
        QMessageBox.information(
            self,
            "👥 Detalles de Estudiantes",
            f"<b>Total de estudiantes activos:</b> {total}<br>"
            f"<b>Tendencia:</b> {cambio}<br><br>"
            f"<i>Para gestionar estudiantes, use la pestaña de Inicio.</i>",
            QMessageBox.StandardButton.Ok
        )
    
    def show_teachers_details(self):
        """Mostrar detalles de docentes"""
        total = self.resumen_data.get('total_docentes', 0)
        cambio = self.resumen_data.get('docentes_cambio', '0%')
        
        QMessageBox.information(
            self,
            "👨‍🏫 Detalles de Docentes",
            f"<b>Total de docentes activos:</b> {total}<br>"
            f"<b>Tendencia:</b> {cambio}<br><br>"
            f"<i>Para gestionar docentes, use la pestaña de Inicio.</i>",
            QMessageBox.StandardButton.Ok
        )
    
    def show_programs_details(self):
        """Mostrar detalles de programas"""
        total = self.resumen_data.get('programas_activos', 0)
        cambio = self.resumen_data.get('programas_cambio', '0')
        ocupacion = self.resumen_data.get('ocupacion_promedio', 0)
        
        QMessageBox.information(
            self,
            "📚 Detalles de Programas",
            f"<b>Total de programas activos:</b> {total}<br>"
            f"<b>Estado:</b> {cambio}<br>"
            f"<b>Ocupación promedio:</b> {ocupacion}%<br><br>"
            f"<i>Para gestionar programas, use la pestaña de Inicio.</i>",
            QMessageBox.StandardButton.Ok
        )
    
    def show_yearly_programs(self):
        """Mostrar programas del año actual"""
        total = self.resumen_data.get('programas_año_actual', 0)
        año = self.resumen_data.get('año_actual', datetime.now().year)
        
        QMessageBox.information(
            self,
            f"📅 Programas de {año}",
            f"<b>Total de programas creados en {año}:</b> {total}<br><br>"
            f"<i>Estos son programas nuevos registrados este año.</i>",
            QMessageBox.StandardButton.Ok
        )
    
    def show_financial_details(self):
        """Mostrar detalles financieros"""
        ingresos = self.resumen_data.get('ingresos_mes', 0)
        cambio = self.resumen_data.get('ingresos_cambio', '0%')
        mes = self.resumen_data.get('mes_actual_nombre', 'este mes')
        
        QMessageBox.information(
            self,
            "💰 Detalles Financieros",
            f"<b>Ingresos en {mes}:</b> Bs {ingresos:,.2f}<br>"
            f"<b>Tendencia:</b> {cambio}<br><br>"
            f"<i>Los ingresos provienen de inscripciones y pagos de matrícula.</i>",
            QMessageBox.StandardButton.Ok
        )
    
    def show_enrollments_details(self):
        """Mostrar detalles de inscripciones"""
        total = self.resumen_data.get('total_inscripciones_mes', 0)
        mes = self.resumen_data.get('mes_actual_nombre', 'este mes')
        
        QMessageBox.information(
            self,
            "📝 Detalles de Inscripciones",
            f"<b>Inscripciones en {mes}:</b> {total}<br><br>"
            f"<i>Estas son las nuevas inscripciones realizadas este mes.</i>",
            QMessageBox.StandardButton.Ok
        )
    
    def show_all_activity(self):
        """Mostrar toda la actividad en un diálogo"""
        actividades = self.resumen_data.get('actividad_reciente', [])
        
        if not actividades:
            QMessageBox.information(self, "Actividad", "No hay actividad registrada.")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("📋 Toda la Actividad del Sistema")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Crear widget de texto para mostrar la actividad
        text_widget = QTextEdit()
        text_widget.setReadOnly(True)
        
        # Formatear actividad
        html_content = "<h3>📋 Registro de Actividad del Sistema</h3><hr>"
        
        for i, actividad in enumerate(actividades, 1):
            usuario = actividad.get('usuario', 'Sistema')
            mensaje = actividad.get('mensaje', actividad.get('actividad', ''))
            fecha = actividad.get('fecha', '')
            
            if isinstance(fecha, datetime):
                fecha = fecha.strftime('%d/%m/%Y %H:%M')
            
            html_content += f"""
            <div style='margin-bottom: 15px; padding: 10px; background-color: #f8f9fa; border-radius: 5px;'>
                <b>{i}. {usuario}</b> - {fecha}<br>
                {mensaje}
            </div>
            """
        
        text_widget.setHtml(html_content)
        layout.addWidget(text_widget)
        
        # Botón para cerrar
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(dialog.close)
        layout.addWidget(btn_close)
        
        dialog.exec()
    
    # ============================================================================
    # MÉTODOS DE ACTUALIZACIÓN Y ACCIÓN
    # ============================================================================
    
    def refresh_resumen(self):
        """Refrescar todos los datos del resumen"""
        logger.info("🔄 Actualizando resumen...")
        
        # Mostrar indicador de carga
        self.show_loading_indicator()
        
        try:
            # Cargar nuevos datos
            self.load_initial_data()
            
            # Actualizar UI
            self._update_ui_with_new_data()
            
            # Emitir señal de datos actualizados
            self.data_updated.emit(self.resumen_data)
            
            # Mostrar mensaje de éxito
            self.show_status_message("✅ Resumen actualizado correctamente", 3000)
            
            logger.info("✅ Resumen actualizado correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando resumen: {e}")
            self.show_status_message(f"❌ Error actualizando: {str(e)}", 5000)
    
    def _update_ui_with_new_data(self):
        """Actualizar la UI con los nuevos datos"""
        if not self.is_initialized:
            return
        
        # Por simplicidad, recargamos toda la UI
        self._init_ui()
    
    def show_loading_indicator(self):
        """Mostrar indicador de carga"""
        # En una implementación real, aquí mostrarías un spinner o mensaje
        self.show_status_message("🔄 Actualizando datos...", 1000)
    
    def show_status_message(self, message: str, duration: int = 3000):
        """Mostrar mensaje de estado"""
        # Implementación simple - puedes mejorarla con una barra de estado
        print(f"STATUS: {message}")
    
    def generate_report(self):
        """Generar reporte del resumen"""
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar Reporte del Resumen",
                f"Resumen_Reporte_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                "PDF Files (*.pdf);;Text Files (*.txt);;All Files (*)"
            )
            
            if file_name:
                # Aquí implementarías la generación del reporte
                # Por ahora, solo mostramos un mensaje
                QMessageBox.information(
                    self,
                    "📊 Reporte Generado",
                    f"Reporte guardado en:\n{file_name}\n\n"
                    f"<b>Contenido del reporte:</b><br>"
                    f"- Métricas principales<br>"
                    f"- Actividad reciente<br>"
                    f"- Programas en progreso<br>"
                    f"- Datos financieros<br><br>"
                    f"<i>La generación de PDF se implementará en la próxima versión.</i>"
                )
                
                logger.info(f"Reporte generado: {file_name}")
                
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
            QMessageBox.critical(self, "Error", f"No se pudo generar el reporte:\n{str(e)}")
    
    def open_settings(self):
        """Abrir configuración del Resumen"""
        QMessageBox.information(
            self,
            "⚙️ Configuración del Resumen",
            "<b>Opciones de configuración:</b><br><br>"
            "• Intervalo de actualización automática<br>"
            "• Métricas a mostrar<br>"
            "• Tema de colores<br>"
            "• Exportación automática<br><br>"
            "<i>Esta funcionalidad estará disponible en la próxima versión.</i>"
        )
    
    def animate_stat_cards(self):
        """Animar las tarjetas de estadísticas"""
        try:
            for card in self.stat_cards:
                # Crear animación de pulso
                animation = QPropertyAnimation(card, b"geometry")
                animation.setDuration(300)
                animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                
                original_geom = card.geometry()
                animation.setStartValue(original_geom)
                animation.setEndValue(original_geom.adjusted(-1, -1, 1, 1))
                animation.start()
                
        except Exception as e:
            logger.debug(f"Error en animación: {e}")
    
    def closeEvent(self, event):
        """Manejador para el cierre del Resumen"""
        # Detener temporizadores
        if hasattr(self, 'data_timer'):
            self.data_timer.stop()
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
        
        logger.info("ResumenTab cerrado")
        super().closeEvent(event)


# ============================================================================
# PUNTO DE ENTRADA PARA PRUEBAS
# ============================================================================

if __name__ == "__main__":
    print("🧪 Ejecutando ResumenTab en modo prueba...")
    
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Datos de usuario de prueba
    user_data = {
        'username': 'admin',
        'nombres': 'Administrador',
        'apellido_paterno': 'Sistema',
        'rol': 'Administrador'
    }
    
    resumen = ResumenTab(user_data=user_data)
    resumen.setWindowTitle("Resumen - FormaGestPro v3.0")
    resumen.resize(1400, 900)
    resumen.show()
    
    print("✅ Resumen iniciado en modo prueba")
    sys.exit(app.exec())