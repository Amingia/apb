@echo off
echo Iniciando instalación del Análisis y Predicción BTC/USDT...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python no está instalado. Por favor, instálalo antes de continuar.
    pause
    exit /b 1
)

echo Creando entorno virtual (venv)...
python -m venv venv

echo Activando entorno virtual e instalando dependencias...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo Instalación completada con éxito.
echo Para arrancar la aplicación, ejecuta: run.bat
pause