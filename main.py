
import time
import os
import pytz
from datetime import datetime
from dotenv import load_dotenv

import database
import naver.poster
import tistory.poster

# Configure Logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_naver_automation():
    load_dotenv()
    PROVIDER_NAVER = 19
    logging.info("--- Starting Naver Automation Cycle ---")
    try:
        naver_jobs = database.get_scheduled_jobs(PROVIDER_NAVER)
        logging.info(f"Found {len(naver_jobs)} Naver jobs.")
        for job in naver_jobs:
            logging.info(f"Processing Naver Job: {job['publish_id']} ({job['title']})")
            success = naver.poster.post_naver(job)
            status_id = 3 if success else 2
            fail_reason = None if success else "Automation Script Failed"
            database.update_job_status(job['publish_id'], status_id, fail_reason)
            time.sleep(5)
    except Exception as e:
        logging.error(f"Naver Loop Error: {e}")
    logging.info("--- Naver Cycle Completed ---")

def run_tistory_automation():
    load_dotenv()
    PROVIDER_TISTORY = 8
    logging.info("--- Starting Tistory Automation Cycle ---")
    try:
        tistory_jobs = database.get_scheduled_jobs(PROVIDER_TISTORY)
        logging.info(f"Found {len(tistory_jobs)} Tistory jobs.")
        for job in tistory_jobs:
            logging.info(f"Processing Tistory Job: {job['publish_id']} ({job['title']})")
            success = tistory.poster.post_tistory(job)
            status_id = 3 if success else 2
            fail_reason = None if success else "Automation Script Failed"
            database.update_job_status(job['publish_id'], status_id, fail_reason)
            time.sleep(5)
    except Exception as e:
        logging.error(f"Tistory Loop Error: {e}")
    logging.info("--- Tistory Cycle Completed ---")

if __name__ == "__main__":
    KST = pytz.timezone('Asia/Seoul')
    logging.info("Worker Started. Scheduled Mode: Naver(00,30m), Tistory(15,45m)")
    
    last_run_minute = -1
    
    while True:
        now = datetime.now(KST)
        current_minute = now.minute
        
        # Avoid running multiple times in the same minute
        if current_minute != last_run_minute:
            if current_minute in [0, 10, 30]: # Added 10 for testing
                run_naver_automation()
                last_run_minute = current_minute
            elif current_minute in [15, 45]:
                run_tistory_automation()
                last_run_minute = current_minute
                
        # Check every 30 seconds to be precise but not too frequent
        time.sleep(30)
