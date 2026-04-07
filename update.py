import re
import time
import os
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 🔧 selenium ayar
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# 🔎 m3u8 bul
def extract_m3u8(html):
    match = re.search(r'https?://[^"\']+\.m3u8', html)
    return match.group(0) if match else None

# 📡 kanal linkini al
def get_stream(driver, domain, cid):
    try:
        url = urljoin(domain, f"matches?id={cid}")
        print(f"🔍 {cid}")

        driver.get(url)
        time.sleep(5)

        html = driver.page_source
        m3u8 = extract_m3u8(html)

        if m3u8:
            print(f"✅ bulundu: {cid}")
            return m3u8
        else:
            print(f"❌ bulunamadı: {cid}")

    except Exception as e:
        print(f"⚠️ hata: {cid} - {e}")

    return None

# ✍️ M3U güncelle
def update_m3u(filename, new_links, referer):
    if not os.path.exists(filename):
        print("⛔ M3U yok")
        return

    with open(filename, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    updated = []
    i = 0

    while i < len(lines):
        line = lines[i]
        updated.append(line)

        if line.startswith("#EXTINF") and 'tvg-id="' in line:
            match = re.search(r'tvg-id="([^"]+)"', line)
            if match:
                cid = match.group(1)

                if cid in new_links:
                    new_url = new_links[cid]

                    j = i + 1
                    if j < len(lines) and lines[j].startswith("#EXTVLCOPT"):
                        j += 1
                    if j < len(lines):
                        old_url = lines[j]

                    if new_url != old_url:
                        print(f"🔄 güncellendi: {cid}")

                        i += 1
                        if i < len(lines) and lines[i].startswith("#EXTVLCOPT"):
                            i += 1
                        if i < len(lines) and lines[i].startswith("http"):
                            i += 1

                        updated.append(f"#EXTVLCOPT:http-referrer={referer}")
                        updated.append(new_url)
                        continue

        i += 1

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(updated))

    print("✅ M3U tamam")

# 📺 kanal listesi
channels = [
    "bein-sports-1",
    "bein-sports-2",
    "bein-sports-3",
    "bein-sports-4",
    "bein-sports-5",
    "bein-sports-max-1",
    "bein-sports-max-2",
    "s-sport",
    "s-sport-2",
    "tivibu-spor-1"
]

# 🚀 ana
domain = "https://atomsportv494.top/"

driver = create_driver()

found = {}

for ch in channels:
    link = get_stream(driver, domain, ch)
    if link:
        found[ch] = link

driver.quit()

if found:
    update_m3u("cafe.m3u", found, domain)
else:
    print("❌ hiç link yok")
