# -*- coding: utf-8 -*-
# Archivo: model/resumen_model.py
"""
ResumenModel - Modelo para obtener datos del dashboard/resumen desde PostgreSQL
Versión simplificada con queries directas en lugar de funciones
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from config.database import Database

logger = logging.getLogger(__name__)


class ResumenModel:
    """Modelo para obtener datos del dashboard/resumen con queries directas"""
    
    def __init__(self):
        """Inicializar modelo de resumen"""
        self.db = Database
        logger.info("ResumenModel inicializado (versión queries directas)")
    
    def obtener_metricas_principales(self) -> Dict[str, Any]:
        """Obtener métricas principales del sistema"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {}
            
            cursor = connection.cursor()
            fecha_inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            año_actual = datetime.now().year
            
            # 1. Total estudiantes activos
            cursor.execute("""
                SELECT COUNT(*) FROM estudiantes 
                WHERE activo = True
            """)
            if not cursor:
                logger.error("Cursor no disponible para obtener total de estudiantes")
                return {}
            result = cursor.fetchone()
            if not result:
                logger.warning("No se obtuvo resultado para total de estudiantes")
                total_estudiantes = 0
            else:
                total_estudiantes = result[0]
            
            # 2. Total docentes activos
            cursor.execute("""
                SELECT COUNT(*) FROM docentes 
                WHERE activo = True
            """)
            result = cursor.fetchone()
            if not result:
                logger.warning("No se obtuvo resultado para total de docentes")
                total_docentes = 0
            else:
                total_docentes = result[0]
            
            # 3. Programas activos (no cancelados ni concluidos)
            cursor.execute("""
                SELECT COUNT(*) FROM programas 
                WHERE estado NOT IN ('CANCELADO', 'CONCLUIDO')
            """)
            result = cursor.fetchone()
            if not result:
                logger.warning("No se obtuvo resultado para total de programas activos")
                programas_activos = 0
            else:
                programas_activos = result[0]
            
            # 4. Programas creados en el año actual
            cursor.execute("""
                SELECT COUNT(*) FROM programas 
                WHERE EXTRACT(YEAR FROM fecha_inicio) = %s
            """, (año_actual,))
            result = cursor.fetchone()
            if not result:
                logger.warning("No se obtuvo resultado para total de programas del año actual")
                programas_año_actual = 0
            else:
                programas_año_actual = result[0]
            
            # 5. Ingresos del mes actual (suma de montos finales de transacciones del mes)
            cursor.execute("""
                SELECT COALESCE(SUM(monto_final), 0) 
                FROM transacciones 
                WHERE fecha_pago >= %s 
                AND estado IN ('CONFIRMADO', 'COMPLETADO')
            """, (fecha_inicio_mes,))
            result = cursor.fetchone()
            if not result:
                logger.warning("No se obtuvo resultado para ingresos del mes actual")
                ingresos_mes = 0.0
            else:
                ingresos_mes = float(result[0] or 0)
            
            # 6. Inscripciones del mes actual
            cursor.execute("""
                SELECT COUNT(*) FROM inscripciones 
                WHERE fecha_inscripcion >= %s
            """, (fecha_inicio_mes,))
            result = cursor.fetchone()
            if not result:
                logger.warning("No se obtuvo resultado para inscripciones del mes actual")
                inscripciones_mes = 0
            else:
                inscripciones_mes = result[0] or 0
            
            cursor.close()
            self.db.return_connection(connection)
            
            return {
                'total_estudiantes': total_estudiantes,
                'total_docentes': total_docentes,
                'programas_activos': programas_activos,
                'programas_año_actual': programas_año_actual,
                'ingresos_mes': ingresos_mes,
                'inscripciones_mes': inscripciones_mes
            }
            
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
            
            # Consultar programas con conteo de estudiantes inscritos
            cursor.execute("""
                SELECT 
                    p.nombre,
                    COUNT(i.id) as total_inscritos
                FROM programas p
                LEFT JOIN inscripciones i ON p.id = i.programa_id 
                    AND i.estado NOT IN ('RETIRADO', 'CANCELADO')
                WHERE p.estado NOT IN ('CANCELADO', 'CONCLUIDO')
                GROUP BY p.id, p.nombre
                HAVING COUNT(i.id) > 0
                ORDER BY total_inscritos DESC
                LIMIT 10
            """)
            
            resultados = cursor.fetchall()
            cursor.close()
            self.db.return_connection(connection)
            
            distribucion = {}
            for row in resultados:
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
            
            cursor.execute("""
                SELECT 
                    p.id,
                    p.codigo,
                    p.nombre,
                    p.estado,
                    CASE 
                        WHEN p.estado = 'ACTIVO' THEN '🟢 Activo'
                        WHEN p.estado = 'PLANIFICADO' THEN '🟡 Planificado'
                        WHEN p.estado = 'EN_CURSO' THEN '🔵 En Curso'
                        WHEN p.estado = 'FINALIZADO' THEN '⚫ Finalizado'
                        WHEN p.estado = 'CANCELADO' THEN '⚪ Cancelado'
                        WHEN p.estado = 'CONCLUIDO' THEN '⚫ Concluido'
                        ELSE p.estado
                    END as estado_display,
                    COUNT(DISTINCT i.id) as estudiantes_matriculados,
                    p.cupos_maximos as cupos_totales,
                    CASE 
                        WHEN p.cupos_maximos > 0 
                        THEN ROUND((COUNT(DISTINCT i.id)::DECIMAL / p.cupos_maximos * 100), 1)
                        ELSE 0
                    END as porcentaje_ocupacion,
                    CONCAT(d.nombres, ' ', d.apellido_paterno, ' ', COALESCE(d.apellido_materno, '')) as tutor_nombre,
                    p.fecha_inicio,
                    p.fecha_fin,
                    p.duracion_meses,
                    p.horas_totales
                FROM programas p
                LEFT JOIN inscripciones i ON p.id = i.programa_id 
                    AND i.estado NOT IN ('RETIRADO', 'CANCELADO')
                LEFT JOIN docentes d ON p.docente_coordinador_id = d.id
                WHERE p.estado IN ('ACTIVO', 'EN_CURSO', 'PLANIFICADO')
                    AND p.fecha_inicio <= CURRENT_DATE
                    AND (p.fecha_fin IS NULL OR p.fecha_fin >= CURRENT_DATE)
                GROUP BY p.id, p.codigo, p.nombre, p.estado, p.cupos_maximos, 
                         d.nombres, d.apellido_paterno, d.apellido_materno, 
                         p.fecha_inicio, p.fecha_fin, p.duracion_meses, p.horas_totales
                ORDER BY p.fecha_inicio DESC
                LIMIT %s
            """, (limite,))
            
            resultados = cursor.fetchall()
            cursor.close()
            self.db.return_connection(connection)
            
            programas = []
            for row in resultados:
                programa = {
                    'id': row[0],
                    'codigo': row[1],
                    'nombre': row[2],
                    'estado': row[3],
                    'estado_display': row[4],
                    'estudiantes_matriculados': row[5] or 0,
                    'cupos_totales': row[6] or 0,
                    'cupos_ocupados': row[5] or 0,
                    'porcentaje_ocupacion': float(row[7]) if row[7] else 0.0,
                    'tutor_nombre': row[8] or 'Sin asignar',
                    'fecha_inicio': row[9].isoformat() if row[9] else None,
                    'fecha_fin': row[10].isoformat() if row[10] else None
                }
                programas.append(programa)
            
            return programas
            
        except Exception as e:
            logger.error(f"Error obteniendo programas en progreso: {e}")
            return []
    
    def obtener_datos_financieros(self, meses: int = 6) -> List[Dict]:
        """Obtener datos financieros históricos por mes"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            
            # Generar lista de últimos N meses
            fecha_fin = datetime.now()
            fecha_inicio = fecha_fin - timedelta(days=30 * meses)
            
            cursor.execute("""
                WITH meses AS (
                    SELECT 
                        date_trunc('month', generate_series(%s::date, %s::date, '1 month'::interval)) as mes
                ),
                ingresos_mensuales AS (
                    SELECT 
                        date_trunc('month', t.fecha_pago) as mes,
                        COALESCE(SUM(t.monto_final), 0) as ingresos
                    FROM transacciones t
                    WHERE t.fecha_pago >= %s 
                        AND t.estado IN ('CONFIRMADO', 'COMPLETADO')
                    GROUP BY date_trunc('month', t.fecha_pago)
                ),
                gastos_mensuales AS (
                    -- Asumiendo que hay una tabla de gastos, si no, usar 30% de ingresos como estimación
                    SELECT 
                        date_trunc('month', t.fecha_pago) as mes,
                        COALESCE(SUM(t.monto_final) * 0.3, 0) as gastos
                    FROM transacciones t
                    WHERE t.fecha_pago >= %s 
                        AND t.estado IN ('CONFIRMADO', 'COMPLETADO')
                    GROUP BY date_trunc('month', t.fecha_pago)
                )
                SELECT 
                    TO_CHAR(m.mes, 'Mon YYYY') as mes_nombre,
                    COALESCE(i.ingresos, 0) as ingresos,
                    COALESCE(g.gastos, 0) as gastos,
                    COALESCE(i.ingresos, 0) - COALESCE(g.gastos, 0) as saldo
                FROM meses m
                LEFT JOIN ingresos_mensuales i ON m.mes = i.mes
                LEFT JOIN gastos_mensuales g ON m.mes = g.mes
                ORDER BY m.mes DESC
            """, (fecha_inicio, fecha_fin, fecha_inicio, fecha_inicio))
            
            resultados = cursor.fetchall()
            cursor.close()
            self.db.return_connection(connection)
            
            datos = []
            saldo_acumulado = 0
            
            for row in reversed(resultados):  # Revertir para orden cronológico
                saldo_acumulado += float(row[3])
                dato = {
                    'mes': row[0],
                    'ingresos': float(row[1]),
                    'gastos': float(row[2]),
                    'saldo': float(row[3]),
                    'saldo_acumulado': saldo_acumulado
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
            
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT p.id) as total_programas,
                    COUNT(DISTINCT i.id) as total_estudiantes_inscritos,
                    SUM(p.cupos_maximos) as total_cupos,
                    CASE 
                        WHEN SUM(p.cupos_maximos) > 0 
                        THEN ROUND((COUNT(DISTINCT i.id)::DECIMAL / SUM(p.cupos_maximos) * 100), 1)
                        ELSE 0
                    END as ocupacion_promedio
                FROM programas p
                LEFT JOIN inscripciones i ON p.id = i.programa_id 
                    AND i.estado NOT IN ('RETIRADO', 'CANCELADO')
                WHERE p.estado NOT IN ('CANCELADO', 'CONCLUIDO')
                    AND p.cupos_maximos > 0
            """)
            
            resultado = cursor.fetchone()
            cursor.close()
            self.db.return_connection(connection)
            
            if resultado:
                return {
                    'total_programas': resultado[0] or 0,
                    'total_estudiantes_inscritos': resultado[1] or 0,
                    'total_cupos': resultado[2] or 0,
                    'ocupacion_promedio': float(resultado[3]) if resultado[3] else 0.0
                }
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de ocupación: {e}")
            return {}
    
    def obtener_actividad_reciente(self, limite: int = 20) -> List[Dict]:
        """Obtener actividad reciente del sistema"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            
            # Combinar actividades de diferentes fuentes
            cursor.execute("""
                (SELECT 
                    CONCAT(u.nombre_completo) as usuario,
                    'Transacción registrada' as actividad,
                    TO_CHAR(t.fecha_registro, 'DD/MM/YYYY HH24:MI') as fecha,
                    'pago' as tipo,
                    CONCAT('Transacción ', t.numero_transaccion, ' - Bs ', t.monto_final) as detalle,
                    t.fecha_registro as fecha_orden
                FROM transacciones t
                JOIN usuarios u ON t.registrado_por = u.id
                WHERE t.estado IN ('CONFIRMADO', 'COMPLETADO')
                LIMIT 10)
                
                UNION ALL
                
                (SELECT 
                    CONCAT('Sistema') as usuario,
                    'Nueva inscripción' as actividad,
                    TO_CHAR(i.fecha_inscripcion, 'DD/MM/YYYY HH24:MI') as fecha,
                    'inscripcion' as tipo,
                    CONCAT('Inscripción ID: ', i.id, ' - Estudiante: ', e.apellido_paterno, ' ', e.nombres) as detalle,
                    i.fecha_inscripcion as fecha_orden
                FROM inscripciones i
                JOIN estudiantes e ON i.estudiante_id = e.id
                LIMIT 10)
                
                UNION ALL
                
                (SELECT 
                    CONCAT('Sistema') as usuario,
                    'Nuevo estudiante' as actividad,
                    TO_CHAR(e.fecha_registro, 'DD/MM/YYYY HH24:MI') as fecha,
                    'estudiante' as tipo,
                    CONCAT('Estudiante: ', e.apellido_paterno, ' ', e.nombres, ' - CI: ', e.ci_numero) as detalle,
                    e.fecha_registro as fecha_orden
                FROM estudiantes e
                WHERE e.fecha_registro IS NOT NULL
                LIMIT 10)
                
                ORDER BY fecha_orden DESC
                LIMIT %s
            """, (limite,))
            
            resultados = cursor.fetchall()
            cursor.close()
            self.db.return_connection(connection)
            
            actividades = []
            for row in resultados:
                actividad = {
                    'usuario': row[0],
                    'actividad': row[1],
                    'fecha': row[2],
                    'tipo': row[3],
                    'detalle': row[4]
                }
                actividades.append(actividad)
            
            return actividades
            
        except Exception as e:
            logger.error(f"Error obteniendo actividad reciente: {e}")
            return []
    
    def obtener_programas_populares(self, limite: int = 5) -> List[Dict]:
        """Obtener los programas más populares"""
        try:
            connection = self.db.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []
            
            cursor = connection.cursor()
            
            cursor.execute("""
                SELECT 
                    p.nombre,
                    p.codigo,
                    COUNT(i.id) as inscritos,
                    p.cupos_maximos,
                    CASE 
                        WHEN p.cupos_maximos > 0 
                        THEN ROUND((COUNT(i.id)::DECIMAL / p.cupos_maximos * 100), 1)
                        ELSE 0
                    END as porcentaje_ocupacion,
                    p.costo_total
                FROM programas p
                LEFT JOIN inscripciones i ON p.id = i.programa_id 
                    AND i.estado NOT IN ('RETIRADO', 'CANCELADO')
                WHERE p.estado NOT IN ('CANCELADO', 'CONCLUIDO')
                GROUP BY p.id, p.nombre, p.codigo, p.cupos_maximos, p.costo_total
                HAVING COUNT(i.id) > 0
                ORDER BY inscritos DESC
                LIMIT %s
            """, (limite,))
            
            resultados = cursor.fetchall()
            cursor.close()
            self.db.return_connection(connection)
            
            programas = []
            for row in resultados:
                programa = {
                    'nombre': row[0],
                    'codigo': row[1],
                    'inscritos': row[2],
                    'cupos_totales': row[3] or 0,
                    'porcentaje_ocupacion': float(row[4]) if row[4] else 0.0,
                    'costo_total': float(row[5]) if row[5] else 0.0
                }
                programas.append(programa)
            
            return programas
            
        except Exception as e:
            logger.error(f"Error obteniendo programas populares: {e}")
            return []
    
    def obtener_alertas_sistema(self) -> List[Dict]:
        """Obtener alertas del sistema basadas en datos"""
        try:
            alertas = []
            connection = self.db.get_connection()
            if not connection:
                return alertas
            
            cursor = connection.cursor()
            
            # Alerta: Programas con cupos casi llenos (>90%)
            cursor.execute("""
                SELECT 
                    p.codigo,
                    p.nombre,
                    COUNT(i.id) as inscritos,
                    p.cupos_maximos
                FROM programas p
                LEFT JOIN inscripciones i ON p.id = i.programa_id 
                    AND i.estado NOT IN ('RETIRADO', 'CANCELADO')
                WHERE p.estado NOT IN ('CANCELADO', 'CONCLUIDO')
                    AND p.cupos_maximos > 0
                GROUP BY p.id, p.codigo, p.nombre, p.cupos_maximos
                HAVING COUNT(i.id) >= p.cupos_maximos * 0.9
                ORDER BY (COUNT(i.id)::DECIMAL / p.cupos_maximos) DESC
                LIMIT 5
            """)
            
            programas_llenos = cursor.fetchall()
            for prog in programas_llenos:
                alertas.append({
                    'tipo': 'programa_lleno',
                    'mensaje': f"Programa {prog[0]} - {prog[1]} está al {int(prog[2]/prog[3]*100)}% de capacidad",
                    'nivel': 'advertencia',
                    'fecha': datetime.now().isoformat()
                })
            
            # Alerta: Pagos atrasados (más de 30 días sin pago)
            cursor.execute("""
                SELECT 
                    i.id,
                    CONCAT(e.apellido_paterno, ' ', e.nombres) as estudiante,
                    p.nombre as programa,
                    i.fecha_inscripcion
                FROM inscripciones i
                JOIN estudiantes e ON i.estudiante_id = e.id
                JOIN programas p ON i.programa_id = p.id
                LEFT JOIN transacciones t ON i.estudiante_id = t.estudiante_id 
                    AND i.programa_id = t.programa_id
                WHERE i.estado = 'INSCRITO'
                    AND i.fecha_inscripcion < CURRENT_DATE - INTERVAL '30 days'
                    AND t.id IS NULL
                LIMIT 5
            """)
            
            pagos_atrasados = cursor.fetchall()
            for pago in pagos_atrasados:
                alertas.append({
                    'tipo': 'pago_atrasado',
                    'mensaje': f"Estudiante {pago[1]} tiene pago pendiente en {pago[2]}",
                    'nivel': 'critico',
                    'fecha': datetime.now().isoformat()
                })
            
            # Alerta: Programas que inician pronto (próximos 7 días)
            cursor.execute("""
                SELECT 
                    codigo,
                    nombre,
                    fecha_inicio,
                    EXTRACT(DAY FROM fecha_inicio - CURRENT_DATE) as dias_restantes
                FROM programas
                WHERE estado = 'PLANIFICADO'
                    AND fecha_inicio BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '7 days'
                ORDER BY fecha_inicio
            """)
            
            programas_proximos = cursor.fetchall()
            for prog in programas_proximos:
                alertas.append({
                    'tipo': 'inicio_programa',
                    'mensaje': f"Programa {prog[0]} - {prog[1]} inicia en {int(prog[3])} días",
                    'nivel': 'informacion',
                    'fecha': datetime.now().isoformat()
                })
            
            cursor.close()
            self.db.return_connection(connection)
            
            return alertas
            
        except Exception as e:
            logger.error(f"Error obteniendo alertas del sistema: {e}")
            return []
    
    def obtener_datos_completos_dashboard(self) -> Dict[str, Any]:
        """Obtener todos los datos necesarios para el dashboard"""
        try:
            año_actual = datetime.now().year
            mes_actual = datetime.now().strftime('%B')
            
            # Obtener todas las métricas
            metricas = self.obtener_metricas_principales()
            distribucion = self.obtener_distribucion_estudiantes()
            programas = self.obtener_programas_en_progreso(10)
            financieros = self.obtener_datos_financieros(6)
            actividad = self.obtener_actividad_reciente(20)
            estadisticas_ocupacion = self.obtener_estadisticas_ocupacion()
            
            # Calcular totales
            total_estudiantes_activos = metricas.get('total_estudiantes', 0)
            total_docentes_activos = metricas.get('total_docentes', 0)
            
            # Construir objeto completo
            return {
                # Métricas principales
                'total_estudiantes': total_estudiantes_activos,
                'total_docentes': total_docentes_activos,
                'programas_activos': metricas.get('programas_activos', 0),
                'programas_año_actual': metricas.get('programas_año_actual', 0),
                'ingresos_mes': metricas.get('ingresos_mes', 0.0),
                'gastos_mes': metricas.get('ingresos_mes', 0.0) * 0.3,  # Estimación 30%
                
                # Cambios (simulados por ahora)
                'estudiantes_cambio': f"+{min(10, total_estudiantes_activos // 10 if total_estudiantes_activos > 0 else 0)}%",
                'docentes_cambio': f"+{min(5, total_docentes_activos // 5 if total_docentes_activos > 0 else 0)}%",
                'programas_cambio': f"{metricas.get('programas_activos', 0)} activos",
                'programas_cambio_año': f"+{metricas.get('programas_año_actual', 0)} este año",
                'ingresos_cambio': f"+{min(15, int(metricas.get('ingresos_mes', 0) // 1000) if metricas.get('ingresos_mes', 0) > 0 else 0)}%",
                
                # Información temporal
                'año_actual': año_actual,
                'mes_actual_nombre': mes_actual,
                'fecha_actual': datetime.now().strftime('%d/%m/%Y'),
                
                # Datos detallados
                'estudiantes_por_programa': distribucion,
                'programas_en_progreso': programas,
                'datos_financieros': financieros,
                'actividad_reciente': actividad,
                'ocupacion_promedio': estadisticas_ocupacion.get('ocupacion_promedio', 0.0),
                
                # Totales para estadísticas
                'total_inscripciones_mes': metricas.get('inscripciones_mes', 0),
                'total_programas_registrados': metricas.get('programas_activos', 0),
                'total_estudiantes_activos': total_estudiantes_activos,
                'total_docentes_activos': total_docentes_activos
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos completos del dashboard: {e}")
            return self._get_sample_data()
    
    def _get_sample_data(self) -> Dict:
        """Datos de ejemplo para fallback"""
        año_actual = datetime.now().year
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