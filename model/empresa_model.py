# model/empresa_model.py
import logging
import json
from typing import Dict, List, Optional, Any
from config.database import Database

logger = logging.getLogger(__name__)

class EmpresaModel:
    """Modelo para la tabla empresa"""
    
    @staticmethod
    def ver_empresa() -> Dict[str, Any]:
        """
        Obtiene los datos de la empresa
        
        Returns:
            Dict con los datos de la empresa
        """
        connection = None
        cursor = None
        try:
            # Obtener conexión del pool
            connection = Database.get_connection()
            cursor = None
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            # Ejecutar función PostgreSQL
            cursor.execute("SELECT * FROM ver_empresa()")
            empresa = cursor.fetchone()
            
            if empresa:
                # Convertir a diccionario
                column_names = [desc[0] for desc in cursor.description]
                empresa_dict = dict(zip(column_names, empresa))
                return empresa_dict
            else:
                return {}
                
        except Exception as e:
            logger.error(f"Error al obtener datos de la empresa: {e}")
            raise
        finally:
            # Cerrar cursor si existe
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            # Devolver conexión al pool
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def insertar_empresa(nombre: str, nit: str, direccion: Optional[str] = None, 
                        telefono: Optional[str] = None, email: Optional[str] = None, 
                        logo_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Inserta una nueva empresa (solo si no existe)
        
        Args:
            nombre: Nombre de la empresa
            nit: NIT de la empresa
            direccion: Dirección (opcional)
            telefono: Teléfono (opcional)
            email: Email (opcional)
            logo_url: URL del logo (opcional)
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            # Obtener conexión del pool
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            # Ejecutar función PostgreSQL
            cursor.callproc('fn_insertar_empresa', (nombre, nit, direccion, telefono, email, logo_url))
            result = cursor.fetchone()[0]
            
            connection.commit()
            
            # Convertir JSON string a dict si es necesario
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
            logger.error(f"Error al insertar empresa: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            # Cerrar cursor si existe
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            # Devolver conexión al pool
            if connection:
                Database.return_connection(connection)
    
    @staticmethod
    def editar_empresa(id: int, nombre: str, nit: str, direccion: Optional[str] = None, 
                      telefono: Optional[str] = None, email: Optional[str] = None, 
                      logo_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Edita los datos de la empresa
        
        Args:
            id: ID de la empresa
            nombre: Nombre de la empresa
            nit: NIT de la empresa
            direccion: Dirección (opcional)
            telefono: Teléfono (opcional)
            email: Email (opcional)
            logo_url: URL del logo (opcional)
            
        Returns:
            Dict con resultado de la operación
        """
        connection = None
        cursor = None
        try:
            # Obtener conexión del pool
            connection = Database.get_connection()
            if not connection:
                raise Exception("No se pudo obtener conexión a la base de datos")
            
            cursor = connection.cursor()
            
            # Ejecutar función PostgreSQL
            cursor.callproc('fn_editar_empresa', (id, nombre, nit, direccion, telefono, email, logo_url))
            result = cursor.fetchone()[0]
            
            connection.commit()
            
            # Convertir JSON string a dict si es necesario
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
            logger.error(f"Error al editar empresa: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            # Cerrar cursor si existe
            try:
                if 'cursor' in locals() and cursor:
                    cursor.close()
            except:
                pass
            
            # Devolver conexión al pool
            if connection:
                Database.return_connection(connection)