// Tensionr Intelligence Web Worker
// Offloads heavy data processing from the main UI thread

importScripts('utils.js');

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
