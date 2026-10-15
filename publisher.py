#!/usr/bin/env python3
"""
publisher.py - Automated X (Twitter) Publisher for Portfolio Campaign
Strictly follows:
- X API v2 via Tweepy with user-context authentication
- Gate: Refuses to post unless GO_LIVE.txt exists and HOLD.txt does not
- Processes pending posts whose datetime_wat has passed
- Handles threads (in_reply_to_tweet_id) and media uploads
- Marks status 'posted:<tweet_id>' and appends to log.txt
- Retries on API errors without crashing the batch
- Supports --dry-run
"""

import os
import sys
import csv
import argparse
from datetime import datetime, timezone, timedelta
import tweepy

# Reconfigure stdout/stderr to utf-8 on Windows
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr.encoding != 'utf-8':
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Timezone: West Africa Time (WAT) is UTC+1
WAT_TZ = timezone(timedelta(hours=1))

CSV_FILE = "posts.csv"
LOG_FILE = "log.txt"
GO_LIVE_FILE = "GO_LIVE.txt"
HOLD_FILE = "HOLD.txt"


def load_env_file():
    """Load environment variables from .env file if present."""
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k not in os.environ:
                        os.environ[k] = v


def get_current_wat():
    """Return current datetime in WAT timezone (UTC+1)."""
    return datetime.now(WAT_TZ)


def log_message(msg):
    """Log to console and append to log.txt."""
    now_str = get_current_wat().strftime("%Y-%m-%d %H:%M:%S WAT")
    formatted = f"[{now_str}] {msg}"
    try:
        print(formatted)
    except Exception:
        print(formatted.encode("ascii", "replace").decode("ascii"))
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception as e:
        print(f"Failed to write to log file: {e}")


def check_gates(dry_run=False):
    """
    Check gating files:
    - Must refuse to post unless GO_LIVE.txt exists and HOLD.txt does not.
    """
    if os.path.exists(HOLD_FILE):
        log_message(f"GATE BLOCKED: '{HOLD_FILE}' exists in repo. All posting is halted.")
        return False

    if not os.path.exists(GO_LIVE_FILE):
        if dry_run:
            log_message(f"GATE NOTICE (Dry Run): '{GO_LIVE_FILE}' does not exist yet (Live runs will refuse to post until created).")
            return True
        else:
            log_message(f"GATE BLOCKED: '{GO_LIVE_FILE}' does not exist. Live publishing is disabled.")
            return False

    return True


def get_twitter_clients():
    """Initialize Tweepy v2 Client and v1.1 API (for media upload)."""
    api_key = os.getenv("TWITTER_API_KEY") or os.getenv("X_API_KEY") or os.getenv("CONSUMER_KEY")
    api_secret = os.getenv("TWITTER_API_SECRET") or os.getenv("X_API_SECRET") or os.getenv("CONSUMER_SECRET")
    access_token = os.getenv("TWITTER_ACCESS_TOKEN") or os.getenv("X_ACCESS_TOKEN")
    access_token_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET") or os.getenv("X_ACCESS_TOKEN_SECRET")

    missing = []
    if not api_key: missing.append("TWITTER_API_KEY")
    if not api_secret: missing.append("TWITTER_API_SECRET")
    if not access_token: missing.append("TWITTER_ACCESS_TOKEN")
    if not access_token_secret: missing.append("TWITTER_ACCESS_TOKEN_SECRET")

    if missing:
        raise ValueError(f"Missing required Twitter/X API credentials in environment: {', '.join(missing)}")

    client = tweepy.Client(
        consumer_key=api_key,
        consumer_secret=api_secret,
        access_token=access_token,
        access_token_secret=access_token_secret
    )

    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api_v1 = tweepy.API(auth)

    return client, api_v1


def parse_datetime_wat(dt_str):
    """Parse 'YYYY-MM-DD HH:MM:SS' string into WAT aware datetime."""
    dt = datetime.strptime(dt_str.strip(), "%Y-%m-%d %H:%M:%S")
    return dt.replace(tzinfo=WAT_TZ)


def read_posts():
    """Read posts from posts.csv."""
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found.")

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def save_posts(posts, fieldnames):
    """Write posts back to posts.csv."""
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(posts)


def extract_tweet_id(status_str):
    """Extract tweet ID from status string like 'posted:123456789' or 'posted (id: 123456)'."""
    if not status_str or not status_str.startswith("posted"):
        return None
    if ":" in status_str:
        return status_str.split(":", 1)[1].strip().strip(")").strip()
    return None


def run_publisher(dry_run=False, simulate_all=False):
    """Execute the publisher pipeline."""
    load_env_file()
    now_wat = get_current_wat()
    log_message(f"Starting publisher run (dry_run={dry_run}, simulate_all={simulate_all}). Current WAT: {now_wat.strftime('%Y-%m-%d %H:%M:%S')}")

    # Gate check
    can_proceed = check_gates(dry_run=dry_run)
    if not can_proceed:
        log_message("Run aborted due to gate condition.")
        return

    posts, fieldnames = read_posts()
    post_map = {p["post_id"]: p for p in posts}

    # Identify eligible posts
    due_posts = []
    for p in posts:
        status = p.get("status", "pending")
        if status.lower() == "pending":
            try:
                dt_wat = parse_datetime_wat(p["datetime_wat"])
                if simulate_all or now_wat >= dt_wat:
                    due_posts.append(p)
            except Exception as e:
                log_message(f"Error parsing date for post {p.get('post_id')}: {e}")

    log_message(f"Found {len(due_posts)} pending posts due for publication.")

    if not due_posts:
        log_message("No posts due at this time. Finished run.")
        return

    # Initialize client if not dry_run
    client, api_v1 = None, None
    if not dry_run:
        try:
            client, api_v1 = get_twitter_clients()
            log_message("Twitter API v2 client initialized successfully.")
        except Exception as e:
            log_message(f"AUTHENTICATION ERROR: Failed to initialize Twitter API client: {e}")
            log_message("Will retry on next scheduled run.")
            return

    published_count = 0

    for p in due_posts:
        post_id = p["post_id"]
        text = p["text"]
        media_path = p.get("media_path", "").strip()
        parent_id = p.get("thread_parent_id", "").strip()

        # Handle thread parent dependency
        in_reply_to_tweet_id = None
        if parent_id:
            parent_post = post_map.get(parent_id)
            if not parent_post:
                log_message(f"ERROR: Parent post {parent_id} not found in posts.csv for {post_id}. Skipping.")
                continue

            parent_tweet_id = extract_tweet_id(parent_post.get("status", ""))
            if not parent_tweet_id:
                if dry_run:
                    log_message(f"[DRY-RUN] Post {post_id} is reply to {parent_id} (parent not yet posted). Simulated in thread.")
                    in_reply_to_tweet_id = "SIMULATED_PARENT_ID"
                else:
                    log_message(f"Post {post_id} is child of {parent_id}, but parent is not yet marked 'posted:<id>'. Skipping until parent is posted.")
                    continue
            else:
                in_reply_to_tweet_id = parent_tweet_id

        if dry_run:
            media_info = f" [Media: {media_path}]" if media_path else ""
            reply_info = f" [Reply to Tweet ID: {in_reply_to_tweet_id}]" if in_reply_to_tweet_id else ""
            log_message(f"[DRY-RUN WOULD POST] {post_id} ({p['datetime_wat']}){media_info}{reply_info}:\n\"{text}\"")
            published_count += 1
            # In dry-run, if part of a thread, assign a simulated ID to in-memory map
            p["status"] = f"posted:SIM_{post_id}"
            continue

        # Live publishing
        try:
            media_ids = None
            if media_path:
                if os.path.exists(media_path):
                    log_message(f"Uploading media '{media_path}' via X API v1.1...")
                    upload_res = api_v1.media_upload(media_path)
                    media_ids = [upload_res.media_id]
                    log_message(f"Media uploaded successfully. Media ID: {upload_res.media_id}")
                else:
                    log_message(f"WARNING: Media path '{media_path}' not found on disk. Posting text only.")

            # Create tweet via v2
            log_message(f"Publishing post {post_id}...")
            response = client.create_tweet(
                text=text,
                media_ids=media_ids,
                in_reply_to_tweet_id=in_reply_to_tweet_id
            )

            tweet_id = response.data["id"]
            new_status = f"posted:{tweet_id}"
            p["status"] = new_status
            published_count += 1
            log_message(f"SUCCESS: Published {post_id} -> Tweet ID: {tweet_id}")

            # Persist status immediately to prevent duplicate posting
            save_posts(posts, fieldnames)

        except tweepy.errors.TooManyRequests as e:
            log_message(f"RATE LIMIT EXCEEDED on post {post_id}: {e}. Halting current run. Will resume next run.")
            break
        except tweepy.errors.Unauthorized as e:
            log_message(f"AUTH ERROR on post {post_id}: {e}. Please check Twitter API credentials.")
            break
        except tweepy.errors.Forbidden as e:
            log_message(f"FORBIDDEN ERROR on post {post_id}: {e}. Skipping post to prevent loop.")
            p["status"] = f"failed:{e}"
            save_posts(posts, fieldnames)
        except Exception as e:
            log_message(f"UNEXPECTED ERROR on post {post_id}: {e}. Will retry on next run.")
            break

    log_message(f"Publisher run finished. Processed {published_count} post(s).")


def main():
    parser = argparse.ArgumentParser(description="Publish scheduled posts to X.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate publishing without calling live API")
    parser.add_argument("--simulate-all", action="store_true", help="Simulate entire campaign of 50 posts regardless of current time")
    args = parser.parse_args()

    run_publisher(dry_run=args.dry_run or args.simulate_all, simulate_all=args.simulate_all)


if __name__ == "__main__":
    main()
