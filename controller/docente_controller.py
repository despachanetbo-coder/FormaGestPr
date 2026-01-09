# Archivo: controller/docente_controller.py
from model.docente_model import DocenteModel
from utils.validators import Validators
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class DocenteController:
    """Controlador para manejar las operaciones de docentes"""
    
    @staticmethod
    def buscar_docentes(filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Buscar docentes con filtros
        
        Args:
            filtros: Diccionario con filtros de búsqueda
        
        Returns:
            Dict con resultados y metadata
        """
        try:
            # Validar y extraer parámetros
            ci_numero = filtros.get('ci_numero')
            ci_expedicion = filtros.get('ci_expedicion')
            nombre = filtros.get('nombre')
            grado_academico = filtros.get('grado_academico')
            activo = filtros.get('activo')
            limit = filtros.get('limit', 20)
            offset = filtros.get('offset', 0)
            
            # Validar límites
            if not isinstance(limit, int) or limit <= 0:
                limit = 20
            
            if not isinstance(offset, int) or offset < 0:
                offset = 0
            
            # Limitar el máximo de registros por consulta
            if limit > 100:
                limit = 100
            
            # Convertir None a strings vacíos para compatibilidad con el modelo
            ci_numero_str = str(ci_numero) if ci_numero is not None else ""
            ci_expedicion_str = str(ci_expedicion) if ci_expedicion is not None else ""
            nombre_str = str(nombre) if nombre is not None else ""
            grado_academico_str = str(grado_academico) if grado_academico is not None else ""
            
            # Validar activo (puede ser None, True o False)
            if activo is not None:
                if isinstance(activo, str):
                    activo = activo.lower() in ['true', '1', 'yes', 'si', 'sí']
                elif isinstance(activo, int):
                    activo = bool(activo)
                elif not isinstance(activo, bool):
                    activo = None
            
            # Ejecutar búsqueda
            docentes = DocenteModel.buscar_docentes(
                ci_numero=ci_numero_str,
                ci_expedicion=ci_expedicion_str,
                nombre=nombre_str,
                grado_academico=grado_academico_str,
                activo=activo, #type:ignore
                limit=limit,
                offset=offset
            )
            
            # Obtener total
            total = DocenteModel.contar_docentes(
                ci_numero=ci_numero_str,
                ci_expedicion=ci_expedicion_str,
                nombre=nombre_str,
                grado_academico=grado_academico_str,
                activo=activo #type:ignore
            )
            
            return {
                'success': True,
                'data': docentes,
                'metadata': {
                    'total': total,
                    'limit': limit,
                    'offset': offset,
                    'count': len(docentes)
                }
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda de docentes: {e}")
            return {
                'success': False,
                'message': f"Error al buscar docentes: {str(e)}",
                'data': []
            }
    
    @staticmethod
    def obtener_docente(docente_id: int) -> Dict[str, Any]:
        """
        Obtener un docente por ID
        
        Args:
            docente_id: ID del docente
        
        Returns:
            Dict con datos del docente o error
        """
        try:
            # Validar ID
            if not isinstance(docente_id, int) or docente_id <= 0:
                return {
                    'success': False,
                    'message': 'ID de docente inválido'
                }
            
            docente = DocenteModel.obtener_docente_por_id(docente_id)
            
            if docente:
                return {
                    'success': True,
                    'data': docente
                }
            else:
                return {
                    'success': False,
                    'message': f'Docente con ID {docente_id} no encontrado'
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo docente: {e}")
            return {
                'success': False,
                'message': f"Error al obtener docente: {str(e)}"
            }
    
    @staticmethod
    def validar_datos_docente(datos: Dict[str, Any], es_actualizacion: bool = False) -> Dict[str, Any]:
        """
        Validar datos del docente antes de enviar a la base de datos
        
        Args:
            datos: Diccionario con datos del docente
            es_actualizacion: True si es una actualización, False si es creación
        
        Returns:
            Dict con resultado de validación y datos limpios
        """
        errores = []
        datos_limpios = {}
        
        # Validar CI Número
        if 'ci_numero' in datos or not es_actualizacion:
            ci_numero = datos.get('ci_numero')
            ci_numero_str = str(ci_numero) if ci_numero is not None else ""
            valido, mensaje = Validators.validar_ci(ci_numero_str)
            if not valido:
                errores.append(mensaje)
            else:
                datos_limpios['ci_numero'] = mensaje  # El mensaje contiene el CI limpio
        
        # Validar CI Expedición (para creación es obligatorio)
        if 'ci_expedicion' in datos or not es_actualizacion:
            ci_expedicion = datos.get('ci_expedicion')
            ci_expedicion_str = str(ci_expedicion) if ci_expedicion is not None else ""
            if not es_actualizacion and (not ci_expedicion_str or ci_expedicion_str.strip() == ""):
                errores.append("La expedición del CI es requerida")
            elif ci_expedicion_str and ci_expedicion_str.strip():
                # Validar que sea una expedición válida (ajustar según enum en BD)
                expediciones_validas = ['LP', 'CB', 'SC', 'OR', 'PT', 'TJ', 'CH', 'BN', 'PA']
                if ci_expedicion_str not in expediciones_validas:
                    errores.append(f"Expedición de CI inválida. Use: {', '.join(expediciones_validas)}")
                else:
                    datos_limpios['ci_expedicion'] = ci_expedicion_str
        
        # Validar nombres (obligatorio)
        if 'nombres' in datos or not es_actualizacion:
            nombres = datos.get('nombres')
            nombres_str = str(nombres) if nombres is not None else ""
            valido, mensaje = Validators.validar_texto_obligatorio('nombres', nombres_str, 'nombres')
            if not valido:
                errores.append(mensaje)
            else:
                datos_limpios['nombres'] = mensaje
        
        # Validar apellido paterno (obligatorio)
        if 'apellido_paterno' in datos or not es_actualizacion:
            apellido_paterno = datos.get('apellido_paterno')
            apellido_paterno_str = str(apellido_paterno) if apellido_paterno is not None else ""
            valido, mensaje = Validators.validar_texto_obligatorio(
                'apellido_paterno', apellido_paterno_str, 'apellido paterno'
            )
            if not valido:
                errores.append(mensaje)
            else:
                datos_limpios['apellido_paterno'] = mensaje
        
        # Validar apellido materno (opcional)
        if 'apellido_materno' in datos:
            apellido_materno = datos.get('apellido_materno')
            apellido_materno_str = str(apellido_materno) if apellido_materno is not None else ""
            valido, mensaje = Validators.validar_texto_opcional('apellido_materno', apellido_materno_str, 100)
            if not valido:
                errores.append(mensaje)
            elif mensaje:  # Solo agregar si tiene valor
                datos_limpios['apellido_materno'] = mensaje
        
        # Validar fecha de nacimiento (opcional)
        if 'fecha_nacimiento' in datos:
            fecha_str = datos.get('fecha_nacimiento')
            fecha_str_val = str(fecha_str) if fecha_str is not None else ""
            if fecha_str_val:
                valido, mensaje, fecha = Validators.validar_fecha_nacimiento(fecha_str_val)
                if not valido:
                    errores.append(mensaje)
                elif fecha:
                    datos_limpios['fecha_nacimiento'] = fecha
        
        # Validar grado académico (opcional)
        if 'grado_academico' in datos:
            grado_academico = datos.get('grado_academico')
            if grado_academico:
                # Validar que sea un grado académico válido (ajustar según enum en BD)
                grados_validos = ['BACHILLER', 'LICENCIATURA', 'MAESTRIA', 'DOCTORADO', 'POSTDOCTORADO']
                grado_str = str(grado_academico).upper()
                if grado_str not in grados_validos:
                    errores.append(f"Grado académico inválido. Use: {', '.join(grados_validos)}")
                else:
                    datos_limpios['grado_academico'] = grado_str
        
        # Validar título profesional (opcional)
        if 'titulo_profesional' in datos:
            titulo_profesional = datos.get('titulo_profesional')
            titulo_profesional_str = str(titulo_profesional) if titulo_profesional is not None else ""
            valido, mensaje = Validators.validar_texto_opcional('titulo_profesional', titulo_profesional_str, 200)
            if not valido:
                errores.append(mensaje)
            elif mensaje:
                datos_limpios['titulo_profesional'] = mensaje
        
        # Validar especialidad (opcional)
        if 'especialidad' in datos:
            especialidad = datos.get('especialidad')
            especialidad_str = str(especialidad) if especialidad is not None else ""
            valido, mensaje = Validators.validar_texto_opcional('especialidad', especialidad_str, 200)
            if not valido:
                errores.append(mensaje)
            elif mensaje:
                datos_limpios['especialidad'] = mensaje
        
        # Validar teléfono (opcional)
        if 'telefono' in datos:
            telefono = datos.get('telefono')
            telefono_str = str(telefono) if telefono is not None else ""
            valido, mensaje = Validators.validar_telefono(telefono_str)
            if not valido:
                errores.append(mensaje)
            elif telefono_str:  # Solo agregar si tiene valor después de limpiar
                datos_limpios['telefono'] = telefono_str
        
        # Validar email (opcional)
        if 'email' in datos:
            email = datos.get('email')
            email_str = str(email) if email is not None else ""
            valido, mensaje = Validators.validar_email(email_str)
            if not valido:
                errores.append(mensaje)
            elif email_str and email_str.strip():
                datos_limpios['email'] = email_str.strip()
        
        # Validar curriculum_url (opcional) - usando validar_path en lugar de validar_url
        if 'curriculum_url' in datos:
            curriculum_url = datos.get('curriculum_url')
            curriculum_url_str = str(curriculum_url) if curriculum_url is not None else ""
            valido, mensaje = Validators.validar_path(curriculum_url_str)
            if not valido:
                errores.append(mensaje)
            elif curriculum_url_str:
                datos_limpios['curriculum_url'] = curriculum_url_str
        
        # Validar honorario por hora (opcional)
        if 'honorario_hora' in datos:
            honorario_hora = datos.get('honorario_hora')
            if honorario_hora is not None:
                try:
                    honorario_decimal = float(honorario_hora)
                    if honorario_decimal < 0:
                        errores.append("El honorario por hora no puede ser negativo")
                    else:
                        datos_limpios['honorario_hora'] = honorario_decimal
                except (ValueError, TypeError):
                    errores.append("El honorario por hora debe ser un número válido")
        
        # Validar activo (opcional)
        if 'activo' in datos:
            activo = datos.get('activo')
            valido, valor_booleano = Validators.validar_booleano(activo)
            if not valido:
                errores.append("El campo 'activo' debe ser verdadero o falso")
            elif valor_booleano is not None:
                datos_limpios['activo'] = valor_booleano
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'datos_limpios': datos_limpios
        }
    
    @staticmethod
    def crear_docente(datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo docente
        
        Args:
            datos: Diccionario con datos del docente
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar datos
            validacion = DocenteController.validar_datos_docente(datos, es_actualizacion=False)
            
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Verificar si el CI ya existe
            ci_numero = validacion['datos_limpios'].get('ci_numero')
            if DocenteModel.verificar_ci_existente(ci_numero):
                return {
                    'success': False,
                    'message': f'El CI {ci_numero} ya está registrado en el sistema'
                }
            
            # Verificar si el email ya existe (si se proporciona)
            email = validacion['datos_limpios'].get('email')
            if email:
                if DocenteModel.verificar_email_existente(email):
                    return {
                        'success': False,
                        'message': f'El email {email} ya está registrado en el sistema'
                    }
            
            # Crear docente usando el modelo
            resultado = DocenteModel.crear_docente(validacion['datos_limpios'])
            
            if resultado['exito']:
                return {
                    'success': True,
                    'message': resultado['mensaje'],
                    'data': {
                        'id': resultado['nuevo_id'],
                        'ci_numero': ci_numero
                    }
                }
            else:
                return {
                    'success': False,
                    'message': resultado['mensaje']
                }
                
        except Exception as e:
            logger.error(f"Error creando docente: {e}")
            return {
                'success': False,
                'message': f"Error al crear docente: {str(e)}"
            }
    
    @staticmethod
    def actualizar_docente(docente_id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar un docente existente
        
        Args:
            docente_id: ID del docente a actualizar
            datos: Diccionario con datos a actualizar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar ID
            if not isinstance(docente_id, int) or docente_id <= 0:
                return {
                    'success': False,
                    'message': 'ID de docente inválido'
                }
            
            # Verificar que el docente exista
            docente = DocenteModel.obtener_docente_por_id(docente_id)
            if not docente:
                return {
                    'success': False,
                    'message': f'Docente con ID {docente_id} no encontrado'
                }
            
            # Validar datos
            validacion = DocenteController.validar_datos_docente(datos, es_actualizacion=True)
            
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Verificar unicidad del CI (si se está actualizando)
            if 'ci_numero' in validacion['datos_limpios']:
                ci_numero = validacion['datos_limpios']['ci_numero']
                if DocenteModel.verificar_ci_existente(ci_numero, docente_id):
                    return {
                        'success': False,
                        'message': f'El CI {ci_numero} ya está registrado en otro docente'
                    }
            
            # Verificar unicidad del email (si se está actualizando)
            if 'email' in validacion['datos_limpios']:
                email = validacion['datos_limpios']['email']
                if email:
                    if DocenteModel.verificar_email_existente(email, docente_id):
                        return {
                            'success': False,
                            'message': f'El email {email} ya está registrado en otro docente'
                        }
            
            # Actualizar docente usando el modelo
            resultado = DocenteModel.actualizar_docente(docente_id, validacion['datos_limpios'])
            
            if resultado['exito']:
                return {
                    'success': True,
                    'message': resultado['mensaje'],
                    'data': {
                        'id': docente_id,
                        'filas_afectadas': resultado['filas_afectadas']
                    }
                }
            else:
                return {
                    'success': False,
                    'message': resultado['mensaje']
                }
                
        except Exception as e:
            logger.error(f"Error actualizando docente: {e}")
            return {
                'success': False,
                'message': f"Error al actualizar docente: {str(e)}"
            }
    
    @staticmethod
    def eliminar_docente(docente_id: int) -> Dict[str, Any]:
        """
        Eliminar (desactivar) un docente
        
        Args:
            docente_id: ID del docente a eliminar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar ID
            if not isinstance(docente_id, int) or docente_id <= 0:
                return {
                    'success': False,
                    'message': 'ID de docente inválido'
                }
            
            # Ejecutar eliminación usando el modelo
            resultado = DocenteModel.eliminar_docente(docente_id)
            
            if resultado['exito']:
                return {
                    'success': True,
                    'message': resultado['mensaje'],
                    'data': {
                        'id': docente_id,
                        'filas_afectadas': resultado['filas_afectadas']
                    }
                }
            else:
                return {
                    'success': False,
                    'message': resultado['mensaje']
                }
                
        except Exception as e:
            logger.error(f"Error eliminando docente: {e}")
            return {
                'success': False,
                'message': f"Error al eliminar docente: {str(e)}"
            }
    
    @staticmethod
    def activar_docente(docente_id: int) -> Dict[str, Any]:
        """
        Activar un docente previamente desactivado
        
        Args:
            docente_id: ID del docente a activar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar ID
            if not isinstance(docente_id, int) or docente_id <= 0:
                return {
                    'success': False,
                    'message': 'ID de docente inválido'
                }
            
            # Ejecutar activación usando el modelo
            resultado = DocenteModel.activar_docente(docente_id)
            
            if resultado['exito']:
                return {
                    'success': True,
                    'message': resultado['mensaje'],
                    'data': {
                        'id': docente_id,
                        'filas_afectadas': resultado['filas_afectadas']
                    }
                }
            else:
                return {
                    'success': False,
                    'message': resultado['mensaje']
                }
                
        except Exception as e:
            logger.error(f"Error activando docente: {e}")
            return {
                'success': False,
                'message': f"Error al activar docente: {str(e)}"
            }
    
    @staticmethod
    def obtener_estadisticas() -> Dict[str, Any]:
        """
        Obtener estadísticas de docentes
        
        Returns:
            Dict con estadísticas
        """
        try:
            estadisticas = DocenteModel.obtener_estadisticas()
            
            return {
                'success': True,
                'data': estadisticas
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {
                'success': False,
                'message': f"Error al obtener estadísticas: {str(e)}"
            }