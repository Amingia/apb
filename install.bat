@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Iniciando instalación robusta del Análisis y Predicción BTC/USDT (V5)...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python no está instalado o no está en el PATH.
    echo Por favor, instálalo antes de continuar.
    pause
    exit /b 1
)

if not exist requirements.txt (
    echo Error: No se ha encontrado el archivo 'requirements.txt' en el directorio actual.
    echo Asegúrate de ejecutar este script desde la carpeta raíz del proyecto.
    pause
    exit /b 1
)

if not exist venv (
    echo Creando entorno virtual (venv)...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo Error crítico: No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
) else (
    echo El entorno virtual ya existe. Procediendo a actualizarlo...
)

echo Activando entorno virtual...
call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo Error crítico: No se pudo activar el entorno virtual.
    pause
    exit /b 1
)

echo Actualizando pip...
python -m pip install --upgrade pip >nul 2>&1

echo Instalando dependencias requeridas...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error crítico: Falló la instalación de las dependencias.
    echo Revisa tu conexión a internet o los errores detallados arriba.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo Instalación completada con éxito. El entorno está listo.
echo Para arrancar la aplicación, ejecuta: run.bat
echo =======================================================
pause
