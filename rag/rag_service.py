"""
RAG Service for QuickBooks AI Agent
Provides REST API interface for the knowledge base
"""

import json
import os
from typing import Dict, List, Any
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from knowledge_base import QuickBooksRAG, create_quickbooks_knowledge_base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Initialize RAG system
rag_system = None

def initialize_rag():
    """Initialize the RAG system with QuickBooks knowledge base"""
    global rag_system
    try:
        rag_system = QuickBooksRAG(index_path="vector_store")
        
        # If no existing knowledge base, create one
        if len(rag_system.documents) == 0:
            logger.info("Creating initial knowledge base...")
            documents = create_quickbooks_knowledge_base()
            rag_system.add_documents(documents)
            logger.info(f"Added {len(documents)} documents to knowledge base")
        else:
            logger.info(f"Loaded existing knowledge base with {len(rag_system.documents)} documents")
            
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        raise

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'QuickBooks RAG Service',
        'documents': len(rag_system.documents) if rag_system else 0
    })

@app.route('/search', methods=['POST'])
def search_knowledge_base():
    """Search the knowledge base for relevant documents"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        min_score = data.get('min_score', 0.5)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        results = rag_system.search(query, top_k=top_k, min_score=min_score)
        
        # Format results for API response
        formatted_results = []
        for result in results:
            doc = result['document']
            formatted_results.append({
                'id': doc.id,
                'title': doc.title,
                'content': doc.content,
                'category': doc.category,
                'keywords': doc.keywords,
                'score': result['score'],
                'relevance': result['relevance'],
                'source_url': doc.source_url
            })
        
        return jsonify({
            'query': query,
            'results': formatted_results,
            'total_results': len(formatted_results)
        })
        
    except Exception as e:
        logger.error(f"Error in search: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/context', methods=['POST'])
def get_context():
    """Get formatted context for RAG prompting"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        max_tokens = data.get('max_tokens', 2000)
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        context = rag_system.get_context(query, max_tokens=max_tokens)
        
        return jsonify({
            'query': query,
            'context': context,
            'context_length': len(context)
        })
        
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get knowledge base statistics"""
    try:
        stats = rag_system.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/categories', methods=['GET'])
def get_categories():
    """Get all document categories"""
    try:
        categories = set()
        for doc in rag_system.documents:
            categories.add(doc.category)
        
        return jsonify({
            'categories': list(categories),
            'total_categories': len(categories)
        })
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/documents', methods=['GET'])
def list_documents():
    """List all documents in the knowledge base"""
    try:
        category_filter = request.args.get('category')
        
        documents = []
        for doc in rag_system.documents:
            if category_filter and doc.category != category_filter:
                continue
                
            documents.append({
                'id': doc.id,
                'title': doc.title,
                'category': doc.category,
                'keywords': doc.keywords,
                'source_url': doc.source_url,
                'content_length': len(doc.content)
            })
        
        return jsonify({
            'documents': documents,
            'total_documents': len(documents),
            'filter': category_filter
        })
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize RAG system
    initialize_rag()
    
    # Run the Flask app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
