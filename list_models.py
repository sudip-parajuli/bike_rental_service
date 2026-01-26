import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {bool(api_key)}")

if api_key:
    genai.configure(api_key=api_key, transport='rest')
    with open('available_models.txt', 'w') as f:
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    f.write(m.name + '\n')
                    print(m.name)
        except Exception as e:
            f.write(f"Failed to list models: {e}\n")
            print(f"Failed: {e}")
