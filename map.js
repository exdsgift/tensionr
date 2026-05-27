// map.js - Leaflet Map integration and marker rendering

function initMaps() {
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

function renderMap(countries, articles) {
    if (!maps.news) initMaps();
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
    mapMarkers.flights.forEach(m => maps.flights.removeLayer(m));
    mapMarkers.flights = [];

    const overlay = document.querySelector('#map-flights div[style*="z-index: 1000"]');
    if (overlay && intel && intel.assets && intel.assets.length > 0) overlay.style.display = 'none';

    if (!intel || !intel.assets) return;
    const activeIcaos = new Set();

    intel.assets.forEach(asset => {
        if (asset.lat && asset.lon) {
            activeIcaos.add(asset.icao24);
            if (!flightHistory[asset.icao24]) flightHistory[asset.icao24] = [];
            const lastPos = flightHistory[asset.icao24][flightHistory[asset.icao24].length - 1];
            if (!lastPos || lastPos[0] !== asset.lat || lastPos[1] !== asset.lon) {
                flightHistory[asset.icao24].push([asset.lat, asset.lon]);
                if (flightHistory[asset.icao24].length > 15) flightHistory[asset.icao24].shift();
            }

            if (countryCoords[asset.origin]) {
                const originPos = countryCoords[asset.origin];
                const tacticalColor = asset.is_mil ? THEME_BRIGHT : THEME_MID;
                const strategicLine = L.polyline([originPos, [asset.lat, asset.lon]], {
                    color: tacticalColor,
                    weight: 2,
                    opacity: 0.5,
                    dashArray: '6, 12',
                    interactive: false
                }).addTo(maps.flights);
                mapMarkers.flights.push(strategicLine);
            }

            if (flightHistory[asset.icao24].length > 1) {
                const trailColor = asset.is_mil ? THEME_BRIGHT : THEME_MID;
                const glowTrail = L.polyline(flightHistory[asset.icao24], {
                    color: trailColor, weight: 8, opacity: 0.5, lineCap: 'round'
                }).addTo(maps.flights);
                mapMarkers.flights.push(glowTrail);
                const polyline = L.polyline(flightHistory[asset.icao24], {
                    color: trailColor, weight: 3.5, opacity: 1.0, lineCap: 'round'
                }).addTo(maps.flights);
                mapMarkers.flights.push(polyline);
            }

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

    Object.keys(flightHistory).forEach(icao => {
        if (!activeIcaos.has(icao)) delete flightHistory[icao];
    });
}
