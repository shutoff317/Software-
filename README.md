# Telegram Job Bot (India IT + Non-IT + WFH)

Har 3 ghante me GitHub Actions bot chalata hai aur naye jobs Telegram me post karta hai. Duplicate jobs `posted.json` se rokte hain.

## Setup
1. @BotFather se bot banao -> token lo. Bot ko apne channel/group me **admin** banao.
2. Chat ID: public channel ho to `@channelname`, warna `-100...` ID.
3. (Recommended) https://developer.adzuna.com se free API key lo - India ke IT + Non-IT jobs isi se aate hain.
4. GitHub repo -> Settings -> Secrets and variables -> Actions -> add:
   - `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY`
5. Actions tab -> "Post Jobs to Telegram" -> **Run workflow** (test).

## Sources
Adzuna India, Remotive, Jobicy (WFH), aur public Telegram channel se sirf apply links.

## Apni website se jobs (SITE_URL)
Bot pehle `SITE_URL/feeds/posts/default` (Blogger feed) try karta hai. Agar jobs JavaScript se load hoti hain to headless Chromium (Playwright) se page render karke job links nikalta hai. Agar galat links aaye to workflow me `SITE_CARD_SELECTOR` env (ek job card ka CSS selector, jaise `.job-card`) set karo.
Adzuna keys optional hain - na ho to skip ho jata hai.
