# model/configuraciones_model.py
import logging
import json
from typing import Dict, List, Optional, Any
from config.database import Database

logger = logging.getLogger(__name__)

class ConfiguracionesModel:
    """Modelo para la tabla configuraciones"""
    
    @staticmethod
    def insertar_configuracion(clave: str, valor: str, descripcion: Optional[str] = None,
                              tipo: str = 'TEXTO', categoria: str = 'GENERAL', 
                              editable: bool = True) -> Dict[str, Any]:
        """
        Inserta una nueva configuración
        
        Args:
            clave: Clave de la configuración
            valor: Valor de la configuración
            descripcion: Descripción (opcional)
            tipo: Tipo de dato (por defecto 'TEXTO')
            categoria: Categoría (por defecto 'GENERAL')
            editable: Si es editable (por defecto True)
            
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
            
            cursor.callproc('fn_insertar_configuracion', (clave, valor, descripcion, tipo, categoria, editable))
            result = cursor.fetchone()[0]
            
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
            logger.error(f"Error al insertar configuración: {e}")
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
    def actualizar_configuracion(clave: str, valor: str, descripcion: Optional[str] = None,
                                tipo: Optional[str] = None, categoria: Optional[str] = None,
                                editable: Optional[bool] = None) -> Dict[str, Any]:
        """
        Actualiza una configuración existente
        
        Args:
            clave: Clave de la configuración
            valor: Nuevo valor
            descripcion: Nueva descripción (opcional)
            tipo: Nuevo tipo (opcional)
            categoria: Nueva categoría (opcional)
            editable: Si es editable (opcional)
            
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
            
            cursor.callproc('fn_actualizar_configuracion', (clave, valor, descripcion, tipo, categoria, editable))
            result = cursor.fetchone()[0]
            
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
            logger.error(f"Error al actualizar configuración: {e}")
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
    def eliminar_configuracion(clave: str) -> Dict[str, Any]:
        """
        Elimina una configuración
        
        Args:
            clave: Clave de la configuración a eliminar
            
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
            
            cursor.callproc('fn_eliminar_configuracion', (clave,))
            result = cursor.fetchone()[0]
            
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
            logger.error(f"Error al eliminar configuración: {e}")
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
    def obtener_configuracion(clave: str) -> Dict[str, Any]:
        """
        Obtiene una configuración por clave
        
        Args:
            clave: Clave de la configuración
            
        Returns:
            Dict con los datos de la configuración
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM obtener_configuracion(%s)", (clave,))
            config = cursor.fetchone()
            
            if config:
                column_names = [desc[0] for desc in cursor.description]
                config_dict = dict(zip(column_names, config))
                return config_dict
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error al obtener configuración: {e}")
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
    def buscar_configuraciones(clave: Optional[str] = None, categoria: Optional[str] = None,
                              tipo: Optional[str] = None, editable: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Busca configuraciones con filtros
        
        Args:
            clave: Clave a buscar (opcional)
            categoria: Categoría a filtrar (opcional)
            tipo: Tipo a filtrar (opcional)
            editable: Si es editable (opcional)
            
        Returns:
            Lista de configuraciones
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM buscar_configuraciones(%s, %s, %s, %s)", 
                          (clave, categoria, tipo, editable))
            configs = cursor.fetchall()
            
            column_names = [desc[0] for desc in cursor.description]
            result = []
            for config in configs:
                config_dict = dict(zip(column_names, config))
                result.append(config_dict)
            
            return result
                
        except Exception as e:
            logger.error(f"Error al buscar configuraciones: {e}")
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
    def listar_configuraciones() -> List[Dict[str, Any]]:
        """
        Lista todas las configuraciones
        
        Returns:
            Lista de configuraciones
        """
        connection = None
        cursor = None
        try:
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            cursor.execute("SELECT * FROM listar_configuraciones()")
            configs = cursor.fetchall()
            
            column_names = [desc[0] for desc in cursor.description]
            result = []
            for config in configs:
                config_dict = dict(zip(column_names, config))
                result.append(config_dict)
            
            return result
                
        except Exception as e:
            logger.error(f"Error al listar configuraciones: {e}")
            raise
        finally:
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            if connection:
                Database.return_connection(connection)