const countryCoords = {
    "United States": [38.8951, -77.0364],
    "United Kingdom": [51.5074, -0.1278],
    "Qatar": [25.2854, 51.5310],
    "France": [48.8566, 2.3522],
    "Russia": [55.7558, 37.6173],
    "Russian Federation": [55.7558, 37.6173],
    "Japan": [35.6762, 139.6503],
    "Australia": [-35.2809, 149.1300],
    "India": [28.6139, 77.2090],
    "Israel": [31.7683, 35.2137],
    "Ukraine": [50.4501, 30.5234],
    "Singapore": [1.3521, 103.8198],
    "Canada": [45.4215, -75.6972],
    "Saudi Arabia": [24.6877, 46.7219],
    "Uruguay": [-34.9011, -56.1645],
    "Iran": [35.6892, 51.3890],
    "China": [39.9042, 116.4074],
    "Germany": [52.5200, 13.4050],
    "Turkey": [39.9334, 32.8597],
    "Egypt": [30.0444, 31.2357],
    "United Arab Emirates": [24.4539, 54.3773],
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
        safeRender('articles', () => initRotatingFeed('articles-list', dedupedArticles, 7));
    }
}

// Load saved theme
const savedTheme = localStorage.getItem('tensionr_theme') || 'phosphor';
document.documentElement.setAttribute('data-theme', savedTheme);

// Global State
let maps = { news: null, flights: null };
let mapMarkers = { news: [], flights: [] };
let charts = {};
let globalFilter = { country: null, keyword: null };
let activeDate = new Date().toISOString().split('T')[0];

function setGlobalFilter(type, value) {
    if (globalFilter[type] === value) {
        globalFilter[type] = null; // Toggle off if clicking the same
    } else {
        globalFilter[type] = value;
    }
    logSystem(`filter updated: ${type}=${value || 'all'}`);
    updateURL();
    refreshFilteredUI();
}

function clearFilters() {
    globalFilter = { country: null, keyword: null };
    logSystem("filters cleared");
    updateURL();
    refreshFilteredUI();
}

function refreshFilteredUI() {
    if (!window.lastData) return;
    
    const filteredArticles = applyFilters(window.lastData.articles);
    
    // Update dependent components
    safeRender('emotions', () => renderEmotions(filteredArticles));
    safeRender('articles', () => initRotatingFeed('articles-list', filteredArticles, 7));
    
    // Update filter indicators in UI
    updateFilterUI();
}

function applyFilters(articles) {
    if (!articles) return [];
    return articles.filter(a => {
        let match = true;
        if (globalFilter.country) {
            match = match && (a.sourcecountry === globalFilter.country);
        }
        if (globalFilter.keyword) {
            const searchStr = `${a.title} ${a.summary} ${a.keywords || ''}`.toLowerCase();
            match = match && searchStr.includes(globalFilter.keyword.toLowerCase());
        }
        return match;
    });
}

function updateURL() {
    const params = new URLSearchParams();
    if (globalFilter.country) params.set('country', globalFilter.country);
    if (globalFilter.keyword) params.set('keyword', globalFilter.keyword);
    if (activeDate !== new Date().toISOString().split('T')[0]) params.set('date', activeDate);
    
    const newURL = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
    window.history.replaceState({ path: newURL }, '', newURL);
}

function loadStateFromURL() {
    const params = new URLSearchParams(window.location.search);
    globalFilter.country = params.get('country');
    globalFilter.keyword = params.get('keyword');
    const dateParam = params.get('date');
    if (dateParam) {
        activeDate = dateParam;
        const datePicker = document.getElementById('time-machine-date');
        if (datePicker) datePicker.value = activeDate;
    }
}

function updateFilterUI() {
    const indicator = document.getElementById('filter-status');
    if (!indicator) return;
    
    if (!globalFilter.country && !globalFilter.keyword) {
        indicator.style.display = 'none';
        return;
    }
    
    indicator.style.display = 'flex';
    let label = 'ACTIVE_FILTERS: ';
    if (globalFilter.country) label += `[LOC:${globalFilter.country.toUpperCase()}] `;
    if (globalFilter.keyword) label += `[KEY:${globalFilter.keyword.toUpperCase()}] `;
    
    indicator.querySelector('.filter-label').textContent = label.trim();
}

function initMaps() {
    // Re-check theme colors right before init to be sure
    updateThemeColors();
    
    if (!maps.news) {
        maps.news = L.map('map-news', { 
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
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(maps.news);
    }

    if (!maps.flights) {
        const flightContainer = document.getElementById('map-flights');
        if (flightContainer) {
            maps.flights = L.map('map-flights', { 
                zoomControl: false,
                dragging: false,
                touchZoom: false,
                doubleClickZoom: false,
                scrollWheelZoom: false,
                boxZoom: false,
                keyboard: false,
                zoomSnap: 0.1,
                zoomDelta: 0.1
            }).setView([25, 0], 1.1);
            L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png').addTo(maps.flights);
        }
    }
}

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

// Intelligence Web Worker Initialization
const intelligenceWorker = new Worker('worker.js');

intelligenceWorker.onmessage = function(e) {
    const { type, payload } = e.data;
    if (type === 'DATA_PROCESSED') {
        const { articles, keywords } = payload;
        
        // Update state
        if (window.lastData) {
            window.lastData.articles = articles;
            window.lastData.stats.top_keywords = keywords;
        }
        
        // Re-render WordCloud and refresh filtered views
        safeRender('wordcloud', () => renderWordCloudEnriched(keywords));
        refreshFilteredUI();
        
        logSystem("intelligence processed via background thread.");
    }
};

async function loadHistoricalData(date) {
    logSystem(`attempting time machine handshake: ${date}`);
    activeDate = date;
    updateURL();
    try {
        const resp = await fetch(`data/archive/${date}.json`);
        if (!resp.ok) throw new Error("snapshot_not_found");
        const archive = await resp.json();
        
        // Temporarily override UI for historical view
        renderSITREP(archive.sitrep, true);
        renderGTI(archive.gti);
        renderWordCloud(archive.top_keywords);
        
        document.getElementById('live-indicator').textContent = '● playback_mode';
        document.getElementById('live-indicator').style.color = '#ff922b';
        document.getElementById('last-updated').textContent = `archive: ${date}`;
        
        logSystem(`historical sync success. date: ${date}`);
    } catch (err) {
        logSystem(`time machine error: ${err.message}`);
        setTimeout(() => updateDashboard(), 3000); // Revert to live
    }
}

function renderSITREP(text, isHistorical = false) {
    const sitrepEl = document.getElementById('sitrep-text');
    const statusEl = document.getElementById('sitrep-status');
    if (!sitrepEl) return;

    const safeText = (text || "Intelligence synthesis active: monitoring global signals...").toLowerCase();
    // Wrap in a span to ensure display:inline-block works for the marquee effect
    sitrepEl.innerHTML = `<span>${safeText} &nbsp;&nbsp;...&nbsp;&nbsp; ${safeText} &nbsp;&nbsp;...&nbsp;&nbsp;</span>`;
    statusEl.textContent = isHistorical ? 'archived_intel' : 'live_stream';
}

function renderWordCloudEnriched(processedKeywords) {
    const container = document.getElementById('word-cloud');
    if (!container) return;
    container.innerHTML = '';
    
    if (processedKeywords.length === 0) {
        container.innerHTML = '<span class="text-dim">no tokens detected</span>';
        return;
    }
    
    const typeColors = {
        "GPE": THEME_BRIGHT,
        "ORG": THEME_MID,
        "PERSON": "#339af0",
        "LOC": "#ff922b",
        "NORP": "#d0d"
    };
    
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

// ... existing code ...

async function updateDashboard() {
    logSystem("syncing telemetry...");
    activeDate = new Date().toISOString().split('T')[0];
    updateURL();
    updateThemeColors();
    try {
        const t = new Date().getTime();
        const fetchFile = (file) => fetch(`data/${file}?t=${t}`).then(r => {
            if (!r.ok) throw new Error(`HTTP_${r.status}`);
            return r.json();
        });

        const [status, news, markets, telemetry, intel] = await Promise.all([
            fetchFile('status.json'),
            fetchFile('news.json'),
            fetchFile('markets.json'),
            fetchFile('telemetry.json'),
            fetchFile('intelligence.json')
        ]);
        
        window.lastData = { ...status, ...news, ...markets, ...telemetry, ...intel };

        document.getElementById('last-updated').textContent = `sync: ${new Date(status.last_updated).toLocaleTimeString().toLowerCase()}`;
        document.getElementById('live-indicator').textContent = '● live_feed';
        document.getElementById('live-indicator').style.color = THEME_BRIGHT;

        // Apply filters immediately to initial data
        refreshFilteredUI();

        // Offload heavy processing to Web Worker
        intelligenceWorker.postMessage({
            type: 'PROCESS_DATA',
            data: {
                articles: news.articles,
                keywords: news.stats.top_keywords
            }
        });

        // Immediate renders for lighter components
        safeRender('sitrep', () => renderSITREP(intel.sitrep || "synthesizing tactical reports..."));
        safeRender('gti', () => renderGTI(status.global_tension_index, status.gti_history));
        safeRender('flights', () => renderFlightIntel(telemetry.flight_intel));
        safeRender('map', () => {
            renderMap(news.stats.source_countries, news.articles);
            renderFlightMap(telemetry.flight_intel);
        });
        safeRender('cyber', () => renderCyberIntel(intel.cyber_intel));
        safeRender('chatter', () => renderRawChatter(intel.raw_chatter));
        safeRender('market', () => renderMarketTicker(markets.market_intel));
        safeRender('stats', () => renderQuickStats(news, status));
        
        logSystem(`handshake success. ${news.articles.length} nodes active.`);

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
    // Exclude neutral from the radar to let other emotions "breathe"
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
    const chartColor = THEME_BRIGHT || '#00ff41';

    // Log the distribution for the analyst
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
            layout: {
                padding: {
                    top: 10,
                    bottom: 10,
                    left: 10,
                    right: 10
                }
            },
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
                        color: THEME_MID || '#888', 
                        font: { family: "'Fira Code', monospace", size: 10 },
                        padding: 15
                    },
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
    // Support both simple and enriched keyword formats
    const max = Math.max(...entries.map(e => (typeof e[1] === 'object' ? e[1].count : e[1])));
    
    // Type colors
    const typeColors = {
        "GPE": THEME_BRIGHT,
        "ORG": THEME_MID,
        "PERSON": "#339af0",
        "LOC": "#ff922b",
        "NORP": "#d0d"
    };
    
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

function renderRawChatter(chatter) {
    const container = document.getElementById('raw-chatter-list');
    if (!container || !chatter || chatter.length === 0) return;
    
    container.innerHTML = '';
    chatter.forEach(item => {
        const div = document.createElement('div');
        div.style.borderBottom = '1px solid var(--border)';
        div.style.paddingBottom = '4px';
        div.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:2px;">
                <div style="display:flex; gap:5px; align-items:center;">
                    <span class="tag" style="color: #ff6b35; border-color: #ff6b35; font-size: 0.45rem;">UNVERIFIED</span>
                    <span style="font-size: 0.5rem; color: var(--text-dim); text-transform: uppercase;">SRC: ${item.source}</span>
                </div>
                <a href="${item.link}" target="_blank" style="color: var(--text-main); font-size: 0.62rem; text-decoration: none; line-height: 1.2;">${item.title.toLowerCase()}</a>
            </div>
        `;
        container.appendChild(div);
    });
}

function renderCyberIntel(intel) {
    const container = document.getElementById('cyber-threat-list');
    if (!container || !intel || intel.length === 0) return;
    
    container.innerHTML = '';
    intel.forEach(threat => {
        const item = document.createElement('div');
        item.style.borderBottom = '1px solid var(--border)';
        item.style.paddingBottom = '4px';
        item.innerHTML = `
            <div style="display:flex; flex-direction:column; gap:2px;">
                <div style="display:flex; gap:5px; align-items:center;">
                    <span class="tag" style="color: var(--theme-bright); border-color: var(--theme-bright); font-size: 0.45rem;">SEC_ALERT</span>
                    <span style="font-size: 0.5rem; color: var(--text-dim); text-transform: uppercase;">HANDSHAKE_ACTIVE</span>
                </div>
                <a href="${threat.link}" target="_blank" style="color: var(--text-main); font-size: 0.62rem; text-decoration: none; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${threat.title.toLowerCase()}</a>
            </div>
        `;
        container.appendChild(item);
    });
}

function renderMap(countries, articles) {
    if (!maps.news) initMaps();
    
    // Clear old markers
    mapMarkers.news.forEach(m => maps.news.removeLayer(m));
    mapMarkers.news = [];

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
            
            const marker = L.marker(countryCoords[country], {icon: icon})
              .addTo(maps.news)
              .on('click', () => setGlobalFilter('country', country))
              .bindPopup(`<div style="font-family:'Fira Code'; font-size: 0.7rem; color: var(--popup-text); background: transparent; padding: 5px; border: none;"><b>${country.toLowerCase()}</b><br>${count} signals detected<br><hr style="margin:5px 0; border-color: var(--border);">"${snippet}"</div>`);
            
            mapMarkers.news.push(marker);
        }
    });
}

let flightHistory = {};

function renderFlightMap(intel) {
    if (!maps.flights) initMaps();
    
    // Clear old markers (but we keep polylines for trails)
    mapMarkers.flights.forEach(m => maps.flights.removeLayer(m));
    mapMarkers.flights = [];

    // Hide connection pending overlay
    const overlay = document.querySelector('#map-flights div[style*="z-index: 1000"]');
    if (overlay && intel && intel.assets && intel.assets.length > 0) overlay.style.display = 'none';

    if (!intel || !intel.assets) return;

    // Track active ICAO24s to prune old history
    const activeIcaos = new Set();

    intel.assets.forEach(asset => {
        if (asset.lat && asset.lon) {
            activeIcaos.add(asset.icao24);
            
            // Update history for trails
            if (!flightHistory[asset.icao24]) {
                flightHistory[asset.icao24] = [];
            }
            
            const lastPos = flightHistory[asset.icao24][flightHistory[asset.icao24].length - 1];
            if (!lastPos || lastPos[0] !== asset.lat || lastPos[1] !== asset.lon) {
                flightHistory[asset.icao24].push([asset.lat, asset.lon]);
                // Keep only last 15 points for performance and "tail" effect
                if (flightHistory[asset.icao24].length > 15) flightHistory[asset.icao24].shift();
            }

            // 1. Strategic Trajectory (Origin -> Current)
            if (countryCoords[asset.origin]) {
                const originPos = countryCoords[asset.origin];
                const tacticalColor = asset.is_mil ? '#00ff41' : '#ff6b35';
                
                const strategicLine = L.polyline([originPos, [asset.lat, asset.lon]], {
                    color: tacticalColor,
                    weight: 2,
                    opacity: 0.5,
                    dashArray: '6, 12',
                    interactive: false
                }).addTo(maps.flights);
                mapMarkers.flights.push(strategicLine);
            }

            // 2. Active Movement Trail (Tail)
            if (flightHistory[asset.icao24].length > 1) {
                const trailColor = asset.is_mil ? '#00ff41' : '#ff6b35';
                
                // Glow tail - maximum visibility for mobile
                const glowTrail = L.polyline(flightHistory[asset.icao24], {
                    color: trailColor,
                    weight: 8,
                    opacity: 0.5,
                    lineCap: 'round'
                }).addTo(maps.flights);
                mapMarkers.flights.push(glowTrail);

                // Core tail - solid visibility for mobile
                const polyline = L.polyline(flightHistory[asset.icao24], {
                    color: trailColor,
                    weight: 3.5,
                    opacity: 1.0,
                    lineCap: 'round'
                }).addTo(maps.flights);
                mapMarkers.flights.push(polyline);
            }

            // Plane Icon with rotation logic
            let rotation = 0;
            if (flightHistory[asset.icao24].length > 1) {
                const p1 = flightHistory[asset.icao24][flightHistory[asset.icao24].length - 2];
                const p2 = flightHistory[asset.icao24][flightHistory[asset.icao24].length - 1];
                rotation = Math.atan2(p2[0] - p1[0], p2[1] - p1[1]) * (180 / Math.PI);
            }

            const icon = L.divIcon({
                className: 'plane-icon',
                html: `<div class="tactical-plane ${asset.is_mil ? 'mil' : 'outlier'}" style="transform: translate(-50%, -50%) rotate(${rotation}deg)"></div>`,
                iconSize: [0, 0],
                iconAnchor: [0, 0]
            });
            
            const marker = L.marker([asset.lat, asset.lon], {icon: icon})
              .addTo(maps.flights)
              .bindPopup(`<div style="font-family:'Fira Code'; font-size: 0.65rem; color: var(--popup-text); background:transparent; border:none; padding:5px;"><b>${asset.callsign}</b><br>ORIGIN: ${asset.origin}<br>ALT: ${asset.alt}m<br>VEL: ${asset.vel}km/h</div>`);
            
            mapMarkers.flights.push(marker);
        }
    });

    // Prune history for aircraft no longer in the feed
    Object.keys(flightHistory).forEach(icao => {
        if (!activeIcaos.has(icao)) delete flightHistory[icao];
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

    container.innerHTML = '';
    let buffer = [...articles];
    
    // Resume from last known index if available
    const storageKey = `feed_index_${containerId}`;
    let lastUrl = localStorage.getItem(storageKey);
    if (lastUrl) {
        const resumeIndex = buffer.findIndex(a => a.url === lastUrl);
        if (resumeIndex !== -1) {
            // Rotate buffer so the resumed articles are at the front
            const resumed = buffer.splice(resumeIndex, buffer.length - resumeIndex);
            buffer = [...resumed, ...buffer];
        }
    }

    let visibleData = buffer.splice(0, Math.min(maxVisible, buffer.length));

    function createItem(art) {
        const item = document.createElement('div');
        item.className = 'article-item';
        const emotion = art.narrative_emotion && art.narrative_emotion !== 'unknown' ? art.narrative_emotion : '';
        const domainsHtml = art.domain.split(', ').map(d => `<span class="tag" style="color:var(--theme-bright); border-color:var(--theme-dim)">${d}</span>`).join('');
        const emotionTag = emotion ? `<span class="tag" style="color:var(--theme-bright); border-color:var(--theme-bright)">${emotion}</span>` : '';
        item.innerHTML = `
            <div class="article-title-wrapper" style="overflow: hidden; white-space: nowrap; margin-bottom: 4px;">
                <a href="${art.url}" target="_blank" class="article-title">${art.title.toLowerCase()}</a>
            </div>
            <div class="article-meta" style="display:flex; flex-wrap:wrap; gap:8px; align-items:center;">
                <span style="font-size: 0.52rem; white-space: nowrap; color: var(--theme-mid);">[${formatDate(art.seendate)}]</span>
                <div style="display:flex; flex-wrap:wrap; gap:4px; align-items:center;">
                    ${emotionTag} ${domainsHtml}
                </div>
            </div>
        `;
        return item;
    }

    function applyScrollEffect(item) {
        const wrapper = item.querySelector('.article-title-wrapper');
        const title = item.querySelector('.article-title');
        if (!wrapper || !title) return;
        
        const recalculate = () => {
            title.classList.remove('should-scroll');
            void title.offsetWidth; // Force reflow
            
            const diff = wrapper.offsetWidth - title.scrollWidth;
            if (diff < 0) {
                title.style.setProperty('--scroll-dist', `${diff - 20}px`);
                title.classList.add('should-scroll');
            }
        };

        // Immediate calc
        recalculate();

        // Use ResizeObserver for continuous robustness on mobile (handles orientation, dynamic bars)
        if (window.ResizeObserver) {
            const ro = new ResizeObserver(() => {
                requestAnimationFrame(recalculate);
            });
            ro.observe(wrapper);
            item._ro = ro; // Store for cleanup if needed
        }
    }

    // Initial Render
    visibleData.forEach(art => {
        const item = createItem(art);
        container.appendChild(item);
        applyScrollEffect(item);
    });

    if (buffer.length > 0) {
        feedsIntervals[containerId] = setInterval(() => {
            const nextArt = buffer.shift();
            const newItem = createItem(nextArt);
            
            // Prepare smooth entrance
            newItem.style.opacity = '0';
            newItem.style.maxHeight = '0';
            newItem.style.overflow = 'hidden';
            newItem.style.paddingTop = '0';
            newItem.style.paddingBottom = '0';
            newItem.style.borderBottomColor = 'transparent';
            newItem.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            
            container.prepend(newItem);
            applyScrollEffect(newItem);
            
            // Trigger entrance
            requestAnimationFrame(() => {
                newItem.style.opacity = '1';
                newItem.style.maxHeight = '44px'; // Updated from 52px to match new layout
                newItem.style.paddingTop = '0.35rem';
                newItem.style.paddingBottom = '0.35rem';
                newItem.style.borderBottomColor = 'var(--border)';
            });

            // Smooth exit of last item
            const items = container.querySelectorAll('.article-item');
            if (items.length > maxVisible) {
                const lastItem = items[items.length - 1];
                if (lastItem._ro) lastItem._ro.disconnect(); // Cleanup observer
                
                lastItem.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                lastItem.style.opacity = '0';
                lastItem.style.maxHeight = '0';
                lastItem.style.paddingTop = '0';
                lastItem.style.paddingBottom = '0';
                lastItem.style.borderBottomColor = 'transparent';
                lastItem.style.pointerEvents = 'none';
                
                setTimeout(() => {
                    if (lastItem.parentNode === container) {
                        container.removeChild(lastItem);
                    }
                }, 850);
                
                buffer.push(visibleData.pop());
                visibleData.unshift(nextArt);

                // Save state
                localStorage.setItem(storageKey, visibleData[0].url);
            }
        }, 4000 + Math.random() * 2000);
    }
}

function renderMarketTicker(markets) {
    const container = document.getElementById('market-ticker');
    if (!container || !markets || markets.length === 0) return;
    
    let html = '';
    markets.forEach(m => {
        const isUp = m.change >= 0;
        const colorClass = isUp ? 'ticker-up' : 'ticker-down';
        const arrow = isUp ? '▲' : '▼';
        const changeStr = (m.change > 0 ? '+' : '') + m.change.toFixed(2) + '%';
        
        html += `
            <span class="market-ticker-item">
                <span class="ticker-symbol">${m.symbol}</span>
                <span class="ticker-price">${m.price.toLocaleString()}</span>
                <span class="${colorClass}" style="font-size: 0.55rem;">${arrow} ${changeStr}</span>
                <span style="margin-left: 1.5rem; color: var(--border);">|</span>
            </span>`;
    });
    
    // Create a temporary element to measure the width of one set of items
    const measure = document.createElement('div');
    measure.style.cssText = "position:absolute; visibility:hidden; display:flex; white-space:nowrap; font-size:0.65rem; letter-spacing:1px; font-family:'Fira Code', monospace;";
    measure.innerHTML = html;
    document.body.appendChild(measure);
    const contentWidth = measure.offsetWidth;
    document.body.removeChild(measure);

    if (contentWidth === 0) return;

    // Calculate repeats needed to fill viewport plus overflow for seamless loop
    // We need at least 2 identical blocks for the 50% scroll animation to look seamless
    const baseRepeats = Math.ceil(window.innerWidth / contentWidth) + 1;
    const totalRepeats = baseRepeats * 2;
    container.innerHTML = html.repeat(totalRepeats);
    
    // Dynamic duration: we want a consistent speed (e.g., 40px per second)
    // The animation moves exactly half of the total width
    const scrollDistance = (contentWidth * totalRepeats) / 2;
    const duration = scrollDistance / 40; // 40px per second
    container.style.setProperty('--ticker-duration', `${duration}s`);
}

function renderQuickStats(news, status) {
    const container = document.getElementById('top-telemetry-ticker');
    if (!container) return;
    
    container.innerHTML = `
        <div title="Total unique nodes in memory (max 500)" style="cursor:help">
            signals: <span style="color:var(--theme-bright)">${news.articles.length}</span>
        </div>
        <div title="Digital integrity verification status" style="cursor:help">
            integrity: <span style="color: #3fb950">verified</span>
        </div>
    `;
}

function renderFlightIntel(intel) {
    if (!intel || intel.status !== 'active') return;
    const slide = document.getElementById('slide-flights');
    const display = slide.querySelector('.flight-intel-display');
    
    // Clear offline message if present and setup grid
    if (display.querySelector('.text-dim')) {
        display.innerHTML = `
            <div class="flight-stat-row">
                <span class="flight-stat-label">active assets</span>
                <span class="flight-stat-value" id="flight-count">--</span>
            </div>
            <div class="flight-stat-row">
                <span class="flight-stat-label">primary theater</span>
                <span id="flight-zone" class="hot-zone-tag">--</span>
            </div>
            <div class="flight-stat-row">
                <span class="flight-stat-label">stream status</span>
                <span class="flight-stat-value" id="flight-status">--</span>
            </div>
            <div class="flight-stat-row">
                <span class="flight-stat-label">strategic alerts</span>
                <span class="flight-stat-value" id="flight-anomalies" style="color: #ff6b35">--</span>
            </div>
        `;
    }

    const countEl = document.getElementById('flight-count');
    const zoneEl = document.getElementById('flight-zone');
    const statusEl = document.getElementById('flight-status');
    const anomalyEl = document.getElementById('flight-anomalies');

    if (countEl) countEl.textContent = intel.count;
    if (zoneEl) zoneEl.textContent = intel.theater;
    if (statusEl) statusEl.textContent = 'active_link';
    if (anomalyEl) anomalyEl.textContent = intel.assets.filter(a => !a.is_mil).length + ' outliers';
}

function renderGTI(score, history) {
    const scoreEl = document.getElementById('gti-score');
    const barEl = document.getElementById('gti-bar');
    if (!scoreEl || !barEl) return;

    // Animate current number
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
    
    // Update bar
    barEl.style.width = `${target}%`;
    
    // Color shift based on tension
    if (target > 75) {
        scoreEl.style.color = '#ff6b35'; // Alert color
        scoreEl.style.textShadow = '0 0 20px #ff6b35';
    } else {
        scoreEl.style.color = 'var(--theme-bright)';
        scoreEl.style.textShadow = 'none';
    }

    // Render History Chart
    if (history && history.length > 0) {
        const historyCanvas = document.getElementById('gtiHistoryChart');
        if (historyCanvas) {
            const ctx = historyCanvas.getContext('2d');
            
            // Downsample for aesthetic clarity if too many points
            let processedHistory = history;
            if (history.length > 40) {
                const step = Math.ceil(history.length / 40);
                processedHistory = history.filter((_, i) => i % step === 0 || i === history.length - 1);
            }

            const labels = processedHistory.map(h => new Date(h.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
            const data = processedHistory.map(h => h.score);
            
            if (charts.gtiHistory) charts.gtiHistory.destroy();

            // Create aesthetic gradient with hex normalization
            const normalizeHex = (hex) => {
                if (hex.length === 4) return '#' + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
                return hex;
            };
            const baseColor = normalizeHex(THEME_BRIGHT);
            const gradient = ctx.createLinearGradient(0, 0, 0, 200);
            gradient.addColorStop(0, baseColor + '66'); // 40% opacity
            gradient.addColorStop(1, baseColor + '00'); // 0% opacity

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
                        pointHoverBorderColor: '#fff',
                        pointHoverBorderWidth: 2,
                        fill: true,
                        tension: 0.45,
                        spanGaps: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        intersect: false,
                        mode: 'index',
                    },
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
                            callbacks: {
                                label: (context) => `index_score: ${context.parsed.y}`
                            }
                        }
                    },
                    scales: {
                        x: { display: false },
                        y: { 
                            min: 0, max: 100, 
                            grid: { 
                                color: 'rgba(255,255,255,0.03)',
                                drawBorder: false
                            },
                            ticks: { 
                                stepSize: 25, 
                                font: { size: 8, family: "'Fira Code', monospace" },
                                color: 'rgba(255,255,255,0.3)',
                                callback: (value) => value + '%'
                            }
                        }
                    },
                    animations: {
                        tension: {
                            duration: 1000,
                            easing: 'linear',
                            from: 1,
                            to: 0.45,
                            loop: false
                        }
                    }
                }
            });
        }
    }
}

let intelCarouselInterval = null;
let currentIntelIndex = 0;

function startIntelCarousel() {
    if (intelCarouselInterval) clearInterval(intelCarouselInterval);
    
    // SCOPE: Only slides and dots belonging to the Intel Carousel
    const slides = document.querySelectorAll('#intel-carousel-card .intel-slide');
    const dots = document.querySelectorAll('#intel-nav-dots .intel-dot');
    if (!slides.length) return;

    function goToSlide(index) {
        if (index === currentIntelIndex) return;
        
        slides[currentIntelIndex].classList.remove('active');
        dots[currentIntelIndex].classList.remove('active');
        
        currentIntelIndex = index;
        
        slides[currentIntelIndex].classList.add('active');
        dots[currentIntelIndex].classList.add('active');
        
        // Ensure charts resize correctly when their container becomes visible
        const activeSlideId = slides[currentIntelIndex].id;
        if (activeSlideId === 'slide-sentiment' && charts.emotions) {
            charts.emotions.resize();
        } else if (activeSlideId === 'slide-gti' && charts.gtiHistory) {
            charts.gtiHistory.resize();
        }

        // Reset timer to give user time to read the manual selection
        resetIntelTimer();
    }

    function resetIntelTimer() {
        if (intelCarouselInterval) clearInterval(intelCarouselInterval);
        intelCarouselInterval = setInterval(() => {
            let nextIndex = (currentIntelIndex + 1) % slides.length;
            goToSlide(nextIndex);
        }, 15000);
    }

    // Add click listeners to dots
    dots.forEach((dot, idx) => {
        dot.addEventListener('click', () => goToSlide(idx));
    });

    resetIntelTimer();
}

let mapCarouselInterval = null;
let currentMapIndex = 0;

function startMapCarousel() {
    if (mapCarouselInterval) clearInterval(mapCarouselInterval);
    
    const slides = document.querySelectorAll('#map-carousel-card .intel-slide');
    const dots = document.querySelectorAll('#map-nav-dots .intel-dot');
    if (!slides.length) return;

    function goToMap(index) {
        if (index === currentMapIndex) return;

        slides[currentMapIndex].classList.remove('active');
        dots[currentMapIndex].classList.remove('active');
        
        currentMapIndex = index;
        
        slides[currentMapIndex].classList.add('active');
        dots[currentMapIndex].classList.add('active');
        
        // Leaflet fix: invalidateSize when map container becomes visible
        setTimeout(() => {
            if (currentMapIndex === 0 && maps.news) maps.news.invalidateSize();
            if (currentMapIndex === 1 && maps.flights) maps.flights.invalidateSize();
        }, 300); // Wait for transition to be partially complete

        resetMapTimer();
    }

    function resetMapTimer() {
        if (mapCarouselInterval) clearInterval(mapCarouselInterval);
        mapCarouselInterval = setInterval(() => {
            let nextIndex = (currentMapIndex + 1) % slides.length;
            goToMap(nextIndex);
        }, 20000); // Maps rotate slower than intel (20s)
    }

    dots.forEach((dot, idx) => {
        dot.addEventListener('click', () => goToMap(idx));
    });

    resetMapTimer();
}

document.addEventListener('DOMContentLoaded', async () => {
    logSystem("booting intelligence engine...");
    
    // Load state from URL parameters
    loadStateFromURL();
    
    // Wait for fonts to ensure layout measurements are correct
    if (document.fonts) await document.fonts.ready;
    
    // Multi-stage initialization for maximum mobile stability
    // 1. Initial render
    setTimeout(async () => {
        const today = new Date().toISOString().split('T')[0];
        if (activeDate !== today) {
            await loadHistoricalData(activeDate);
        } else {
            await updateDashboard();
        }
        startIntelCarousel();
        startMapCarousel();
        window.dispatchEvent(new Event('resize'));
    }, 300);

    // 2. Secondary "Kick" (handles address bar shifts/slow renders)
    setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
        if (window.lastData) {
            // Re-sync specific layout sensitive components
            const dedupedArticles = deduplicateArticles(window.lastData.articles);
            safeRender('articles', () => initRotatingFeed('articles-list', dedupedArticles, 7));
        }
    }, 1200);

    // Final safety check and resize handler
    setTimeout(() => window.dispatchEvent(new Event('resize')), 3500);

    // Time Machine Event Listener & Range Restriction
    const datePicker = document.getElementById('time-machine-date');
    if (datePicker) {
        const today = new Date().toISOString().split('T')[0];
        datePicker.setAttribute('min', '2026-05-21'); // Archive Start Date
        datePicker.setAttribute('max', today);
        datePicker.value = today; // Default to today

        datePicker.addEventListener('change', (e) => {
            if (e.target.value) {
                if (e.target.value === today) {
                    updateDashboard(); // Return to live
                } else {
                    loadHistoricalData(e.target.value);
                }
            }
        });
    }

    window.addEventListener('resize', () => {
        if (window.lastData && window.lastData.market_intel) {
            renderMarketTicker(window.lastData.market_intel);
        }
    });

    setInterval(() => {
        const today = new Date().toISOString().split('T')[0];
        if (activeDate === today) updateDashboard();
    }, 40000);
});
