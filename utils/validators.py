# Archivo: utils/validators.py
import os
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple

class Validators:
    """Clase para validaciones reutilizables"""
    
    @staticmethod
    def validar_email(email: Optional[str]) -> Tuple[bool, str]:
        """Validar formato de email"""
        if not email or email.strip() == "":
            return True, ""  # Email opcional
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(pattern, email):
            return True, ""
        return False, "El formato del email no es válido"
    
    @staticmethod
    def validar_telefono(telefono: Optional[str]) -> Tuple[bool, str]:
        """Validar formato de teléfono"""
        if not telefono or telefono.strip() == "":
            return True, ""  # Teléfono opcional
        
        # Patrón básico para teléfonos (ajustar según país)
        if re.match(r'^[\d\s\-\+\(\)]{7,20}$', telefono):
            return True, ""
        return False, "El formato del teléfono no es válido"
    
    @staticmethod
    def validar_fecha_nacimiento(fecha_str: str) -> Tuple[bool, str, Optional[date]]:
        """Validar fecha de nacimiento"""
        if not fecha_str or fecha_str.strip() == "":
            return True, "", None
        
        try:
            fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            hoy = date.today()
            
            # Verificar que no sea fecha futura
            if fecha > hoy:
                return False, "La fecha de nacimiento no puede ser futura", None
            
            # Verificar edad mínima (ej: 16 años)
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            if edad < 16:
                return False, "El estudiante debe tener al menos 16 años", None
            
            # Verificar edad máxima razonable (ej: 120 años)
            if edad > 120:
                return False, "La fecha de nacimiento no es válida", None
            
            return True, "", fecha
        except ValueError:
            return False, "Formato de fecha inválido. Use YYYY-MM-DD", None
    
    @staticmethod
    def validar_ci(ci_numero: Optional[str]) -> Tuple[bool, str]:
        """Validar formato de cédula de identidad"""
        if not ci_numero or ci_numero.strip() == "":
            return False, "El número de CI es requerido"
        
        # Eliminar espacios y guiones
        ci_limpio = re.sub(r'[\s\-]', '', ci_numero)
        
        # Verificar que sean solo dígitos
        if not ci_limpio.isdigit():
            return False, "El CI debe contener solo números"
        
        # Verificar longitud (ajustar según país)
        if len(ci_limpio) < 5 or len(ci_limpio) > 15:
            return False, f"El CI debe tener entre 5 y 15 dígitos"
        
        return True, ci_limpio
    
    @staticmethod
    def validar_texto_obligatorio(campo: str, valor: Optional[str], nombre_campo: str) -> Tuple[bool, str]:
        """Validar que un campo de texto sea obligatorio y válido"""
        if not valor or valor.strip() == "":
            return False, f"El campo {nombre_campo} es requerido"
        
        if len(valor.strip()) < 2:
            return False, f"El campo {nombre_campo} debe tener al menos 2 caracteres"
        
        # Verificar caracteres válidos (letras, espacios, algunos símbolos)
        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s\-\'\.]+$', valor.strip()):
            return False, f"El campo {nombre_campo} contiene caracteres inválidos"
        
        return True, valor.strip()
    
    @staticmethod
    def validar_texto_opcional(campo: str, valor: str, max_length: int = 500) -> Tuple[bool, str]:
        """Validar campo de texto opcional"""
        if not valor or valor.strip() == "":
            return True, ""
        
        if len(valor.strip()) > max_length:
            return False, f"El campo excede los {max_length} caracteres permitidos"
        
        return True, valor.strip()
    
    @staticmethod
    def validar_booleano(valor) -> Tuple[bool, Optional[bool]]:
        """Validar valor booleano"""
        if valor is None:
            return True, None
        
        if isinstance(valor, bool):
            return True, valor
        
        if isinstance(valor, str):
            valor_lower = valor.lower()
            if valor_lower in ['true', '1', 'yes', 'si', 'sí']:
                return True, True
            elif valor_lower in ['false', '0', 'no']:
                return True, False
        
        if isinstance(valor, int):
            if valor in [0, 1]:
                return True, bool(valor)
        
        return False, None
    
    @staticmethod
    def validar_path(path: Optional[str], permitir_relativas: bool = True, permitir_archivos: bool = True) -> Tuple[bool, str]:
        """
        Validar formato de ruta de archivo en Windows

        Args:
            path: Ruta a validar
            permitir_relativas: Si permite rutas relativas
            permitir_archivos: Si permite rutas a archivos (no solo directorios)

        Returns:
            Tuple[bool, str]: (válido, mensaje_de_error_o_path_limpio)
        """
        if not path or path.strip() == "":
            return True, ""

        # Limpiar espacios
        path_limpio = path.strip()

        # Caracteres prohibidos en nombres de archivo en Windows
        caracteres_prohibidos = ['<', '>', ':', '"', '|', '?', '*']
        for char in caracteres_prohibidos:
            if char in path_limpio:
                return False, f"La ruta contiene el carácter prohibido '{char}'"

        # Verificar longitud máxima
        if len(path_limpio) > 259:
            return False, "La ruta excede la longitud máxima permitida en Windows (260 caracteres)"

        # Verificar que no termine con espacio o punto
        if path_limpio.endswith(' ') or path_limpio.endswith('.'):
            return False, "La ruta no puede terminar con espacio o punto"

        # Verificar nombres reservados de Windows
        nombres_reservados = [
            'CON', 'PRN', 'AUX', 'NUL', 
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]

        # Extraer cada componente del path para verificar nombres reservados
        componentes = [comp for comp in path_limpio.split('\\') if comp]
        for componente in componentes:
            # Verificar si es un nombre reservado (sin extensión)
            nombre_sin_ext = os.path.splitext(componente)[0].upper()
            if nombre_sin_ext in nombres_reservados:
                return False, f"'{componente}' contiene un nombre reservado de Windows"

        # Patrones de validación
        patron_absoluto = r'^[A-Za-z]:\\(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$'
        patron_unc = r'^\\\\[^\\/:*?"<>|\r\n]+(?:\\[^\\/:*?"<>|\r\n]+)*$'
        patron_relativo = r'^(?:[^\\/:*?"<>|\r\n]+\\)*[^\\/:*?"<>|\r\n]*$'

        # Validar según el tipo de ruta
        es_absoluto = re.match(patron_absoluto, path_limpio)
        es_unc = re.match(patron_unc, path_limpio)
        es_relativo = re.match(patron_relativo, path_limpio)

        if es_absoluto or es_unc:
            return True, path_limpio
        elif permitir_relativas and es_relativo:
            return True, path_limpio
        else:
            return False, "La ruta no tiene un formato válido para Windows"    
    
    @staticmethod
    def validar_url(url: Optional[str]) -> Tuple[bool, str]:
        """Validar formato de URL o ruta de archivo en Windows"""
        if not url or url.strip() == "":
            return True, ""
        
        url_str = url.strip()
        
        # Primero verificar si parece una URL web
        if url_str.startswith(('http://', 'https://', 'ftp://', 'file://')):
            pattern = r'^(https?|ftp|file)://[^\s/$.?#].[^\s]*$'
            if re.match(pattern, url_str, re.IGNORECASE):
                return True, url_str
            return False, "La URL no tiene un formato válido"
        
        # Si no es una URL web, asumimos que es una ruta de Windows
        # Llamar a la función de validación de path
        return Validators.validar_path(url_str)
