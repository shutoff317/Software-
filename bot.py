import os, json, html, requests

BLOG_URL = os.environ.get("BLOG_URL", "https://applyfresherjob.blogspot.com").rstrip("/")
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]          # e.g. @your_channel
MAX_PER_RUN = 5                          # ek baar me max itni posts
FIRST_RUN_POSTS = 3                      # pehli baar sirf latest itni bhejo
STATE_FILE = "posted.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f), False
    return [], True

def fetch_posts():
    url = f"{BLOG_URL}/feeds/posts/default?alt=json&max-results=20"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    posts = []
    for e in r.json()["feed"].get("entry", []):
        link = next(l["href"] for l in e["link"] if l["rel"] == "alternate")
        posts.append({"id": e["id"]["$t"], "title": e["title"]["$t"], "link": link})
    return posts  # newest first

def send(post):
    text = f"💼 <b>{html.escape(post['title'])}</b>\n\n👉 Apply: {post['link']}"
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=30,
    )
    r.raise_for_status()

def main():
    seen, first_run = load_state()
    posts = fetch_posts()
    new = [p for p in posts if p["id"] not in seen]

    if first_run:
        to_send = list(reversed(new[:FIRST_RUN_POSTS]))
    else:
        to_send = list(reversed(new))[:MAX_PER_RUN]

    for p in to_send:
        send(p)
        print("Sent:", p["title"])

    sent_ids = {p["id"] for p in to_send}
    # first run me baaki purani posts ko bhi seen mark karo
    mark = [p["id"] for p in (new if first_run else to_send)]
    seen = list(dict.fromkeys(seen + mark))[-500:]
    with open(STATE_FILE, "w") as f:
        json.dump(seen, f)

if __name__ == "__main__":
    main()
