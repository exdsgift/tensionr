const countryCoords = {
    "United States": [38.8951, -77.0364],
    "United Kingdom": [51.5074, -0.1278],
    "Qatar": [25.2854, 51.5310],
    "France": [48.8566, 2.3522],
    "Russia": [55.7558, 37.6173],
    "Russian Federation": [55.7558, 37.6173],
    "Japan": [35.6762, 139.6503],
    "Australia": [-35.2809, 149.1300],
    "India": [28.6139, 77.2090],
    "Israel": [31.7683, 35.2137],
    "Ukraine": [50.4501, 30.5234],
    "Singapore": [1.3521, 103.8198],
    "Canada": [45.4215, -75.6972],
    "Saudi Arabia": [24.6877, 46.7219],
    "Uruguay": [-34.9011, -56.1645],
    "Iran": [35.6892, 51.3890],
    "China": [39.9042, 116.4074],
    "Germany": [52.5200, 13.4050],
    "Turkey": [39.9334, 32.8597],
    "Egypt": [30.0444, 31.2357],
    "United Arab Emirates": [24.4539, 54.3773],
    "South Korea": [37.5665, 126.9780],
    "North Korea": [39.0392, 125.7625],
    "Taiwan": [25.0330, 121.5654],
    "Pakistan": [33.6844, 73.0479],
    "Syria": [33.5138, 36.2765],
    "Lebanon": [33.8938, 35.5018],
    "Yemen": [15.3694, 44.1910],
    "Iraq": [33.3152, 44.3661],
    "Afghanistan": [34.5553, 69.2075],
    "Mexico": [19.4326, -99.1332],
    "Brazil": [-15.7975, -47.8919],
    "Venezuela": [10.4806, -66.9036],
    "Colombia": [4.7110, -74.0721],
    "South Africa": [-25.7479, 28.2293],
    "Nigeria": [9.0579, 7.4951],
    "Kenya": [-1.2921, 36.8219],
    "Somalia": [2.0469, 45.3182],
    "Sudan": [15.5007, 32.5599],
    "Ethiopia": [9.0300, 38.7400],
    "Poland": [52.2297, 21.0122],
    "Italy": [41.9028, 12.4964],
    "Spain": [40.4168, -3.7038],
    "Palestine": [31.9038, 35.2034]
};

function deduplicateArticles(articles) {
    if (!articles) return [];
    const grouped = {};
    articles.forEach(art => {
        // Normalize title for fuzzy matching
        const normTitle = art.title.toLowerCase().replace(/[^\w\s]/gi, '').substring(0, 45);
        if (!grouped[normTitle]) {
            grouped[normTitle] = { ...art, all_domains: new Set([art.domain]) };
        } else {
            grouped[normTitle].all_domains.add(art.domain);
            // Keep the one with higher manipulation score if conflict
            if ((art.manipulation_score || 0) > (grouped[normTitle].manipulation_score || 0)) {
                grouped[normTitle].manipulation_score = art.manipulation_score;
                grouped[normTitle].narrative_emotion = art.narrative_emotion;
            }
        }
    });
    return Object.values(grouped).map(art => {
        art.domain = Array.from(art.all_domains).join(', ');
        delete art.all_domains;
        return art;
    });
}
