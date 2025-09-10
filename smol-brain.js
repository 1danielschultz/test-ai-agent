// SmolLM2-135M Brain - WebAssembly LLM for QuickBooks Assistant
// Uses llama.cpp WASM for efficient inference

class SmolLMBrain {
    constructor() {
        this.isLoading = false;
        this.isReady = false;
        this.llamaCpp = null;
        this.model = null;
        this.modelPath = new URL('./models/SmolLM2-135M-Instruct.Q4_1.gguf', window.location.href).href;
        
        // Response caching for speed
        this.responseCache = new Map();
        this.maxCacheSize = 50;
        
        // RAG engine for knowledge enhancement
        this.rag = new LocalRAG();
        this.ragReady = false;
    }

    async initialize() {
        if (this.isLoading || this.isReady) return this.isReady;
        
        try {
            this.isLoading = true;
            console.log('🧠 Loading SmolLM2-135M-Instruct...');
            
            // Load llama.cpp WASM
            await this.loadLlamaCppWasm();
            
            // Download and load the model
            await this.loadModel();
            
            // Initialize RAG engine
            await this.initializeRAG();
            
            this.isReady = true;
            this.isLoading = false;
            
            console.log('✅ SmolLM2 ready for inference!');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to load SmolLM2:', error);
            this.isLoading = false;
            return false;
        }
    }

    async loadLlamaCppWasm() {
        console.log('🔄 Loading Wllama directly...');
        
        try {
            // Use latest wllama with SmolLM2 support
            const wllamaModule = await import('https://cdn.jsdelivr.net/npm/@wllama/wllama@2.3.5/esm/index.js');
            
            this.llamaCpp = wllamaModule.Wllama;
            
            // Complete WASM config for latest version
            this.wasmConfig = {
                'single-thread/wllama.js': 'https://cdn.jsdelivr.net/npm/@wllama/wllama@2.3.5/esm/single-thread/wllama.js',
                'single-thread/wllama.wasm': 'https://cdn.jsdelivr.net/npm/@wllama/wllama@2.3.5/esm/single-thread/wllama.wasm',
                'multi-thread/wllama.js': 'https://cdn.jsdelivr.net/npm/@wllama/wllama@2.3.5/esm/multi-thread/wllama.js',
                'multi-thread/wllama.wasm': 'https://cdn.jsdelivr.net/npm/@wllama/wllama@2.3.5/esm/multi-thread/wllama.wasm',
                'multi-thread/wllama.worker.mjs': 'https://cdn.jsdelivr.net/npm/@wllama/wllama@2.3.5/esm/multi-thread/wllama.worker.mjs',
            };
            
            console.log('✅ Wllama loaded successfully');
            console.log('🔄 Wllama class available:', !!this.llamaCpp);
            
        } catch (error) {
            console.warn('🔄 Wllama direct import failed, will use rule-based fallback:', error);
            this.llamaCpp = null;
            this.wasmConfig = null;
        }
    }

    async loadModel() {
        console.log('📥 Loading local SmolLM2 model (98MB)...');
        console.log('🔗 Model URL:', this.modelPath);
        
        try {
            if (!this.llamaCpp || !this.wasmConfig) {
                console.warn('🔄 Wllama not available, will use rule-based fallback');
                return;
            }
            
            console.log('🔄 Initializing Wllama...');
            
            // Initialize Wllama with optimized settings for speed
            this.model = new this.llamaCpp(this.wasmConfig, {
                n_threads: Math.min(navigator.hardwareConcurrency || 4, 12),
                n_ctx: 2048,      // Reduced context window for faster inference
                n_batch: 512,     // Larger batch size for efficiency
                n_gpu_layers: 0   // Ensure CPU-only processing
            });
            
            // Load model from local file using loadModelFromUrl
            console.log('🔄 Loading model with Wllama...');
            await this.model.loadModelFromUrl(this.modelPath, {
                progressCallback: ({ loaded, total }) => {
                    const progress = Math.round((loaded / total) * 100);
                    console.log(`📥 Model loading: ${progress}%`);
                },
                parallelDownloads: 3,
                allowOffline: true
            });

            console.log('✅ Model initialized successfully!');

        } catch (error) {
            console.warn('Failed to load with Wllama, will use rule-based responses:', error);
            this.model = null;
            // Don't throw - just mark as "loaded" and use fallback responses
        }
    }

    async initializeRAG() {
        try {
            this.ragReady = await this.rag.initialize();
            if (this.ragReady) {
                console.log('🔍 RAG knowledge base loaded successfully');
            }
        } catch (error) {
            console.warn('⚠️ RAG initialization failed, using basic responses:', error);
            this.ragReady = false;
        }
    }

    async generateResponse(userMessage) {
        if (!this.isReady) {
            return {
                success: false,
                message: "🤖 SmolLM2 model is still loading. Please wait..."
            };
        }

        // Check cache first for speed
        const cacheKey = this.normalizeMessage(userMessage);
        const cachedResponse = this.responseCache.get(cacheKey);
        if (cachedResponse) {
            console.log('⚡ Using cached response for faster delivery');
            return {
                success: true,
                message: cachedResponse,
                source: 'cache'
            };
        }

        // Try WASM inference with wllama if available
        try {
            if (this.model && this.llamaCpp) {
                console.log('🤖 Generating response with SmolLM2...');
                
                // Get RAG context if available
                let ragContext = '';
                if (this.ragReady) {
                    const currentLayer = this.rag.determineCurrentUdasLayer(userMessage);
                    const relevantKnowledge = await this.rag.searchRelevantKnowledge(userMessage, currentLayer);
                    ragContext = this.rag.formatContextForPrompt(relevantKnowledge);
                }
                
                const prompt = `<|im_start|>system
You are a QuickBooks Online expert who uses UDAS methodology to systematically troubleshoot issues.

UDAS Framework:
- USER layer: Check permissions, user training, workflow issues first
- DATA layer: Look for duplicates, missing entries, corrupted data
- APPLICATION layer: Browser problems, cache issues, QuickBooks bugs
- SYSTEM layer: Internet connectivity, external service issues

Response Format:
1. Acknowledge the issue with empathy
2. Ask ONE specific diagnostic question (start with User layer)
3. Briefly explain why you're asking this question
4. Provide a helpful tip while they investigate

Example Response:
"I understand how frustrating bank connection issues can be! Let's solve this systematically.

First, let's check the User layer - have you successfully logged into your bank's website today using the same credentials? I'm asking because banks often require direct login before allowing third-party connections.

While you check that, here's a tip: Most connection issues resolve when you verify your online banking is active first."${ragContext}<|im_end|>
<|im_start|>user
${userMessage}<|im_end|>
<|im_start|>assistant
`;

                const response = await this.model.createCompletion(prompt, {
                    nPredict: 150,        // Increased for proper UDAS responses
                    sampling: {
                        temp: 0.7,        // Higher temp for more varied responses
                        top_k: 40,        // More options for better quality
                        top_p: 0.9        // More diversity in sampling
                    },
                    stopSequences: ['<|im_end|>', '<|im_start|>']
                });

                let text = this.cleanResponse(response);
                
                if (text.length > 15 && !this.isGenericResponse(text)) {
                    console.log('✅ SmolLM2 response generated successfully');
                    
                    // Cache the successful response for future use
                    this.cacheResponse(cacheKey, text);
                    
                    return {
                        success: true,
                        message: text,
                        source: 'smollm2-local'
                    };
                }
            }
        } catch (error) {
            console.warn('WASM inference failed, using enhanced rule-based responses:', error);
        }

        // Use enhanced rule-based responses (very comprehensive for QuickBooks)
        return {
            success: true,
            message: this.getQuickBooksGuidance(userMessage),
            source: 'enhanced-rules'
        };
    }

    cleanResponse(text) {
        // Remove instruction tokens and clean up
        text = text.replace(/<\|im_start\|>/g, '')
                  .replace(/<\|im_end\|>/g, '')
                  .replace(/^assistant\s*/i, '')
                  .trim();

        // Remove incomplete sentences at the end
        const sentences = text.split(/[.!?]+/);
        if (sentences.length > 1 && sentences[sentences.length - 1].trim().length < 10) {
            sentences.pop();
            text = sentences.join('.') + '.';
        }

        return text;
    }

    // Cache management for speed optimization
    normalizeMessage(message) {
        return message.toLowerCase()
                     .replace(/[^\w\s]/g, '')
                     .replace(/\s+/g, ' ')
                     .trim()
                     .substring(0, 100); // Limit key length
    }

    cacheResponse(key, response) {
        // Manage cache size
        if (this.responseCache.size >= this.maxCacheSize) {
            const firstKey = this.responseCache.keys().next().value;
            this.responseCache.delete(firstKey);
        }
        this.responseCache.set(key, response);
    }

    isGenericResponse(text) {
        const badPhrases = [
            'I\'m sorry for the confusion',
            'I\'m unable to provide',
            'I\'m not equipped to',
            'I can\'t help with',
            'I don\'t have access',
            'as a UDAS-guided AI',
            'I\'m designed to assist you with your business needs'
        ];
        
        // Check for bad generic responses that avoid helping
        const hasGenericAvoidance = badPhrases.some(phrase => 
            text.toLowerCase().includes(phrase.toLowerCase())
        );
        
        // Check if response is too short and generic
        const tooShortAndGeneric = text.length < 30 && (
            text.toLowerCase().includes('help') || 
            text.toLowerCase().includes('assist')
        );
        
        return hasGenericAvoidance || tooShortAndGeneric;
    }

    getQuickBooksGuidance(userMessage) {
        const message = userMessage.toLowerCase();
        
        // UDAS-guided fallback responses 
        if (message.includes('bank') || message.includes('connect') || message.includes('link')) {
            return "I understand how frustrating bank connection issues can be! Let's work through this systematically using UDAS troubleshooting.\n\nFirst, let's check the User layer - have you successfully logged into your bank's website today using the same credentials you use for QuickBooks? I'm asking this because banks often require you to log in directly before allowing third-party connections.\n\nWhile you check that, here's a quick tip: Most connection issues resolve when you verify your online banking is active first.";
        }
        
        if (message.includes('invoice') || message.includes('bill') || message.includes('customer')) {
            return "Create professional invoices in QuickBooks:\n\n1. Go to **Sales** → **Invoices** → **Create Invoice**\n2. Select or add customer details\n3. Add products/services with quantities and rates\n4. Set payment terms and due date\n5. Email directly or download PDF\n\n**Pro tip**: Set up recurring invoices for regular clients under **Recurring Transactions**.";
        }
        
        if (message.includes('expense') || message.includes('receipt') || message.includes('cost')) {
            return "Track expenses efficiently:\n\n1. **Mobile**: Use QuickBooks app to photograph receipts instantly\n2. **Desktop**: Go to **Expenses** → **Add Expense**\n3. Enter vendor, amount, and category\n4. Upload receipt image\n5. Link to projects if applicable\n\n**Smart feature**: Receipt capture auto-extracts vendor, date, and amount data.";
        }
        
        if (message.includes('payroll') || message.includes('employee') || message.includes('salary')) {
            return "QuickBooks Payroll setup:\n\n1. **Upgrade**: Payroll requires subscription ($45/month + $6/employee)\n2. **Setup**: Go to **Payroll** → **Get Started**\n3. **Employees**: Add worker details, tax info, pay rates\n4. **Schedule**: Set pay frequency (weekly, bi-weekly, monthly)\n5. **Run**: Process payroll and handle tax filings automatically\n\n**Includes**: Direct deposit, tax calculations, W-2s, and compliance.";
        }
        
        if (message.includes('report') || message.includes('profit') || message.includes('loss') || message.includes('financial')) {
            return "Generate key financial reports:\n\n**Profit & Loss**: Shows income vs expenses over time\n**Balance Sheet**: Assets, liabilities, and equity snapshot\n**Cash Flow**: Track money in/out by period\n\n**Steps**: **Reports** → Search report name → Select date range → **Run Report**\n\n**Customize**: Filter by class, location, or customer for detailed analysis.";
        }
        
        if (message.includes('tax') || message.includes('1099') || message.includes('deduction')) {
            return "QuickBooks tax features:\n\n**Sales Tax**: **Taxes** → **Sales Tax** → Set up rates and track automatically\n**1099s**: **Payroll** → **Contractors** → Generate 1099-NEC forms\n**Deductions**: Categorize expenses properly for tax writeoffs\n**Export**: Send data directly to TurboTax or accountant\n\n**Year-end**: Run tax summary reports and backup your data.";
        }
        
        if (message.includes('inventory') || message.includes('product') || message.includes('stock')) {
            return "Manage inventory in QuickBooks:\n\n1. **Enable**: **Settings** → **Account & Settings** → **Sales** → Turn on inventory tracking\n2. **Add Items**: **Sales** → **Products & Services** → **New** → **Inventory**\n3. **Set Details**: SKU, cost, sale price, quantity on hand\n4. **Reorder**: Set reorder points for low stock alerts\n5. **Track**: Quantities auto-update with sales and purchases\n\n**Reports**: Use inventory reports to monitor stock levels and valuation.";
        }

        if (message.includes('error') || message.includes('problem') || message.includes('not working') || message.includes('issue')) {
            return "QuickBooks troubleshooting steps:\n\n**Browser Issues**:\n• Clear cache and cookies\n• Try incognito/private mode\n• Disable browser extensions\n• Update browser to latest version\n\n**Sync Problems**:\n• Check internet connection\n• Update bank credentials\n• Refresh browser page\n\n**Need Help?**: Contact QuickBooks Support at **1-800-446-8848** or use in-app chat.";
        }
        
        // Default comprehensive response
        return "I'm your QuickBooks Online AI assistant! I can help with:\n\n💰 **Banking** - Connect accounts, categorize transactions\n📄 **Invoicing** - Create professional invoices, set up recurring billing\n📊 **Reports** - P&L, Balance Sheet, Cash Flow analysis\n💼 **Expenses** - Receipt capture, expense tracking, tax deductions\n👥 **Payroll** - Employee management, tax compliance, direct deposit\n📦 **Inventory** - Stock tracking, reorder alerts, product management\n🔧 **Setup & Support** - Account configuration, troubleshooting\n\n**What specific QuickBooks task can I help you with today?**";
    }

    getStatus() {
        if (this.isLoading) return { status: 'loading', message: 'Loading SmolLM2...' };
        if (this.isReady) return { status: 'ready', message: 'SmolLM2 ready' };
        return { status: 'offline', message: 'SmolLM2 not loaded' };
    }

    getModelInfo() {
        return {
            name: 'SmolLM2-135M-Instruct',
            size: '95MB (Q8_0 quantized)',
            params: '135M parameters',
            training: '2T tokens',
            features: ['Instruction-tuned', 'Chat optimized', 'GGUF format', 'WebAssembly inference']
        };
    }
}

// Fallback to original implementation if SmolLM2 fails
class FallbackBrain {
    constructor() {
        this.isReady = true;
    }

    async initialize() {
        return true;
    }

    async generateResponse(userMessage) {
        // Use the same rule-based responses as SmolLM2's fallback
        const smolBrain = new SmolLMBrain();
        return {
            success: true,
            message: smolBrain.getQuickBooksGuidance(userMessage),
            source: 'rules'
        };
    }

    getStatus() {
        return { status: 'ready', message: 'Rule-based responses' };
    }
}

// Export for main application
window.SmolLMBrain = SmolLMBrain;
window.FallbackBrain = FallbackBrain;
