import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import urllib3

# MEB sitelerindeki SSL doğrulama uyarılarını gizle
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def en_son_duyuruyu_getir():
    url = "https://yyegm.meb.gov.tr/www/duyurular/kategori/2"
    
    # MEB sunucularının isteği engellememesi için tarayıcı kimliği (User-Agent)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
    }
    
    try:
        # SSL doğrulama hatası almamak için verify=False kullanıyoruz
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        response.raise_for_status()
        
        # Türkçe karakterlerin doğru görünmesi için encoding ayarı
        response.encoding = response.apparent_encoding or 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        duyurular = []
        
        # MEB CMS altyapısında duyuru detay sayfalarının URL'si '/icerik/' içerir
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            
            # Sadece duyuru detay linklerini hedefle
            if '/icerik/' in href:
                baslik = a_tag.get_text(strip=True)
                
                # "Devamı...", "Detay" veya boş olan menü/buton metinlerini eleyelim
                if baslik and len(baslik) > 5 and not baslik.lower().startswith('devam'):
                    tam_link = urljoin(url, href)
                    
                    # Tekrar eden linkleri önlemek için kontrol
                    if not any(d['link'] == tam_link for d in duyurular):
                        duyurular.append({
                            'baslik': baslik,
                            'link': tam_link
                        })
        
        if duyurular:
            # Liste kronolojik olarak yeniden eskiye doğru sıralandığından ilk eleman en son duyurudur
            en_son_duyuru = duyurular[0]
            print("==========================================")
            print("EN SON DUYURU BULUNDU")
            print("==========================================")
            print(f"Başlık : {en_son_duyuru['baslik']}")
            print(f"Link   : {en_son_duyuru['link']}")
            print("==========================================")
            return en_son_duyuru
        else:
            print("Sayfada duyuru bağlantısı bulunamadı.")
            return None

    except Exception as e:
        print(f"Bir hata oluştu: {e}")
        return None

if __name__ == "__main__":
    en_son_duyuruyu_getir()
