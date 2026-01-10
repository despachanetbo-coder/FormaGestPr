# debug_auth.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import bcrypt
from config.database import Database

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def debug_hash_comparison():
    """Debug de comparación de hash"""
    print("\n" + "="*60)
    print("🔍 DEBUG DE COMPARACIÓN DE HASH")
    print("="*60)
    
    # Hash que debería estar en la BD
    stored_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    print(f"Hash almacenado (completo): {stored_hash}")
    print(f"Longitud del hash: {len(stored_hash)} caracteres")
    
    # Probar diferentes variaciones de "secret"
    test_passwords = [
        "secret",           # Exacto
        "secret ",          # Con espacio al final
        " secret",          # Con espacio al inicio
        "Secret",           # Con S mayúscula
        "SECRET",           # Todo mayúsculas
        "admin123",         # Otra contraseña
    ]
    
    print("\n🔐 Probando diferentes contraseñas:")
    for pwd in test_passwords:
        try:
            result = bcrypt.checkpw(pwd.encode('utf-8'), stored_hash.encode('utf-8'))
            print(f"  '{pwd}' -> {result}")
            if result:
                print(f"    ✅ ¡ESTA ES LA CONTRASEÑA CORRECTA!")
        except Exception as e:
            print(f"  '{pwd}' -> ERROR: {e}")

def get_user_from_db(username="admin"):
    """Obtener usuario directamente de la BD"""
    print("\n" + "="*60)
    print(f"🔍 OBTENIENDO USUARIO '{username}' DE LA BD")
    print("="*60)
    
    connection = None
    cursor = None
    
    try:
        connection = Database.get_connection()
        if not connection:
            print("❌ No se pudo obtener conexión")
            return None
        
        cursor = connection.cursor()
        
        # Intentar diferentes formas de obtener el usuario
        queries = [
            ("Consulta directa", """
                SELECT id, username, password_hash, nombre_completo, 
                    email, rol::text as rol, activo, fecha_registro, ultimo_acceso
                FROM usuarios 
                WHERE username = %s
            """),
            ("Función fn_obtener_usuario_por_username", 
             "SELECT * FROM fn_obtener_usuario_por_username(%s)"),
        ]
        
        for query_name, query in queries:
            print(f"\n📊 Intentando: {query_name}")
            try:
                cursor.execute(query, (username,))
                result = cursor.fetchone()
                
                if result:
                    print(f"✅ Usuario encontrado con {query_name}")
                    
                    # Obtener nombres de columnas
                    if cursor.description:
                        column_names = [desc[0] for desc in cursor.description]
                        user_dict = dict(zip(column_names, result))
                        
                        print(f"📋 Datos del usuario:")
                        for key, value in user_dict.items():
                            if key == 'password_hash' and value:
                                print(f"  {key}: {value[:30]}... (longitud: {len(value)})")
                            else:
                                print(f"  {key}: {value}")
                        
                        return user_dict
                else:
                    print(f"❌ Usuario no encontrado con {query_name}")
                    
            except Exception as e:
                print(f"⚠️ Error con {query_name}: {e}")
        
        print("\n❌ No se pudo obtener el usuario con ninguna consulta")
        return None
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            Database.return_connection(connection)

def test_bcrypt_directly():
    """Probar bcrypt directamente"""
    print("\n" + "="*60)
    print("🔐 PRUEBA DIRECTA DE BCRYPT")
    print("="*60)
    
    # Hash de ejemplo
    test_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    print(f"Hash de prueba: {test_hash}")
    
    # Generar hash para "secret" y comparar
    password = "secret"
    
    print(f"\n🔐 Generando nuevo hash para '{password}':")
    new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12))
    print(f"Nuevo hash: {new_hash.decode('utf-8')}")
    
    print(f"\n🔍 Comparando '{password}' con hash existente:")
    try:
        result = bcrypt.checkpw(password.encode('utf-8'), test_hash.encode('utf-8'))
        print(f"Resultado: {result}")
        
        if result:
            print("✅ La contraseña 'secret' coincide con el hash")
        else:
            print("❌ La contraseña 'secret' NO coincide con el hash")
            
    except Exception as e:
        print(f"❌ Error en checkpw: {e}")

def check_table_structure():
    """Verificar estructura de la tabla usuarios"""
    print("\n" + "="*60)
    print("🗄️  ESTRUCTURA DE LA TABLA USUARIOS")
    print("="*60)
    
    connection = None
    cursor = None
    
    try:
        connection = Database.get_connection()
        if not connection:
            print("❌ No se pudo obtener conexión")
            return
        
        cursor = connection.cursor()
        
        # Verificar estructura de la tabla
        cursor.execute("""
            SELECT column_name, data_type, character_maximum_length, 
                is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'usuarios'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        if columns:
            print(f"✅ Tabla 'usuarios' encontrada con {len(columns)} columnas:\n")
            
            for col in columns:
                print(f"  {col[0]}:")
                print(f"    Tipo: {col[1]}")
                if col[2]:
                    print(f"    Longitud máx: {col[2]}")
                print(f"    Nullable: {col[3]}")
                if col[4]:
                    print(f"    Valor por defecto: {col[4]}")
                print()
        else:
            print("❌ Tabla 'usuarios' no encontrada")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if cursor:
            cursor.close()
        if connection:
            Database.return_connection(connection)

def create_test_user():
    """Crear un usuario de prueba con contraseña simple"""
    print("\n" + "="*60)
    print("👤 CREANDO USUARIO DE PRUEBA")
    print("="*60)
    
    connection = None
    cursor = None
    
    try:
        connection = Database.get_connection()
        if not connection:
            print("❌ No se pudo obtener conexión")
            return
        
        cursor = connection.cursor()
        
        # Crear usuario de prueba con contraseña simple
        test_user = "testuser"
        test_password = "test123"
        test_email = "test@example.com"
        test_name = "Usuario de Prueba"
        
        print(f"Creando usuario: {test_user}")
        print(f"Contraseña: {test_password}")
        print(f"Email: {test_email}")
        
        # Verificar si ya existe
        cursor.execute("SELECT id FROM usuarios WHERE username = %s", (test_user,))
        if cursor.fetchone():
            print("⚠️ El usuario de prueba ya existe")
        else:
            # Crear usuario
            cursor.execute("""
                INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol, activo)
                VALUES (%s, %s, %s, %s, 'CAJERO', true)
            """, (test_user, test_password, test_name, test_email))
            
            connection.commit()
            print("✅ Usuario de prueba creado exitosamente")
            
            print(f"\n🔐 Credenciales de prueba:")
            print(f"  Usuario: {test_user}")
            print(f"  Contraseña: {test_password}")
            
    except Exception as e:
        print(f"❌ Error creando usuario: {e}")
        if connection:
            connection.rollback()
    finally:
        if cursor:
            cursor.close()
        if connection:
            Database.return_connection(connection)

if __name__ == "__main__":
    print("🚀 DIAGNÓSTICO COMPLETO DEL SISTEMA DE AUTENTICACIÓN")
    print("="*60)
    
    # 1. Verificar hash bcrypt
    debug_hash_comparison()
    
    # 2. Obtener usuario de la BD
    user_data = get_user_from_db("admin")
    
    # 3. Probar bcrypt directamente
    test_bcrypt_directly()
    
    # 4. Verificar estructura de tabla
    check_table_structure()
    
    # 5. Crear usuario de prueba
    create_test_user()
    
    print("\n" + "="*60)
    print("🎯 DIAGNÓSTICO COMPLETADO")
    print("="*60)