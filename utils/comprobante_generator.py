# -*- coding: utf-8 -*-
# Archivo: utils/comprobante_generator.py
"""
Módulo para generar comprobantes de pago en formato para impresión térmica
Soporta impresoras Epson TM (térmicas) con ancho de 80mm (40-48 columnas)
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import os
import tempfile

logger = logging.getLogger(__name__)

class ComprobanteGenerator:
    """
    Generador de comprobantes de pago en formato texto para impresión térmica
    """
    
    # Ancho estándar para impresoras térmicas (42 columnas)
    ANCHO = 42
    
    @classmethod
    def generar_comprobante(cls, transaccion: Dict[str, Any], 
                            detalles: List[Dict[str, Any]],
                            inscripcion: Optional[Dict[str, Any]] = None) -> str:
        """
        Generar el texto del comprobante para impresión
        
        Args:
            transaccion: Datos de la transacción
            detalles: Lista de detalles (conceptos) de la transacción
            inscripcion: Datos de la inscripción (opcional)
            
        Returns:
            String con el formato del comprobante
        """
        lineas = []
        
        # ===== ENCABEZADO =====
        lineas.append(cls._centrar("=" * cls.ANCHO))
        lineas.append(cls._centrar("COMPROBANTE DE PAGO"))
        lineas.append(cls._centrar("=" * cls.ANCHO))
        lineas.append("")
        
        # ===== INFORMACIÓN DE LA INSTITUCIÓN =====
        lineas.append(cls._centrar("FORMA GEST PRO"))
        lineas.append(cls._centrar("Sistema de Gestión Académica"))
        lineas.append("")
        
        # ===== INFORMACIÓN DE LA TRANSACCIÓN =====
        lineas.append(cls._linea_separador())
        lineas.append(cls._centrar("DATOS DE LA TRANSACCIÓN"))
        lineas.append(cls._linea_separador())
        
        # Número de transacción
        num_trans = transaccion.get('numero_transaccion', 'N/A')
        lineas.append(cls._formatear_linea("N° Transacción:", num_trans))
        
        # Fecha y hora
        fecha_pago = transaccion.get('fecha_pago', '')
        if fecha_pago:
            if hasattr(fecha_pago, 'strftime'):
                fecha_str = fecha_pago.strftime('%d/%m/%Y')
            else:
                fecha_str = str(fecha_pago)[:10]
        else:
            fecha_str = 'N/A'
        
        hora_str = datetime.now().strftime('%H:%M:%S')
        lineas.append(cls._formatear_linea("Fecha:", f"{fecha_str} {hora_str}"))
        
        # ===== INFORMACIÓN DEL ESTUDIANTE =====
        lineas.append("")
        lineas.append(cls._linea_separador())
        lineas.append(cls._centrar("DATOS DEL ESTUDIANTE"))
        lineas.append(cls._linea_separador())
        
        # Nombre del estudiante
        nombre = cls._obtener_nombre_estudiante(transaccion)
        lineas.append(cls._formatear_linea("Estudiante:", nombre[:30]))
        
        # CI
        ci = transaccion.get('estudiante_ci', 'N/A')
        lineas.append(cls._formatear_linea("CI:", ci))
        
        # ===== INFORMACIÓN DEL PROGRAMA =====
        if transaccion.get('programa_nombre'):
            lineas.append("")
            lineas.append(cls._linea_separador())
            lineas.append(cls._centrar("PROGRAMA"))
            lineas.append(cls._linea_separador())
            
            programa = transaccion.get('programa_nombre', '')
            codigo = transaccion.get('programa_codigo', '')
            lineas.append(cls._formatear_linea("Programa:", f"{codigo} - {programa[:20]}"))
        
        # ===== DETALLE DE PAGOS =====
        lineas.append("")
        lineas.append(cls._linea_separador())
        lineas.append(cls._centrar("DETALLE DE PAGOS"))
        lineas.append(cls._linea_separador())
        
        # Encabezados de tabla
        lineas.append(cls._formatear_linea_detalle("Concepto", "Cant.", "P.Unit", "Subtotal"))
        lineas.append(cls._linea_punteada())
        
        # Detalles
        total = 0
        for detalle in detalles:
            concepto = detalle.get('concepto_nombre', 'Concepto')[:15]
            cantidad = detalle.get('cantidad', 1)
            precio = float(detalle.get('precio_unitario', 0))
            subtotal = float(detalle.get('subtotal', 0))
            total += subtotal
            
            lineas.append(cls._formatear_linea_detalle(
                concepto,
                str(cantidad),
                f"{precio:.2f}",
                f"{subtotal:.2f}"
            ))
            
            # Descripción adicional si existe
            descripcion = detalle.get('descripcion', '')
            if descripcion and len(descripcion) > 0 and descripcion != concepto:
                lineas.append(f"  {descripcion[:35]}")
        
        lineas.append(cls._linea_punteada())
        
        # ===== TOTALES =====
        monto_final = float(transaccion.get('monto_final', total))
        lineas.append(cls._formatear_linea("TOTAL Bs.:", f"{monto_final:.2f}", derecha=True))
        
        # Forma de pago
        forma_pago = transaccion.get('forma_pago', 'EFECTIVO')
        lineas.append(cls._formatear_linea("Forma de Pago:", forma_pago))
        
        # Número de comprobante si existe
        num_comprobante = transaccion.get('numero_comprobante')
        if num_comprobante:
            lineas.append(cls._formatear_linea("N° Comprobante:", num_comprobante))
        
        # ===== PIE DE PÁGINA =====
        lineas.append("")
        lineas.append(cls._linea_separador('='))
        lineas.append(cls._centrar("¡GRACIAS POR SU PAGO!"))
        lineas.append(cls._centrar("Este documento es un comprobante válido"))
        lineas.append(cls._centrar("Conserve para cualquier reclamo"))
        lineas.append(cls._linea_separador('='))
        
        # Espacio para firma
        lineas.append("")
        lineas.append(cls._centrar("_________________________"))
        lineas.append(cls._centrar("Firma Autorizada"))
        lineas.append("")
        lineas.append("")
        
        # Comando de corte para impresora térmica (ESC/POS)
        lineas.append("\x1B\x69")  # ESC i - corte parcial
        lineas.append("\x1B\x64\x03")  # ESC d 3 - avanzar 3 líneas
        
        return "\n".join(lineas)
    
    @classmethod
    def _centrar(cls, texto: str) -> str:
        """Centrar texto en el ancho de la impresora"""
        espacio = cls.ANCHO - len(texto)
        if espacio <= 0:
            return texto[:cls.ANCHO]
        izquierda = espacio // 2
        return " " * izquierda + texto
    
    @classmethod
    def _formatear_linea(cls, label: str, valor: str, derecha: bool = False) -> str:
        """Formatear línea con label y valor"""
        texto = f"{label} {valor}"
        if derecha:
            return texto.rjust(cls.ANCHO)
        return texto.ljust(cls.ANCHO)
    
    @classmethod
    def _formatear_linea_detalle(cls, concepto: str, cant: str, punit: str, subtotal: str) -> str:
        """Formatear línea de detalle con columnas fijas"""
        # Ajustar longitudes
        concepto = concepto[:15].ljust(15)
        cant = cant.rjust(5)
        punit = punit.rjust(8)
        subtotal = subtotal.rjust(8)
        return f"{concepto} {cant} {punit} {subtotal}"
    
    @classmethod
    def _linea_separador(cls, caracter: str = "-") -> str:
        """Generar línea separadora"""
        return caracter * cls.ANCHO
    
    @classmethod
    def _linea_punteada(cls) -> str:
        """Generar línea punteada"""
        return "-" * cls.ANCHO
    
    @classmethod
    def _obtener_nombre_estudiante(cls, transaccion: Dict) -> str:
        """Obtener nombre completo del estudiante"""
        nombre = transaccion.get('estudiante_nombre', '')
        apellido_p = transaccion.get('estudiante_apellido_paterno', '')
        apellido_m = transaccion.get('estudiante_apellido_materno', '')
        
        if nombre or apellido_p or apellido_m:
            return f"{nombre} {apellido_p} {apellido_m}".strip()
        
        return f"Estudiante ID: {transaccion.get('estudiante_id', 'N/A')}"
    
    @classmethod
    def imprimir(cls, texto: str, printer_name: Optional[str] = None) -> bool:
        """
        Enviar texto a la impresora

        Args:
            texto: Texto del comprobante
            printer_name: Nombre de la impresora (None para usar predeterminada)

        Returns:
            True si se imprimió correctamente, False en caso contrario
        """
        try:
            import win32print
            import win32ui

            # Abrir impresora
            if printer_name:
                hprinter = win32print.OpenPrinter(printer_name)
            else:
                # Usar impresora predeterminada
                printer_name = win32print.GetDefaultPrinter()
                hprinter = win32print.OpenPrinter(printer_name)

            try:
                # Iniciar trabajo de impresión - CORREGIDO: segundo elemento debe ser string vacío, no None
                hjob = win32print.StartDocPrinter(
                    hprinter, 
                    1, 
                    ("Comprobante de Pago", "", "RAW")  # <-- CORREGIDO: "" en lugar de None
                )
                win32print.StartPagePrinter(hprinter)

                # Enviar texto (codificado en CP850 para impresoras térmicas)
                win32print.WritePrinter(hprinter, texto.encode('cp850', errors='ignore'))

                win32print.EndPagePrinter(hprinter)
                win32print.EndDocPrinter(hprinter)

                logger.info(f"✅ Comprobante enviado a impresora: {printer_name}")
                return True

            finally:
                win32print.ClosePrinter(hprinter)

        except ImportError:
            logger.warning("⚠️ win32print no disponible. Guardando archivo...")
            return cls._guardar_archivo(texto)

        except Exception as e:
            logger.error(f"❌ Error imprimiendo: {e}")
            return cls._guardar_archivo(texto)
    
    @classmethod
    def _guardar_archivo(cls, texto: str) -> bool:
        """Guardar comprobante como archivo de texto"""
        try:
            # Crear directorio si no existe
            os.makedirs("comprobantes", exist_ok=True)
            
            # Generar nombre de archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprobantes/comprobante_{timestamp}.txt"
            
            with open(filename, "w", encoding="cp850") as f:
                f.write(texto)
            
            logger.info(f"✅ Comprobante guardado en: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando archivo: {e}")
            return False
    
    @classmethod
    def obtener_impresoras(cls) -> List[str]:
        """Obtener lista de impresoras disponibles"""
        try:
            import win32print
            impresoras = []
            printers = win32print.EnumPrinters(2)
            for printer in printers:
                impresoras.append(printer[2])
            return impresoras
        except:
            return []