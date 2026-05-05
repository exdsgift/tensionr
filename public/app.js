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

// Colors
const COLOR_GREEN = '#3fb950';
const COLOR_WHITE = '#ffffff';
const COLOR_DIM = '#8b949e';
const COLOR_BORDER = '#30363d';

Chart.defaults.color = COLOR_DIM;
Chart.defaults.font.family = "'JetBrains Mono', monospace";
Chart.defaults.font.size = 9;
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';

let mapInstance = null;
let charts = {};

function logSystem(msg) {
    const log = document.getElementById('system-log');
    if (!log) return;
    const time = new Date().toLocaleTimeString().toLowerCase();
    log.innerHTML += `[${time}] ${msg}<br>`;
    log.scrollTop = log.scrollHeight;
    if (log.innerHTML.split('<br>').length > 20) {
        log.innerHTML = log.innerHTML.split('<br>').slice(-20).join('<br>');
    }
}

function formatDate(isoStr) {
    if (!isoStr) return "--:--";
    try {
        const d = new Date(isoStr);
        if (isNaN(d.getTime())) {
            // Fallback for GDELT format: 20260505T130000Z
            const parts = isoStr.match(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})/);
            if (parts) return `${parts[4]}:${parts[5]} ${parts[3]}/${parts[2]}`;
            return isoStr.substring(0, 10);
        }
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " " + d.toLocaleDateString([], { day: '2-digit', month: '2-digit' });
    } catch { return "--:--" }
}

async function updateDashboard() {
    logSystem("syncing signal...");
    try {
        const response = await fetch('../data/latest.json?t=' + new Date().getTime());
        const payload = await response.json();
        const data = payload.data;
        const signature = payload.signature;

        document.getElementById('last-updated').textContent = `sync: ${new Date(data.last_updated).toLocaleTimeString().toLowerCase()} // sig: ${signature.substring(0,6)}`;

        renderTimeline(data.timeline_vol);
        renderDomains(data.stats.top_domains);
        renderLanguages(data.stats.languages);
        renderMap(data.stats.source_countries);
        renderArticles(data.articles);
        renderQuickStats(data);
        renderContrast(data.articles);

        logSystem(`handshake success. ${data.articles.length} nodes verified.`);
    } catch (error) {
        logSystem("sync failed: packet loss");
        console.error(error);
    }
}

function renderTimeline(timeline) {
    const ctx = document.getElementById('timelineChart').getContext('2d');
    const hasData = timeline && timeline.length > 0;
    const labels = hasData ? timeline.map(item => `${item.datetime.substring(9,11)}:00`) : Array(12).fill("--");
    const values = hasData ? timeline.map(item => item.value) : Array(12).fill(0);

    if (charts.timeline) charts.timeline.destroy();
    charts.timeline = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                borderColor: COLOR_GREEN,
                backgroundColor: 'rgba(63, 185, 80, 0.05)',
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: 'rgba(255, 255, 255, 0.03)' }, beginAtZero: true }
            }
        }
    });
}

function renderDomains(domains) {
    const ctx = document.getElementById('domainsChart').getContext('2d');
    const hasData = domains && Object.keys(domains).length > 0;
    const labels = hasData ? Object.keys(domains).map(d => d.toLowerCase()) : ["none"];
    const values = hasData ? Object.values(domains) : [0];

    if (charts.domains) charts.domains.destroy();
    charts.domains = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: COLOR_GREEN,
                borderRadius: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
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
    const labels = hasData ? Object.keys(languages).map(l => l.toLowerCase()) : ["none"];
    const values = hasData ? Object.values(languages) : [1];

    if (charts.languages) charts.languages.destroy();
    charts.languages = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: hasData ? [COLOR_GREEN, COLOR_WHITE, '#2ea043', '#238636', COLOR_BORDER] : [COLOR_BORDER],
                borderWidth: 0,
                cutout: '85%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'bottom', labels: { boxWidth: 6, padding: 8, font: { size: 8 } } }
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
                radius: Math.min(Math.sqrt(count) * 2 + 2, 12),
                fillColor: COLOR_GREEN,
                color: COLOR_GREEN,
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

        item.innerHTML = `
            <a href="${art.url}" target="_blank" class="article-title">${art.title.toLowerCase()}</a>
            <div class="article-meta">
                ${isHighRisk ? '<span class="tag tag-danger">anomaly</span>' : ''}
                <span class="tag">${art.source || 'rss'}</span>
                <span>${art.domain.toLowerCase()}</span> // 
                <span class="text-success">${formatDate(art.seendate)}</span> // 
                <span class="text-success">risk: ${score}%</span>
            </div>
        `;
        list.appendChild(item);
    });
}

function renderContrast(articles) {
    const list = document.getElementById('contrast-list');
    list.innerHTML = '';
    articles.slice(0, 8).forEach(art => {
        const card = document.createElement('div');
        card.className = 'contrast-card';
        const bias = art.manipulation_score > 60 ? 'bias detected' : 'neutral';
        card.innerHTML = `
            <span class="source-tag">${art.domain.toLowerCase()}</span>
            <div class="article-title">"${art.title.toLowerCase()}"</div>
            <div class="text-dim" style="font-size: 0.6rem;">
                >> analysis: <span class="${art.manipulation_score > 60 ? 'text-danger' : 'text-success'}">${bias}</span> // 
                time: ${formatDate(art.seendate)}
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
        <div class="mb-1">// nodes: <span class="text-success">${data.articles.length}</span></div>
        <div class="mb-1">// risk: <span class="${avgScore > 50 ? 'text-danger' : 'text-success'}">${avgScore.toFixed(1)}%</span></div>
        <div class="mb-1">// layer: <span class="text-dim">multi_platform</span></div>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    logSystem("booting engine...");
    updateDashboard();
    setInterval(updateDashboard, 30000); // 30s refresh
});
