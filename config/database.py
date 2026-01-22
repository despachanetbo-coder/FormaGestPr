# Archivo: config/database.py
import psycopg2
from psycopg2 import pool
from typing import Optional, Dict, List, Any, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Database:
    """Clase para manejar la conexión a PostgreSQL"""
    
    _instance = None
    _connection_pool = None
    _config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'formagestpro_db',
        'user': 'postgres',
        'password': 'Despachanet'
    }
    
    def __init__(self):
        """Constructor privado para Singleton"""
        raise RuntimeError('Usa get_instance() en lugar de esto')
    
    @classmethod
    def get_instance(cls):
        """Obtener instancia única del Singleton"""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            # Inicializar el pool si no está inicializado
            if cls._connection_pool is None:
                cls.initialize_pool()
        return cls._instance
    
    @classmethod
    def initialize_pool(cls, min_connections=1, max_connections=10):
        """Inicializar el pool de conexiones"""
        try:
            cls._connection_pool = psycopg2.pool.SimpleConnectionPool( #type:ignore
                min_connections,
                max_connections,
                **cls._config
            )
            logger.info("✅ Pool de conexiones a PostgreSQL inicializado")
            return True
        except Exception as e:
            logger.error(f"❌ Error inicializando pool de conexiones: {e}")
            return False
    
    @classmethod
    def get_connection(cls):
        """Obtener una conexión del pool"""
        if cls._connection_pool:
            try:
                return cls._connection_pool.getconn()
            except Exception as e:
                logger.error(f"❌ Error obteniendo conexión: {e}")
                return None
        return None
    
    @classmethod
    def return_connection(cls, connection):
        """Devolver conexión al pool"""
        if cls._connection_pool and connection:
            cls._connection_pool.putconn(connection)
    
    @classmethod
    def close_all_connections(cls):
        """Cerrar todas las conexiones del pool"""
        if cls._connection_pool:
            cls._connection_pool.closeall()
            logger.info("🔒 Todas las conexiones cerradas")
    
    @classmethod
    def execute_query(cls, query: str, 
                    params: Optional[Tuple] = None, 
                    fetch_one: bool = False, 
                    fetch_all: bool = True, 
                    commit: bool = False) -> Optional[Any]:
        """Ejecutar una consulta SQL"""
        connection = cls.get_connection()
        if not connection:
            return None
            
        cursor = None
        try:
            cursor = connection.cursor()
            
            # Si params es None, ejecutar sin parámetros
            if params is None:
                cursor.execute(query)
            else:
                cursor.execute(query, params)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = cursor.rowcount
            
            if commit:
                connection.commit()
                logger.debug("✅ Commit realizado")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando query: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            if connection:
                connection.rollback()
            return None
            
        finally:
            if cursor:
                cursor.close()
            cls.return_connection(connection)
    
    @classmethod
    def test_connection(cls):
        """Probar la conexión a la base de datos"""
        try:
            conn = psycopg2.connect(**cls._config)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            cursor.close()
            conn.close()
            logger.info(f"✅ Conexión exitosa a PostgreSQL: {version[0]}")
            return True
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False
    
    @classmethod
    def execute_procedure(cls, proc_name: str, params: Tuple):
        """Ejecutar un procedimiento almacenado"""
        connection = cls.get_connection()
        if not connection:
            return False
            
        cursor = None
        try:
            cursor = connection.cursor()
            # Construir la llamada al procedimiento
            placeholders = ', '.join(['%s'] * len(params))
            call_query = f"CALL {proc_name}({placeholders})"
            cursor.execute(call_query, params)
            connection.commit()
            return True
        except Exception as e:
            logger.error(f"❌ Error ejecutando procedimiento {proc_name}: {e}")
            if connection:
                connection.rollback()
            return False
        finally:
            if cursor:
                cursor.close()
            cls.return_connection(connection)
            
    # Archivo: config/database.py - Método alternativo para procedimientos OUT

    @classmethod
    def execute_procedure_simple_out(cls, proc_name: str, in_params: Tuple):
        """Ejecutar procedimiento con parámetros OUT (versión simplificada)"""
        connection = cls.get_connection()
        if not connection:
            return None
            
        cursor = None
        try:
            cursor = connection.cursor()
            
            # Para PostgreSQL, necesitamos usar una función wrapper
            # Crear función temporal que llama al procedimiento
            wrapper_function = f"""
            CREATE OR REPLACE FUNCTION temp_wrapper_{proc_name}()
            RETURNS TABLE(out1 VARCHAR, out2 VARCHAR, out3 VARCHAR) AS $$
            DECLARE
                v_out1 VARCHAR;
                v_out2 VARCHAR;
                v_out3 VARCHAR;
            BEGIN
                CALL {proc_name}({', '.join(['$' + str(i+1) for i in range(len(in_params))])}, v_out1, v_out2, v_out3);
                RETURN QUERY SELECT v_out1, v_out2, v_out3;
            END;
            $$ LANGUAGE plpgsql;
            """
            
            # Crear función wrapper
            cursor.execute(wrapper_function)
            
            # Ejecutar función wrapper
            cursor.execute(f"SELECT * FROM temp_wrapper_{proc_name}()", in_params)
            result = cursor.fetchone()
            
            # Limpiar función temporal
            cursor.execute(f"DROP FUNCTION temp_wrapper_{proc_name}()")
            
            connection.commit()
            return result
            
        except Exception as e:
            logger.error(f"❌ Error ejecutando procedimiento {proc_name}: {e}")
            if connection:
                connection.rollback()
            return None
            
        finally:
            if cursor:
                cursor.close()
            cls.return_connection(connection)

# Inicializar el pool al importar
Database.initialize_pool()