import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

URL = "https://yyegm.meb.gov.tr/www/duyurular/kategori/2"
STATE_FILE = "last_announcement.txt"

SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

def send_email(title, link):
    if not SENDER_EMAIL or not SENDER_PASSWORD or not RECEIVER_EMAIL:
        print("HATA: E-posta değişkenlerinden biri (Secrets) eksik!")
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
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        response = requests.get(URL, headers=headers, timeout=20)
        response.encoding = 'utf-8'
        print(f"HTTP Yanıt Kodu: {response.status_code}")
    except Exception as e:
        print(f"Sayfaya ulaşılamadı. Hata: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    candidates = []

    # Sayfadaki tüm linkleri tara
    for a in soup.find_all("a"):
        href = a.get("href", "").strip()
        text = a.get_text(strip=True)

        if not href or href.startswith("#") or href.startswith("javascript"):
            continue

        # MEB duyuruları genellikle 'icerik', 'duyuru' veya '/www/' ifadelerini içerir
        if any(keyword in href.lower() for keyword in ["icerik", "duyuru", "/www/"]):
            ignore_words = ["anasayfa", "kategori", "iletişim", "tümü", "devamı", "harita", "yönetim"]
            if len(text) > 5 and not any(w in text.lower() for w in ignore_words):
                full_url = urljoin(URL, href)
                candidates.append((text, full_url))

    print(f"Sayfada {len(candidates)} adet potansiyel duyuru bağlantısı bulundu.")

    if candidates:
        # En üstteki (en güncel) duyuruyu seç
        latest_title, latest_href = candidates[0]
        print(f"Bulunan En Güncel Duyuru: {latest_title}")
        print(f"Bağlantı: {latest_href}")
    else:
        print("Duyuru bağlantısı ayrıştırılamadı. Sayfadaki ilk 10 link örneği:")
        for idx, a in enumerate(soup.find_all("a")[:10]):
            print(f"{idx+1}. Metin: '{a.get_text(strip=True)}' | Href: '{a.get('href')}'")
        return

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
        print("Kayıtlı duyuru ile aynı, yeni duyuru yok.")

if __name__ == "__main__":
    check_announcements()
