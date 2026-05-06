@echo off
title Calculadora IMC - Christian Lera
echo ===============================================
echo    CALCULADORA DE IMC CON HISTORIAL Y GRAFICO
echo               Autor: Christian Lera
echo ===============================================
echo.

:: Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] No se encuentra Python instalado en el sistema.
    echo.
    echo Por favor, instale Python desde https://www.python.org/downloads/
    echo Asegurese de marcar la opcion "Add Python to PATH" durante la instalacion.
    echo.
    pause
    exit /b 1
)

:: Mostrar versión de Python
echo [INFO] Python instalado:
python --version
echo.

:: Verificar e instalar matplotlib si es necesario
echo [INFO] Verificando dependencias...
python -c "import matplotlib" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Matplotlib no encontrado. Instalando...
    pip install matplotlib
    if errorlevel 1 (
        echo [ERROR] No se pudo instalar matplotlib.
        echo Intente manualmente: pip install matplotlib
        pause
        exit /b 1
    )
    echo [INFO] Matplotlib instalado correctamente.
) else (
    echo [INFO] Matplotlib ya esta instalado.
)

echo.
echo [INFO] Iniciando la aplicacion...
echo.

:: Ejecutar la calculadora
python CalculadoraIMC.py

:: Si el programa se cierra, mostrar mensaje
echo.
echo [INFO] La aplicacion se ha cerrado.
pause