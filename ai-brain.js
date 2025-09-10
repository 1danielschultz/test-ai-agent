// Browser-based AI Engine for QuickBooks Assistant
// Uses Transformers.js for client-side inference

class AIBrain {
    constructor() {
        this.isLoading = false;
        this.isReady = false;
        this.generator = null;
        this.tokenizer = null;
    }

    async initialize() {
        if (this.isLoading || this.isReady) return;
        
        try {
            this.isLoading = true;
            console.log('🧠 Loading AI model...');
            
            // Import Transformers.js
            const { pipeline } = await import('https://cdn.jsdelivr.net/npm/@xenova/transformers@2.17.2');
            
            // Load DistilGPT-2 (82MB, fast, decent quality)
            this.generator = await pipeline('text-generation', 'Xenova/distilgpt2');
            
            this.isReady = true;
            this.isLoading = false;
            
            console.log('✅ AI model ready!');
            return true;
            
        } catch (error) {
            console.error('❌ Failed to load AI:', error);
            this.isLoading = false;
            return false;
        }
    }

    async generateResponse(userMessage) {
        if (!this.isReady) {
            return {
                success: false,
                message: "🤖 AI model is still loading. Please wait..."
            };
        }

        try {
            // Create QuickBooks-focused prompt
            const prompt = this.createQuickBooksPrompt(userMessage);
            
            const result = await this.generator(prompt, {
                max_length: 120,
                temperature: 0.7,
                do_sample: true,
                pad_token_id: 50256,
                repetition_penalty: 1.1
            });

            let response = result[0].generated_text;
            response = this.cleanResponse(response, prompt);
            
            // Fallback to rule-based if AI response is poor
            if (response.length < 15 || this.isGenericResponse(response)) {
                response = this.getRuleBasedResponse(userMessage);
            }

            return {
                success: true,
                message: response,
                source: 'ai'
            };

        } catch (error) {
            console.error('AI generation error:', error);
            return {
                success: true,
                message: this.getRuleBasedResponse(userMessage),
                source: 'fallback'
            };
        }
    }

    createQuickBooksPrompt(userMessage) {
        return `QuickBooks Online Support Chat

User: ${userMessage}
Assistant: `;
    }

    cleanResponse(response, prompt) {
        // Remove the prompt from response
        response = response.replace(prompt, '').trim();
        
        // Stop at natural ending points
        const stopTokens = ['\nUser:', '\nAssistant:', 'User:', '###', '\n\n'];
        for (const token of stopTokens) {
            const index = response.indexOf(token);
            if (index !== -1) {
                response = response.substring(0, index);
            }
        }
        
        // Clean up and format
        response = response.trim();
        if (response.endsWith('.') || response.endsWith('!') || response.endsWith('?')) {
            return response;
        }
        
        // Find last complete sentence
        const lastPeriod = response.lastIndexOf('.');
        const lastExclamation = response.lastIndexOf('!');
        const lastQuestion = response.lastIndexOf('?');
        
        const lastPunctuation = Math.max(lastPeriod, lastExclamation, lastQuestion);
        if (lastPunctuation > response.length * 0.6) {
            response = response.substring(0, lastPunctuation + 1);
        }
        
        return response;
    }

    isGenericResponse(response) {
        const genericPhrases = [
            'I can help',
            'I understand',
            'Thank you',
            'undefined',
            'null',
            'error'
        ];
        
        return genericPhrases.some(phrase => 
            response.toLowerCase().includes(phrase.toLowerCase())
        ) && response.length < 30;
    }

    getRuleBasedResponse(userMessage) {
        const message = userMessage.toLowerCase();
        
        // Banking & Connection Issues
        if (message.includes('bank') || message.includes('connect') || message.includes('link')) {
            return "To connect your bank: Go to **Banking** → **Connect Account** → Select your bank → Enter online banking credentials. Ensure your bank supports Open Banking or use manual CSV upload if needed.";
        }
        
        // Invoicing
        if (message.includes('invoice') || message.includes('bill') || message.includes('customer')) {
            return "Create invoices: **Sales** → **Invoices** → **Create Invoice**. Add customer details, line items, tax rates, and payment terms. You can email directly from QuickBooks or print/download PDF.";
        }
        
        // Expenses & Receipts
        if (message.includes('expense') || message.includes('receipt') || message.includes('cost')) {
            return "Record expenses: **Expenses** → **Add Expense** → Enter vendor, amount, category, and upload receipt photo. Use the mobile app to capture receipts instantly with automatic data extraction.";
        }
        
        // Payroll
        if (message.includes('payroll') || message.includes('employee') || message.includes('salary') || message.includes('wage')) {
            return "Set up payroll: **Payroll** → **Get Started** → Add employees, set pay rates, and configure tax settings. Requires QuickBooks Payroll subscription ($45/month + $6/employee).";
        }
        
        // Reports & Analytics
        if (message.includes('report') || message.includes('profit') || message.includes('loss') || message.includes('balance')) {
            return "View financial reports: **Reports** → **Standard**. Key reports: **Profit & Loss**, **Balance Sheet**, **Cash Flow Statement**. Customize date ranges and add filters for detailed analysis.";
        }
        
        // Tax & Compliance
        if (message.includes('tax') || message.includes('1099') || message.includes('w2') || message.includes('irs')) {
            return "Tax preparation: **Taxes** → **Forms** → Generate 1099s, W2s, and other tax forms. Export data to TurboTax or share with your accountant. Set up sales tax tracking under **Taxes** → **Sales Tax**.";
        }
        
        // Inventory
        if (message.includes('inventory') || message.includes('stock') || message.includes('product')) {
            return "Manage inventory: **Sales** → **Products and Services** → **New** → **Inventory**. Track quantities, set reorder points, and QuickBooks will update stock levels automatically with sales.";
        }
        
        // Account Setup
        if (message.includes('setup') || message.includes('start') || message.includes('begin')) {
            return "Getting started: Complete the **Setup Wizard** → Add business info → Connect bank accounts → Import existing data. Use the **QuickBooks Setup** guide under **Help** for step-by-step assistance.";
        }
        
        // Error & Troubleshooting
        if (message.includes('error') || message.includes('problem') || message.includes('issue') || message.includes('not working')) {
            return "Common fixes: **Clear browser cache** → **Disable browser extensions** → **Try incognito mode** → **Check internet connection**. For persistent issues, contact QuickBooks Support at 1-800-446-8848.";
        }
        
        // Mobile App
        if (message.includes('mobile') || message.includes('app') || message.includes('phone')) {
            return "QuickBooks Mobile: Download from **App Store** or **Google Play** → Sign in with same credentials → Capture receipts, send invoices, accept payments, and view reports on-the-go.";
        }
        
        // Default helpful response
        return "I'm here to help with QuickBooks Online! I can assist with:\n\n💰 **Banking** - Connect accounts, categorize transactions\n📄 **Invoicing** - Create and send professional invoices\n📊 **Reports** - Profit & Loss, Balance Sheet, Cash Flow\n💼 **Expenses** - Track costs and upload receipts\n👥 **Payroll** - Manage employees and payments\n📱 **Mobile** - Use QuickBooks on your phone\n\nWhat specific area would you like help with?";
    }

    getStatus() {
        if (this.isLoading) return { status: 'loading', message: 'Loading AI model...' };
        if (this.isReady) return { status: 'ready', message: 'AI ready' };
        return { status: 'offline', message: 'AI not loaded' };
    }
}

// Export for use in main app
window.AIBrain = AIBrain;
