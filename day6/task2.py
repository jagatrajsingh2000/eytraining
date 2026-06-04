# -*- coding: utf-8 -*-
"""Day 6 Task 2: Python Automation Tools."""

# Install required libraries if needed:
# pip install requests beautifulsoup4 schedule apscheduler watchdog

import argparse
import csv
import logging
import os
import shutil
import subprocess
import time
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
import smtplib

import requests
import schedule
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).parent
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"
QUOTES_CSV = BASE_DIR / "quotes.csv"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("Python automation project started")


# ============================================
# FILE ORGANIZER AUTOMATION
# ============================================

EXT_MAP = {
    ".pdf": "PDFs",
    ".jpg": "Images",
    ".png": "Images",
    ".csv": "Data",
    ".xlsx": "Data",
    ".mp4": "Videos",
}


def organise(folder):
    src = Path(folder)
    src.mkdir(exist_ok=True)

    for file in src.iterdir():
        if file.is_file():
            destination = src / EXT_MAP.get(file.suffix.lower(), "Other")
            destination.mkdir(exist_ok=True)
            shutil.move(str(file), destination / file.name)
            print(f"Moved {file.name} -> {destination.name}/")


# ============================================
# WEB SCRAPING AUTOMATION
# ============================================

def scrape_quotes():
    url = "https://quotes.toscrape.com"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    quotes = []

    for quote in soup.select(".quote")[:5]:
        quotes.append(
            {
                "text": quote.find("span", class_="text").text,
                "author": quote.find("small").text,
                "scraped_at": datetime.now().isoformat(),
            }
        )

    return quotes


# ============================================
# SAVE DATA TO CSV
# ============================================

def save_to_csv(rows, path=QUOTES_CSV):
    file_exists = os.path.isfile(path)

    with open(path, "a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["text", "author", "scraped_at"],
        )

        if not file_exists:
            writer.writeheader()

        writer.writerows(rows)

    print(f"Saved {len(rows)} rows into {path}")


# ============================================
# EMAIL AUTOMATION
# ============================================

def send_alert(subject, body, to, gmail_user, app_password):
    try:
        msg = MIMEText(body)

        msg["Subject"] = subject
        msg["From"] = gmail_user
        msg["To"] = to

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, app_password)
            server.send_message(msg)

        print("Email sent successfully.")

    except Exception as error:
        print("Email failed.")
        print("Error:", error)


# ============================================
# SCHEDULED AUTOMATION JOBS
# ============================================

def job_scrape():
    data = scrape_quotes()
    save_to_csv(data)
    print(f"[{datetime.now():%H:%M:%S}] Scraping completed")


def job_report():
    print(f"[{datetime.now():%H:%M:%S}] Daily report generated")


# ============================================
# ARGPARSE EXAMPLE
# ============================================

def argparse_example():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--name",
        type=str,
        default="jagat",
    )

    args = parser.parse_args(args=[])

    print(f"Hello, {args.name}")


# ============================================
# SUBPROCESS EXAMPLE
# ============================================

def subprocess_example():
    result = subprocess.run(
        ["ls", str(BASE_DIR)],
        capture_output=True,
        text=True,
        check=False,
    )

    print("Subprocess Output:\n")
    print(result.stdout)


# ============================================
# CRON EXAMPLE
# ============================================

def cron_example():
    cron_expression = "0 8 * * *"

    print("Cron Schedule Example:")
    print(f"Runs daily at 08:00 AM -> {cron_expression}")


# ============================================
# MAIN PROGRAM
# ============================================

def main():
    organise(SAMPLE_DATA_DIR)

    data = scrape_quotes()
    save_to_csv(data)

    schedule.every(10).seconds.do(job_scrape)
    schedule.every().day.at("08:00").do(job_report)

    print("Scheduler Started...")

    end_time = time.time() + 35

    while time.time() < end_time:
        schedule.run_pending()
        time.sleep(1)

    print("Scheduler Stopped.")

    scheduler = BackgroundScheduler()

    scheduler.add_job(
        job_scrape,
        trigger="interval",
        seconds=15,
        id="scraper_job",
    )

    scheduler.add_job(
        job_report,
        CronTrigger(day_of_week="mon-fri", hour=7, minute=30),
        id="daily_report_job",
    )

    scheduler.start()

    print("APScheduler Running...\n")

    for job in scheduler.get_jobs():
        print(f"Job ID: {job.id}")
        print(f"Next Run Time: {job.next_run_time}\n")

    time.sleep(40)

    scheduler.shutdown()

    print("APScheduler Stopped.")
    print("\nPython Automation Project Completed Successfully.")

    argparse_example()
    subprocess_example()
    cron_example()


if __name__ == "__main__":
    main()
