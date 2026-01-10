# generate_bcrypt_hash.py
import bcrypt
import sys

def generate_bcrypt_hash(password):
    """Genera un hash bcrypt para una contraseña"""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_bcrypt_hash(password, hashed_password):
    """Verifica una contraseña contra un hash bcrypt"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

if __name__ == "__main__":
    print("🔐 GENERADOR DE HASH BCRYPT")
    print("="*50)
    
    # Probar con "secret" (el hash que tienes actualmente)
    existing_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW"
    
    print(f"Hash existente en BD: {existing_hash[:30]}...")
    
    # Verificar a qué contraseña corresponde
    test_passwords = ["secret", "admin123", "admin", "password", "123456"]
    
    print("\n🔍 Verificando contraseñas para hash existente:")
    for pwd in test_passwords:
        try:
            if verify_bcrypt_hash(pwd, existing_hash):
                print(f"✅ El hash corresponde a la contraseña: '{pwd}'")
                break
        except:
            continue
    
    # Generar nuevo hash para admin123
    print("\n🔐 Generando nuevo hash para 'admin123':")
    new_hash = generate_bcrypt_hash("admin123")
    print(f"Hash bcrypt generado: {new_hash}")
    
    # Verificar que funciona
    if verify_bcrypt_hash("admin123", new_hash):
        print("✅ Verificación exitosa - el hash funciona para 'admin123'")
    
    # SQL para actualizar
    print("\n📝 SQL para actualizar base de datos:")
    print(f"UPDATE usuarios SET password_hash = '{new_hash}' WHERE username = 'admin';")
    
    # Opción 2: Usar contraseña "secret" temporalmente
    print("\n⚠️  SOLUCIÓN TEMPORAL:")
    print("   Puedes usar la contraseña: 'secret' (sin comillas)")
    print("   Usuario: admin")
    print("   Contraseña: secret")