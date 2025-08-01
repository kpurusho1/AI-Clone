import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LlamaParse configuration
LLAMAPARSE_API_KEY = os.getenv("LLAMAPARSE_API_KEY")
