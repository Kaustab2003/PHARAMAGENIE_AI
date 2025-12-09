# save as download_rolls.py
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import requests

# configure
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
URL = "https://ceowestbengal.wb.gov.in/Roll_ps/186"

# start Chrome
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(options=options)  # ensure chromedriver on PATH

driver.get(URL)

print("Please solve the CAPTCHA in the opened browser. After solving, press Enter here to continue...")
input()

time.sleep(1)  # small delay after manual solve

# Example: locate all links that look like final roll PDFs (adjust selector to site)
# Try common selectors: links containing ".pdf" or containing "Final Roll" text
anchors = driver.find_elements(By.TAG_NAME, "a")
pdf_urls = []
for a in anchors:
    href = a.get_attribute("href")
    text = (a.text or "").lower()
    if href and (href.lower().endswith(".pdf") or "final" in text or "roll" in text):
        pdf_urls.append(href)

pdf_urls = list(dict.fromkeys(pdf_urls))  # unique
print(f"Found {len(pdf_urls)} candidate URLs")

# Use session cookies from selenium to download via requests (so session is preserved)
s = requests.Session()
for c in driver.get_cookies():
    s.cookies.set(c['name'], c['value'], domain=c.get('domain'))

for i, url in enumerate(pdf_urls, 1):
    try:
        print(f"Downloading {i}/{len(pdf_urls)}: {url}")
        r = s.get(url, stream=True, timeout=60)
        if r.status_code == 200:
            fname = os.path.join(DOWNLOAD_DIR, url.split("/")[-1].split("?")[0] or f"file_{i}.pdf")
            with open(fname, "wb") as f:
                for chunk in r.iter_content(1024*8):
                    if chunk:
                        f.write(chunk)
            print("Saved:", fname)
        else:
            print("Failed:", r.status_code, url)
    except Exception as e:
        print("Error downloading", url, e)

driver.quit()
print("Done.")

