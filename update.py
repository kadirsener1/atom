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

# 🔧 Selenium
def create_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
    return webdriver.Chrome(options=options)

# 📺 Kanal listesi
def get_channels():
    r = requests.get(DOMAIN, headers=HEADERS, timeout=10)
    ids = re.findall(r'matches\?id=([a-zA-Z0-9\-]+)', r.text)
    return list(set(ids))

# 📡 m3u8 yakala + LOG
def get_m3u8(driver, cid):
    try:
        url = urljoin(DOMAIN, f"matches?id={cid}")
        print(f"\n🔍 Kanal: {cid}")
        print(f"➡️ URL: {url}")

        driver.get(url)
        time.sleep(6)

        logs = driver.get_log("performance")

        for log in logs:
            msg = log["message"]
            if ".m3u8" in msg:
                start = msg.find("http")
                end = msg.find(".m3u8") + 5
                link = msg[start:end]

                print(f"🎯 M3U8 BULUNDU:")
                print(f"{cid} => {link}")

                return link

        print("❌ M3U8 bulunamadı")

    except Exception as e:
        print(f"⚠️ hata: {cid} - {e}")

    return None

# ✍️ M3U YAZ (SIFIRDAN YAZDIRMA - GARANTİ)
def write_m3u(filename, links, referer):
    print("\n📄 M3U dosyası yazılıyor...")

    lines = ["#EXTM3U"]

    for cid, url in links.items():
        lines.append(f'#EXTINF:-1 tvg-id="{cid}",{cid}')
        lines.append(f"#EXTVLCOPT:http-referrer={referer}")
        lines.append(url)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("✅ M3U dosyası tamamen güncellendi")

# 🚀 ANA AKIŞ
channels = get_channels()
print(f"\n📺 Toplam kanal: {len(channels)}")

driver = create_driver()

found_links = {}

for cid in channels:
    link = get_m3u8(driver, cid)
    if link:
        found_links[cid] = link

driver.quit()

# 🔥 LOGDA TOPLU GÖSTER
print("\n📡 BULUNAN TÜM LİNKLER:")
for k, v in found_links.items():
    print(f"{k} => {v}")

# 📄 M3U YAZ
if found_links:
    write_m3u("cafe.m3u", found_links, DOMAIN)
else:
    print("❌ Hiç link bulunamadı")
