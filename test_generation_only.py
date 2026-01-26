import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key)
    print("Testing gemini-pro generation...")
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello")
        print(f"Success! Response: {response.text}")
    except Exception as e:
        print(f"Failed: {e}")
