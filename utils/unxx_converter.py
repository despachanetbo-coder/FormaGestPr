# utils/unxx_converter.py

import logging
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
from decimal import Decimal, getcontext, ROUND_HALF_UP

logger = logging.getLogger(__name__)

class UNSXXConverter:
    """
    Convertidor entre formato estándar de la base de datos y formato UNSXX
    para programas académicos.
    """
    
    # Mapeo de estados
    ESTADOS_MAP = {
        'PLANIFICADO': 'PLANIFICADO',
        'INSCRIPCIONES': 'INSCRIPCIONES',
        'EN_CURSO': 'EN_CURSO',
        'CONCLUIDO': 'CONCLUIDO',
        'CANCELADO': 'CANCELADO',
        'ACTIVO': 'EN_CURSO',  # Alias
        'FINALIZADO': 'CONCLUIDO',  # Alias
    }
    
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
    
    def convertir_unsxx_a_programa(self, unsxx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir datos de formato UNSXX a formato estándar de la base de datos.
        CORREGIDO: Manejar correctamente decimal.Decimal vs float
        """
        programa_data = unsxx_data.copy() if unsxx_data else {}
        
        try:
            # IMPORTANTE: Convertir TODOS los valores decimales a float
            # antes de cualquier operación matemática
            
            # Costos - convertir a float
            campos_decimales = ['costo_total', 'costo_matricula', 'costo_inscripcion', 'costo_mensualidad']
            for campo in campos_decimales:
                if campo in unsxx_data and unsxx_data[campo] is not None:
                    valor = unsxx_data[campo]
                    # Convertir Decimal a float
                    if hasattr(valor, 'to_decimal') or hasattr(valor, 'as_tuple'):
                        valor = float(str(valor))
                    programa_data[campo] = float(valor)
                else:
                    programa_data[campo] = 0.0
            
            # Número de cuotas - convertir a int
            if 'numero_cuotas' in unsxx_data:
                programa_data['numero_cuotas'] = int(unsxx_data['numero_cuotas'])
            else:
                programa_data['numero_cuotas'] = 0
            
            # Recalcular costo_mensualidad si es necesario
            if programa_data['costo_total'] > 0 and programa_data['numero_cuotas'] > 0:
                programa_data['costo_mensualidad'] = round(
                    programa_data['costo_total'] / programa_data['numero_cuotas'], 
                    2
                )
            
            # Campos numéricos enteros
            campos_enteros = ['duracion_meses', 'horas_totales', 'cupos_maximos', 'cupos_inscritos']
            for campo in campos_enteros:
                if campo in unsxx_data and unsxx_data[campo] is not None:
                    programa_data[campo] = int(unsxx_data[campo])
                else:
                    programa_data[campo] = 0
            
            # Estado - mapear a valores válidos de BD
            if 'estado' in unsxx_data:
                estado = unsxx_data['estado']
                programa_data['estado'] = self.ESTADOS_MAP.get(estado, 'PLANIFICADO')
            
            # Fechas - mantener formato string
            if 'fecha_inicio' in unsxx_data and unsxx_data['fecha_inicio']:
                programa_data['fecha_inicio'] = str(unsxx_data['fecha_inicio'])
            if 'fecha_fin' in unsxx_data and unsxx_data['fecha_fin']:
                programa_data['fecha_fin'] = str(unsxx_data['fecha_fin'])
            
            # Docente coordinador
            if 'docente_coordinador_id' in unsxx_data:
                programa_data['docente_coordinador_id'] = unsxx_data['docente_coordinador_id']
            
            # Nombre y descripción
            if 'nombre' in unsxx_data:
                programa_data['nombre'] = str(unsxx_data['nombre'])
            if 'descripcion' in unsxx_data:
                programa_data['descripcion'] = str(unsxx_data['descripcion'])
            
            # Código
            if 'codigo' in unsxx_data:
                programa_data['codigo'] = str(unsxx_data['codigo'])
            
            logger.info(f"✅ Datos convertidos a formato estándar para: {programa_data.get('codigo', 'N/A')}")
            
        except Exception as e:
            logger.error(f"Error convirtiendo datos UNSXX: {e}")
            import traceback
            traceback.print_exc()
            # Devolver datos originales con valores por defecto para no romper
            for campo in ['costo_total', 'costo_matricula', 'costo_inscripcion', 'costo_mensualidad']:
                if campo not in programa_data or programa_data[campo] is None:
                    programa_data[campo] = 0.0
        
        return programa_data
    
    def convertir_programa_a_unsxx(self, programa_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertir datos de programa (formato BD) a formato UNSXX.
        Este método debe ser compatible con lo que espera ProgramaOverlay.cargar_datos()
        """
        unsxx_data = programa_data.copy() if programa_data else {}
        
        try:
            # Extraer componentes del código UNSXX (ej: DIP-INF-2025-I)
            codigo = programa_data.get('codigo', '')
            if codigo and isinstance(codigo, str):
                partes = codigo.split('-')
                if len(partes) >= 4:
                    # Mapear abreviatura a nombre completo si es posible
                    from view.overlays.programa_overlay import ProgramaOverlay
                    nivel_abrev = partes[0]
                    nivel_completo = next(
                        (k for k, v in ProgramaOverlay.NIVELES_ACADEMICOS.items() if v == nivel_abrev),
                        nivel_abrev
                    )
                    unsxx_data['nivel_academico'] = nivel_completo
                    
                    carrera_abrev = partes[1]
                    carrera_completa = next(
                        (nombre for nombre, abrev in ProgramaOverlay.CARRERAS_UNSXX if abrev == carrera_abrev),
                        carrera_abrev
                    )
                    unsxx_data['carrera_programa'] = carrera_completa
                    
                    # Año
                    try:
                        año = int(partes[2]) if len(partes[2]) == 4 else int("20" + partes[2])
                        unsxx_data['anio_academico'] = año
                    except:
                        unsxx_data['anio_academico'] = datetime.now().year
                    
                    # Versión (número romano)
                    if len(partes) >= 4:
                        unsxx_data['version'] = partes[3]
            
            # Mapear campos específicos
            campo_mapeos = {
                'nombre': 'nombre',
                'descripcion': 'descripcion',
                'duracion_meses': 'duracion_meses',
                'horas_totales': 'horas_totales',
                'cupos_maximos': 'cupos_maximos',
                'cupos_inscritos': 'cupos_inscritos',
                'fecha_inicio': 'fecha_inicio',
                'fecha_fin': 'fecha_fin',
                'estado': 'estado',
            }
            
            for campo_std, campo_unsxx in campo_mapeos.items():
                if campo_std in programa_data:
                    unsxx_data[campo_unsxx] = programa_data[campo_std]
            
            # Manejar costos
            unsxx_data['costo_total'] = float(programa_data.get('costo_total', 0))
            unsxx_data['costo_matricula'] = float(programa_data.get('costo_matricula', 0))
            unsxx_data['costo_inscripcion'] = float(programa_data.get('costo_inscripcion', 0))
            unsxx_data['costo_mensualidad'] = float(programa_data.get('costo_mensualidad', 0))
            unsxx_data['numero_cuotas'] = int(programa_data.get('numero_cuotas', 0))
            
            # Créditos (opcional)
            if 'creditos' in programa_data:
                unsxx_data['creditos_academicos'] = int(programa_data['creditos'])
            
            # Docente coordinador
            if 'docente_coordinador_id' in programa_data:
                unsxx_data['docente_coordinador_id'] = programa_data['docente_coordinador_id']
            
            # Campos adicionales UNSXX
            unsxx_data['institucion'] = 'UNSXX'
            unsxx_data['modalidad'] = 'VIRTUAL'  # Valor por defecto
            unsxx_data['modalidad_abreviatura'] = 'VIR'
            
            logger.info(f"✅ Datos convertidos a UNSXX para: {codigo}")
            
        except Exception as e:
            logger.error(f"Error convirtiendo a UNSXX: {e}")
            import traceback
            traceback.print_exc()
        
        return unsxx_data
    
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

