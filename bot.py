import json
import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
DATA_FILE = "posted_jobs.json"


def load_posted_jobs():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r") as f:
        return json.load(f)
    except:
      return []
  return []


def save_posted_jobs(posted_jobs):
  with open(DATA_FILE, "w") as f:
    json.dump(posted_jobs, f, indent=4)


def send_to_telegram(title, company, link):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  message = (
      f"🔥 <b>New Remote Job Alert!</b> 🔥\n\n"
      f"📌 <b>Role:</b> {title}\n"
      f"🏢 <b>Company:</b> {company}\n\n"
      f"🔗 <a href='{link}'>Apply Here</a>"
  )
  payload = {
      "chat_id": TELEGRAM_CHANNEL_ID,
      "text": message,
      "parse_mode": "HTML",
  }
  response = requests.post(url, json=payload)
  return response.status_code == 200


def fetch_jobs():
  api_url = "https://remoteok.com/api"
  headers = {"User-Agent": "Mozilla/5.0"}

  print("Fetching jobs from RemoteOK API...")
  response = requests.get(api_url, headers=headers)

  if response.status_code != 200:
    print(f"API Error: {response.status_code}")
    return

  jobs = response.json()
  # Pehla item metadata hota hai, isliye jobs[1:] se start karein
  job_list = jobs[1:6]

  posted_jobs = load_posted_jobs()
  new_posts_found = False

  for job in job_list:
    job_id = str(job.get("id"))
    title = job.get("position", "N/A")
    company = job.get("company", "N/A")
    apply_url = job.get("url", "N/A")

    if job_id and job_id not in posted_jobs:
      print(f"Posting new job: {title} at {company}")
      if send_to_telegram(title, company, apply_url):
        posted_jobs.append(job_id)
        new_posts_found = True

  if new_posts_found:
    save_posted_jobs(posted_jobs)
    print("JSON file updated successfully.")
  else:
    print("Koi nayi job nahi mili.")


if __name__ == "__main__":
  fetch_jobs()
