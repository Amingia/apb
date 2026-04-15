#!/bin/bash
cd "$(dirname "$0")"

echo "Iniciando instalación robusta del Análisis y Predicción BTC/USDT (V4)..."

# Comprobar si Python está instalado
if ! command -v python3 &> /dev/null
then
    echo "Error crítico: Python 3 no está instalado o no está en el PATH."
    echo "Por favor, instálalo antes de continuar."
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "Error crítico: No se ha encontrado el archivo 'requirements.txt' en el directorio actual."
    echo "Asegúrate de ejecutar este script desde la carpeta raíz del proyecto."
    exit 1
fi

if [ ! -d "venv" ]; then
    echo "Creando entorno virtual (venv)..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error crítico: No se pudo crear el entorno virtual."
        exit 1
    fi
else
    echo "El entorno virtual ya existe. Procediendo a actualizarlo..."
fi

echo "Activando entorno virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "Error crítico: No se pudo activar el entorno virtual."
    exit 1
fi

echo "Actualizando pip..."
python3 -m pip install --upgrade pip > /dev/null 2>&1

echo "Instalando dependencias requeridas..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error crítico: Falló la instalación de las dependencias mediante pip."
    echo "Revisa tu conexión a internet o los errores detallados arriba."
    exit 1
fi

echo ""
echo "======================================================="
echo "Instalación completada con éxito. El entorno está listo."
echo "Para arrancar la aplicación, ejecuta: ./run.sh"
echo "======================================================="
