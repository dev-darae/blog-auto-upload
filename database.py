
import os
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = None
Session = None

def init_db():
    global engine, Session
    if not DATABASE_URL:
        print("CRITICAL: DATABASE_URL is missing.")
        return

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)
        session_factory = sessionmaker(bind=engine)
        Session = scoped_session(session_factory)
        print("Database initialized.")
    except Exception as e:
        print(f"Database initialization failed: {e}")

def get_scheduled_jobs(platform_provider_id):
    """
    Fetches jobs that are:
    1. Scheduled (reserved_at <= NOW)
    2. Status is PENDING (publish_status_id = 0, assuming 0 is pending based on typical usage)
    3. Matches the platform provider ID (Naver=1, Tistory=2 - TBD, need to verify or accept logic)
    
    Logic updates logic:
    - User mentioned checking: platform_accounts, publish_contents, publish_contents_groups, content_text_by_provider
    - We need to join these tables.
    """
    if not Session:
        init_db()
    
    s = Session()
    try:
        # Assuming Status IDs: 0=PENDING, 1=SUCCESS, 2=FAILED (User didn't specify, extracting from context or using conventions)
        # Let's assume 'reserved_at' is the trigger.
        
        # We also need to get the blog_id, blog_pw from platform_accounts
        # And content from content_text_by_provider
        
        # Query: 
        # Select publish_contents that are ready
        # JOIN platform_accounts ON pc.platform_account_id = pa.id
        # JOIN content_text_by_provider ON pc.content_text_by_provider_id = ctp.id
        # WHERE pa.provider_id = :provider_id 
        # AND pc.reserved_at <= NOW() 
        # AND pc.publish_status_id = 0 (PENDING)
        

        # Fetch Job Details including Title (from content_texts) and Content
        query = text("""
            SELECT 
                pc.id as publish_id,
                pc.content_image_ids,
                pc.content_video_id,
                
                pa.id as account_id,
                pa.blog_id,
                pa.blog_pw,
                pa.blog_url,
                pa.category_no,
                
                ctp.content as content_html,
                
                ct.content_title
                
            FROM publish_contents pc
            JOIN platform_accounts pa ON pc.platform_account_id = pa.id
            JOIN content_text_by_provider ctp ON pc.content_text_by_provider_id = ctp.id
            JOIN content_texts ct ON ctp.content_text_id = ct.id
            
            WHERE pa.provider_id = :provider_id
              AND pc.publish_status_id = 1
              AND pc.reserved_at <= NOW()
        """)
        
        result = s.execute(query, {'provider_id': platform_provider_id}).fetchall()
        
        jobs = []
        for row in result:
            image_urls = []
            # Resolve Image IDs to URLs
            if row.content_image_ids:
                try:
                    img_ids = row.content_image_ids
                    if isinstance(img_ids, str):
                        img_ids = json.loads(img_ids)
                    
                    if img_ids:
                        # Fetch URLs for these IDs
                        # We have to do this in a loop or WHERE IN clause. 
                        # Since list might be small, WHERE IN is better.
                        # Note: Postgres/SQLAlchemy passing list to IN clause requires tuple or specific handling.
                        # Easier to just run a quick query here since traffic is low.
                        img_query = text("SELECT image_url FROM content_images WHERE id IN :ids ORDER BY \"order\" ASC")
                        img_rows = s.execute(img_query, {'ids': tuple(img_ids)}).fetchall()
                        image_urls = [r.image_url for r in img_rows]
                except Exception as e:
                    print(f"Error resolving images for job {row.publish_id}: {e}")

            jobs.append({
                'publish_id': row.publish_id,
                'blog_id': row.blog_id,
                'blog_pw': row.blog_pw,
                'blog_url': row.blog_url,
                'category_no': row.category_no,
                'title': row.content_title,       # Now we have the title!
                'content': row.content_html, 
                'images': image_urls,             # List of URL strings
                'video': row.content_video_id
            })
        return jobs
        
    except Exception as e:
        print(f"Error fetching jobs: {e}")
        return []
    finally:
        Session.remove()

def update_job_status(publish_id, status_id, fail_reason=None):
    """
    Updates the job status.
    status_id: 1=Success, 2=Fail
    """
    if not Session:
        init_db()
    s = Session()
    try:

        # 1. Update the individual job status
        query = text("""
            UPDATE publish_contents
            SET publish_status_id = :status_id,
                fail_reason = :fail_reason,
                published_at = NOW(),
                updated_at = NOW()
            WHERE id = :publish_id
            RETURNING group_id
        """)
        result = s.execute(query, {
            'status_id': status_id, 
            'fail_reason': fail_reason, 
            'publish_id': publish_id
        })
        
        row = result.fetchone()
        group_id = row.group_id if row else None
        
        # 2. Check if Group Status needs update
        if group_id and status_id == 3: # Only check on success for now, or always?
            # Check if there are any non-success items in this group
            # Assuming we want to mark group as COMPLETE (3) only if ALL items are 3.
            check_query = text("""
                SELECT COUNT(*) 
                FROM publish_contents 
                WHERE group_id = :group_id 
                  AND publish_status_id != 3
            """)
            pending_count = s.execute(check_query, {'group_id': group_id}).scalar()
            
            if pending_count == 0:
                print(f"All items in Group {group_id} are published. Updating Group Status.")
                group_update = text("""
                    UPDATE publish_contents_groups
                    SET publish_status_id = 3
                    WHERE id = :group_id
                """)
                s.execute(group_update, {'group_id': group_id})
                
        s.commit()
    except Exception as e:
        print(f"Error updating job {publish_id}: {e}")
        s.rollback()
    finally:
        Session.remove()
