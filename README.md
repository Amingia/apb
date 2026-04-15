# Análisis y Predicción Inteligente BTC/USDT

Esta aplicación proporciona un análisis técnico avanzado en tiempo real y una predicción híbrida de 24 horas para el par BTC/USDT. Utiliza datos del mercado histórico, información en vivo del libro de órdenes (order book) y el análisis de sentimiento de noticias globales (GDELT). Todo ello bajo un backend optimizado en FastAPI y servido mediante una interfaz gráfica oscura, elegante y completamente en español de España.

## Requisitos Previos

- Python 3.9 o superior instalado en el sistema y añadido a la variable PATH.
- Conexión a internet estable (para acceder en tiempo real a Binance y a las API de noticias).

## Instalación Automática

El proyecto incluye rutinas de instalación robustas que gestionan la creación de entornos virtuales y la instalación de dependencias, asegurando un despliegue libre de conflictos independientemente del directorio en el que te encuentres.

**En Windows:**
Ejecuta el script por lotes haciendo doble clic en él o ejecutándolo desde la consola de comandos. Su codificación ha sido corregida para ejecutarse sin caracteres extraños:
```cmd
install.bat
```

**En Linux / macOS:**
Concede permisos de ejecución y lanza el script shell:
```bash
chmod +x install.sh run.sh
./install.sh
```

## Arranque de la Aplicación

Para iniciar el servidor local sin tener que activar el entorno manualmente, utiliza el lanzador correspondiente a tu sistema operativo. Estos lanzadores ahora están programados para comprobar automáticamente si las dependencias críticas están disponibles, emitiendo un error claro si la instalación anterior falló.

**En Windows:**
```cmd
run.bat
```

**En Linux / macOS:**
```bash
./run.sh
```

Una vez que el terminal confirme que el servidor está escuchando peticiones, accede a la interfaz gráfica desde tu navegador preferido: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## Modos del Modelo de Predicción Competitiva

El motor interno se ha rediseñado para utilizar variables logarítmicas, ratios de volatilidad y momentum intrabarra. Cada consulta entrena varios modelos candidatos simultáneamente (como `HistGradientBoostingRegressor` y `Ridge`), evalúa su precisión (RMSE) contra datos de validación cruzada temporal y utiliza el ganador para proyectar los futuros 24 puntos aplicando decaimiento matemático para prevenir inestabilidades extremas.

Además, el sistema es completamente resiliente a caídas de red y opera bajo tres posibles modos:

- **HÍBRIDO (HYBRID):** El estado óptimo. Emplea señales numéricas del mercado y el sentimiento agregado de las noticias mundiales para predecir.
- **SOLO MERCADO (MARKET_ONLY):** Se activa automáticamente si las fuentes informativas no responden a tiempo o no contienen resultados de impacto. Se alerta discretamente en la UI y la proyección se basa únicamente en comportamiento algorítmico y del libro de órdenes.
- **CONTINGENCIA (NAIVE):** Salva el entorno de bloqueos fatales. Si la API pública de Binance limita el tráfico y es imposible recopilar el historial base de entrenamiento, el backend lo intercepta y emite un flujo de proyecciones planas y seguras sin congelar el flujo de la aplicación.

## La API REST

El corazón del sistema es transparente e integrable con cualquier otra plataforma o bot externo garantizando la integridad de las claves.

- **Endpoint:** `GET /api/analysis`
- **Contrato JSON Estricto:** Siempre devuelve el objeto completo pre-poblado (arrays exactos, métricas numéricas y sin llaves nulas `null`). Si quieres confirmar que la base funciona correctamente, ejecuta `curl -s http://127.0.0.1:8000/api/analysis` desde tu terminal y valida los metadatos y el bloque `model.mode`.

## Solución de Problemas Frecuentes

- **`install.bat` falla indicando que no encuentra `requirements.txt`:** Asegúrate de no mover el archivo bat fuera del proyecto base. El script en esta versión resuelve automáticamente la ruta correcta basándose en su propia ubicación para evitar falsos positivos de carpetas de arranque.
- **Error crítico al activar el entorno en Linux (`./run.sh`):** Esto significa que el proceso previo falló o que interrumpiste la descarga. Asegúrate de ejecutar `./install.sh` hasta que te confirme un mensaje claro de éxito.
- **Mensaje persistente de "Modo de contingencia" en la Interfaz:** Es muy probable que tu dirección IP esté siendo regulada (rate-limit) por la API pública de Binance debido a un exceso de recargas seguidas de la página. Espera entre 5 y 10 minutos y vuelve a intentarlo.
