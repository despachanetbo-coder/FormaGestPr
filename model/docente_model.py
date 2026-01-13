# Archivo: model/docente_model.py - VERSIÓN OPTIMIZADA Y REORGANIZADA
from config.database import Database
from typing import List, Dict, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class DocenteModel:
    """Modelo optimizado para manejar operaciones CRUD de docentes"""
    
    # ===== CONSTANTES Y CONFIGURACIÓN =====
    
    # Columnas de la tabla docentes para mapeo de resultados
    COLUMNAS = [
        'id', 'ci_numero', 'ci_expedicion', 'nombres', 'apellido_paterno', 
        'apellido_materno', 'fecha_nacimiento', 'grado_academico', 
        'titulo_profesional', 'especialidad', 'telefono', 'email', 
        'curriculum_url', 'honorario_hora', 'activo', 'fecha_registro'
    ]
    
    # ===== MÉTODOS CRUD BÁSICOS =====
    
    @staticmethod
    def crear_docente(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crear un nuevo docente usando INSERT directo
        
        Args:
            data: Diccionario con los datos del docente
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Construir query INSERT con parámetros dinámicos
            query = """
            INSERT INTO public.docentes (
                ci_numero, ci_expedicion, nombres, apellido_paterno, 
                apellido_materno, fecha_nacimiento, grado_academico, 
                titulo_profesional, especialidad, telefono, email, 
                curriculum_url, honorario_hora, activo
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """
            
            # Preparar parámetros asegurando valores por defecto
            params = (
                data.get('ci_numero'),
                data.get('ci_expedicion'),
                data.get('nombres'),
                data.get('apellido_paterno'),
                data.get('apellido_materno'),
                data.get('fecha_nacimiento'),
                data.get('grado_academico'),
                data.get('titulo_profesional'),
                data.get('especialidad'),
                data.get('telefono'),
                data.get('email'),
                data.get('curriculum_url'),
                data.get('honorario_hora', 0.0),
                data.get('activo', True)
            )
            
            logger.info(f"Creando docente: {data.get('nombres')} {data.get('apellido_paterno')}")
            
            # Ejecutar INSERT
            result = Database.execute_query(query, params, fetch_one=True, commit=True)
            
            if result:
                nuevo_id = result[0]
                logger.info(f"✅ Docente creado exitosamente - ID: {nuevo_id}")
                return {
                    'nuevo_id': nuevo_id,
                    'mensaje': 'Docente creado exitosamente',
                    'exito': True
                }
            
            return {
                'nuevo_id': None,
                'mensaje': 'No se pudo crear el docente',
                'exito': False
            }
            
        except Exception as e:
            logger.error(f"❌ Error creando docente: {e}")
            return {
                'nuevo_id': None,
                'mensaje': f'Error al crear docente: {str(e)}',
                'exito': False
            }
    
    @staticmethod
    def actualizar_docente(docente_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Actualizar un docente existente usando UPDATE dinámico
        
        Args:
            docente_id: ID del docente a actualizar
            data: Diccionario con los campos a actualizar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            # Construir UPDATE dinámico basado en los campos proporcionados
            campos_actualizar = []
            params = []
            
            # Mapeo de campos de data a columnas de la tabla
            mapeo_campos = {
                'ci_numero': 'ci_numero',
                'ci_expedicion': 'ci_expedicion',
                'nombres': 'nombres',
                'apellido_paterno': 'apellido_paterno',
                'apellido_materno': 'apellido_materno',
                'fecha_nacimiento': 'fecha_nacimiento',
                'grado_academico': 'grado_academico',
                'titulo_profesional': 'titulo_profesional',
                'especialidad': 'especialidad',
                'telefono': 'telefono',
                'email': 'email',
                'curriculum_url': 'curriculum_url',
                'honorario_hora': 'honorario_hora',
                'activo': 'activo'
            }
            
            # Agregar solo los campos que están presentes en data
            for campo_data, campo_db in mapeo_campos.items():
                if campo_data in data and data[campo_data] is not None:
                    campos_actualizar.append(f"{campo_db} = %s")
                    params.append(data[campo_data])
            
            # Si no hay campos para actualizar
            if not campos_actualizar:
                return {
                    'filas_afectadas': 0,
                    'mensaje': 'No se proporcionaron datos para actualizar',
                    'exito': False
                }
            
            # Agregar ID al final de los parámetros
            params.append(docente_id)
            
            # Construir query final
            query = f"""
            UPDATE public.docentes 
            SET {', '.join(campos_actualizar)}, fecha_registro = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            logger.info(f"Actualizando docente ID: {docente_id}")
            
            # Ejecutar UPDATE
            filas_afectadas = Database.execute_query(query, tuple(params), fetch_all=False, commit=True)
            
            if filas_afectadas and filas_afectadas > 0:
                logger.info(f"✅ Docente actualizado - Filas afectadas: {filas_afectadas}")
                return {
                    'filas_afectadas': filas_afectadas,
                    'mensaje': 'Docente actualizado exitosamente',
                    'exito': True
                }
            
            return {
                'filas_afectadas': 0,
                'mensaje': 'No se encontró el docente o no hubo cambios',
                'exito': False
            }
            
        except Exception as e:
            logger.error(f"❌ Error actualizando docente: {e}")
            return {
                'filas_afectadas': 0,
                'mensaje': f'Error al actualizar docente: {str(e)}',
                'exito': False
            }
    
    @staticmethod
    def obtener_docente_por_id(docente_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtener un docente por ID
        
        Args:
            docente_id: ID del docente
            
        Returns:
            Dict con datos del docente o None si no existe
        """
        try:
            connection = Database.get_connection()
            if not connection:
                return {
                    'success': False,
                    'data': None,
                    'message': 'No se pudo obtener conexión a la base de datos'
                }
            
            cursor = connection.cursor()
            
            # Ejecutar función
            cursor.callproc('fn_obtener_docente_por_id', (docente_id,))
            result = cursor.fetchone()
            
            cursor.close()
            Database.return_connection(connection)
            
            if result:
                docente = dict(zip(DocenteModel.COLUMNAS, result))
                logger.debug(f"Docente encontrado: ID {docente_id}")
                return docente
            
        except Exception as e:
            logger.error(f"Error obteniendo docente por ID: {e}")
            return None
    
    # ===== MÉTODOS DE BÚSQUEDA =====
    
    @staticmethod
    def buscar_docentes(
        ci_numero: Optional[str] = None,
        ci_expedicion: Optional[str] = None,
        nombre: Optional[str] = None,
        grado_academico: Optional[str] = None,
        activo: Optional[bool] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Buscar docentes usando filtros opcionales
        
        Args:
            ci_numero: Número de CI (búsqueda parcial)
            ci_expedicion: Expedición del CI
            nombre: Nombre o apellidos (búsqueda parcial)
            grado_academico: Grado académico
            activo: Estado activo/inactivo
            limit: Límite de resultados
            offset: Desplazamiento
            
        Returns:
            Lista de docentes encontrados
        """
        try:
            query = """
            SELECT * FROM public.docentes 
            WHERE 1=1
            """
            
            params = []
            
            # Aplicar filtros dinámicamente
            if ci_numero:
                query += " AND ci_numero ILIKE %s"
                params.append(f"%{ci_numero}%")
            
            if ci_expedicion:
                query += " AND ci_expedicion = %s"
                params.append(ci_expedicion)
            
            if nombre:
                query += " AND (nombres ILIKE %s OR apellido_paterno ILIKE %s OR apellido_materno ILIKE %s)"
                params.extend([f"%{nombre}%", f"%{nombre}%", f"%{nombre}%"])
            
            if grado_academico:
                query += " AND grado_academico = %s"
                params.append(grado_academico)
            
            if activo is not None:
                query += " AND activo = %s"
                params.append(activo)
            
            # Ordenar y paginar
            query += " ORDER BY apellido_paterno, apellido_materno, nombres"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            results = Database.execute_query(query, tuple(params))
            
            if results:
                docentes = [dict(zip(DocenteModel.COLUMNAS, row)) for row in results]
                logger.debug(f"Búsqueda encontrada: {len(docentes)} docentes")
                return docentes
            
            return []
            
        except Exception as e:
            logger.error(f"Error buscando docentes: {e}")
            return []
    
    @staticmethod
    def buscar_docentes_completo(
        ci_numero: Optional[str] = None,
        ci_expedicion: Optional[str] = None,
        nombres: Optional[str] = None,
        apellido_paterno: Optional[str] = None,
        apellido_materno: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda avanzada de docentes para la interfaz de usuario
        
        Args:
            ci_numero: Número de CI (puede contener '-')
            ci_expedicion: Expedición del CI
            nombres: Nombres (búsqueda parcial)
            apellido_paterno: Apellido paterno (búsqueda parcial)
            apellido_materno: Apellido materno (búsqueda parcial)
            
        Returns:
            Lista de docentes encontrados
        """
        try:
            query = """
            SELECT * FROM public.docentes 
            WHERE 1=1
            """
            
            params = []
            
            # Manejo especial para CI con formato "numero-expedicion"
            if ci_numero:
                if '-' in ci_numero:
                    partes = ci_numero.split('-', 1)
                    query += " AND ci_numero ILIKE %s"
                    params.append(f"%{partes[0]}%")
                    
                    if len(partes) > 1 and partes[1]:
                        query += " AND ci_expedicion ILIKE %s"
                        params.append(f"%{partes[1]}%")
                else:
                    query += " AND ci_numero ILIKE %s"
                    params.append(f"%{ci_numero}%")
            
            if ci_expedicion and ci_expedicion != "Todos":
                query += " AND ci_expedicion = %s"
                params.append(ci_expedicion)
            
            if nombres:
                query += " AND nombres ILIKE %s"
                params.append(f"%{nombres}%")
            
            if apellido_paterno:
                query += " AND apellido_paterno ILIKE %s"
                params.append(f"%{apellido_paterno}%")
            
            if apellido_materno:
                query += " AND apellido_materno ILIKE %s"
                params.append(f"%{apellido_materno}%")
            
            # Ordenar y paginar
            query += " ORDER BY apellido_paterno, apellido_materno, nombres"
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            results = Database.execute_query(query, tuple(params))
            
            if results:
                docentes = [dict(zip(DocenteModel.COLUMNAS, row)) for row in results]
                logger.debug(f"Búsqueda completa: {len(docentes)} docentes")
                return docentes
            
            return []
            
        except Exception as e:
            logger.error(f"Error en búsqueda completa de docentes: {e}")
            return []
    
    # ===== MÉTODOS DE CONSULTA Y CONTEO =====
    
    @staticmethod
    def contar_docentes(
        ci_numero: Optional[str] = None,
        ci_expedicion: Optional[str] = None,
        nombre: Optional[str] = None,
        grado_academico: Optional[str] = None,
        activo: Optional[bool] = None
    ) -> int:
        """
        Contar total de docentes según filtros
        
        Args:
            Filtros iguales que en buscar_docentes
            
        Returns:
            Número total de docentes
        """
        try:
            query = """
            SELECT COUNT(*) FROM public.docentes 
            WHERE 1=1
            """
            
            params = []
            
            # Aplicar mismos filtros que en buscar_docentes
            if ci_numero:
                query += " AND ci_numero ILIKE %s"
                params.append(f"%{ci_numero}%")
            
            if ci_expedicion:
                query += " AND ci_expedicion = %s"
                params.append(ci_expedicion)
            
            if nombre:
                query += " AND (nombres ILIKE %s OR apellido_paterno ILIKE %s OR apellido_materno ILIKE %s)"
                params.extend([f"%{nombre}%", f"%{nombre}%", f"%{nombre}%"])
            
            if grado_academico:
                query += " AND grado_academico = %s"
                params.append(grado_academico)
            
            if activo is not None:
                query += " AND activo = %s"
                params.append(activo)
            
            result = Database.execute_query(query, tuple(params), fetch_one=True)
            
            return result[0] if result else 0
            
        except Exception as e:
            logger.error(f"Error contando docentes: {e}")
            return 0
    
    @staticmethod
    def obtener_todos_docentes(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Obtener todos los docentes (sin filtros)
        
        Args:
            limit: Límite de resultados
            offset: Desplazamiento
            
        Returns:
            Lista de todos los docentes
        """
        try:
            return DocenteModel.buscar_docentes(
                ci_numero=None,
                ci_expedicion=None,
                nombre=None,
                grado_academico=None,
                activo=None,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Error obteniendo todos los docentes: {e}")
            return []
    
    # ===== MÉTODOS DE ESTADO =====
    
    @staticmethod
    def eliminar_docente(docente_id: int) -> Dict[str, Any]:
        """
        Eliminar (desactivar) un docente
        
        Args:
            docente_id: ID del docente a desactivar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            query = """
            UPDATE public.docentes 
            SET activo = FALSE, fecha_registro = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            filas_afectadas = Database.execute_query(query, (docente_id,), fetch_all=False, commit=True)
            
            if filas_afectadas and filas_afectadas > 0:
                logger.info(f"Docente desactivado: ID {docente_id}")
                return {
                    'filas_afectadas': filas_afectadas,
                    'mensaje': 'Docente desactivado exitosamente',
                    'exito': True
                }
            
            return {
                'filas_afectadas': 0,
                'mensaje': 'Docente no encontrado',
                'exito': False
            }
            
        except Exception as e:
            logger.error(f"Error eliminando docente: {e}")
            return {
                'filas_afectadas': 0,
                'mensaje': f'Error al eliminar docente: {str(e)}',
                'exito': False
            }
    
    @staticmethod
    def activar_docente(docente_id: int) -> Dict[str, Any]:
        """
        Activar un docente previamente desactivado
        
        Args:
            docente_id: ID del docente a activar
            
        Returns:
            Dict con resultado de la operación
        """
        try:
            query = """
            UPDATE public.docentes 
            SET activo = TRUE, fecha_registro = CURRENT_TIMESTAMP
            WHERE id = %s
            """
            
            filas_afectadas = Database.execute_query(query, (docente_id,), fetch_all=False, commit=True)
            
            if filas_afectadas and filas_afectadas > 0:
                logger.info(f"Docente activado: ID {docente_id}")
                return {
                    'filas_afectadas': filas_afectadas,
                    'mensaje': 'Docente activado exitosamente',
                    'exito': True
                }
            
            return {
                'filas_afectadas': 0,
                'mensaje': 'Docente no encontrado',
                'exito': False
            }
            
        except Exception as e:
            logger.error(f"Error activando docente: {e}")
            return {
                'filas_afectadas': 0,
                'mensaje': f'Error al activar docente: {str(e)}',
                'exito': False
            }
    
    # ===== MÉTODOS DE VALIDACIÓN =====
    
    @staticmethod
    def verificar_ci_existente(ci_numero: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verificar si un número de CI ya existe
        
        Args:
            ci_numero: Número de CI a verificar
            excluir_id: ID a excluir de la verificación (para actualizaciones)
            
        Returns:
            True si el CI ya existe, False en caso contrario
        """
        try:
            if excluir_id:
                query = """
                SELECT EXISTS(
                    SELECT 1 FROM public.docentes 
                    WHERE ci_numero = %s AND id != %s
                )
                """
                params = (ci_numero, excluir_id)
            else:
                query = "SELECT EXISTS(SELECT 1 FROM public.docentes WHERE ci_numero = %s)"
                params = (ci_numero,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            return result[0] if result else False
            
        except Exception as e:
            logger.error(f"Error verificando CI: {e}")
            return False
    
    @staticmethod
    def verificar_email_existente(email: str, excluir_id: Optional[int] = None) -> bool:
        """
        Verificar si un email ya existe
        
        Args:
            email: Email a verificar
            excluir_id: ID a excluir de la verificación
            
        Returns:
            True si el email ya existe, False en caso contrario
        """
        try:
            if excluir_id:
                query = """
                SELECT EXISTS(
                    SELECT 1 FROM public.docentes 
                    WHERE email = %s AND id != %s
                )
                """
                params = (email, excluir_id)
            else:
                query = "SELECT EXISTS(SELECT 1 FROM public.docentes WHERE email = %s)"
                params = (email,)
            
            result = Database.execute_query(query, params, fetch_one=True)
            return result[0] if result else False
            
        except Exception as e:
            logger.error(f"Error verificando email: {e}")
            return False
    
    # ===== MÉTODOS DE ESTADÍSTICAS =====
    
    @staticmethod
    def obtener_estadisticas() -> Dict[str, Any]:
        """
        Obtener estadísticas generales de docentes
        
        Returns:
            Dict con estadísticas de docentes
        """
        try:
            query = """
            SELECT 
                COUNT(*) as total_docentes,
                COUNT(CASE WHEN activo = TRUE THEN 1 END) as activos,
                COUNT(CASE WHEN activo = FALSE THEN 1 END) as inactivos,
                COALESCE(AVG(honorario_hora), 0) as promedio_honorario,
                COUNT(CASE WHEN email IS NOT NULL AND email != '' THEN 1 END) as con_email,
                COUNT(CASE WHEN telefono IS NOT NULL AND telefono != '' THEN 1 END) as con_telefono,
                COUNT(CASE WHEN curriculum_url IS NOT NULL AND curriculum_url != '' THEN 1 END) as con_curriculum
            FROM public.docentes
            """
            
            result = Database.execute_query(query, fetch_one=True)
            
            if result:
                column_names = [
                    'total_docentes', 'activos', 'inactivos', 'promedio_honorario',
                    'con_email', 'con_telefono', 'con_curriculum'
                ]
                return dict(zip(column_names, result))
            
            return {}
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {e}")
            return {}
    
    # ===== MÉTODOS DE UTILIDAD =====
    
    @staticmethod
    def obtener_docentes_activos(limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtener solo docentes activos (para comboboxes, etc.)
        
        Args:
            limit: Límite de resultados
            
        Returns:
            Lista de docentes activos
        """
        try:
            return DocenteModel.buscar_docentes(
                activo=True,
                limit=limit,
                offset=0
            )
        except Exception as e:
            logger.error(f"Error obteniendo docentes activos: {e}")
            return []
    
    @staticmethod
    def formatear_nombre_docente(docente: Dict[str, Any]) -> str:
        """
        Formatear nombre completo del docente para mostrar
        
        Args:
            docente: Dict con datos del docente
            
        Returns:
            String con nombre formateado
        """
        grado = docente.get('grado_academico', '')
        nombres = docente.get('nombres', '')
        apellido_paterno = docente.get('apellido_paterno', '')
        apellido_materno = docente.get('apellido_materno', '')
        
        if grado:
            return f"{grado} {nombres} {apellido_paterno} {apellido_materno}".strip()
        else:
            return f"{nombres} {apellido_paterno} {apellido_materno}".strip()