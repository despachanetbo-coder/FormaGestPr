# Archivo: controller/transaccion_controller.py
"""
Controlador para gestionar transacciones de pago
Hereda de BaseController y utiliza TransaccionModel
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from controller.base_controller import BaseController
from model.transaccion_model import TransaccionModel
from config.constants import EstadoTransaccion, FormaPago

logger = logging.getLogger(__name__)

class TransaccionController(BaseController):
    """
    Controlador de transacciones
    Maneja la lógica de negocio y validaciones antes de llamar al modelo
    """
    
    def __init__(self, db_config: Dict[str, Any]):
        """Inicializar controlador con configuración de BD"""
        super().__init__(db_config)
        self.model = TransaccionModel
    
    def crear(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear una nueva transacción
        
        Args:
            datos: Diccionario con datos de la transacción
            
        Returns:
            Respuesta formateada con resultado
        """
        try:
            # Validar campos requeridos
            campos_requeridos = [
                'estudiante_id', 'fecha_pago', 'monto_total',
                'descuento_total', 'monto_final', 'forma_pago'
            ]
            
            validacion = self.validar_campos_requeridos(datos, campos_requeridos)
            if not validacion['success']:
                return self.formatear_respuesta(
                    success=False,
                    message='Error de validación',
                    error=validacion['message']
                )
            
            # Validar montos
            validacion_montos = self._validar_montos(datos)
            if not validacion_montos['success']:
                return self.formatear_respuesta(
                    success=False,
                    message='Error en montos',
                    error=validacion_montos['error']
                )
            
            # Validar forma de pago
            validacion_forma = self._validar_forma_pago(datos)
            if not validacion_forma['success']:
                return self.formatear_respuesta(
                    success=False,
                    message='Error en forma de pago',
                    error=validacion_forma['error']
                )
            
            # Validar que el número de comprobante no exista (si aplica)
            if datos.get('numero_comprobante'):
                if self._existe_comprobante(datos['numero_comprobante']):
                    return self.formatear_respuesta(
                        success=False,
                        message='Error de validación',
                        error='El número de comprobante ya existe'
                    )
            
            # Crear transacción
            resultado = self.model.crear(datos)
            
            if resultado['success']:
                # Obtener la transacción creada para devolver todos los datos
                transaccion = self.model.obtener_por_id(resultado['id'])
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacción creada exitosamente',
                    data=transaccion.get('data') if transaccion.get('success') else resultado
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al crear transacción',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error en crear transacción: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al crear transacción',
                error=str(e)
            )
    
    def actualizar(self, id_transaccion: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar una transacción existente
        
        Args:
            id_transaccion: ID de la transacción
            datos: Diccionario con datos a actualizar
            
        Returns:
            Respuesta formateada con resultado
        """
        try:
            # Verificar que la transacción existe
            existe = self.model.obtener_por_id(id_transaccion)
            if not existe.get('success'):
                return self.formatear_respuesta(
                    success=False,
                    message='Transacción no encontrada',
                    error=f'ID {id_transaccion} no existe'
                )
            
            # No permitir actualizar ciertos campos en ciertos estados
            validacion_estado = self._validar_actualizacion_por_estado(
                id_transaccion, 
                datos
            )
            if not validacion_estado['success']:
                return self.formatear_respuesta(
                    success=False,
                    message='Error de validación por estado',
                    error=validacion_estado['error']
                )
            
            # Validar montos si se están actualizando
            if any(k in datos for k in ['monto_total', 'descuento_total', 'monto_final']):
                # Obtener datos actuales para validación completa
                transaccion_actual = existe['data']
                datos_completos = {**transaccion_actual, **datos}
                
                validacion_montos = self._validar_montos(datos_completos)
                if not validacion_montos['success']:
                    return self.formatear_respuesta(
                        success=False,
                        message='Error en montos',
                        error=validacion_montos['error']
                    )
            
            # Validar número de comprobante si se actualiza
            if datos.get('numero_comprobante'):
                if self._existe_comprobante(datos['numero_comprobante'], id_transaccion):
                    return self.formatear_respuesta(
                        success=False,
                        message='Error de validación',
                        error='El número de comprobante ya existe'
                    )
            
            # Actualizar transacción
            resultado = self.model.actualizar(id_transaccion, datos)
            
            if resultado['success']:
                # Obtener transacción actualizada
                transaccion = self.model.obtener_por_id(id_transaccion)
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacción actualizada exitosamente',
                    data=transaccion.get('data')
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al actualizar transacción',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error en actualizar transacción {id_transaccion}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al actualizar transacción',
                error=str(e)
            )
    
    def obtener_por_id(self, id_transaccion: int) -> Dict[str, Any]:
        """
        Obtener una transacción por su ID
        
        Args:
            id_transaccion: ID de la transacción
            
        Returns:
            Respuesta formateada con datos de la transacción
        """
        try:
            resultado = self.model.obtener_por_id(id_transaccion)
            
            if resultado['success']:
                # Formatear datos para presentación
                datos_formateados = self._formatear_datos_para_presentacion(resultado['data'])
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacción encontrada',
                    data=datos_formateados
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Transacción no encontrada',
                    error=resultado.get('error', f'ID {id_transaccion} no existe')
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo transacción {id_transaccion}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al obtener transacción',
                error=str(e)
            )
    
    def obtener_por_numero(self, numero_transaccion: str) -> Dict[str, Any]:
        """
        Obtener una transacción por su número
        
        Args:
            numero_transaccion: Número de transacción
            
        Returns:
            Respuesta formateada con datos de la transacción
        """
        try:
            resultado = self.model.obtener_por_numero(numero_transaccion)
            
            if resultado['success']:
                datos_formateados = self._formatear_datos_para_presentacion(resultado['data'])
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacción encontrada',
                    data=datos_formateados
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Transacción no encontrada',
                    error=resultado.get('error', f'Número {numero_transaccion} no existe')
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo transacción {numero_transaccion}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al obtener transacción',
                error=str(e)
            )
    
    def listar(self, filtros: Optional[Dict[str, Any]] = None, 
                pagina: int = 1, por_pagina: int = 50) -> Dict[str, Any]:
        """
        Listar transacciones con paginación
        
        Args:
            filtros: Diccionario con filtros
            pagina: Número de página
            por_pagina: Cantidad por página
            
        Returns:
            Respuesta formateada con lista de transacciones
        """
        try:
            # Calcular offset
            offset = (pagina - 1) * por_pagina
            
            resultado = self.model.listar(
                filtros=filtros,
                limite=por_pagina,
                offset=offset
            )
            
            if resultado['success']:
                # Formatear cada transacción para presentación
                datos_formateados = []
                for transaccion in resultado['data']:
                    datos_formateados.append(
                        self._formatear_datos_para_presentacion(transaccion)
                    )
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacciones obtenidas exitosamente',
                    data={
                        'transacciones': datos_formateados,
                        'paginacion': {
                            'pagina_actual': pagina,
                            'por_pagina': por_pagina,
                            'total_registros': resultado.get('total', 0),
                            'total_paginas': resultado.get('total_paginas', 0)
                        }
                    }
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al listar transacciones',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error listando transacciones: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al listar transacciones',
                error=str(e)
            )
    
    def listar_por_estudiante(self, estudiante_id: int, 
                                pagina: int = 1, por_pagina: int = 50) -> Dict[str, Any]:
        """
        Listar transacciones de un estudiante
        
        Args:
            estudiante_id: ID del estudiante
            pagina: Número de página
            por_pagina: Cantidad por página
            
        Returns:
            Respuesta formateada con lista de transacciones
        """
        try:
            offset = (pagina - 1) * por_pagina
            
            resultado = self.model.listar_por_estudiante(
                estudiante_id=estudiante_id,
                limite=por_pagina,
                offset=offset
            )
            
            if resultado['success']:
                # Obtener resumen del estudiante
                resumen = self.model.obtener_resumen_por_estudiante(estudiante_id)
                
                datos_formateados = []
                for transaccion in resultado['data']:
                    datos_formateados.append(
                        self._formatear_datos_para_presentacion(transaccion)
                    )
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacciones del estudiante obtenidas',
                    data={
                        'estudiante_id': estudiante_id,
                        'transacciones': datos_formateados,
                        'resumen': resumen.get('data') if resumen.get('success') else {},
                        'paginacion': {
                            'pagina_actual': pagina,
                            'por_pagina': por_pagina,
                            'total_registros': resultado.get('total', 0),
                            'total_paginas': resultado.get('total_paginas', 0)
                        }
                    }
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al listar transacciones del estudiante',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error listando transacciones del estudiante {estudiante_id}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al listar transacciones',
                error=str(e)
            )
    
    def listar_por_programa(self, programa_id: int,
                            pagina: int = 1, por_pagina: int = 50) -> Dict[str, Any]:
        """
        Listar transacciones de un programa
        
        Args:
            programa_id: ID del programa
            pagina: Número de página
            por_pagina: Cantidad por página
            
        Returns:
            Respuesta formateada con lista de transacciones
        """
        try:
            offset = (pagina - 1) * por_pagina
            
            resultado = self.model.listar_por_programa(
                programa_id=programa_id,
                limite=por_pagina,
                offset=offset
            )
            
            if resultado['success']:
                datos_formateados = []
                for transaccion in resultado['data']:
                    datos_formateados.append(
                        self._formatear_datos_para_presentacion(transaccion)
                    )
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacciones del programa obtenidas',
                    data={
                        'programa_id': programa_id,
                        'transacciones': datos_formateados,
                        'paginacion': {
                            'pagina_actual': pagina,
                            'por_pagina': por_pagina,
                            'total_registros': resultado.get('total', 0),
                            'total_paginas': resultado.get('total_paginas', 0)
                        }
                    }
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al listar transacciones del programa',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error listando transacciones del programa {programa_id}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al listar transacciones',
                error=str(e)
            )
    
    def listar_por_fecha(self, fecha_inicio: str, fecha_fin: str,
                        pagina: int = 1, por_pagina: int = 100) -> Dict[str, Any]:
        """
        Listar transacciones en un rango de fechas
        
        Args:
            fecha_inicio: Fecha inicio (YYYY-MM-DD)
            fecha_fin: Fecha fin (YYYY-MM-DD)
            pagina: Número de página
            por_pagina: Cantidad por página
            
        Returns:
            Respuesta formateada con lista de transacciones
        """
        try:
            offset = (pagina - 1) * por_pagina
            
            resultado = self.model.listar_por_fecha(
                fecha_inicio=fecha_inicio,
                fecha_fin=fecha_fin,
                limite=por_pagina,
                offset=offset
            )
            
            if resultado['success']:
                datos_formateados = []
                for transaccion in resultado['data']:
                    datos_formateados.append(
                        self._formatear_datos_para_presentacion(transaccion)
                    )
                
                # Calcular totales
                total_monto = sum(t['monto_final'] for t in datos_formateados)
                
                return self.formatear_respuesta(
                    success=True,
                    message='Transacciones por fecha obtenidas',
                    data={
                        'fecha_inicio': fecha_inicio,
                        'fecha_fin': fecha_fin,
                        'transacciones': datos_formateados,
                        'resumen': {
                            'total_transacciones': resultado.get('total', 0),
                            'total_monto': total_monto
                        },
                        'paginacion': {
                            'pagina_actual': pagina,
                            'por_pagina': por_pagina,
                            'total_registros': resultado.get('total', 0)
                        }
                    }
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al listar transacciones por fecha',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error listando transacciones por fecha: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al listar transacciones',
                error=str(e)
            )
    
    def cambiar_estado(self, id_transaccion: int, nuevo_estado: str,
                        observaciones: Optional[str] = None) -> Dict[str, Any]:
        """
        Cambiar estado de una transacción
        
        Args:
            id_transaccion: ID de la transacción
            nuevo_estado: Nuevo estado
            observaciones: Observaciones adicionales
            
        Returns:
            Respuesta formateada con resultado
        """
        try:
            # Validar que el estado sea válido
            estados_validos = [e.value for e in EstadoTransaccion]
            if nuevo_estado not in estados_validos:
                return self.formatear_respuesta(
                    success=False,
                    message='Error de validación',
                    error=f'Estado inválido. Debe ser uno de: {", ".join(estados_validos)}'
                )
            
            # Verificar que la transacción existe
            existe = self.model.obtener_por_id(id_transaccion)
            if not existe.get('success'):
                return self.formatear_respuesta(
                    success=False,
                    message='Transacción no encontrada',
                    error=f'ID {id_transaccion} no existe'
                )
            
            # Validar transición de estado
            estado_actual = existe['data']['estado']
            validacion_transicion = self._validar_transicion_estado(
                estado_actual, 
                nuevo_estado
            )
            if not validacion_transicion['success']:
                return self.formatear_respuesta(
                    success=False,
                    message='Transición de estado no válida',
                    error=validacion_transicion['error']
                )
            
            # Cambiar estado
            resultado = self.model.cambiar_estado(
                id_transaccion, 
                nuevo_estado, 
                observaciones
            )
            
            if resultado['success']:
                transaccion = self.model.obtener_por_id(id_transaccion)
                
                return self.formatear_respuesta(
                    success=True,
                    message=f'Estado cambiado a {nuevo_estado} exitosamente',
                    data=transaccion.get('data')
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al cambiar estado',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error cambiando estado de transacción {id_transaccion}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al cambiar estado',
                error=str(e)
            )
    
    def confirmar(self, id_transaccion: int) -> Dict[str, Any]:
        """Confirmar una transacción"""
        return self.cambiar_estado(
            id_transaccion, 
            EstadoTransaccion.CONFIRMADO.value
        )
    
    def anular(self, id_transaccion: int, motivo: str) -> Dict[str, Any]:
        """Anular una transacción"""
        return self.cambiar_estado(
            id_transaccion,
            EstadoTransaccion.ANULADO.value,
            f"ANULADO: {motivo}"
        )
    
    def eliminar(self, id_transaccion: int) -> Dict[str, Any]:
        """
        Eliminar una transacción (solo si está en estado REGISTRADO)
        
        Args:
            id_transaccion: ID de la transacción
            
        Returns:
            Respuesta formateada con resultado
        """
        try:
            # Verificar que la transacción existe
            existe = self.model.obtener_por_id(id_transaccion)
            if not existe.get('success'):
                return self.formatear_respuesta(
                    success=False,
                    message='Transacción no encontrada',
                    error=f'ID {id_transaccion} no existe'
                )
            
            # Solo se puede eliminar si está en estado REGISTRADO o PENDIENTE
            estado_actual = existe['data']['estado']
            if estado_actual not in [
                EstadoTransaccion.REGISTRADO.value,
                EstadoTransaccion.PENDIENTE.value
            ]:
                return self.formatear_respuesta(
                    success=False,
                    message='No se puede eliminar la transacción',
                    error=f'La transacción está en estado {estado_actual}. Solo se pueden eliminar transacciones en estado REGISTRADO o PENDIENTE.'
                )
            
            resultado = self.model.eliminar(id_transaccion)
            
            if resultado['success']:
                return self.formatear_respuesta(
                    success=True,
                    message='Transacción eliminada exitosamente',
                    data={'id': id_transaccion}
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al eliminar transacción',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error eliminando transacción {id_transaccion}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al eliminar transacción',
                error=str(e)
            )
    
    def obtener_estadisticas(self, año: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtener estadísticas de transacciones
        
        Args:
            año: Año para filtrar
            
        Returns:
            Respuesta formateada con estadísticas
        """
        try:
            if not año:
                año = datetime.now().year
            
            resultado = self.model.obtener_estadisticas(año)
            
            if resultado['success']:
                return self.formatear_respuesta(
                    success=True,
                    message=f'Estadísticas del año {año} obtenidas',
                    data=resultado
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al obtener estadísticas',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al obtener estadísticas',
                error=str(e)
            )
    
    def obtener_pagos_del_dia(self) -> Dict[str, Any]:
        """
        Obtener resumen de pagos del día
        
        Returns:
            Respuesta formateada con pagos del día
        """
        try:
            resultado = self.model.obtener_pagos_del_dia()
            
            if resultado['success']:
                return self.formatear_respuesta(
                    success=True,
                    message='Pagos del día obtenidos',
                    data=resultado
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al obtener pagos del día',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo pagos del día: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al obtener pagos del día',
                error=str(e)
            )
    
    def buscar(self, termino: str, limite: int = 20) -> Dict[str, Any]:
        """
        Buscar transacciones
        
        Args:
            termino: Término de búsqueda
            limite: Límite de resultados
            
        Returns:
            Respuesta formateada con resultados
        """
        try:
            resultado = self.model.buscar(termino, limite)
            
            if resultado['success']:
                datos_formateados = []
                for transaccion in resultado['data']:
                    datos_formateados.append(
                        self._formatear_datos_para_presentacion(transaccion)
                    )
                
                return self.formatear_respuesta(
                    success=True,
                    message=f'Búsqueda completada: {resultado["total"]} resultados',
                    data={
                        'termino': termino,
                        'resultados': datos_formateados,
                        'total': resultado['total']
                    }
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error en búsqueda',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error en búsqueda: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error en búsqueda',
                error=str(e)
            )
    
    def obtener_resumen_estudiante(self, estudiante_id: int) -> Dict[str, Any]:
        """
        Obtener resumen de pagos de un estudiante
        
        Args:
            estudiante_id: ID del estudiante
            
        Returns:
            Respuesta formateada con resumen
        """
        try:
            resultado = self.model.obtener_resumen_por_estudiante(estudiante_id)
            
            if resultado['success']:
                return self.formatear_respuesta(
                    success=True,
                    message='Resumen del estudiante obtenido',
                    data={
                        'estudiante_id': estudiante_id,
                        'resumen': resultado.get('data', {})
                    }
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Error al obtener resumen del estudiante',
                    error=resultado.get('error', 'Error desconocido')
                )
                
        except Exception as e:
            logger.error(f"Error obteniendo resumen del estudiante {estudiante_id}: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error al obtener resumen',
                error=str(e)
            )
    
    def validar_datos(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validar datos de transacción sin guardar
        
        Args:
            datos: Datos a validar
            
        Returns:
            Respuesta con resultado de validación
        """
        try:
            resultado = self.model.validar_datos(datos)
            
            if resultado['success']:
                return self.formatear_respuesta(
                    success=True,
                    message='Datos válidos',
                    data=resultado.get('data')
                )
            else:
                return self.formatear_respuesta(
                    success=False,
                    message='Errores de validación',
                    error=resultado.get('errors', {})
                )
                
        except Exception as e:
            logger.error(f"Error en validación: {e}")
            return self.formatear_respuesta(
                success=False,
                message='Error en validación',
                error=str(e)
            )
    
    # Métodos privados de validación y utilidad
    
    def _validar_montos(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Validar consistencia de montos"""
        try:
            monto_total = float(datos.get('monto_total', 0))
            descuento_total = float(datos.get('descuento_total', 0))
            monto_final = float(datos.get('monto_final', 0))
            
            if monto_total < 0:
                return {'success': False, 'error': 'El monto total no puede ser negativo'}
            
            if descuento_total < 0:
                return {'success': False, 'error': 'El descuento no puede ser negativo'}
            
            if descuento_total > monto_total:
                return {'success': False, 'error': 'El descuento no puede ser mayor al monto total'}
            
            if monto_final < 0:
                return {'success': False, 'error': 'El monto final no puede ser negativo'}
            
            # Permitir pequeña diferencia por redondeo
            if abs(monto_final - (monto_total - descuento_total)) > 0.01:
                return {
                    'success': False, 
                    'error': f'El monto final ({monto_final}) debe ser igual a monto total ({monto_total}) menos descuento ({descuento_total}) = {monto_total - descuento_total}'
                }
            
            return {'success': True}
            
        except (ValueError, TypeError) as e:
            return {'success': False, 'error': f'Error en formato de montos: {str(e)}'}
    
    def _validar_forma_pago(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Validar datos según forma de pago"""
        forma_pago = datos.get('forma_pago')
        
        formas_validas = [f.value for f in FormaPago]
        if forma_pago not in formas_validas:
            return {
                'success': False,
                'error': f'Forma de pago inválida. Debe ser una de: {", ".join(formas_validas)}'
            }
        
        # Validaciones específicas por forma de pago
        if forma_pago == FormaPago.TRANSFERENCIA.value:
            if not datos.get('numero_comprobante'):
                return {
                    'success': False,
                    'error': 'El número de comprobante es obligatorio para transferencias'
                }
            if not datos.get('banco_origen'):
                return {
                    'success': False,
                    'error': 'El banco de origen es obligatorio para transferencias'
                }
        
        elif forma_pago == FormaPago.DEPOSITO.value:
            if not datos.get('numero_comprobante'):
                return {
                    'success': False,
                    'error': 'El número de comprobante es obligatorio para depósitos'
                }
        
        return {'success': True}
    
    def _validar_actualizacion_por_estado(self, id_transaccion: int, 
                                            datos_nuevos: Dict[str, Any]) -> Dict[str, Any]:
        """Validar qué campos se pueden actualizar según el estado"""
        # Obtener estado actual
        transaccion = self.model.obtener_por_id(id_transaccion)
        if not transaccion.get('success'):
            return {'success': False, 'error': 'Transacción no encontrada'}
        
        estado_actual = transaccion['data']['estado']
        
        # Estados en los que no se permite ninguna actualización
        if estado_actual in [EstadoTransaccion.ANULADO.value]:
            return {
                'success': False,
                'error': f'No se puede actualizar una transacción en estado {estado_actual}'
            }
        
        # Si está confirmada, solo permitir cambios en observaciones
        if estado_actual == EstadoTransaccion.CONFIRMADO.value:
            campos_permitidos = ['observaciones']
            campos_no_permitidos = [
                k for k in datos_nuevos.keys() 
                if k not in campos_permitidos
            ]
            
            if campos_no_permitidos:
                return {
                    'success': False,
                    'error': f'Una transacción confirmada solo permite actualizar observaciones. Campos no permitidos: {", ".join(campos_no_permitidos)}'
                }
        
        return {'success': True}
    
    def _validar_transicion_estado(self, estado_actual: str, 
                                    nuevo_estado: str) -> Dict[str, Any]:
        """Validar si la transición de estado es permitida"""
        
        # Definir transiciones permitidas
        transiciones_permitidas = {
            EstadoTransaccion.REGISTRADO.value: [
                EstadoTransaccion.CONFIRMADO.value,
                EstadoTransaccion.PENDIENTE.value,
                EstadoTransaccion.ANULADO.value
            ],
            EstadoTransaccion.PENDIENTE.value: [
                EstadoTransaccion.CONFIRMADO.value,
                EstadoTransaccion.REGISTRADO.value,
                EstadoTransaccion.ANULADO.value
            ],
            EstadoTransaccion.CONFIRMADO.value: [
                EstadoTransaccion.ANULADO.value  # Solo si se requiere
            ],
            EstadoTransaccion.ANULADO.value: [],  # No se puede cambiar desde anulado
            EstadoTransaccion.RECHAZADO.value: [
                EstadoTransaccion.REGISTRADO.value,
                EstadoTransaccion.PENDIENTE.value
            ]
        }
        
        if nuevo_estado not in transiciones_permitidas.get(estado_actual, []):
            return {
                'success': False,
                'error': f'No se puede cambiar de {estado_actual} a {nuevo_estado}'
            }
        
        return {'success': True}
    
    def _existe_comprobante(self, numero_comprobante: str, 
                            excluir_id: Optional[int] = None) -> bool:
        """Verificar si un número de comprobante ya existe"""
        return self.model.existe_numero_comprobante(
            numero_comprobante, 
            excluir_id
        )
    
    def _formatear_datos_para_presentacion(self, transaccion: Dict[str, Any]) -> Dict[str, Any]:
        """Formatear datos de transacción para presentación en UI"""
        datos = transaccion.copy()
        
        # Formatear montos
        if 'monto_total' in datos:
            datos['monto_total_formateado'] = f"Bs. {datos['monto_total']:,.2f}"
        if 'descuento_total' in datos:
            datos['descuento_total_formateado'] = f"Bs. {datos['descuento_total']:,.2f}"
        if 'monto_final' in datos:
            datos['monto_final_formateado'] = f"Bs. {datos['monto_final']:,.2f}"
        
        # Formatear fechas
        if 'fecha_pago' in datos and datos['fecha_pago']:
            try:
                if isinstance(datos['fecha_pago'], str):
                    fecha = datetime.strptime(datos['fecha_pago'], '%Y-%m-%d')
                    datos['fecha_pago_formateada'] = fecha.strftime('%d/%m/%Y')
            except:
                datos['fecha_pago_formateada'] = datos['fecha_pago']
        
        if 'fecha_registro' in datos and datos['fecha_registro']:
            try:
                if isinstance(datos['fecha_registro'], str):
                    fecha = datetime.strptime(datos['fecha_registro'], '%Y-%m-%d %H:%M:%S')
                    datos['fecha_registro_formateada'] = fecha.strftime('%d/%m/%Y %H:%M')
            except:
                datos['fecha_registro_formateada'] = datos['fecha_registro']
        
        # Formatear estado para mostrar
        if 'estado' in datos:
            estado_display = {
                'REGISTRADO': '📝 Registrado',
                'CONFIRMADO': '✅ Confirmado',
                'PENDIENTE': '⏳ Pendiente',
                'ANULADO': '❌ Anulado',
                'RECHAZADO': '⚠️ Rechazado'
            }
            datos['estado_display'] = estado_display.get(
                datos['estado'], 
                datos['estado']
            )
        
        # Formatear forma de pago
        if 'forma_pago' in datos:
            forma_display = {
                'EFECTIVO': '💰 Efectivo',
                'TRANSFERENCIA': '🏦 Transferencia',
                'TARJETA': '💳 Tarjeta',
                'DEPOSITO': '🏧 Depósito',
                'QR': '📱 Pago QR'
            }
            datos['forma_pago_display'] = forma_display.get(
                datos['forma_pago'],
                datos['forma_pago']
            )
        
        # Crear nombre completo del estudiante
        if 'estudiante_nombre' in datos and 'estudiante_apellido' in datos:
            datos['estudiante_completo'] = f"{datos['estudiante_nombre']} {datos['estudiante_apellido']}".strip()
        
        return datos