import re
import time
import os
import requests
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DOMAIN = "https://atomsportv494.top/"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# 🔧 Selenium driver
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=options)

# 📺 Kanal listesi çek
def get_channels():
    r = requests.get(DOMAIN, headers=HEADERS, timeout=10)
    ids = re.findall(r'matches\?id=([a-zA-Z0-9\-]+)', r.text)
    unique_ids = list(set(ids))
    print(f"📺 {len(unique_ids)} kanal bulundu")
    return unique_ids

# 📡 m3u8 yakala
def get_m3u8(driver, cid):
    try:
        url = urljoin(DOMAIN, f"matches?id={cid}")
        print(f"🔍 {cid}")

        driver.get(url)
        time.sleep(6)

        logs = driver.get_log("performance")

        for log in logs:
            msg = log["message"]
            if ".m3u8" in msg:
                start = msg.find("http")
                end = msg.find(".m3u8") + 5
                link = msg[start:end]
                print(f"✅ bulundu: {cid}")
                return link

        print(f"❌ bulunamadı: {cid}")

    except Exception as e:
        print(f"⚠️ hata: {cid} - {e}")

    return None

# ✍️ M3U GÜNCELLE (DÜZELTİLMİŞ)
def update_m3u(filename, new_links, referer):
    lines = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    updated_lines = []
    existing_ids = set()
    i = 0

    while i < len(lines):
        line = lines[i]
        updated_lines.append(line)

        if line.startswith("#EXTINF") and 'tvg-id="' in line:
            match = re.search(r'tvg-id="([^"]+)"', line)
            if match:
                cid = match.group(1)
                existing_ids.add(cid)

                if cid in new_links:
                    new_url = new_links[cid]

                    # eski url satırını atla
                    j = i + 1
                    if j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                        i += 1
                        j += 1
                    if j < len(lines) and lines[j].startswith("http"):
                        i += 1

                    # yeni url ekle
                    updated_lines.append(f"#EXTVLCOPT:http-referrer={referer}")
                    updated_lines.append(new_url)
                    continue

        i += 1

    # eksik kanalları ekle
    for cid, url in new_links.items():
        if cid not in existing_ids:
            print(f"➕ yeni eklendi: {cid}")
            updated_lines.append(f"#EXTINF:-1 tvg-id=\"{cid}\",{cid}")
            updated_lines.append(f"#EXTVLCOPT:http-referrer={referer}")
            updated_lines.append(url)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(updated_lines))

    print("✅ M3U tamamen güncellendi")

# 🚀 ANA AKIŞ
channels = get_channels()

driver = create_driver()

found_links = {}

for cid in channels:
    link = get_m3u8(driver, cid)
    if link:
        found_links[cid] = link

driver.quit()

if found_links:
    update_m3u("cafe.m3u", found_links, DOMAIN)
else:
    print("❌ hiç link bulunamadı")
