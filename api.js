// api.js - Data fetching and state management

/**
 * @file api.js
 * @description Data orchestration, background processing, and historical data retrieval.
 */

/**
 * Background worker for heavy NLP/data processing tasks.
 * @type {Worker}
 */
const intelligenceWorker = new Worker('worker.js');

intelligenceWorker.onmessage = function(e) {
    const { type, payload } = e.data;
    if (type === 'DATA_PROCESSED') {
        const { articles, keywords } = payload;
        if (window.lastData) {
            window.lastData.articles = articles;
            window.lastData.stats.top_keywords = keywords;
        }
        safeRender('wordcloud', () => renderWordCloudEnriched(keywords));
        refreshFilteredUI();
        logSystem("intelligence processed via background thread.");
    }
};

/**
 * Main dashboard synchronization engine. 
 * Fetches all real-time intelligence nodes and triggers rendering.
 * 
 * @async
 * @description Bridges geopolitical data nodes (China, Russia, Middle East) into the monitoring pipeline.
 * @listens geopolitical_hotspots
 */
async function updateDashboard() {
    logSystem("syncing telemetry...");
    window.activeDate = new Date().toISOString().split('T')[0];
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
        document.getElementById('live-indicator').style.color = window.THEME_BRIGHT;

        refreshFilteredUI();

        intelligenceWorker.postMessage({
            type: 'PROCESS_DATA',
            data: {
                articles: news.articles,
                keywords: news.stats.top_keywords
            }
        });

        safeRender('sitrep', () => renderSITREP(intel.sitrep || "synthesizing tactical reports..."));
        safeRender('insight', () => renderStrategicInsight(intel.strategic_insight));
        safeRender('gti', () => renderGTI(status.global_tension_index, status.gti_history, status.gti_forecast));
        safeRender('flights', () => renderFlightIntel(telemetry.flight_intel));
        safeRender('map', () => {
            renderMap(news.stats.source_countries, news.articles);
            renderFlightMap(telemetry.flight_intel);
            if (typeof renderTacticalMap === 'function') {
                renderTacticalMap(news.articles);
            }
        });
        safeRender('cyber', () => renderCyberIntel(intel.cyber_intel));
        safeRender('chatter', () => renderRawChatter(intel.raw_chatter));
        safeRender('market', () => renderMarketTicker(markets.market_intel));
        safeRender('stats', () => renderQuickStats(news, status));
        
        logSystem(`handshake success. ${news.articles.length} nodes active.`);

        document.querySelectorAll('.card').forEach(card => {
            card.classList.remove('fade-update');
            void card.offsetWidth;
            card.classList.add('fade-update');
        });
    } catch (error) {
        logSystem("sync failed: packet loss");
        console.error(error);
    }
}

/**
 * Loads and renders historical snapshots from the static data lake.
 * @async
 * @param {string} date - ISO date string (YYYY-MM-DD).
 */
async function loadHistoricalData(date) {
    logSystem(`attempting time machine handshake: ${date}`);
    window.activeDate = date;
    updateURL();
    try {
        const resp = await fetch(`data/archive/${date}.json`);
        if (!resp.ok) throw new Error("snapshot_not_found");
        const archive = await resp.json();
        
        renderSITREP(archive.sitrep, true);
        renderGTI(archive.gti);
        renderWordCloud(archive.top_keywords);
        
        document.getElementById('live-indicator').textContent = '● playback_mode';
        document.getElementById('live-indicator').style.color = window.THEME_MID;
        document.getElementById('last-updated').textContent = `archive: ${date}`;
        
        logSystem(`historical sync success. date: ${date}`);
    } catch (err) {
        logSystem(`time machine error: ${err.message}`);
        setTimeout(() => updateDashboard(), 3000);
    }
}

/**
 * Updates browser history and URL search parameters based on global filter state.
 */
function updateURL() {
    const params = new URLSearchParams();
    if (window.globalFilter.country) params.set('country', window.globalFilter.country);
    if (window.globalFilter.keyword) params.set('keyword', window.globalFilter.keyword);
    if (window.activeDate !== new Date().toISOString().split('T')[0]) params.set('date', window.activeDate);
    
    const newURL = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
    window.history.replaceState({ path: newURL }, '', newURL);
}

/**
 * Restores application filter state from URL parameters on initialization.
 */
function loadStateFromURL() {
    const params = new URLSearchParams(window.location.search);
    window.globalFilter.country = params.get('country');
    window.globalFilter.keyword = params.get('keyword');
    const dateParam = params.get('date');
    if (dateParam) {
        window.activeDate = dateParam;
        const datePicker = document.getElementById('time-machine-date');
        if (datePicker) datePicker.value = window.activeDate;
    }
}
