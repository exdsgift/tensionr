// tactical_map.js - Main full-screen map: base tiles, layer panes and coordinate HUD.

function initMainMap() {
    if (maps.main) return;

    const southWest = L.latLng(-85, -180);
    const northEast = L.latLng(85, 180);
    const bounds = L.latLngBounds(southWest, northEast);

    maps.main = L.map('map-main', {
        zoomControl: false,
        dragging: true,
        touchZoom: true,
        scrollWheelZoom: true,
        doubleClickZoom: true,
        boxZoom: true,
        keyboard: true,
        zoomSnap: 0.1,
        zoomDelta: 0.1,
        attributionControl: false,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0,
        worldCopyJump: false
    });

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
        noWrap: true,
        bounds: bounds
    }).addTo(maps.main);

    // Dedicated pane + renderer for flight vectors, above the overlay pane (400)
    // and below markers (600).
    maps.main.createPane('flightsPane');
    maps.main.getPane('flightsPane').style.zIndex = 450;
    window.flightRenderer = L.svg({ pane: 'flightsPane' });

    // Marker overlays, toggled from the layers legend.
    overlays.news = L.layerGroup();
    overlays.flights = L.layerGroup();
    if (layerToggles.news) overlays.news.addTo(maps.main);
    if (layerToggles.flights) overlays.flights.addTo(maps.main);

    fitWorldZoom();
    maps.main.setView([25, 0], maps.main.getMinZoom());

    // The container can be 0-sized at init (or change on rotation/panel resize):
    // re-fit whenever its real dimensions change.
    if (window.ResizeObserver) {
        new ResizeObserver(() => {
            if (!maps.main) return;
            maps.main.invalidateSize({ animate: false });
            fitWorldZoom();
        }).observe(maps.main.getContainer());
    }

    maps.main.on('move zoom', updateTacticalOverlay);
    updateTacticalOverlay();
}

/**
 * Keep the world exactly filling the viewport: the minimum zoom is the level at
 * which one mercator world (256*2^z px) covers the larger viewport dimension,
 * so zooming out never exposes black bands or repeated worlds on any device.
 */
function fitWorldZoom() {
    const map = maps.main;
    if (!map) return;
    // Read the container directly: Leaflet's getSize() cache can be stale (0x0)
    // right after map creation.
    const el = map.getContainer();
    const w = el.clientWidth;
    const h = el.clientHeight;
    if (!w || !h) return;
    map.invalidateSize({ animate: false });
    const minZoom = Math.ceil(Math.log2(Math.max(w, h) / 256) * 10) / 10;
    map.setMinZoom(minZoom);
    if (!(map.getZoom() >= minZoom)) map.setZoom(minZoom);
}

function updateTacticalOverlay() {
    const map = maps.main;
    if (!map) return;
    const overlay = document.getElementById('tactical-coord-overlay');
    if (!overlay) return;

    const center = map.getCenter();
    const zoom = map.getZoom().toFixed(1);

    // Use a more compact HUD for mobile
    const isMobile = window.innerWidth < 768;
    overlay.innerHTML = `
        <div class="coord-chip">
            <span class="coord-chip-label">${isMobile ? 'AO' : 'OP_CENTER'}:</span>
            ${center.lat.toFixed(2)}N ${center.lng.toFixed(2)}E | ${zoom}x
        </div>
    `;
}

window.addEventListener('resize', () => {
    if (maps.main) {
        maps.main.invalidateSize();
        fitWorldZoom();
        updateTacticalOverlay();
    }
});
