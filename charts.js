// charts.js - Chart.js rendering logic

function renderEmotions(articles) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    const counts = { anger: 0, fear: 0, sadness: 0, surprise: 0, positive: 0 };
    let neutralCount = 0;

    articles.forEach(a => {
        const emo = a.narrative_emotion;
        if (emo === 'neutral' || !emo || emo === 'unknown') {
            neutralCount++;
        } else if (counts[emo] !== undefined) {
            counts[emo]++;
        } else {
            neutralCount++;
        }
    });
    
    const labels = Object.keys(counts);
    const data = Object.values(counts);
    const chartColor = THEME_BRIGHT;

    const totalActive = articles.length - neutralCount;
    logSystem(`resonance sync: ${totalActive} active signals, ${neutralCount} baseline/neutral`);

    if (charts.emotions) charts.emotions.destroy();
    charts.emotions = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'signals',
                data: data,
                backgroundColor: chartColor + '33', 
                borderColor: chartColor,
                pointBackgroundColor: chartColor,
                pointBorderColor: COLOR_BORDER || '#000',
                borderWidth: 2,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: { top: 10, bottom: 10, left: 10, right: 10 } },
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: TOOLTIP_BG,
                    titleFont: { family: "'Fira Code', monospace", size: 11 },
                    bodyFont: { family: "'Fira Code', monospace", size: 11 },
                    borderColor: chartColor,
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        title: (items) => items[0].label.toLowerCase(),
                        label: (item) => `signals: ${item.raw}`
                    }
                }
            },
            scales: {
                r: {
                    angleLines: { color: CHART_GRID },
                    grid: { color: CHART_GRID },
                    suggestedMin: 0,
                    pointLabels: {
                        color: THEME_MID,
                        font: { family: "'Fira Code', monospace", size: 11 },
                        padding: 15
                    },
                    ticks: { display: false, backdropColor: 'transparent' }
                }
            }
        }
    });
}

function renderGTI(score, history, forecast) {
    const scoreEl = document.getElementById('gti-score');
    const barEl = document.getElementById('gti-bar');
    const miniEl = document.getElementById('gti-score-mini');
    if (!scoreEl || !barEl) return;

    const target = score || 30;
    const duration = 1000;
    const start = performance.now();

    function animate(time) {
        const progress = Math.min((time - start) / duration, 1);
        const value = Math.floor(progress * target);
        scoreEl.textContent = value.toString().padStart(2, '0');
        if (progress < 1) requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);
    barEl.style.width = `${target}%`;
    if (miniEl) miniEl.textContent = target.toString().padStart(2, '0');
    
    if (target > 75) {
        scoreEl.style.color = THEME_BRIGHT; 
        scoreEl.style.textShadow = `0 0 20px ${THEME_BRIGHT}`;
    } else {
        scoreEl.style.color = 'var(--theme-bright)';
        scoreEl.style.textShadow = 'none';
    }

    if (history && history.length > 0) {
        const historyCanvas = document.getElementById('gtiHistoryChart');
        if (historyCanvas) {
            const ctx = historyCanvas.getContext('2d');
            let processedHistory = history;
            
            const labels = processedHistory.map(h => new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            const data = processedHistory.map(h => h.score);

            // Add forecast if available
            let forecastData = [];
            let forecastLabels = [];
            if (forecast && forecast.length > 0) {
                // Ensure continuity
                forecastData = [data[data.length - 1], ...forecast.map(f => f.score)];
                forecastLabels = ["", ...forecast.map(f => new Date(f.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }))];
            }

            if (charts.gtiHistory) charts.gtiHistory.destroy();

            const normalizeHex = (hex) => {
                if (hex.length === 4) return '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
                return hex;
            };
            const baseColor = normalizeHex(THEME_BRIGHT);
            const gradient = ctx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, baseColor + '66');
            gradient.addColorStop(1, baseColor + '00');

            charts.gtiHistory = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [...labels, ...forecastLabels.slice(1)],
                    datasets: [
                        {
                            label: 'gti_trend',
                            data: data,
                            borderColor: THEME_BRIGHT,
                            backgroundColor: gradient,
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true,
                            tension: 0.4
                        },
                        {
                            label: 'gti_forecast',
                            data: [...Array(data.length - 1).fill(null), ...forecastData],
                            borderColor: THEME_MID,
                            borderDash: [5, 5],
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false,
                            tension: 0.4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: { 
                        legend: { display: false },
                        tooltip: {
                            enabled: true,
                            backgroundColor: TOOLTIP_BG,
                            titleFont: { size: 10, family: "'Fira Code', monospace" },
                            bodyFont: { size: 11, family: "'Fira Code', monospace" },
                            borderColor: THEME_BRIGHT + '44',
                            borderWidth: 1,
                            padding: 10,
                            displayColors: false,
                            callbacks: { label: (context) => `${context.dataset.label}: ${context.parsed.y}` }
                        }
                    },
                    scales: {
                        x: { display: false },
                        y: {
                            min: 0, max: 100,
                            grid: { color: CHART_GRID },
                            border: { display: false },
                            ticks: {
                                stepSize: 25,
                                font: { size: 10, family: "'Fira Code', monospace" },
                                color: CHART_TICK,
                                callback: (value) => value + '%'
                            }
                        }
                    }
                }
            });
        }
    }
}

function renderWordCloud(keywords) {
    const container = document.getElementById('word-cloud');
    if (!container) return;
    container.innerHTML = '';
    if (!keywords || Object.keys(keywords).length === 0) {
        container.innerHTML = '<span class="text-dim">no tokens detected</span>';
        return;
    }
    const entries = Object.entries(keywords);
    const max = Math.max(...entries.map(e => (typeof e[1] === 'object' ? e[1].count : e[1])));
    // LOC uses --theme-mid, not --theme-dim: dim is a border/divider tone, below AA as text.
    const typeColors = { "GPE": THEME_BRIGHT, "ORG": THEME_MID, "PERSON": COLOR_WHITE, "LOC": THEME_MID, "NORP": THEME_MID };
    entries.forEach(([word, info]) => {
        const count = typeof info === 'object' ? info.count : info;
        const type = typeof info === 'object' ? info.type : "UNKNOWN";
        const size = 0.7 + (count / max) * 1.0;
        const opacity = 0.5 + (count / max) * 0.5;
        const color = typeColors[type] || THEME_MID;
        const span = document.createElement('span');
        span.className = 'word-item';
        span.style.fontSize = `${size}rem`;
        span.style.opacity = opacity;
        span.style.color = color;
        span.style.animation = `floatText ${2 + Math.random() * 2}s ease-in-out infinite`;
        span.style.animationDelay = `${Math.random()}s`;
        span.textContent = word.toLowerCase();
        span.title = `Type: ${type} | Mentions: ${count} | Click to filter`;
        span.onclick = () => setGlobalFilter('keyword', word);
        container.appendChild(span);
    });
}

function renderWordCloudEnriched(processedKeywords) {
    const container = document.getElementById('word-cloud');
    if (!container) return;
    container.innerHTML = '';
    if (processedKeywords.length === 0) {
        container.innerHTML = '<span class="text-dim">no tokens detected</span>';
        return;
    }
    // LOC uses --theme-mid, not --theme-dim: dim is a border/divider tone, below AA as text.
    const typeColors = { "GPE": THEME_BRIGHT, "ORG": THEME_MID, "PERSON": COLOR_WHITE, "LOC": THEME_MID, "NORP": THEME_MID };
    processedKeywords.forEach(item => {
        const size = 0.7 + (item.weight) * 1.0;
        const opacity = 0.5 + (item.weight) * 0.5;
        const color = typeColors[item.type] || THEME_MID;
        const span = document.createElement('span');
        span.className = 'word-item';
        span.style.fontSize = `${size}rem`;
        span.style.opacity = opacity;
        span.style.color = color;
        span.style.animation = `floatText ${2 + Math.random() * 2}s ease-in-out infinite`;
        span.style.animationDelay = `${Math.random()}s`;
        span.textContent = item.word.toLowerCase();
        span.title = `Type: ${item.type} | Mentions: ${item.count} | Click to filter`;
        span.onclick = () => setGlobalFilter('keyword', item.word);
        container.appendChild(span);
    });
}
