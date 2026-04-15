#!/bin/bash
cd "$(dirname "$0")"

echo "Arrancando aplicación de Análisis y Predicción BTC/USDT (V5)..."

if [ ! -f "venv/bin/activate" ]; then
    echo "Error crítico: No se ha encontrado el entorno virtual."
    echo "Asegúrate de ejecutar './install.sh' primero en este directorio."
    exit 1
fi

echo "Activando entorno virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error crítico: Falló la activación del entorno virtual."
    exit 1
fi

echo "Comprobando instalación de dependencias principales..."
python3 -c "import uvicorn; import fastapi" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Error crítico: Faltan dependencias esenciales (FastAPI, Uvicorn, etc)."
    echo "Por favor, asegúrate de que './install.sh' finalizó correctamente."
    exit 1
fi

echo ""
echo "======================================================="
echo "Servidor levantándose..."
echo "Podrás acceder a la aplicación localmente en: http://127.0.0.1:8000"
echo "======================================================="
echo ""

uvicorn app.main:app --host 127.0.0.1 --port 8000
if [ $? -ne 0 ]; then
    echo "Error crítico: El servidor uvicorn se detuvo o falló al arrancar."
    echo "Revisa el registro de errores anterior."
    exit 1
fi
