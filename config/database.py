# Archivo: config/database.py
import psycopg2
import psycopg2.pool
from typing import Optional, Dict, List, Any, Tuple, Union
import logging
from datetime import datetime
import threading
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)

# Variable global para el timer de limpieza
_cleanup_timer: Optional[threading.Timer] = None

class Database:
    """Clase para manejar la conexión a PostgreSQL con pool robusto"""
    
    _instance: Optional['Database'] = None
    _connection_pool: Optional[psycopg2.pool.SimpleConnectionPool] = None
    _lock = threading.Lock()  # Para sincronización de hilos
    _active_connections: Dict[int, Dict[str, Any]] = {}  # Para rastrear conexiones activas
    
    _config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'formagestpro_db',
        'user': 'postgres',
        'password': 'Despachanet'
    }
    
    # Configuración del pool optimizada
    POOL_MIN = 2
    POOL_MAX = 20  # Aumentado de 10 a 20
    
    def __init__(self):
        """Constructor privado para Singleton"""
        raise RuntimeError('Usa get_instance() en lugar de esto')
    
    @classmethod
    def get_instance(cls) -> 'Database':
        """Obtener instancia única del Singleton"""
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            # Inicializar el pool si no está inicializado
            if cls._connection_pool is None:
                cls.initialize_pool()
        return cls._instance
    
    @classmethod
    def get_db_config(cls) -> Dict[str, Any]:
        """Obtener configuración de la base de datos"""
        return cls._config.copy()
    
    @classmethod
    def initialize_pool(cls) -> bool:
        """Inicializar el pool de conexiones optimizado"""
        with cls._lock:
            if cls._connection_pool is not None:
                return True
                
            try:
                # Usar SimpleConnectionPool que es más estable
                cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=cls.POOL_MIN,
                    maxconn=cls.POOL_MAX,
                    host=cls._config['host'],
                    database=cls._config['database'],
                    user=cls._config['user'],
                    password=cls._config['password'],
                    port=cls._config['port']
                )
                
                logger.info(f"✅ Pool de conexiones a PostgreSQL inicializado")
                logger.info(f"   Config: min={cls.POOL_MIN}, max={cls.POOL_MAX}")
                
                # Probar conexión inicial SIN usar get_connection_safe (para evitar deadlock)
                try:
                    # Obtener conexión directamente del pool
                    connection = cls._connection_pool.getconn()
                    if connection:
                        cursor = connection.cursor()
                        cursor.execute("SELECT 1")
                        cursor.close()
                        cls._connection_pool.putconn(connection)
                        logger.info("✅ Conexión de prueba exitosa")
                        return True
                    else:
                        logger.error("❌ No se pudo obtener conexión de prueba")
                        return False
                except Exception as e:
                    logger.error(f"❌ Error probando conexión inicial: {e}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ Error inicializando pool de conexiones: {e}")
                cls._connection_pool = None
                return False
    
    @classmethod
    def get_connection_safe(cls) -> Optional[psycopg2.extensions.connection]:
        """Obtener conexión de forma segura (sin timeout)"""
        with cls._lock:
            if cls._connection_pool is None:
                # Intentar inicializar sin lock para evitar deadlock
                # Temporarily release lock to avoid deadlock
                cls._lock.release()
                try:
                    if not cls.initialize_pool():
                        return None
                finally:
                    cls._lock.acquire()
                
                # Verificar nuevamente después de inicializar
                if cls._connection_pool is None:
                    return None
            
            # Verificación explícita para Pylance
            pool = cls._connection_pool
            if pool is None:
                logger.error("❌ Pool no inicializado")
                return None
            
            try:
                connection = pool.getconn()
                
                if connection is None:
                    logger.error("❌ No se pudo obtener conexión")
                    return None
                
                # Verificar que la conexión sea válida
                try:
                    cursor = connection.cursor()
                    cursor.execute("SELECT 1")
                    cursor.close()
                    
                    # Registrar conexión activa
                    thread_id = threading.get_ident()
                    cls._active_connections[thread_id] = {
                        'connection': connection,
                        'timestamp': time.time()
                    }
                    
                    logger.debug(f"🔗 Conexión obtenida (Activas: {len(cls._active_connections)})")
                    return connection
                    
                except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
                    # La conexión está rota, cerrarla
                    logger.warning(f"⚠️  Conexión inválida: {e}")
                    try:
                        connection.close()
                    except:
                        pass
                    
                    # Intentar obtener nueva conexión
                    try:
                        # Verificar pool nuevamente
                        pool = cls._connection_pool
                        if pool is None:
                            return None
                            
                        connection = pool.getconn()
                        if connection:
                            # Registrar la nueva conexión
                            thread_id = threading.get_ident()
                            cls._active_connections[thread_id] = {
                                'connection': connection,
                                'timestamp': time.time()
                            }
                            logger.debug(f"🔗 Nueva conexión obtenida tras error")
                            return connection
                    except Exception as e2:
                        logger.error(f"❌ Error obteniendo nueva conexión: {e2}")
                        return None
                        
            except Exception as e:
                logger.error(f"❌ Error obteniendo conexión del pool: {e}")
                return None
    
    @classmethod
    def get_connection(cls) -> Optional[psycopg2.extensions.connection]:
        """Alias para get_connection_safe (para mantener compatibilidad)"""
        return cls.get_connection_safe()
    
    @classmethod
    def _get_direct_connection(cls) -> Optional[psycopg2.extensions.connection]:
        """Obtener conexión directa como fallback cuando el pool falla"""
        try:
            connection = psycopg2.connect(**cls._config)
            connection.autocommit = False
            
            # Registrar como conexión temporal
            thread_id = threading.get_ident()
            cls._active_connections[thread_id] = {
                'connection': connection,
                'timestamp': time.time(),
                'direct': True
            }
            
            logger.info("🆕 Conexión directa creada (fallback)")
            return connection
            
        except Exception as e:
            logger.error(f"❌ Error creando conexión directa: {e}")
            return None
    
    @classmethod
    def return_connection(cls, connection: Optional[psycopg2.extensions.connection]) -> None:
        """Devolver conexión al pool de forma segura"""
        with cls._lock:
            if connection is None:
                logger.warning("⚠️  Intento de devolver conexión None")
                return
            
            # Remover de conexiones activas
            thread_id = threading.get_ident()
            if thread_id in cls._active_connections:
                cls._active_connections.pop(thread_id, None)
            
            pool = cls._connection_pool
            if pool is None:
                # Si no hay pool, simplemente cerrar la conexión
                try:
                    if not connection.closed:
                        connection.close()
                    logger.debug("🔒 Conexión cerrada (pool no disponible)")
                except:
                    pass
                return
            
            try:
                # Verificar si la conexión aún es válida
                if connection.closed:
                    logger.warning("⚠️  Intento de devolver conexión cerrada")
                    return
                
                # Resetear la conexión
                try:
                    connection.rollback()
                except:
                    pass
                
                # Devolver al pool
                pool.putconn(connection)
                logger.debug(f"🔙 Conexión devuelta al pool")
                    
            except (psycopg2.InterfaceError, psycopg2.OperationalError) as e:
                # La conexión está dañada, cerrarla
                logger.warning(f"⚠️  Conexión dañada, cerrando: {e}")
                try:
                    connection.close()
                except:
                    pass
            except Exception as e:
                logger.error(f"❌ Error devolviendo conexión: {e}")
    
    @classmethod
    def close_all_connections(cls) -> None:
        """Cerrar todas las conexiones del pool"""
        with cls._lock:
            # Cerrar conexiones activas
            for thread_id, conn_info in list(cls._active_connections.items()):
                try:
                    conn = conn_info.get('connection')
                    if conn and not conn.closed:
                        conn.close()
                except:
                    pass
            cls._active_connections.clear()
            
            # Cerrar el pool
            pool = cls._connection_pool
            if pool:
                try:
                    pool.closeall()
                    logger.info("🔒 Todas las conexiones del pool cerradas")
                except Exception as e:
                    logger.error(f"❌ Error cerrando pool: {e}")
                finally:
                    cls._connection_pool = None
    
    @classmethod
    @contextmanager
    def get_cursor(cls):
        """Context manager para obtener cursor de forma segura"""
        connection: Optional[psycopg2.extensions.connection] = None
        cursor: Optional[psycopg2.extensions.cursor] = None
        try:
            connection = cls.get_connection_safe()
            if connection:
                cursor = connection.cursor()
                yield cursor
                connection.commit()
            else:
                raise Exception("No se pudo obtener conexión")
        except Exception as e:
            if connection:
                try:
                    connection.rollback()
                except:
                    pass
            logger.error(f"❌ Error en contexto de cursor: {e}")
            raise
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if connection:
                cls.return_connection(connection)
    
    @classmethod
    def execute_query(cls, query: str, 
                    params: Optional[Tuple] = None, 
                    fetch_one: bool = False, 
                    fetch_all: bool = True, 
                    commit: bool = False) -> Optional[Any]:
        """Ejecutar una consulta SQL de forma segura"""
        with cls.get_cursor() as cursor:
            try:
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
                    cursor.connection.commit()
                    logger.debug("✅ Commit realizado")
                
                return result
                
            except Exception as e:
                logger.error(f"❌ Error ejecutando query: {e}")
                logger.error(f"Query: {query[:100]}...")
                raise
    
    @classmethod
    def test_connection(cls) -> bool:
        """Probar la conexión a la base de datos"""
        try:
            with cls.get_cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()
                if version and version[0]:  # Verificar que version no sea None y tenga al menos un elemento
                    logger.info(f"✅ Conexión exitosa a PostgreSQL: {version[0]}")
                    return True
                else:
                    logger.error("❌ No se pudo obtener versión de PostgreSQL")
                    return False
        except Exception as e:
            logger.error(f"❌ Error de conexión: {e}")
            return False
    
    @classmethod
    def cleanup_idle_connections(cls, max_age_seconds: int = 300) -> None:
        """Limpiar conexiones inactivas o dañadas"""
        # NO usar lock aquí para evitar deadlocks con limpieza periódica
        try:
            current_time = time.time()
            to_remove = []
            
            # Limpiar conexiones activas antiguas
            for thread_id, conn_info in cls._active_connections.items():
                timestamp = conn_info.get('timestamp', 0)
                if current_time - timestamp > max_age_seconds:
                    to_remove.append(thread_id)
            
            for thread_id in to_remove:
                conn_info = cls._active_connections.pop(thread_id, None)
                if conn_info:
                    conn = conn_info.get('connection')
                    if conn and not conn.closed:
                        try:
                            conn.close()
                            logger.debug(f"🔒 Conexión inactiva cerrada (hilo {thread_id})")
                        except:
                            pass
            
        except Exception as e:
            logger.warning(f"⚠️  Error en limpieza general: {e}")
    
    @classmethod
    def get_pool_status(cls) -> Dict[str, Any]:
        """Obtener estado del pool de conexiones"""
        with cls._lock:
            status = {
                'pool_initialized': cls._connection_pool is not None,
                'active_connections': len(cls._active_connections),
                'pool_min': cls.POOL_MIN,
                'pool_max': cls.POOL_MAX,
                'timestamp': datetime.now().isoformat()
            }
            
            # Obtener información adicional si está disponible
            try:
                if cls._connection_pool:
                    status['pool_type'] = 'SimpleConnectionPool'
            except:
                pass
            
            return status

# Inicializar el pool al importar - versión segura sin deadlock
def safe_initialize_pool():
    """Inicializar el pool de forma segura evitando deadlocks"""
    try:
        # No usar Database.initialize_pool() directamente porque puede causar deadlock
        # En su lugar, crear el pool de forma simple
        Database._connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=Database.POOL_MIN,
            maxconn=Database.POOL_MAX,
            host=Database._config['host'],
            database=Database._config['database'],
            user=Database._config['user'],
            password=Database._config['password'],
            port=Database._config['port']
        )
        logger.info(f"✅ Pool de conexiones inicializado (min={Database.POOL_MIN}, max={Database.POOL_MAX})")
        
        # Probar conexión de forma simple
        try:
            conn = Database._connection_pool.getconn()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                Database._connection_pool.putconn(conn)
                logger.info("✅ Conexión de prueba exitosa")
        except Exception as e:
            logger.error(f"⚠️  Error probando conexión inicial: {e}")
            
    except Exception as e:
        logger.error(f"❌ Error inicializando pool: {e}")
        Database._connection_pool = None

try:
    safe_initialize_pool()
    logger.info("✅ Módulo database.py cargado e inicializado")
except Exception as e:
    logger.error(f"❌ Error al inicializar database.py: {e}")

def setup_periodic_cleanup(interval_seconds: int = 300) -> None:
    """Configurar limpieza periódica"""
    global _cleanup_timer
    
    def cleanup_task():
            global _cleanup_timer
            try:
                Database.cleanup_idle_connections()
            except Exception as e:
                logger.error(f"❌ Error en limpieza periódica: {e}")
            finally:
                # Re-programar
                timer = _cleanup_timer
            if timer is not None:
                timer.cancel()
            _cleanup_timer = threading.Timer(interval_seconds, cleanup_task)
            _cleanup_timer.daemon = True
            _cleanup_timer.start()
    
    # Iniciar limpieza periódica
    _cleanup_timer = threading.Timer(interval_seconds, cleanup_task)
    _cleanup_timer.daemon = True
    _cleanup_timer.start()
    logger.info(f"🔄 Limpieza periódica configurada cada {interval_seconds} segundos")

# Iniciar limpieza periódica (comentado por defecto, descomentar si es necesario)
# setup_periodic_cleanup(300)  # Cada 5 minutos

# Limpiar al salir
import atexit
atexit.register(Database.close_all_connections)