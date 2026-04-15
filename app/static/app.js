document.addEventListener('DOMContentLoaded', () => {
    const loadingMessage = document.getElementById('loading-message');
    const fallbackMessage = document.getElementById('fallback-message');
    const marketOnlyMessage = document.getElementById('market-only-message');
    const contentArea = document.getElementById('content-area');
    const currentPriceElement = document.getElementById('current-price');
    const modelStatusElement = document.getElementById('model-status');
    let chartInstance = null;

    const MODE_TRANSLATIONS = {
        'hybrid': 'Híbrido',
        'market_only': 'Solo mercado',
        'naive': 'Contingencia'
    };

    fetch('/api/analysis')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Siempre quitar el mensaje de carga
            loadingMessage.classList.add('hidden');

            // Validar contrato
            if (
                typeof data.price !== 'number' ||
                typeof data.is_training !== 'boolean' ||
                typeof data.is_fallback !== 'boolean' ||
                !data.history || !Array.isArray(data.history.timestamps) || !Array.isArray(data.history.prices) ||
                !data.prediction || !Array.isArray(data.prediction.timestamps) || !Array.isArray(data.prediction.prices)
            ) {
                throw new Error('Invalid JSON structure');
            }

            // Render basic UI elements
            if (data.price > 0) {
                contentArea.classList.remove('hidden');
                currentPriceElement.textContent = `$${data.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            } else {
                showFallback(true);
                return;
            }

            // Handle fallback and mode states
            if (data.is_fallback || data.model.mode === 'naive') {
                showFallback(false);
            } else if (data.model.mode === 'market_only') {
                marketOnlyMessage.classList.remove('hidden');
            }

            const modeEs = MODE_TRANSLATIONS[data.model.mode] || data.model.mode.toUpperCase();
            modelStatusElement.textContent = `Modo: ${modeEs}`;

            // Render signals
            const regimenTraducido = {
                'bullish': 'Alcista',
                'bearish': 'Bajista',
                'neutral': 'Neutral'
            }[data.signals.market_regime] || data.signals.market_regime;

            document.getElementById('sig-regime').textContent = regimenTraducido;
            document.getElementById('sig-imbalance').textContent = data.signals.order_book_imbalance.toFixed(4);
            document.getElementById('sig-spread').textContent = data.signals.spread_bps.toFixed(2);
            document.getElementById('sig-volume').textContent = data.signals.volume_pressure.toFixed(4);

            const confidencePct = (data.signals.confidence * 100).toFixed(1);
            document.getElementById('sig-confidence').textContent = confidencePct + '%';
            document.getElementById('confidence-bar').style.width = confidencePct + '%';

            // Note: News data is intentionally excluded from the UI per V5 constraints,
            // although it is still processed in the backend.

            // Render chart combining history and prediction
            renderChart(data.history, data.prediction);

        })
        .catch(error => {
            console.error('Fetch error:', error);
            loadingMessage.classList.add('hidden');
            showFallback();
        });

    function showFallback(hideContent) {
        fallbackMessage.classList.remove('hidden');
        if (hideContent) {
            contentArea.classList.add('hidden');
        }
    }

    function renderChart(history, prediction) {
        const ctx = document.getElementById('historyChart').getContext('2d');

        // Limit history to the last 168 hours for better visibility
        const MAX_HISTORY_POINTS = 168;
        let histTimestamps = [];
        let histPrices = [];

        if (history.timestamps && history.timestamps.length > 0 && history.prices && history.prices.length > 0) {
            const numPoints = Math.min(history.timestamps.length, MAX_HISTORY_POINTS);
            histTimestamps = history.timestamps.slice(-numPoints);
            histPrices = history.prices.slice(-numPoints);
        }

        // Combine timestamps for X-axis
        let allTimestamps = [...histTimestamps];
        let predStartIndex = allTimestamps.length;

        if (prediction.timestamps && prediction.timestamps.length > 0) {
            allTimestamps = [...allTimestamps, ...prediction.timestamps];
        }

        // Format labels
        const labels = allTimestamps.map(ts => {
            const date = new Date(ts);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        });

        // Prepare datasets
        let historyData = [];
        if (histPrices.length > 0) {
            historyData = [...histPrices];
            // Pad historyData with nulls for the prediction portion
            if (prediction.prices && prediction.prices.length > 0) {
                historyData = historyData.concat(Array(prediction.prices.length).fill(null));
            }
        }

        let predictionData = [];
        if (prediction.prices && prediction.prices.length > 0) {
            // Pad predictionData with nulls for the history portion
            predictionData = Array(predStartIndex).fill(null);

            // To connect the lines, set the last point of history as the first point of prediction if possible
            if (histPrices.length > 0) {
                predictionData[predStartIndex - 1] = histPrices[histPrices.length - 1];
            }

            predictionData = predictionData.concat(prediction.prices);
        }

        // Destruir instancia anterior si existe
        if (chartInstance) {
            chartInstance.destroy();
        }

        const datasets = [];
        if (historyData.length > 0) {
            datasets.push({
                label: 'Histórico BTC/USDT',
                data: historyData,
                borderColor: '#f7931a', // Naranja Bitcoin
                backgroundColor: 'rgba(247, 147, 26, 0.1)',
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: true,
                tension: 0.1
            });
        }

        if (predictionData.length > 0) {
            datasets.push({
                label: 'Predicción 24h',
                data: predictionData,
                borderColor: '#3498db', // Azul
                borderDash: [5, 5],
                borderWidth: 2,
                pointRadius: 0,
                pointHoverRadius: 4,
                fill: false,
                tension: 0.1
            });
        }

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        ticks: {
                            maxTicksLimit: 10
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Precio (USDT)'
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        intersect: false,
                        mode: 'index'
                    }
                }
            }
        });
    }
});
