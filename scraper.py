import os
import re
import json
import time
import logging
from datetime import datetime
import requests as req_lib

# ── Logging ───────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(
            f"logs/scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

logging.getLogger("seleniumwire").setLevel(logging.ERROR)

# ═══════════════════════════════════════════════════════
# BASE URL BUL
# ═══════════════════════════════════════════════════════
MIN_NUMBER = 490
MAX_NUMBER = 520

def generate_domains():
    return [f"https://atomsportv{i}.top" for i in range(MIN_NUMBER, MAX_NUMBER + 1)]

def find_base_url():
    headers = {"User-Agent": "Mozilla/5.0"}
    for domain in generate_domains():
        try:
            r = req_lib.get(domain, headers=headers, timeout=5)
            if r.status_code == 200:
                return r.url.rstrip("/")
        except:
            pass
    return f"https://atomsportv{MIN_NUMBER}.top"

BASE_URL = find_base_url()
OUTPUT_FILE = "playlist.m3u"
STATS_FILE = "stats.json"

# ── SAYFALAR ──────────────────────────────────────────
PAGES = [
    {"slug": "matches?id=bein-sports-1", "name": "beIN Sports 1", "group": "Spor"},
    {"slug": "matches?id=bein-sports-2", "name": "beIN Sports 2", "group": "Spor"},
    {"slug": "matches?id=bein-sports-3", "name": "beIN Sports 3", "group": "Spor"},
    {"slug": "matches?id=bein-sports-4", "name": "beIN Sports 4", "group": "Spor"},
    {"slug": "matches?id=bein-sports-5", "name": "beIN Sports 5", "group": "Spor"},
]

# ── SELENIUM ──────────────────────────────────────────
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--mute-audio")

    return webdriver.Chrome(options=options)

# ── M3U8 KONTROL ──────────────────────────────────────
def is_m3u8(url):
    return url and ".m3u8" in url.lower()

# ═══════════════════════════════════════════════════════
# PLAY TIKLA
# ═══════════════════════════════════════════════════════
def click_play(driver):
    try:
        btn = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button, .play"))
        )
        btn.click()
    except:
        driver.execute_script("""
            document.querySelectorAll('video').forEach(v=>{
                v.muted=true;
                v.play().catch(()=>{});
            });
        """)

# ═══════════════════════════════════════════════════════
# SAYFA TARA (FIXED)
# ═══════════════════════════════════════════════════════
def scrape_page(driver, page):
    url = f"{BASE_URL}/{page['slug']}"
    log.info(f"🔍 {page['name']}")

    # 🔥 EN KRİTİK FIX
    driver.requests.clear()

    driver.get(url)
    time.sleep(2)

    click_play(driver)

    start = time.time()
    m3u8_url = None

    while time.time() - start < 10:
        m3u8_list = []

        for req in driver.requests:
            if is_m3u8(req.url):
                m3u8_list.append(req.url)

        if m3u8_list:
            m3u8_url = m3u8_list[-1]  # 🔥 SON GELEN
            break

        time.sleep(1)

    if m3u8_url:
        log.info(f"✅ BULUNDU: {m3u8_url}")
    else:
        log.info("❌ BULUNAMADI")

    return m3u8_url

# ═══════════════════════════════════════════════════════
# M3U OLUŞTUR
# ═══════════════════════════════════════════════════════
def create_m3u(channels):
    lines = ["#EXTM3U\n"]
    for ch in channels:
        lines.append(f'#EXTINF:-1 group-title="{ch["group"]}",{ch["name"]}\n')
        lines.append(f'{ch["url"]}\n\n')
    return "".join(lines)

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════
def main():
    driver = get_driver()
    channels = []

    try:
        for page in PAGES:
            url = scrape_page(driver, page)
            if url:
                channels.append({
                    "name": page["name"],
                    "url": url,
                    "group": page["group"]
                })

    finally:
        driver.quit()

    # DOSYAYA YAZ
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(create_m3u(channels))

    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)

    log.info("✅ TAMAMLANDI")

if __name__ == "__main__":
    main()
