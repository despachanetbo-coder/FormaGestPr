# Archivo: controller/estudiante_controller.py
"""
Controlador para gestión de estudiantes
Maneja la lógica de negocio entre la vista y el modelo
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date

from .base_controller import BaseController
from model.estudiante_model import EstudianteModel
from utils.validators import Validators

logger = logging.getLogger(__name__)


class EstudianteController(BaseController):
    """Controlador para operaciones de estudiantes"""
    
    @staticmethod
    def crear_estudiante(datos: Dict[str, Any]) -> Dict[str, Any]:
        """Crear un nuevo estudiante"""
        try:
            logger.info("=" * 50)
            logger.info("DEBUG - Iniciando creación de estudiante")
            logger.info(f"DEBUG - Datos recibidos: {datos}")
            
            # 1. Validar datos
            resultado_validacion = EstudianteController.validar_datos_estudiante(datos)
            
            if not resultado_validacion['valido']:
                return {
                    'success': False,
                    'message': f"Error de validación: {', '.join(resultado_validacion['errores'])}"
                }
            
            datos_limpios = resultado_validacion['datos_limpios']
            
            logger.info(f"DEBUG - Datos limpios: {datos_limpios}")
            logger.info(f"DEBUG - ¿Tiene fotografia_url?: {'fotografia_url' in datos_limpios}")
            
            # 2. Verificar CI único
            ci_numero = datos_limpios['ci_numero']
            if EstudianteModel.verificar_ci_existente(ci_numero):
                return {
                    'success': False,
                    'message': f"El CI {ci_numero} ya está registrado"
                }
            
            # 3. Verificar email único (si se proporcionó)
            email = datos_limpios.get('email')
            if email:
                if EstudianteModel.verificar_email_existente(email):
                    return {
                        'success': False,
                        'message': f"El email {email} ya está registrado"
                    }
            
            # 4. Crear estudiante en la base de datos
            logger.info("DEBUG - Llamando a EstudianteModel.crear_estudiante")
            resultado_modelo = EstudianteModel.crear_estudiante(datos_limpios)
            
            if resultado_modelo['exito']:
                estudiante_id = resultado_modelo['nuevo_id']
                logger.info(f"✅ Estudiante creado exitosamente - ID: {estudiante_id}")
                
                # Obtener datos completos del estudiante creado
                estudiante = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
                
                if estudiante:
                    logger.info(f"DEBUG - Estudiante obtenido de BD: {estudiante.get('nombres')} {estudiante.get('apellido_paterno')}")
                    logger.info(f"DEBUG - Ruta de foto en BD: {estudiante.get('fotografia_url')}")
                else:
                    logger.warning(f"DEBUG - No se pudo obtener estudiante {estudiante_id} después de crearlo")
                
                return {
                    'success': True,
                    'message': resultado_modelo['mensaje'],
                    'data': {
                        'id': estudiante_id,
                        'ci_numero': datos_limpios.get('ci_numero'),
                        'nombres': datos_limpios.get('nombres'),
                        'apellido_paterno': datos_limpios.get('apellido_paterno'),
                        'apellido_materno': datos_limpios.get('apellido_materno'),
                        'email': datos_limpios.get('email'),
                        'estudiante_id': estudiante_id,
                        'fotografia_url': datos_limpios.get('fotografia_url')
                    }
                }
            else:
                logger.error(f"❌ Error en modelo: {resultado_modelo.get('mensaje')}")
                return {
                    'success': False,
                    'message': resultado_modelo.get('mensaje', 'Error desconocido en el modelo')
                }
                
        except Exception as e:
            logger.error(f"❌ Error inesperado en crear_estudiante: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'message': f"Error inesperado: {str(e)}"
            }
    
    @staticmethod
    def actualizar_estudiante(estudiante_id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """Actualizar un estudiante existente"""
        try:
            logger.info(f"DEBUG - Actualizando estudiante ID: {estudiante_id}")
            logger.info(f"DEBUG - Datos para actualizar: {datos}")
            
            # 1. Validar datos
            resultado_validacion = EstudianteController.validar_datos_estudiante(datos, es_actualizacion=True)
            
            if not resultado_validacion['valido']:
                return {
                    'success': False,
                    'message': f"Error de validación: {', '.join(resultado_validacion['errores'])}"
                }
                
            datos_limpios = resultado_validacion['datos_limpios']
            
            # 2. Verificar que el estudiante existe
            estudiante_actual = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
            if not estudiante_actual:
                return {
                    'success': False,
                    'message': f'Estudiante con ID {estudiante_id} no encontrado'
                }
                
            # 3. Verificar CI único si cambió
            if 'ci_numero' in datos_limpios and datos_limpios['ci_numero']:
                ci_actual = estudiante_actual.get('ci_numero')
                ci_nuevo = datos_limpios['ci_numero']
                
                # Extraer valor si es diccionario
                if isinstance(ci_nuevo, dict):
                    ci_nuevo = ci_nuevo.get('value') if isinstance(ci_nuevo.get('value'), str) else str(ci_nuevo)
                    
                # Asegurar que ci_nuevo no sea None o vacío
                if ci_nuevo and str(ci_nuevo).strip():
                    if ci_nuevo != ci_actual:
                        # Ahora ci_nuevo está garantizado como string no vacío
                        if EstudianteModel.verificar_ci_existente(str(ci_nuevo).strip(), excluir_id=estudiante_id): # <-- Línea 142 corregida
                            return {
                                'success': False,
                                'message': f"El CI {ci_nuevo} ya está registrado por otro estudiante"
                            }
                
            # 4. Verificar email único si cambió
            if 'email' in datos_limpios and datos_limpios['email']:
                email_actual = estudiante_actual.get('email', '')
                email_nuevo = datos_limpios['email']
                
                # Extraer valor si es diccionario
                if isinstance(email_nuevo, dict):
                    email_nuevo = email_nuevo.get('value') if isinstance(email_nuevo.get('value'), str) else str(email_nuevo)
                
                # Asegurar que email_nuevo no sea None o vacío
                if email_nuevo and str(email_nuevo).strip():
                    if email_nuevo != email_actual:
                        # Ahora email_nuevo está garantizado como string no vacío
                        if EstudianteModel.verificar_email_existente(str(email_nuevo).strip(), excluir_id=estudiante_id): # <-- Línea 158 corregida
                            return {
                                'success': False,
                                'message': f"El email {email_nuevo} ya está registrado por otro estudiante"
                            }
            
            # 5. Actualizar en la base de datos
            # Ahora pasamos directamente el diccionario al modelo
            resultado_modelo = EstudianteModel.actualizar_estudiante(estudiante_id, datos_limpios)
            
            if resultado_modelo.get('success', False):
                return {
                    'success': True,
                    'message': resultado_modelo.get('message', 'Estudiante actualizado exitosamente'),
                    'data': resultado_modelo.get('data', {'estudiante_id': estudiante_id})
                }
            else:
                return {
                    'success': False,
                    'message': resultado_modelo.get('message', 'Error al actualizar estudiante')
                }
        
        except Exception as e:
            logger.error(f"Error actualizando estudiante {estudiante_id}: {e}")
            return {
                'success': False,
                'message': f'Error al actualizar estudiante: {str(e)}'
            }
    
    @staticmethod
    def eliminar_estudiante(estudiante_id: int) -> Dict[str, Any]:
        """Eliminar (desactivar) un estudiante"""
        try:
            # Verificar que el estudiante existe
            estudiante = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
            if not estudiante:
                return {
                    'success': False,
                    'message': f'Estudiante con ID {estudiante_id} no encontrado'
                }
            
            # Actualizar estado a inactivo
            resultado = EstudianteModel.actualizar_estudiante(estudiante_id, {'activo': False})
            
            if resultado['success']:
                return {
                    'success': True,
                    'message': f'Estudiante {estudiante_id} eliminado (desactivado) exitosamente',
                    'data': {'estudiante_id': estudiante_id}
                }
            else:
                return {
                    'success': False,
                    'message': resultado['message']
                }
                
        except Exception as e:
            logger.error(f"Error eliminando estudiante {estudiante_id}: {e}")
            return {
                'success': False,
                'message': f'Error al eliminar estudiante: {str(e)}'
            }
    
    @staticmethod
    def obtener_estudiante(estudiante_id: int) -> Dict[str, Any]:
        """Obtener un estudiante por ID"""
        try:
            estudiante = EstudianteModel.obtener_estudiante_por_id(estudiante_id)
            
            if estudiante:
                return {
                    'success': True,
                    'data': estudiante
                }
            else:
                return {
                    'success': False,
                    'message': f'Estudiante con ID {estudiante_id} no encontrado'
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estudiante {estudiante_id}: {e}")
            return {
                'success': False,
                'message': f'Error al obtener estudiante: {str(e)}'
            }
    
    @staticmethod
    def buscar_estudiantes(filtros: Optional[Dict[str, Any]] = None, 
        pagina: int = 1, 
        por_pagina: int = 10) -> Dict[str, Any]:
        """Buscar estudiantes con filtros"""
        try:
            # Extraer parámetros específicos de los filtros
            ci_numero = None
            ci_expedicion = None
            nombre = None
            
            if filtros:
                ci_numero = filtros.get('ci_numero')
                ci_expedicion = filtros.get('ci_expedicion')
                nombre = filtros.get('nombre')
            
            # Calcular offset para paginación
            offset = (pagina - 1) * por_pagina
            
            # Llamar al modelo con los parámetros correctos
            estudiantes = EstudianteModel.buscar_estudiantes(
                ci_numero=ci_numero,
                ci_expedicion=ci_expedicion,
                nombre=nombre,
                limit=por_pagina,
                offset=offset
            )
            
            # Para obtener el total, necesitamos otra consulta sin limit/offset
            # (asumiendo que existe un método obtener_total_estudiantes)
            try:
                total = EstudianteModel.obtener_total_estudiantes(filtros)
            except:
                # Si no existe el método, estimar basado en resultados
                total = len(estudiantes) + offset
            
            total_paginas = (total + por_pagina - 1) // por_pagina if por_pagina > 0 else 0
            
            return {
                'success': True,
                'message': f'Se encontraron {len(estudiantes)} estudiantes',
                'data': estudiantes,
                'metadata': {
                    'total': total,
                    'pagina': pagina,
                    'por_pagina': por_pagina,
                    'total_paginas': total_paginas
                }
            }
            
        except Exception as e:
            logger.error(f"Error buscando estudiantes: {e}")
            return {
                'success': False,
                'message': f'Error buscando estudiantes: {str(e)}',
                'data': [],
                'metadata': {
                    'total': 0,
                    'pagina': pagina,
                    'por_pagina': por_pagina,
                    'total_paginas': 0
                }
            }
    
    @staticmethod
    def validar_datos_estudiante(datos: Dict[str, Any], es_actualizacion: bool = False) -> Dict[str, Any]:
        """
        Validar datos del estudiante
        
        Args:
            datos: Datos del estudiante
            es_actualizacion: Si es una actualización, algunos campos pueden ser opcionales
        
        Returns:
            dict: Resultado de validación
        """
        errores = []
        datos_limpios = {}
        
        # Validar CI Número
        if not es_actualizacion or 'ci_numero' in datos:
            ci_numero = str(datos.get('ci_numero', '')).strip()
            if not ci_numero:
                errores.append("El CI Número es obligatorio")
            elif not ci_numero.isdigit():
                errores.append("El CI debe contener solo números")
            elif len(ci_numero) < 5 or len(ci_numero) > 15:
                errores.append("El CI debe tener entre 5 y 15 dígitos")
            else:
                datos_limpios['ci_numero'] = ci_numero
        
        # Validar CI Expedición
        if not es_actualizacion or 'ci_expedicion' in datos:
            ci_expedicion = datos.get('ci_expedicion', '').strip().upper()
            expediciones_validas = ["LP", "CB", "SC", "OR", "PT", "TJ", "PA", "BE", "CH"]
            if not ci_expedicion:
                errores.append("La expedición del CI es obligatoria")
            elif ci_expedicion not in expediciones_validas:
                errores.append(f"Expedición inválida. Válidas: {', '.join(expediciones_validas)}")
            else:
                datos_limpios['ci_expedicion'] = ci_expedicion
        
        # Validar Nombres
        if not es_actualizacion or 'nombres' in datos:
            nombres = datos.get('nombres', '').strip()
            if not nombres:
                errores.append("Los nombres son obligatorios")
            elif len(nombres) < 2:
                errores.append("Los nombres deben tener al menos 2 caracteres")
            else:
                datos_limpios['nombres'] = nombres
        
        # Validar Apellido Paterno
        if not es_actualizacion or 'apellido_paterno' in datos:
            apellido_paterno = datos.get('apellido_paterno', '').strip()
            if not apellido_paterno:
                errores.append("El apellido paterno es obligatorio")
            elif len(apellido_paterno) < 2:
                errores.append("El apellido paterno debe tener al menos 2 caracteres")
            else:
                datos_limpios['apellido_paterno'] = apellido_paterno
        
        # Validar Apellido Materno (opcional)
        if 'apellido_materno' in datos:
            apellido_materno = datos.get('apellido_materno', '').strip()
            if apellido_materno:
                datos_limpios['apellido_materno'] = apellido_materno
        
        # Validar Fecha de Nacimiento (opcional)
        if 'fecha_nacimiento' in datos:
            fecha_nacimiento = datos.get('fecha_nacimiento')
            if fecha_nacimiento:
                # Convertir a date si es string
                if isinstance(fecha_nacimiento, str):
                    try:
                        fecha_nacimiento = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                    except ValueError:
                        errores.append("Formato de fecha inválido. Use YYYY-MM-DD")
                
                if isinstance(fecha_nacimiento, date):
                    # Verificar edad mínima (16 años)
                    hoy = date.today()
                    edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                    
                    if edad < 16:
                        errores.append("El estudiante debe tener al menos 16 años")
                    elif edad > 120:
                        errores.append("La edad no es válida")
                    else:
                        datos_limpios['fecha_nacimiento'] = fecha_nacimiento
        
        # Validar Teléfono (opcional)
        if 'telefono' in datos:
            telefono = datos.get('telefono', '').strip()
            if telefono:
                if len(telefono) > 20:
                    errores.append("El teléfono no puede exceder 20 caracteres")
                else:
                    datos_limpios['telefono'] = telefono
        
        # Validar Email (opcional)
        if 'email' in datos:
            email = datos.get('email', '').strip()
            if email:
                valido, mensaje = Validators.validar_email(email)
                if not valido:
                    errores.append(f"Email: {mensaje}")
                else:
                    datos_limpios['email'] = email
        
        # Validar Dirección (opcional)
        if 'direccion' in datos:
            direccion = datos.get('direccion', '').strip()
            if direccion:
                if len(direccion) > 500:
                    errores.append("La dirección no puede exceder 500 caracteres")
                else:
                    datos_limpios['direccion'] = direccion
        
        # Validar Profesión (opcional)
        if 'profesion' in datos:
            profesion = datos.get('profesion', '').strip()
            if profesion:
                if len(profesion) > 200:
                    errores.append("La profesión no puede exceder 200 caracteres")
                else:
                    datos_limpios['profesion'] = profesion
        
        # Validar Universidad (opcional)
        if 'universidad' in datos:
            universidad = datos.get('universidad', '').strip()
            if universidad:
                if len(universidad) > 200:
                    errores.append("La universidad no puede exceder 200 caracteres")
                else:
                    datos_limpios['universidad'] = universidad
        
        # Validar Activo
        if 'activo' in datos:
            activo = datos.get('activo')
            if isinstance(activo, bool):
                datos_limpios['activo'] = activo
            elif activo in [1, '1', 'true', 'True', 'TRUE']:
                datos_limpios['activo'] = True
            elif activo in [0, '0', 'false', 'False', 'FALSE']:
                datos_limpios['activo'] = False
            else:
                # Valor por defecto para creación
                if not es_actualizacion:
                    datos_limpios['activo'] = True
        
        # Fotografía URL (opcional, se pasa directamente)
        if 'fotografia_url' in datos:
            fotografia_url = datos.get('fotografia_url', '').strip()
            if fotografia_url:
                datos_limpios['fotografia_url'] = fotografia_url
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'datos_limpios': datos_limpios
        }