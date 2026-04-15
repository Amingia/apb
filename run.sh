#!/bin/bash
echo "Iniciando la aplicación de Análisis y Predicción BTC/USDT..."

if [ ! -d "venv" ]; then
    echo "Error: No se ha encontrado el entorno virtual. Por favor, ejecuta primero ./install.sh"
    exit 1
fi

echo "Activando entorno virtual..."
source venv/bin/activate

echo "Arrancando el servidor..."
echo "Podrás acceder a la aplicación en: http://127.0.0.1:8000"
uvicorn app.main:app --host 127.0.0.1 --port 8000