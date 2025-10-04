import os
import google.generativeai as genai
from dotenv import load_dotenv

# This script tests your Google AI API key.

# Load environment variables from .env file
load_dotenv()

print("--- Starting API Key Test ---")

try:
    # 1. Load the API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("\n[ERROR] GOOGLE_API_KEY not found in your .env file.")
        print("Please make sure the .env file exists in the same directory and contains your key.")
    else:
        print("\nAPI key found in .env file.")
        
        # 2. Configure the generative AI client
        genai.configure(api_key=api_key)
        print("Successfully configured the Google AI client.")
        
        # 3. List available models
        print("\nFetching available models for your key...")
        model_list = list(genai.list_models())
        
        if not model_list:
            print("\n[ERROR] No models are available for your API key.")
            print("This might mean the key is invalid, has expired, or has no services enabled.")
        else:
            print("\n--- Available Generative Models ---")
            for m in model_list:
                if 'generateContent' in m.supported_generation_methods:
                    print(f"- {m.name}")
            print("-------------------------------------")

        print("\n[SUCCESS] Test complete.")
        print("If you see a list of models above, your API key is working correctly.")
        print("The error in the main app is likely because the specific model name in main.py is not in this list.")

except Exception as e:
    print(f"\n[ERROR] An unexpected error occurred during the test: {e}")

print("\n--- End of API Key Test ---")
