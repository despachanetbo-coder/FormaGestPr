@echo off
chcp 65001 >nul
title Sistema de Gestión de Docentes - UNSXX
color 0F

echo ========================================
echo    SISTEMA DE GESTIÓN DE DOCENTES
echo             UNSXX
echo ========================================
echo.

REM Verificar si existe entorno virtual
if exist "venv\Scripts\activate.bat" (
    echo [✓] Entorno virtual encontrado
    call venv\Scripts\activate.bat
) else (
    echo [⚠] No se encontró entorno virtual
    echo     Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\activate.bat
    
    echo [✓] Instalando dependencias...
    pip install --upgrade pip
    pip install -r requirements.txt
)

echo.
echo [✓] Entorno configurado
echo [✓] Iniciando aplicación...

REM Verificar si existe el archivo principal
if exist "main.py" (
    echo [✓] Archivo main.py encontrado
    echo [✓] Ejecutando aplicación...
    echo.
    python main.py
) else (
    echo [✗] ERROR: No se encontró main.py
    echo     Buscando archivos alternativos...
    echo.
    
    if exist "app.py" (
        echo [✓] Encontrado app.py
        python app.py
    ) else (
        if exist "run.py" (
            echo [✓] Encontrado run.py
            python run.py
        ) else (
            echo [✗] ERROR: No se encontró archivo principal de Python
            echo     Archivos disponibles en el directorio:
            dir /b *.py
        )
    )
)

echo.
echo ========================================
echo    Aplicación finalizada
echo ========================================
pause