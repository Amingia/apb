# Análisis y Predicción Inteligente BTC/USDT (Versión 8)

Esta aplicación proporciona un análisis técnico avanzado en tiempo real y una predicción algorítmica de 24 horas para el par BTC/USDT. Utiliza datos del mercado histórico (restringidos visualmente a las últimas 168 horas para máxima legibilidad), información en vivo del libro de órdenes y análisis de sentimiento de noticias globales. Todo ello funciona bajo un backend de FastAPI cacheado de refresco continuo, servido mediante una interfaz oscura, limpia y sin ruido visual innecesario, completamente en español de España.

**Nota importante sobre datos:** La aplicación recupera noticias globales y las utiliza internamente como una señal para potenciar la precisión de la inteligencia artificial. Sin embargo, **estas no se muestran en la interfaz de usuario**, manteniendo el cuadro de mando simple y centrado exclusivamente en la lectura e interpretación del mercado.

## Requisitos Previos

- Windows 10 o Windows 11.
- Python 3.9 o superior instalado y marcado en la casilla "Add Python to PATH".
- Conexión a internet estable (para acceder a Binance y API de noticias).

## Instalación Automática en Windows

El proyecto incluye una rutina de instalación sólida y a prueba de fallos que gestiona la creación de entornos virtuales y dependencias sin errores de codificación ni rutas mal resueltas. Abre tu terminal (o simplemente haz doble clic) y ejecuta:

```cmd
install.bat
```

## Arranque de la Aplicación en Windows

El script de ejecución comprobará primero si el entorno existe y si la instalación finalizó correctamente, evitando errores en cascada.

```cmd
run.bat
```

Abre tu navegador en: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## Actualización Continua y Precio Vivo

Una de las características clave de esta versión es la recolección continua de datos con dos cadencias diferenciadas:

1. **El Precio en Vivo:** El cliente consulta independientemente al backend (`/api/price`) cada **5 segundos** para traerte el último valor dictado por Binance, manteniendo la interfaz viva y reactiva.
2. **El Análisis Completo:** El servidor de Python cuenta con un hilo de fondo que actualiza la caché local, re-entrenando el modelo y extrayendo nueva información pesada cada **60 segundos** automáticamente. La gráfica absorbe estos cálculos masivos sin bloquearte el precio.

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
