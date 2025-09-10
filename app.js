// QuickBooks AI Assistant - Frontend Application
class QuickBooksAI {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.setupAutoResize();
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
        this.clearChatBtn = document.getElementById('clearChat');
        
        // UI elements
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.settingsBtn = document.getElementById('settingsBtn');
        this.settingsModal = document.getElementById('settingsModal');
        this.closeSettingsBtn = document.getElementById('closeSettings');
        this.saveSettingsBtn = document.getElementById('saveSettings');
        
        // Settings inputs
        this.darkModeToggle = document.getElementById('darkMode');
        
        // Quick action buttons
        this.quickActionBtns = document.querySelectorAll('.quick-action-btn');
        
        // Welcome section
        this.welcomeSection = document.querySelector('.welcome-section');
        this.hasStartedChat = false;
    }

    async initializeBrowserAI() {
        try {
            // Try to initialize SmolLM2-135M-Instruct first
            this.aiBrain = new SmolLMBrain();
            
            // Start loading the model silently
            const success = await this.aiBrain.initialize();
            
            if (success) {
                const modelInfo = this.aiBrain.getModelInfo();
                console.log(`✅ SmolLM2 ready! Running ${modelInfo.params} model`);
            } else {
                // Fallback to rule-based system
                console.log('Falling back to rule-based responses');
                this.aiBrain = new FallbackBrain();
                await this.aiBrain.initialize();
            }
            
        } catch (error) {
            console.error('Failed to initialize SmolLM2:', error);
            // Initialize fallback system
            this.aiBrain = new FallbackBrain();
            await this.aiBrain.initialize();
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
                this.startChat(message);
            });
        });
        
        // UI controls
        this.clearChatBtn.addEventListener('click', () => this.clearChat());
        this.settingsBtn.addEventListener('click', () => this.showSettings());
        this.closeSettingsBtn.addEventListener('click', () => this.hideSettings());
        this.saveSettingsBtn.addEventListener('click', () => this.saveSettings());
        
        // Settings
        this.darkModeToggle.addEventListener('change', () => this.toggleDarkMode());
        
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

    startChat(message) {
        this.messageInput.value = message || this.messageInput.value.trim();
        if (!this.hasStartedChat && this.welcomeSection) {
            this.welcomeSection.style.display = 'none';
            this.hasStartedChat = true;
        }
        this.sendMessage();
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message || this.isLoading) return;

        // Hide welcome section if first message
        if (!this.hasStartedChat && this.welcomeSection) {
            this.welcomeSection.style.display = 'none';
            this.hasStartedChat = true;
        }

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
        } catch (error) {
            console.error('Error calling AI:', error);
            this.addMessage(
                'I apologize, but I\'m having trouble right now. Please try again.',
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
            // Clear all messages and show welcome section again
            this.chatMessages.innerHTML = `
                <div class="welcome-section">
                    <div class="welcome-content">
                        <div class="welcome-header">
                            <i class="fas fa-robot"></i>
                            <h2>QuickBooks AI Assistant</h2>
                        </div>
                        <p class="welcome-subtitle">How can I help you with QuickBooks today?</p>
                        
                        <div class="quick-actions">
                            <button class="quick-action-btn" data-message="How do I connect my bank account to QuickBooks Online?">
                                <i class="fas fa-university"></i>
                                <span>Connect Bank Account</span>
                            </button>
                            <button class="quick-action-btn" data-message="How do I generate a profit and loss report?">
                                <i class="fas fa-chart-line"></i>
                                <span>Generate Reports</span>
                            </button>
                            <button class="quick-action-btn" data-message="I need help with payroll setup in QuickBooks Online.">
                                <i class="fas fa-users"></i>
                                <span>Payroll Setup</span>
                            </button>
                            <button class="quick-action-btn" data-message="I'm getting a sync error with my bank transactions. How do I fix this?">
                                <i class="fas fa-sync-alt"></i>
                                <span>Fix Sync Issues</span>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            // Re-bind quick action buttons
            this.welcomeSection = document.querySelector('.welcome-section');
            this.quickActionBtns = document.querySelectorAll('.quick-action-btn');
            this.quickActionBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    const message = btn.getAttribute('data-message');
                    this.startChat(message);
                });
            });
            
            this.hasStartedChat = false;
        }
    }

    // Removed recent topics functionality since sidebar is removed

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
    }

    hideSettings() {
        this.settingsModal.style.display = 'none';
    }

    saveSettings() {
        // Save to localStorage
        localStorage.setItem('qb-ai-settings', JSON.stringify({
            darkMode: this.darkModeToggle.checked
        }));
        
        this.hideSettings();
    }

    loadSettings() {
        const settings = localStorage.getItem('qb-ai-settings');
        if (settings) {
            try {
                const parsed = JSON.parse(settings);
                
                if (parsed.darkMode !== false) { // Default to dark mode
                    this.darkModeToggle.checked = true;
                }
            } catch (error) {
                console.error('Error loading settings:', error);
            }
        } else {
            // Default to dark mode for new users
            this.darkModeToggle.checked = true;
        }
    }

    toggleDarkMode() {
        if (this.darkModeToggle.checked) {
            document.body.classList.add('dark-mode');
        } else {
            document.body.classList.remove('dark-mode');
        }
    }

    // Removed attachment functionality
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.qbAI = new QuickBooksAI();
    
    // Add some demo functionality for testing
    console.log('QuickBooks AI Assistant loaded successfully!');
    console.log('Local SmolLM2 AI brain initialized for offline inference.');
});
