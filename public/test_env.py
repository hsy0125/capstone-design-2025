from dotenv import load_dotenv
import os

print(" code start")

load_dotenv()
print(" .env load")

api_key = os.getenv("OPENAI_API_KEY")
print(" loaded API key:", api_key if api_key else " no key")
