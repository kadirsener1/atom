import os
import re
import json
import time
import logging
from datetime import datetime
import requests as req_lib

# Logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# Proxy prefix
PROXY_PREFIX = "https://ronaldo.magnitude.workers.dev/?url="

# Domain bulma
MIN_NUMBER, MAX_NUMBER = 503, 535
def find_base_url():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"}
    for i in range(MIN_NUMBER, MAX_NUMBER + 1):
        try:
            resp = req_lib.get(f"https://atomsportv{i}.top", headers=headers, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                return resp.url.rstrip("/")
        except: pass
    return f"https://atomsportv{MIN_NUMBER}.top"

BASE_URL = find_base_url()
OUTPUT_FILE, STATS_FILE = "playlist.m3u", "stats.json"
STREAM_WAIT = 15
log.info(f"🌐 BASE_URL: {BASE_URL}")

# Kanallar
PAGES = [
    {"slug": "matches?id=bein-sports-1",     "name": "beIN Sports 1",     "group": "Spor"},
    {"slug": "matches?id=bein-sports-2",     "name": "beIN Sports 2",     "group": "Spor"},
    {"slug": "matches?id=bein-sports-3",     "name": "beIN Sports 3",     "group": "Spor"},
    {"slug": "matches?id=bein-sports-4",     "name": "beIN Sports 4",     "group": "Spor"},
    {"slug": "matches?id=bein-sports-5",     "name": "beIN Sports 5",     "group": "Spor"},
    {"slug": "matches?id=bein-sports-max-1", "name": "beIN Sports Max 1", "group": "Spor"},
    {"slug": "matches?id=bein-sports-max-2", "name": "beIN Sports Max 2", "group": "Spor"},
    {"slug": "matches?id=s-sport",           "name": "S Sport",           "group": "Spor"},
    {"slug": "matches?id=s-sport-2",         "name": "S Sport 2",         "group": "Spor"},
    {"slug": "matches?id=a-spor",            "name": "A Spor",            "group": "Spor"},
    {"slug": "matches?id=tivibu-spor-1",     "name": "Tivibu Spor 1",     "group": "Spor"},
    {"slug": "matches?id=tivibu-spor-2",     "name": "Tivibu Spor 2",     "group": "Spor"},
    {"slug": "matches?id=tivibu-spor-3",     "name": "Tivibu Spor 3",     "group": "Spor"},
    {"slug": "matches?id=tivibu-spor-4",     "name": "Tivibu Spor 4",     "group": "Spor"},
]

# Selenium Wire
try:
    from seleniumwire import webdriver
except ImportError:
    log.error("❌ Selenium Wire kurulu değil! pip install selenium-wire")
    exit(1)

from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def is_m3u8(url):
    return url and isinstance(url, str) and (url.lower().endswith(".m3u8") or ".m3u8?" in url.lower())

def get_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    # Chrome yolunu kendinize göre değiştirin veya çevre değişkeni kullanın
    chrome_bin = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
    if os.path.exists(chrome_bin):
        options.binary_location = chrome_bin
    
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver")
    service = Service(executable_path=chromedriver_path)
    
    driver = webdriver.Chrome(service=service, options=options, seleniumwire_options={"verify_ssl": False})
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def click_play(driver):
    # Video elementlerine play() yap
    try:
        for v in driver.find_elements(By.TAG_NAME, "video"):
            driver.execute_script("arguments[0].muted = true; arguments[0].play();", v)
            time.sleep(1)
            return
    except: pass
    
    # Buton ara
    for sel in [".play-button", ".btn-play", "#play-button", ".jw-icon-playback", ".vjs-play-button", 
                "[aria-label='Play']", "button.play", ".overlay-play"]:
        try:
            WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.CSS_SELECTOR, sel))).click()
            time.sleep(1)
            return
        except: pass

def scrape_page(driver, page):
    url = f"{BASE_URL}/{page['slug']}"
    log.info(f"🔍 {page['name']} → {url}")
    
    # Önceki istekleri temizle (çok önemli)
    del driver.requests
    
    driver.get(url)
    WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(2)
    click_play(driver)
    
    # M3U8 ara
    start = time.time()
    while time.time() - start < STREAM_WAIT:
        for req in driver.requests:
            if is_m3u8(req.url):
                log.info(f"  ✅ M3U8 bulundu: {req.url}")
                return req.url
        time.sleep(0.5)
    
    # JS/HTML'de ara
    try:
        m3u8 = driver.execute_script("""
            for (let v of document.querySelectorAll('video')) {
                if (v.src && v.src.includes('.m3u8')) return v.src;
                if (v.currentSrc && v.currentSrc.includes('.m3u8')) return v.currentSrc;
            }
            let m = document.documentElement.innerHTML.match(/https?:\\/\\/[^\\s'\"]+\\.m3u8[^\\s'\"]*/i);
            return m ? m[0] : null;
        """)
        if m3u8 and is_m3u8(m3u8):
            log.info(f"  ✅ JS/HTML'den bulundu: {m3u8}")
            return m3u8
    except: pass
    
    log.warning(f"  ❌ {page['name']} için M3U8 bulunamadı")
    return None

def create_m3u(channels):
    lines = ["#EXTM3U\n", f"# Guncelleme: {datetime.now()}\n", f"# Toplam: {len(channels)}\n\n"]
    for ch in channels:
        lines.append(f'#EXTINF:-1 tvg-name="{ch["name"]}" group-title="{ch["group"]}",{ch["name"]}\n')
        lines.append(f"{PROXY_PREFIX}{ch['url']}\n\n")
    return "".join(lines)

def main():
    log.info(f"Başlanıyor... {len(PAGES)} kanal taranacak")
    driver = get_driver()
    channels = []
    
    try:
        for i, page in enumerate(PAGES, 1):
            log.info(f"\n[{i}/{len(PAGES)}]")
            m3u8_url = scrape_page(driver, page)
            if m3u8_url:
                channels.append({"name": page["name"], "url": m3u8_url, "group": page["group"]})
            time.sleep(1)
    finally:
        driver.quit()
    
    # Dosyaları yaz
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(create_m3u(channels))
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_update": datetime.now().isoformat(), "total_channels": len(channels), "channels": channels}, f, indent=2)
    
    log.info(f"✅ {len(channels)} kanal bulundu, {OUTPUT_FILE} kaydedildi")

if __name__ == "__main__":
    main()
