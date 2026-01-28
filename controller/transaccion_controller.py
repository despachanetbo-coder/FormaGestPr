"""
Controlador para gestionar transacciones financieras.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from decimal import Decimal

from model.transaccion_model import TransaccionModel
from model.estudiante_model import EstudianteModel
from model.programa_model import ProgramaModel
from model.concepto_pago_model import ConceptoPagoModel
from config.constants import EstadoTransaccion, FormaPago, TipoDocumento, Messages, AppConstants
from config.database import Database
from utils.file_manager import FileManager

logger = logging.getLogger(__name__)

class TransaccionController:
    """Controlador para operaciones con transacciones"""
    
    def __init__(self):
        """Inicializar controlador de transacciones"""
        self.transaccion_model = TransaccionModel()
        self.estudiante_model = EstudianteModel()
        self.programa_model = ProgramaModel()
        self.concepto_model = ConceptoPagoModel()
    
    def crear_transaccion(self, datos_transaccion, usuario_id):
        """Crear una nueva transacción."""
        try:
            from datetime import datetime
            
            # Determinar si es ingreso o egreso
            es_ingreso = datos_transaccion.get('monto_final', 0) >= 0
            # O puedes tener un campo específico en el formulario
            # es_ingreso = datos_transaccion.get('tipo_operacion', 'INGRESO') == 'INGRESO'
            
            # Generar número de transacción
            fecha_pago = datos_transaccion.get('fecha_pago')
            if isinstance(fecha_pago, str):
                from datetime import datetime
                fecha_pago = datetime.strptime(fecha_pago, "%Y-%m-%d").date()
            
            numero_transaccion = TransaccionModel.generar_numero_transaccion(
                fecha_pago=fecha_pago,
                estudiante_id=datos_transaccion.get('estudiante_id'),
                programa_id=datos_transaccion.get('programa_id'),
                inscripcion_id=datos_transaccion.get('inscripcion_id'),
                usuario_id=usuario_id,
                es_ingreso=es_ingreso
            )
            
            # Agregar número a los datos
            datos_transaccion['numero_transaccion'] = numero_transaccion
            
            # Llamar al modelo para crear
            resultado = TransaccionModel.crear_transaccion(datos_transaccion, usuario_id)
            
            if resultado:
                # También generar número de comprobante si aplica
                if datos_transaccion.get('forma_pago') not in ['EFECTIVO', 'OTROS']:
                    # Generar número de comprobante basado en la transacción
                    numero_comprobante = self._generar_numero_comprobante(
                        transaccion_id=resultado.get('id'),
                        fecha_pago=fecha_pago,
                        forma_pago=datos_transaccion.get('forma_pago')
                    )
                    
                    # Actualizar transacción con número de comprobante
                    if numero_comprobante:
                        TransaccionModel.actualizar_comprobante(
                            transaccion_id=resultado.get('id'),
                            numero_comprobante=numero_comprobante
                        )
                        resultado['numero_comprobante'] = numero_comprobante
                
                resultado['numero_transaccion'] = numero_transaccion
                return {'exito': True, 'transaccion_id': resultado.get('id'), 
                        'numero_transaccion': numero_transaccion, 
                        'mensaje': 'Transacción registrada exitosamente'}
            else:
                return {'exito': False, 'mensaje': 'Error al crear transacción'}
                
        except Exception as e:
            logger.error(f"Error en crear_transaccion: {e}")
            return {'exito': False, 'mensaje': str(e)}
    
    def _generar_numero_comprobante(self, transaccion_id, fecha_pago, forma_pago):
        """
        Generar número de comprobante único.
        
        Formato: TIPO-YYMM-XXXXXX
        Ejemplo: TRF-2512-000123 (Transferencia de dic/2025, número 123)
        
        Args:
            transaccion_id: ID de la transacción
            fecha_pago: Fecha del pago
            forma_pago: Forma de pago
            
        Returns:
            str: Número de comprobante generado
        """
        try:
            from config.database import Database
            
            # Mapear tipo de comprobante
            tipo_map = {
                'TRANSFERENCIA': 'TRF',
                'DEPOSITO': 'DEP',
                'TARJETA_CREDITO': 'TDC',
                'TARJETA_DEBITO': 'TDD',
                'CHEQUE': 'CHQ',
                'OTROS': 'OTR'
            }
            
            # Obtener prefijo
            prefijo = tipo_map.get(forma_pago.upper() if forma_pago else 'OTROS', 'OTR')
            
            # Formatear mes/año
            if isinstance(fecha_pago, str):
                fecha_obj = datetime.strptime(fecha_pago, "%Y-%m-%d")
            else:
                fecha_obj = fecha_pago
            
            periodo = fecha_obj.strftime("%y%m")  # Ej: 2512 para dic 2025
            
            # Obtener secuencia del mes
            db = Database()
            conn = db.get_connection()
            if not conn:
                logger.error("Error en la conexión con la base de datos")
                return
            
            with conn.cursor() as cursor:
                # Contar transacciones del mismo tipo en el mes
                query = """
                    SELECT COUNT(*) 
                    FROM transacciones 
                    WHERE forma_pago = %s 
                    AND EXTRACT(YEAR FROM fecha_pago) = %s 
                    AND EXTRACT(MONTH FROM fecha_pago) = %s
                """
                cursor.execute(query, (forma_pago, fecha_obj.year, fecha_obj.month))
                count = cursor.fetchone()[0]
                
                # Formatear secuencia (empezar desde 1)
                secuencia = str(count + 1).zfill(6)
                
                return f"{prefijo}-{periodo}-{secuencia}"
                
        except Exception as e:
            logger.error(f"Error generando número de comprobante: {e}")
            return None
    
    def _crear_transaccion_inscripcion(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear transacción para una inscripción específica

        Args:
            datos: Datos de la transacción

        Returns:
            Dict con resultado
        """
        connection = None  # Inicializar connection
        cursor = None      # Inicializar cursor

        try:
            # Obtener datos de la inscripción
            inscripcion_id = datos.get('inscripcion_id')
            if not inscripcion_id:
                return {'exito': False, 'mensaje': 'ID de inscripción requerido'}

            # Obtener estudiante y programa de la inscripción
            connection = Database.get_connection()
            if not connection:
                return {'exito': False, 'mensaje': 'Error al conectar con la base de datos'}

            cursor = connection.cursor()

            cursor.execute("""
                SELECT estudiante_id, programa_id 
                FROM inscripciones 
                WHERE id = %s
            """, (inscripcion_id,))

            inscripcion = cursor.fetchone()
            if not inscripcion:
                return {'exito': False, 'mensaje': 'Inscripción no encontrada'}

            estudiante_id, programa_id = inscripcion

            # Preparar detalles basados en el programa
            detalles = self._generar_detalles_inscripcion(programa_id, datos)

            # Actualizar datos con estudiante y programa
            datos['estudiante_id'] = estudiante_id
            datos['programa_id'] = programa_id
            datos['detalles'] = detalles

            # Crear transacción usando el modelo corregido
            return TransaccionModel.crear_transaccion_completa(
                estudiante_id=estudiante_id,
                programa_id=programa_id,
                fecha_pago=datos['fecha_pago'],
                monto_total=datos['monto_total'],
                descuento_total=datos.get('descuento_total', 0),
                forma_pago=datos['forma_pago'],
                estado=datos.get('estado', 'REGISTRADO'),
                numero_comprobante=datos.get('numero_comprobante'),
                banco_origen=datos.get('banco_origen'),
                cuenta_origen=datos.get('cuenta_origen'),
                observaciones=datos.get('observaciones'),
                registrado_por=datos.get('registrado_por'),
                detalles=detalles
            )

        except Exception as e:
            logger.error(f"Error creando transacción de inscripción: {e}")
            return {'exito': False, 'mensaje': f'Error: {str(e)}'}

        finally:
            # Cerrar cursor si existe
            if cursor:
                cursor.close()

            # Devolver conexión si existe
            if connection:
                Database.return_connection(connection)
    
    def _crear_transaccion_general(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear transacción general (no ligada a inscripción)
        
        Args:
            datos: Datos de la transacción
            
        Returns:
            Dict con resultado
        """
        try:
            # Preparar detalles
            detalles = datos.get('detalles', [])
            if not detalles:
                detalles = self._generar_detalles_generales(datos)
            
            # Crear transacción usando el modelo corregido
            return TransaccionModel.crear_transaccion_completa(
                estudiante_id=datos.get('estudiante_id'),
                programa_id=datos.get('programa_id'),
                fecha_pago=datos['fecha_pago'],
                monto_total=datos['monto_total'],
                descuento_total=datos.get('descuento_total', 0),
                forma_pago=datos['forma_pago'],
                estado=datos.get('estado', 'REGISTRADO'),
                numero_comprobante=datos.get('numero_comprobante'),
                banco_origen=datos.get('banco_origen'),
                cuenta_origen=datos.get('cuenta_origen'),
                observaciones=datos.get('observaciones'),
                registrado_por=datos.get('registrado_por'),
                detalles=detalles
            )
            
        except Exception as e:
            logger.error(f"Error creando transacción general: {e}")
            return {'exito': False, 'mensaje': f'Error: {str(e)}'}
    
    def _generar_detalles_inscripcion(self, programa_id: int, datos: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generar detalles de transacción para una inscripción

        Args:
            programa_id: ID del programa
            datos: Datos de la transacción

        Returns:
            Lista de detalles
        """
        try:
            detalles = []

            # Obtener información del programa
            resultado_programa = self.programa_model.obtener_programa(programa_id)
            if not resultado_programa.get('exito'):
                programa_nombre = "Programa no encontrado"
                costo_total = datos['monto_total']
            else:
                programa = resultado_programa['data']
                programa_nombre = programa.get('nombre', 'Programa')
                costo_total = programa.get('costo_total', datos['monto_total'])

            # Determinar tipo de pago
            tipo_pago = datos.get('tipo_pago', 'MENSUALIDAD')

            # Obtener concepto de pago
            concepto = self._obtener_concepto_por_tipo(tipo_pago)

            # Crear detalle principal - CORREGIDO: Verificar si concepto no es None
            detalle_principal = {
                'concepto_pago_id': concepto['id'] if concepto else 1,
                'descripcion': f"{concepto.get('nombre', 'Pago') if concepto else 'Pago'} - {programa_nombre}",
                'cantidad': 1,
                'precio_unitario': datos['monto_total'],
                'subtotal': datos['monto_total'],
                'orden': 0
            }

            detalles.append(detalle_principal)

            return detalles

        except Exception as e:
            logger.error(f"Error generando detalles de inscripción: {e}")
            # Retornar detalle básico
            return [{
                'concepto_pago_id': 1,
                'descripcion': f"Pago {datos.get('forma_pago', 'General')}",
                'cantidad': 1,
                'precio_unitario': datos['monto_total'],
                'subtotal': datos['monto_total'],
                'orden': 0
            }]
    
    def _generar_detalles_generales(self, datos: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generar detalles para transacción general
        
        Args:
            datos: Datos de la transacción
            
        Returns:
            Lista de detalles
        """
        try:
            # Obtener concepto apropiado
            concepto = self._obtener_concepto_general(datos)
            
            # Crear descripción
            descripcion = datos.get('descripcion_concepto', '')
            if not descripcion:
                if datos.get('estudiante_id'):
                    estudiante = self.estudiante_model.obtener_estudiante_por_id(datos['estudiante_id'])
                    if estudiante:
                        nombre = f"{estudiante['nombres']} {estudiante['apellido_paterno']}"
                        descripcion = f"Pago - {nombre}"
                else:
                    descripcion = "Pago general"
            
            return [{
                'concepto_pago_id': concepto['id'] if concepto else 1,
                'descripcion': descripcion,
                'cantidad': 1,
                'precio_unitario': datos['monto_total'],
                'subtotal': datos['monto_total'],
                'orden': 0
            }]
            
        except Exception as e:
            logger.error(f"Error generando detalles generales: {e}")
            return []
    
    def _obtener_concepto_por_tipo(self, tipo_pago: str) -> Optional[Dict[str, Any]]:
        """
        Obtener concepto de pago por tipo
        
        Args:
            tipo_pago: Tipo de pago (MATRICULA, INSCRIPCION, MENSUALIDAD, etc.)
            
        Returns:
            Dict con concepto o None
        """
        try:
            conceptos = self.concepto_model.obtener_conceptos_activos()
            for concepto in conceptos:
                if concepto['codigo'] == tipo_pago:
                    return concepto
            return None
        except Exception:
            return None
    
    def _obtener_concepto_general(self, datos: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Obtener concepto general apropiado
        
        Args:
            datos: Datos de la transacción
            
        Returns:
            Dict con concepto
        """
        try:
            conceptos = self.concepto_model.obtener_conceptos_activos()
            
            # Priorizar conceptos según contexto
            for concepto in conceptos:
                if datos.get('programa_id'):
                    if concepto['codigo'] == 'MENSUALIDAD' and concepto['aplica_programa']:
                        return concepto
                elif datos.get('estudiante_id'):
                    if concepto['aplica_estudiante']:
                        return concepto
                else:
                    if concepto['codigo'] == 'OTROS':
                        return concepto
            
            # Si no se encuentra, usar el primero
            return conceptos[0] if conceptos else None
            
        except Exception as e:
            logger.error(f"Error obteniendo concepto general: {e}")
            return None
    
    def _preparar_datos_transaccion(self, datos: Dict[str, Any], usuario_id: Optional[int]) -> Dict[str, Any]:
        """
        Preparar datos para la transacción
        
        Args:
            datos: Datos del formulario
            usuario_id: ID del usuario
            
        Returns:
            Dict con datos preparados
        """
        datos_preparados = datos.copy()
        
        # Asegurar tipos de datos
        if 'monto_total' in datos_preparados:
            datos_preparados['monto_total'] = float(datos_preparados['monto_total'])
        
        if 'descuento_total' in datos_preparados:
            datos_preparados['descuento_total'] = float(datos_preparados['descuento_total'])
        else:
            datos_preparados['descuento_total'] = 0.0
        
        # Agregar usuario si existe
        if usuario_id:
            datos_preparados['registrado_por'] = usuario_id
        
        # Agregar fecha si no existe
        if 'fecha_pago' not in datos_preparados:
            datos_preparados['fecha_pago'] = datetime.now().strftime('%Y-%m-%d')
        
        # Asegurar estado
        if 'estado' not in datos_preparados:
            datos_preparados['estado'] = 'REGISTRADO'
        
        return datos_preparados
    
    def _validar_datos_transaccion(self, datos: Dict[str, Any]) -> List[str]:
        """
        Validar datos de transacción
        
        Args:
            datos: Datos a validar
            
        Returns:
            Lista de errores
        """
        errores = []
        
        # Validar campos requeridos
        campos_requeridos = ['fecha_pago', 'forma_pago', 'monto_total']
        for campo in campos_requeridos:
            if campo not in datos or not datos[campo]:
                errores.append(f"El campo '{campo}' es requerido")
        
        # Validar montos
        monto_total = datos.get('monto_total', 0)
        try:
            monto_total = float(monto_total)
            if monto_total <= 0:
                errores.append("El monto total debe ser mayor a 0")
        except (ValueError, TypeError):
            errores.append("Monto total no válido")
        
        descuento_total = datos.get('descuento_total', 0)
        try:
            descuento_total = float(descuento_total)
            if descuento_total < 0:
                errores.append("El descuento no puede ser negativo")
            if descuento_total > monto_total:
                errores.append("El descuento no puede ser mayor al monto total")
        except (ValueError, TypeError):
            errores.append("Descuento no válido")
        
        # Validar forma de pago
        forma_pago = datos.get('forma_pago')
        if forma_pago:
            formas_validas = [fp.value for fp in FormaPago]
            if forma_pago not in formas_validas:
                errores.append(f"Forma de pago no válida. Debe ser una de: {', '.join(formas_validas)}")
            
            # Validar datos específicos por forma de pago
            if forma_pago in ['TRANSFERENCIA', 'DEPOSITO']:
                if not datos.get('banco_origen'):
                    errores.append("Banco origen es requerido para transferencias/depósitos")
                if not datos.get('cuenta_origen'):
                    errores.append("Cuenta origen es requerida para transferencias/depósitos")
        
        # Validar fecha
        fecha_pago = datos.get('fecha_pago')
        if fecha_pago:
            try:
                datetime.strptime(str(fecha_pago), '%Y-%m-%d')
            except ValueError:
                errores.append("Fecha de pago no válida. Formato: YYYY-MM-DD")
        
        return errores
    
    def _procesar_documentos_adjuntos(self, transaccion_id: int, documentos_temp: List[Dict], usuario_id: Optional[int]) -> None:
        """
        Procesar documentos adjuntos temporales
        
        Args:
            transaccion_id: ID de la transacción
            documentos_temp: Lista de documentos temporales
            usuario_id: ID del usuario
        """
        try:
            for doc_temp in documentos_temp:
                if 'ruta_original' in doc_temp:
                    resultado = self.transaccion_model.subir_documento_respaldo(
                        transaccion_id=transaccion_id,
                        tipo_documento=doc_temp.get('tipo_documento', 'COMPROBANTE'),
                        ruta_archivo=doc_temp['ruta_original'],
                        observaciones=doc_temp.get('observaciones'),
                        subido_por=usuario_id
                    )
                    
                    if not resultado.get('success'):
                        logger.error(f"Error subiendo documento: {resultado.get('message')}")
                        
        except Exception as e:
            logger.error(f"Error procesando documentos adjuntos: {e}")
    
    # ===== MÉTODOS DE CONSULTA =====
    
    def obtener_transaccion(self, transaccion_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener una transacción por ID
        
        Args:
            transaccion_id: ID de la transacción
            
        Returns:
            Dict con datos de la transacción o None
        """
        try:
            return self.transaccion_model.obtener_transaccion(transaccion_id)
        except Exception as e:
            logger.error(f"Error obteniendo transacción: {e}")
            return None
    
    def obtener_transacciones_filtradas(self, filtros: Optional[Dict] = None) -> List[Dict]:
        """
        Obtener transacciones con filtros
        
        Args:
            filtros: Diccionario con filtros
            
        Returns:
            Lista de transacciones
        """
        try:
            # Si el modelo tiene el método, usarlo
            if hasattr(self.transaccion_model, 'obtener_transacciones_filtradas'):
                return self.transaccion_model.obtener_transacciones_filtradas(filtros)
            
            # Implementación alternativa
            return self._obtener_transacciones_filtradas_alternativo(filtros) # <-- Línea 482
            
        except Exception as e:
            logger.error(f"Error obteniendo transacciones filtradas: {e}")
            return []
    
    def _obtener_transacciones_filtradas_alternativo(self, filtros: Optional[Dict] = None) -> List[Dict]:
        """Implementación alternativa para obtener transacciones filtradas"""
        connection = None
        cursor = None

        try:
            where_clauses = []
            params = []

            if filtros:
                # Filtrar por fecha
                if 'fecha_desde' in filtros:
                    where_clauses.append("t.fecha_pago >= %s")
                    params.append(filtros['fecha_desde'])

                if 'fecha_hasta' in filtros:
                    where_clauses.append("t.fecha_pago <= %s")
                    params.append(filtros['fecha_hasta'])

                # Filtrar por estado
                if 'estado' in filtros:
                    where_clauses.append("t.estado = %s")
                    params.append(filtros['estado'])

                # Filtrar por forma de pago
                if 'forma_pago' in filtros:
                    where_clauses.append("t.forma_pago = %s")
                    params.append(filtros['forma_pago'])

                # Filtrar por estudiante
                if 'estudiante_id' in filtros:
                    where_clauses.append("t.estudiante_id = %s")
                    params.append(filtros['estudiante_id'])

                # Filtrar por programa
                if 'programa_id' in filtros:
                    where_clauses.append("t.programa_id = %s")
                    params.append(filtros['programa_id'])

            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            query = f"""
                SELECT t.*, 
                    e.nombres || ' ' || e.apellido_paterno as estudiante_nombre,
                    p.nombre as programa_nombre,
                    u.nombre_completo as usuario_registro
                FROM transacciones t
                LEFT JOIN estudiantes e ON t.estudiante_id = e.id
                LEFT JOIN programas p ON t.programa_id = p.id
                LEFT JOIN usuarios u ON t.registrado_por = u.id
                WHERE {where_sql}
                ORDER BY t.fecha_pago DESC, t.id DESC
                LIMIT 100
            """

            connection = Database.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return []  # Este return ocurre antes de que cursor sea definido

            cursor = connection.cursor()
            cursor.execute(query, params)
            resultados = cursor.fetchall()

            transacciones = []
            column_names = [desc[0] for desc in cursor.description]

            for row in resultados:
                transaccion = dict(zip(column_names, row))
                # Formatear fechas
                for key in ['fecha_pago', 'fecha_registro']:
                    if key in transaccion and transaccion[key]:
                        if isinstance(transaccion[key], datetime):
                            transaccion[key] = transaccion[key].strftime('%Y-%m-%d')
                transacciones.append(transaccion)

            return transacciones

        except Exception as e:
            logger.error(f"Error en consulta alternativa: {e}")
            return []

        finally:
            # Cerrar cursor si existe - ESTA ES LA LÍNEA 576
            if cursor:
                cursor.close()

            # Devolver conexión si existe
            if connection:
                Database.return_connection(connection)
    
    def obtener_detalles_transaccion(self, transaccion_id: int) -> List[Dict]:
        """
        Obtener detalles de una transacción
        
        Args:
            transaccion_id: ID de la transacción
            
        Returns:
            Lista de detalles
        """
        try:
            return self.transaccion_model.obtener_detalles_transaccion(transaccion_id)
        except Exception as e:
            logger.error(f"Error obteniendo detalles: {e}")
            return []
    
    def obtener_documentos_transaccion(self, transaccion_id: int) -> List[Dict]:
        """
        Obtener documentos de una transacción
        
        Args:
            transaccion_id: ID de la transacción
            
        Returns:
            Lista de documentos
        """
        try:
            return self.transaccion_model.obtener_documentos_respaldo(transaccion_id)
        except Exception as e:
            logger.error(f"Error obteniendo documentos: {e}")
            return []
    
    # ===== MÉTODOS DE ACTUALIZACIÓN =====
    
    def anular_transaccion(self, transaccion_id: int, motivo: str, usuario_id: int) -> Dict[str, Any]:
        """
        Anular una transacción
        
        Args:
            transaccion_id: ID de la transacción
            motivo: Motivo de anulación
            usuario_id: ID del usuario que anula
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Verificar que la transacción existe
            transaccion = self.obtener_transaccion(transaccion_id)
            if not transaccion:
                return {
                    'exito': False,
                    'mensaje': 'Transacción no encontrada'
                }
            
            # Verificar que no esté ya anulada
            if transaccion['estado'] == EstadoTransaccion.ANULADO.value:
                return {
                    'exito': False,
                    'mensaje': 'La transacción ya está anulada'
                }
            
            # Anular usando el modelo
            return self.transaccion_model.anular_transaccion(transaccion_id, motivo, usuario_id)
            
        except Exception as e:
            logger.error(f"Error anulando transacción: {e}")
            return {
                'exito': False,
                'mensaje': f'Error al anular transacción: {str(e)}'
            }
    
    def actualizar_estado_transaccion(self, transaccion_id: int, nuevo_estado: str) -> Dict[str, Any]:
        """
        Actualizar estado de una transacción

        Args:
            transaccion_id: ID de la transacción
            nuevo_estado: Nuevo estado

        Returns:
            Dict con resultado
        """
        connection = None
        cursor = None  # Inicializar explícitamente

        try:
            connection = Database.get_connection()
            if not connection:
                return {
                    'exito': False,
                    'mensaje': 'Error al conectar con la base de datos'
                }

            cursor = connection.cursor()

            cursor.execute("""
                UPDATE transacciones
                SET estado = %s
                WHERE id = %s
                RETURNING id
            """, (nuevo_estado, transaccion_id))

            filas_afectadas = cursor.rowcount
            connection.commit()

            return {
                'exito': filas_afectadas > 0,
                'mensaje': 'Estado actualizado' if filas_afectadas > 0 else 'Transacción no encontrada',
                'filas_afectadas': filas_afectadas
            }

        except Exception as e:
            logger.error(f"Error actualizando estado: {e}")
            return {
                'exito': False,
                'mensaje': f'Error al actualizar estado: {str(e)}'
            }
        finally:
            # Asegurar que cursor se cierre si existe
            if cursor is not None:  # Usar 'is not None' en lugar de solo 'if cursor'
                cursor.close()

            # Devolver conexión si existe
            if connection is not None:
                Database.return_connection(connection)
    
    # ===== MÉTODOS DE REPORTES =====
    
    def obtener_resumen_diario(self, fecha: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtener resumen financiero diario

        Args:
            fecha: Fecha en formato YYYY-MM-DD (None para hoy)

        Returns:
            Dict con resumen
        """
        try:
            if not fecha:
                fecha = datetime.now().strftime('%Y-%m-%d')

            query = """
                SELECT 
                    COUNT(*) as total_transacciones,
                    SUM(monto_final) as total_ingresos,
                    COUNT(CASE WHEN forma_pago = 'EFECTIVO' THEN 1 END) as efectivo_count,
                    SUM(CASE WHEN forma_pago = 'EFECTIVO' THEN monto_final ELSE 0 END) as efectivo_total,
                    COUNT(CASE WHEN forma_pago = 'TRANSFERENCIA' THEN 1 END) as transferencia_count,
                    SUM(CASE WHEN forma_pago = 'TRANSFERENCIA' THEN monto_final ELSE 0 END) as transferencia_total,
                    COUNT(CASE WHEN forma_pago = 'TARJETA' THEN 1 END) as tarjeta_count,
                    SUM(CASE WHEN forma_pago = 'TARJETA' THEN monto_final ELSE 0 END) as tarjeta_total,
                    COUNT(CASE WHEN forma_pago = 'DEPOSITO' THEN 1 END) as deposito_count,
                    SUM(CASE WHEN forma_pago = 'DEPOSITO' THEN monto_final ELSE 0 END) as deposito_total
                FROM transacciones
                WHERE fecha_pago = %s AND estado = 'CONFIRMADO'
            """

            # Obtener conexión
            connection = Database.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {
                    'total_transacciones': 0,
                    'total_ingresos': 0
                }

            # Crear cursor
            cursor = connection.cursor()

            try:
                cursor.execute(query, (fecha,))
                result = cursor.fetchone()

                if result:
                    column_names = [
                        'total_transacciones', 'total_ingresos',
                        'efectivo_count', 'efectivo_total',
                        'transferencia_count', 'transferencia_total',
                        'tarjeta_count', 'tarjeta_total',
                        'deposito_count', 'deposito_total'
                    ]
                    return dict(zip(column_names, result))

                return {
                    'total_transacciones': 0,
                    'total_ingresos': 0
                }

            finally:
                # Cerrar cursor
                cursor.close()
                # Devolver conexión al pool
                Database.return_connection(connection)

        except Exception as e:
            logger.error(f"Error obteniendo resumen diario: {e}")
            return {
                'total_transacciones': 0,
                'total_ingresos': 0
            }
    
    def obtener_resumen_mensual(self, año: int, mes: int) -> Dict[str, Any]:
        """
        Obtener resumen financiero mensual
        
        Args:
            año: Año
            mes: Mes (1-12)
            
        Returns:
            Dict con resumen
        """
        try:
            fecha_inicio = f"{año:04d}-{mes:02d}-01"
            
            if mes == 12:
                fecha_fin = f"{año+1:04d}-01-01"
            else:
                fecha_fin = f"{año:04d}-{mes+1:02d}-01"
            
            query = """
                SELECT 
                    fecha_pago,
                    COUNT(*) as transacciones_dia,
                    SUM(monto_final) as ingresos_dia
                FROM transacciones
                WHERE fecha_pago >= %s 
                    AND fecha_pago < %s 
                    AND estado = 'CONFIRMADO'
                GROUP BY fecha_pago
                ORDER BY fecha_pago
            """
            
            # Obtener conexión
            connection = Database.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {}
            
            cursor = None  # Definir explícitamente
            try:
                cursor = connection.cursor()
                cursor.execute(query, (fecha_inicio, fecha_fin))
                resultados = cursor.fetchall()
                
                resumen = {
                    'año': año,
                    'mes': mes,
                    'total_transacciones': 0,
                    'total_ingresos': 0,
                    'detalle_dias': []
                }
                
                for row in resultados:
                    fecha, transacciones_dia, ingresos_dia = row
                    resumen['total_transacciones'] += transacciones_dia
                    resumen['total_ingresos'] += ingresos_dia
                    resumen['detalle_dias'].append({
                        'fecha': fecha.strftime('%Y-%m-%d') if isinstance(fecha, datetime) else fecha,
                        'transacciones': transacciones_dia,
                        'ingresos': float(ingresos_dia)
                    })
                
                return resumen
                
            finally:
                # Cerrar cursor si fue creado
                if cursor is not None:
                    cursor.close()
                # Devolver conexión siempre
                Database.return_connection(connection)
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen mensual: {e}")
            return {}
    
    # ===== MÉTODOS DE UTILIDAD =====
    
    def obtener_conceptos_pago(self) -> List[Dict[str, Any]]:
        """
        Obtener conceptos de pago activos
        
        Returns:
            Lista de conceptos
        """
        try:
            return self.concepto_model.obtener_conceptos_activos()
        except Exception as e:
            logger.error(f"Error obteniendo conceptos: {e}")
            return []
    
    def obtener_ultimo_numero_transaccion(self) -> Optional[str]:
        """
        Obtener el último número de transacción generado
        
        Returns:
            Último número de transacción o None
        """
        try:
            query = """
                SELECT numero_transaccion
                FROM transacciones
                ORDER BY fecha_registro DESC, id DESC
                LIMIT 1
            """
            
            result = Database.execute_query(query, fetch_one=True)
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"Error obteniendo último número: {e}")
            return None
    
    def generar_numero_transaccion_sugerido(self) -> str:
        """
        Generar número de transacción sugerido
        
        Returns:
            Número de transacción sugerido
        """
        try:
            ultimo_numero = self.obtener_ultimo_numero_transaccion()
            
            if not ultimo_numero:
                return "T-00000001"
            
            # Extraer número consecutivo
            if ultimo_numero.startswith('T-'):
                try:
                    partes = ultimo_numero.split('-')
                    if len(partes) >= 2:
                        ultimo_consecutivo = int(partes[-1])
                        nuevo_consecutivo = ultimo_consecutivo + 1
                        return f"T-{nuevo_consecutivo:08d}"
                except (ValueError, IndexError):
                    pass
            
            # Si no se puede parsear, usar timestamp
            timestamp = int(datetime.now().timestamp())
            return f"T-{timestamp}"
            
        except Exception as e:
            logger.error(f"Error generando número sugerido: {e}")
            timestamp = int(datetime.now().timestamp())
            return f"T-{timestamp}"
    
    def obtener_estadisticas_generales(self) -> Dict[str, Any]:
        """
        Obtener estadísticas generales de transacciones
        
        Returns:
            Dict con estadísticas
        """
        try:
            query = """
                SELECT 
                    COUNT(*) as total_transacciones,
                    SUM(monto_final) as total_ingresos,
                    AVG(monto_final) as promedio_transaccion,
                    COUNT(CASE WHEN estado = 'CONFIRMADO' THEN 1 END) as confirmadas,
                    COUNT(CASE WHEN estado = 'REGISTRADO' THEN 1 END) as registradas,
                    COUNT(CASE WHEN estado = 'ANULADO' THEN 1 END) as anuladas
                FROM transacciones
            """
            
            # SOLUCIÓN SIMPLE: Sin finally complicado
            connection = Database.get_connection()
            if not connection:
                logger.error("No se pudo obtener conexión a la base de datos")
                return {}
            
            # Crear cursor (está garantizado que connection no es None)
            cursor = connection.cursor()
            
            try:
                cursor.execute(query)
                result = cursor.fetchone()
                
                estadisticas = {}
                if result:
                    column_names = [
                        'total_transacciones', 'total_ingresos', 'promedio_transaccion',
                        'confirmadas', 'registradas', 'anuladas'
                    ]
                    estadisticas = dict(zip(column_names, result))
                    
                    # Calcular porcentajes
                    total = estadisticas.get('total_transacciones', 0)
                    if total > 0:
                        for estado in ['confirmadas', 'registradas', 'anuladas']:
                            estadisticas[f'porcentaje_{estado}'] = (estadisticas.get(estado, 0) / total) * 100
                
                return estadisticas
                
            except Exception as e:
                logger.error(f"Error en consulta de estadísticas: {e}")
                return {}
            finally:
                # cursor SIEMPRE está definido aquí porque se creó antes del try interno
                cursor.close()
                Database.return_connection(connection)
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    