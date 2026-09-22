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
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(URL, headers=headers, timeout=15)
    if response.status_code != 200:
        print(f"Sayfaya ulaşılamadı. Durum Kodu: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "html.parser")
    
    # Sayfadaki duyuru bağlantılarını arar
    links = soup.find_all("a")
    announcement = None
    for link in links:
        href = link.get("href", "")
        text = link.get_text(strip=True)
        if "duyuru" in href.lower() and len(text) > 5:
            announcement = (text, href)
            break

    if not announcement:
        print("Duyuru bulunamadı.")
        return

    latest_title, latest_href = announcement
    if not latest_href.startswith("http"):
        latest_href = f"https://yyegm.meb.gov.tr{latest_href}"

    last_title = ""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()

    if latest_title != last_title:
        print(f"Yeni duyuru bulundu: {latest_title}")
        send_email(latest_title, latest_href)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            f.write(latest_title)
    else:
        print("Yeni duyuru yok, sayfa güncel.")

if __name__ == "__main__":
    check_announcements()