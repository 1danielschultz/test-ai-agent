// QuickBooks AI Assistant - Frontend Application
class QuickBooksAI {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.setupAutoResize();
        this.loadSettings();
        
        // State
        this.isLoading = false;
        this.isInitialized = false;
        
        // Initialize AI after a brief delay to show loading screen
        setTimeout(() => this.initializeBrowserAI(), 500);
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
        
        // Loading elements
        this.initialLoading = document.getElementById('initialLoading');
        this.loadingText = document.getElementById('loadingText');
        this.loadingProgress = document.getElementById('loadingProgress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
    }

    async initializeBrowserAI() {
        try {
            this.updateLoadingStatus('Loading AI model...', 10);
            
            // Try to initialize SmolLM2-135M-Instruct first
            this.aiBrain = new SmolLMBrain();
            
            this.updateLoadingStatus('Initializing SmolLM2-135M-Instruct...', 30);
            
            // Set up progress callback for model loading
            const originalInit = this.aiBrain.initialize.bind(this.aiBrain);
            this.aiBrain.initialize = async () => {
                return new Promise((resolve) => {
                    // Show progress bar when model starts loading
                    this.showLoadingProgress();
                    
                    // Override the progress callback in loadModel
                    const originalLoadModel = this.aiBrain.loadModel.bind(this.aiBrain);
                    this.aiBrain.loadModel = async function() {
                        console.log('📥 Loading local SmolLM2 model (98MB)...');
                        try {
                            if (!this.llamaCpp || !this.wasmConfig) {
                                console.warn('🔄 Wllama not available, will use rule-based fallback');
                                return;
                            }
                            
                            this.model = new this.llamaCpp(this.wasmConfig, {
                                n_threads: Math.min(navigator.hardwareConcurrency || 4, 8),
                                n_ctx: 4096
                            });
                            
                            await this.model.loadModelFromUrl(this.modelPath, {
                                progressCallback: ({ loaded, total }) => {
                                    const progress = Math.round((loaded / total) * 100);
                                    const finalProgress = 40 + (progress * 0.5); // Map 0-100% to 40-90%
                                    window.qbAI.updateLoadingProgress(finalProgress, `Loading model: ${progress}%`);
                                },
                                parallelDownloads: 3,
                                allowOffline: true
                            });
                            
                            console.log('✅ Model initialized successfully!');
                        } catch (error) {
                            console.warn('Failed to load with Wllama, will use rule-based responses:', error);
                            this.model = null;
                        }
                    };
                    
                    originalInit().then(resolve);
                });
            };
            
            const success = await this.aiBrain.initialize();
            
            if (success) {
                const modelInfo = this.aiBrain.getModelInfo();
                this.updateLoadingStatus('AI ready! Starting assistant...', 95);
                console.log(`✅ SmolLM2 ready! Running ${modelInfo.params} model`);
            } else {
                // Fallback to rule-based system
                this.updateLoadingStatus('Loading enhanced assistant...', 80);
                console.log('Falling back to rule-based responses');
                this.aiBrain = new FallbackBrain();
                await this.aiBrain.initialize();
            }
            
            // Final completion
            this.updateLoadingStatus('Ready!', 100);
            setTimeout(() => this.hideInitialLoading(), 500);
            
        } catch (error) {
            console.error('Failed to initialize SmolLM2:', error);
            
            // Initialize fallback system
            this.updateLoadingStatus('Loading backup system...', 70);
            this.aiBrain = new FallbackBrain();
            await this.aiBrain.initialize();
            
            this.updateLoadingStatus('Ready!', 100);
            setTimeout(() => this.hideInitialLoading(), 500);
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

    // Loading screen methods
    updateLoadingStatus(text, progress = null) {
        if (this.loadingText) {
            this.loadingText.textContent = text;
        }
        if (progress !== null) {
            this.updateLoadingProgress(progress);
        }
    }
    
    showLoadingProgress() {
        if (this.loadingProgress) {
            this.loadingProgress.classList.add('visible');
        }
    }
    
    updateLoadingProgress(progress, text = null) {
        if (this.progressFill) {
            this.progressFill.style.width = `${Math.min(progress, 100)}%`;
        }
        if (this.progressText) {
            this.progressText.textContent = `${Math.round(progress)}%`;
        }
        if (text && this.loadingText) {
            this.loadingText.textContent = text;
        }
    }
    
    hideInitialLoading() {
        this.isInitialized = true;
        if (this.initialLoading) {
            this.initialLoading.classList.add('hidden');
            // Remove from DOM after transition
            setTimeout(() => {
                if (this.initialLoading && this.initialLoading.parentNode) {
                    this.initialLoading.parentNode.removeChild(this.initialLoading);
                }
            }, 500);
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
