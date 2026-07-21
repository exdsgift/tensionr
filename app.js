// app.js - Main Orchestrator and HUD controllers

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
        const domainsHtml = art.domain.split(', ').map(d => `<span class="tag tag-domain">${d}</span>`).join('');
        const emotionTag = emotion ? `<span class="tag tag-emotion">${emotion}</span>` : '';
        item.innerHTML = `
            <div class="article-title-wrapper">
                <a href="${art.url}" target="_blank" class="article-title">${art.title.toLowerCase()}</a>
            </div>
            <div class="article-meta">
                <span class="article-time">[${formatDate(art.seendate)}]</span>
                <div class="article-tags">
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

function renderMarketTicker(markets) {
    const container = document.getElementById('market-ticker');
    if (!container || !markets || markets.length === 0) return;
    let html = '';
    markets.forEach(m => {
        const isUp = m.change >= 0;
        const colorClass = isUp ? 'ticker-up' : 'ticker-down';
        const arrow = isUp ? '▲' : '▼';
        const changeStr = (m.change > 0 ? '+' : '') + m.change.toFixed(2) + '%';
        html += `<span class="market-ticker-item"><span class="ticker-symbol">${m.symbol}</span><span class="ticker-price">${m.price.toLocaleString()}</span><span class="${colorClass} ticker-change">${arrow} ${changeStr}</span><span class="ticker-sep">|</span></span>`;
    });
    const measure = document.createElement('div');
    measure.style.cssText = "position:absolute; visibility:hidden; display:flex; white-space:nowrap; font-size:0.7rem; letter-spacing:1px; font-family:'Fira Code', monospace;";
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

function renderQuickStats(news) {
    const signalsEl = document.getElementById('kpi-signals');
    const integrityEl = document.getElementById('kpi-integrity');
    if (signalsEl) signalsEl.innerHTML = `signals: <b>${news.articles.length}</b>`;
    if (integrityEl) integrityEl.innerHTML = `integrity: <b>verified</b>`;
}

function renderFlightIntel(intel) {
    const toggle = document.getElementById('toggle-flights');
    const availability = document.getElementById('flights-availability');
    const mini = document.getElementById('flight-intel-mini');
    const active = !!(intel && intel.status === 'active');

    if (toggle) toggle.disabled = !active;
    if (availability) availability.textContent = active ? '' : '[offline]';
    if (!mini) return;
    if (!active) {
        mini.hidden = true;
        return;
    }
    mini.hidden = false;
    const outliers = intel.assets.filter(a => !a.is_mil).length;
    mini.innerHTML = `
        <div class="flight-stat-row"><span class="flight-stat-label">active assets</span><span class="flight-stat-value">${intel.count}</span></div>
        <div class="flight-stat-row"><span class="flight-stat-label">primary theater</span><span class="hot-zone-tag">${intel.theater}</span></div>
        <div class="flight-stat-row"><span class="flight-stat-label">strategic alerts</span><span class="flight-stat-value">${outliers} outliers</span></div>
    `;
}

function createIntelItem(tagClass, tagText, srcText, link, title) {
    const item = document.createElement('div');
    item.className = 'intel-item';
    item.innerHTML = `
        <div class="intel-item-head">
            <span class="tag ${tagClass}">${tagText}</span>
            <span class="intel-item-src">${srcText}</span>
        </div>
        <a href="${link}" target="_blank" class="intel-item-link">${title.toLowerCase()}</a>
    `;
    return item;
}

function renderRawChatter(chatter) {
    const container = document.getElementById('raw-chatter-list');
    if (!container || !chatter) return;
    container.innerHTML = '';
    chatter.forEach(item => {
        container.appendChild(createIntelItem('tag-unverified', 'UNVERIFIED', `SRC: ${item.source}`, item.link, item.title));
    });
}

function renderCyberIntel(intel) {
    const container = document.getElementById('cyber-threat-list');
    if (!container || !intel) return;
    container.innerHTML = '';
    intel.forEach(threat => {
        container.appendChild(createIntelItem('tag-alert', 'SEC_ALERT', 'HANDSHAKE_ACTIVE', threat.link, threat.title));
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

/* ---------------------------------------------------------------------------
 * HUD controllers
 * ------------------------------------------------------------------------- */

function initDrawer() {
    const drawer = document.getElementById('hud-drawer');
    const handle = document.getElementById('drawer-handle');
    const tabs = document.querySelectorAll('#drawer-tabs button');
    const panes = document.querySelectorAll('.drawer-pane');
    if (!drawer || !handle) return;

    // Legend/coords anchor above the drawer via --drawer-h, and the feed panel
    // hangs below the top strip via --hud-top-h; keep both in sync with reality.
    const hudTop = document.getElementById('hud-top');
    const syncDrawerVar = () => {
        const open = drawer.getAttribute('data-open') === 'true';
        document.documentElement.style.setProperty('--drawer-h', open ? `${drawer.offsetHeight}px` : '38px');
        if (hudTop) document.documentElement.style.setProperty('--hud-top-h', `${hudTop.offsetHeight}px`);
    };

    const setOpen = (open) => {
        drawer.setAttribute('data-open', String(open));
        handle.textContent = open ? '▾ intel_panels' : '▴ intel_panels';
        syncDrawerVar();
    };

    handle.addEventListener('click', () => {
        setOpen(drawer.getAttribute('data-open') !== 'true');
    });

    tabs.forEach(btn => btn.addEventListener('click', () => {
        tabs.forEach(b => b.classList.remove('active'));
        panes.forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const pane = document.getElementById(`pane-${btn.dataset.tab}`);
        if (pane) pane.classList.add('active');
        if (drawer.getAttribute('data-open') !== 'true') setOpen(true);
        // Chart.js canvases render 0x0 while their pane is display:none.
        if (btn.dataset.tab === 'radar' && charts.emotions) charts.emotions.resize();
        if (btn.dataset.tab === 'gti' && charts.gtiHistory) charts.gtiHistory.resize();
    }));

    syncDrawerVar();
    window.addEventListener('resize', syncDrawerVar);
}

function initPanelToggles() {
    [['hud-feed', 'feed-toggle'], ['hud-legend', 'legend-toggle']].forEach(([panelId, btnId]) => {
        const panel = document.getElementById(panelId);
        const btn = document.getElementById(btnId);
        if (!panel || !btn) return;
        btn.addEventListener('click', () => {
            const open = panel.getAttribute('data-open') === 'true';
            panel.setAttribute('data-open', String(!open));
            btn.textContent = open ? '▸' : '▾';
        });
    });
}

function initLayerToggles() {
    try {
        const saved = JSON.parse(localStorage.getItem('tensionr_layers'));
        if (saved && typeof saved === 'object') {
            // Pick only known keys: older saved states carried a removed hex layer.
            if (typeof saved.news === 'boolean') layerToggles.news = saved.news;
            if (typeof saved.flights === 'boolean') layerToggles.flights = saved.flights;
        }
    } catch (e) { /* corrupt saved state: keep defaults */ }
    const save = () => localStorage.setItem('tensionr_layers', JSON.stringify(layerToggles));

    const newsBox = document.getElementById('toggle-news');
    const flightsBox = document.getElementById('toggle-flights');
    if (!newsBox || !flightsBox) return;
    newsBox.checked = layerToggles.news;
    flightsBox.checked = layerToggles.flights;

    newsBox.addEventListener('change', e => {
        layerToggles.news = e.target.checked;
        if (maps.main && overlays.news) e.target.checked ? overlays.news.addTo(maps.main) : overlays.news.remove();
        save();
    });
    flightsBox.addEventListener('change', e => {
        layerToggles.flights = e.target.checked;
        if (maps.main && overlays.flights) e.target.checked ? overlays.flights.addTo(maps.main) : overlays.flights.remove();
        save();
    });
}

/**
 * On mobile the right feed panel is hidden and its article list lives in the
 * drawer's "feed" tab. Moving the node preserves rotation intervals/observers.
 */
function relocateFeed() {
    const list = document.getElementById('articles-list');
    const feedPanel = document.getElementById('hud-feed');
    const pane = document.getElementById('pane-feed');
    if (!list || !feedPanel || !pane) return;
    const mobile = window.matchMedia('(max-width: 767px)').matches;
    if (mobile && list.parentElement !== pane) pane.appendChild(list);
    else if (!mobile && list.parentElement !== feedPanel) feedPanel.appendChild(list);
}

document.addEventListener('DOMContentLoaded', async () => {
    logSystem("booting intelligence engine...");
    loadStateFromURL();
    if (document.fonts) await document.fonts.ready;

    // Theme is applied before first paint by the inline head script; sync + wire the selector.
    const themeSelect = document.getElementById('theme-select');
    if (themeSelect) {
        themeSelect.value = document.documentElement.getAttribute('data-theme');
        themeSelect.addEventListener('change', e => setTheme(e.target.value));
    }
    updateThemeColors();

    // Map-first on mobile: drawer and legend start collapsed (before initDrawer
    // so the layout var is computed from the collapsed state).
    if (window.matchMedia('(max-width: 767px)').matches) {
        document.getElementById('hud-drawer').setAttribute('data-open', 'false');
        document.getElementById('drawer-handle').textContent = '▴ intel_panels';
        document.getElementById('hud-legend').setAttribute('data-open', 'false');
        document.getElementById('legend-toggle').textContent = '▸';
    }

    initDrawer();
    initPanelToggles();
    initLayerToggles();
    relocateFeed();
    window.matchMedia('(max-width: 767px)').addEventListener('change', relocateFeed);

    const clearBtn = document.getElementById('clear-filters-btn');
    if (clearBtn) clearBtn.addEventListener('click', clearFilters);

    initMainMap();

    setTimeout(async () => {
        const today = new Date().toISOString().split('T')[0];
        if (activeDate !== today) await loadHistoricalData(activeDate);
        else await updateDashboard();
        window.dispatchEvent(new Event('resize'));
        type();
    }, 300);

    const datePicker = document.getElementById('time-machine-date');
    if (datePicker && typeof flatpickr !== 'undefined') {
        const today = new Date().toISOString().split('T')[0];
        flatpickr(datePicker, {
            defaultDate: activeDate,
            minDate: "2026-05-21",
            maxDate: today,
            dateFormat: "Y-m-d",
            disableMobile: "true",
            onChange: function(selectedDates, dateStr) {
                if (dateStr === today) updateDashboard();
                else loadHistoricalData(dateStr);
            },
            onReady: function(selectedDates, dateStr, instance) {
                instance.calendarContainer.classList.add('tactical-calendar');
            }
        });
    }

    window.addEventListener('resize', () => {
        if (window.lastData && window.lastData.market_intel) renderMarketTicker(window.lastData.market_intel);
    });

    setInterval(() => { if (activeDate === new Date().toISOString().split('T')[0]) updateDashboard(); }, 40000);
    setInterval(updateClock, 1000);
    updateClock();
});
