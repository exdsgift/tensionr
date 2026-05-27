// api.js - Data fetching and state management

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

        refreshFilteredUI();

        intelligenceWorker.postMessage({
            type: 'PROCESS_DATA',
            data: {
                articles: news.articles,
                keywords: news.stats.top_keywords
            }
        });

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

async function loadHistoricalData(date) {
    logSystem(`attempting time machine handshake: ${date}`);
    activeDate = date;
    updateURL();
    try {
        const resp = await fetch(`data/archive/${date}.json`);
        if (!resp.ok) throw new Error("snapshot_not_found");
        const archive = await resp.json();
        
        renderSITREP(archive.sitrep, true);
        renderGTI(archive.gti);
        renderWordCloud(archive.top_keywords);
        
        document.getElementById('live-indicator').textContent = '● playback_mode';
        document.getElementById('live-indicator').style.color = THEME_MID;
        document.getElementById('last-updated').textContent = `archive: ${date}`;
        
        logSystem(`historical sync success. date: ${date}`);
    } catch (err) {
        logSystem(`time machine error: ${err.message}`);
        setTimeout(() => updateDashboard(), 3000);
    }
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
