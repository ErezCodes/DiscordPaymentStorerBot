
import asyncio
import random
import time
from collections import deque
from googleapiclient.errors import HttpError

# A queue to store pending Google Sheets requests
request_queue = deque()

# Exponential backoff limits
MAX_RETRIES = 5
INITIAL_DELAY = 1  # Start with a 1-second delay

# Cooldown dictionary to track user cooldowns
user_cooldowns = {}

# Cooldown duration in seconds
COOLDOWN_DURATION = 5

async def process_request_with_retry(request_func, *args, **kwargs):
    """Retries the given request function with exponential backoff if needed."""
    retries = 0
    delay = INITIAL_DELAY

    while retries < MAX_RETRIES:
        try:
            # Attempt to execute the request
            request_func(*args, **kwargs)
            return  # Exit if successful
        except HttpError as e:
            if e.resp.status in [429, 500, 503]:  # API overuse or temporary failure
                print(f"Google API limit reached. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)  # Wait before retrying
                retries += 1
                delay *= 2  # Exponential backoff
            else:
                raise  # Raise the exception for non-retryable errors

    # If all retries fail, queue the request for later processing
    print("Max retries exceeded. Adding request to queue.")
    request_queue.append((request_func, args, kwargs))

async def process_request_queue():
    """Processes queued requests."""
    while request_queue:
        request_func, args, kwargs = request_queue.popleft()
        await process_request_with_retry(request_func, *args, **kwargs)

def is_on_cooldown(user_id):
    """Check if a user is on cooldown."""
    current_time = time.time()
    if user_id in user_cooldowns:
        last_time = user_cooldowns[user_id]
        if current_time - last_time < COOLDOWN_DURATION:
            return True
    return False

def update_cooldown(user_id):
    """Update the cooldown for a user."""
    user_cooldowns[user_id] = time.time()
