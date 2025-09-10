# QuickBooks AI Assistant

A modern, privacy-first AI assistant for QuickBooks Online that runs entirely in your browser using local machine learning inference.

## ✨ Features

- **🧠 Local AI Brain**: SmolLM2-135M-Instruct model (98MB) running entirely in-browser
- **🔒 Privacy First**: No data sent to external servers, everything runs locally
- **💰 Zero Cost**: No API keys, no cloud services, no monthly fees
- **🎨 Modern UI**: Beautiful glassmorphism design with responsive interface
- **📱 Mobile Friendly**: Works on desktop, tablet, and mobile devices
- **⚡ Fast**: WebAssembly-powered inference with 4096 token context window

## 🚀 Live Demo

Visit: **https://1danielschultz.github.io/test-ai-agent/**

## 🛠️ Technology Stack

- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **AI Model**: SmolLM2-135M-Instruct (Quantized GGUF)
- **ML Runtime**: Wllama (WebAssembly binding for llama.cpp)
- **Hosting**: GitHub Pages
- **UI Framework**: Custom glassmorphism design

## 🧠 AI Capabilities

The assistant can help with:

- **💰 Banking**: Account connections, transaction categorization
- **📄 Invoicing**: Professional invoice creation, recurring billing
- **📊 Reports**: P&L, Balance Sheet, Cash Flow analysis
- **💼 Expenses**: Receipt capture, expense tracking, deductions
- **👥 Payroll**: Employee management, tax compliance
- **📦 Inventory**: Stock tracking, reorder alerts
- **🔧 Setup & Support**: Configuration, troubleshooting

## 📁 Project Structure

```
├── index.html          # Main application interface
├── app.js             # Core application logic
├── smol-brain.js      # AI model integration (SmolLM2)
├── styles.css         # Glassmorphism UI styling
├── models/           # Local AI model storage
│   └── SmolLM2-135M-Instruct.Q4_1.gguf
├── package.json      # Project metadata
└── .nojekyll        # GitHub Pages configuration
```

## 🔧 Technical Details

### AI Model
- **Model**: SmolLM2-135M-Instruct (HuggingFace)
- **Size**: 98MB (Q4_1 quantization)
- **Context**: 4096 tokens for extended conversations
- **Runtime**: Wllama v2.3.5 with WebAssembly
- **Tokenizer**: SmolLM pre-tokenizer (supported since llama.cpp July 2024)

### Performance
- **Loading**: ~10-30 seconds (depending on connection)
- **Inference**: Real-time responses
- **Memory**: ~200-400MB browser usage
- **Compatibility**: Modern browsers with WebAssembly support

## 🚀 Development

### Local Development

1. Clone the repository:
```bash
git clone https://github.com/1danielschultz/test-ai-agent.git
cd test-ai-agent
```

2. Serve locally (Python example):
```bash
python -m http.server 8000
```

3. Open: `http://localhost:8000`

### Deployment

The project is configured for GitHub Pages:
- Push to `main` branch
- Enable GitHub Pages in repository settings
- Site available at: `https://username.github.io/repository-name/`

## 🔒 Privacy & Security

- **Local Processing**: All AI inference happens in your browser
- **No Data Collection**: No user data sent to external servers
- **No Tracking**: No analytics or monitoring
- **Offline Capable**: Works without internet after initial load

## 📝 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- **SmolLM2**: HuggingFace Team for the excellent small language model
- **Wllama**: ngxson for the WebAssembly llama.cpp binding
- **llama.cpp**: ggerganov and contributors for the inference engine

## 📧 Support

For issues or questions, please open a GitHub issue.

---

**Built with ❤️ for privacy-conscious QuickBooks users**
