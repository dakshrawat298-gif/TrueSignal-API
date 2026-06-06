import boto3
import os
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    print("Connecting to AWS Bedrock...")
    # Using 'bedrock' client instead of 'bedrock-runtime' to check model list
    client = boto3.client('bedrock', region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
    
    response = client.list_foundation_models()
    print("\n✅ SUCCESS! Connected to AWS. Finding Claude models...\n")
    
    claude_found = False
    for model in response['modelSummaries']:
        if 'claude' in model['modelId'].lower():
            claude_found = True
            print(f"- {model['modelId']}")
            
    if not claude_found:
        print("No Claude models found in your accessible list.")
        
except Exception as e:
    print(f"\n❌ AWS ERROR: {str(e)}")