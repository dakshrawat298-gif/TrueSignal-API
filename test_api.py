import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load API key from .env
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("[FATAL ERROR] API Key nahi mili! Apni .env file check kar.")
else:
    print(f"[INFO] API Key loaded successfully (Starts with: {api_key[:5]}...)")
    genai.configure(api_key=api_key)
    
    print("[INFO] Contacting Google Gemini 1.5 Flash...")
    try:
        # Hum 1.5-flash test kar rahe hain
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'BOOM! THE API IS WORKING PERFECTLY.'")
        print("\n[SUCCESS] Response from AI:")
        print("=>", response.text.strip())
    except Exception as e:
        print("\n[FAILED] Google ne error phek diya:")
        print("=>", str(e))