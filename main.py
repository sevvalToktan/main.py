import os
import time
import random
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

# --- KULLANICI AYARLARI ---
TELEGRAM_TOKEN = "8752514015:AAH1iWVgJnnpwQQun_fQ0CFDHyL0yDCDAT8"
CHAT_ID = "5316219134"

# Takip ettiğin Hepsiemlak arama linklerin
HEPSIEMLAK_URLLER = [
    "https://www.hepsiemlak.com/tepebasi/konut?districts=tepebasi-bahcelievler-mah,tepebasi-eskibaglar,tepebasi-gulluk,tepebasi-yenibaglar,tepebasi-sutluce-mah&p33=1&sortDirection=DESC&sortField=UPDATED_DATE&p32=11500&p63=180402-180404-180403",
    "https://www.hepsiemlak.com/tepebasi-sahibinden/konut?districts=tepebasi-bahcelievler-mah,tepebasi-eskibaglar,tepebasi-gulluk,tepebasi-yenibaglar,tepebasi-sutluce-mah&p33=1&sortDirection=DESC&sortField=UPDATED_DATE&p32=13500&p63=180402-180404-180403"
]

# Takip ettiğin Emlakjet arama linklerin
EMLAKJET_URLLER = [
    "https://www.emlakjet.com/kiralik-konut/eskisehir-tepebasi/sahibinden?filtreler=max-fiyat=13500&oda-sayisi=1-1,15-1,2-0,3-0&siralama=4&semt=bahcelievler-10001515&mahalle=eskisehir-tepebasi-eskibaglar-mahallesi-130197,eskisehir-tepebasi-yenibaglar-mahallesi-130219,eskisehir-tepebasi-bahcelievler-mahallesi-130191,eskisehir-tepebasi-sutluce-mahallesi-130212,eskisehir-tepebasi-gulluk-mahallesi-130200",
    "https://www.emlakjet.com/kiralik-konut/eskisehir-tepebasi?filtreler=max-fiyat=11500&oda-sayisi=1-1,15-1,2-0,3-0&esya-durumu=esyali&siralama=4&semt=bahcelievler-10001515&mahalle=eskisehir-tepebasi-yenibaglar-mahallesi-130219,eskisehir-tepebasi-eskibaglar-mahallesi-130197,eskisehir-tepebasi-bahcelievler-mahallesi-130191,eskisehir-tepebasi-sutluce-mahallesi-130212,eskisehir-tepebasi-gulluk-mahallesi-130200"
]

# --- BULUT HAFIZA SİSTEMİ ---
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
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080}
    )
    page = context.new_page()
    
    # EN KRİTİK DÜZELTME: Sayfaya askeri düzeyde gizlilik maskesi takıyoruz
    stealth_sync(page)
    
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(random.uniform(5, 8))
        page.evaluate("window.scrollBy(0, 600);")
        time.sleep(random.uniform(3, 5))
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
    # --- DEDEKTİF KODU BAŞLANGICI ---
    print("\n--- HEPSİEMLAK SAYFA RAPORU ---")
    print("Sayfa Başlığı:", soup.title.text if soup.title else "Başlık Yok")
    print("-------------------------------\n")
    # --- DEDEKTİF KODU BİTİŞİ ---
    
    # Sınıf isimlerini tamamen boş verip sayfadaki tüm linkleri tarıyoruz
    tum_linkler = soup.find_all('a', href=True)
    
    for a in tum_linkler:
        href = a['href']
        ilan_id_adayi = href.split('/')[-1]
        
        if "-" in ilan_id_adayi:
            parcalar = ilan_id_adayi.split('-')
            # Eğer linkin sonu iki grup rakamla bitiyorsa bu kesin ilandır (Örn: 148965-134)
            if len(parcalar) >= 2 and parcalar[-1].isdigit() and parcalar[-2].isdigit():
                if ilan_id_adayi not in gorulen_ilanlar:
                    gorulen_ilanlar.add(ilan_id_adayi)
                    with open(HAFIZA_DOSYASI, "a") as f:
                        f.write(ilan_id_adayi + "\n")
                    if not ILK_TARAMA_MI:
                        link = "https://www.hepsiemlak.com" + href if href.startswith('/') else href
                        telegram_mesaj_gonder(f"❤️ **[Hepsiemlak] Yeni İlan!**\n\n🔗 [İlanı İncele]({link})")

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
                    telegram_mesaj_gonder(f"💚 **[Emlakjet] Yeni İlan!**\n\n🔗 [İlanı İncele]({link})")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for url in HEPSIEMLAK_URLLER:
            hepsiemlak_tara(browser, url)
        for url in EMLAKJET_URLLER:
            emlakjet_tara(browser, url)
        browser.close()

if __name__ == "__main__":
    main()
