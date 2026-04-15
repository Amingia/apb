@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo Arrancando aplicación de Análisis y Predicción BTC/USDT (V4)...

if not exist venv\Scripts\activate.bat (
    echo Error crítico: No se ha encontrado el entorno virtual.
    echo Asegúrate de ejecutar 'install.bat' primero en este directorio.
    pause
    exit /b 1
)

echo Activando entorno virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Error: Falló la activación del entorno virtual.
    pause
    exit /b 1
)

echo Comprobando instalación de dependencias principales...
python -c "import uvicorn; import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Faltan dependencias críticas (FastAPI, Uvicorn, etc).
    echo Por favor, asegúrate de que 'install.bat' finalizó correctamente.
    pause
    exit /b 1
)

echo.
echo =======================================================
echo Servidor levantándose...
echo Podrás acceder a la aplicación localmente en: http://127.0.0.1:8000
echo =======================================================
echo.

uvicorn app.main:app --host 127.0.0.1 --port 8000
if %errorlevel% neq 0 (
    echo Error crítico: El servidor uvicorn se detuvo o falló al arrancar.
    echo Revisa el registro de errores anterior.
    pause
    exit /b 1
)

pause
