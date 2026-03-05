import google.generativeai as genai
import feedparser
import requests
import os
import time
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MI_CHAT_ID = os.getenv("MI_CHAT_ID")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- FUENTES AMPLIADAS ---
FUENTES = [
    "https://www.elobservador.com.uy/rss/home.xml",
    "https://www.elpais.com.uy/rss/ultimo-momento",
    "https://www.subrayado.com.uy/rss/ultimo-momento",
    "https://www.montevideo.com.uy/anxml.aspx?1",
    "https://www.gub.uy/presidencia/rss"
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try: requests.post(url, json={"chat_id": MI_CHAT_ID, "text": texto, "parse_mode": "Markdown"}, timeout=10)
    except: pass

def analizar(texto):
    # Volvemos al criterio periodístico que buscabas
    prompt = (
        f"Sos un editor uruguayo senior. ¿Este titular es una RUPTURA DE INERCIA informativa? "
        f"(Primicias, seguridad grave, crisis política, interpelaciones o anuncios de infraestructura). "
        f"Titular: '{texto}'. Responde '🚨' si es relevante o 'SKIP' si es rutina."
    )
    try:
        res = model.generate_content(prompt).text.strip()
        return "🚨" in res
    except: return False

print(f"🚀 Ejecutando Radar - {datetime.now()}")

for url in FUENTES:
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.content)
        ahora = datetime.now(timezone.utc)
        
        for entry in feed.entries[:5]: # Revisamos las últimas 5 de cada portal
            # FILTRO DE TIEMPO: Solo noticias de los últimos 20 minutos
            pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if ahora - pub_time < timedelta(minutes=20):
                if analizar(entry.title):
                    enviar_telegram(f"🚨 *URGENTE*\n\n{entry.title}\n\n🔗 [Ver noticia]({entry.link})")
                    print(f"Alerta enviada: {entry.title}")
            
    except Exception as e:
        print(f"Error en {url}: {e}")

print("✅ Ronda completada.")
