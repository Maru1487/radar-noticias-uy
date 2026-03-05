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

# Simplificamos a los modelos que GitHub SÍ localizó en tu cuenta
CANDIDATOS = [
    'gemini-2.0-flash-001', # Nombre técnico directo
    'gemini-2.0-flash', 
    'gemini-2.0-flash-lite-preview-02-05' # El que suele tener más cuota libre
]

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
    try: requests.post(url, json=payload, timeout=10)
    except: pass

def analizar_con_gemini(titular):
    prompt = (
        f"Sos un editor senior uruguayo. ¿Este titular ROMPE LA INERCIA? (Crisis, seguridad, anuncios país). "
        f"Titular: '{titular}'. Responde 'SI' o 'NO' y EXPLICA brevemente."
    )
    
    for modelo in CANDIDATOS:
        try:
            print(f"   🔎 Consultando a {modelo}...")
            response = client.models.generate_content(model=modelo, contents=prompt)
            res = response.text.strip()
            print(f"   ✅ RESPUESTA: {res}")
            return "SI" in res.upper()
        except Exception as e:
            print(f"   ⚠️ {modelo} ocupado/sin cuota.")
            time.sleep(10) # Pausa larga si hay error para recuperar cuota
            continue 
    return False

print(f"🚀 Patrullaje Estratégico - {datetime.now()}")
# PAUSA INICIAL: Esperamos 15 segundos para que la API se limpie antes de empezar
print("⏳ Esperando ventana de cuota...")
time.sleep(15)

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        print(f"\n📡 Portal: {url}")
        for entry in feed.entries[:3]: # Solo 3 noticias por portal para máxima seguridad de cuota
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if ahora - pub_time < timedelta(minutes=25):
                    print(f"🧐 Evaluando: {entry.title}")
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA DE IMPACTO*\n\n{entry.title}\n\n🔗 [Leer]({entry.link})")
                        print(f"   🔔 ALERTA ENVIADA")
                    # Pausa de 10 segundos entre noticias: lento pero SEGURO
                    time.sleep(10) 
            except: continue
    except Exception as e:
        print(f"⚠️ Error en {url}: {e}")

print("\n🏁 Guardia completada.")
