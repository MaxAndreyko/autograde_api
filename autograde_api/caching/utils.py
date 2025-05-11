import hashlib
import json

def make_cache_key(username: str, data: dict) -> str:
    """Generate a unique cache key for each username+data combo."""
    raw = f"{username}:{json.dumps(data, sort_keys=True)}"
    return "prediction:" + hashlib.sha256(raw.encode()).hexdigest()