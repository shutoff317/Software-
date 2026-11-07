import os
from bs4 import BeautifulSoup
import requests

# Environment Variables se credentials uthayenge
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")  # Jaise: @myjobchannel


def send_to_telegram(title, link, snippet):
  if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID:
    print("Telegram credentials missing!")
    return

  url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

  # Message format jo Telegram channel par dikhega
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
      "disable_web_page_preview": False,
  }

  response = requests.post(url, json=payload)
  if response.status_code == 200:
    print(f"Successfully posted: {title}")
  else:
    print(f"Failed to post: {response.text}")


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

  if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")

    # Blogspot ke posts target karein
    posts = soup.find_all("article", class_="hentry") or soup.find_all(
        "div", class_="post-outer"
    )

    if not posts:
      print("Koi posts nahi mile.")
      return

    # Sirf latest top 3 posts uthayenge taaki spam na ho
    for post in posts[:3]:
      title_tag = post.find("h2", class_="entry-title") or post.find(
          "h3", class_="post-title"
      )
      if title_tag and title_tag.find("a"):
        title = title_tag.find("a").text.strip()
        link = title_tag.find("a")["href"]
      else:
        continue

      snippet_tag = post.find("div", class_="post-snippet") or post.find(
          "div", class_="entry-content"
      )
      snippet = (
          snippet_tag.text.strip()[:120] + "..." if snippet_tag else ""
      )

      # Telegram par bhein
      send_to_telegram(title, link, snippet)
  else:
    print(f"Website load nahi hui. Status code: {response.status_code}")


if __name__ == "__main__":
  fetch_and_post_vacancies()
