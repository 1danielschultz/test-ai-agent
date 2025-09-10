"""
AWS SageMaker Deployment Script for QuickBooks AI Agent
Deploys a Hugging Face model for text generation with RAG integration
"""

import boto3
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import os
from pathlib import Path

class SageMakerDeployer:
    """Handles SageMaker model deployment and endpoint management"""
    
    def __init__(self, region_name: str = 'us-east-1', role_name: str = 'SageMakerExecutionRole'):
        self.region_name = region_name
        self.role_name = role_name
        self.sagemaker = boto3.client('sagemaker', region_name=region_name)
        self.sts = boto3.client('sts', region_name=region_name)
        self.iam = boto3.client('iam', region_name=region_name)
        
        # Get account ID for role ARN
        self.account_id = self.sts.get_caller_identity()['Account']
        self.execution_role_arn = f"arn:aws:iam::{self.account_id}:role/{role_name}"
        
    def create_execution_role(self) -> str:
        """Create SageMaker execution role if it doesn't exist"""
        try:
            # Check if role exists
            self.iam.get_role(RoleName=self.role_name)
            print(f"Role {self.role_name} already exists")
            return self.execution_role_arn
        except self.iam.exceptions.NoSuchEntityException:
            pass
        
        # Create role
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "sagemaker.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            self.iam.create_role(
                RoleName=self.role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description="SageMaker execution role for QuickBooks AI Agent"
            )
            
            # Attach necessary policies
            policies = [
                "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess",
                "arn:aws:iam::aws:policy/AmazonS3FullAccess",
                "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(
                    RoleName=self.role_name,
                    PolicyArn=policy
                )
            
            print(f"Created role {self.role_name} with necessary policies")
            return self.execution_role_arn
            
        except Exception as e:
            print(f"Error creating role: {e}")
            raise
    
    def create_model(self, model_name: str, model_config: Dict[str, Any]) -> str:
        """Create SageMaker model"""
        try:
            response = self.sagemaker.create_model(
                ModelName=model_name,
                PrimaryContainer={
                    'Image': model_config['image'],
                    'ModelDataUrl': model_config.get('model_data_url'),
                    'Environment': model_config.get('environment', {})
                },
                ExecutionRoleArn=self.execution_role_arn,
                Tags=[
                    {'Key': 'Project', 'Value': 'QuickBooksAI'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            print(f"Created model: {model_name}")
            return response['ModelArn']
            
        except Exception as e:
            print(f"Error creating model: {e}")
            raise
    
    def create_endpoint_config(self, config_name: str, model_name: str, 
                             instance_type: str = 'ml.t2.medium') -> str:
        """Create SageMaker endpoint configuration"""
        try:
            response = self.sagemaker.create_endpoint_config(
                EndpointConfigName=config_name,
                ProductionVariants=[
                    {
                        'VariantName': 'Primary',
                        'ModelName': model_name,
                        'InitialInstanceCount': 1,
                        'InstanceType': instance_type,
                        'InitialVariantWeight': 1.0
                    }
                ],
                Tags=[
                    {'Key': 'Project', 'Value': 'QuickBooksAI'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            print(f"Created endpoint configuration: {config_name}")
            return response['EndpointConfigArn']
            
        except Exception as e:
            print(f"Error creating endpoint config: {e}")
            raise
    
    def create_endpoint(self, endpoint_name: str, config_name: str) -> str:
        """Create SageMaker endpoint"""
        try:
            response = self.sagemaker.create_endpoint(
                EndpointName=endpoint_name,
                EndpointConfigName=config_name,
                Tags=[
                    {'Key': 'Project', 'Value': 'QuickBooksAI'},
                    {'Key': 'Environment', 'Value': 'Production'}
                ]
            )
            
            print(f"Creating endpoint: {endpoint_name}")
            return response['EndpointArn']
            
        except Exception as e:
            print(f"Error creating endpoint: {e}")
            raise
    
    def wait_for_endpoint(self, endpoint_name: str, timeout: int = 1800) -> bool:
        """Wait for endpoint to be in service"""
        print(f"Waiting for endpoint {endpoint_name} to be in service...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.sagemaker.describe_endpoint(EndpointName=endpoint_name)
                status = response['EndpointStatus']
                
                if status == 'InService':
                    print(f"Endpoint {endpoint_name} is now in service!")
                    return True
                elif status in ['Failed', 'OutOfService']:
                    print(f"Endpoint {endpoint_name} failed: {response.get('FailureReason', 'Unknown error')}")
                    return False
                else:
                    print(f"Endpoint status: {status}")
                    time.sleep(30)
                    
            except Exception as e:
                print(f"Error checking endpoint status: {e}")
                time.sleep(30)
        
        print(f"Timeout waiting for endpoint {endpoint_name}")
        return False
    
    def deploy_huggingface_model(self, model_id: str = "microsoft/DialoGPT-medium", 
                                endpoint_name: Optional[str] = None) -> Dict[str, str]:
        """Deploy a Hugging Face model to SageMaker"""
        if endpoint_name is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            endpoint_name = f"quickbooks-ai-{timestamp}"
        
        model_name = f"{endpoint_name}-model"
        config_name = f"{endpoint_name}-config"
        
        # Hugging Face Deep Learning Container
        image_uri = f"763104351884.dkr.ecr.{self.region_name}.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-gpu-py39-cu117-ubuntu20.04"
        
        model_config = {
            'image': image_uri,
            'environment': {
                'HF_MODEL_ID': model_id,
                'HF_TASK': 'text-generation',
                'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
                'SAGEMAKER_REGION': self.region_name
            }
        }
        
        try:
            # Create execution role
            self.create_execution_role()
            
            # Create model
            model_arn = self.create_model(model_name, model_config)
            
            # Create endpoint configuration
            config_arn = self.create_endpoint_config(config_name, model_name, 'ml.g4dn.xlarge')
            
            # Create endpoint
            endpoint_arn = self.create_endpoint(endpoint_name, config_name)
            
            # Wait for endpoint to be ready
            if self.wait_for_endpoint(endpoint_name):
                return {
                    'endpoint_name': endpoint_name,
                    'endpoint_arn': endpoint_arn,
                    'model_name': model_name,
                    'config_name': config_name,
                    'status': 'InService'
                }
            else:
                return {
                    'endpoint_name': endpoint_name,
                    'status': 'Failed'
                }
                
        except Exception as e:
            print(f"Deployment failed: {e}")
            raise
    
    def delete_endpoint(self, endpoint_name: str) -> bool:
        """Delete SageMaker endpoint and associated resources"""
        try:
            # Get endpoint details
            response = self.sagemaker.describe_endpoint(EndpointName=endpoint_name)
            config_name = response['EndpointConfigName']
            
            # Get model name from config
            config_response = self.sagemaker.describe_endpoint_config(EndpointConfigName=config_name)
            model_name = config_response['ProductionVariants'][0]['ModelName']
            
            # Delete endpoint
            self.sagemaker.delete_endpoint(EndpointName=endpoint_name)
            print(f"Deleted endpoint: {endpoint_name}")
            
            # Delete endpoint configuration
            self.sagemaker.delete_endpoint_config(EndpointConfigName=config_name)
            print(f"Deleted endpoint config: {config_name}")
            
            # Delete model
            self.sagemaker.delete_model(ModelName=model_name)
            print(f"Deleted model: {model_name}")
            
            return True
            
        except Exception as e:
            print(f"Error deleting endpoint: {e}")
            return False
    
    def list_endpoints(self) -> list:
        """List all SageMaker endpoints"""
        try:
            response = self.sagemaker.list_endpoints(
                NameContains='quickbooks-ai',
                MaxResults=50
            )
            return response['Endpoints']
        except Exception as e:
            print(f"Error listing endpoints: {e}")
            return []

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy QuickBooks AI model to SageMaker')
    parser.add_argument('--model-id', default='microsoft/DialoGPT-medium', 
                       help='Hugging Face model ID to deploy')
    parser.add_argument('--endpoint-name', help='Custom endpoint name')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--action', choices=['deploy', 'delete', 'list'], default='deploy',
                       help='Action to perform')
    
    args = parser.parse_args()
    
    deployer = SageMakerDeployer(region_name=args.region)
    
    if args.action == 'deploy':
        print(f"Deploying model {args.model_id} to SageMaker...")
        result = deployer.deploy_huggingface_model(
            model_id=args.model_id,
            endpoint_name=args.endpoint_name
        )
        print(f"Deployment result: {json.dumps(result, indent=2)}")
        
    elif args.action == 'delete':
        if not args.endpoint_name:
            print("Endpoint name required for delete action")
            return
        
        success = deployer.delete_endpoint(args.endpoint_name)
        if success:
            print(f"Successfully deleted endpoint {args.endpoint_name}")
        else:
            print(f"Failed to delete endpoint {args.endpoint_name}")
    
    elif args.action == 'list':
        endpoints = deployer.list_endpoints()
        print(f"Found {len(endpoints)} QuickBooks AI endpoints:")
        for endpoint in endpoints:
            print(f"- {endpoint['EndpointName']}: {endpoint['EndpointStatus']}")

if __name__ == "__main__":
    main()
