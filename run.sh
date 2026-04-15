#!/bin/bash
cd "$(dirname "$0")"

echo "======================================================="
echo "    Iniciando Análisis y Predicción BTC/USDT V6..."
echo "======================================================="
echo ""

if [ ! -f "venv/bin/activate" ]; then
    echo "[ERROR] El entorno virtual no existe. Por favor ejecuta ./install.sh primero."
    exit 1
fi

source venv/bin/activate

echo "Arrancando el servidor local..."
echo "La aplicación estará disponible en http://localhost:8000"
echo "Mantén esta ventana abierta mientras uses la aplicación."
echo "Presiona Ctrl+C para cerrar el servidor."
echo ""

python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
