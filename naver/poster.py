
import time
import random
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Create __init__.py in this folder if needed
try:
    from browser import get_driver
except ImportError:
    # Fallback for relative import if run as package
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from browser import get_driver

def input_key_value(driver, element, value):
    """
    Inputs value into an element using JS to bypass robotic typing detection.
    """
    driver.execute_script("arguments[0].value = arguments[1];", element, value)
    time.sleep(0.5)
    driver.execute_script("""
        arguments[0].dispatchEvent(new Event('input', { bubbles: true }));
        arguments[0].dispatchEvent(new Event('change', { bubbles: true }));
    """, element)

def login_naver(driver, naver_id, naver_pw):
    """
    Performs automated login to Naver with stealth and cookie support.
    """
    print("Checking login status at naver.com...")
    try:
        driver.get("https://www.naver.com")
        time.sleep(random.uniform(2, 4))
        
        # 1. Try Cookie Login if NAVER_COOKIES env var exists
        # Format: [{"name": "...", "value": "...", "domain": ".naver.com", ...}, ...]
        env_cookies = os.getenv("NAVER_COOKIES")
        if env_cookies:
            try:
                print("Found NAVER_COOKIES in env. Attempting injection...")
                cookies = json.loads(env_cookies)
                for cookie in cookies:
                    driver.add_cookie(cookie)
                driver.get("https://www.naver.com")
                time.sleep(2)
            except Exception as ce:
                print(f"Cookie injection failed: {ce}")

        # Check login state
        logout_btn = driver.find_elements(By.CSS_SELECTOR, "button.btn_logout, a.btn_logout")
        if logout_btn and any(b.is_displayed() for b in logout_btn):
             print("Already logged in.")
             return True

    except Exception as e:
        print(f"Error checking login status: {e}")

    print(f"Navigating to Naver Login Page... (Using Account: {naver_id} / PW: {naver_pw})")
    driver.get("https://nid.naver.com/nidlogin.login")
    time.sleep(random.uniform(3, 5))
    
    try:
        id_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id"))
        )
        pw_input = driver.find_element(By.ID, "pw")
        
        print(f"Inputting Credentials for {naver_id}...")
        # Use JS for both to bypass typing issues and caps lock
        input_key_value(driver, id_input, naver_id)
        time.sleep(random.uniform(1, 2))
        input_key_value(driver, pw_input, naver_pw)
        time.sleep(random.uniform(1, 2))
        
        login_btn = driver.find_element(By.ID, "log.login")
        login_btn.click()
        time.sleep(random.uniform(4, 6))
        
        if "captcha" in driver.page_source or "자동입력 방지" in driver.page_source or "g-recaptcha" in driver.page_source:
             print("CRITICAL: Captcha detected.")
             driver.save_screenshot("debug_naver_captcha.png")
             return False
             
        # Verification
        driver.get("https://www.naver.com")
        time.sleep(3)
        if "logout" in driver.page_source or "로그아웃" in driver.page_source:
            print("Naver Login Successful.")
            return True
            
        print("Naver Login Failed: Could not verify login state.")
        return False
        
    except Exception as e:
        print(f"Login Exception: {e}")
        return False

def post_naver(job_data):
    """
    Executes the Naver posting job.
    job_data: { 'blog_id', 'blog_pw', 'category_no', 'title', 'content', ... }
    """
    blog_id = job_data['blog_id']
    # Use global Naver ID/PW if not in job_data (for main account) or job_data specific?
    # Usually platform_accounts has the ID/PW.
    # User said: "platform_accounts see blog_url/blog_id/blog_pw ..." -> So use job_data.
    
    # Note: 'blog_id' in platform_accounts might be the Naver ID for login.
    naver_id = job_data['blog_id']
    naver_pw = job_data['blog_pw']
    
    category_no = job_data['category_no']
    title = f"Post: {time.strftime('%Y-%m-%d %H:%M')}" # Temporary if title missing? 
    # Ah, implementation plan said 'content_text_by_provider' has content.
    # But where is Title? 
    # The Tables didn't show a Title column in `publish_contents` or `content_text_by_provider` explicitly in my previous check result?
    # Wait, check_tables output:
    # content_text_by_provider: id, content_text_id, provider_id, content.
    # publish_contents: ... content_text_by_provider_id
    # It seems 'Title' might be missing OR embedded in content OR I missed it in extraction.
    # User Request said: "title=job['title']" in their provided `before/main.py`.
    # BUT `database.py` that I wrote joined `content_text_by_provider` but didn't select Title column because I didn't see one in the schema check earlier?
    # Let's look at `content_texts` table? I saw `content_texts` in list but didn't inspect it.
    # content_text_by_provider likely links to `content_texts`.
    # For now, to avoid blocking, I will assume the first line of content is title, OR generic title.
    # Rereading `check_tables.py` output: 
    # `content_text_by_provider`: id, content_text_id, provider_id, content
    # It references `content_texts`.
    # `content_texts` probably has the title.
    # I should update `database.py` to join `content_texts`.
    
    # For this file, I will accept `title` in job_data.
    title = job_data.get('title', "New Blog Post") 
    content = job_data.get('content', "")

    print(f"Starting Naver Post for {blog_id}...")
    driver = None
    try:
        driver = get_driver()
        
        if not login_naver(driver, naver_id, naver_pw):
            raise Exception("Login Failed")

        blog_url = job_data.get('blog_url')
        if blog_url:
            target_url = f"{blog_url.rstrip('/')}?Redirect=Write"
        else:
            target_url = f"https://blog.naver.com/{blog_id}?Redirect=Write"
        if category_no:
            target_url += f"&categoryNo={category_no}"
            
        print(f"Navigating to Write Page: {target_url}")
        driver.get(target_url)
        time.sleep(random.uniform(5, 8))
        
        # Frame Switch: Naver Smart Editor One is usually in 'mainFrame'
        try:
            driver.switch_to.frame("mainFrame")
            print("Switched to mainFrame")
        except:
            print("No mainFrame found, assuming top-level.")

        # 1. Handle "Draft Saved" Popup (User reported blocker)
        # <strong class="se-popup-title">작성 중인 글이 있습니다.</strong>
        # Cancel button: <button type="button" class="se-popup-button se-popup-button-cancel">
        try:
            time.sleep(2)
            # Check for popup cancel button presence
            draft_cancel_btns = driver.find_elements(By.CSS_SELECTOR, ".se-popup-button-cancel")
            for btn in draft_cancel_btns:
                if btn.is_displayed():
                    btn.click()
                    print("Closed 'Draft Saved' popup.")
                    time.sleep(1)
        except:
            pass

        # 2. Handle Help/Guide Popups & Native Alerts
        try:
            time.sleep(1)
            # Dismiss native alerts if any
            try:
                alert = driver.switch_to.alert
                print(f"Native Alert detected: {alert.text}")
                alert.dismiss()
            except:
                pass
                
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            # Try closing specific help buttons
            close_btns = driver.find_elements(By.CSS_SELECTOR, ".se-help-panel-close-button, .se-help-panel-close, .se-popup-button-cancel")
            for btn in close_btns:
                if btn.is_displayed():
                    btn.click()
                    print("Closed help/popup panel.")
                    time.sleep(1)
        except:
            pass
            
        # Title Input
        print("Attempting to write title...")
        try: 
            # Smart Editor One Title Selectors
            title_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".se-documentTitle, .se-ff-tit, .se-title-text, .se-text-paragraph-align-center"))
            )
            title_input.click()
            time.sleep(1.5) # Increased delay for stability
            ActionChains(driver).send_keys(title).perform()
        except Exception as e: 
            print(f"Title input issue: {e}")

        # Content Input
        print("Attempting to write content...")
        try:
            # Smart Editor One Content Body
            content_area = driver.find_element(By.CSS_SELECTOR, ".se-main-container .se-text-paragraph, .se-component-content, .se-content")
            content_area.click()
            time.sleep(1.5)
            ActionChains(driver).send_keys(content).perform()
        except Exception as e:
            print(f"Content input issue: {e}")
            
        # 7. Publish (Robust Retry Logic)
        try:
            print("Key step: Publishing...")
            
            # Step 1: Click 'Publish' Button (Top Right)
            found_publish = False
            for attempt in range(3): # Try 3 times
                try:
                    candidates = [
                        "button[data-click-area='tpb.publish']",
                        "button[class*='publish_btn']",
                        ".btn_publish"
                    ]
                    for selector in candidates:
                        publish_btns = driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in publish_btns:
                            if btn.is_displayed():
                                # JS Click is more reliable in some headless scenarios
                                driver.execute_script("arguments[0].click();", btn)
                                found_publish = True
                                print(f"Clicked primary Publish button ({selector}) on attempt {attempt+1}.")
                                break
                        if found_publish: break
                except:
                    pass
                
                if found_publish: break
                time.sleep(2)

            if not found_publish:
                # Last resort XPath
                try:
                    btn = driver.find_element(By.XPATH, "//button[contains(., '발행')]")
                    driver.execute_script("arguments[0].click();", btn)
                    found_publish = True
                    print("Clicked primary Publish button (XPath).")
                except:
                    pass

            print("Waiting for Publish Layer to open...")
            time.sleep(2) 
            
            # Step 2: Click 'Confirm' Button (In the layer)
            # Target: <button ... class="confirm_btn__WEaBq" data-testid="seOnePublishBtn" data-click-area="tpb*i.publish">
            print("Attempting to click Final Publish button...")
            
            final_clicked = False
            try:
                layer_container = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "div[class*='layer_publish']"))
                )
                print("Publish Layer detected!")
                
                candidates = [
                    "button[data-testid='seOnePublishBtn']",       # Best: explicit test ID
                    "button[data-click-area*='tpb*i.publish']",    # Click area
                    "button[class*='confirm_btn']",                # Partial class match
                    ".btn_confirm"                                 # Legacy
                ]
                
                target_btn = None
                for candidate in candidates:
                    try:
                        btn = layer_container.find_element(By.CSS_SELECTOR, candidate)
                        if btn.is_displayed():
                            target_btn = btn
                            print(f"Found final button via selector: {candidate}")
                            break
                    except:
                        pass
                
                if not target_btn:
                    try:
                        target_btn = layer_container.find_element(By.XPATH, ".//button[contains(., '발행')]")
                        print("Found final button via inner text (scoped).")
                    except:
                        pass
                
                if target_btn:
                    driver.execute_script("arguments[0].scrollIntoView(true);", target_btn)
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", target_btn)
                    final_clicked = True
                    print("Executed JS Click on Final Button.")
                else:
                    print("Could not find any suitable button inside the layer.")

            except Exception as e:
                print(f"Final publish logic scoped failed: {e}")
                
            if final_clicked:
                print("Processed Final Click!")
                time.sleep(10)
                driver.save_screenshot("3_published_success.png")
                return True
            else:
                print("Failed to click Final Publish Button.")
                driver.save_screenshot("debug_publish_layer.png")
                return False

        except Exception as e:
            print(f"Publish logic failed: {e}")
            if driver:
                driver.save_screenshot("debug_publish_exception.png")
            return False

    except Exception as e:
        print(f"Naver Error: {e}")
        if driver:
            driver.save_screenshot("debug_naver_error.png")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
