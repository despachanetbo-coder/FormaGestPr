# Archivo: utils/unsxx_converter.py
from typing import Dict, Any, Optional, Tuple
import logging
import re

logger = logging.getLogger(__name__)

class UNSXXConverter:
    """Conversor de datos UNSXX a formato estándar de programas - ACTUALIZADO"""
    
    # Mapeo de abreviaturas UNSXX (actualizado)
    NIVELES_ABREV = {
        "Diplomado": "DIP",
        "Especialidad": "ESP", 
        "Maestría": "MSC",
        "Doctorado": "PHD",
        "Certificación": "CER",
        "Curso": "CUR",
        "Taller": "TAL",
        "Pregrado": "PRE",
        "Capacitación": "CAP"
    }
    
    # Mapeo inverso (abreviatura → nombre)
    ABREV_NIVELES = {v: k for k, v in NIVELES_ABREV.items()}
    
    # Mapeo de carreras (abreviatura → nombre)
    CARRERAS_ABREV = {
        "BIO": "Bioquímica",
        "ODO": "Odontología",
        "ENF": "Enfermería",
        "MED": "Medicina",
        "LBC": "Laboratorio Clínico",
        "FIS": "Fisioterapia",
        "CIV": "Ing. Civil",
        "AGR": "Ing. Agronómica",
        "INF": "Ing. Informática",
        "MEC": "Ing. Mecánica",
        "MIN": "Ing. Minas",
        "ELE": "Ing. Electromecánica",
        "EDU": "Ciencias Educación",
        "CON": "Contaduría Pública",
        "DER": "Derecho",
        "COM": "Comunicación",
        "ADM": "Administración",
        "PSI": "Psicología",
        "SAP": "Salud Pública",
        "GFM": "Gestión Farmacia",
        "GEN": "General"  # Por defecto
    }
    
    # Mapeo inverso (nombre → abreviatura)
    CARRERAS_NOMBRES = {v: k for k, v in CARRERAS_ABREV.items()}
    
    # Números romanos hasta 20
    NUMEROS_ROMANOS = {
        1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V',
        6: 'VI', 7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X',
        11: 'XI', 12: 'XII', 13: 'XIII', 14: 'XIV', 15: 'XV',
        16: 'XVI', 17: 'XVII', 18: 'XVIII', 19: 'XIX', 20: 'XX'
    }
    
    # Mapeo inverso (romano → número)
    ROMANOS_NUMEROS = {v: k for k, v in NUMEROS_ROMANOS.items()}
    
    @staticmethod
    def convertir_unsxx_a_programa(unsxx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir datos del overlay UNSXX a formato estándar de programa
        
        Args:
            unsxx_data: Datos del formulario UNSXX (nuevo formato)
        
        Returns:
            Dict con datos convertidos al formato estándar
        """
        try:
            # Mapear estado UNSXX a estado estándar
            estado_unsxx = unsxx_data.get('estado', 'PLANIFICADO').upper()
            estado_estandar = 'PLANIFICADO'  # Por defecto
            
            if estado_unsxx == 'PRE INSCRIPCIÓN' or estado_unsxx == 'INSCRIPCIONES ABIERTAS':
                estado_estandar = 'PLANIFICADO'
            elif estado_unsxx == 'EN CURSO':
                estado_estandar = 'EN_CURSO'
            elif estado_unsxx == 'CONCLUIDO':
                estado_estandar = 'FINALIZADO'
            elif estado_unsxx == 'CANCELADO' or estado_unsxx == 'SUSPENDIDO':
                estado_estandar = 'CANCELADO'
            
            # Calcular costo de inscripción como 10% del costo total
            costo_total = unsxx_data.get('costo_total', 0)
            costo_inscripcion = round(costo_total * 0.10, 2) if costo_total > 0 else 0
            
            # Preparar datos estándar
            programa_data = {
                'codigo': unsxx_data.get('codigo', ''),
                'nombre': unsxx_data.get('nombre', ''),
                'descripcion': unsxx_data.get('descripcion', ''),
                'duracion_meses': unsxx_data.get('duracion_meses', 24),
                'horas_totales': unsxx_data.get('horas_totales', 1200),
                'costo_total': costo_total,
                'costo_matricula': unsxx_data.get('costo_matricula', 0),
                'costo_inscripcion': costo_inscripcion,
                'costo_mensualidad': unsxx_data.get('costo_por_cuota', 0),
                'numero_cuotas': unsxx_data.get('numero_cuotas', 10),
                'cupos_maximos': unsxx_data.get('cupos_maximos', 30),
                'cupos_inscritos': unsxx_data.get('cupos_inscritos', 0),
                'estado': estado_estandar,
                'fecha_inicio': unsxx_data.get('fecha_inicio'),
                'fecha_fin': unsxx_data.get('fecha_fin'),
                'docente_coordinador_id': unsxx_data.get('docente_coordinador_id'),
                'promocion_descuento': 0,  # Por defecto
                'promocion_descripcion': '',
                'promocion_valido_hasta': None
            }
            
            # Agregar metadatos UNSXX como JSON en descripción extendida
            descripcion_extendida = programa_data['descripcion'] + "\n\n"
            descripcion_extendida += f"=== METADATOS UNSXX ===\n"
            descripcion_extendida += f"• Nivel: {unsxx_data.get('nivel_academico', '')}\n"
            descripcion_extendida += f"• Carrera/Programa: {unsxx_data.get('carrera_programa', '')}\n"
            descripcion_extendida += f"• Modalidad: VIRTUAL\n"  # Siempre virtual
            descripcion_extendida += f"• Año Académico: {unsxx_data.get('anio_academico', '')}\n"
            descripcion_extendida += f"• Versión: {unsxx_data.get('version', '')}\n"
            descripcion_extendida += f"• Créditos: {unsxx_data.get('creditos_academicos', '')}\n"
            descripcion_extendida += f"• Código UNSXX: {unsxx_data.get('codigo', '')}"
            
            programa_data['descripcion'] = descripcion_extendida
            
            logger.info(f"✅ Datos UNSXX convertidos: {programa_data['codigo']}")
            return programa_data
            
        except Exception as e:
            logger.error(f"Error convirtiendo datos UNSXX: {e}")
            return {}
    
    @staticmethod
    def convertir_programa_a_unsxx(programa_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir datos de programa estándar a formato UNSXX para el overlay
        
        Args:
            programa_data: Datos del programa estándar
        
        Returns:
            Dict con datos convertidos al formato UNSXX
        """
        try:
            # Extraer código UNSXX
            codigo = programa_data.get('codigo', '')
            
            # Extraer metadatos de la descripción si existen
            descripcion = programa_data.get('descripcion', '')
            
            # Intentar extraer información del código UNSXX
            nivel_extraido = None
            carrera_extraida = None
            año_extraido = None
            version_extraida = None
            
            if codigo:
                partes = codigo.split('-')
                if len(partes) >= 4:
                    # Formato: NIVEL-CARRERA-AÑO-VERSION
                    nivel_abrev = partes[0]
                    carrera_abrev = partes[1]
                    año_str = partes[2]
                    version_romana = '-'.join(partes[3:])  # Por si hay guiones en la versión
                    
                    # Convertir a valores legibles
                    nivel_extraido = UNSXXConverter.ABREV_NIVELES.get(nivel_abrev, nivel_abrev)
                    carrera_extraida = UNSXXConverter.CARRERAS_ABREV.get(carrera_abrev, carrera_abrev)
                    año_extraido = int(año_str) if año_str.isdigit() else año_str
                    version_extraida = version_romana
            
            # Extraer descripción básica (sin metadatos UNSXX)
            descripcion_basica = descripcion
            if "=== METADATOS UNSXX ===" in descripcion:
                partes = descripcion.split("=== METADATOS UNSXX ===")
                descripcion_basica = partes[0].strip()
            
            from datetime import datetime
            año_hoy = datetime.now().year
            
            unsxx_data = {
                'codigo': codigo,
                'nombre': programa_data.get('nombre', ''),
                'descripcion': descripcion_basica,
                'nombre_activo': True,
                
                # Valores por defecto o extraídos del código
                'nivel_academico': nivel_extraido or "Maestría",
                'carrera_programa': carrera_extraida or "Ing. Informática",
                'anio_academico': año_extraido or año_hoy,
                'version': version_extraida or "I",
                
                # Datos del programa
                'duracion_meses': programa_data.get('duracion_meses', 24),
                'horas_totales': programa_data.get('horas_totales', 1200),
                'creditos_academicos': 60,
                'estado': programa_data.get('estado', 'PLANIFICADO'),
                'cupos_maximos': programa_data.get('cupos_maximos', 30),
                'cupos_inscritos': programa_data.get('cupos_inscritos', 0),
                'costo_total': float(programa_data.get('costo_total', 5000)),
                'costo_matricula': float(programa_data.get('costo_matricula', 200)),
                'numero_cuotas': programa_data.get('numero_cuotas', 10),
                'costo_por_cuota': float(programa_data.get('costo_mensualidad', 500)),
                'fecha_inicio': programa_data.get('fecha_inicio'),
                'fecha_fin': programa_data.get('fecha_fin'),
                'modo': 'editar',
                'id': programa_data.get('id'),
                
                # Campos eliminados (para compatibilidad)
                'facultad': '',  # Eliminado
                'modalidad': 'VIRTUAL',  # Fijo
                'facultad_abreviatura': '',
                'modalidad_abreviatura': 'VIR',
                'nivel_abreviatura': '',
                'carrera_abreviatura': '',
                'institucion': 'UNSXX',
                'docente_coordinador_id': None
            }
            
            logger.info(f"✅ Datos convertidos a UNSXX para: {codigo}")
            return unsxx_data
            
        except Exception as e:
            logger.error(f"Error convirtiendo a UNSXX: {e}")
            return {}
    
    @staticmethod
    def parsear_codigo_unsxx(codigo: str) -> Optional[Dict[str, Any]]:
        """
        Parsear un código UNSXX para extraer sus componentes
        
        Args:
            codigo: Código UNSXX en formato NIVEL-CARRERA-AÑO-VERSION
        
        Returns:
            Dict con componentes parseados o None si no es válido
        """
        try:
            if not codigo or '-' not in codigo:
                return None
            
            partes = codigo.split('-')
            if len(partes) < 4:
                return None
            
            nivel_abrev = partes[0]
            carrera_abrev = partes[1]
            año_str = partes[2]
            version_romana = '-'.join(partes[3:])
            
            # Validar año
            año = None
            if año_str.isdigit():
                año = int(año_str)
                # Si el año tiene 2 dígitos, asumir siglo 21
                if año < 100:
                    año = 2000 + año
            else:
                # Intentar extraer año del texto
                import re
                numeros = re.findall(r'\d+', año_str)
                if numeros:
                    año = int(numeros[0])
            
            # Convertir versión romana a número
            version_num = UNSXXConverter.ROMANOS_NUMEROS.get(version_romana, 1)
            
            return {
                'nivel_abreviatura': nivel_abrev,
                'nivel': UNSXXConverter.ABREV_NIVELES.get(nivel_abrev, nivel_abrev),
                'carrera_abreviatura': carrera_abrev,
                'carrera': UNSXXConverter.CARRERAS_ABREV.get(carrera_abrev, carrera_abrev),
                'anio': año,
                'version_romana': version_romana,
                'version_numero': version_num,
                'modalidad': 'VIRTUAL',
                'modalidad_abrev': 'VIR',
                'codigo_completo': codigo,
                'longitud': len(codigo)
            }
            
        except Exception as e:
            logger.error(f"Error parseando código UNSXX {codigo}: {e}")
            return None
    
    @staticmethod
    def generar_codigo_unsxx(nivel: str, carrera: str, año: int, version: int = 1) -> str:
        """
        Generar código UNSXX a partir de sus componentes
        
        Args:
            nivel: Nivel académico (ej: "Maestría")
            carrera: Nombre de la carrera (ej: "Ing. Informática")
            año: Año académico (ej: 2024)
            version: Número de versión (1-20)
        
        Returns:
            Código UNSXX generado
        """
        try:
            # Obtener abreviaturas
            nivel_abrev = UNSXXConverter.NIVELES_ABREV.get(nivel, "GEN")
            
            # Buscar abreviatura de carrera
            carrera_abrev = "GEN"
            for abrev, nombre in UNSXXConverter.CARRERAS_ABREV.items():
                if nombre.lower() == carrera.lower():
                    carrera_abrev = abrev
                    break
            
            # Si no se encuentra, usar las primeras 3 letras
            if carrera_abrev == "GEN" and carrera:
                carrera_abrev = carrera[:3].upper()
            
            # Obtener versión romana
            version_romana = UNSXXConverter.NUMEROS_ROMANOS.get(version, "I")
            
            # Formar código
            codigo = f"{nivel_abrev}-{carrera_abrev}-{año}-{version_romana}"
            
            # Si excede 20 caracteres, usar año de 2 dígitos
            if len(codigo) > 20:
                año_corto = str(año)[-2:]  # Últimos 2 dígitos
                codigo = f"{nivel_abrev}-{carrera_abrev}-{año_corto}-{version_romana}"
            
            return codigo
            
        except Exception as e:
            logger.error(f"Error generando código UNSXX: {e}")
            return "GEN-GEN-0000-I"
    
    @staticmethod
    def extraer_metadatos_de_descripcion(descripcion: str) -> Dict[str, Any]:
        """
        Extraer metadatos UNSXX de la descripción del programa
        
        Args:
            descripcion: Descripción que puede contener metadatos UNSXX
        
        Returns:
            Dict con metadatos extraídos
        """
        try:
            if "=== METADATOS UNSXX ===" not in descripcion:
                return {}
            
            partes = descripcion.split("=== METADATOS UNSXX ===")
            if len(partes) < 2:
                return {}
            
            metadatos_texto = partes[1]
            metadatos = {}
            
            # Extraer líneas individuales
            lineas = metadatos_texto.strip().split('\n')
            for linea in lineas:
                if ':' in linea or '•' in linea:
                    # Limpiar la línea
                    linea_limpia = linea.replace('•', '').strip()
                    if ':' in linea_limpia:
                        key_value = linea_limpia.split(':', 1)
                        if len(key_value) == 2:
                            clave = key_value[0].strip().lower()
                            valor = key_value[1].strip()
                            metadatos[clave] = valor
            
            return metadatos
            
        except Exception as e:
            logger.error(f"Error extrayendo metadatos: {e}")
            return {}
    
    @staticmethod
    def validar_codigo_unsxx(codigo: str) -> Tuple[bool, str]:
        """
        Validar un código UNSXX
        
        Args:
            codigo: Código a validar
        
        Returns:
            Tuple (valido, mensaje_error)
        """
        try:
            # Verificar que no esté vacío
            if not codigo or not codigo.strip():
                return False, "El código no puede estar vacío"
            
            # Verificar longitud máxima
            if len(codigo) > 20:
                return False, f"El código excede los 20 caracteres permitidos (tiene {len(codigo)})"
            
            # Verificar formato básico
            if '-' not in codigo:
                return False, "El código debe seguir el formato NIVEL-CARRERA-AÑO-VERSION"
            
            # Verificar número de partes
            partes = codigo.split('-')
            if len(partes) < 4:
                return False, "Código incompleto. Formato esperado: NIVEL-CARRERA-AÑO-VERSION"
            
            # Verificar que el año sea numérico
            año_str = partes[2]
            if not año_str.isdigit():
                return False, f"El año '{año_str}' no es válido. Debe ser un número"
            
            # Verificar que la versión sea válida
            version_romana = '-'.join(partes[3:])
            if version_romana not in UNSXXConverter.ROMANOS_NUMEROS:
                return False, f"La versión '{version_romana}' no es válida. Use números romanos I-XX"
            
            return True, "Código válido"
            
        except Exception as e:
            return False, f"Error validando código: {str(e)}"

