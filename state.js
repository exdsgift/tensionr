// state.js - Global Application State
window.maps = { news: null, flights: null, tactical: null };
window.mapMarkers = { news: [], flights: [], tactical: [] };
window.charts = {};
window.globalFilter = { country: null, keyword: null };
window.activeDate = new Date().toISOString().split('T')[0];
window.lastData = null;
window.feedsIntervals = {};

// Theme Colors
window.THEME_BRIGHT = '';
window.THEME_MID = '';
window.THEME_DIM = '';
window.COLOR_WHITE = '';
window.COLOR_BORDER = '';
