@echo off
cd /d "%~dp0"
echo =======================================================
echo     Iniciando Analisis y Prediccion BTC/USDT V7...
echo =======================================================
echo.

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] El entorno virtual no existe. Por favor ejecuta install.bat primero.
    pause
    goto :eof
)

call venv\Scripts\activate.bat

echo Arrancando el servidor local...
echo La aplicacion estara disponible en http://localhost:8000
echo Manten esta ventana abierta mientras uses la aplicacion.
echo Presiona Ctrl+C para cerrar el servidor.
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
