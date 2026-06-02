import os
import time
import random
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth

TELEGRAM_TOKEN = "8752514015:AAH1iWVgJnnpwQQun_fQ0CFDHyL0yDCDAT8"
CHAT_ID = "5316219134"

HEPSIEMLAK_URLLER = [
    "https://www.hepsiemlak.com/tepebasi/konut?districts=tepebasi-bahcelievler-mah,tepebasi-eskibaglar,tepebasi-gulluk,tepebasi-yenibaglar,tepebasi-sutluce-mah&p63=180402-180404-180403&p32=11500&p33=1",
    "https://www.hepsiemlak.com/tepebasi-sahibinden/konut?districts=tepebasi-bahcelievler-mah,tepebasi-eskibaglar,tepebasi-gulluk,tepebasi-yenibaglar,tepebasi-sutluce-mah&p63=180402-180404-180403&p32=13500&p33=1"
]

EMLAKJET_URLLER = [
    "https://www.emlakjet.com/kiralik-konut/eskisehir-tepebasi/sahibinden?filtreler=max-fiyat=13500&oda-sayisi=1-1,15-1,2-0,3-0&semt=bahcelievler-10001515&mahalle=eskisehir-tepebasi-yenibaglar-mahallesi-130219,eskisehir-tepebasi-eskibaglar-mahallesi-130197,eskisehir-tepebasi-bahcelievler-mahallesi-130191,eskisehir-tepebasi-sutluce-mahallesi-130212,eskisehir-tepebasi-gulluk-mahallesi-130200",
    "https://www.emlakjet.com/kiralik-konut/eskisehir-tepebasi?filtreler=max-fiyat=11500&oda-sayisi=1-1,15-1,2-0,3-0&esya-durumu=esyali&semt=bahcelievler-10001515&mahalle=eskisehir-tepebasi-yenibaglar-mahallesi-130219,eskisehir-tepebasi-eskibaglar-mahallesi-130197,eskisehir-tepebasi-bahcelievler-mahallesi-130191,eskisehir-tepebasi-sutluce-mahallesi-130212,eskisehir-tepebasi-gulluk-mahallesi-130200"
]

# SUNUCU İÇİN HAFIZA DOSYASI
HAFIZA_DOSYASI = "hafiza.txt"
if not os.path.exists(HAFIZA_DOSYASI):
    open(HAFIZA_DOSYASI, 'w').close()

with open(HAFIZA_DOSYASI, "r") as f:
    gorulen_ilanlar = set(f.read().splitlines())

ILK_TARAMA_MI = len(gorulen_ilanlar) == 0

def telegram_mesaj_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload)
    except: pass

def sayfayi_guvenli_getir(browser, url):
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(random.uniform(4, 7))
        page.evaluate("window.scrollBy(0, 500);")
        time.sleep(random.uniform(2, 4))
        html = page.content()
        context.close()
        return html
    except:
        context.close()
        return None

def hepsiemlak_tara(browser, url):
    html = sayfayi_guvenli_getir(browser, url)
    if not html: return
    soup = BeautifulSoup(html, 'html.parser')
    ilanlar = soup.find_all('li', class_='listing-item') 
    
    for ilan in ilanlar:
        link_el = ilan.find('a')
        if not link_el or not link_el.has_attr('href'): continue
        
        link = "https://www.hepsiemlak.com" + link_el['href']
        ilan_id = link.split('-')[-1]
        if not ilan_id.isdigit(): continue 
        
        if ilan_id not in gorulen_ilanlar:
            gorulen_ilanlar.add(ilan_id)
            with open(HAFIZA_DOSYASI, "a") as f:
                f.write(ilan_id + "\n")
            if not ILK_TARAMA_MI:
                title = link_el.get('title', 'Hepsiemlak İlanı')
                telegram_mesaj_gonder(f"❤️ **[Hepsiemlak]**\n\n🏠 {title}\n🔗 [İlanı İncele]({link})")

def emlakjet_tara(browser, url):
    html = sayfayi_guvenli_getir(browser, url)
    if not html: return
    soup = BeautifulSoup(html, 'html.parser')
    tum_linkler = soup.find_all('a', href=True)
    
    for a in tum_linkler:
        href = a['href']
        if "/ilan/" in href and "-ilani-" not in href: 
            ilan_id = href.split('-')[-1]
            if not ilan_id.isdigit(): continue
            
            if ilan_id not in gorulen_ilanlar:
                gorulen_ilanlar.add(ilan_id)
                with open(HAFIZA_DOSYASI, "a") as f:
                    f.write(ilan_id + "\n")
                if not ILK_TARAMA_MI:
                    link = "https://www.emlakjet.com" + href
                    telegram_mesaj_gonder(f"💚 **[Emlakjet]**\n\n🏠 Yeni Emlakjet İlanı\n🔗 [İlanı İncele]({link})")

def main():
    stealth = Stealth()
    with stealth.use_sync(sync_playwright()) as p:
        browser = p.chromium.launch(headless=True) # Bulut sunucusunda ekran yoktur
        for url in HEPSIEMLAK_URLLER:
            hepsiemlak_tara(browser, url)
        for url in EMLAKJET_URLLER:
            emlakjet_tara(browser, url)
        browser.close()

if __name__ == "__main__":
    main()
