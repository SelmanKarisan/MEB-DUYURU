import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from bs4 import BeautifulSoup

URL = "https://yyegm.meb.gov.tr/www/duyurular/kategori/2"
STATE_FILE = "last_announcement.txt"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def send_email(title, link):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        print("HATA: E-posta değişkenlerinden biri (Secrets) eksik! Lütfen GitHub Secrets alanını kontrol edin.")
        return

    subject = "🚨 MEB YYEGM Yeni Duyuru Yayınlandı!"
    body = f"Yeni bir duyuru tespit edildi:\n\n📌 Başlık: {title}\n🔗 Bağlantı: {link}"

    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("E-posta başarıyla gönderildi.")
    except Exception as e:
        print(f"E-posta gönderim hatası: {e}")

def check_announcements():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    try:
        response = requests.get(URL, headers=headers, timeout=15)
        print(f"Sayfa yanıt kodu: {response.status_code}")
    except Exception as e:
        print(f"Sayfaya ulaşılamadı. Hata: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    
    title_tag = soup.find("title")
    print(f"Sayfa Başlığı: {title_tag.text.strip() if title_tag else 'Başlık bulunamadı'}")

    announcement = None

    # MEB duyuru listesindeki bağlantıları arar
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        
        # Genel menü linklerini eler
        ignore_words = ["anasayfa", "ana sayfa", "iletişim", "harita", "kategori", "yönetim", "fotoğraf", "arama"]
        if len(text) > 8 and href:
            if not any(word in text.lower() for word in ignore_words):
                if any(k in href.lower() for k in ["duyuru", "icerik", "detay", "www"]):
                    announcement = (text, href)
                    break

    # Genel filtre yakalayamazsa uzun metinli ilk bağlantıyı alır
    if not announcement:
        for a in soup.find_all("a"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            if len(text) > 15 and href and not href.startswith("#") and not href.startswith("javascript"):
                announcement = (text, href)
                break

    if not announcement:
        print("Duyuru bulunamadı. Sayfada bulunan ilk 5 link örneği:")
        for idx, a in enumerate(soup.find_all("a")[:5]):
            print(f"{idx+1}. Metin: '{a.get_text(strip=True)}' -> Href: '{a.get('href')}'")
        return

    latest_title, latest_href = announcement
    if not latest_href.startswith("http"):
        if latest_href.startswith("/"):
            latest_href = f"https://yyegm.meb.gov.tr{latest_href}"
        else:
            latest_href = f"https://yyegm.meb.gov.tr/{latest_href}"

    print(f"Tespit edilen güncel duyuru: '{latest_title}'")
    print(f"Bağlantı: {latest_href}")

    last_title = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    if latest_title != last_title:
        print("Yeni duyuru algılandı! E-posta gönderiliyor...")
        send_email(latest_title, latest_href)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(latest_title)
    else:
        print("Yeni duyuru yok, kayıtlı duyuru ile aynı.")

if __name__ == "__main__":
    check_announcements()
