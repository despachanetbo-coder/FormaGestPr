# model/usuarios_model.py
import logging
import json
from typing import Dict, List, Optional, Any
from config.database import Database

logger = logging.getLogger(__name__)

class UsuariosModel:
    """Modelo para la tabla usuarios"""
    
    @staticmethod
    def insertar_usuario(username: str, password_hash: str, nombre_completo: str,
                        email: Optional[str] = None, rol: str = 'CAJERO', 
                        activo: bool = True) -> Dict[str, Any]:
        """
        Inserta un nuevo usuario
        
        Args:
            username: Nombre de usuario
            password_hash: Hash de la contraseña
            nombre_completo: Nombre completo del usuario
            email: Email (opcional)
            rol: Rol del usuario (por defecto 'CAJERO')
            activo: Si está activo (por defecto True)
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('fn_insertar_usuario', (username, password_hash, nombre_completo, email, rol, activo))
            fetchone_result = cursor.fetchone()
            if fetchone_result is None:
                raise Exception("No se recibió respuesta del procedimiento almacenado")
            result = fetchone_result[0]
            
            connection.commit()
            
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {'success': True, 'data': result}
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al insertar usuario: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def actualizar_usuario( id: int, username: Optional[str] = None, 
                            password_hash: Optional[str] = None, 
                            nombre_completo: Optional[str] = None,
                            email: Optional[str] = None, rol: Optional[str] = None,
                            activo: Optional[bool] = None) -> Dict[str, Any]:
        """
        Actualiza un usuario existente
        
        Args:
            id: ID del usuario
            username: Nuevo nombre de usuario (opcional)
            password_hash: Nuevo hash de contraseña (opcional)
            nombre_completo: Nuevo nombre completo (opcional)
            email: Nuevo email (opcional)
            rol: Nuevo rol (opcional)
            activo: Nuevo estado activo (opcional)
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('fn_actualizar_usuario', (id, username, password_hash, nombre_completo, email, rol, activo))
            fetchone_result = cursor.fetchone()
            if fetchone_result is None:
                raise Exception("No se recibió respuesta del procedimiento almacenado")
            result = fetchone_result[0]
            
            connection.commit()
            
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {'success': True, 'data': result}
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al actualizar usuario: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def eliminar_usuario(id: int) -> Dict[str, Any]:
        """
        Elimina (desactiva) un usuario
        
        Args:
            id: ID del usuario a eliminar
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('fn_eliminar_usuario', (id,))
            fetchone_result = cursor.fetchone()
            if fetchone_result is None:
                raise Exception("No se recibió respuesta del procedimiento almacenado")
            result = fetchone_result[0]
            
            connection.commit()
            
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {'success': True, 'data': result}
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al eliminar usuario: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def activar_usuario(id: int) -> Dict[str, Any]:
        """
        Activa un usuario
        
        Args:
            id: ID del usuario a activar
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('fn_activar_usuario', (id,))
            fetchone_result = cursor.fetchone()
            if fetchone_result is None:
                raise Exception("No se recibió respuesta del procedimiento almacenado")
            result = fetchone_result[0]
            
            connection.commit()
            
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {'success': True, 'data': result}
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al activar usuario: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
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
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.callproc('fn_cambiar_rol_usuario', (id, nuevo_rol))
            fetchone_result = cursor.fetchone()
            if fetchone_result is None:
                raise Exception("No se recibió respuesta del procedimiento almacenado")
            result = fetchone_result[0]
            
            connection.commit()
            
            if isinstance(result, str):
                try:
                    return json.loads(result)
                except json.JSONDecodeError:
                    return {'success': True, 'data': result}
            elif isinstance(result, dict):
                return result
            else:
                return {'success': True, 'data': result}
                
        except Exception as e:
            logger.error(f"Error al cambiar rol de usuario: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def obtener_usuario_por_id(id: int) -> Dict[str, Any]:
        """
        Obtiene un usuario por ID
        
        Args:
            id: ID del usuario
            
        Returns:
            Dict con los datos del usuario
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM obtener_usuario_por_id(%s)", (id,))
            usuario = cursor.fetchone()
            
            if usuario:
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                usuario_dict = dict(zip(column_names, usuario))
                return usuario_dict
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error al obtener usuario por ID: {e}")
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def obtener_usuario_por_username(username: str) -> Dict[str, Any]:
        """
        Obtiene un usuario por nombre de usuario
        
        Args:
            username: Nombre de usuario
            
        Returns:
            Dict con los datos del usuario
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM fn_obtener_usuario_por_username(%s)", (username,))
            usuario = cursor.fetchone()
            
            if usuario:
                column_names = [desc[0] for desc in cursor.description] if cursor.description else []
                usuario_dict = dict(zip(column_names, usuario))
                return usuario_dict
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error al obtener usuario por username: {e}")
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def buscar_usuarios(username: Optional[str] = None, 
                        nombre_completo: Optional[str] = None,
                        rol: Optional[str] = None, 
                        activo: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Busca usuarios con filtros
        
        Args:
            username: Username a buscar (opcional)
            nombre_completo: Nombre completo a buscar (opcional)
            rol: Rol a filtrar (opcional)
            activo: Estado activo a filtrar (opcional)
            
        Returns:
            Lista de usuarios
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM buscar_usuarios(%s, %s, %s, %s)", 
                            (username, nombre_completo, rol, activo))
            usuarios = cursor.fetchall()
            
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            result = []
            for usuario in usuarios:
                usuario_dict = dict(zip(column_names, usuario))
                result.append(usuario_dict)
            
            return result
                
        except Exception as e:
            logger.error(f"Error al buscar usuarios: {e}")
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def listar_usuarios() -> List[Dict[str, Any]]:
        """
        Lista todos los usuarios
        
        Returns:
            Lista de usuarios
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM listar_usuarios()")
            usuarios = cursor.fetchall()
            
            column_names = [desc[0] for desc in cursor.description] if cursor.description else []
            result = []
            for usuario in usuarios:
                usuario_dict = dict(zip(column_names, usuario))
                result.append(usuario_dict)
            
            return result
                
        except Exception as e:
            logger.error(f"Error al listar usuarios: {e}")
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)