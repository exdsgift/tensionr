// state.js - Global Application State
window.maps = { main: null };
window.overlays = { news: null, flights: null };
window.layerToggles = { news: true, flights: true };
window.charts = {};
window.globalFilter = { country: null, keyword: null };
window.activeDate = new Date().toISOString().split('T')[0];
window.lastData = null;
window.feedsIntervals = {};

// Theme Colors (populated from CSS variables by updateThemeColors)
window.THEME_BRIGHT = '';
window.THEME_MID = '';
window.THEME_DIM = '';
window.COLOR_WHITE = '';
window.COLOR_BORDER = '';
window.CHART_GRID = '';
window.CHART_TICK = '';
window.TOOLTIP_BG = '';
