# Análisis y Predicción Inteligente BTC/USDT (Versión 6)

Esta aplicación proporciona un análisis técnico avanzado en tiempo real y una predicción algorítmica de 24 horas para el par BTC/USDT. Utiliza datos del mercado histórico (restringidos visualmente a las últimas 168 horas para máxima legibilidad), información en vivo del libro de órdenes y análisis de sentimiento de noticias globales. Todo ello funciona bajo un backend de FastAPI cacheado de refresco continuo, servido mediante una interfaz oscura, limpia y sin ruido visual innecesario, completamente en español de España.

**Nota importante sobre datos:** La aplicación recupera noticias globales y las utiliza internamente como una señal para potenciar la precisión de la inteligencia artificial. Sin embargo, **estas no se muestran en la interfaz de usuario**, manteniendo el cuadro de mando simple y centrado exclusivamente en la lectura e interpretación del mercado.

## Requisitos Previos

- Python 3.9 o superior.
- Conexión a internet estable (para acceder a Binance y API de noticias).

## Instalación Automática

El proyecto incluye rutinas de instalación altamente robustas (`install.bat` y `install.sh`) que gestionan la creación de entornos virtuales y dependencias sin errores de codificación ni rutas de archivos mal resueltas.

**En Windows:**
```cmd
install.bat
```

**En Linux / macOS:**
```bash
chmod +x install.sh run.sh
./install.sh
```

## Arranque de la Aplicación

Los scripts de ejecución comprueban primero si el entorno existe y si la instalación finalizó correctamente, evitando errores en cascada.

**En Windows:**
```cmd
run.bat
```

**En Linux / macOS:**
```bash
./run.sh
```

Abre tu navegador en: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## Actualización Continua y Autónoma

Una de las características clave de esta versión es la recolección continua de datos en segundo plano.

1. **Refresco del Servidor:** El servidor de Python cuenta con un hilo de fondo (`background task`) que actualiza la caché local, re-entrenando el modelo y extrayendo nueva información cada 60 segundos automáticamente.
2. **Refresco del Cliente:** Al tener la web abierta, tu navegador se sincroniza de forma transparente con esa caché, sin que la página parpadee ni se bloquee el gráfico.

## El Modelo Predictivo Multi-Horizonte y sus Bandas

El motor ha sido rediseñado drásticamente para evitar la temida proyección lineal. Ya no usamos recursión básica; en su lugar, modelos como `Ridge` o `HistGradientBoostingRegressor` generan predicciones directas a múltiples horizontes simultáneamente (MultiOutputRegressor).

* **La línea principal (Azul punteada):** Proyecta la evolución direccional en cada uno de los 24 bloques de una hora basándose puramente en patrones encontrados de retornos, distancias a la media y momentum.
* **El rango de incertidumbre (Sombra azul celeste):** Entiende que el mercado tiene desviación. Acompañando a la línea principal se dibuja una banda mínima (`lower_prices`) y máxima (`upper_prices`). Este margen se calcula rigurosamente a través de los residuos estándar detectados en los tests de validación.

## API y Contrato JSON Robusto

- **Endpoint:** `GET /api/analysis`
- La API garantiza estrictamente que claves estructurales (como `news`, `prediction`, `history` o `signals`) jamás devuelvan `null` ni errores tipo NaN. A partir de V6 la salida de `prediction` incluye también `lower_prices` y `upper_prices` poblados.

## Solución de Problemas Frecuentes

- **El gráfico se ve extraño al principio:** Espera unos segundos, está calibrado para enseñar únicamente las últimas 168 horas y conectar automáticamente el punto presente con la proyección futura.
- **Modo Contingencia (Aviso de error en rojo visible):** El script de Binance en tu IP ha sido temporalmente bloqueado debido al rate-limit. No te preocupes, el frontend no se rompe y el backend espera automáticamente mientras sirve una predicción plana y segura hasta restablecerse en unos minutos.
