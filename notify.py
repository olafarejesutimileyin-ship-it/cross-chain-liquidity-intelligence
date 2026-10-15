#!/usr/bin/env python3
"""
notify.py - Email Notification Engine for Portfolio Campaign Schedule
Sends the full 35-day / 50-post schedule table and pause instructions via Gmail SMTP.
"""

import os
import sys
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

CSV_FILE = "posts.csv"


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


def read_posts():
    """Read schedule from posts.csv."""
    if not os.path.exists(CSV_FILE):
        raise FileNotFoundError(f"{CSV_FILE} not found.")

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def generate_email_content(posts):
    """Generate both HTML and plain-text versions of the schedule email."""
    # Plain text version
    text_lines = [
        "=" * 80,
        "ON-CHAIN PORTFOLIO X CAMPAIGN: 5-WEEK SCHEDULE & EMERGENCY PAUSE INSTRUCTIONS",
        "=" * 80,
        "",
        "CRITICAL INSTRUCTIONS TO PAUSE POSTING:",
        "--------------------------------------------------------------------------------",
        "To stop or pause all posting at any time:",
        "Create a file named HOLD.txt in the root of the repository on github.com.",
        "The automated publisher will immediately detect HOLD.txt and refuse to publish any post.",
        "To resume posting later, simply delete HOLD.txt from the repository.",
        "--------------------------------------------------------------------------------",
        "",
        f"TOTAL SCHEDULED POSTS: {len(posts)} across 35 days (Oct 16 - Nov 19, 2026 WAT)",
        "",
        f"{'ID':<8} | {'Date (WAT)':<10} | {'Time':<8} | {'Thread Parent':<14} | Text",
        "-" * 80,
    ]

    for p in posts:
        dt_parts = p["datetime_wat"].split(" ")
        d_str = dt_parts[0]
        t_str = dt_parts[1][:5]
        parent = p["thread_parent_id"] if p["thread_parent_id"] else "-"
        text_lines.append(f"{p['post_id']:<8} | {d_str:<10} | {t_str:<8} | {parent:<14} | {p['text']}")

    plain_text = "\n".join(text_lines)

    # HTML table version
    rows_html = []
    for i, p in enumerate(posts):
        dt_parts = p["datetime_wat"].split(" ")
        d_str = dt_parts[0]
        t_str = dt_parts[1][:5]
        parent = p["thread_parent_id"]
        media = p["media_path"]

        row_bg = "#ffffff" if i % 2 == 0 else "#f8fafc"
        thread_badge = f'<span style="background:#e0e7ff;color:#3730a3;padding:2px 6px;border-radius:4px;font-size:11px;">Thread -> {parent}</span>' if parent else '<span style="color:#64748b;font-size:11px;">Standalone</span>'
        media_badge = f'<br/><span style="background:#fef3c7;color:#92400e;padding:2px 6px;border-radius:4px;font-size:11px;">{os.path.basename(media)}</span>' if media else ''

        rows_html.append(f"""
        <tr style="background-color:{row_bg}; border-bottom: 1px solid #e2e8f0;">
            <td style="padding:10px 12px; font-weight:600; color:#0f172a; white-space:nowrap; vertical-align:top;">{p['post_id']}</td>
            <td style="padding:10px 12px; color:#334155; white-space:nowrap; vertical-align:top;">{d_str}</td>
            <td style="padding:10px 12px; font-family:monospace; color:#0284c7; white-space:nowrap; vertical-align:top;">{t_str} WAT</td>
            <td style="padding:10px 12px; vertical-align:top;">{thread_badge}{media_badge}</td>
            <td style="padding:10px 12px; color:#1e293b; line-height:1.5; font-size:13px; vertical-align:top;">{p['text']}</td>
        </tr>
        """)

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Portfolio X Campaign Schedule</title>
    </head>
    <body style="font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color:#f1f5f9; margin:0; padding:24px; color:#0f172a;">
        <div style="max-width:980px; margin:0 auto; background:#ffffff; border-radius:12px; box-shadow:0 4px 6px -1px rgba(0,0,0,0.1); overflow:hidden; border:1px solid #e2e8f0;">
            
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); padding:28px 32px; color:#ffffff;">
                <h1 style="margin:0 0 8px 0; font-size:22px; font-weight:700; letter-spacing:-0.5px;">On-Chain Portfolio X Campaign Schedule</h1>
                <p style="margin:0; font-size:14px; color:#94a3b8;">5-Week Automated Schedule (Oct 16 - Nov 19, 2026 WAT) • 50 Posts Total</p>
            </div>

            <!-- Emergency Pause Card -->
            <div style="margin:24px 32px; padding:18px 22px; background-color:#fef2f2; border:2px solid #ef4444; border-radius:8px;">
                <h3 style="margin:0 0 8px 0; color:#991b1b; font-size:15px; font-weight:700;">EMERGENCY PAUSE PROCEDURE</h3>
                <p style="margin:0 0 10px 0; font-size:14px; color:#7f1d1d; line-height:1.5;">
                    To stop or pause all posting immediately at any time:
                </p>
                <div style="background:#ffffff; padding:10px 14px; border-radius:6px; font-family:monospace; font-size:13px; color:#b91c1c; border:1px dashed #f87171; font-weight:600;">
                    create a file named HOLD.txt in the repo on github.com to stop all posting
                </div>
                <p style="margin:10px 0 0 0; font-size:13px; color:#7f1d1d;">
                    The publisher automatically checks for <code>HOLD.txt</code> before every run and refuses to post when it exists. To resume posting, simply delete <code>HOLD.txt</code>.
                </p>
            </div>

            <!-- Schedule Summary -->
            <div style="padding:0 32px 16px 32px;">
                <div style="display:flex; gap:16px; margin-bottom:16px;">
                    <div style="flex:1; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px 18px;">
                        <div style="font-size:11px; text-transform:uppercase; color:#64748b; font-weight:700;">Duration</div>
                        <div style="font-size:16px; font-weight:700; color:#0f172a; margin-top:4px;">35 Days (5 Weeks)</div>
                    </div>
                    <div style="flex:1; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px 18px;">
                        <div style="font-size:11px; text-transform:uppercase; color:#64748b; font-weight:700;">Total Posts</div>
                        <div style="font-size:16px; font-weight:700; color:#0f172a; margin-top:4px;">50 Posts</div>
                    </div>
                    <div style="flex:1; background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:14px 18px;">
                        <div style="font-size:11px; text-transform:uppercase; color:#64748b; font-weight:700;">Max Slots / Day</div>
                        <div style="font-size:16px; font-weight:700; color:#0f172a; margin-top:4px;">Max 2 (Thread = 1)</div>
                    </div>
                </div>

                <h3 style="margin:24px 0 12px 0; font-size:16px; font-weight:700; color:#0f172a;">Full Campaign Schedule</h3>
                <div style="overflow-x:auto; border:1px solid #e2e8f0; border-radius:8px;">
                    <table style="width:100%; border-collapse:collapse; text-align:left; font-size:13px;">
                        <thead>
                            <tr style="background:#f1f5f9; border-bottom:2px solid #cbd5e1; color:#475569; font-weight:700; font-size:12px; text-transform:uppercase;">
                                <th style="padding:10px 12px;">ID</th>
                                <th style="padding:10px 12px;">Date (WAT)</th>
                                <th style="padding:10px 12px;">Time</th>
                                <th style="padding:10px 12px;">Format</th>
                                <th style="padding:10px 12px;">Post Text</th>
                            </tr>
                        </thead>
                        <tbody>
                            {"".join(rows_html)}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Footer -->
            <div style="background:#f8fafc; border-top:1px solid #e2e8f0; padding:20px 32px; font-size:12px; color:#64748b; text-align:center;">
                Cross-Chain Liquidity Acquisition Intelligence • Automated Unattended Campaign • West Africa Time (UTC+1)
            </div>
        </div>
    </body>
    </html>
    """

    return plain_text, html_content


def send_notification_email():
    """Send the schedule notification email via Gmail SMTP."""
    load_env_file()

    smtp_user = os.getenv("SMTP_USER") or os.getenv("GMAIL_ADDRESS")
    smtp_pass = os.getenv("SMTP_APP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD")
    notify_email = os.getenv("NOTIFY_EMAIL") or os.getenv("GMAIL_ADDRESS") or "olafarejesutimileyin@gmail.com"

    if not smtp_user or not smtp_pass:
        raise ValueError("Missing SMTP_USER or SMTP_APP_PASSWORD in environment.")

    # Remove any internal spaces in app passwords (e.g. 'ztpu nncd wvsj szlo' -> 'ztpunncdwvsjszlo')
    clean_pass = smtp_pass.replace(" ", "")

    posts = read_posts()
    plain_text, html_content = generate_email_content(posts)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Portfolio X Campaign Schedule: 50 Posts (35 Days) & Pause Instructions"
    msg["From"] = f"Campaign Automation <{smtp_user}>"
    msg["To"] = notify_email

    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    print(f"Connecting to Gmail SMTP to send notification to {notify_email}...")

    # Connect via SSL port 465, with fallback to 587
    sent = False
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as server:
            server.login(smtp_user, clean_pass)
            server.send_message(msg)
            sent = True
            print(f"Email successfully delivered via SMTP_SSL (port 465) to {notify_email}!")
    except Exception as e_ssl:
        print(f"SMTP_SSL (port 465) attempt failed: {e_ssl}. Retrying with STARTTLS (port 587)...")
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, clean_pass)
            server.send_message(msg)
            sent = True
            print(f"Email successfully delivered via STARTTLS (port 587) to {notify_email}!")

    return sent


if __name__ == "__main__":
    try:
        success = send_notification_email()
        if success:
            print("Notification workflow completed successfully.")
            sys.exit(0)
        else:
            print("Failed to send notification email.")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
