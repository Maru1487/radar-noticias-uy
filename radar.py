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

# FORZAMOS el único modelo que garantiza cuota gratuita real hoy
MODELO_PARA_USAR = 'gemini-1.5-flash'

FUENTES = [
    "https://www.elobservador.com.uy/rss/home.xml",
    "https://www.elpais.com.uy/rss/latest",
    "https://www.subrayado.com.uy/anxml.aspx?0",
    "https://www.montevideo.com.uy/anxml.aspx?59",
    "https://ladiaria.com.uy/feeds/articulos/",
    "https://www.teledoce.com/telemundo/feed/",
    "https://www.telenoche.com.uy/feed"
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try: requests.post(url, json=payload, timeout=30)
    except: pass

def analizar_con_gemini(titular):
    prompt = (
        f"Sos un editor uruguayo. ¿Este titular es una RUPTURA DE INERCIA (crisis, seguridad, anuncios país)? "
        f"Responde SI o NO y explica en una frase. Titular: '{titular}'"
    )
    intentos = 0
    while intentos < 2: # Si da error de cuota, reintenta una vez
        try:
            response = client.models.generate_content(model=MODELO_PARA_USAR, contents=prompt)
            texto_ia = response.text.strip()
            print(f"   🤖 Decisión: {texto_ia}")
            return "SI" in texto_ia.upper()
        except Exception as e:
            if "429" in str(e):
                print(f"   ⏳ Esperando 20s por cuota...")
                time.sleep(20)
                intentos += 1
            else:
                print(f"   ❌ Error IA: {str(e)[:50]}")
                return False
    return False

print(f"🚀 Radar v1.5 Estable - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=40)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        print(f"\n📡 Portal: {url}")
        for entry in feed.entries[:2]: # Analizamos las 2 más frescas
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if ahora - pub_time < timedelta(minutes=40):
                    print(f"🧐 Analizando: {entry.title}")
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA*\n\n{entry.title}\n\n🔗 [Leer]({entry.link})")
                        print("   🔔 Alerta enviada")
                    time.sleep(10) # Pausa entre noticias
            except: continue
    except Exception as e:
        print(f"⚠️ Error en {url}: {e}")

print("\n🏁 Guardia completada.")
