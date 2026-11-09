"""Telegram bot: aapki website se company/job ki heading uthata hai,
aur har post me apply link hamesha aapka blog link lagata hai."""
import os, json, time, hashlib, html
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"].strip()
SITE_URL = os.getenv("SITE_URL", "https://coursecertificate231.blogspot.com/")
APPLY_LINK = os.getenv("APPLY_LINK", "https://coursecertificate231.blogspot.com/2026/11/latest-jobs-in-india-2026-fresher-it.html")
CARD_SELECTOR = os.getenv("SITE_CARD_SELECTOR", "").strip()   # optional
MAX_POSTS = int(os.getenv("MAX_POSTS_PER_RUN", "5"))
STATE_FILE = "posted.json"

SKIP = {"it", "non-it", "government", "india", "world", "india + world", "work from home",
        "all categories", "all companies", "all work modes", "show more jobs",
        "loading jobs...", "sources loading...", "pages", "blog archive", "followers",
        "labels", "about me", "report abuse", "popular posts", "search this blog",
        "contact form", "subscribe", "menu", "home"}


def headings_from_feed():
    """Agar jobs Blogger posts hain to unke titles."""
    try:
        r = requests.get(SITE_URL.rstrip("/") + "/feeds/posts/default",
                         params={"alt": "json", "max-results": 30}, timeout=25)
        r.raise_for_status()
        return [e["title"]["$t"].strip() for e in r.json()["feed"].get("entry", [])]
    except Exception as e:
        print("[info] feed not usable:", e)
        return []


def headings_from_browser():
    """Page JavaScript se jobs load karta hai, isliye real browser se padhte hain."""
    from playwright.sync_api import sync_playwright
    js = """([sel, skip]) => {
      const skipSet = new Set(skip);
      const out = [];
      const nodes = sel
        ? document.querySelectorAll(sel)
        : document.querySelectorAll('h1,h2,h3,h4,h5,.job-title,[class*=title],[class*=company]');
      nodes.forEach(n => {
        if (n.closest('nav,header,footer,select,button,label,option')) return;
        let t = (n.innerText || '').trim().split('\\n')[0].trim();
        const l = t.toLowerCase();
        if (t.length < 6 || t.length > 140) return;
        if (skipSet.has(l) || l.startsWith('latest jobs') || l.includes('loading')) return;
        out.push(t);
      });
      return out;
    }"""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto(SITE_URL, wait_until="networkidle", timeout=60000)
        pg.wait_for_timeout(6000)
        for _ in range(2):                       # "Show more jobs"
            try:
                pg.get_by_text("Show more jobs").click(timeout=3000)
                pg.wait_for_timeout(2500)
            except Exception:
                break
        body = pg.inner_text("body")
        if "unusual traffic" in body.lower():
            print("[warn] Google ne captcha diya (GitHub server IP block)")
            b.close()
            return []
        found = pg.evaluate(js, [CARD_SELECTOR, sorted(SKIP)])
        if not found:                            # debug: page par kya dikha
            print("[debug] page text:\n", pg.inner_text("body")[:1500])
        b.close()
    return found



def headings_from_apis():
    """Site block ho to wahi public job APIs se seedha headings."""
    heads = []
    def fetch(url):
        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=25)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"[warn] {url[:50]} failed: {e}")
            return {}
    heads += [j.get("title", "") for j in fetch("https://remotive.com/api/remote-jobs?limit=40").get("jobs", [])]
    heads += [j.get("title", "") for j in fetch("https://www.arbeitnow.com/api/job-board-api").get("data", [])[:40]]
    heads += [j.get("jobTitle", "") for j in fetch("https://jobicy.com/api/v2/remote-jobs?count=30").get("jobs", [])]
    return [h.strip() for h in heads if h and len(h.strip()) >= 6]


def get_headings():
    heads = headings_from_feed()
    if not heads:
        try:
            heads = headings_from_browser()
        except Exception as e:
            print("[warn] browser mode failed:", e)
            heads = []
    if not heads:
        print("[info] site se nahi mila, APIs se le raha hoon")
        heads = headings_from_apis()
    seen, uniq = set(), []
    for h in heads:
        if h.lower() not in seen:
            seen.add(h.lower())
            uniq.append(h)
    print(f"[info] {len(uniq)} headings from site")
    for h in uniq[:15]:
        print("   -", h)
    return uniq


def key(t):
    return hashlib.sha1(t.strip().lower().encode()).hexdigest()[:16]


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except Exception:
        return []


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
    new = [h for h in get_headings() if key(h) not in seen][:MAX_POSTS]
    posted = 0
    for h in new:
        msg = (f"🏢 <b>{html.escape(html.unescape(h))}</b>\n\n"
               f"✅ Hiring now!\n"
               f"👉 <a href=\"{html.escape(APPLY_LINK)}\">Apply Here</a>")
        if send(msg):
            state.append(key(h))
            posted += 1
        time.sleep(4)
    with open(STATE_FILE, "w") as f:
        json.dump(state[-3000:], f)
    print(f"Posted {posted} jobs")


if __name__ == "__main__":
    main()
