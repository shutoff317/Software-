import json
import os
from bs4 import BeautifulSoup
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
DATA_FILE = "posted_jobs.json"

print(
    f"Token Loaded: {'Yes' if TELEGRAM_BOT_TOKEN else 'No'}, Channel ID:"
    f" {TELEGRAM_CHANNEL_ID}"
)


def load_posted_jobs():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r") as f:
        data = json.load(f)
        print(f"Loaded {len(data)} already posted jobs from JSON.")
        return data
    except Exception as e:
      print(f"Error reading JSON: {e}")
      return []
  print("JSON file nahi mili, nayi banegi.")
  return []


def save_posted_jobs(posted_jobs):
  with open(DATA_FILE, "w") as f:
    json.dump(posted_jobs, f, indent=4)


def send_to_telegram(title, link, snippet):
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
    print("❌ ERROR: Telegram Token ya Channel ID missing hai!")
    return False

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
  print(f"Telegram API Response Status: {response.status_code}")
  if response.status_code != 200:
    print(f"Telegram Error Details: {response.text}")
    return False
  return True


def fetch_and_post_vacancies():
  blog_url = "https://coursecertificate231.blogspot.com/"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      )
  }

  print(f"Fetching from {blog_url}...")
  response = requests.get(blog_url, headers=headers)
  print(f"Blog Website Status Code: {response.status_code}")

  if response.status_code != 200:
    print("Website load nahi hui.")
    return

  soup = BeautifulSoup(response.text, "html.parser")

  # Blogspot ke alag-alag possible tags check karte hain
  posts = soup.find_all("article", class_="hentry")
  if not posts:
    posts = soup.find_all("div", class_="post-outer")
  if not posts:
    posts = soup.find_all("div", class_="post")

  print(f"Total posts found on page: {len(posts)}")

  if not posts:
    print("❌ Koi posts nahi mile! HTML structure match nahi ho raha.")
    return

  posted_jobs = load_posted_jobs()
  new_posts_found = False

  for index, post in enumerate(posts[:5]):
    title_tag = (
        post.find("h2", class_="entry-title")
        or post.find("h3", class_="post-title")
        or post.find("a", class_="timestamp-link")
    )

    link_tag = post.find("a")
    if title_tag and title_tag.find("a"):
      title = title_tag.find("a").text.strip()
      link = title_tag.find("a")["href"]
    elif link_tag:
      title = link_tag.text.strip() or "Job Vacancy"
      link = link_tag["href"]
    else:
      print(f"Post #{index+1}: Title ya link nahi mila, skip kar rahe hain.")
      continue

    print(f"Checking Post: {title} | Link: {link}")

    if link not in posted_jobs:
      snippet_tag = post.find("div", class_="post-snippet") or post.find(
          "div", class_="entry-content"
      )
      snippet = (
          snippet_tag.text.strip()[:120] + "..." if snippet_tag else ""
      )

      print(f"-> Nayi job mili! Telegram par bhej rahe hain: {title}")
      if send_to_telegram(title, link, snippet):
        posted_jobs.append(link)
        new_posts_found = True
    else:
      print("-> Yeh job pehle se posted_jobs.json mein hai, skip kiya.")

  if new_posts_found:
    save_posted_jobs(posted_jobs)
    print("✅ JSON file successfully updated.")
  else:
    print("ℹ️ Koi nayi vacancy nahi mili (sab pehle se posted hain).")


if __name__ == "__main__":
  fetch_and_post_vacancies()
