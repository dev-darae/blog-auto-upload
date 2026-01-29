
import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options

def get_driver(headless=True):
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
    env_headless = os.getenv("HEADLESS", None)
    if env_headless is not None:
        headless = env_headless.lower() == "true"
    
    # Basic Options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-blink-features=AutomationControlled")
    
    # Headless Mode
    if headless or is_server:
        options.add_argument("--headless=new") 
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        # Headless specific flags to avoid detection
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    else:
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Language
    options.add_argument("--lang=ko_KR")

    try:
        if is_server:
            # Render's current google-chrome-stable is 144, but UC is trying to use 145 driver.
            # We force version_main=144 for compatibility on the server.
            driver = uc.Chrome(options=options, use_subprocess=True, version_main=144)
        else:
            # Locally, let it auto-detect or use default (currently 144 on user's Mac)
            driver = uc.Chrome(options=options, use_subprocess=True)
            
        driver.set_window_size(1920, 1080)
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        # Fallback to standard selenium if UC fails (sometimes happens in strict docker)
        # But for now, just raise or return None
        raise e
