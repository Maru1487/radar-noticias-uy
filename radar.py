from google.genai import Client
import feedparser
import requests
import os
import time
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN ---
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

client = Client(api_key=GEMINI_KEY)

# Nombres exactos validados para la librería en 2026
CANDIDATOS = [
    'models/gemini-1.5-flash',
    'models/gemini-1.5-flash-8b',
    'models/gemini-2.0-flash-lite',
    'models/gemini-2.0-flash'
]

FUENTES = [
    "https://www.elobservador.com.uy/rss/home.xml",
    "https://www.elpais.com.uy/rss/latest",
    "https://www.subrayado.com.uy/anxml.aspx?0",
    "https://www.montevideo.com.uy/anxml.aspx?59",
    "https://www.gub.uy/rss/noticias.xml",
    "https://ladiaria.com.uy/feeds/articulos/",
    "https://www.teledoce.com/telemundo/feed/",
    "https://www.telenoche.com.uy/feed"
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def analizar_con_gemini(titular):
    prompt = (
        f"Sos un editor senior uruguayo. ¿Este titular ROMPE LA INERCIA? (Crisis, seguridad, anuncios país). "
        f"Titular: '{titular}'. Responde 'SI' o 'NO' y EXPLICA brevemente."
    )
    
    for modelo in CANDIDATOS:
        try:
            print(f"   🔎 Intentando con {modelo}...")
            response = client.models.generate_content(model=modelo, contents=prompt)
            res = response.text.strip()
            print(f"   ✅ ÉXITO: {res}")
            return "SI" in res.upper()
        except Exception as e:
            error_str = str(e)
            if "404" in error_str:
                print(f"   ❌ {modelo} no encontrado (404).")
            elif "429" in error_str:
                print(f"   ⏳ {modelo} sin cuota (429).")
            else:
                print(f"   ⚠️ Error inesperado en {modelo}: {error_str[:50]}")
            continue 
    return False

print(f"🚀 Patrullaje Transparente v3 - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        print(f"\n📡 Portal: {url}")
        # Analizamos máximo 5 noticias por portal para no quemar la cuota diaria
        for entry in feed.entries[:5]: 
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if ahora - pub_time < timedelta(minutes=25):
                    print(f"🧐 Evaluando: {entry.title}")
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA DE IMPACTO*\n\n{entry.title}\n\n🔗 [Leer]({entry.link})")
                        print(f"   🔔 ALERTA ENVIADA")
                    # PAUSA CRÍTICA: Esperamos 4 segundos entre noticias para evitar bloqueos
                    time.sleep(4) 
            except: continue
    except Exception as e:
        print(f"⚠️ Error en {url}: {e}")

print("\n🏁 Guardia completada.")
