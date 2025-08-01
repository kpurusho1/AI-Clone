from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY

# Initialize Supabase client
def get_supabase_client():
    """
    Creates and returns a Supabase client instance
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("Supabase URL and service role key must be provided")
    
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

# Get a client instance
supabase = get_supabase_client()
