# controller/auth_controller.py
import logging
from typing import Dict, Any, Optional
from model.usuarios_model import UsuariosModel
from utils.security import SecurityUtils
import bcrypt

logger = logging.getLogger(__name__)

class AuthController:
    """Controlador para autenticación y manejo de sesiones"""
    
    def __init__(self):
        """Inicializar controlador de autenticación"""
        self.current_user = None
    
    def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """
        Autenticar un usuario usando BCrypt
        
        Args:
            username: Nombre de usuario
            password: Contraseña
            
        Returns:
            Dict con resultado de autenticación
        """
        logger.info(f"🔐 Autenticando: {username}")
        
        try:
            # 1. Limpiar entrada
            clean_username = username.strip()
            
            # 2. Obtener usuario de la BD
            usuario_data = UsuariosModel.obtener_usuario_por_username(clean_username)
            
            if not usuario_data:
                logger.warning(f"❌ Usuario no encontrado: {clean_username}")
                return {
                    'success': False,
                    'message': 'Usuario o contraseña incorrectos'
                }
            
            # 3. Verificar si está activo
            if not usuario_data.get('activo', True):
                logger.warning(f"❌ Usuario inactivo: {clean_username}")
                return {
                    'success': False,
                    'message': 'Usuario inactivo'
                }
            
            # 4. Obtener hash de la BD
            stored_hash = usuario_data.get('password_hash', '')
            
            if not stored_hash:
                logger.error(f"❌ No hay hash para usuario: {clean_username}")
                return {
                    'success': False,
                    'message': 'Error en credenciales'
                }
            
            # 5. VERIFICAR CON BCRYPT - ESTO ES LO CLAVE
            logger.debug(f"🔍 Hash en BD: {stored_hash[:30]}...")
            logger.debug(f"🔍 Contraseña ingresada: {'*' * len(password)}")
            
            # Usar bcrypt.checkpw para comparar
            password_bytes = password.encode('utf-8')
            hash_bytes = stored_hash.encode('utf-8')
            
            if bcrypt.checkpw(password_bytes, hash_bytes):
                logger.info(f"✅ Autenticación exitosa para: {clean_username}")
                
                # 6. Preparar datos del usuario
                user_data = {
                    'id': usuario_data.get('id'),
                    'username': usuario_data.get('username'),
                    'nombre_completo': usuario_data.get('nombre_completo'),
                    'email': usuario_data.get('email'),
                    'rol': usuario_data.get('rol'),
                    'fecha_registro': usuario_data.get('fecha_registro'),
                    'ultimo_acceso': usuario_data.get('ultimo_acceso')
                }
                
                # 7. Actualizar último acceso (opcional)
                # self._actualizar_ultimo_acceso(clean_username)
                
                return {
                    'success': True,
                    'message': 'Autenticación exitosa',
                    'user_data': user_data
                }
            else:
                logger.warning(f"❌ Contraseña incorrecta para: {clean_username}")
                return {
                    'success': False,
                    'message': 'Usuario o contraseña incorrectos'
                }
            
        except Exception as e:
            logger.error(f"❌ Error en autenticación: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                'success': False,
                'message': f'Error del sistema: {str(e)}'
            }
    
    def _actualizar_ultimo_acceso(self, username: str):
        """Actualizar último acceso del usuario"""
        try:
            # Aquí puedes implementar la actualización del último acceso
            pass
        except Exception as e:
            logger.error(f"Error actualizando último acceso: {e}")
    
    def validate_session(self, token: str) -> Dict[str, Any]:
        """
        Validar un token de sesión
        
        Args:
            token: Token de sesión
            
        Returns:
            Dict con resultado de validación
        """
        try:
            # Validar token
            token_data = SecurityUtils.validate_session_token(token)
            
            if not token_data:
                return {
                    'success': False,
                    'message': 'Sesión inválida o expirada'
                }
            
            # Obtener datos actualizados del usuario
            usuario_data = UsuariosModel.obtener_usuario_por_id(token_data['user_id'])
            
            if not usuario_data:
                return {
                    'success': False,
                    'message': 'Usuario no encontrado'
                }
            
            if not usuario_data.get('activo', False):
                return {
                    'success': False,
                    'message': 'Usuario inactivo'
                }
            
            # Crear datos de usuario
            user_data = {
                'id': usuario_data.get('id'),
                'username': usuario_data.get('username'),
                'nombre_completo': usuario_data.get('nombre_completo'),
                'email': usuario_data.get('email'),
                'rol': usuario_data.get('rol'),
                'fecha_creacion': usuario_data.get('fecha_creacion'),
                'ultimo_acceso': usuario_data.get('ultimo_acceso')
            }
            
            return {
                'success': True,
                'message': 'Sesión válida',
                'user_data': user_data
            }
            
        except Exception as e:
            logger.error(f"❌ Error validando sesión: {e}")
            return {
                'success': False,
                'message': f'Error validando sesión: {str(e)}'
            }
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Dict[str, Any]:
        """
        Cambiar contraseña de usuario
        
        Args:
            user_id: ID del usuario
            current_password: Contraseña actual
            new_password: Nueva contraseña
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Obtener usuario
            usuario_data = UsuariosModel.obtener_usuario_por_id(user_id)
            
            if not usuario_data:
                return {
                    'success': False,
                    'message': 'Usuario no encontrado'
                }
            
            # Verificar contraseña actual
            stored_password = usuario_data.get('password_hash', '')
            
            # Descomenta cuando implementes hash:
            # if not SecurityUtils.verify_password(current_password, stored_password):
            #     return {
            #         'success': False,
            #         'message': 'Contraseña actual incorrecta'
            #     }
            
            # Verificación temporal (ELIMINAR):
            if current_password != stored_password:
                return {
                    'success': False,
                    'message': 'Contraseña actual incorrecta'
                }
            
            # Verificar fortaleza de nueva contraseña
            strength = SecurityUtils.calculate_password_strength(new_password)
            if not strength['is_acceptable']:
                return {
                    'success': False,
                    'message': 'La nueva contraseña no es suficientemente segura',
                    'feedback': strength['feedback']
                }
            
            # Hashear nueva contraseña
            # new_password_hash = SecurityUtils.hash_password(new_password)
            new_password_hash = new_password  # TEMPORAL - usar hash después
            
            # Actualizar en base de datos
            resultado = UsuariosModel.actualizar_usuario(
                id=user_id,
                password_hash=new_password_hash
            )
            
            if isinstance(resultado, dict) and resultado.get('success', False):
                logger.info(f"✅ Contraseña cambiada para usuario ID: {user_id}")
                return {
                    'success': True,
                    'message': 'Contraseña cambiada exitosamente'
                }
            else:
                return {
                    'success': False,
                    'message': 'Error al actualizar contraseña en la base de datos'
                }
            
        except Exception as e:
            logger.error(f"❌ Error cambiando contraseña: {e}")
            return {
                'success': False,
                    'message': f'Error cambiando contraseña: {str(e)}'
                }
    
    def logout(self, user_id: int) -> Dict[str, Any]:
        """
        Cerrar sesión de usuario
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Aquí puedes implementar lógica adicional como:
            # - Invalidar tokens
            # - Registrar logout en bitácora
            # - Limpiar caché de sesión
            
            logger.info(f"✅ Logout exitoso para usuario ID: {user_id}")
            
            return {
                'success': True,
                'message': 'Sesión cerrada exitosamente'
            }
            
        except Exception as e:
            logger.error(f"❌ Error en logout: {e}")
            return {
                'success': False,
                'message': f'Error cerrando sesión: {str(e)}'
            }
    
    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """Obtener usuario actualmente autenticado"""
        return self.current_user
    
    def set_current_user(self, user_data: Dict[str, Any]):
        """Establecer usuario actual"""
        self.current_user = user_data
    
    def check_permission(self, required_roles: list) -> bool:
        """
        Verificar si el usuario actual tiene permisos
        
        Args:
            required_roles: Lista de roles permitidos
            
        Returns:
            True si tiene permiso
        """
        if not self.current_user:
            return False
        
        user_role = self.current_user.get('rol', '').upper()
        return user_role in [r.upper() for r in required_roles]