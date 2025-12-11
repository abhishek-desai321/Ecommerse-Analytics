import requests
import time
import random
import uuid
from concurrent.futures import ThreadPoolExecutor

API_URL = "http://localhost:8000/ingest"

URLS = [
    "/home",
    "/products/shoes",
    "/products/electronics",
    "/products/furniture",
    "/products/clothing",
    "/cart",
    "/checkout",
    "/blog/trends",
    "/blog/news",
    "/about",
    "/contact",
    "/faq"
]

# Weights for URLS (Home is 5x more likely)
WEIGHTS = [5, 2, 3, 1, 3, 2, 1, 1, 1, 1, 1, 1]

# Sticky Sessions: {user_id: session_id}
ACTIVE_SESSIONS = {}

# Initialize with 100 users
for i in range(100):
    uid = f"user_{i}"
    sid = str(uuid.uuid4())
    ACTIVE_SESSIONS[uid] = sid

import datetime

def send_event():
    if not ACTIVE_SESSIONS:
        return

    # Weighted selection
    page_url = random.choices(URLS, weights=WEIGHTS, k=1)[0]
    
    # Pick a random active user (and their sticky session)
    user_id = random.choice(list(ACTIVE_SESSIONS.keys()))
    session_id = ACTIVE_SESSIONS[user_id]
    
    event = {
        "event_type": "page_view",
        "page_url": page_url,
        "user_id": user_id,
        "session_id": session_id,
        # ISO format Z
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }
    try:
        requests.post(API_URL, json=event, timeout=1)
    except Exception:
        pass

def rotate_ids():
    """Periodically rotate users and sessions to simulate churn."""
    global ACTIVE_SESSIONS
    while True:
        time.sleep(5) # Faster rotation for demo visibility
        
        keys = list(ACTIVE_SESSIONS.keys())
        if not keys:
            continue
            
        # 1. Churn Users (Remove ~5 users and their sessions)
        num_remove = min(len(keys), 5)
        for _ in range(num_remove):
            if keys:
                k = random.choice(keys)
                del ACTIVE_SESSIONS[k]
                keys.remove(k) # Update local list
        
        # 2. Add New Users (~5 new users with new sessions)
        for _ in range(5):
            new_uid = f"user_{str(uuid.uuid4())[:8]}"
            new_sid = str(uuid.uuid4())
            ACTIVE_SESSIONS[new_uid] = new_sid
            
        # 3. New Sessions for Existing Users (Refresh ~5 users with new session_id)
        # This simulates a user coming back in a new session
        keys = list(ACTIVE_SESSIONS.keys()) # Refresh keys
        if keys:
            num_refresh = min(len(keys), 5)
            for _ in range(num_refresh):
                k = random.choice(keys)
                ACTIVE_SESSIONS[k] = str(uuid.uuid4())
            
        print(f"Rotated IDs. Active User/Session Pairs: {len(ACTIVE_SESSIONS)}")

def flood():
    print(f"Starting flood to {API_URL}...")
    
    # Start separate thread for rotation
    import threading
    threading.Thread(target=rotate_ids, daemon=True).start()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            # Generate ~100 events/sec
            # If we submit 10 tasks every 0.1s => 100/sec
            futures = [executor.submit(send_event) for _ in range(10)]
            time.sleep(0.1)

if __name__ == "__main__":
    flood()
