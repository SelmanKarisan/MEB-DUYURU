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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status()
    except Exception as e:
        print(f"Sayfaya ulaşılamadı. Hata: {e}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    announcement = None

    # Yöntem 1: MEB listelerinde genellikle ilk duyuru bir tablo (table) içindedir
    table = soup.find("table")
    if table:
        for link in table.find_all("a"):
            text = link.get_text(strip=True)
            href = link.get("href", "")
            if len(text) > 8 and href:
                announcement = (text, href)
                break

    # Yöntem 2: Tablo yoksa genel içerik bağlantılarını tara
    if not announcement:
        for link in soup.find_all("a"):
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if ("icerik" in href.lower() or "duyuru" in href.lower() or "detay" in href.lower()) and len(text) > 8:
                announcement = (text, href)
                break

    if not announcement:
        print("Duyuru bulunamadı. Sayfa yapısı değişmiş veya çekilememiş olabilir.")
        return

    latest_title, latest_href = announcement
    if not latest_href.startswith("http"):
        latest_href = f"https://yyegm.meb.gov.tr{latest_href}"

    print(f"Tespit edilen güncel duyuru: {latest_title}")

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
