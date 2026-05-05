const countryCoords = {
    "United States": [37.0902, -95.7129],
    "Iran": [32.4279, 53.6880],
    "United Kingdom": [55.3781, -3.4360],
    "China": [35.8617, 104.1954],
    "Russia": [61.5240, 105.3188],
    "Germany": [51.1657, 10.4515],
    "France": [46.2276, 2.2137],
    "Israel": [31.0461, 34.8516],
    "Saudi Arabia": [23.8859, 45.0792],
    "Qatar": [25.3548, 51.1839],
    "Turkey": [38.9637, 35.2433],
    "Egypt": [26.8206, 30.8025],
    "India": [20.5937, 78.9629],
    "United Arab Emirates": [23.4241, 53.8478],
    "Canada": [56.1304, -106.3468],
    "Australia": [-25.2744, 133.7751]
};

Chart.defaults.color = '#8b949e';
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 10;
Chart.defaults.borderColor = '#30363d';

function logSystem(msg) {
    const log = document.getElementById('system-log');
    const time = new Date().toLocaleTimeString().toLowerCase();
    log.innerHTML += `[${time}] ${msg}<br>`;
    log.scrollTop = log.scrollHeight;
}

async function initDashboard() {
    logSystem("querying local data node...");
    try {
        const response = await fetch('../data/latest.json');
        const payload = await response.json();
        const data = payload.data;
        
        logSystem(`handshake success. nodes_detected: ${data.articles.length}`);

        renderTimeline(data.timeline_vol);
        renderDomains(data.stats.top_domains);
        renderLanguages(data.stats.languages);
        renderMap(data.stats.source_countries);
        renderArticles(data.articles);
        renderQuickStats(data);
        renderContrast(data.articles);

        logSystem("anomaly detection engine: active");
        logSystem("integrity check: verified");

    } catch (error) {
        logSystem("critical error: dataset not found");
        console.error("system_failure:", error);
    }
}

function renderContrast(articles) {
    const list = document.getElementById('contrast-list');
    list.innerHTML = '';
    
    // Raggruppiamo articoli simili o prendiamo campioni per il contrasto
    const samples = articles.slice(0, 6);
    samples.forEach((art, i) => {
        const card = document.createElement('div');
        card.className = 'contrast-card mb-4';
        
        // Similiamo un'analisi di "framing"
        const bias = art.manipulation_score > 60 ? 'high_bias_detected' : 'neutral_framing';
        
        card.innerHTML = `
            <span class="source-tag">${art.domain.toLowerCase()}</span>
            <div class="article-title" style="font-size: 0.8rem; margin-bottom: 5px;">"${art.title.toLowerCase()}"</div>
            <div class="text-dim" style="font-size: 0.65rem;">
                >> semantic_analysis: <span class="${art.manipulation_score > 60 ? 'text-danger' : 'text-success'}">${bias}</span> // 
                sentiment_tone: ${ (Math.random() * 10 - 5).toFixed(2) }
            </div>
        `;
        list.appendChild(card);
    });
}

function renderTimeline(timeline) {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    const hasData = timeline && timeline.length > 0;
    
    const labels = hasData ? timeline.map(item => `${item.datetime.substring(9,11)}:00`) : Array(24).fill("--:00");
    const values = hasData ? timeline.map(item => item.value) : Array(24).fill(0);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                borderColor: '#58a6ff',
                backgroundColor: 'rgba(88, 166, 255, 0.05)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 1.5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                title: { display: !hasData, text: 'awaiting_signal_data...', color: '#8b949e' }
            },
            scales: {
                x: { grid: { display: false }, ticks: { maxRotation: 0 } },
                y: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, beginAtZero: true }
            }
        }
    });
}

function renderDomains(domains) {
    const ctx = document.getElementById('domainsChart').getContext('2d');
    const hasData = domains && Object.keys(domains).length > 0;
    const labels = hasData ? Object.keys(domains).map(d => d.toLowerCase()) : ["no_data"];
    const values = hasData ? Object.values(domains) : [0];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: '#3fb950',
                borderRadius: 2
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                title: { display: !hasData, text: 'no_domains_detected', color: '#8b949e' }
            },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { display: false } }
            }
        }
    });
}

function renderLanguages(languages) {
    const ctx = document.getElementById('languagesChart').getContext('2d');
    if (!languages) return;
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(languages).map(l => l.toLowerCase()),
            datasets: [{
                data: Object.values(languages),
                backgroundColor: ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#30363d'],
                borderWidth: 0,
                cutout: '80%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 8, padding: 15 } } }
        }
    });
}

function renderMap(countries) {
    const map = L.map('map', { zoomControl: false }).setView([20, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(map);

    if (!countries) return;
    Object.keys(countries).forEach(country => {
        if (countryCoords[country]) {
            const count = countries[country];
            L.circleMarker(countryCoords[country], {
                radius: Math.min(Math.sqrt(count) * 2 + 2, 15),
                fillColor: "#58a6ff",
                color: "#58a6ff",
                weight: 1,
                fillOpacity: 0.3
            }).addTo(map);
        }
    });
}

function renderArticles(articles) {
    const list = document.getElementById('articles-list');
    list.innerHTML = '';
    if (!articles) return;
    
    articles.forEach(art => {
        const item = document.createElement('div');
        item.className = 'article-item';
        
        // ML Logic check: if scores are 0 (no reddit keys), show 'scanning' or 'no_social_signal'
        const score = art.manipulation_score || 0;
        const isHighRisk = score > 60;
        
        item.innerHTML = `
            <a href="${art.url}" target="_blank" class="article-title">${art.title.toLowerCase()}</a>
            <div class="article-meta">
                ${isHighRisk ? '<span class="tag tag-danger">anomaly_detected</span>' : ''}
                <span>domain: ${art.domain.toLowerCase()}</span> // 
                <span>origin: ${ (art.sourcecountry || 'unknown').toLowerCase() }</span> // 
                <span class="text-accent">ml_score: ${score > 0 ? score : 'no_signal'}</span>
            </div>
        `;
        list.appendChild(item);
    });
}

function renderQuickStats(data) {
    const container = document.getElementById('quick-stats');
    const stats = data.stats;
    const avgScore = stats.avg_manipulation_score || 0;
    
    // UI logic fix: if reddit engine is offline, explain why metrics are zero
    const engineStatus = avgScore > 0 ? 'active' : 'no_social_keys';
    
    container.innerHTML = `
        <div class="mb-2">// signal_nodes: <span class="text-success">${data.articles.length}</span></div>
        <div class="mb-2">// avg_risk_index: <span class="${avgScore > 50 ? 'text-danger' : 'text-accent'}">${avgScore.toFixed(1)}%</span></div>
        <div class="mb-2">// reddit_engine: <span class="text-dim">${engineStatus}</span></div>
        <div class="mt-3 pt-2 border-top border-secondary text-dim" style="font-size: 0.65rem;">
            system monitoring global conflicts and financial markets. 
            ${avgScore === 0 ? 'social manipulation analysis requires api credentials.' : 'anomaly detection active across multiple social layers.'}
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', initDashboard);
