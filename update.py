import requests
from bs4 import BeautifulSoup
import re
import base64
from github import Github
import time
from urllib.parse import urljoin, urlparse

# ============ AYARLAR ============
TARGET_URL = "https://atomsportv494.top"
GITHUB_TOKEN = "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"  # GitHub Personal Access Token
GITHUB_REPO = "kadirsener1/İptv-bot"       # GitHub repo adı
GITHUB_FILE_PATH = "cafe.m3u"        # Kaydedilecek dosya adı
# =================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Referer": TARGET_URL,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def get_page_links(url):
    """Sayfadaki tüm linkleri çeker"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        links = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(url, href)
            if TARGET_URL in full_url:
                links.add(full_url)
        
        return links, response.text
    except Exception as e:
        print(f"[HATA] Sayfa alınamadı: {e}")
        return set(), ""

def extract_m3u8_from_text(text, base_url=""):
    """Metin içinden m3u8 linklerini çeker"""
    m3u8_links = set()
    
    # Direkt m3u8 URL pattern
    patterns = [
        r'https?://[^\s\'"<>]+\.m3u8[^\s\'"<>]*',
        r'["\']([^"\']*\.m3u8[^"\']*)["\']',
        r'src:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        r'file:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        r'hls["\']?\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
        r'source\s+src=["\']([^"\']+\.m3u8[^"\']*)["\']',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            if match.startswith("http"):
                m3u8_links.add(match)
            elif match.startswith("/") and base_url:
                m3u8_links.add(urljoin(base_url, match))
    
    return m3u8_links

def extract_m3u8_from_iframes(soup, base_url):
    """iframe içindeki m3u8 linklerini çeker"""
    m3u8_links = set()
    
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "")
        if src:
            full_src = urljoin(base_url, src)
            try:
                print(f"  [iframe] {full_src}")
                resp = requests.get(full_src, headers=HEADERS, timeout=10)
                links = extract_m3u8_from_text(resp.text, full_src)
                m3u8_links.update(links)
                
                # JavaScript içinden de ara
                scripts = BeautifulSoup(resp.text, "html.parser").find_all("script")
                for script in scripts:
                    if script.string:
                        links = extract_m3u8_from_text(script.string, full_src)
                        m3u8_links.update(links)
                        
                        # Base64 encoded URL'leri çöz
                        b64_pattern = r'atob\(["\']([A-Za-z0-9+/=]+)["\']\)'
                        b64_matches = re.findall(b64_pattern, script.string)
                        for b64 in b64_matches:
                            try:
                                decoded = base64.b64decode(b64).decode("utf-8")
                                links = extract_m3u8_from_text(decoded, full_src)
                                m3u8_links.update(links)
                            except:
                                pass
                                
            except Exception as e:
                print(f"  [HATA] iframe alınamadı: {e}")
            
            time.sleep(1)
    
    return m3u8_links

def get_channel_name(url, soup):
    """Kanal adını çekmeye çalışır"""
    try:
        title = soup.find("title")
        if title:
            return title.text.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.text.strip()
    except:
        pass
    return urlparse(url).path.strip("/").replace("/", "_") or "Channel"

def scrape_all_channels():
    """Tüm kanalları tara ve m3u8 linklerini topla"""
    print(f"[*] Ana sayfa taranıyor: {TARGET_URL}")
    
    all_m3u8 = {}  # {channel_name: m3u8_url}
    
    # Ana sayfa
    channel_links, main_html = get_page_links(TARGET_URL)
    
    # Ana sayfadan direkt m3u8 ara
    direct = extract_m3u8_from_text(main_html, TARGET_URL)
    for link in direct:
        all_m3u8[f"Direct_{len(all_m3u8)+1}"] = link
    
    print(f"[*] {len(channel_links)} kanal linki bulundu")
    
    # Her kanal sayfasını tara
    for ch_url in channel_links:
        print(f"\n[→] Taranıyor: {ch_url}")
        try:
            resp = requests.get(ch_url, headers=HEADERS, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            channel_name = get_channel_name(ch_url, soup)
            
            found = set()
            
            # 1. Direkt metin içinde ara
            found.update(extract_m3u8_from_text(resp.text, ch_url))
            
            # 2. Script tagları içinde ara
            for script in soup.find_all("script"):
                if script.string:
                    found.update(extract_m3u8_from_text(script.string, ch_url))
                    
                    # Base64 decode
                    b64_matches = re.findall(
                        r'atob\(["\']([A-Za-z0-9+/=]+)["\']\)', 
                        script.string
                    )
                    for b64 in b64_matches:
                        try:
                            decoded = base64.b64decode(b64).decode("utf-8")
                            found.update(extract_m3u8_from_text(decoded, ch_url))
                        except:
                            pass
            
            # 3. iframe'leri tara
            iframe_links = extract_m3u8_from_iframes(soup, ch_url)
            found.update(iframe_links)
            
            # Bulunan linkleri kaydet
            for i, link in enumerate(found):
                key = f"{channel_name}_{i+1}" if len(found) > 1 else channel_name
                all_m3u8[key] = link
                print(f"  [✓] M3U8 bulundu: {link}")
            
            time.sleep(2)  # Rate limiting
            
        except Exception as e:
            print(f"  [HATA] {e}")
    
    return all_m3u8

def create_m3u_content(channels):
    """M3U dosyası oluştur"""
    lines = ["#EXTM3U\n"]
    
    for name, url in channels.items():
        # Temizle
        clean_name = re.sub(r'[^\w\s\-]', '', name).strip()
        lines.append(f'#EXTINF:-1 tvg-name="{clean_name}",{clean_name}\n')
        lines.append(f'{url}\n')
        lines.append('\n')
    
    return "".join(lines)

def save_to_github(content, channels_count):
    """GitHub'a kaydet"""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        
        commit_message = f"🔄 M3U playlist güncellendi - {channels_count} kanal - {time.strftime('%Y-%m-%d %H:%M')}"
        
        try:
            # Dosya varsa güncelle
            existing = repo.get_contents(GITHUB_FILE_PATH)
            repo.update_file(
                GITHUB_FILE_PATH,
                commit_message,
                content,
                existing.sha
            )
            print(f"[✓] GitHub dosyası güncellendi: {GITHUB_FILE_PATH}")
        except:
            # Dosya yoksa oluştur
            repo.create_file(
                GITHUB_FILE_PATH,
                commit_message,
                content
            )
            print(f"[✓] GitHub dosyası oluşturuldu: {GITHUB_FILE_PATH}")
            
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{GITHUB_FILE_PATH}"
        print(f"[✓] Raw URL: {raw_url}")
        return True
        
    except Exception as e:
        print(f"[HATA] GitHub'a kaydedilemedi: {e}")
        return False

def save_local(content, filename="playlist.m3u"):
    """Yerel dosyaya kaydet"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[✓] Yerel dosyaya kaydedildi: {filename}")

def main():
    print("=" * 50)
    print("   M3U8 Scraper & GitHub Uploader")
    print("=" * 50)
    
    # Tüm kanalları tara
    channels = scrape_all_channels()
    
    if not channels:
        print("\n[!] Hiç M3U8 linki bulunamadı!")
        return
    
    print(f"\n[*] Toplam {len(channels)} M3U8 linki bulundu")
    
    # M3U içeriği oluştur
    m3u_content = create_m3u_content(channels)
    
    # Yerel kaydet
    save_local(m3u_content)
    
    # GitHub'a kaydet
    if GITHUB_TOKEN != "your_github_token_here":
        save_to_github(m3u_content, len(channels))
    else:
        print("[!] GitHub token ayarlanmamış, sadece yerel kaydedildi")

if __name__ == "__main__":
    main()
