# QuickBooks AI Agent

A comprehensive AI-powered troubleshooting assistant for QuickBooks Online, featuring:

- 🤖 AI-powered chat interface hosted on GitHub Pages
- ☁️ AWS SageMaker backend for scalable AI inference
- 📚 RAG (Retrieval-Augmented Generation) for QuickBooks knowledge base
- 🔒 Secure API integration with authentication
- 🚀 Automated deployment via GitHub Actions

## Architecture

```
Frontend (GitHub Pages) → API Gateway → Lambda → SageMaker Endpoint
                                     ↓
                               Vector Database (RAG)
```

## Features

- **Interactive Chat Interface**: Modern, responsive web UI for user interactions
- **QuickBooks Expertise**: Specialized knowledge base for QB Online troubleshooting
- **Real-time Responses**: Fast AI inference via AWS SageMaker
- **Contextual Help**: RAG system provides relevant documentation and solutions
- **Secure Access**: API authentication and rate limiting

## Quick Start

1. Clone this repository
2. Configure AWS credentials and SageMaker endpoint
3. Deploy to GitHub Pages
4. Start troubleshooting QuickBooks issues!

## Setup Instructions

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed setup instructions.

## Project Structure

```
├── frontend/           # GitHub Pages web application
├── backend/           # AWS Lambda functions and API
├── sagemaker/         # SageMaker model deployment scripts
├── rag/              # RAG knowledge base and vector store
├── docs/             # Documentation
├── .github/          # GitHub Actions workflows
└── scripts/          # Deployment and utility scripts
```

## Contributing

This is a test project for demonstrating AI agent capabilities. Feel free to extend and modify as needed.

## License

MIT License - see LICENSE file for details.
