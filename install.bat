@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo =======================================================
echo      Instalador Análisis y Predicción BTC/USDT V6
echo =======================================================
echo.

REM Comprobar si Python está instalado
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python no está instalado o no está en el PATH.
    echo Por favor, descarga e instala Python desde https://www.python.org/downloads/
    echo Asegúrate de marcar la casilla "Add Python to PATH" durante la instalación.
    pause
    goto :eof
)

echo [OK] Python detectado.

if not exist "%~dp0requirements.txt" (
    echo [ERROR] No se ha encontrado el archivo 'requirements.txt' en el directorio actual.
    echo Asegúrate de ejecutar este script desde la carpeta raíz del proyecto.
    pause
    goto :eof
)

echo.
echo Creando entorno virtual...
python -c "import venv; venv.create('venv', with_pip=True)"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    goto :eof
)

echo.
echo Activando entorno virtual e instalando dependencias...
call venv\Scripts\activate.bat

REM Actualizamos pip de forma segura usando el ejecutable del entorno virtual
python -m pip install --upgrade pip >nul 2>&1

REM Instalamos las dependencias usando la ruta absoluta
python -m pip install -r "%~dp0requirements.txt"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Hubo un problema instalando las dependencias.
    pause
    goto :eof
)

echo.
echo =======================================================
echo [ÉXITO] Instalación completada con éxito. El entorno está listo.
echo Para arrancar la aplicación, ejecuta: run.bat
echo =======================================================
pause
