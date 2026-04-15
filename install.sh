#!/bin/bash
cd "$(dirname "$0")"

echo "======================================================="
echo "     Instalador Análisis y Predicción BTC/USDT V6"
echo "======================================================="
echo ""

# Comprobar si Python está instalado
if ! command -v python3 &> /dev/null
then
    echo "[ERROR] Python 3 no está instalado o no está en el PATH."
    echo "Por favor, instálalo antes de continuar."
    exit 1
fi

echo "[OK] Python detectado."

if [ ! -f "requirements.txt" ]; then
    echo "[ERROR] No se ha encontrado el archivo 'requirements.txt' en el directorio actual."
    echo "Asegúrate de ejecutar este script desde la carpeta raíz del proyecto."
    exit 1
fi

echo ""
echo "Creando entorno virtual..."
python3 -c "import venv; venv.create('venv', with_pip=True)"
if [ $? -ne 0 ]; then
    echo "[ERROR] No se pudo crear el entorno virtual."
    exit 1
fi

echo ""
echo "Activando entorno virtual e instalando dependencias..."
source venv/bin/activate

# Actualizamos pip
python3 -m pip install --upgrade pip > /dev/null 2>&1

# Instalamos las dependencias
python3 -m pip install -r "$(pwd)/requirements.txt"
if [ $? -ne 0 ]; then
    echo "[ERROR] Hubo un problema instalando las dependencias."
    exit 1
fi

echo ""
echo "======================================================="
echo "[ÉXITO] Instalación completada con éxito. El entorno está listo."
echo "Para arrancar la aplicación, ejecuta: ./run.sh"
echo "======================================================="
