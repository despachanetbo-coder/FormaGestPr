# utils/security.py
import hashlib
import hmac
import secrets
import base64
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt

logger = logging.getLogger(__name__)

class SecurityUtils:
    """Utilidades de seguridad para la aplicación"""
    
    # Coste para bcrypt (ajustar según necesidades de rendimiento)
    BCRYPT_COST = 12
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hashea una contraseña usando bcrypt
        
        Args:
            password: Contraseña en texto plano
            
        Returns:
            Hash de la contraseña
        """
        try:
            # Generar salt y hashear
            salt = bcrypt.gensalt(rounds=SecurityUtils.BCRYPT_COST)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"❌ Error hasheando contraseña: {e}")
            raise
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verifica una contraseña contra su hash
        
        Args:
            password: Contraseña en texto plano
            hashed_password: Hash almacenado
            
        Returns:
            True si la contraseña es válida
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed_password.encode('utf-8')
            )
        except Exception as e:
            logger.error(f"❌ Error verificando contraseña: {e}")
            return False
    
    @staticmethod
    def generate_random_token(length: int = 32) -> str:
        """
        Genera un token aleatorio seguro
        
        Args:
            length: Longitud del token en bytes
            
        Returns:
            Token en formato URL-safe base64
        """
        random_bytes = secrets.token_bytes(length)
        return base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    
    @staticmethod
    def generate_session_token(user_id: int, username: str) -> Dict[str, str]:
        """
        Genera un token de sesión para un usuario
        
        Args:
            user_id: ID del usuario
            username: Nombre de usuario
            
        Returns:
            Dict con token y timestamp
        """
        # Crear payload
        timestamp = datetime.utcnow().isoformat()
        payload = f"{user_id}:{username}:{timestamp}"
        
        # Crear HMAC usando una clave secreta
        secret_key = "your-secret-key-here"  # En producción, usar variable de entorno
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Combinar payload y firma
        token = f"{payload}:{signature}"
        encoded_token = base64.urlsafe_b64encode(token.encode('utf-8')).decode('utf-8')
        
        return {
            'token': encoded_token,
            'timestamp': timestamp,
            'expires_at': (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
    
    @staticmethod
    def validate_session_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Valida un token de sesión
        
        Args:
            token: Token a validar
            
        Returns:
            Dict con datos del usuario si es válido, None si no
        """
        try:
            # Decodificar token
            decoded_token = base64.urlsafe_b64decode(token).decode('utf-8')
            
            # Separar componentes
            parts = decoded_token.split(':')
            if len(parts) != 4:
                return None
            
            user_id, username, timestamp, signature = parts
            
            # Verificar firma
            secret_key = "your-secret-key-here"  # En producción, usar variable de entorno
            payload = f"{user_id}:{username}:{timestamp}"
            expected_signature = hmac.new(
                secret_key.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(signature, expected_signature):
                return None
            
            # Verificar expiración (24 horas)
            token_time = datetime.fromisoformat(timestamp)
            if datetime.utcnow() - token_time > timedelta(hours=24):
                return None
            
            return {
                'user_id': int(user_id),
                'username': username,
                'token_time': timestamp
            }
            
        except Exception as e:
            logger.error(f"❌ Error validando token: {e}")
            return None
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """
        Sanitiza entrada de usuario para prevenir inyecciones
        
        Args:
            input_string: String a sanitizar
            
        Returns:
            String sanitizado
        """
        if not input_string:
            return ""
        
        # Remover caracteres peligrosos
        dangerous_chars = ['<', '>', '"', "'", ';', '(', ')', '&', '|']
        sanitized = input_string
        
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        # Limitar longitud
        sanitized = sanitized[:500]
        
        return sanitized.strip()
    
    @staticmethod
    def generate_password_reset_token() -> str:
        """
        Genera un token para restablecimiento de contraseña
        
        Returns:
            Token seguro
        """
        return SecurityUtils.generate_random_token(48)
    
    @staticmethod
    def calculate_password_strength(password: str) -> Dict[str, Any]:
        """
        Calcula la fortaleza de una contraseña
        
        Args:
            password: Contraseña a evaluar
            
        Returns:
            Dict con puntuación y recomendaciones
        """
        score = 0
        feedback = []
        
        # Longitud
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("La contraseña debe tener al menos 8 caracteres")
        
        # Mayúsculas
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Agregue al menos una letra mayúscula")
        
        # Minúsculas
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Agregue al menos una letra minúscula")
        
        # Números
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Agregue al menos un número")
        
        # Caracteres especiales
        special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        if any(c in special_chars for c in password):
            score += 1
        else:
            feedback.append("Agregue al menos un carácter especial (!@#$% etc.)")
        
        # Determinar nivel
        if score >= 5:
            strength = "Muy fuerte"
            color = "#4CAF50"  # Verde
        elif score >= 4:
            strength = "Fuerte"
            color = "#8BC34A"  # Verde claro
        elif score >= 3:
            strength = "Moderada"
            color = "#FFC107"  # Amarillo
        elif score >= 2:
            strength = "Débil"
            color = "#FF9800"  # Naranja
        else:
            strength = "Muy débil"
            color = "#F44336"  # Rojo
        
        return {
            'score': score,
            'max_score': 5,
            'strength': strength,
            'color': color,
            'feedback': feedback,
            'is_acceptable': score >= 3
        }