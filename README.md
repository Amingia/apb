# Análisis y Predicción Inteligente BTC/USDT (Versión 5)

Esta aplicación proporciona un análisis técnico avanzado en tiempo real y una predicción híbrida de 24 horas para el par BTC/USDT. Utiliza datos del mercado histórico (restringidos a las últimas 168 horas para máxima legibilidad), información en vivo del libro de órdenes y análisis de sentimiento de noticias globales. Todo ello funciona bajo un backend en FastAPI y una interfaz oscura y limpia, completamente en español de España.

**Nota importante:** Aunque la aplicación recupera noticias globales y las usa internamente para potenciar la precisión de la inteligencia artificial, estas *no se muestran en la interfaz de usuario* para mantener el cuadro de mando simple, directo y orientado exclusivamente al mercado numérico.

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

## Modos del Modelo

El motor competitivo compite entre varios modelos (ej. `HistGradientBoostingRegressor` y `Ridge`), utilizando retornos logarítmicos, momentum y validación temporal con decaimiento de 24 horas (decay) en las predicciones recursivas. En la interfaz gráfica verás indicado uno de estos 3 modos según las circunstancias:

- **Híbrido:** Estado óptimo. Emplea señales del libro de órdenes, precios y noticias globales.
- **Solo mercado:** Se activa si las noticias fallan. La predicción se calcula exclusivamente con análisis técnico numérico.
- **Contingencia:** Si Binance limita tu conexión, se muestra un histórico plano para no bloquear ni romper la web.

## API y Contrato JSON

- **Endpoint:** `GET /api/analysis`
- La API garantiza estrictamente que claves estructurales (como `news`, `prediction`, `history` o `signals`) jamás devuelvan `null` y estén siempre presentes para no romper integraciones o clientes externos de terceros.

## Solución de Problemas Frecuentes

- **El gráfico se ve extraño al principio:** Espera unos segundos y si hace falta recarga. El gráfico está calibrado para enseñar únicamente las últimas 168 horas y conectar automáticamente el punto presente con la proyección futura mediante una línea azul discontinua.
- **Modo Contingencia constante:** Has recargado demasiadas veces seguidas y Binance ha limitado temporalmente tu IP pública. Espera 5-10 minutos.
