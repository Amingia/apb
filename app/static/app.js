document.addEventListener('DOMContentLoaded', () => {
    const loadingMessage = document.getElementById('loading-message');
    const fallbackMessage = document.getElementById('fallback-message');
    const contentArea = document.getElementById('content-area');
    const currentPriceElement = document.getElementById('current-price');
    const updateTimeElement = document.getElementById('update-time');
    let chartInstance = null;

    function fetchData() {
        fetch('/api/analysis')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                loadingMessage.classList.add('hidden');

                if (
                    typeof data.price !== 'number' ||
                    typeof data.is_training !== 'boolean' ||
                    typeof data.is_fallback !== 'boolean' ||
                    !data.history || !Array.isArray(data.history.timestamps) || !Array.isArray(data.history.prices) ||
                    !data.prediction || !Array.isArray(data.prediction.timestamps) || !Array.isArray(data.prediction.prices)
                ) {
                    throw new Error('Invalid JSON structure');
                }

                if (data.price > 0) {
                    contentArea.classList.remove('hidden');
                    currentPriceElement.textContent = `$${data.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                } else {
                    showFallback(true);
                    return;
                }

                if (data.is_fallback || data.model.mode === 'naive') {
                    showFallback(false);
                } else {
                    fallbackMessage.classList.add('hidden');
                }

                // Update Time
                if (data.last_updated) {
                    const date = new Date(data.last_updated);
                    updateTimeElement.textContent = 'Última actualización: ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
                }

                // Render Market Summary
                renderMarketSummary(data.signals, data.prediction);

                // Render Confidence
                const confidenceVal = data.signals.confidence * 100;
                let confidenceLabel = "Baja";
                if (confidenceVal >= 60) confidenceLabel = "Alta";
                else if (confidenceVal >= 30) confidenceLabel = "Media";

                const confidencePct = confidenceVal.toFixed(1);
                document.getElementById('sig-confidence').textContent = `${confidencePct}% (${confidenceLabel})`;
                document.getElementById('confidence-bar').style.width = confidencePct + '%';

                renderChart(data.history, data.prediction);
            })
            .catch(error => {
                console.error('Fetch error:', error);
                loadingMessage.classList.add('hidden');
                showFallback();
            });
    }

    function showFallback(hideContent) {
        fallbackMessage.classList.remove('hidden');
        if (hideContent) {
            contentArea.classList.add('hidden');
        }
    }

    function renderMarketSummary(signals, prediction) {
        // Trend (Dirección probable 24h)
        let trend = "Probable lateralidad";
        let trendColor = "var(--text-muted)";

        // Calculate dynamic trend based on the prediction if available
        if (prediction && prediction.prices && prediction.prices.length > 0) {
            const firstP = prediction.prices[0];
            const lastP = prediction.prices[prediction.prices.length - 1];
            const diffPct = (lastP - firstP) / firstP;

            if (diffPct > 0.005) { // more than 0.5% up
                trend = "Probable subida";
                trendColor = "var(--success-text)";
            } else if (diffPct < -0.005) { // more than 0.5% down
                trend = "Probable bajada";
                trendColor = "var(--danger-text)";
            }
        }

        const trendEl = document.getElementById('market-trend');
        trendEl.textContent = trend;
        trendEl.style.color = trendColor;

        // Volatility logic
        let vol = "Media";
        if (signals.confidence < 0.3) vol = "Alta";
        else if (signals.confidence > 0.7) vol = "Baja";
        document.getElementById('market-volatility').textContent = vol;

        // Strength of signal
        let strength = "Débil";
        const combinedPressure = Math.abs(signals.order_book_imbalance) + Math.abs(signals.volume_pressure);
        if (combinedPressure > 0.4) {
            strength = "Alta";
        } else if (combinedPressure > 0.15) {
            strength = "Moderada";
        }
        document.getElementById('market-strength').textContent = strength;

        // 24h Expected Range
        let rangeText = "Calculando...";
        if (prediction && prediction.lower_prices && prediction.upper_prices && prediction.lower_prices.length > 0) {
            const minP = Math.min(...prediction.lower_prices);
            const maxP = Math.max(...prediction.upper_prices);
            rangeText = `$${minP.toLocaleString(undefined, {maximumFractionDigits: 0})} - $${maxP.toLocaleString(undefined, {maximumFractionDigits: 0})}`;
        }
        document.getElementById('market-range').textContent = rangeText;

        // Descriptive sentence
        let description = `El mercado muestra lateralidad probable con rango esperado entre ${rangeText} y baja convicción.`;
        if (trend === "Probable subida") {
            description = `Se detecta sesgo alcista moderado con fuerza ${strength.toLowerCase()} y volatilidad ${vol.toLowerCase()}.`;
        } else if (trend === "Probable bajada") {
            description = `Predomina la presión vendedora y el escenario más probable es bajista.`;
        }

        document.getElementById('market-summary-text').textContent = description;
    }

    function fetchLivePrice() {
        fetch('/api/price')
            .then(response => {
                if (!response.ok) throw new Error('Price fetch failed');
                return response.json();
            })
            .then(data => {
                if (data.price > 0 && !contentArea.classList.contains('hidden')) {
                    currentPriceElement.textContent = `$${data.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                }
            })
            .catch(error => {
                console.warn('Live price update skipped:', error);
            });
    }

    // Initial fetch
    fetchData();

    // Auto-refresh Full Analysis every 60 seconds
    setInterval(fetchData, 60000);

    // Auto-refresh Live Price every 5 seconds
    setInterval(fetchLivePrice, 5000);

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
        let lowerBandData = [];
        let upperBandData = [];

        if (prediction.prices && prediction.prices.length > 0) {
            // Pad prediction datasets with nulls for the history portion
            predictionData = Array(predStartIndex).fill(null);
            lowerBandData = Array(predStartIndex).fill(null);
            upperBandData = Array(predStartIndex).fill(null);

            // To connect the lines visually, set the last point of history as the first point
            if (histPrices.length > 0) {
                const lastHistPrice = histPrices[histPrices.length - 1];
                predictionData[predStartIndex - 1] = lastHistPrice;
                lowerBandData[predStartIndex - 1] = lastHistPrice;
                upperBandData[predStartIndex - 1] = lastHistPrice;
            }

            predictionData = predictionData.concat(prediction.prices);

            if (prediction.lower_prices && prediction.upper_prices) {
                lowerBandData = lowerBandData.concat(prediction.lower_prices);
                upperBandData = upperBandData.concat(prediction.upper_prices);
            }
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

        if (upperBandData.length > predStartIndex) {
            datasets.push({
                label: 'Banda Superior',
                data: upperBandData,
                borderColor: 'rgba(52, 152, 219, 0.0)', // Transparent border
                backgroundColor: 'rgba(52, 152, 219, 0.15)', // Light blue shade
                borderWidth: 0,
                pointRadius: 0,
                fill: '+1', // Fill to next dataset (lower band)
                tension: 0.1
            });
        }

        if (lowerBandData.length > predStartIndex) {
            datasets.push({
                label: 'Banda Inferior',
                data: lowerBandData,
                borderColor: 'rgba(52, 152, 219, 0.0)',
                borderWidth: 0,
                pointRadius: 0,
                fill: false,
                tension: 0.1
            });
        }

        if (predictionData.length > predStartIndex) {
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
