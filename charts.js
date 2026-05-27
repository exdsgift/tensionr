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
                    backgroundColor: 'rgba(0, 0, 0, 0.85)',
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
                    angleLines: { color: 'rgba(255,255,255,0.1)' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    suggestedMin: 0,
                    pointLabels: { 
                        color: THEME_MID, 
                        font: { family: "'Fira Code', monospace", size: 10 },
                        padding: 15
                    },
                    ticks: { display: false, backdropColor: 'transparent' }
                }
            }
        }
    });
}

function renderGTI(score, history) {
    const scoreEl = document.getElementById('gti-score');
    const barEl = document.getElementById('gti-bar');
    if (!scoreEl || !barEl) return;

    let current = 0;
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
            if (history.length > 40) {
                const step = Math.ceil(history.length / 40);
                processedHistory = history.filter((_, i) => i % step === 0 || i === history.length - 1);
            }
            const labels = processedHistory.map(h => new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            const data = processedHistory.map(h => h.score);
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
                    labels: labels,
                    datasets: [{
                        label: 'gti_trend',
                        data: data,
                        borderColor: THEME_BRIGHT,
                        backgroundColor: gradient,
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: THEME_BRIGHT,
                        pointHoverBorderColor: COLOR_WHITE,
                        pointHoverBorderWidth: 2,
                        fill: true,
                        tension: 0.45,
                        spanGaps: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: { intersect: false, mode: 'index' },
                    plugins: { 
                        legend: { display: false },
                        tooltip: {
                            enabled: true,
                            backgroundColor: 'rgba(10, 10, 10, 0.9)',
                            titleFont: { size: 10, family: "'Fira Code', monospace" },
                            bodyFont: { size: 11, family: "'Fira Code', monospace" },
                            borderColor: THEME_BRIGHT + '44',
                            borderWidth: 1,
                            padding: 10,
                            displayColors: false,
                            callbacks: { label: (context) => `index_score: ${context.parsed.y}` }
                        }
                    },
                    scales: {
                        x: { display: false },
                        y: { 
                            min: 0, max: 100, 
                            grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                            ticks: { 
                                stepSize: 25, 
                                font: { size: 8, family: "'Fira Code', monospace" },
                                color: 'rgba(255,255,255,0.3)',
                                callback: (value) => value + '%'
                            }
                        }
                    },
                    animations: {
                        tension: { duration: 1000, easing: 'linear', from: 1, to: 0.45, loop: false }
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
    const typeColors = { "GPE": THEME_BRIGHT, "ORG": THEME_MID, "PERSON": COLOR_WHITE, "LOC": THEME_DIM, "NORP": THEME_MID };
    entries.forEach(([word, info]) => {
        const count = typeof info === 'object' ? info.count : info;
        const type = typeof info === 'object' ? info.type : "UNKNOWN";
        const size = 0.55 + (count / max) * 1.1;
        const opacity = 0.4 + (count / max) * 0.6;
        const color = typeColors[type] || THEME_MID;
        const span = document.createElement('span');
        span.className = 'word-item';
        span.style.fontSize = `${size}rem`;
        span.style.opacity = opacity;
        span.style.color = color;
        span.style.margin = '1px 4px';
        span.style.animation = `floatText ${2 + Math.random() * 2}s ease-in-out infinite`;
        span.style.animationDelay = `${Math.random()}s`;
        span.textContent = word.toLowerCase();
        span.title = `Type: ${type} | Mentions: ${count} | Click to filter`;
        span.style.cursor = 'pointer';
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
    const typeColors = { "GPE": THEME_BRIGHT, "ORG": THEME_MID, "PERSON": COLOR_WHITE, "LOC": THEME_DIM, "NORP": THEME_MID };
    processedKeywords.forEach(item => {
        const size = 0.55 + (item.weight) * 1.1;
        const opacity = 0.4 + (item.weight) * 0.6;
        const color = typeColors[item.type] || THEME_MID;
        const span = document.createElement('span');
        span.className = 'word-item';
        span.style.fontSize = `${size}rem`;
        span.style.opacity = opacity;
        span.style.color = color;
        span.style.margin = '1px 4px';
        span.style.animation = `floatText ${2 + Math.random() * 2}s ease-in-out infinite`;
        span.style.animationDelay = `${Math.random()}s`;
        span.textContent = item.word.toLowerCase();
        span.title = `Type: ${item.type} | Mentions: ${item.count} | Click to filter`;
        span.style.cursor = 'pointer';
        span.onclick = () => setGlobalFilter('keyword', item.word);
        container.appendChild(span);
    });
}
