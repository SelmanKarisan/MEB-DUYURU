import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.parse import urljoin
import urllib3
import requests
from bs4 import BeautifulSoup

# MEB SSL sertifika uyarılarını bastırma
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
    RSS_URL = "https://yyegm.meb.gov.tr/meb_iys_dosyalar/xml/rss_duyurular.xml"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
    }

    try:
        response = requests.get(
            RSS_URL,
            headers=headers,
            verify=False,
            timeout=20
        )

        response.encoding = "utf-8"

        print(f"RSS HTTP Yanıt Kodu: {response.status_code}")

        if response.status_code != 200:
            print("RSS sayfasına erişilemedi.")
            return

    except Exception as e:
        print(f"RSS sayfasına ulaşılamadı. Hata: {e}")
        return


    soup = BeautifulSoup(response.content, "xml")

    items = soup.find_all("item")

    print(f"RSS içerisinde bulunan duyuru sayısı: {len(items)}")

    if not items:
        print("RSS içerisinde duyuru bulunamadı.")
        return


    latest_item = items[0]

    title_tag = latest_item.find("title")
    link_tag = latest_item.find("link")

    if not title_tag or not link_tag:
        print("RSS içerisindeki duyuruda başlık veya bağlantı bulunamadı.")
        return

    latest_title = title_tag.get_text(strip=True)
    latest_href = link_tag.get_text(strip=True)

    # ---------------------------------------------------------
    # KONTROL
    # ---------------------------------------------------------

    if not latest_title or not latest_href:
        print("Duyuru başlığı veya bağlantısı boş.")
        return

    print("--------------------------------------------------")
    print("EN GÜNCEL DUYURU TESPİT EDİLDİ:")
    print(f"Başlık : {latest_title}")
    print(f"Bağlantı: {latest_href}")
    print("--------------------------------------------------")


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
        print("Kayıtlı duyuru ile aynı, e-posta gönderilmedi.")

if __name__ == "__main__":
    check_announcements()
