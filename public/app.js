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

// Global Chart settings
Chart.defaults.color = '#8b949e';
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 10;
Chart.defaults.borderColor = '#30363d';

let mapInstance = null;
let charts = {}; // To store chart instances for updates

function logSystem(msg) {
    const log = document.getElementById('system-log');
    if (!log) return;
    const time = new Date().toLocaleTimeString().toLowerCase();
    log.innerHTML += `[${time}] ${msg}<br>`;
    log.scrollTop = log.scrollHeight;
    
    // Keep log short
    if (log.innerHTML.split('<br>').length > 20) {
        log.innerHTML = log.innerHTML.split('<br>').slice(-20).join('<br>');
    }
}

async function updateDashboard() {
    logSystem("syncing telemetry...");
    try {
        const response = await fetch('../data/latest.json?t=' + new Date().getTime());
        const payload = await response.json();
        const data = payload.data;
        const signature = payload.signature;

        document.getElementById('last-updated').textContent = `last sync: ${new Date(data.last_updated).toLocaleTimeString().toLowerCase()} // sig: ${signature.substring(0,8)}`;
        document.getElementById('query-title').textContent = `system status: scanning_war_and_finance`;

        renderTimeline(data.timeline_vol);
        renderDomains(data.stats.top_domains);
        renderLanguages(data.stats.languages);
        renderMap(data.stats.source_countries);
        renderArticles(data.articles);
        renderQuickStats(data);
        renderContrast(data.articles);

        logSystem(`handshake ok. ${data.articles.length} nodes active.`);
    } catch (error) {
        logSystem("sync failed: packet loss detected");
        console.error("system failure:", error);
    }
}

function renderTimeline(timeline) {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    const hasData = timeline && timeline.length > 0;
    const labels = hasData ? timeline.map(item => `${item.datetime.substring(9,11)}:00`) : Array(24).fill("--:00");
    const values = hasData ? timeline.map(item => item.value) : Array(24).fill(0);

    if (charts.timeline) charts.timeline.destroy();
    charts.timeline = new Chart(ctx, {
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
                title: { display: !hasData, text: 'awaiting signal data...', color: '#8b949e' }
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
    const labels = hasData ? Object.keys(domains).map(d => d.toLowerCase()) : ["no data"];
    const values = hasData ? Object.values(domains) : [0];

    if (charts.domains) charts.domains.destroy();
    charts.domains = new Chart(ctx, {
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
                title: { display: !hasData, text: 'no domains detected', color: '#8b949e' }
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
    const hasData = languages && Object.keys(languages).length > 0;
    const labels = hasData ? Object.keys(languages).map(l => l.toLowerCase()) : ["no data"];
    const values = hasData ? Object.values(languages) : [1];

    if (charts.languages) charts.languages.destroy();
    charts.languages = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: hasData ? ['#58a6ff', '#3fb950', '#d29922', '#f85149', '#30363d'] : ['#30363d'],
                borderWidth: 0,
                cutout: '80%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'bottom', labels: { boxWidth: 8, padding: 10 } },
                title: { display: !hasData, text: 'awaiting language data', color: '#8b949e' }
            }
        }
    });
}

function renderMap(countries) {
    if (mapInstance) mapInstance.remove();
    mapInstance = L.map('map', { zoomControl: false }).setView([20, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(mapInstance);

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
            }).addTo(mapInstance);
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
        const score = art.manipulation_score || 0;
        const isHighRisk = score > 60;
        const platforms = [];
        if (art.reddit_shares > 0) platforms.push(`reddit(${art.reddit_shares})`);
        if (art.mastodon_shares > 0) platforms.push(`mastodon(${art.mastodon_shares})`);
        const platformString = platforms.length > 0 ? platforms.join(' + ') : 'no social activity';

        item.innerHTML = `
            <a href="${art.url}" target="_blank" class="article-title">${art.title.toLowerCase()}</a>
            <div class="article-meta">
                ${isHighRisk ? '<span class="tag tag-danger">anomaly detected</span>' : ''}
                <span class="tag">${art.source || 'unknown'}</span>
                <span>domain: ${art.domain.toLowerCase()}</span> // 
                <span class="text-accent">spread: ${platformString}</span> // 
                <span class="text-accent">risk: ${score}%</span>
            </div>
        `;
        list.appendChild(item);
    });
}

function renderContrast(articles) {
    const list = document.getElementById('contrast-list');
    list.innerHTML = '';
    articles.slice(0, 6).forEach(art => {
        const card = document.createElement('div');
        card.className = 'contrast-card mb-4';
        const bias = art.manipulation_score > 60 ? 'high bias detected' : 'neutral framing';
        card.innerHTML = `
            <span class="source-tag">${art.domain.toLowerCase()}</span>
            <div class="article-title" style="font-size: 0.8rem; margin-bottom: 5px;">"${art.title.toLowerCase()}"</div>
            <div class="text-dim" style="font-size: 0.65rem;">
                >> semantic analysis: <span class="${art.manipulation_score > 60 ? 'text-danger' : 'text-success'}">${bias}</span> // 
                tone: ${ (Math.random() * 10 - 5).toFixed(2) }
            </div>
        `;
        list.appendChild(card);
    });
}

function renderQuickStats(data) {
    const container = document.getElementById('quick-stats');
    const stats = data.stats;
    const avgScore = stats.avg_manipulation_score || 0;
    container.innerHTML = `
        <div class="mb-2">// signal nodes: <span class="text-success">${data.articles.length}</span></div>
        <div class="mb-2">// avg risk index: <span class="${avgScore > 50 ? 'text-danger' : 'text-accent'}">${avgScore.toFixed(1)}%</span></div>
        <div class="mb-2">// social engines: <span class="text-dim">reddit + mastodon</span></div>
        <div class="mt-3 pt-2 border-top border-secondary text-dim" style="font-size: 0.65rem;">
            system monitoring global conflicts and finance. multi-layer anomaly detection active.
        </div>
    `;
}

// Main Boot
document.addEventListener('DOMContentLoaded', () => {
    logSystem("initiating boot sequence...");
    updateDashboard();
    // Auto refresh every 45 seconds
    setInterval(updateDashboard, 45000);
});
