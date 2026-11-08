"""Telegram Job Bot - India IT + Non-IT + WFH jobs, auto-post via GitHub Actions."""
import os, json, time, hashlib, html, random
import requests
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]          # @channelname ya -100xxxxxxxxxx
ADZUNA_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_KEY = os.getenv("ADZUNA_APP_KEY", "")
BLOG_URL = os.getenv("BLOG_URL", "https://coursecertificate231.blogspot.com/")
FRESHERS_CHANNEL = os.getenv("FRESHERS_CHANNEL", "Freshers_job_updates_by_akhila")
MAX_POSTS = int(os.getenv("MAX_POSTS_PER_RUN", "8"))
SITE_URL = os.getenv("SITE_URL", "https://coursecertificate231.blogspot.com/")
SITE_CARD_SELECTOR = os.getenv("SITE_CARD_SELECTOR", "")   # optional CSS selector of one job card
STATE_FILE = "posted.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (JobBot)"}

IT_QUERIES = ["software developer", "python developer", "web developer",
              "data analyst", "java developer", "fresher software"]
NON_IT_QUERIES = ["accountant", "sales executive", "hr executive",
                  "customer support", "bank", "teacher", "digital marketing"]


def get(url, **kw):
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, **kw)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"[warn] {url[:60]} failed: {e}")
        return None


# ---------- SOURCES ----------
def src_adzuna():
    """India jobs (IT + Non-IT). Free key: developer.adzuna.com"""
    if not (ADZUNA_ID and ADZUNA_KEY):
        print("[info] Adzuna keys not set, skipping")
        return []
    jobs = []
    for tag, queries in (("IT", IT_QUERIES), ("Non-IT", NON_IT_QUERIES)):
        for q in queries:
            r = get("https://api.adzuna.com/v1/api/jobs/in/search/1",
                    params={"app_id": ADZUNA_ID, "app_key": ADZUNA_KEY,
                            "results_per_page": 5, "what": q,
                            "sort_by": "date", "max_days_old": 3})
            if not r:
                continue
            for j in r.json().get("results", []):
                jobs.append({"title": j.get("title", ""),
                             "company": (j.get("company") or {}).get("display_name", "N/A"),
                             "location": (j.get("location") or {}).get("display_name", "India"),
                             "url": j.get("redirect_url", ""), "tag": tag})
    return jobs


def src_remotive():
    r = get("https://remotive.com/api/remote-jobs", params={"limit": 40})
    jobs = []
    if r:
        for j in r.json().get("jobs", []):
            loc = j.get("candidate_required_location", "")
            if any(k in loc.lower() for k in ("india", "worldwide", "anywhere", "asia")):
                jobs.append({"title": j["title"], "company": j.get("company_name", "N/A"),
                             "location": f"Remote ({loc})", "url": j["url"], "tag": "WFH"})
    return jobs


def src_jobicy():
    r = get("https://jobicy.com/api/v2/remote-jobs", params={"count": 30, "geo": "india"})
    jobs = []
    if r:
        for j in r.json().get("jobs", []):
            jobs.append({"title": j.get("jobTitle", ""), "company": j.get("companyName", "N/A"),
                         "location": f"Remote ({j.get('jobGeo', 'India')})",
                         "url": j.get("url", ""), "tag": "WFH"})
    return jobs


def src_freshers_channel():
    """Public channel preview se sirf apply links (title/text nahi)."""
    r = get(f"https://t.me/s/{FRESHERS_CHANNEL}")
    jobs = []
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for msg in soup.select(".tgme_widget_message_text")[-15:]:
            for a in msg.find_all("a", href=True):
                href = a["href"]
                if href.startswith("http") and "t.me" not in href:
                    jobs.append({"title": "", "company": "", "location": "",
                                 "url": href, "tag": "Fresher"})
    return jobs



def src_my_site():
    """Aapki website se jobs: pehle Blogger feed, phir browser se JS-rendered page."""
    jobs = []
    base = SITE_URL.rstrip("/")
    # 1) Blogger feed (agar jobs posts ki tarah hain)
    r = get(f"{base}/feeds/posts/default", params={"alt": "json", "max-results": 25})
    if r:
        try:
            for e in r.json()["feed"].get("entry", []):
                link = next((l["href"] for l in e["link"] if l["rel"] == "alternate"), "")
                if link:
                    jobs.append({"title": e["title"]["$t"], "company": "", "location": "",
                                 "url": link, "tag": "Job"})
        except Exception as ex:
            print("[warn] feed parse:", ex)
    if jobs:
        print(f"[info] site feed: {len(jobs)} jobs")
        return jobs
    # 2) Page JavaScript se load hota hai -> headless browser
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[info] playwright not installed, site skipped")
        return []
    js = """(sel) => {
      const out = [];
      const bad = /blogspot\\.com|blogger\\.com|google\\./i;
      if (sel) {
        document.querySelectorAll(sel).forEach(c => {
          const a = c.querySelector('a[href^=http]');
          if (!a) return;
          const t = (c.querySelector('h1,h2,h3,h4,.title') || a).innerText.trim();
          out.push({title: t.split('\\n')[0], url: a.href, text: c.innerText});
        });
      } else {
        document.querySelectorAll('a[href^=http]').forEach(a => {
          const t = a.innerText.trim().split('\\n')[0];
          if (t.length >= 12 && !bad.test(a.href)) out.push({title: t, url: a.href, text: ''});
        });
      }
      return out;
    }"""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(SITE_URL, wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(5000)
        for _ in range(2):   # "Show more jobs" button
            try:
                pg.get_by_text("Show more jobs").click(timeout=3000)
                pg.wait_for_timeout(2000)
            except Exception:
                break
        data = pg.evaluate(js, SITE_CARD_SELECTOR or None)
        b.close()
    seen_u = set()
    for d in data:
        if d["url"] not in seen_u:
            seen_u.add(d["url"])
            jobs.append({"title": d["title"][:150], "company": "", "location": "",
                         "url": d["url"], "tag": "Job"})
    print(f"[info] site browser: {len(jobs)} jobs")
    return jobs[:40]


# ---------- STATE ----------
def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return []


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state[-3000:], f)


def key(url):
    return hashlib.sha1(url.strip().encode()).hexdigest()[:16]


# ---------- TELEGRAM ----------
def fmt(j):
    e = html.escape
    lines = []
    if j["title"]:
        lines.append(f"💼 <b>{e(j['title'])}</b>")
        if j["company"]:
            lines.append(f"🏢 {e(j['company'])}")
        if j["location"]:
            lines.append(f"📍 {e(j['location'])}")
    else:
        lines.append("💼 <b>New Fresher Job Opening</b>")
    lines.append(f"🏷 {j['tag']}")
    lines.append(f"\n👉 <a href=\"{e(j['url'])}\">Apply Here</a>")
    if BLOG_URL:
        lines.append(f"🌐 <a href=\"{e(BLOG_URL)}\">More Jobs &amp; Updates</a>")
    return "\n".join(lines)


def send(text):
    for _ in range(3):
        r = requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                          json={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML",
                                "disable_web_page_preview": True}, timeout=25)
        if r.status_code == 429:
            time.sleep(r.json().get("parameters", {}).get("retry_after", 10) + 1)
            continue
        if not r.ok:
            print("[error]", r.text)
        return r.ok
    return False


def main():
    state = load_state()
    seen = set(state)
    pools = [src_my_site(), src_adzuna(), src_remotive(), src_jobicy(), src_freshers_channel()]

    # alag-alag tag/source se mix karke pick karo
    fresh = []
    for p in pools:
        random.shuffle(p)
        fresh.append([j for j in p if j["url"] and key(j["url"]) not in seen])

    queue, i = [], 0
    while len(queue) < MAX_POSTS and any(fresh):
        pool = fresh[i % len(fresh)]
        if pool:
            j = pool.pop()
            if key(j["url"]) not in {key(x["url"]) for x in queue}:
                queue.append(j)
        i += 1

    posted = 0
    for j in queue:
        if send(fmt(j)):
            state.append(key(j["url"]))
            posted += 1
        time.sleep(4)
    save_state(state)
    print(f"Posted {posted} jobs")


if __name__ == "__main__":
    main()
