#!/usr/bin/env python3
""" Redis Module """

from functools import wraps
import redis
import requests
from typing import Callable

# Initialize Redis client
redis_ = redis.Redis()

def count_requests(method: Callable) -> Callable:
    """ Decorator for counting and caching requests """
    @wraps(method)
    def wrapper(url: str) -> str:
        """ Wrapper that increments count and caches the result """
        # Increment the count for this URL
        redis_.incr(f"count:{url}")
        
        # Check if the URL is cached
        cached_html = redis_.get(f"cached:{url}")
        if cached_html:
            return cached_html.decode('utf-8')
        
        # If not cached, fetch the page and cache it for 10 seconds
        html = method(url)
        redis_.setex(f"cached:{url}", 10, html)  # Cache with a 10-second expiry
        return html

    return wrapper

@count_requests
def get_page(url: str) -> str:
    """ Obtain the HTML content of a URL """
    # Perform the actual request
    req = requests.get(url)
    return req.text
