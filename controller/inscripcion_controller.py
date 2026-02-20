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
            estudiante_id: ID del estudiante
            programa_id: ID del programa
            
        Returns:
            Dict con datos verificados y costos calculados
        """
        try:
            # Buscar estudiante
            from model.estudiante_model import EstudianteModel
            
            # El método buscar_estudiante_id devuelve un diccionario directamente
            estudiante = EstudianteModel.buscar_estudiante_id(estudiante_id)
            
            if not estudiante:
                return {
                    'success': False,
                    'message': f'Estudiante con ID {estudiante_id} no encontrado'
                }
            
            # Buscar programa
            from model.programa_model import ProgramaModel
            resultado_programa = ProgramaModel.obtener_programa(programa_id)
            
            if not resultado_programa.get('success'):
                return {
                    'success': False,
                    'message': f'Programa con ID {programa_id} no encontrado'
                }
            
            programa = resultado_programa['data']
            
            # Verificar disponibilidad
            disponibilidad = InscripcionModel.verificar_disponibilidad_programa(programa_id)
            
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
            cursor.execute(query, (estudiante_id, programa_id))
            ya_inscrito = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if ya_inscrito:
                return {
                    'success': False,
                    'message': 'El estudiante ya está inscrito en este programa'
                }
            
            # Calcular costos iniciales
            costo_matricula = float(programa.get('costo_matricula', 0) or 0)
            costo_inscripcion = float(programa.get('costo_inscripcion', 0) or 0)
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
                        'total': float(programa.get('costo_total', 0) or 0),
                        'mensualidad': float(programa.get('costo_mensualidad', 0) or 0)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error verificando pre-inscripción: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                'success': False,
                'message': f'Error verificando pre-inscripción: {str(e)}'
            }
    
    @staticmethod
    def validar_observaciones_con_descuento(
        valor_real: float,
        valor_final: float,
        observaciones: str
    ) -> tuple[bool, str]:
        """
        Valida que las observaciones tengan el formato correcto cuando hay descuento
        
        Args:
            valor_real: Valor real del programa
            valor_final: Valor final de la inscripción
            observaciones: Observaciones a validar
            
        Returns:
            Tuple (es_valido, mensaje_error)
        """
        if valor_final <= 0:
            return False, "El valor final debe ser mayor a 0"
        
        if valor_final > valor_real:
            return False, f"El valor final ({valor_final:.2f}) no puede ser mayor al valor real ({valor_real:.2f})"
        
        # Si no hay descuento
        if abs(valor_final - valor_real) < 0.01:  # Consideramos iguales si la diferencia es menor a 1 centavo
            esperado = "No se aplicó ningún descuento"
            if esperado not in observaciones:
                return False, f"Cuando no hay descuento, las observaciones deben contener: '{esperado}'"
            return True, ""
        
        # Si hay descuento
        porcentaje = ((valor_real - valor_final) / valor_real) * 100
        patron_esperado = f"Se aplica un descuento de {porcentaje:.2f}% Justificación:"
        
        if not observaciones.startswith(patron_esperado):
            return False, f"Las observaciones deben comenzar con: '{patron_esperado}'"
        
        # Verificar que haya justificación después de "Justificación: "
        if "Justificación:" in observaciones:
            partes = observaciones.split("Justificación:")
            if len(partes) > 1 and partes[1].strip() == "":
                return False, "Debe proporcionar una justificación para el descuento"
        
        return True, ""
    
    @staticmethod
    def generar_observaciones_automaticas(
        valor_real: float,
        valor_final: float,
        justificacion: str = ""
    ) -> str:
        """
        Genera observaciones automáticas según el valor final
        
        Args:
            valor_real: Valor real del programa
            valor_final: Valor final de la inscripción
            justificacion: Justificación si hay descuento
            
        Returns:
            Observaciones formateadas
        """
        if abs(valor_final - valor_real) < 0.01:
            return "No se aplicó ningún descuento"
        
        porcentaje = ((valor_real - valor_final) / valor_real) * 100
        return f"Se aplica un descuento de {porcentaje:.2f}% Justificación: {justificacion}".strip()
    
    @staticmethod
    def procesar_inscripcion(
        estudiante_id: int,
        programa_id: int,
        valor_final: float,  # Cambiado de descuento a valor_final
        observaciones: Optional[str] = None,
        es_retroactiva: bool = False,
        fecha_retroactiva: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Procesa una inscripción completa con validaciones
        
        Args:
            estudiante_id: ID del estudiante
            programa_id: ID del programa
            valor_final: Valor final acordado para la inscripción
            observaciones: Observaciones adicionales (debe incluir justificación si hay descuento)
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
            programa = data['programa']
            valor_real = float(programa['costo_total'] or 0)
            
            # 2. Validar valor final
            if valor_final <= 0:
                return {
                    'success': False,
                    'message': 'El valor final debe ser mayor a 0'
                }
            
            if valor_final > valor_real:
                return {
                    'success': False,
                    'message': f'El valor final ({valor_final:.2f}) no puede ser mayor al valor real ({valor_real:.2f})'
                }
            
            # 3. Validar observaciones según descuento
            if observaciones:
                valido, error = InscripcionController.validar_observaciones_con_descuento(
                    valor_real, valor_final, observaciones
                )
                if not valido:
                    return {
                        'success': False,
                        'message': error
                    }
            
            # 4. Crear inscripción
            if es_retroactiva and fecha_retroactiva:
                resultado = InscripcionModel.crear_inscripcion_retroactiva(
                    estudiante_id=estudiante_id,
                    programa_id=programa_id,
                    fecha_inscripcion=fecha_retroactiva,
                    valor_final=valor_final,  # Cambiado
                    observaciones=observaciones
                )
            else:
                resultado = InscripcionModel.crear_inscripcion(
                    estudiante_id=estudiante_id,
                    programa_id=programa_id,
                    valor_final=valor_final,  # Cambiado
                    observaciones=observaciones,
                    fecha_inscripcion=None  # Usa fecha actual
                )
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error procesando inscripción: {e}")
            return {
                'success': False,
                'message': f'Error procesando inscripción: {str(e)}'
            }
    
    @staticmethod
    def actualizar_inscripcion(
        inscripcion_id: int,
        nuevo_estado: Optional[str] = None,
        nuevo_valor_final: Optional[float] = None,  # Cambiado
        nuevas_observaciones: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Actualiza una inscripción existente con validaciones
        
        Args:
            inscripcion_id: ID de la inscripción
            nuevo_estado: Nuevo estado
            nuevo_valor_final: Nuevo valor final
            nuevas_observaciones: Nuevas observaciones
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Si se está actualizando el valor final, validar
            if nuevo_valor_final is not None:
                # Obtener información actual de la inscripción
                from config.database import Database
                connection = Database.get_connection()
                if connection:
                    cursor = connection.cursor()
                    cursor.execute("""
                        SELECT p.costo_total, i.valor_final, i.observaciones
                        FROM inscripciones i
                        JOIN programas p ON i.programa_id = p.id
                        WHERE i.id = %s
                    """, (inscripcion_id,))
                    resultado = cursor.fetchone()
                    cursor.close()
                    Database.return_connection(connection)
                    
                    if resultado:
                        valor_real = float(resultado[0] or 0)
                        valor_actual = float(resultado[1] or 0)
                        obs_actuales = resultado[2] or ""
                        
                        # Validar valor final
                        if nuevo_valor_final <= 0:
                            return {
                                'success': False,
                                'message': 'El valor final debe ser mayor a 0'
                            }
                        
                        if nuevo_valor_final > valor_real:
                            return {
                                'success': False,
                                'message': f'El valor final ({nuevo_valor_final:.2f}) no puede ser mayor al valor real ({valor_real:.2f})'
                            }
                        
                        # Validar observaciones si se proporcionan nuevas
                        obs_a_validar = nuevas_observaciones if nuevas_observaciones is not None else obs_actuales
                        valido, error = InscripcionController.validar_observaciones_con_descuento(
                            valor_real, nuevo_valor_final, obs_a_validar
                        )
                        if not valido:
                            return {
                                'success': False,
                                'message': error
                            }
            
            # Realizar la actualización
            resultado = InscripcionModel.actualizar_inscripcion(
                inscripcion_id=inscripcion_id,
                nuevo_estado=nuevo_estado,
                nuevo_valor_final=nuevo_valor_final,  # Cambiado
                nuevas_observaciones=nuevas_observaciones
            )
            
            return resultado
            
        except Exception as e:
            logger.error(f"Error actualizando inscripción: {e}")
            return {
                'success': False,
                'message': f'Error actualizando inscripción: {str(e)}'
            }
    
    @staticmethod
    def obtener_inscripcion_para_edicion(inscripcion_id: int) -> Dict[str, Any]:
        """
        Obtiene los datos de una inscripción para edición, verificando si requiere
        completar justificación
        
        Args:
            inscripcion_id: ID de la inscripción
            
        Returns:
            Dict con datos de la inscripción y bandera de requiere_completar
        """
        try:
            from config.database import Database
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'message': 'Error de conexión'
                }
            
            cursor = connection.cursor()
            query = """
            SELECT 
                i.id,
                i.estudiante_id,
                i.programa_id,
                i.fecha_inscripcion,
                i.estado,
                i.valor_final,
                i.observaciones,
                p.costo_total as valor_real,
                p.codigo as programa_codigo,
                p.nombre as programa_nombre,
                CONCAT(e.nombres, ' ', e.apellido_paterno) as estudiante_nombre
            FROM inscripciones i
            JOIN programas p ON i.programa_id = p.id
            JOIN estudiantes e ON i.estudiante_id = e.id
            WHERE i.id = %s
            """
            
            cursor.execute(query, (inscripcion_id,))
            resultado = cursor.fetchone()
            
            if not resultado:
                cursor.close()
                Database.return_connection(connection)
                return {
                    'success': False,
                    'message': f'No se encontró la inscripción {inscripcion_id}'
                }
                
            if cursor.description is None:
                cursor.close()
                Database.return_connection(connection)
                return {
                    'success': False,
                    'message': 'Error al obtener datos de la inscripción'
                }
            
            column_names = [desc[0] for desc in cursor.description]
            inscripcion = dict(zip(column_names, resultado))
            
            cursor.close()
            Database.return_connection(connection)
            
            # Verificar si requiere completar justificación
            requiere_completar = False
            valor_real = float(inscripcion['valor_real'] or 0)
            valor_final = float(inscripcion['valor_final'] or valor_real)
            observaciones = inscripcion['observaciones'] or ""
            
            if valor_final < valor_real and abs(valor_final - valor_real) >= 0.01:
                # Hay descuento, verificar si la justificación está completa
                if "Justificación:" in observaciones:
                    partes = observaciones.split("Justificación:")
                    if len(partes) > 1 and partes[1].strip() == "":
                        requiere_completar = True
                else:
                    requiere_completar = True
            
            inscripcion['requiere_completar'] = requiere_completar
            inscripcion['valor_real'] = valor_real
            
            return {
                'success': True,
                'data': inscripcion
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo inscripción para edición: {e}")
            return {
                'success': False,
                'message': str(e)
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