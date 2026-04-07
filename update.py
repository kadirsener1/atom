import re
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DOMAIN = "https://atomsportv494.top/"

# 🔧 Selenium
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=options)

# 📺 kanal linklerini çek
def get_channels():
    r = requests.get(DOMAIN, timeout=10)
    return list(set(re.findall(r'matches\?id=([a-zA-Z0-9\-]+)', r.text)))

# 📡 sadece m3u8 yakala
def get_m3u8(driver, cid):
    url = f"{DOMAIN}matches?id={cid}"

    driver.get(url)
    time.sleep(5)

    logs = driver.get_log("performance")

    for log in logs:
        msg = log["message"]
        if ".m3u8" in msg:
            start = msg.find("http")
            end = msg.find(".m3u8") + 5
            return msg[start:end]

    return None

# 📄 M3U yaz
def write_m3u(filename, links):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n\n")

        for i, link in enumerate(links, start=1):
            f.write(f"#EXTINF:-1, Kanal {i}\n")
            f.write(f"{link}\n\n")

# 🚀 ANA
driver = create_driver()
channels = get_channels()

found_links = []

for cid in channels:
    link = get_m3u8(driver, cid)
    if link:
        print(link)  # 🔥 SADECE LINK LOGDA
        found_links.append(link)

driver.quit()

if found_links:
    write_m3u("cafe.m3u", found_links)
else:
    print("link yok")
