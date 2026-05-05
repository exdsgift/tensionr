const countryCoords = {
    "United States": [38.8951, -77.0364],   // Washington DC ✓
    "United Kingdom": [51.5074, -0.1278],    // London ✓
    "Qatar": [25.2854, 51.5310],             // Doha ✓
    "France": [48.8566, 2.3522],             // Paris ✓
    "Russia": [55.7558, 37.6173],            // Moscow ✓
    "Japan": [35.6762, 139.6503],            // Tokyo ✓
    "Australia": [-35.2809, 149.1300],       // Canberra ✓
    "India": [28.6139, 77.2090],             // New Delhi ✓
    "Israel": [31.7683, 35.2137],            // Jerusalem ✓
    "Ukraine": [50.4501, 30.5234],           // Kyiv ✓
    "Singapore": [1.3521, 103.8198],         // Singapore ✓
    "Canada": [45.4215, -75.6972],           // Ottawa ✓
    "Saudi Arabia": [24.6877, 46.7219],      // Riyadh ✗ → corretto
    "Uruguay": [-34.9011, -56.1645],         // Montevideo ✓
    "Iran": [35.6892, 51.3890],              // Tehran ✓
    "China": [39.9042, 116.4074],            // Beijing ✓
    "Germany": [52.5200, 13.4050],           // Berlin ✓
    "Turkey": [39.9334, 32.8597],            // Ankara ✓
    "Egypt": [30.0444, 31.2357],             // Cairo ✓
    "United Arab Emirates": [24.4539, 54.3773], // Abu Dhabi ✓
    "South Korea": [37.5665, 126.9780],
    "North Korea": [39.0392, 125.7625],
    "Taiwan": [25.0330, 121.5654],
    "Pakistan": [33.6844, 73.0479],
    "Syria": [33.5138, 36.2765],
    "Lebanon": [33.8938, 35.5018],
    "Yemen": [15.3694, 44.1910],
    "Iraq": [33.3152, 44.3661],
    "Afghanistan": [34.5553, 69.2075],
    "Mexico": [19.4326, -99.1332],
    "Brazil": [-15.7975, -47.8919],
    "Venezuela": [10.4806, -66.9036],
    "Colombia": [4.7110, -74.0721],
    "South Africa": [-25.7479, 28.2293],
    "Nigeria": [9.0579, 7.4951],
    "Kenya": [-1.2921, 36.8219],
    "Somalia": [2.0469, 45.3182],
    "Sudan": [15.5007, 32.5599],
    "Ethiopia": [9.0300, 38.7400],
    "Poland": [52.2297, 21.0122],
    "Italy": [41.9028, 12.4964],
    "Spain": [40.4168, -3.7038],
    "Palestine": [31.9038, 35.2034]
};

// Dynamic Theme Colors
let THEME_BRIGHT, THEME_MID, THEME_DIM, COLOR_WHITE, COLOR_BORDER;

function updateThemeColors() {
    const root = getComputedStyle(document.documentElement);
    THEME_BRIGHT = root.getPropertyValue('--theme-bright').trim();
    THEME_MID = root.getPropertyValue('--theme-mid').trim();
    THEME_DIM = root.getPropertyValue('--theme-dim').trim();
    COLOR_WHITE = root.getPropertyValue('--text-main').trim();
    COLOR_BORDER = root.getPropertyValue('--border').trim();

    Chart.defaults.color = root.getPropertyValue('--text-dim').trim();
    Chart.defaults.font.family = "'Fira Code', monospace";
    Chart.defaults.font.size = 10;
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';
    
    const liveIndicator = document.getElementById('live-indicator');
    if(liveIndicator) liveIndicator.style.color = THEME_BRIGHT;
}

function setTheme(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem('tensionr_theme', themeName);
    updateThemeColors();
    
    // Re-render charts and map with new colors if data is already loaded
    if (window.lastData) {
        safeRender('emotions', () => renderEmotions(window.lastData.articles));
        safeRender('map', () => renderMap(window.lastData.stats.source_countries, window.lastData.articles));
        safeRender('wordcloud', () => renderWordCloud(window.lastData.stats.top_keywords));
        // Force refresh feed to update colors
        const dedupedArticles = deduplicateArticles(window.lastData.articles);
        safeRender('articles', () => initRotatingFeed('articles-list', dedupedArticles, 6));
    }
}

// Load saved theme
const savedTheme = localStorage.getItem('tensionr_theme') || 'phosphor';
document.documentElement.setAttribute('data-theme', savedTheme);
updateThemeColors();

let mapInstance = null;
let charts = {};

function logSystem(msg) {
    const log = document.getElementById('system-log');
    if (log) { // The terminal might be removed
        const time = new Date().toLocaleTimeString().toLowerCase();
        log.innerHTML += `[${time}] ${msg}<br>`;
        log.scrollTop = log.scrollHeight;
    }
}

function formatDate(isoStr) {
    if (!isoStr) return "--:--";
    try {
        // Handle GDELT formats like 20260505T130000Z or ISO
        const parts = isoStr.match(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})/);
        if (parts) return `${parts[4]}:${parts[5]} ${parts[3]}/${parts[2]}`;
        
        const d = new Date(isoStr);
        if (!isNaN(d.getTime())) {
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " " + d.toLocaleDateString([], { day: '2-digit', month: '2-digit' });
        }
        return isoStr.substring(0, 10);
    } catch { return "--:--" }
}

async function updateDashboard() {
    logSystem("syncing telemetry...");
    try {
        const response = await fetch('../data/latest.json?t=' + new Date().getTime());
        const payload = await response.json();
        const data = payload.data;
        const signature = payload.signature;
        
        window.lastData = data; // Save for theme switcher

        document.getElementById('last-updated').textContent = `sync: ${new Date(data.last_updated).toLocaleTimeString().toLowerCase()}   sig: ${signature.substring(0,6)}`;

        const dedupedArticles = deduplicateArticles(data.articles);

        // Safe execution of all renders
        safeRender('emotions', () => renderEmotions(data.articles));
        safeRender('map', () => renderMap(data.stats.source_countries, data.articles));
        
        safeRender('articles', () => initRotatingFeed('articles-list', dedupedArticles, 6));
        safeRender('stats', () => renderQuickStats(data));
        safeRender('wordcloud', () => renderWordCloud(data.stats.top_keywords));
        logSystem(`handshake success. ${data.articles.length} nodes active.`);

        // Trigger subtle aesthetic refresh animation
        document.querySelectorAll('.card').forEach(card => {
            card.classList.remove('fade-update');
            void card.offsetWidth; // trigger reflow
            card.classList.add('fade-update');
        });
    } catch (error) {
        logSystem("sync failed: packet loss");
        console.error(error);
    }
}

function safeRender(name, fn) {
    try {
        fn();
    } catch (e) {
        logSystem(`warning: component_${name} failure`);
        console.warn(`render error in ${name}:`, e);
    }
}

function renderEmotions(articles) {
    const ctx = document.getElementById('emotionChart').getContext('2d');
    const counts = { anger: 0, fear: 0, sadness: 0, surprise: 0, neutral: 0 };
    articles.forEach(a => {
        if (a.narrative_emotion && counts[a.narrative_emotion] !== undefined) {
            counts[a.narrative_emotion]++;
        } else if (a.narrative_emotion) {
            counts.neutral++;
        }
    });
    
    const labels = Object.keys(counts);
    const data = Object.values(counts);

    if (charts.emotions) charts.emotions.destroy();
    charts.emotions = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'signals',
                data: data,
                backgroundColor: THEME_BRIGHT + '33', // 20% opacity hex
                borderColor: THEME_BRIGHT,
                pointBackgroundColor: THEME_BRIGHT,
                pointBorderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                r: {
                    angleLines: { color: 'rgba(255,255,255,0.1)' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    pointLabels: { color: THEME_MID, font: { family: "'Fira Code', monospace", size: 10 } },
                    ticks: { display: false, backdropColor: 'transparent' }
                }
            }
        }
    });
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
    const max = Math.max(...entries.map(e => e[1]));
    
    entries.forEach(([word, count]) => {
        const size = 0.55 + (count / max) * 1.1;
        const opacity = 0.4 + (count / max) * 0.6;
        const color = count > max * 0.6 ? THEME_BRIGHT : THEME_MID;
        
        const span = document.createElement('span');
        span.className = 'word-item';
        span.style.fontSize = `${size}rem`;
        span.style.opacity = opacity;
        span.style.color = color;
        span.style.margin = '1px 4px';
        span.style.animation = `floatText ${2 + Math.random() * 2}s ease-in-out infinite`;
        span.style.animationDelay = `${Math.random()}s`;
        span.textContent = word.toLowerCase();
        container.appendChild(span);
    });
}

function renderMap(countries, articles) {
    if (mapInstance) mapInstance.remove();
    mapInstance = L.map('map', { 
        zoomControl: false,
        dragging: false,
        touchZoom: false,
        doubleClickZoom: false,
        scrollWheelZoom: false,
        boxZoom: false,
        keyboard: false,
        zoomSnap: 0.1,
        zoomDelta: 0.1
    }).setView([25, 0], 1.3);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(mapInstance);

    if (!countries || !articles) return;
    Object.keys(countries).forEach(country => {
        if (countryCoords[country]) {
            const count = countries[country];
            const snippet = articles.find(a => a.sourcecountry === country)?.title.toLowerCase() || 'multi-node activity';
            
            const icon = L.divIcon({
                className: 'pulse-icon',
                html: `<div class="pulse-ring" style="animation-delay: ${Math.random() * 2}s"></div><div class="pulse-dot"></div>`,
                iconSize: [0, 0],
                iconAnchor: [0, 0],
                popupAnchor: [0, -10]
            });
            
            L.marker(countryCoords[country], {icon: icon})
              .addTo(mapInstance)
              .bindPopup(`<div style="font-family:'Fira Code'; font-size: 0.7rem; color: var(--text-main); background: transparent; padding: 5px; border: none;"><b>${country.toLowerCase()}</b><br>${count} signals detected<br><hr style="margin:5px 0; border-color: var(--border);">"${snippet}"</div>`);
        }
    });
}

function deduplicateArticles(articles) {
    const grouped = {};
    articles.forEach(art => {
        const normTitle = art.title.toLowerCase().replace(/[^\w\s]/gi, '').substring(0, 40);
        if (!grouped[normTitle]) {
            grouped[normTitle] = { ...art, all_domains: new Set([art.domain]) };
        } else {
            grouped[normTitle].all_domains.add(art.domain);
            if ((art.manipulation_score || 0) > (grouped[normTitle].manipulation_score || 0)) {
                grouped[normTitle].manipulation_score = art.manipulation_score;
                grouped[normTitle].narrative_emotion = art.narrative_emotion;
            }
        }
    });
    return Object.values(grouped).map(art => {
        art.domain = Array.from(art.all_domains).join(', ');
        return art;
    });
}

let feedsIntervals = {};
function initRotatingFeed(containerId, articles, maxVisible) {
    const container = document.getElementById(containerId);
    if (!container) return;
    if (feedsIntervals[containerId]) clearInterval(feedsIntervals[containerId]);

    if (!articles || articles.length === 0) {
        container.innerHTML = '<div class="text-dim text-center py-5">no active signals</div>';
        return;
    }

    let buffer = [...articles];
    let visible = buffer.splice(0, Math.min(maxVisible, buffer.length));

    function render() {
        container.innerHTML = '';
        visible.forEach((art, index) => {
            const item = document.createElement('div');
            item.className = 'article-item';
            if (index === 0 && buffer.length > 0) item.classList.add('feed-item-enter');

            const score = art.manipulation_score || 0;
            const emotion = art.narrative_emotion && art.narrative_emotion !== 'unknown' ? art.narrative_emotion : '';
            const domainsHtml = art.domain.split(', ').map(d => `<span class="tag" style="color:var(--theme-bright); border-color:var(--theme-dim)">${d}</span>`).join('');
            const riskLabel = score > 60 ? 'high' : (score > 30 ? 'moderate' : 'baseline');
            const emotionTag = emotion ? `<span class="tag" style="color:var(--theme-bright); border-color:var(--theme-bright)">${emotion}</span>` : '';
            item.innerHTML = `
                <div style="display:flex; justify-content: space-between; align-items: baseline; gap: 10px;">
                    <a href="${art.url}" target="_blank" class="article-title" style="flex-grow: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${art.title.toLowerCase()}</a>
                    <span class="text-dim" style="font-size: 0.55rem; white-space: nowrap;">${formatDate(art.seendate)}</span>
                </div>
                <div class="article-meta" style="display:flex; flex-wrap:wrap; gap:4px; align-items:center; margin-top:2px;">
                    ${score > 60 ? '<span class="tag" style="color:#ff5555; border-color:#ff5555">anomaly</span>' : ''}
                    ${emotionTag} ${domainsHtml} 
                <span style="color:var(--theme-mid); margin-left: 4px;">  risk: <span style="color:${score > 60 ? '#ff5555' : 'var(--theme-bright)'}">${riskLabel} (${score}%)</span></span>
                </div>
            `;
            container.appendChild(item);
        });
    }

    render();
    if (buffer.length > 0) {
        feedsIntervals[containerId] = setInterval(() => {
            buffer.push(visible.pop());
            visible.unshift(buffer.shift());
            render();
        }, 3500 + Math.random() * 2000);
    }
}

function renderQuickStats(data) {
    const container = document.getElementById('top-telemetry-ticker');
    if (!container) return;
    const stats = data.stats;
    const avgScore = stats.avg_risk || 0;
    const criticalCount = stats.critical_anomalies || 0;
    
    container.innerHTML = `
        <div title="Total number of unique intelligence nodes currently stored in local memory (max 500).">
            monitored_signals: <span style="color:var(--theme-bright)">${data.articles.length}</span>
        </div>
        <div title="Number of intercepted nodes with a narrative bias risk score exceeding 60%.">
            critical_anomalies: <span style="color:${criticalCount > 0 ? '#ff5555' : 'var(--theme-bright)'}">${criticalCount}</span>
        </div>
        <div title="The average manipulation and bias risk across all monitored signals.">
            average_risk: <span style="color:${avgScore > 50 ? '#ff5555' : 'var(--theme-bright)'}">${avgScore.toFixed(1)}%</span>
        </div>
        <div title="Digital integrity verification status for the current telemetry packet.">
            integrity: <span style="color: #3fb950">verified</span>
        </div>
    `;
}

document.addEventListener('DOMContentLoaded', () => {
    logSystem("booting intelligence engine...");
    updateDashboard();
    setInterval(updateDashboard, 40000);
});
