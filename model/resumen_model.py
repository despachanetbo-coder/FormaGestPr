# Archivo: model/resumen_model.py
# -*- coding: utf-8 -*-
"""
ResumenModel - Modelo para obtener datos del dashboard/resumen desde PostgreSQL
Autor: Sistema FormaGestPro
Versión: 1.0.0
"""

import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

from config.database import Database

# Configurar logging
logger = logging.getLogger(__name__)


class ResumenModel:
    """Modelo para obtener datos del dashboard/resumen"""
    
    def __init__(self, db_config: Optional[Dict] = None):
        """Inicializar modelo de resumen"""
        self.db = Database.get_instance()
        self.db_config = db_config or {}
        logger.info("ResumenModel inicializado")
    
    def obtener_datos_dashboard(self) -> Dict[str, Any]:
        """
        Obtener todos los datos del dashboard usando la función PostgreSQL
        
        Returns:
            Dict con todos los datos del dashboard
        """
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return self._get_sample_data()
            
            cursor = connection.cursor()
            
            # Ejecutar función PostgreSQL
            cursor.execute("SELECT * FROM fn_obtener_datos_dashboard();")
            result = cursor.fetchone()
            
            if result and result[0]:
                # Convertir JSON de PostgreSQL a diccionario Python
                datos_json = result[0]
                if isinstance(datos_json, str):
                    datos = json.loads(datos_json)
                else:
                    datos = datos_json
                
                logger.info(f"Datos del dashboard obtenidos desde PostgreSQL")
                return datos
            else:
                logger.warning("Función obtener_datos_dashboard no devolvió datos")
                return self._get_sample_data()
                
        except Exception as e:
            logger.error(f"Error obteniendo datos del dashboard desde PostgreSQL: {e}")
            return self._get_sample_data()
    
    def obtener_metricas_principales(self) -> Dict[str, Any]:
        """Obtener métricas principales rápidas"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {}
            
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM fn_obtener_metricas_principales();")
            result = cursor.fetchone()
            
            if result:
                return {
                    'total_estudiantes': result[0],
                    'total_docentes': result[1],
                    'programas_activos': result[2],
                    'programas_año_actual': result[3],
                    'ingresos_mes': float(result[4]) if result[4] else 0.0,
                    'inscripciones_mes': result[5]
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo métricas principales: {e}")
            return {}
    
    def obtener_distribucion_estudiantes(self) -> Dict[str, int]:
        """Obtener distribución de estudiantes por programa"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {}
            
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM fn_obtener_distribucion_estudiantes();")
            results = cursor.fetchall()
            
            distribucion = {}
            for row in results:
                distribucion[row[0]] = row[1]
            
            return distribucion
            
        except Exception as e:
            logger.error(f"Error obteniendo distribución de estudiantes: {e}")
            return {}
    
    def obtener_programas_en_progreso(self, limite: int = 10) -> List[Dict]:
        """Obtener programas en progreso con detalles"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM fn_obtener_programas_en_progreso({limite});")
            results = cursor.fetchall()
            
            programas = []
            for row in results:
                programa = {
                    'id': row[0],
                    'codigo': row[1],
                    'nombre': row[2],
                    'estado': row[3],
                    'estado_display': row[4],
                    'estudiantes_matriculados': row[5],
                    'cupos_totales': row[6],
                    'cupos_ocupados': row[5],  # Mismo que estudiantes matriculados
                    'porcentaje_ocupacion': float(row[7]) if row[7] else 0.0,
                    'tutor_nombre': row[8],
                    'fecha_inicio': row[9].isoformat() if row[9] else None,
                    'fecha_fin': row[10].isoformat() if row[10] else None
                }
                programas.append(programa)
            
            return programas
            
        except Exception as e:
            logger.error(f"Error obteniendo programas en progreso: {e}")
            return []
    
    def obtener_datos_financieros(self, meses: int = 6) -> List[Dict]:
        """Obtener datos financieros históricos"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM fn_obtener_datos_financieros({meses});")
            results = cursor.fetchall()
            
            datos = []
            for row in results:
                dato = {
                    'mes': row[0],
                    'ingresos': float(row[1]) if row[1] else 0.0,
                    'gastos': float(row[2]) if row[2] else 0.0,
                    'saldo': float(row[3]) if row[3] else 0.0,
                    'saldo_acumulado': float(row[4]) if row[4] else 0.0
                }
                datos.append(dato)
            
            return datos
            
        except Exception as e:
            logger.error(f"Error obteniendo datos financieros: {e}")
            return []
    
    def obtener_estadisticas_ocupacion(self) -> Dict[str, Any]:
        """Obtener estadísticas de ocupación de programas"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {}
            
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM fn_obtener_estadisticas_ocupacion();")
            result = cursor.fetchone()
            
            if result:
                return {
                    'total_programas': result[0],
                    'total_estudiantes_inscritos': result[1],
                    'total_cupos': result[2],
                    'ocupacion_promedio': float(result[3]) if result[3] else 0.0
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de ocupación: {e}")
            return {}
    
    def obtener_contadores_tiempo_real(self) -> Dict[str, Any]:
        """Obtener contadores en tiempo real para actualización automática"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {}
            
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM fn_obtener_contadores_tiempo_real();")
            result = cursor.fetchone()
            
            if result and result[0]:
                datos_json = result[0]
                if isinstance(datos_json, str):
                    return json.loads(datos_json)
                return datos_json
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo contadores tiempo real: {e}")
            return {}
    
    def obtener_programas_populares(self, limite: int = 5) -> List[Dict]:
        """Obtener los programas más populares"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            cursor.execute(f"SELECT * FROM fn_obtener_programas_populares({limite});")
            results = cursor.fetchall()
            
            programas = []
            for row in results:
                programa = {
                    'nombre': row[0],
                    'codigo': row[1],
                    'inscritos': row[2],
                    'cupos_totales': row[3],
                    'porcentaje_ocupacion': float(row[4]) if row[4] else 0.0,
                    'costo_total': float(row[5]) if row[5] else 0.0
                }
                programas.append(programa)
            
            return programas
            
        except Exception as e:
            logger.error(f"Error obteniendo programas populares: {e}")
            return []
    
    def obtener_alertas_sistema(self) -> List[Dict]:
        """Obtener alertas del sistema"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM fn_obtener_alertas_sistema();")
            results = cursor.fetchall()
            
            alertas = []
            for row in results:
                alerta = {
                    'tipo': row[0],
                    'mensaje': row[1],
                    'nivel': row[2],
                    'fecha': row[3].isoformat() if row[3] else None
                }
                alertas.append(alerta)
            
            return alertas
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas del sistema: {e}")
            return []
    
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
            'estudiantes_cambio': '+3 este mes',
            'docentes_cambio': '+1 este mes',
            'programas_cambio': '3 activos',
            'programas_cambio_año': '+2 este año',
            'ingresos_cambio': '+12%',
            'año_actual': año_actual,
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
                    'estado_display': '🟢 Activo',
                    'estudiantes_matriculados': 24,
                    'cupos_ocupados': 24,
                    'cupos_totales': 30,
                    'porcentaje_ocupacion': 80.0,
                    'tutor_nombre': 'Dr. Carlos Méndez'
                }
            ],
            'datos_financieros': [
                {'mes': 'Ene 2024', 'ingresos': 12000, 'gastos': 4000, 'saldo': 8000, 'saldo_acumulado': 8000},
                {'mes': 'Feb 2024', 'ingresos': 14000, 'gastos': 4500, 'saldo': 9500, 'saldo_acumulado': 17500},
                {'mes': 'Mar 2024', 'ingresos': 16000, 'gastos': 5000, 'saldo': 11000, 'saldo_acumulado': 28500}
            ],
            'actividad_reciente': [],
            'ocupacion_promedio': 65.5,
            'total_inscripciones_mes': 15,
            'total_programas_registrados': 25,
            'total_estudiantes_activos': 150,
            'total_docentes_activos': 25
        }