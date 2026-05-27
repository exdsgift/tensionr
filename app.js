// app.js - Main Orchestrator and Global State

function setGlobalFilter(type, value) {
    if (globalFilter[type] === value) {
        globalFilter[type] = null;
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
    safeRender('emotions', () => renderEmotions(filteredArticles));
    safeRender('articles', () => initRotatingFeed('articles-list', filteredArticles, 7));
    updateFilterUI();
}

function applyFilters(articles) {
    if (!articles) return [];
    return articles.filter(a => {
        let match = true;
        if (globalFilter.country) match = match && (a.sourcecountry === globalFilter.country);
        if (globalFilter.keyword) {
            const searchStr = `${a.title} ${a.summary} ${a.keywords || ''}`.toLowerCase();
            match = match && searchStr.includes(globalFilter.keyword.toLowerCase());
        }
        return match;
    });
}

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
    const storageKey = `feed_index_${containerId}`;
    let lastUrl = localStorage.getItem(storageKey);
    if (lastUrl) {
        const resumeIndex = buffer.findIndex(a => a.url === lastUrl);
        if (resumeIndex !== -1) {
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
            void title.offsetWidth;
            const diff = wrapper.offsetWidth - title.scrollWidth;
            if (diff < 0) {
                title.style.setProperty('--scroll-dist', `${diff - 20}px`);
                title.classList.add('should-scroll');
            }
        };
        recalculate();
        if (window.ResizeObserver) {
            const ro = new ResizeObserver(() => requestAnimationFrame(recalculate));
            ro.observe(wrapper);
            item._ro = ro;
        }
    }

    visibleData.forEach(art => {
        const item = createItem(art);
        container.appendChild(item);
        applyScrollEffect(item);
    });

    if (buffer.length > 0) {
        feedsIntervals[containerId] = setInterval(() => {
            const nextArt = buffer.shift();
            const newItem = createItem(nextArt);
            newItem.style.opacity = '0';
            newItem.style.maxHeight = '0';
            newItem.style.overflow = 'hidden';
            newItem.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            container.prepend(newItem);
            applyScrollEffect(newItem);
            requestAnimationFrame(() => {
                newItem.style.opacity = '1';
                newItem.style.maxHeight = '44px';
                newItem.style.paddingTop = '0.35rem';
                newItem.style.paddingBottom = '0.35rem';
                newItem.style.borderBottomColor = 'var(--border)';
            });
            const items = container.querySelectorAll('.article-item');
            if (items.length > maxVisible) {
                const lastItem = items[items.length - 1];
                if (lastItem._ro) lastItem._ro.disconnect();
                lastItem.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
                lastItem.style.opacity = '0';
                lastItem.style.maxHeight = '0';
                setTimeout(() => { if (lastItem.parentNode === container) container.removeChild(lastItem); }, 850);
                buffer.push(visibleData.pop());
                visibleData.unshift(nextArt);
                localStorage.setItem(storageKey, visibleData[0].url);
            }
        }, 4000 + Math.random() * 2000);
    }
}

let feedsIntervals = {};

function renderMarketTicker(markets) {
    const container = document.getElementById('market-ticker');
    if (!container || !markets || markets.length === 0) return;
    let html = '';
    markets.forEach(m => {
        const isUp = m.change >= 0;
        const colorClass = isUp ? 'ticker-up' : 'ticker-down';
        const arrow = isUp ? '▲' : '▼';
        const changeStr = (m.change > 0 ? '+' : '') + m.change.toFixed(2) + '%';
        html += `<span class="market-ticker-item"><span class="ticker-symbol">${m.symbol}</span><span class="ticker-price">${m.price.toLocaleString()}</span><span class="${colorClass}" style="font-size: 0.55rem;">${arrow} ${changeStr}</span><span style="margin-left: 1.5rem; color: var(--border);">|</span></span>`;
    });
    const measure = document.createElement('div');
    measure.style.cssText = "position:absolute; visibility:hidden; display:flex; white-space:nowrap; font-size:0.65rem; letter-spacing:1px; font-family:'Fira Code', monospace;";
    measure.innerHTML = html;
    document.body.appendChild(measure);
    const contentWidth = measure.offsetWidth;
    document.body.removeChild(measure);
    if (contentWidth === 0) return;
    const baseRepeats = Math.ceil(window.innerWidth / contentWidth) + 1;
    const totalRepeats = baseRepeats * 2;
    container.innerHTML = html.repeat(totalRepeats);
    const scrollDistance = (contentWidth * totalRepeats) / 2;
    const duration = scrollDistance / 40;
    container.style.setProperty('--ticker-duration', `${duration}s`);
}

function renderQuickStats(news, status) {
    const container = document.getElementById('top-telemetry-ticker');
    if (!container) return;
    container.innerHTML = `<div>signals: <span style="color:var(--theme-bright)">${news.articles.length}</span></div><div>integrity: <span style="color: var(--theme-bright)">verified</span></div>`;
}

function renderFlightIntel(intel) {
    if (!intel || intel.status !== 'active') return;
    const display = document.querySelector('#slide-flights .flight-intel-display');
    if (display.querySelector('.text-dim')) {
        display.innerHTML = `<div class="flight-stat-row"><span class="flight-stat-label">active assets</span><span class="flight-stat-value" id="flight-count">--</span></div><div class="flight-stat-row"><span class="flight-stat-label">primary theater</span><span id="flight-zone" class="hot-zone-tag">--</span></div><div class="flight-stat-row"><span class="flight-stat-label">stream status</span><span class="flight-stat-value" id="flight-status">--</span></div><div class="flight-stat-row"><span class="flight-stat-label">strategic alerts</span><span class="flight-stat-value" id="flight-anomalies" style="color: var(--theme-bright)">--</span></div>`;
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

function renderRawChatter(chatter) {
    const container = document.getElementById('raw-chatter-list');
    if (!container || !chatter) return;
    container.innerHTML = '';
    chatter.forEach(item => {
        const div = document.createElement('div');
        div.style.borderBottom = '1px solid var(--border)';
        div.style.paddingBottom = '4px';
        div.innerHTML = `<div style="display:flex; flex-direction:column; gap:2px;"><div style="display:flex; gap:5px; align-items:center;"><span class="tag" style="color: var(--theme-mid); border-color: var(--theme-mid); font-size: 0.45rem;">UNVERIFIED</span><span style="font-size: 0.5rem; color: var(--text-dim); text-transform: uppercase;">SRC: ${item.source}</span></div><a href="${item.link}" target="_blank" style="color: var(--text-main); font-size: 0.62rem; text-decoration: none; line-height: 1.2;">${item.title.toLowerCase()}</a></div>`;
        container.appendChild(div);
    });
}

function renderCyberIntel(intel) {
    const container = document.getElementById('cyber-threat-list');
    if (!container || !intel) return;
    container.innerHTML = '';
    intel.forEach(threat => {
        const item = document.createElement('div');
        item.style.borderBottom = '1px solid var(--border)';
        item.style.paddingBottom = '4px';
        item.innerHTML = `<div style="display:flex; flex-direction:column; gap:2px;"><div style="display:flex; gap:5px; align-items:center;"><span class="tag" style="color: var(--theme-bright); border-color: var(--theme-bright); font-size: 0.45rem;">SEC_ALERT</span><span style="font-size: 0.5rem; color: var(--text-dim); text-transform: uppercase;">HANDSHAKE_ACTIVE</span></div><a href="${threat.link}" target="_blank" style="color: var(--text-main); font-size: 0.62rem; text-decoration: none; line-height: 1.2; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${threat.title.toLowerCase()}</a></div>`;
        container.appendChild(item);
    });
}

function renderSITREP(text, isHistorical = false) {
    const sitrepEl = document.getElementById('sitrep-text');
    const statusEl = document.getElementById('sitrep-status');
    if (!sitrepEl) return;
    const safeText = (text || "Intelligence synthesis active: monitoring global signals...").toLowerCase();
    sitrepEl.innerHTML = `<span>${safeText} &nbsp;&nbsp;...&nbsp;&nbsp; ${safeText} &nbsp;&nbsp;...&nbsp;&nbsp;</span>`;
    if (statusEl) statusEl.textContent = isHistorical ? 'archived_intel' : 'live_stream';
}

let intelCarouselInterval, mapCarouselInterval;
let currentIntelIndex = 0, currentMapIndex = 0;

function startIntelCarousel() {
    const slides = document.querySelectorAll('#intel-carousel-card .intel-slide');
    const dots = document.querySelectorAll('#intel-nav-dots .intel-dot');
    if (!slides.length) return;
    function goToSlide(index) {
        slides[currentIntelIndex].classList.remove('active');
        dots[currentIntelIndex].classList.remove('active');
        currentIntelIndex = index;
        slides[currentIntelIndex].classList.add('active');
        dots[currentIntelIndex].classList.add('active');
        if (slides[currentIntelIndex].id === 'slide-sentiment' && charts.emotions) charts.emotions.resize();
        if (slides[currentIntelIndex].id === 'slide-gti' && charts.gtiHistory) charts.gtiHistory.resize();
    }
    dots.forEach((dot, idx) => dot.addEventListener('click', () => { goToSlide(idx); clearInterval(intelCarouselInterval); }));
    intelCarouselInterval = setInterval(() => goToSlide((currentIntelIndex + 1) % slides.length), 15000);
}

function startMapCarousel() {
    const slides = document.querySelectorAll('#map-carousel-card .intel-slide');
    const dots = document.querySelectorAll('#map-nav-dots .intel-dot');
    if (!slides.length) return;
    function goToMap(index) {
        slides[currentMapIndex].classList.remove('active');
        dots[currentMapIndex].classList.remove('active');
        currentMapIndex = index;
        slides[currentMapIndex].classList.add('active');
        dots[currentMapIndex].classList.add('active');
        setTimeout(() => {
            if (currentMapIndex === 0 && maps.tactical) maps.tactical.invalidateSize();
            if (currentMapIndex === 1 && maps.news) maps.news.invalidateSize();
            if (currentMapIndex === 2 && maps.flights) maps.flights.invalidateSize();
        }, 300);
    }
    dots.forEach((dot, idx) => dot.addEventListener('click', () => { goToMap(idx); clearInterval(mapCarouselInterval); }));
    mapCarouselInterval = setInterval(() => goToMap((currentMapIndex + 1) % slides.length), 20000);
}

document.addEventListener('DOMContentLoaded', async () => {
    logSystem("booting intelligence engine...");
    loadStateFromURL();
    if (document.fonts) await document.fonts.ready;
    const savedTheme = localStorage.getItem('tensionr_theme') || 'phosphor';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeColors();

    setTimeout(async () => {
        const today = new Date().toISOString().split('T')[0];
        if (activeDate !== today) await loadHistoricalData(activeDate);
        else await updateDashboard();
        startIntelCarousel();
        startMapCarousel();
        window.dispatchEvent(new Event('resize'));
        type();
    }, 300);

    const datePicker = document.getElementById('time-machine-date');
    if (datePicker) {
        const today = new Date().toISOString().split('T')[0];
        datePicker.setAttribute('min', '2026-05-21');
        datePicker.setAttribute('max', today);
        datePicker.addEventListener('change', (e) => {
            if (e.target.value === today) updateDashboard();
            else loadHistoricalData(e.target.value);
        });
    }

    window.addEventListener('resize', () => {
        if (window.lastData && window.lastData.market_intel) renderMarketTicker(window.lastData.market_intel);
    });

    setInterval(() => { if (activeDate === new Date().toISOString().split('T')[0]) updateDashboard(); }, 40000);
    setInterval(updateClock, 1000);
    updateClock();
});
