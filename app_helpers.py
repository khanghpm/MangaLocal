import requests
import time
from functools import wraps

MAX_RETRIES = 3
TIMEOUT = 10
API_URL = "https://api.mangadex.org"

class APIError(Exception):
    """Custom exception cho API errors"""
    pass

def safe_api_call(max_retries=MAX_RETRIES):
    """Decorator để wrap tất cả API calls với error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.Timeout:
                    if attempt == max_retries - 1:
                        raise APIError("API request timed out. Please try again.")
                    time.sleep(1)
                except requests.exceptions.ConnectionError:
                    if attempt == max_retries - 1:
                        raise APIError("Cannot connect to MangaDex. Check your internet.")
                    time.sleep(2)
                except (ValueError, KeyError) as e:
                    raise APIError(f"Invalid API response: {str(e)}")
            return None
        return wrapper
    return decorator

@safe_api_call()
def fetch_manga_list(params):
    """Fetch manga list từ MangaDex"""
    resp = requests.get(f"{API_URL}/manga", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

@safe_api_call()
def fetch_manga_detail(manga_id):
    """Fetch chi tiết 1 manga"""
    resp = requests.get(
        f"{API_URL}/manga/{manga_id}",
        params={"includes[]": ["cover_art", "author"]},
        timeout=TIMEOUT
    )
    resp.raise_for_status()
    return resp.json()

@safe_api_call()
def fetch_chapters(manga_id, lang='en'):
    """Fetch chapters của 1 manga"""
    params = {
        "limit": 500,
        "translatedLanguage[]": [lang, "no"],
        "order[chapter]": "desc",
        "contentRating[]": ["safe", "suggestive", "erotica", "pornographic"]
    }
    resp = requests.get(f"{API_URL}/manga/{manga_id}/feed", params=params, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

@safe_api_call()
def fetch_tags():
    """Fetch tất cả tags"""
    resp = requests.get(f"{API_URL}/manga/tag", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

@safe_api_call()
def fetch_chapter_pages(chapter_id):
    """Fetch pages của 1 chapter"""
    resp = requests.get(f"{API_URL}/at-home/server/{chapter_id}", timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()