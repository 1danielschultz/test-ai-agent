"""
Custom inference script for SageMaker endpoint
Integrates RAG context with language model for QuickBooks troubleshooting
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import requests
import os
from typing import Dict, List, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

class QuickBooksAIPredictor:
    """Custom predictor class for SageMaker inference"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.generator = None
        self.rag_endpoint = os.environ.get('RAG_ENDPOINT', 'http://localhost:5000')
        self.max_length = 512
        self.temperature = 0.7
        
    def model_fn(self, model_dir: str):
        """Load model for inference"""
        try:
            model_id = os.environ.get('HF_MODEL_ID', 'microsoft/DialoGPT-medium')
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )
            
            # Set pad token if not exists
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Create generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info(f"Model {model_id} loaded successfully")
            return self
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def input_fn(self, request_body: str, content_type: str = 'application/json') -> Dict[str, Any]:
        """Parse input request"""
        try:
            if content_type == 'application/json':
                input_data = json.loads(request_body)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
            
            return input_data
            
        except Exception as e:
            logger.error(f"Error parsing input: {e}")
            raise
    
    def get_rag_context(self, query: str) -> str:
        """Retrieve relevant context from RAG system"""
        try:
            response = requests.post(
                f"{self.rag_endpoint}/context",
                json={'query': query, 'max_tokens': 1500},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('context', '')
            else:
                logger.warning(f"RAG service error: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.warning(f"Could not retrieve RAG context: {e}")
            return ""
    
    def create_prompt(self, user_message: str, context: str = "") -> str:
        """Create a comprehensive prompt for the model"""
        
        system_prompt = """You are a QuickBooks Online expert assistant. Your role is to help users troubleshoot QuickBooks issues, answer questions about features, and provide step-by-step guidance.

Guidelines:
- Be helpful, accurate, and professional
- Provide specific, actionable steps when possible
- If you're not certain, recommend contacting QuickBooks support
- Use the provided context to give relevant, detailed answers
- Keep responses concise but comprehensive
- Include warnings about important considerations (like data backup)

"""
        
        if context.strip():
            formatted_context = f"Relevant QuickBooks Documentation:\n{context}\n\n"
        else:
            formatted_context = ""
        
        prompt = f"{system_prompt}{formatted_context}User Question: {user_message}\n\nAssistant Response:"
        
        return prompt
    
    def predict_fn(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate prediction/response"""
        try:
            user_message = input_data.get('message', '')
            include_rag = input_data.get('use_rag', True)
            max_length = input_data.get('max_length', self.max_length)
            temperature = input_data.get('temperature', self.temperature)
            
            if not user_message:
                return {'error': 'No message provided'}
            
            # Get RAG context if enabled
            context = ""
            if include_rag:
                context = self.get_rag_context(user_message)
            
            # Create prompt
            prompt = self.create_prompt(user_message, context)
            
            # Generate response
            response = self.generator(
                prompt,
                max_length=len(prompt.split()) + max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                num_return_sequences=1,
                truncation=True
            )
            
            # Extract generated text (remove prompt)
            generated_text = response[0]['generated_text']
            
            # Find where the assistant response starts
            assistant_marker = "Assistant Response:"
            if assistant_marker in generated_text:
                response_text = generated_text.split(assistant_marker, 1)[1].strip()
            else:
                response_text = generated_text[len(prompt):].strip()
            
            # Clean up response
            response_text = self.clean_response(response_text)
            
            return {
                'response': response_text,
                'context_used': bool(context),
                'context_length': len(context) if context else 0,
                'model_info': {
                    'model_id': os.environ.get('HF_MODEL_ID', 'microsoft/DialoGPT-medium'),
                    'temperature': temperature,
                    'max_length': max_length
                }
            }
            
        except Exception as e:
            logger.error(f"Error in prediction: {e}")
            return {
                'error': str(e),
                'response': 'I apologize, but I encountered an error processing your request. Please try again or contact QuickBooks support for assistance.'
            }
    
    def clean_response(self, text: str) -> str:
        """Clean and format the generated response"""
        # Remove common artifacts
        text = text.strip()
        
        # Stop at common ending markers
        endings = ['\nUser:', '\nHuman:', '\nQ:', '\nQuestion:']
        for ending in endings:
            if ending in text:
                text = text.split(ending)[0]
        
        # Limit response length
        sentences = text.split('. ')
        if len(sentences) > 10:  # Limit to reasonable length
            text = '. '.join(sentences[:10]) + '.'
        
        return text.strip()
    
    def output_fn(self, prediction: Dict[str, Any], accept: str = 'application/json') -> str:
        """Format output response"""
        try:
            if accept == 'application/json':
                return json.dumps(prediction)
            else:
                return str(prediction.get('response', ''))
        except Exception as e:
            logger.error(f"Error formatting output: {e}")
            return json.dumps({'error': 'Error formatting response'})

# Global predictor instance
predictor = QuickBooksAIPredictor()

def model_fn(model_dir):
    """SageMaker model loading function"""
    return predictor.model_fn(model_dir)

def input_fn(request_body, content_type='application/json'):
    """SageMaker input parsing function"""
    return predictor.input_fn(request_body, content_type)

def predict_fn(input_data, model):
    """SageMaker prediction function"""
    return predictor.predict_fn(input_data)

def output_fn(prediction, accept='application/json'):
    """SageMaker output formatting function"""
    return predictor.output_fn(prediction, accept)
