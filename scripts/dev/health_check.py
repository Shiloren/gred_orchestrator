import argparse
import sys
import time

try:
    import requests
except ImportError:
    # If requests is not available, try to use urllib.request (built-in)
    import urllib.request as urllib_request
    requests = None

def check_health(url, timeout=1, max_retries=30, retry_delay=1):
    """
    Checks if the GIMO backend is up and running.
    """
    for i in range(max_retries):
        try:
            if requests:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    return True
            else:
                with urllib_request.urlopen(url, timeout=timeout) as response:
                    if response.status == 200:
                        return True
        except Exception:
            pass
        
        if i < max_retries - 1:
            time.sleep(retry_delay)
            
    return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check GIMO Backend Health")
    parser.add_argument("--port", type=int, default=9325, help="Port to check")
    parser.add_argument("--timeout", type=int, default=30, help="Max wait time in seconds")
    
    args = parser.parse_args()
    
    health_url = f"http://127.0.0.1:{args.port}/"
    
    if check_health(health_url, max_retries=args.timeout):
        print(f"Backend is healthy at {health_url}")
        sys.exit(0)
    else:
        print(f"Timeout: Backend at {health_url} is not responding.")
        sys.exit(1)
