
import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

def get_driver(headline=False):
    """
    Initializes and returns an undetected_chromedriver instance.
    """
    options = Options()
    
    # Render / Server Environment Detection
    # If running in Docker (often indicated by specific env vars or just standard server setup)
    # we usually need headless. However, undetected-chromedriver works best with head if possible,
    # but on a server with no display, we must use headless or Xvfb.
    # For Render Basic Tier (Docker), we usually need headless.
    
    is_server = os.getenv("RENDER", False) or os.getenv("CI", False)
    
    # Basic Options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    
    # Headless Mode (Optional via argument, or forced by environment)
    # Note: undetected-chromedriver has a special way to handle headless to avoid detection.
    # But for simple blog posting, standard headless might fail bot checks. 
    # Valid pattern for UC headless:
    if headline or is_server:
        options.add_argument("--headless=new") 
    
    # Language and User Agent (Generic)
    options.add_argument("--lang=ko_KR")
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        driver.set_window_size(1920, 1080)
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        # Fallback to standard selenium if UC fails (sometimes happens in strict docker)
        # But for now, just raise or return None
        raise e
