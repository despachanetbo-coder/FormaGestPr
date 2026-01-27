# Archivo: controller/inscripcion_controller.py
"""
Controlador para gestión de inscripciones
Siguiendo el estilo establecido en la aplicación
"""
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import date, datetime
from model.inscripcion_model import InscripcionModel
from model.estudiante_model import EstudianteModel
from model.programa_model import ProgramaModel

from .base_controller import BaseController

logger = logging.getLogger(__name__)

class InscripcionController(BaseController):
    """Controlador para operaciones de inscripción"""
    
    # Configuración de directorios para documentos
    DOCUMENTOS_DIR = Path("documentos_respaldo")
    MAX_TAMANO_MB = 10  # Tamaño máximo por archivo
    
    def __init__(self):
        """Inicializa el controlador"""
        # Crear directorio si no existe
        self.DOCUMENTOS_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def verificar_preinscripcion(
        estudiante_id: int,
        programa_id: int
    ) -> Dict[str, Any]:
        """
        Verifica y prepara datos para pre-inscripción
        
        Args:
            estudiante_ci: CI del estudiante
            programa_codigo: Código del programa
            
        Returns:
            Dict con datos verificados y costos calculados
        """
        try:
            # Buscar estudiante
            from model.estudiante_model import EstudianteModel
            estudiante = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
            
            if not estudiante:
                return {
                    'success': False,
                    'message': 'Estudiante no encontrado'
                }
            
            # Buscar programa
            from model.programa_model import ProgramaModel
            programa = ProgramaModel.obtener_programa(programa_id)
            
            if not programa:
                return {
                    'success': False,
                    'message': 'Programa no encontrado'
                }
            
            # Verificar disponibilidad
            disponibilidad = InscripcionModel.verificar_disponibilidad_programa(
                programa['id']
            )
            
            if not disponibilidad.get('success', False):
                return disponibilidad
            
            if not disponibilidad['data']['disponible']:
                return {
                    'success': False,
                    'message': disponibilidad['data']['mensaje']
                }
            
            # Verificar si ya está inscrito
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'message': 'Error de conexión a la base de datos'
                }
            
            cursor = connection.cursor()
            
            query = """
            SELECT 1 FROM inscripciones 
            WHERE estudiante_id = %s AND programa_id = %s
            """
            cursor.execute(query, (estudiante['id'], programa['id']))
            ya_inscrito = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if ya_inscrito:
                return {
                    'success': False,
                    'message': 'El estudiante ya está inscrito en este programa'
                }
            
            # Calcular costos iniciales
            costo_matricula = programa['costo_matricula'] or 0
            costo_inscripcion = programa['costo_inscripcion'] or 0
            costo_inicial = costo_matricula + costo_inscripcion
            
            return {
                'success': True,
                'data': {
                    'estudiante': estudiante,
                    'programa': programa,
                    'disponibilidad': disponibilidad['data'],
                    'costos': {
                        'matricula': costo_matricula,
                        'inscripcion': costo_inscripcion,
                        'inicial': costo_inicial,
                        'total': programa['costo_total'],
                        'mensualidad': programa['costo_mensualidad']
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error verificando pre-inscripción: {e}")
            return {
                'success': False,
                'message': f'Error verificando pre-inscripción: {str(e)}'
            }
    
    @staticmethod
    def procesar_inscripcion(
        estudiante_id: int,
        programa_id: int,
        descuento: float = 0.0,
        observaciones: Optional[str] = None,
        es_retroactiva: bool = False,
        fecha_retroactiva: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Procesa una inscripción completa
        
        Args:
            estudiante_ci: CI del estudiante
            programa_codigo: Código del programa
            descuento: Descuento a aplicar
            observaciones: Observaciones adicionales
            es_retroactiva: Si es inscripción retroactiva
            fecha_retroactiva: Fecha retroactiva (si aplica)
            
        Returns:
            Dict con resultado de la inscripción
        """
        try:
            # 1. Verificar pre-inscripción
            verificacion = InscripcionController.verificar_preinscripcion(
                estudiante_id, programa_id
            )
            
            if not verificacion['success']:
                return verificacion
            
            data = verificacion['data']
            estudiante = data['estudiante']
            programa = data['programa']
            
            # 2. Crear inscripción
            if es_retroactiva and fecha_retroactiva:
                resultado = InscripcionModel.crear_inscripcion_retroactiva(
                    estudiante_id=estudiante['id'],
                    programa_id=programa['id'],
                    fecha_inscripcion=fecha_retroactiva,
                    descuento_aplicado=descuento,
                    observaciones=observaciones
                )
            else:
                resultado = InscripcionModel.crear_inscripcion(
                    estudiante_id=estudiante['id'],
                    programa_id=programa['id'],
                    descuento_aplicado=descuento,
                    observaciones=observaciones
                )
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando inscripción: {e}")
            return {
                'success': False,
                'message': f'Error procesando inscripción: {str(e)}'
            }
    
    @staticmethod
    def procesar_pago_inscripcion(
        inscripcion_id: int,
        forma_pago: str,
        monto_pagado: float,
        documentos_adjuntos: Optional[List[Dict[str, Any]]] = None,
        fecha_pago: Optional[date] = None,
        numero_comprobante: Optional[str] = None,
        banco_origen: Optional[str] = None,
        cuenta_origen: Optional[str] = None,
        observaciones: Optional[str] = None,
        usuario_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Procesa pago de inscripción con documentos adjuntos
        
        Args:
            inscripcion_id: ID de la inscripción
            forma_pago: Forma de pago
            monto_pagado: Monto pagado
            documentos_adjuntos: Lista de documentos a adjuntar
            fecha_pago: Fecha del pago
            numero_comprobante: Número de comprobante
            banco_origen: Banco de origen
            cuenta_origen: Cuenta de origen
            observaciones: Observaciones
            usuario_id: ID del usuario
            
        Returns:
            Dict con resultado del pago
        """
        try:
            # Preparar documentos para la base de datos
            documentos_db = []
            if documentos_adjuntos:
                for doc in documentos_adjuntos:
                    # Aquí deberías guardar físicamente los archivos
                    # Por ahora solo preparamos la estructura
                    documentos_db.append({
                        'tipo_documento': doc.get('tipo_documento', 'COMPROBANTE_PAGO'),
                        'nombre_original': doc.get('nombre_original', ''),
                        'nombre_archivo': doc.get('nombre_archivo', ''),
                        'extension': doc.get('extension', 'pdf'),
                        'ruta_archivo': doc.get('ruta_archivo', ''),
                        'tamano_bytes': doc.get('tamano_bytes'),
                        'observaciones': doc.get('observaciones', '')
                    })
            
            # Registrar pago completo con documentos
            if documentos_db:
                resultado = InscripcionModel.registrar_pago_completo(
                    inscripcion_id=inscripcion_id,
                    forma_pago=forma_pago,
                    monto_pagado=monto_pagado,
                    fecha_pago=fecha_pago,
                    numero_comprobante=numero_comprobante,
                    banco_origen=banco_origen,
                    cuenta_origen=cuenta_origen,
                    observaciones=observaciones,
                    registrado_por=usuario_id,
                    documentos=documentos_db
                )
            else:
                resultado = InscripcionModel.registrar_pago_inscripcion(
                    inscripcion_id=inscripcion_id,
                    forma_pago=forma_pago,
                    monto_pagado=monto_pagado,
                    fecha_pago=fecha_pago,
                    numero_comprobante=numero_comprobante,
                    banco_origen=banco_origen,
                    cuenta_origen=cuenta_origen,
                    observaciones=observaciones,
                    registrado_por=usuario_id
                )
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando pago de inscripción: {e}")
            return {
                'success': False,
                'message': f'Error procesando pago: {str(e)}'
            }
    
    @classmethod
    def guardar_documento_fisico(
        cls,
        archivo_bytes: bytes,
        nombre_original: str,
        transaccion_id: int
    ) -> Dict[str, Any]:
        """
        Guarda documento físicamente en el sistema de archivos
        
        Args:
            archivo_bytes: Contenido del archivo en bytes
            nombre_original: Nombre original del archivo
            transaccion_id: ID de la transacción
            
        Returns:
            Dict con información del archivo guardado
        """
        try:
            # Validar tamaño
            tamano_bytes = len(archivo_bytes)
            if tamano_bytes > (cls.MAX_TAMANO_MB * 1024 * 1024):
                return {
                    'success': False,
                    'message': f'Archivo demasiado grande. Máximo: {cls.MAX_TAMANO_MB}MB'
                }
            
            # Crear estructura de carpetas por año/mes
            hoy = datetime.now()
            carpeta_año = cls.DOCUMENTOS_DIR / str(hoy.year)
            carpeta_mes = carpeta_año / f"{hoy.month:02d}"
            carpeta_mes.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre único
            extension = Path(nombre_original).suffix.lower().lstrip('.')
            if extension not in ['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx']:
                extension = 'pdf'  # Por defecto
            
            nombre_unico = f"trans_{transaccion_id}_{uuid.uuid4().hex[:8]}.{extension}"
            ruta_archivo = carpeta_mes / nombre_unico
            
            # Guardar archivo
            with open(ruta_archivo, 'wb') as f:
                f.write(archivo_bytes)
            
            return {
                'success': True,
                'nombre_archivo': nombre_unico,
                'extension': extension,
                'ruta_archivo': str(ruta_archivo.relative_to(cls.DOCUMENTOS_DIR)),
                'ruta_absoluta': str(ruta_archivo.resolve()),
                'tamano_bytes': tamano_bytes
            }
            
        except Exception as e:
            logger.error(f"Error guardando documento físico: {e}")
            return {
                'success': False,
                'message': f'Error guardando documento: {str(e)}'
            }
    
    @staticmethod
    def obtener_inscripciones_con_filtros(
        estado: Optional[str] = None,
        programa_id: Optional[int] = None,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Obtiene inscripciones con filtros y estadísticas
        
        Args:
            estado: Filtrar por estado
            programa_id: Filtrar por programa
            fecha_desde: Filtrar desde fecha
            fecha_hasta: Filtrar hasta fecha
            
        Returns:
            Dict con inscripciones y estadísticas
        """
        try:
            # Obtener inscripciones
            inscripciones = InscripcionModel.obtener_inscripciones(
                filtro_estado=estado,
                filtro_programa=programa_id,
                filtro_fecha_desde=fecha_desde,
                filtro_fecha_hasta=fecha_hasta
            )
            
            # Calcular estadísticas
            total_inscripciones = len(inscripciones)
            total_recaudado = sum(i['pagos_realizados'] for i in inscripciones)
            total_saldo = sum(i['saldo_pendiente'] for i in inscripciones)
            
            # Agrupar por estado
            por_estado = {}
            for insc in inscripciones:
                estado_actual = insc['estado']
                if estado_actual not in por_estado:
                    por_estado[estado_actual] = 0
                por_estado[estado_actual] += 1
            
            # Agrupar por programa
            por_programa = {}
            for insc in inscripciones:
                programa_key = f"{insc['programa_codigo']} - {insc['programa_nombre']}"
                if programa_key not in por_programa:
                    por_programa[programa_key] = {
                        'count': 0,
                        'recaudado': 0,
                        'saldo': 0
                    }
                por_programa[programa_key]['count'] += 1
                por_programa[programa_key]['recaudado'] += insc['pagos_realizados']
                por_programa[programa_key]['saldo'] += insc['saldo_pendiente']
            
            return {
                'success': True,
                'data': {
                    'inscripciones': inscripciones,
                    'estadisticas': {
                        'total': total_inscripciones,
                        'recaudado': total_recaudado,
                        'saldo_pendiente': total_saldo,
                        'por_estado': por_estado
                    },
                    'agrupados_por_programa': por_programa,
                    'filtros_aplicados': {
                        'estado': estado,
                        'programa_id': programa_id,
                        'fecha_desde': fecha_desde.isoformat() if fecha_desde else None,
                        'fecha_hasta': fecha_hasta.isoformat() if fecha_hasta else None
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo inscripciones con filtros: {e}")
            return {
                'success': False,
                'message': f'Error obteniendo inscripciones: {str(e)}'
            }
    
    @staticmethod
    def obtener_informacion_pagos_inscripcion(inscripcion_id: int) -> Dict[str, Any]:
        """
        Obtener información completa de pagos de una inscripción
        
        Args:
            inscripcion_id: ID de la inscripción
            
        Returns:
            Dict con información de saldos, pagos y detalles
        """
        try:
            from model.inscripcion_model import InscripcionModel
            from model.transaccion_model import TransaccionModel
            
            # Obtener saldo pendiente del modelo
            resultado_saldo = InscripcionModel.obtener_saldo_pendiente_inscripcion(inscripcion_id)
            
            if not resultado_saldo.get('exito'):
                return resultado_saldo
            
            # Obtener transacciones de la inscripción
            transacciones = TransaccionModel.obtener_transacciones_inscripcion(inscripcion_id)
            
            # Enriquecer resultado con transacciones
            resultado_saldo['transacciones'] = transacciones
            resultado_saldo['cantidad_transacciones'] = len(transacciones)
            
            return resultado_saldo
            
        except Exception as e:
            logger.error(f"Error obteniendo información de pagos inscripción {inscripcion_id}: {e}")
            return {
                'exito': False,
                'error': str(e),
                'saldo_pendiente': 0.0,
                'transacciones': []
            }
    
    @staticmethod
    def generar_reporte_inscripciones(
        fecha_inicio: date,
        fecha_fin: date,
        programa_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Genera reporte detallado de inscripciones en un periodo
        
        Args:
            fecha_inicio: Fecha de inicio del reporte
            fecha_fin: Fecha de fin del reporte
            programa_id: ID del programa (opcional)
            
        Returns:
            Dict con reporte detallado
        """
        try:
            # Obtener inscripciones del periodo
            resultado = InscripcionController.obtener_inscripciones_con_filtros(
                programa_id=programa_id,
                fecha_desde=fecha_inicio,
                fecha_hasta=fecha_fin
            )
            
            if not resultado['success']:
                return resultado
            
            data = resultado['data']
            
            # Obtener información adicional si hay programa específico
            info_programa = None
            if programa_id:
                from model.programa_model import ProgramaModel
                programa = ProgramaModel.obtener_por_id(programa_id)
                if programa:
                    info_programa = programa
            
            # Calcular promedios
            total_inscripciones = data['estadisticas']['total']
            if total_inscripciones > 0:
                promedio_recaudado = data['estadisticas']['recaudado'] / total_inscripciones
                promedio_saldo = data['estadisticas']['saldo_pendiente'] / total_inscripciones
            else:
                promedio_recaudado = promedio_saldo = 0
            
            # Generar estructura del reporte
            reporte = {
                'periodo': {
                    'inicio': fecha_inicio.isoformat(),
                    'fin': fecha_fin.isoformat()
                },
                'programa': info_programa,
                'resumen': {
                    'total_inscripciones': total_inscripciones,
                    'total_recaudado': data['estadisticas']['recaudado'],
                    'total_saldo_pendiente': data['estadisticas']['saldo_pendiente'],
                    'promedio_recaudado_por_inscripcion': promedio_recaudado,
                    'promedio_saldo_por_inscripcion': promedio_saldo,
                    'distribucion_por_estado': data['estadisticas']['por_estado']
                },
                'detalle_por_programa': data['agrupados_por_programa'],
                'inscripciones_detalladas': data['inscripciones']
            }
            
            return {
                'success': True,
                'data': reporte
            }
            
        except Exception as e:
            logger.error(f"Error generando reporte de inscripciones: {e}")
            return {
                'success': False,
                'message': f'Error generando reporte: {str(e)}'
            }