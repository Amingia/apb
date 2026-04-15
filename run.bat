@echo off
echo Iniciando la aplicación de Análisis y Predicción BTC/USDT...

if not exist venv\Scripts\activate (
    echo Error: No se ha encontrado el entorno virtual. Por favor, ejecuta primero install.bat
    pause
    exit /b 1
)

echo Activando entorno virtual...
call venv\Scripts\activate

echo Arrancando el servidor...
echo Podrás acceder a la aplicación en: http://127.0.0.1:8000
uvicorn app.main:app --host 127.0.0.1 --port 8000
pause