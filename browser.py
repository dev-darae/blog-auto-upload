import os
import time
import random
import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
import subprocess
import re

def get_installed_chrome_version():
    """
    Attempts to detect the major version of the installed Google Chrome.
    """
    try:
        if os.name == 'nt':
            # Windows
            # Standard Registry path for Chrome version
            try:
                cmd = 'reg query "HKEY_CURRENT_USER\\Software\\Google\\Chrome\\BLBeacon" /v version'
                output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            except:
                try:
                    # System-wide install
                    cmd = 'reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\Google\\Chrome\\BLBeacon" /v version'
                    output = subprocess.check_output(cmd, shell=True).decode('utf-8')
                except:
                    output = ""
        elif os.path.exists("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"):
            # Mac
            cmd = "'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' --version"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
        else:
            # Linux/Server paths
            cmd = "google-chrome --version || google-chrome-stable --version"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')
            
        # Parse version
        version_match = re.search(r'(\d+)\.\d+\.\d+\.\d+', output)
        if not version_match:
             version_match = re.search(r' (\d+)\.', output)

        if version_match:
            return int(version_match.group(1))
    except Exception as e:
        print(f"Warning: Could not detect Chrome version: {e}")
    return None

def get_driver(headless=False):
    """
    Initializes and returns an undetected_chromedriver instance.
    """
    options = Options()
    
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
        options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    else:
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    # Language
    options.add_argument("--lang=ko_KR")

    # Version Detection
    installed_version = get_installed_chrome_version()
    if installed_version:
        print(f"Detected Chrome version: {installed_version}")
    
    try:
        # Detected version and use_subprocess=True for maximum compatibility/stealth
        driver = uc.Chrome(options=options, use_subprocess=True, version_main=installed_version)
            
        driver.set_window_size(1920, 1080)
        return driver
    except Exception as e:
        print(f"Failed to initialize driver: {e}")
        raise e
