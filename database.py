import os
from supabase import create_client, Client
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not url or not key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables must be set"
        )

    return create_client(url, key)


# Module-level client (recreated per request if needed)
_client: Client | None = None


def get_db() -> Client:
    global _client
    if _client is None:
        _client = get_supabase_client()
    return _client
