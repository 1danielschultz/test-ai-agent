// QuickBooks AI Assistant - Frontend Application
class QuickBooksAI {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
        this.initializeBrowserAI();
        
        // State
        this.isLoading = false;
    }

    initializeElements() {
        // Chat elements
        this.chatMessages = document.getElementById('chatMessages');
        this.messageInput = document.getElementById('messageInput');
        this.sendBtn = document.getElementById('sendBtn');
        this.attachBtn = document.getElementById('attachBtn');
        this.clearChatBtn = document.getElementById('clearChat');
        
        // UI elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettingsBtn = document.getElementById('closeSettings');
        this.saveSettingsBtn = document.getElementById('saveSettings');
        
        // Settings inputs
        this.apiEndpointInput = document.getElementById('apiEndpoint');
        this.apiKeyInput = document.getElementById('apiKey');
        this.darkModeToggle = document.getElementById('darkMode');
        
        // Quick action buttons
        this.quickActionBtns = document.querySelectorAll('.quick-action-btn');
        this.recentTopics = document.getElementById('recentTopics');
    }

    async initializeBrowserAI() {
        try {
            // Initialize browser-based AI
            this.aiBrain = new AIBrain();
            
            // Show loading message
            this.addMessage("🧠 Initializing AI model... This may take 1-2 minutes on first visit.", false);
            
            // Start loading the model
            const success = await this.aiBrain.initialize();
            
            if (success) {
                this.addMessage("✅ AI model ready! I can now provide intelligent QuickBooks assistance.", false);
            } else {
                this.addMessage("⚠️ AI model couldn't load, but I can still help with rule-based responses.", false);
            }
            
        } catch (error) {
            console.error('Failed to initialize AI:', error);
            this.addMessage("ℹ️ Running in basic mode. I can help with common QuickBooks questions.", false);
        }
    }

    bindEvents() {
        // Send message events
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.messageInput.addEventListener('keydown', (e) => this.handleKeyDown(e));
        
        // Quick action buttons
        this.quickActionBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const message = btn.getAttribute('data-message');
                this.messageInput.value = message;
                this.sendMessage();
            });
        });
        
        // UI controls
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.settingsBtn.addEventListener('click', () => this.showSettings());
        this.closeSettingsBtn.addEventListener('click', () => this.hideSettings());
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        
        // Settings
        this.darkModeToggle.addEventListener('change', () => this.toggleDarkMode());
        
        // Attach button (placeholder)
        this.attachBtn.addEventListener('click', () => this.handleAttachment());
        
        // Modal close on backdrop click
        this.settingsModal.addEventListener('click', (e) => {
            if (e.target === this.settingsModal) {
                this.hideSettings();
            }
        });
    }

    setupAutoResize() {
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
        });
    }

    handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Clear input and add user message
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.addMessage(message, 'user');
        
        // Show loading
        this.setLoading(true);
        
        try {
            // Send to AI backend
            const response = await this.callAI(message);
            this.addMessage(response, 'bot');
            this.addToRecentTopics(message);
        } catch (error) {
            console.error('Error calling AI:', error);
            this.addMessage(
                'I apologize, but I\'m having trouble connecting to the AI service right now. Please check your settings and try again. If the problem persists, you can visit the QuickBooks support resources in the sidebar.',
                'bot',
                true
            );
        } finally {
            this.setLoading(false);
        }
    }

    async callAI(message) {
        // Use browser-based AI if available
        if (this.aiBrain) {
            const result = await this.aiBrain.generateResponse(message);
            return result.message;
        }

        // Fallback if no AI is available
        return 'AI is not currently available. Please try refreshing the page or check your internet connection.';
    }

    getContext() {
        // Return recent chat history for context
        return [];
    }

    addMessage(content, type, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.innerHTML = type === 'user' 
            ? '<i class="fas fa-user"></i>' 
            : '<i class="fas fa-robot"></i>';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        if (isError) {
            messageText.style.borderLeft = '4px solid var(--error-color)';
        }
        
        // Format content (basic markdown support)
        messageText.innerHTML = this.formatMessage(content);
        
        messageContent.appendChild(messageText);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        
        // Note: chatMessages is now a DOM element, not an array
    }

    formatMessage(content) {
        // Basic markdown formatting
        return content
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>')
            .replace(/(?:https?:\/\/)[\w\-._~:/?#[\]@!$&'()*+,;=%]+/g, '<a href="$&" target="_blank">$&</a>');
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            // Keep only the welcome message
            const welcomeMessage = this.chatMessages.querySelector('.message.bot-message');
            this.chatMessages.innerHTML = '';
            if (welcomeMessage) {
                this.chatMessages.appendChild(welcomeMessage.cloneNode(true));
            }
            // Chat history cleared
        }
    }

    addToRecentTopics(message) {
        // Extract topic from message (simplified)
        const topic = message.length > 50 ? message.substring(0, 47) + '...' : message;
        
        const topicItem = document.createElement('div');
        topicItem.className = 'topic-item';
        topicItem.innerHTML = `
            <i class="fas fa-clock"></i>
            <span>${this.escapeHtml(topic)}</span>
        `;
        
        topicItem.addEventListener('click', () => {
            this.messageInput.value = message;
            this.messageInput.focus();
        });
        
        // Add to top of recent topics
        this.recentTopics.insertBefore(topicItem, this.recentTopics.firstChild);
        
        // Keep only 5 recent topics
        while (this.recentTopics.children.length > 5) {
            this.recentTopics.removeChild(this.recentTopics.lastChild);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.sendBtn.disabled = loading;
        this.messageInput.disabled = loading;
        
        if (loading) {
            this.loadingOverlay.style.display = 'flex';
        } else {
            this.loadingOverlay.style.display = 'none';
        }
    }

    showSettings() {
        this.settingsModal.style.display = 'flex';
        this.apiEndpointInput.value = this.apiEndpoint;
        this.apiKeyInput.value = this.apiKey;
    }

    hideSettings() {
        this.settingsModal.style.display = 'none';
    }

    saveSettings() {
        this.apiEndpoint = this.apiEndpointInput.value.trim();
        this.apiKey = this.apiKeyInput.value.trim();
        
        // Save to localStorage
        localStorage.setItem('qb-ai-settings', JSON.stringify({
            apiEndpoint: this.apiEndpoint,
            apiKey: this.apiKey,
            darkMode: this.darkModeToggle.checked
        }));
        
        this.hideSettings();
        
        // Show confirmation
        this.addMessage('Settings saved successfully!', 'bot');
    }

    loadSettings() {
        const settings = localStorage.getItem('qb-ai-settings');
        if (settings) {
            try {
                const parsed = JSON.parse(settings);
                this.apiEndpoint = parsed.apiEndpoint || this.apiEndpoint;
                this.apiKey = parsed.apiKey || '';
                
                if (parsed.darkMode) {
                    this.darkModeToggle.checked = true;
                    this.toggleDarkMode();
                }
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        }
    }

    toggleDarkMode() {
        if (this.darkModeToggle.checked) {
            document.documentElement.setAttribute('data-theme', 'dark');
        } else {
            document.documentElement.removeAttribute('data-theme');
        }
    }

    handleAttachment() {
        // Placeholder for file attachment functionality
        alert('File attachment feature coming soon! For now, you can describe your QuickBooks screenshots or error messages in text.');
    }

    // Utility method to simulate AI responses for demo purposes
    async simulateResponse(message) {
        // This is a fallback for demo purposes when API is not configured
        const responses = {
            'bank': 'To connect your bank account to QuickBooks Online:\n\n1. Go to Banking > Overview\n2. Click "Connect account"\n3. Search for your bank\n4. Enter your online banking credentials\n5. Select the accounts to connect\n\nIf you\'re having trouble, make sure your bank supports QuickBooks integration and your credentials are correct.',
            
            'sync': 'Bank sync errors can be resolved by:\n\n1. Go to Banking > Overview\n2. Click the gear icon next to your bank account\n3. Select "Update"\n4. Re-enter your banking credentials if prompted\n5. Wait for the sync to complete\n\nIf the error persists, try disconnecting and reconnecting your bank account.',
            
            'report': 'To generate a Profit and Loss report:\n\n1. Go to Reports in the left menu\n2. Search for "Profit and Loss"\n3. Select "Profit and Loss" report\n4. Choose your date range\n5. Click "Display" to generate\n6. You can customize, export, or save the report\n\nThe P&L shows your income and expenses for the selected period.',
            
            'payroll': 'Setting up payroll in QuickBooks Online:\n\n1. Go to Payroll > Overview\n2. Click "Get started" if not already set up\n3. Add your employees and their details\n4. Set up pay schedules and rates\n5. Configure tax settings\n6. Run your first payroll\n\nNote: Payroll is a premium feature and requires a subscription upgrade.'
        };

        // Simple keyword matching for demo
        const lowerMessage = message.toLowerCase();
        for (const [keyword, response] of Object.entries(responses)) {
            if (lowerMessage.includes(keyword)) {
                return response;
            }
        }

        return 'I understand you need help with QuickBooks Online. While I\'m designed to provide comprehensive assistance, I need to be connected to the AI service to give you the most accurate and detailed help. Please configure the API settings to unlock my full capabilities.\n\nIn the meantime, you can check the helpful resources in the sidebar or describe your specific issue in more detail.';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.qbAI = new QuickBooksAI();
    
    // Add some demo functionality for testing
    console.log('QuickBooks AI Assistant loaded successfully!');
    console.log('Configure API settings to connect to AWS SageMaker backend.');
});
