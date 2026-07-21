// map.js - News and flight overlays on the main tactical map.

function renderMap(countries, articles) {
    if (!maps.main) initMainMap();
    overlays.news.clearLayers();

    if (!countries || !articles) return;
    Object.keys(countries).forEach(country => {
        if (countryCoords[country]) {
            const count = countries[country];
            const snippet = articles.find(a => a.sourcecountry === country)?.title.toLowerCase() || 'multi-node activity';
            // Two staggered rings make a continuous, fluid sonar sweep; the random
            // offset keeps the markers from pulsing in lockstep.
            const delay = Math.random() * 3;
            const icon = L.divIcon({
                className: 'pulse-icon',
                html: `<div class="pulse-ring" style="animation-delay: ${delay.toFixed(2)}s"></div>` +
                      `<div class="pulse-ring" style="animation-delay: ${(delay + 1.6).toFixed(2)}s"></div>` +
                      `<div class="pulse-dot"></div>`,
                iconSize: [0, 0],
                iconAnchor: [0, 0],
                popupAnchor: [0, -10]
            });
            L.marker(countryCoords[country], { icon: icon })
                .addTo(overlays.news)
                .on('click', () => setGlobalFilter('country', country))
                .bindPopup(`<div class="map-popup"><b>${country.toLowerCase()}</b><br>${count} signals detected<br><hr>"${snippet}"</div>`);
        }
    });
}

let flightHistory = {};

function renderFlightMap(intel) {
    if (!maps.main) initMainMap();
    overlays.flights.clearLayers();

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
                L.polyline([originPos, [asset.lat, asset.lon]], {
                    color: tacticalColor,
                    weight: 2,
                    opacity: 0.5,
                    dashArray: '6, 12',
                    interactive: false,
                    renderer: window.flightRenderer
                }).addTo(overlays.flights);
            }

            if (flightHistory[asset.icao24].length > 1) {
                const trailColor = asset.is_mil ? THEME_BRIGHT : THEME_MID;
                L.polyline(flightHistory[asset.icao24], {
                    color: trailColor, weight: 8, opacity: 0.5, lineCap: 'round',
                    renderer: window.flightRenderer
                }).addTo(overlays.flights);
                L.polyline(flightHistory[asset.icao24], {
                    color: trailColor, weight: 3.5, opacity: 1.0, lineCap: 'round',
                    renderer: window.flightRenderer
                }).addTo(overlays.flights);
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
            L.marker([asset.lat, asset.lon], { icon: icon })
                .addTo(overlays.flights)
                .bindPopup(`<div class="map-popup"><b>${asset.callsign}</b><br>ORIGIN: ${asset.origin}<br>ALT: ${asset.alt}m<br>VEL: ${asset.vel}km/h</div>`);
        }
    });

    Object.keys(flightHistory).forEach(icao => {
        if (!activeIcaos.has(icao)) delete flightHistory[icao];
    });
}
