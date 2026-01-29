
import time
import json
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import os

try:
    from browser import get_driver
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from browser import get_driver

def login_kakao(driver, user_id, user_pw):
    """
    Logins to Tistory via Kakao Account using 'Click then Type' logic.
    """
    print("Navigating to Tistory Login...")
    driver.get("https://www.tistory.com/auth/login")
    time.sleep(2)
    
    # Click 'Kakao Login' button
    try:
        kakao_login_btn = driver.find_element(By.CSS_SELECTOR, ".btn_login.link_kakao_id")
        kakao_login_btn.click()
    except:
        pass
        
    time.sleep(2)
    
    # Check if on Kakao login page
    if "accounts.kakao.com" in driver.current_url:
        print("On Kakao Login Page. Inputting credentials...")
        try:
            # Login Input
            # 1. ID
            id_input = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "loginId--1"))
            )
            id_input.click()
            time.sleep(0.5)
            id_input.send_keys(user_id)
            time.sleep(0.5)
            
            # 2. Password
            pw_input = driver.find_element(By.ID, "password--2")
            pw_input.click()
            time.sleep(0.5)
            pw_input.send_keys(user_pw)
            time.sleep(0.5)
            
            # Submit: <button type="submit" class="btn_g highlight submit">로그인</button>
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button.btn_g.highlight.submit")
            submit_btn.click()
            time.sleep(5)
            
            # Check success
            if "tistory.com" in driver.current_url:
                print("Login successful.")
                return True
            elif "protect" in driver.current_url:
                print("CRITICAL: Kakao Account Protection triggered.")
                return False
            else:
                 # Fallback check
                 return True 
                 
        except Exception as e:
            print(f"Kakao Login failed: {e}")
            driver.save_screenshot("debug_tistory_login_fail.png")
            return False
            
    return True

def format_content_to_html(text, images):
    """
    Converts plain text to HTML.
    Detects image URLs in text and converts them to <img> tags.
    """
    html_parts = []
    used_images = set()
    
    if text:
        lines = text.split('\n')
        for line in lines:
            safe_line = line.strip()
            if not safe_line:
                html_parts.append('<p data-ke-size="size16">&nbsp;</p>')
                continue
                
            # Check if line is an image URL
            # Simple heuristic: starts with http and ends with extension or looks like the vercel blob url
            if safe_line.startswith('http') and ('blob.vercel-storage.com' in safe_line or safe_line.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))):
                # Convert to Image Tag
                html_parts.append(f'<p style="text-align: center;"><img src="{safe_line}" style="max-width: 100%;" /></p>')
                used_images.add(safe_line)
            else:
                html_parts.append(f'<p data-ke-size="size16">{safe_line}</p>')
                
    # Append Images that passed within 'images' list but weren't found in text (Fallback)
    if images:
        remaining_images = [img for img in images if img not in used_images]
        if remaining_images:
            html_parts.append('<hr contenteditable="false" data-ke-type="horizontalRule" data-ke-style="style5" />')
            for img_url in remaining_images:
                html_parts.append(f'<p style="text-align: center;"><img src="{img_url}" style="max-width: 100%;" /></p>')
            
    return "".join(html_parts)

def post_tistory(job_data):
    """
    Executes Tistory posting using strict user flow.
    """
    # Credentials
    user_id = job_data['blog_id']
    user_pw = job_data['blog_pw']
    
    # Blog URL
    blog_url = job_data.get('blog_url')
    if not blog_url: return False
    blog_url = blog_url.rstrip('/')
    if not blog_url.startswith('http'):
        blog_url = f"https://{blog_url}"

    title = job_data.get('title', 'No Title')
    content_raw = job_data.get('content', '')
    images = job_data.get('images', [])
    category_id = str(job_data.get('category_no', ''))

    print(f"Starting Tistory Post to {blog_url}...")
    
    driver = None
    try:
        driver = get_driver()
        
        # 1. Login
        if not login_kakao(driver, user_id, user_pw):
            return False
            
        # 2. Navigate to Blog Home & Click Write
        print(f"Navigating to Blog Home: {blog_url}")
        driver.get(blog_url)
        time.sleep(3)
        
        try:
            # <button type="button" class="btn-g btn-primary btn-write">글쓰기</button>
            write_btn = driver.find_element(By.CSS_SELECTOR, "button.btn-write, .btn-write, a[href*='/manage/newpost']")
            write_btn.click()
            print("Clicked Write button.")
        except:
            print("Write button not found on home, trying direct URL...")
            driver.get(f"{blog_url}/manage/newpost")
            
        time.sleep(5)
        
        # 2.5 Handle "Draft Saved" alert if it exists
        try:
            alert = driver.switch_to.alert
            print(f"Draft Alert detected: {alert.text}")
            alert.dismiss() # Or alert.accept()? User said "취소를 누르고" -> dismiss()
            print("Dismissed draft saved alert.")
            time.sleep(1)
        except:
            pass
        
        # 3. Switch to HTML Mode
        try:
            mode_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "editor-mode-layer-btn-open"))
            )
            mode_btn.click()
            time.sleep(0.5)
            
            html_item = driver.find_element(By.ID, "editor-mode-html")
            html_item.click()
            print("Switched to HTML mode.")
            time.sleep(1)
            
            try:
                alert = driver.switch_to.alert
                alert.accept()
                print("Accepted HTML switch alert.")
            except:
                pass
                
        except Exception as e:
            print(f"HTML Switch failed: {e}")
            
        # 4. Select Category
        if category_id:
            try:
                print(f"Attempting to select Category ID: {category_id}")
                cat_btn = driver.find_element(By.ID, "category-btn")
                cat_btn.click()
                print("Clicked Category Button.")
                
                # Wait for the list to appear
                # User provided: <div id="category-list" ...>
                try:
                    WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.ID, "category-list"))
                    )
                except:
                    print("Category list check timed out, proceeding anyway.")
                
                time.sleep(1) 
                
                # Find selector by attribute
                target_cat = driver.find_element(By.CSS_SELECTOR, f"div[category-id='{category_id}']")
                
                # Ensure visible?
                if not target_cat.is_displayed():
                     print("Category item hidden, trying script click.")
                     driver.execute_script("arguments[0].click();", target_cat)
                else:
                    target_cat.click()
                    
                print(f"Selected category {category_id}")
            except Exception as e:
                print(f"Category selection failed: {e}")
                
        # 5. Input Title
        try:
            title_inp = driver.find_element(By.ID, "post-title-inp")
            title_inp.click()
            time.sleep(0.5)
            title_inp.send_keys(title)
            print("Entered Title.")
        except Exception as e:
             print(f"Title input failed: {e}")

        # 6. Input Content (HTML)
        html_content = format_content_to_html(content_raw, images)
        time.sleep(1)
        
        try:
            # Strategies to focus Content Area
            # Tistory HTML mode uses AceEditor often
            content_entered = False
            
            # Strategy A: Find the Ace Text Input (often 1px hidden but accepts keys)
            try:
                ace_input = driver.find_element(By.CSS_SELECTOR, "textarea.ace_text-input")
                ace_input.send_keys(html_content)
                content_entered = True
                print("Entered Content (Ace Input).")
            except:
                pass
                
            # Strategy B: Tab from Title
            if not content_entered:
                try:
                    # Move focus back to title then Tab
                    driver.find_element(By.ID, "post-title-inp").click()
                    actions = ActionChains(driver)
                    actions.send_keys(Keys.TAB).perform() # Move to potential toolbar
                    time.sleep(0.1)
                    actions.send_keys(Keys.TAB).perform() # Move to Content?
                    time.sleep(0.5)
                    actions.send_keys(html_content).perform()
                    content_entered = True
                    print("Entered Content (Tab Navigation).")
                except:
                    pass
            
            if not content_entered:
                # Strategy C: Active Element Fallback
                driver.switch_to.active_element.send_keys(html_content)
                print("Entered Content (Active Element Fallback).")

        except Exception as e:
            print(f"Content input failed: {e}")
            
        time.sleep(2)

        # 7. Publish
        try:
            complete_btn = driver.find_element(By.ID, "publish-layer-btn")
            complete_btn.click()
            print("Clicked Compelte (Open Layer).")
            time.sleep(1)
            
            try:
                public_label = driver.find_element(By.XPATH, "//span[contains(text(), '공개')]")
                public_label.click()
                print("Selected Public.")
            except:
                pass
                
            time.sleep(1)
            
            final_btn = driver.find_element(By.ID, "publish-btn")
            final_btn.click()
            print("Clicked Final Publish.")
            
            time.sleep(5)
            # Check success (redirect to entry)
            if "/entry/" in driver.current_url or "numeric ID" in driver.current_url:
                print("Published successfully.")
                return True
                
            # If still on write page, assume fail
            if "newpost" in driver.current_url:
                 return False
                 
            return True # Optimistic if redirected elsewhere
            
        except Exception as e:
            print(f"Publishing failed: {e}")
            driver.save_screenshot("debug_tistory_publish_fail.png")
            return False

    except Exception as e:
        print(f"Tistory Post Error: {e}")
        if driver:
            driver.save_screenshot("debug_tistory_error.png")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass
    
    return False
