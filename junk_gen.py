import requests
import time
import random

def junk_flood():
    print("Starting junk flood to http://localhost:8000/ingest...")
    
    url = "http://localhost:8000/ingest"
    
    # 1. Invalid JSON
    print("Sending invalid JSON...")
    try:
        requests.post(url, data="This is not JSON", headers={"Content-Type": "application/json"})
    except:
        pass

    # 2. Missing fields
    print("Sending missing fields...")
    try:
        requests.post(url, json={"user_id": "123"}, headers={"Content-Type": "application/json"})
    except:
        pass

    # 3. Wrong types
    print("Sending wrong types...")
    try:
        requests.post(url, json={"user_id": 123, "timestamp": "not-a-date"}, headers={"Content-Type": "application/json"})
    except:
        pass

    print("Sending random junk...")
    while True:
        try:
            # Random mix of bad requests
            case = random.randint(1, 3)
            if case == 1:
                requests.post(url, data="{ bad json }", headers={"Content-Type": "application/json"})
            elif case == 2:
                requests.post(url, json={"unknown_field": "test"})
            elif case == 3:
                # 404
                requests.get("http://localhost:8000/not-found")
            
            print(".", end="", flush=True)
            time.sleep(0.5)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    junk_flood()
