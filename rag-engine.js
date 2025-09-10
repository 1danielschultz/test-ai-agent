// RAG Engine - Local Knowledge Base Search and Context Injection
// Provides UDAS-organized QuickBooks troubleshooting context to SmolLM2

class LocalRAG {
    constructor() {
        this.knowledge = {};
        this.searchIndex = {};
        this.isLoaded = false;
        this.categories = ['banking', 'invoicing', 'payroll', 'reports', 'inventory'];
    }

    async initialize() {
        if (this.isLoaded) return true;
        
        try {
            console.log('🔍 Loading RAG knowledge base...');
            
            // Load search index first
            await this.loadSearchIndex();
            
            // Load knowledge categories on-demand for performance
            console.log('✅ RAG engine initialized');
            this.isLoaded = true;
            return true;
            
        } catch (error) {
            console.error('❌ Failed to initialize RAG engine:', error);
            return false;
        }
    }

    async loadSearchIndex() {
        const response = await fetch('./knowledge/search-index.json');
        this.searchIndex = await response.json();
    }

    async loadKnowledgeCategory(category) {
        if (this.knowledge[category]) {
            return this.knowledge[category];
        }
        
        try {
            const response = await fetch(`./knowledge/udas-${category}.json`);
            this.knowledge[category] = await response.json();
            return this.knowledge[category];
        } catch (error) {
            console.warn(`Failed to load knowledge category: ${category}`, error);
            return null;
        }
    }

    // Extract keywords from user message
    extractKeywords(message) {
        const words = message.toLowerCase()
                            .replace(/[^\w\s]/g, ' ')
                            .split(/\s+/)
                            .filter(word => word.length > 2);
        
        // Add multi-word phrases
        const phrases = this.extractPhrases(message.toLowerCase());
        return [...words, ...phrases];
    }

    extractPhrases(message) {
        const phrases = [];
        const commonPhrases = [
            'bank connection', 'direct deposit', 'profit loss', 'balance sheet',
            'cash flow', 'pay invoice', 'online banking', 'credit card',
            'tax calculation', 'inventory tracking', 'stock levels'
        ];
        
        for (const phrase of commonPhrases) {
            if (message.includes(phrase)) {
                phrases.push(phrase);
            }
        }
        return phrases;
    }

    // Determine most relevant categories for the user's question
    identifyRelevantCategories(keywords) {
        const categoryScores = {};
        
        // Initialize scores
        this.categories.forEach(cat => categoryScores[cat] = 0);
        
        // Score based on keyword matches
        for (const keyword of keywords) {
            if (this.searchIndex.keywords[keyword]) {
                for (const category of this.searchIndex.keywords[keyword]) {
                    categoryScores[category] += 1;
                }
            }
        }
        
        // Return categories sorted by relevance
        return Object.entries(categoryScores)
                     .filter(([, score]) => score > 0)
                     .sort(([, a], [, b]) => b - a)
                     .map(([category]) => category)
                     .slice(0, 2); // Top 2 most relevant categories
    }

    // Determine current UDAS layer based on conversation context
    determineCurrentUdasLayer(userMessage, conversationHistory = []) {
        const message = userMessage.toLowerCase();
        const layers = this.searchIndex.udas_layers;
        
        // Check for layer-specific keywords
        for (const [layer, info] of Object.entries(layers)) {
            for (const keyword of info.keywords) {
                if (message.includes(keyword)) {
                    return layer;
                }
            }
        }
        
        // Default progression: start with user layer
        return 'user';
    }

    // Calculate relevance score between keywords and triggers
    calculateRelevanceScore(userKeywords, triggerKeywords) {
        let matches = 0;
        let totalTriggers = triggerKeywords.length;
        
        for (const trigger of triggerKeywords) {
            for (const userKeyword of userKeywords) {
                if (this.isKeywordMatch(userKeyword, trigger)) {
                    matches++;
                    break;
                }
            }
        }
        
        return matches / totalTriggers;
    }

    isKeywordMatch(userKeyword, triggerKeyword) {
        // Exact match
        if (userKeyword === triggerKeyword) return true;
        
        // Partial match for longer phrases
        if (userKeyword.includes(triggerKeyword) || triggerKeyword.includes(userKeyword)) {
            return true;
        }
        
        // Fuzzy match for typos (simple Levenshtein for short words)
        if (this.calculateLevenshteinDistance(userKeyword, triggerKeyword) <= 1 && 
            Math.min(userKeyword.length, triggerKeyword.length) >= 4) {
            return true;
        }
        
        return false;
    }

    calculateLevenshteinDistance(a, b) {
        const matrix = Array(b.length + 1).fill().map(() => Array(a.length + 1).fill(0));
        
        for (let i = 0; i <= a.length; i++) matrix[0][i] = i;
        for (let j = 0; j <= b.length; j++) matrix[j][0] = j;
        
        for (let j = 1; j <= b.length; j++) {
            for (let i = 1; i <= a.length; i++) {
                const cost = a[i - 1] === b[j - 1] ? 0 : 1;
                matrix[j][i] = Math.min(
                    matrix[j - 1][i] + 1,     // deletion
                    matrix[j][i - 1] + 1,     // insertion
                    matrix[j - 1][i - 1] + cost // substitution
                );
            }
        }
        
        return matrix[b.length][a.length];
    }

    // Main search function to find relevant knowledge
    async searchRelevantKnowledge(userMessage, currentUdasLayer = 'user') {
        if (!this.isLoaded) {
            await this.initialize();
        }
        
        const keywords = this.extractKeywords(userMessage);
        const relevantCategories = this.identifyRelevantCategories(keywords);
        const matches = [];
        
        console.log(`🔍 RAG Search: Keywords=${keywords.slice(0,5)}, Categories=${relevantCategories}, Layer=${currentUdasLayer}`);
        
        // Search through relevant categories
        for (const category of relevantCategories) {
            const knowledge = await this.loadKnowledgeCategory(category);
            if (!knowledge) continue;
            
            const layerData = knowledge.udas_layers[currentUdasLayer] || [];
            
            for (const item of layerData) {
                const score = this.calculateRelevanceScore(keywords, item.trigger_keywords);
                if (score > 0.3) {  // Relevance threshold
                    matches.push({
                        ...item,
                        score,
                        category,
                        layer: currentUdasLayer
                    });
                }
            }
        }
        
        // Sort by relevance and return top matches
        const topMatches = matches.sort((a, b) => b.score - a.score).slice(0, 3);
        console.log(`📊 RAG Found ${topMatches.length} relevant matches`);
        
        return topMatches;
    }

    // Generate context snippets for SmolLM2 prompt enhancement
    formatContextForPrompt(matches) {
        if (matches.length === 0) {
            return '';
        }
        
        const contextSnippets = matches.map(match => {
            const questions = match.diagnostic_questions.slice(0, 2).join(' ');
            const solutions = match.solutions.slice(0, 3).join(' ');
            return `Issue: ${match.issue}\nQuestions: ${questions}\nSolutions: ${solutions}`;
        }).join('\n\n');
        
        return `\n\n## Relevant Knowledge Context:\n${contextSnippets}\n\nUse this context to inform your UDAS-guided response, but adapt the language to be conversational.`;
    }

    // Get status of RAG system
    getStatus() {
        return {
            loaded: this.isLoaded,
            categories: this.categories,
            knowledgeLoaded: Object.keys(this.knowledge)
        };
    }
}

// Export for integration with SmolLM2
window.LocalRAG = LocalRAG;
