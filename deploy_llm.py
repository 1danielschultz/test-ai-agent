#!/usr/bin/env python3
"""
Simple SageMaker LLM Deployment Script
Deploys a Hugging Face model for QuickBooks AI Assistant
"""

import boto3
import json
import time
from datetime import datetime

class SimpleLLMDeployment:
    def __init__(self, region='us-east-1'):
        self.region = region
        self.sagemaker = boto3.client('sagemaker', region_name=region)
        self.iam = boto3.client('iam', region_name=region)
        
        # Configuration
        self.model_name = f"quickbooks-ai-{int(time.time())}"
        self.endpoint_config_name = f"quickbooks-ai-config-{int(time.time())}"
        self.endpoint_name = f"quickbooks-ai-endpoint-{int(time.time())}"
        
        # Use a lightweight, fast model for testing
        self.huggingface_model = {
            'model_id': 'microsoft/DialoGPT-small',  # Fast, lightweight
            'task': 'text-generation'
        }

    def create_sagemaker_role(self):
        """Create IAM role for SageMaker"""
        role_name = 'QuickBooksAI-SageMaker-Role'
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "sagemaker.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Try to create role
            response = self.iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description='Role for QuickBooks AI SageMaker endpoint'
            )
            role_arn = response['Role']['Arn']
            print(f"✅ Created IAM role: {role_arn}")
            
            # Attach required policies
            policies = [
                'arn:aws:iam::aws:policy/AmazonSageMakerFullAccess',
                'arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess'
            ]
            
            for policy in policies:
                self.iam.attach_role_policy(RoleName=role_name, PolicyArn=policy)
                print(f"✅ Attached policy: {policy}")
                
            # Wait for role propagation
            print("⏳ Waiting for IAM role to propagate...")
            time.sleep(10)
            
        except self.iam.exceptions.EntityAlreadyExistsException:
            # Role already exists
            role_arn = f"arn:aws:iam::{boto3.client('sts').get_caller_identity()['Account']}:role/{role_name}"
            print(f"✅ Using existing IAM role: {role_arn}")
        
        return role_arn

    def create_model(self, role_arn):
        """Create SageMaker model"""
        
        # Hugging Face model configuration
        model_data = {
            'Image': '763104351884.dkr.ecr.us-east-1.amazonaws.com/huggingface-pytorch-inference:1.13.1-transformers4.26.0-gpu-py39-cu117-ubuntu20.04',
            'Environment': {
                'HF_MODEL_ID': self.huggingface_model['model_id'],
                'HF_TASK': self.huggingface_model['task'],
                'SAGEMAKER_CONTAINER_LOG_LEVEL': '20',
                'SAGEMAKER_REGION': self.region
            }
        }
        
        try:
            response = self.sagemaker.create_model(
                ModelName=self.model_name,
                ExecutionRoleArn=role_arn,
                PrimaryContainer=model_data
            )
            print(f"✅ Created model: {self.model_name}")
            return response
            
        except Exception as e:
            print(f"❌ Error creating model: {e}")
            raise

    def create_endpoint_config(self):
        """Create endpoint configuration"""
        try:
            response = self.sagemaker.create_endpoint_config(
                EndpointConfigName=self.endpoint_config_name,
                ProductionVariants=[
                    {
                        'VariantName': 'AllTraffic',
                        'ModelName': self.model_name,
                        'InitialInstanceCount': 1,
                        'InstanceType': 'ml.g4dn.xlarge',  # GPU instance for better performance
                        'InitialVariantWeight': 1
                    }
                ]
            )
            print(f"✅ Created endpoint config: {self.endpoint_config_name}")
            return response
            
        except Exception as e:
            print(f"❌ Error creating endpoint config: {e}")
            raise

    def create_endpoint(self):
        """Create and deploy endpoint"""
        try:
            response = self.sagemaker.create_endpoint(
                EndpointName=self.endpoint_name,
                EndpointConfigName=self.endpoint_config_name
            )
            print(f"✅ Creating endpoint: {self.endpoint_name}")
            print("⏳ This will take 5-10 minutes...")
            
            return response
            
        except Exception as e:
            print(f"❌ Error creating endpoint: {e}")
            raise

    def wait_for_endpoint(self):
        """Wait for endpoint to be ready"""
        print("⏳ Waiting for endpoint to be ready...")
        
        start_time = time.time()
        while True:
            try:
                response = self.sagemaker.describe_endpoint(EndpointName=self.endpoint_name)
                status = response['EndpointStatus']
                
                elapsed = int(time.time() - start_time)
                print(f"   Status: {status} (elapsed: {elapsed}s)")
                
                if status == 'InService':
                    print("🎉 Endpoint is ready!")
                    return True
                elif status == 'Failed':
                    print(f"❌ Endpoint failed: {response.get('FailureReason', 'Unknown error')}")
                    return False
                elif elapsed > 1200:  # 20 minutes timeout
                    print("❌ Timeout waiting for endpoint")
                    return False
                    
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                print(f"❌ Error checking endpoint status: {e}")
                return False

    def test_endpoint(self):
        """Test the deployed endpoint"""
        runtime = boto3.client('sagemaker-runtime', region_name=self.region)
        
        test_payload = {
            "inputs": "Hello, I need help with QuickBooks Online.",
            "parameters": {
                "max_length": 100,
                "temperature": 0.7,
                "do_sample": True
            }
        }
        
        try:
            response = runtime.invoke_endpoint(
                EndpointName=self.endpoint_name,
                ContentType='application/json',
                Body=json.dumps(test_payload)
            )
            
            result = json.loads(response['Body'].read().decode())
            print("🧪 Test successful!")
            print(f"   Response: {result}")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            return False

    def deploy(self):
        """Full deployment process"""
        print("🚀 Starting QuickBooks AI LLM Deployment")
        print(f"📍 Region: {self.region}")
        print(f"🤖 Model: {self.huggingface_model['model_id']}")
        print()
        
        try:
            # Step 1: Create IAM role
            print("1️⃣ Setting up IAM role...")
            role_arn = self.create_sagemaker_role()
            
            # Step 2: Create model
            print("\n2️⃣ Creating SageMaker model...")
            self.create_model(role_arn)
            
            # Step 3: Create endpoint config
            print("\n3️⃣ Creating endpoint configuration...")
            self.create_endpoint_config()
            
            # Step 4: Deploy endpoint
            print("\n4️⃣ Deploying endpoint...")
            self.create_endpoint()
            
            # Step 5: Wait for deployment
            print("\n5️⃣ Waiting for deployment to complete...")
            if self.wait_for_endpoint():
                # Step 6: Test endpoint
                print("\n6️⃣ Testing endpoint...")
                if self.test_endpoint():
                    print(f"\n🎉 SUCCESS! Your QuickBooks AI is ready!")
                    print(f"📝 Endpoint Name: {self.endpoint_name}")
                    print(f"💰 Estimated cost: ~$1-2/hour while running")
                    print(f"🔧 Save this endpoint name for your Lambda function!")
                    return self.endpoint_name
                    
            return None
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            return None

    def cleanup(self):
        """Delete endpoint and resources"""
        try:
            print("🗑️ Cleaning up resources...")
            self.sagemaker.delete_endpoint(EndpointName=self.endpoint_name)
            self.sagemaker.delete_endpoint_config(EndpointConfigName=self.endpoint_config_name)
            self.sagemaker.delete_model(ModelName=self.model_name)
            print("✅ Cleanup complete")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")


def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'cleanup':
        print("This would cleanup resources. Run deployment first to get endpoint names.")
        return
    
    # Deploy the LLM
    deployer = SimpleLLMDeployment()
    endpoint_name = deployer.deploy()
    
    if endpoint_name:
        print(f"\n💾 Save this endpoint name: {endpoint_name}")
        print("🔄 Next: We'll create a Lambda function to use this endpoint")
    else:
        print("\n❌ Deployment failed. Check AWS console for details.")


if __name__ == "__main__":
    main()
