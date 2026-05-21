// Tensionr Intelligence Web Worker
// Offloads heavy data processing from the main UI thread

self.onmessage = function(e) {
    const { type, data } = e.data;

    if (type === 'PROCESS_DATA') {
        const { articles, keywords } = data;
        
        // 1. Deduplicate Articles (Heavy O(N) regex operation)
        const processedArticles = deduplicateArticles(articles);
        
        // 2. Process Keywords for WordCloud
        const processedKeywords = processKeywords(keywords);

        self.postMessage({
            type: 'DATA_PROCESSED',
            payload: {
                articles: processedArticles,
                keywords: processedKeywords
            }
        });
    }
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

function processKeywords(keywords) {
    if (!keywords) return [];
    const entries = Object.entries(keywords);
    if (entries.length === 0) return [];

    const max = Math.max(...entries.map(e => (typeof e[1] === 'object' ? e[1].count : e[1])));
    
    return entries.map(([word, info]) => {
        const count = typeof info === 'object' ? info.count : info;
        const type = typeof info === 'object' ? info.type : "UNKNOWN";
        const weight = count / max;
        
        return { word, count, type, weight };
    });
}
