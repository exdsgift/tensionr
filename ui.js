// ui.js - Theme, Clock, and general UI interactions

/**
 * @file ui.js
 * @description Core UI management, theme handling, and common interface interactions.
 */

/**
 * Updates the system clock in the UI.
 */
function updateClock() {
    const clockElement = document.getElementById('clock');
    if (clockElement) {
        clockElement.textContent = new Date().toTimeString().split(' ')[0];
    }
}

/**
 * Synchronizes CSS theme variables with JavaScript constants and Chart.js defaults.
 */
function updateThemeColors() {
    const root = getComputedStyle(document.documentElement);
    window.THEME_BRIGHT = root.getPropertyValue('--theme-bright').trim();
    window.THEME_MID = root.getPropertyValue('--theme-mid').trim();
    window.THEME_DIM = root.getPropertyValue('--theme-dim').trim();
    window.COLOR_WHITE = root.getPropertyValue('--text-main').trim();
    window.COLOR_BORDER = root.getPropertyValue('--border').trim();

    Chart.defaults.color = root.getPropertyValue('--text-dim').trim();
    Chart.defaults.font.family = "'Fira Code', monospace";
    Chart.defaults.font.size = 10;
    Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';
    
    const liveIndicator = document.getElementById('live-indicator');
    if(liveIndicator) liveIndicator.style.color = window.THEME_BRIGHT;
}

/**
 * Sets the application theme and triggers necessary re-renders.
 * @param {string} themeName - The name of the theme ('ghost' or 'phosphor').
 */
function setTheme(themeName) {
    document.documentElement.setAttribute('data-theme', themeName);
    localStorage.setItem('tensionr_theme', themeName);
    updateThemeColors();
    
    // Re-render components with new colors if data is available
    if (window.lastData) {
        safeRender('emotions', () => renderEmotions(window.lastData.articles));
        safeRender('map', () => renderMap(window.lastData.stats.source_countries, window.lastData.articles));
        if (Array.isArray(window.lastData.stats.top_keywords)) {
            safeRender('wordcloud', () => renderWordCloudEnriched(window.lastData.stats.top_keywords));
        } else {
            safeRender('wordcloud', () => renderWordCloud(window.lastData.stats.top_keywords));
        }
        const dedupedArticles = deduplicateArticles(window.lastData.articles);
        safeRender('articles', () => initRotatingFeed('articles-list', dedupedArticles, 7));
    }
}

function toggleMode() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = (current === 'ghost') ? 'phosphor' : 'ghost';
    setTheme(next);
    const themeSelect = document.getElementById('theme-select');
    if (themeSelect) themeSelect.value = next;
    
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.style.transform = 'rotate(180deg) scale(1.2)';
        setTimeout(() => {
            toggle.style.transform = 'rotate(0deg) scale(1)';
        }, 300);
    }
}

const titleText = "tensionr";
let charIndex = 0;
let isDeleting = false;
let typeSpeed = 200;

function type() {
    const titleElement = document.getElementById('site-title');
    if (!titleElement) return;

    const current = titleText.substring(0, charIndex);
    titleElement.textContent = current;

    if (!isDeleting && charIndex < titleText.length) {
        charIndex++;
        typeSpeed = 150;
    } else if (isDeleting && charIndex > 0) {
        charIndex--;
        typeSpeed = 75;
    } else {
        isDeleting = !isDeleting;
        typeSpeed = isDeleting ? 3000 : 800;
    }

    setTimeout(type, typeSpeed);
}

function logSystem(msg) {
    const log = document.getElementById('system-log');
    if (log) {
        const time = new Date().toLocaleTimeString().toLowerCase();
        log.innerHTML += `[${time}] ${msg}<br>`;
        log.scrollTop = log.scrollHeight;
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

function formatDate(isoStr) {
    if (!isoStr) return "--:--";
    try {
        const parts = isoStr.match(/(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})/);
        if (parts) return `${parts[4]}:${parts[5]} ${parts[3]}/${parts[2]}`;
        const d = new Date(isoStr);
        if (!isNaN(d.getTime())) {
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + " " + d.toLocaleDateString([], { day: '2-digit', month: '2-digit' });
        }
        return isoStr.substring(0, 10);
    } catch { return "--:--" }
}

function safeRender(name, fn) {
    try {
        fn();
    } catch (e) {
        logSystem(`warning: component_${name} failure`);
        console.warn(`render error in ${name}:`, e);
    }
}

/**
 * Renders the Strategic Insight report from the Agentic Analyst.
 * @param {string} text - The insight text.
 */
function renderStrategicInsight(text) {
    const el = document.getElementById('strategic-insight');
    if (!el) return;
    const safeText = (text || "Analyzing multi-domain vectors: identifying non-obvious correlations...").toLowerCase();
    el.textContent = safeText;
}
