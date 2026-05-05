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

// Colors - Lime Shades
const LIME_BRIGHT = '#ccff00';
const LIME_MID = '#3fb950';
const LIME_DIM = '#238636';
const COLOR_WHITE = '#ffffff';
const COLOR_BORDER = '#30363d';

Chart.defaults.color = '#8b949e';
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
}

function formatDate(isoStr) {
    if (!isoStr) return "--:--";
    try {
        const d = new Date(isoStr);
        if (isNaN(d.getTime())) {
            const parts = isoStr.match(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})/);
            if (parts) return `${parts[4]}:${parts[5]} ${parts[3]}/${parts[2]}`;
            return isoStr.substring(0, 10);
        }
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " " + d.toLocaleDateString([], { day: '2-digit', month: '2-digit' });
    } catch { return "--:--" }
}

async function updateDashboard() {
    logSystem("syncing telemetry...");
    try {
        const response = await fetch('../data/latest.json?t=' + new Date().getTime());
        const payload = await response.json();
        const data = payload.data;
        const signature = payload.signature;

        document.getElementById('last-updated').textContent = `sync: ${new Date(data.last_updated).toLocaleTimeString().toLowerCase()} // sig: ${signature.substring(0,6)}`;

        renderTimeline(data.timeline_vol);
        renderDomains(data.stats.top_domains);
        renderLanguages(data.stats.languages);
        renderMap(data.stats.source_countries, data.articles);
        renderArticles(data.articles);
        renderQuickStats(data);
        renderContrast(data.articles);
        renderWordCloud(data.stats.top_keywords);

        logSystem(`handshake success. ${data.articles.length} nodes active.`);
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
                borderColor: LIME_BRIGHT,
                backgroundColor: 'rgba(204, 255, 0, 0.05)',
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
                backgroundColor: LIME_MID,
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
                backgroundColor: hasData ? [LIME_BRIGHT, COLOR_WHITE, LIME_MID, LIME_DIM, COLOR_BORDER] : [COLOR_BORDER],
                borderWidth: 0,
                cutout: '82%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { position: 'bottom', labels: { boxWidth: 6, padding: 5, font: { size: 8 } } }
            }
        }
    });
}

function renderWordCloud(keywords) {
    const container = document.getElementById('word-cloud');
    if (!container || !keywords) return;
    container.innerHTML = '';
    
    const entries = Object.entries(keywords);
    const max = Math.max(...entries.map(e => e[1]));
    
    entries.forEach(([word, count]) => {
        const size = 0.5 + (count / max) * 1;
        const opacity = 0.3 + (count / max) * 0.7;
        const color = count > max * 0.7 ? LIME_BRIGHT : LIME_MID;
        
        const span = document.createElement('span');
        span.className = 'word-item';
        span.style.fontSize = `${size}rem`;
        span.style.opacity = opacity;
        span.style.color = color;
        span.textContent = word.toLowerCase();
        container.appendChild(span);
    });
}

function renderMap(countries, articles) {
    if (mapInstance) mapInstance.remove();
    mapInstance = L.map('map', { zoomControl: false }).setView([20, 0], 2);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(mapInstance);

    if (!countries) return;
    Object.keys(countries).forEach(country => {
        if (countryCoords[country]) {
            const count = countries[country];
            // Get a random snippet for this country if available
            const snippet = articles.find(a => a.sourcecountry === country)?.title.toLowerCase() || 'no snippet available';
            
            L.circleMarker(countryCoords[country], {
                radius: Math.min(Math.sqrt(count) * 2 + 2, 12),
                fillColor: LIME_BRIGHT,
                color: LIME_BRIGHT,
                weight: 1,
                fillOpacity: 0.3
            }).addTo(mapInstance).bindPopup(`<div style="font-family:'JetBrains Mono'; font-size: 0.7rem; color: #000;"><b>${country.toLowerCase()}</b><br>${count} nodes<br><hr style="margin:5px 0;">"${snippet}"</div>`);
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
                <span class="tag" style="color:var(--lime-bright); border-color:var(--lime-dim)">${art.source || 'rss'}</span>
                <span>${art.domain.toLowerCase()}</span> // 
                <span style="color:var(--lime-mid)">${formatDate(art.seendate)}</span> // 
                <span style="color:var(--lime-bright)">risk: ${score}%</span>
            </div>
        `;
        list.appendChild(item);
    });
}

function renderContrast(articles) {
    const list = document.getElementById('contrast-list');
    list.innerHTML = '';
    articles.slice(0, 10).forEach(art => {
        const card = document.createElement('div');
        card.className = 'contrast-card';
        const bias = art.manipulation_score > 60 ? 'high bias' : 'neutral';
        card.innerHTML = `
            <span class="source-tag">${art.domain.toLowerCase()}</span>
            <div class="article-title">"${art.title.toLowerCase()}"</div>
            <div class="text-dim" style="font-size: 0.58rem;">
                >> semantic analysis: <span style="color:${art.manipulation_score > 60 ? 'var(--danger)' : 'var(--lime-bright)'}">${bias}</span> // 
                timestamp: ${formatDate(art.seendate)}
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
        <div class="mb-1">// nodes active: <span style="color:var(--lime-bright)">${data.articles.length}</span></div>
        <div class="mb-1">// risk index: <span style="color:${avgScore > 50 ? 'var(--danger)' : 'var(--lime-bright)'}">${avgScore.toFixed(1)}%</span></div>
        <div class="mb-1">// integrity: <span class="text-dim">verified</span></div>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    logSystem("booting intelligence engine...");
    updateDashboard();
    setInterval(updateDashboard, 40000);
});
