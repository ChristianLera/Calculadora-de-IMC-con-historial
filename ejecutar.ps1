
# ejecutar.ps1 - Script de inicio para Calculadora de IMC
# Autor: Christian Lera

Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "   CALCULADORA DE IMC CON HISTORIAL Y GRAFICO" -ForegroundColor Cyan
Write-Host "              Autor: Christian Lera" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Verificar si Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[INFO] Python instalado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] No se encuentra Python instalado en el sistema." -ForegroundColor Red
    Write-Host ""
    Write-Host "Por favor, instale Python desde https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "Asegurese de marcar la opcion 'Add Python to PATH' durante la instalacion."
    Write-Host ""
    Read-Host "Presione Enter para salir"
    exit 1
}

Write-Host ""

# Verificar e instalar matplotlib si es necesario
Write-Host "[INFO] Verificando dependencias..." -ForegroundColor Yellow
try {
    python -c "import matplotlib" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Matplotlib no encontrado"
    }
    Write-Host "[INFO] Matplotlib ya esta instalado." -ForegroundColor Green
} catch {
    Write-Host "[INFO] Matplotlib no encontrado. Instalando..." -ForegroundColor Yellow
    try {
        pip install matplotlib
        if ($LASTEXITCODE -ne 0) {
            throw "Error en instalacion"
        }
        Write-Host "[INFO] Matplotlib instalado correctamente." -ForegroundColor Green
    } catch {
        Write-Host "[ERROR] No se pudo instalar matplotlib." -ForegroundColor Red
        Write-Host "Intente manualmente: pip install matplotlib" -ForegroundColor Yellow
        Read-Host "Presione Enter para salir"
        exit 1
    }
}

Write-Host ""
Write-Host "[INFO] Iniciando la aplicacion..." -ForegroundColor Yellow
Write-Host ""

# Ejecutar la calculadora
python CalculadoraIMC.py

# Si el programa se cierra, mostrar mensaje
Write-Host ""
Write-Host "[INFO] La aplicacion se ha cerrado." -ForegroundColor Cyan
Read-Host "Presione Enter para salir"