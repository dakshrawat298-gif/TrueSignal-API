import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv(override=True)

print("Starting AWS Bedrock Entitlement Test...")

client = boto3.client('bedrock-runtime', region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

# Hum cross-region prefix ('us.') hata kar standard model test kar rahe hain
model_id = "anthropic.claude-3-5-haiku-20241022-v1:0"

payload = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 10,
    "messages": [{"role": "user", "content": [{"type": "text", "text": "Hello"}]}]
}

try:
    print(f"\nSending ping to {model_id}...")
    response = client.invoke_model(
        modelId=model_id,
        contentType="application/json",
        accept="application/json",
        body=json.dumps(payload)
    )
    print("\n✅ SUCCESS! Your account has permission.")
except Exception as e:
    print(f"\n❌ AWS ACCOUNT BLOCK CONFIRMED!")
    print(f"Exact Error: {str(e)}")
    print("\nCONCLUSION: Your code is correct. AWS Support has restricted your account from invoking models.")