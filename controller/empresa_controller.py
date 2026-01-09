# controller/empresa_controller.py
import logging
from typing import Dict, Any, Optional
from model.empresa_model import EmpresaModel
from utils.validators import Validators

logger = logging.getLogger(__name__)

class EmpresaController:
    """Controlador para la tabla empresa"""
    
    @staticmethod
    def ver_empresa() -> Dict[str, Any]:
        """
        Obtiene los datos de la empresa
        
        Returns:
            Dict con los datos de la empresa
        """
        try:
            empresa = EmpresaModel.ver_empresa()
            return {
                'success': True,
                'data': empresa
            }
        except Exception as e:
            logger.error(f"Error al obtener empresa: {e}")
            return {
                'success': False,
                'message': f"Error al obtener datos de la empresa: {str(e)}"
            }
    
    @staticmethod
    def validar_datos_empresa(datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida los datos de la empresa antes de enviar a la base de datos
        
        Args:
            datos: Diccionario con los datos de la empresa
        
        Returns:
            Dict con resultado de validación y datos limpios
        """
        errores = []
        datos_limpios = {}
        
        # Validar nombre
        nombre = datos.get('nombre')
        if not nombre or nombre.strip() == "":
            errores.append("El nombre de la empresa es requerido")
        elif len(nombre.strip()) > 200:
            errores.append("El nombre no puede exceder los 200 caracteres")
        else:
            datos_limpios['nombre'] = nombre.strip()
        
        # Validar NIT
        nit = datos.get('nit')
        if not nit or nit.strip() == "":
            errores.append("El NIT de la empresa es requerido")
        elif len(nit.strip()) > 20:
            errores.append("El NIT no puede exceder los 20 caracteres")
        else:
            datos_limpios['nit'] = nit.strip()
        
        # Validar dirección (opcional)
        direccion = datos.get('direccion')
        if direccion:
            if len(direccion.strip()) > 300:
                errores.append("La dirección no puede exceder los 300 caracteres")
            else:
                datos_limpios['direccion'] = direccion.strip()
        
        # Validar teléfono (opcional)
        telefono = datos.get('telefono')
        if telefono:
            valido, mensaje = Validators.validar_telefono(telefono)
            if not valido:
                errores.append(mensaje)
            else:
                datos_limpios['telefono'] = telefono.strip()
        
        # Validar email (opcional)
        email = datos.get('email')
        if email:
            valido, mensaje = Validators.validar_email(email)
            if not valido:
                errores.append(mensaje)
            else:
                datos_limpios['email'] = email.strip()
        
        # Validar logo_url (opcional)
        logo_url = datos.get('logo_url')
        if logo_url:
            valido, mensaje = Validators.validar_url(logo_url)
            if not valido:
                errores.append(mensaje)
            else:
                datos_limpios['logo_url'] = logo_url.strip()
        
        return {
            'valido': len(errores) == 0,
            'errores': errores,
            'datos_limpios': datos_limpios
        }
    
    @staticmethod
    def insertar_empresa(datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta una nueva empresa
        
        Args:
            datos: Diccionario con los datos de la empresa
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar datos
            validacion = EmpresaController.validar_datos_empresa(datos)
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Llamar al modelo
            resultado = EmpresaModel.insertar_empresa(
                nombre=validacion['datos_limpios']['nombre'],
                nit=validacion['datos_limpios']['nit'],
                direccion=validacion['datos_limpios'].get('direccion'),
                telefono=validacion['datos_limpios'].get('telefono'),
                email=validacion['datos_limpios'].get('email'),
                logo_url=validacion['datos_limpios'].get('logo_url')
            )
            
            # La función de PostgreSQL ya devuelve un JSON, lo convertimos a dict
            if isinstance(resultado, dict):
                return resultado
            else:
                # Si no es dict, asumimos que es un string JSON o algo inesperado
                logger.error(f"Resultado inesperado al insertar empresa: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al insertar empresa'
                }
                
        except Exception as e:
            logger.error(f"Error al insertar empresa: {e}")
            return {
                'success': False,
                'message': f"Error al insertar empresa: {str(e)}"
            }
    
    @staticmethod
    def editar_empresa(id: int, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Edita los datos de la empresa
        
        Args:
            id: ID de la empresa
            datos: Diccionario con los datos a actualizar
        
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Validar ID
            if not isinstance(id, int) or id <= 0:
                return {
                    'success': False,
                    'message': 'ID de empresa inválido'
                }
            
            # Validar datos
            validacion = EmpresaController.validar_datos_empresa(datos)
            if not validacion['valido']:
                return {
                    'success': False,
                    'message': 'Errores de validación',
                    'errors': validacion['errores']
                }
            
            # Llamar al modelo
            resultado = EmpresaModel.editar_empresa(
                id=id,
                nombre=validacion['datos_limpios']['nombre'],
                nit=validacion['datos_limpios']['nit'],
                direccion=validacion['datos_limpios'].get('direccion'),
                telefono=validacion['datos_limpios'].get('telefono'),
                email=validacion['datos_limpios'].get('email'),
                logo_url=validacion['datos_limpios'].get('logo_url')
            )
            
            if isinstance(resultado, dict):
                return resultado
            else:
                logger.error(f"Resultado inesperado al editar empresa: {resultado}")
                return {
                    'success': False,
                    'message': 'Error inesperado al editar empresa'
                }
                
        except Exception as e:
            logger.error(f"Error al editar empresa: {e}")
            return {
                'success': False,
                'message': f"Error al editar empresa: {str(e)}"
            }