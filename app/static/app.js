document.addEventListener('DOMContentLoaded', () => {
    const loadingMessage = document.getElementById('loading-message');
    const fallbackMessage = document.getElementById('fallback-message');
    const contentArea = document.getElementById('content-area');
    const currentPriceElement = document.getElementById('current-price');
    let chartInstance = null;

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

            if (data.is_fallback) {
                showFallback();
                return;
            }

            // Mostrar el precio si es válido
            if (data.price > 0) {
                contentArea.classList.remove('hidden');
                currentPriceElement.textContent = `$${data.price.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
            } else {
                showFallback();
                return;
            }

            // Dibujar el gráfico si el histórico es válido
            const timestamps = data.history.timestamps;
            const prices = data.history.prices;

            if (timestamps.length > 0 && prices.length > 0 && timestamps.length === prices.length) {
                renderChart(timestamps, prices);
            }

        })
        .catch(error => {
            console.error('Fetch error:', error);
            loadingMessage.classList.add('hidden');
            showFallback();
        });

    function showFallback() {
        fallbackMessage.classList.remove('hidden');
        contentArea.classList.add('hidden');
    }

    function renderChart(timestamps, prices) {
        const ctx = document.getElementById('historyChart').getContext('2d');

        // Formatear timestamps a fechas legibles
        const labels = timestamps.map(ts => {
            const date = new Date(ts);
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        });

        // Destruir instancia anterior si existe
        if (chartInstance) {
            chartInstance.destroy();
        }

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'BTC/USDT',
                    data: prices,
                    borderColor: '#f7931a', // Color naranja de Bitcoin
                    backgroundColor: 'rgba(247, 147, 26, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHoverRadius: 4,
                    fill: true,
                    tension: 0.1
                }]
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
