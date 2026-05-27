// tactical_map.js - High-fidelity OSINT Tactical Visualization

function initTacticalMap() {
    if (maps.tactical) return;

    const southWest = L.latLng(-85, -180);
    const northEast = L.latLng(85, 180);
    const bounds = L.latLngBounds(southWest, northEast);

    maps.tactical = L.map('map-tactical', {
        zoomControl: false,
        dragging: true,
        touchZoom: true,
        scrollWheelZoom: true, // Enabled for better UX
        doubleClickZoom: true, // Enabled for better UX
        boxZoom: true,
        keyboard: true,
        zoomSnap: 0.1,
        zoomDelta: 0.1,
        attributionControl: false,
        maxBounds: bounds,
        maxBoundsViscosity: 1.0,
        worldCopyJump: false
    }).setView([20, 0], 2);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}{r}.png', {
        opacity: 0.7,
        noWrap: true,
        bounds: bounds
    }).addTo(maps.tactical);

    // Create SVG layer for D3 - Ensure it's interactive
    L.svg({clickable:true}).addTo(maps.tactical);
    
    maps.tactical.on('move zoom', updateTacticalOverlay);
    updateTacticalOverlay();
    
    maps.tactical.on('zoomend moveend', () => {
        if (window.lastData) renderTacticalMap(window.lastData.articles);
    });
}

function updateTacticalOverlay() {
    const map = maps.tactical;
    if (!map) return;
    const overlay = document.getElementById('tactical-coord-overlay');
    if (!overlay) return;

    const center = map.getCenter();
    const zoom = map.getZoom().toFixed(1);
    
    // Use a more compact HUD for mobile
    const isMobile = window.innerWidth < 768;
    overlay.innerHTML = `
        <div style="background: rgba(0,255,65,0.1); border: 1px solid var(--theme-bright); padding: 2px 6px; border-radius: 2px; backdrop-filter: blur(4px);">
            <span style="color: var(--theme-bright); font-weight: bold;">${isMobile ? 'AO' : 'OP_CENTER'}:</span> 
            ${center.lat.toFixed(2)}N ${center.lng.toFixed(2)}E | ${zoom}x
        </div>
    `;
}

function renderTacticalMap(articles) {
    if (!maps.tactical) initTacticalMap();
    
    const map = maps.tactical;
    // Target the specific SVG group Leaflet creates
    const svg = d3.select("#map-tactical").select("svg");
    const g = svg.select("g");

    g.selectAll("*").remove();
    mapMarkers.tactical.forEach(m => map.removeLayer(m));
    mapMarkers.tactical = [];

    if (!articles || articles.length === 0) return;

    const points = articles
        .filter(a => countryCoords[a.sourcecountry])
        .map(a => {
            const coords = countryCoords[a.sourcecountry];
            const point = map.latLngToLayerPoint(new L.LatLng(coords[0], coords[1]));
            return [point.x, point.y, a];
        });

    const zoom = map.getZoom();
    const radius = Math.max(12, 30 / Math.pow(zoom, 0.4));
    
    const hexbin = d3.hexbin()
        .radius(radius)
        .extent([[0, 0], [map.getSize().x, map.getSize().y]]);

    const bins = hexbin(points);

    const colorScale = d3.scaleSequential(d3.interpolateYlGnBu)
        .domain([0, d3.max(bins, d => d.length) || 10]);

    const binsSelection = g.selectAll(".hex-bin")
        .data(bins)
        .enter().append("path")
        .attr("class", "hex-bin")
        .attr("d", d => hexbin.hexagon())
        .attr("transform", d => `translate(${d.x},${d.y})`)
        .attr("fill", d => colorScale(d.length))
        .attr("fill-opacity", 0.6)
        .attr("stroke", "var(--theme-bright)")
        .attr("stroke-width", 0.3)
        .style("pointer-events", "auto") // Crucial for events
        .style("cursor", "pointer");

    // Unified handler for hover (desktop) and tap (mobile)
    function showTacticalPopup(event, d) {
        d3.select(event.currentTarget).transition().duration(150)
            .attr("stroke-width", 1.5)
            .attr("fill-opacity", 0.9);
        
        const topSources = Array.from(new Set(d.map(p => p[2].sourcecountry))).slice(0, 3);
        const isMobile = window.innerWidth < 768;
        
        const content = `
            <div style="font-family:'Fira Code'; font-size:0.65rem; color:var(--theme-bright); background:rgba(0,0,0,0.95); padding:8px; border:1px solid var(--theme-bright); min-width:${isMobile ? '160px' : '220px'};">
                <div style="border-bottom:1px solid var(--theme-bright); padding-bottom:4px; margin-bottom:6px; display:flex; justify-content:space-between; font-weight:bold;">
                    <span>THEATER_SIG</span> <span>${d.length} NODES</span>
                </div>
                <div style="color:var(--text-main); margin-bottom:6px; max-height: 100px; overflow-y: auto;">
                    ${d.slice(0, 5).map(p => `• ${p[2].title.substring(0, isMobile ? 25 : 45)}...`).join("<br>")}
                    ${d.length > 5 ? `<br><span style="opacity:0.5">+ ${d.length - 5} others</span>` : ""}
                </div>
                <div style="font-size:0.55rem; color:var(--theme-bright); opacity:0.8; border-top: 1px solid rgba(0,255,65,0.2); padding-top:4px;">
                    LOCI: ${topSources.join(", ").toUpperCase()}
                </div>
            </div>
        `;
        
        L.popup({
            closeButton: false,
            offset: [0, -5],
            className: 'tactical-popup'
        })
            .setLatLng(map.layerPointToLatLng(L.point(d.x, d.y)))
            .setContent(content)
            .openOn(map);
    }

    function hideTacticalPopup(event) {
        d3.select(event.currentTarget).transition().duration(150)
            .attr("stroke-width", 0.3)
            .attr("fill-opacity", 0.6);
    }

    binsSelection
        .on("mouseover", showTacticalPopup)
        .on("mouseout", hideTacticalPopup)
        .on("click", function(event, d) {
            // Mobile optimization: one tap opens popup, two taps filters
            if (d.length > 0) {
                setGlobalFilter('country', d[0][2].sourcecountry);
                logSystem(`theater focused: ${d[0][2].sourcecountry.toUpperCase()}`);
            }
        });

    if (zoom > 4) {
        points.forEach(p => {
            const art = p[2];
            const icon = L.divIcon({
                className: 'tactical-marker',
                html: `<div class="tactical-diamond" style="width:6px; height:6px; background:var(--theme-bright); border:none; box-shadow: 0 0 8px var(--theme-bright);"></div>`,
                iconSize: [6, 6]
            });
            const marker = L.marker(countryCoords[art.sourcecountry], {icon: icon})
                .addTo(map)
                .bindPopup(`<div style="font-family:'Fira Code'; font-size:0.6rem; border:1px solid var(--theme-bright); padding:5px; background:rgba(0,0,0,0.9);">[ ${art.sourcecountry.toUpperCase()} ]<br>${art.title.toLowerCase()}</div>`, {
                    closeButton: false,
                    className: 'tactical-popup'
                });
            mapMarkers.tactical.push(marker);
        });
    }
}

window.addEventListener('resize', () => {
    if (maps.tactical) {
        maps.tactical.invalidateSize();
        updateTacticalOverlay();
    }
});
