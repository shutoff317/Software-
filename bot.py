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

  # Yahan status code print karwayein taaki error dikhe
  print(f"Response Status Code: {response.status_code}")

  if response.status_code != 200:
    print(
        f"Website load nahi hui. Error text (agar koi ho):"
        f" {response.text[:200]}"
    )
    return

  soup = BeautifulSoup(response.text, "html.parser")
  posts = soup.find_all("article", class_="hentry") or soup.find_all(
      "div", class_="post-outer"
  )

  if not posts:
    print("Koi posts nahi mile. HTML structure alag ho sakta hai.")
    print(
        "Page HTML preview:"
        f" {soup.text[:300]}"
    )  # Check karne ke liye ki page khula ya nahi
    return

  # Baaki ka code waisa hi rahega...
