# controller/usuarios_controller.py
import logging
from typing import Dict, List, Optional, Any
from model.usuarios_model import UsuariosModel
from utils.validators import Validators

logger = logging.getLogger(__name__)

class UsuariosController:
    """Controlador para la tabla usuarios"""
    
    @staticmethod
    def validar_datos_usuario(datos: Dict[str, Any], es_actualizacion: bool = False) -> Dict[str, Any]:
        """
        Valida los datos del usuario
        
        Args:
            datos: Diccionario con los datos del usuario
            es_actualizacion: True si es una actualización
        
        Returns:
            Dict con resultado de validación y datos limpios
        """
        errores = []
        datos_limpios = {}
        
        # Validar username (obligatorio)
        username = datos.get('username')
        if not es_actualizacion or 'username' in datos:
            if not username or username.strip() == "":
                errores.append("El nombre de usuario es requerido")
            elif len(username.strip()) > 50:
                errores.append("El nombre de usuario no puede exceder los 50 caracteres")
            else:
                datos_limpios['username'] = username.strip()
        
        # Validar password (obligatorio solo si no es actualización o se está cambiando)
        password = datos.get('password')
        if not es_actualizacion or 'password' in datos:
            if not password or password.strip() == "":
                errores.append("La contraseña es requerida")
            elif len(password) < 6:
                errores.append("La contraseña debe tener al menos 6 caracteres")
            else:
                # En una implementación real, aquí se hashearía la contraseña
                # Por ahora, almacenamos el hash simulado
                datos_limpios['password_hash'] = password  # Esto debería ser un hash
        
        # Validar nombre_completo (obligatorio)
        nombre_completo = datos.get('nombre_completo')
        if not es_actualizacion or 'nombre_completo' in datos:
            if not nombre_completo or nombre_completo.strip() == "":
                errores.append("El nombre completo es requerido")
            elif len(nombre_completo.strip()) > 200:
                errores.append("El nombre completo no puede exceder los 200 caracteres")
            else:
                datos_limpios['nombre_completo'] = nombre_completo.strip()
        
        # Validar email (opcional)
        email = datos.get('email')
        if email is not None:
            valido, mensaje = Validators.validar_email(email)
            if not valido:
                errores.append(mensaje)
            else:
                datos_limpios['email'] = email.strip()
        
        # Validar rol (opcional)
        rol = datos.get('rol')
        if rol is not None:
            roles_permitidos = ['ADMIN', 'CAJERO', 'DOCENTE', 'SECRETARIA']
            if str(rol).upper() not in roles_permitidos:
                errores.append(f"Rol inválido. Debe ser uno de: {', '.join(roles_permitidos)}")
            else:
                datos_limpios['rol'] = str(rol).upper()
        
        # Validar activo (opcional, booleano)
        activo = datos.get('activo')
        if activo is not None:
            valido, valor_booleano = Validators.validar_booleano(activo)
            if not valido:
                errores.append("El campo activo debe ser un valor booleano")
            else:
                datos_limpios['activo'] = valor_booleano
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'datos_limpios': datos_limpios
        }
    
    @staticmethod
    def crear_usuario(datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crea un nuevo usuario
        
        Args:
            datos: Diccionario con los datos del usuario
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar datos
            validacion = UsuariosController.validar_datos_usuario(datos, es_actualizacion=False)
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Hash de la contraseña (en producción, usar bcrypt o similar)
            # Aquí solo simulamos
            password_hash = validacion['datos_limpios']['password_hash']  # Debería ser el hash
            
            # Llamar al modelo
            resultado = UsuariosModel.insertar_usuario(
                username=validacion['datos_limpios']['username'],
                password_hash=password_hash,
                nombre_completo=validacion['datos_limpios']['nombre_completo'],
                email=validacion['datos_limpios'].get('email'),
                rol=validacion['datos_limpios'].get('rol', 'CAJERO'),
                activo=validacion['datos_limpios'].get('activo', True)
            )
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al crear usuario: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al crear usuario'
                }
                
        except Exception as e:
            logger.error(f"Error al crear usuario: {e}")
            return {
                'success': False,
                'message': f"Error al crear usuario: {str(e)}"
            }
    
    @staticmethod
    def actualizar_usuario(id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualiza un usuario existente
        
        Args:
            id: ID del usuario a actualizar
            datos: Diccionario con los datos a actualizar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar ID
            if not isinstance(id, int) or id <= 0:
                return {
                    'success': False,
                    'message': 'ID de usuario inválido'
                }
            
            # Validar datos
            validacion = UsuariosController.validar_datos_usuario(datos, es_actualizacion=True)
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Preparar datos para el modelo
            username = validacion['datos_limpios'].get('username')
            password_hash = validacion['datos_limpios'].get('password_hash')
            nombre_completo = validacion['datos_limpios'].get('nombre_completo')
            email = validacion['datos_limpios'].get('email')
            rol = validacion['datos_limpios'].get('rol')
            activo = validacion['datos_limpios'].get('activo')
            
            # Llamar al modelo
            resultado = UsuariosModel.actualizar_usuario(
                id=id,
                username=username,
                password_hash=password_hash,
                nombre_completo=nombre_completo,
                email=email,
                rol=rol,
                activo=activo
            )
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al actualizar usuario: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al actualizar usuario'
                }
                
        except Exception as e:
            logger.error(f"Error al actualizar usuario: {e}")
            return {
                'success': False,
                'message': f"Error al actualizar usuario: {str(e)}"
            }
    
    @staticmethod
    def eliminar_usuario(id: int) -> Dict[str, Any]:
        """
        Elimina (desactiva) un usuario
        
        Args:
            id: ID del usuario a eliminar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if not isinstance(id, int) or id <= 0:
                return {
                    'success': False,
                    'message': 'ID de usuario inválido'
                }
            
            resultado = UsuariosModel.eliminar_usuario(id)
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al eliminar usuario: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al eliminar usuario'
                }
                
        except Exception as e:
            logger.error(f"Error al eliminar usuario: {e}")
            return {
                'success': False,
                'message': f"Error al eliminar usuario: {str(e)}"
            }
    
    @staticmethod
    def activar_usuario(id: int) -> Dict[str, Any]:
        """
        Activa un usuario
        
        Args:
            id: ID del usuario a activar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if not isinstance(id, int) or id <= 0:
                return {
                    'success': False,
                    'message': 'ID de usuario inválido'
                }
            
            resultado = UsuariosModel.activar_usuario(id)
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al activar usuario: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al activar usuario'
                }
                
        except Exception as e:
            logger.error(f"Error al activar usuario: {e}")
            return {
                'success': False,
                'message': f"Error al activar usuario: {str(e)}"
            }
    
    @staticmethod
    def cambiar_rol_usuario(id: int, nuevo_rol: str) -> Dict[str, Any]:
        """
        Cambia el rol de un usuario
        
        Args:
            id: ID del usuario
            nuevo_rol: Nuevo rol a asignar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            if not isinstance(id, int) or id <= 0:
                return {
                    'success': False,
                    'message': 'ID de usuario inválido'
                }
            
            if not nuevo_rol or nuevo_rol.strip() == "":
                return {
                    'success': False,
                    'message': 'El nuevo rol es requerido'
                }
            
            resultado = UsuariosModel.cambiar_rol_usuario(id, nuevo_rol)
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al cambiar rol de usuario: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al cambiar rol de usuario'
                }
                
        except Exception as e:
            logger.error(f"Error al cambiar rol de usuario: {e}")
            return {
                'success': False,
                'message': f"Error al cambiar rol de usuario: {str(e)}"
            }
    
    @staticmethod
    def obtener_usuario_por_id(id: int) -> Dict[str, Any]:
        """
        Obtiene un usuario por ID
        
        Args:
            id: ID del usuario
        
        Returns:
            Dict con los datos del usuario
        """
        try:
            if not isinstance(id, int) or id <= 0:
                return {
                    'success': False,
                    'message': 'ID de usuario inválido'
                }
            
            usuario = UsuariosModel.obtener_usuario_por_id(id)
            
            if usuario:
                return {
                    'success': True,
                    'data': usuario
                }
            else:
                return {
                    'success': False,
                    'message': f'Usuario con ID {id} no encontrado'
                }
                
        except Exception as e:
            logger.error(f"Error al obtener usuario: {e}")
            return {
                'success': False,
                'message': f"Error al obtener usuario: {str(e)}"
            }
    
    @staticmethod
    def obtener_usuario_por_username(username: str) -> Dict[str, Any]:
        """
        Obtiene un usuario por nombre de usuario
        
        Args:
            username: Nombre de usuario
        
        Returns:
            Dict con los datos del usuario
        """
        try:
            if not username or username.strip() == "":
                return {
                    'success': False,
                    'message': 'Nombre de usuario requerido'
                }
            
            usuario = UsuariosModel.obtener_usuario_por_username(username)
            
            if usuario:
                return {
                    'success': True,
                    'data': usuario
                }
            else:
                return {
                    'success': False,
                    'message': f'Usuario "{username}" no encontrado'
                }
                
        except Exception as e:
            logger.error(f"Error al obtener usuario por username: {e}")
            return {
                'success': False,
                'message': f"Error al obtener usuario por username: {str(e)}"
            }
    
    @staticmethod
    def buscar_usuarios(filtros: Dict[str, Any]) -> Dict[str, Any]:
        """
        Busca usuarios con filtros
        
        Args:
            filtros: Diccionario con filtros de búsqueda
        
        Returns:
            Dict con resultados
        """
        try:
            username = filtros.get('username')
            nombre_completo = filtros.get('nombre_completo')
            rol = filtros.get('rol')
            activo = filtros.get('activo')
            
            usuarios = UsuariosModel.buscar_usuarios(
                username=username,
                nombre_completo=nombre_completo,
                rol=rol,
                activo=activo
            )
            
            return {
                'success': True,
                'data': usuarios
            }
            
        except Exception as e:
            logger.error(f"Error al buscar usuarios: {e}")
            return {
                'success': False,
                'message': f"Error al buscar usuarios: {str(e)}"
            }
    
    @staticmethod
    def listar_usuarios() -> Dict[str, Any]:
        """
        Lista todos los usuarios
        
        Returns:
            Dict con lista de usuarios
        """
        try:
            usuarios = UsuariosModel.listar_usuarios()
            
            return {
                'success': True,
                'data': usuarios
            }
            
        except Exception as e:
            logger.error(f"Error al listar usuarios: {e}")
            return {
                'success': False,
                'message': f"Error al listar usuarios: {str(e)}"
            }