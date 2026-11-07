import json
import os
from bs4 import BeautifulSoup
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
DATA_FILE = "posted_jobs.json"


def load_posted_jobs():
  """Pehle se posted jobs ki list load karna"""
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r") as f:
        return json.load(f)
    except:
      return []
  return []


def save_posted_jobs(posted_jobs):
  """Nayi job ko json file mein save karna"""
  with open(DATA_FILE, "w") as f:
    json.dump(posted_jobs, f, indent=4)


def send_to_telegram(title, link, snippet):
  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
  message = (
      f"🔥 <b>New Vacancy Alert!</b> 🔥\n\n"
      f"📌 <b>{title}</b>\n\n"
      f"{snippet}\n\n"
      f"🔗 <a href='{link}'>Apply / Read More</a>"
  )
  payload = {
      "chat_id": TELEGRAM_CHANNEL_ID,
      "text": message,
      "parse_mode": "HTML",
  }
  response = requests.post(url, json=payload)
  return response.status_code == 200


def fetch_and_post_vacancies():
  blog_url = "https://coursecertificate231.blogspot.com/"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  print(f"Fetching from {blog_url}")
  response = requests.get(blog_url, headers=headers)

  if response.status_code != 200:
    print("Website load nahi hui.")
    return

  soup = BeautifulSoup(response.text, "html.parser")
  posts = soup.find_all("article", class_="hentry") or soup.find_all(
      "div", class_="post-outer"
  )

  if not posts:
    print("Koi posts nahi mile.")
    return

  posted_jobs = load_posted_jobs()
  new_posts_found = False

  # Latest posts check karein
  for post in posts[:5]:
    title_tag = post.find("h2", class_="entry-title") or post.find(
        "h3", class_="post-title"
    )
    if title_tag and title_tag.find("a"):
      title = title_tag.find("a").text.strip()
      link = title_tag.find("a")["href"]
    else:
      continue

    # Agar yeh link pehle se posted_jobs.json mein nahi hai, toh hi post karo
    if link not in posted_jobs:
      snippet_tag = post.find("div", class_="post-snippet") or post.find(
          "div", class_="entry-content"
      )
      snippet = snippet_tag.text.strip()[:120] + "..." if snippet_tag else ""

      print(sending := f"Posting new job: {title}")
      if send_to_telegram(title, link, snippet):
        posted_jobs.append(link)  # Link ko list mein add kar diya
        new_posts_found = True

  # Agar naye posts post hue hain toh JSON file ko update karke GitHub par commit kar do
  if new_posts_found:
    save_posted_jobs(posted_jobs)
    print("Posted jobs list updated in JSON file.")
  else:
     print("Koi nayi vacancy nahi mili.")


if __name__ == "__main__":
  fetch_and_post_vacancies()
