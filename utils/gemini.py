import os
from dotenv import load_dotenv
from google import genai
from env import env

client = genai.Client(api_key=env.gemini_api_key)