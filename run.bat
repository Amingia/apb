@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo     Iniciando Análisis y Predicción BTC/USDT V6...
echo =======================================================
echo.

IF NOT EXIST "venv\Scripts\activate.bat" (
    echo [ERROR] El entorno virtual no existe. Por favor ejecuta install.bat primero.
    pause
    goto :eof
)

call venv\Scripts\activate.bat

echo Arrancando el servidor local...
echo La aplicación estará disponible en http://localhost:8000
echo Mantén esta ventana abierta mientras uses la aplicación.
echo Presiona Ctrl+C para cerrar el servidor.
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
