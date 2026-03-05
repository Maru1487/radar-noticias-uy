import feedparser
import requests
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MI_CHAT_ID = os.getenv("MI_CHAT_ID")

def enviar_directo(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": MI_CHAT_ID, "text": msg})

FUENTES = ["https://www.elobservador.com.uy/rss/home.xml"]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

print("🕵️ MODO FORENSE ACTIVADO")
for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        print(f"Status Code: {r.status_code}") # 200 es OK, 403 es Bloqueado
        
        feed = feedparser.parse(r.content)
        cantidad = len(feed.entries)
        print(f"Noticias encontradas: {cantidad}")
        
        if cantidad > 0:
            titular = feed.entries[0].title
            enviar_directo(f"📡 LECTURA EXITOSA\nPortal: El Observador\nStatus: {r.status_code}\nNoticias: {cantidad}\nÚltima: {titular}")
        else:
            enviar_directo(f"⚠️ PORTAL VACÍO\nEl sitio respondió {r.status_code} pero no envió noticias.")
            
    except Exception as e:
        enviar_directo(f"💥 ERROR TÉCNICO: {str(e)}")

print("Fin del análisis.")
