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

  # Yahan print karke check karein ki Telegram kya bol raha hai
  print(f"Telegram Response Code: {response.status_code}")
  print(f"Telegram Response Text: {response.text}")

  return response.status_code == 200
