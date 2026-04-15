#!/bin/bash
echo "Iniciando instalación del Análisis y Predicción BTC/USDT..."

# Comprobar si Python está instalado
if ! command -v python3 &> /dev/null
then
    echo "Error: Python 3 no está instalado. Por favor, instálalo antes de continuar."
    exit 1
fi

echo "Creando entorno virtual (venv)..."
python3 -m venv venv

echo "Activando entorno virtual e instalando dependencias..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Instalación completada con éxito."
echo "Para arrancar la aplicación, ejecuta: ./run.sh"