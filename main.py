
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

def run_automation():
    load_dotenv()
    
    # Provider IDs (CONSTANTS, assumed based on DB context)
    PROVIDER_NAVER = 19
    PROVIDER_TISTORY = 8
    
    logging.info("--- Starting Automation Cycle ---")
    
    # 1. Naver Jobs
    try:
        naver_jobs = database.get_scheduled_jobs(PROVIDER_NAVER)
        logging.info(f"Found {len(naver_jobs)} Naver jobs.")
        
        for job in naver_jobs:
            logging.info(f"Processing Naver Job: {job['publish_id']} ({job['title']})")
            success = naver.poster.post_naver(job)
            
            status_id = 3 if success else 2 # 3=Published, 2=Fail
            fail_reason = None if success else "Automation Script Failed"
            
            database.update_job_status(job['publish_id'], status_id, fail_reason)
            time.sleep(10) # Cooling between jobs
            
    except Exception as e:
        logging.error(f"Naver Loop Error: {e}")

    # 2. Tistory Jobs
    try:
        tistory_jobs = database.get_scheduled_jobs(PROVIDER_TISTORY)
        logging.info(f"Found {len(tistory_jobs)} Tistory jobs.")
        
        for job in tistory_jobs:
            logging.info(f"Processing Tistory Job: {job['publish_id']} ({job['title']})")
            success = tistory.poster.post_tistory(job)
            
            status_id = 3 if success else 2
            fail_reason = None if success else "Automation Script Failed"
            
            database.update_job_status(job['publish_id'], status_id, fail_reason)
            time.sleep(10)
            
    except Exception as e:
        logging.error(f"Tistory Loop Error: {e}")

    logging.info("--- Cycle Completed ---")

if __name__ == "__main__":
    # Background Worker Loop
    # User requested: "Run 4 times an hour" -> every 15 minutes.
    INTERVAL_MINUTES = 15
    
    logging.info(f"Worker Started. Running every {INTERVAL_MINUTES} minutes.")
    
    while True:
        run_automation()
        
        # Wait for next cycle
        logging.info(f"Sleeping for {INTERVAL_MINUTES} minutes...")
        time.sleep(60 * INTERVAL_MINUTES)
