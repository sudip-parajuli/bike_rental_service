import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key)
    
    models = ['gemini-2.5-flash', 'gemini-pro', 'gemini-1.0-pro', 'gemini-2.5-pro']
    
    for model_name in models:
        print(f"\nTesting {model_name}...")
        try:
            model = genai.GenerativeModel(model_name)
            # Set a timeout if possible, or just hope it doesn't hang forever
            response = model.generate_content("Hello", request_options={'timeout': 10})
            print(f"SUCCESS with {model_name}")
        except Exception as e:
            print(f"FAILED with {model_name}: {e}")
