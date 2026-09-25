import os
import google.generativeai as genai
from dotenv import load_dotenv

# -------------------------------
# STEP 1: Load environment variables
# -------------------------------
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: GEMINI_API_KEY is not set in your .env file!")
    print("Please create a .env file in the same directory with the line: GEMINI_API_KEY='YOUR_API_KEY'")
    exit()

# Configure Gemini API
try:
    genai.configure(api_key=GEMINI_API_KEY)
    print("Successfully configured Google Generative AI.")
except Exception as e:
    print(f"Error configuring Google Generative AI: {e}")
    print("Please check your API key.")
    exit()


# -------------------------------
# STEP 2: List available models
# -------------------------------
print("\nListing available Generative AI models:")

try:
    # Use genai.list_models() to get an iterable of Model objects
    for model in genai.list_models():
        # Print the model name and the generation methods it supports
        # 'generateContent' is the method used for text generation
        print(f"- Model Name: {model.name}")
        print(f"  Supported Methods: {model.supported_generation_methods}")
        print("-" * 20) # Separator for clarity

except Exception as e:
    print(f"An error occurred while listing models: {e}")
    print("This could be due to an invalid API key, network issues, or API restrictions.")

print("\nModel listing complete.")
print("Look for models that support 'generateContent'. Their names (e.g., 'gemini-pro') are what you use in genai.GenerativeModel().")