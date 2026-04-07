from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

def get_m3u8(url):
    options = Options()
    options.add_argument("--headless=new")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=options)

    driver.get(url)
    time.sleep(7)

    logs = driver.get_log("performance")

    for log in logs:
        message = log["message"]

        if ".m3u8" in message:
            start = message.find("http")
            end = message.find(".m3u8") + 5
            link = message[start:end]
            print("✅ BULUNDU:", link)
            driver.quit()
            return link

    driver.quit()
    print("❌ bulunamadı")
    return None


url = "https://atomsportv494.top/matches?id=bein-sports-2"

get_m3u8(url)
