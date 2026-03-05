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

# Lista de nombres que Google acepta según la región y tipo de cuenta
MODELOS_A_PROBAR = ['gemini-1.5-flash', 'gemini-1.5-flash-002', 'gemini-1.5-flash-latest']

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
    try: requests.post(url, json=payload, timeout=20)
    except: pass

def analizar_con_gemini(titular):
    prompt = (
        f"Sos un editor uruguayo. ¿Este titular es una RUPTURA DE INERCIA (crisis, seguridad, anuncios país)? "
        f"Responde SI o NO y explica en una frase. Titular: '{titular}'"
    )
    
    # Intentamos con los 3 nombres posibles hasta que uno funcione
    for m in MODELOS_A_PROBAR:
        try:
            response = client.models.generate_content(model=m, contents=prompt)
            print(f"   ✅ Respuesta ({m}): {response.text.strip()}")
            return "SI" in response.text.upper()
        except Exception as e:
            if "404" in str(e):
                continue # Probamos el siguiente nombre
            print(f"   ⚠️ Error con {m}: {str(e)[:50]}")
    return False

print(f"🚀 Guardia de Emergencia - {datetime.now()}")

for url in FUENTES:
    try:
        # Aumentamos el timeout a 30 segundos para evitar el error de La Diaria
        r = requests.get(url, headers=HEADERS, timeout=30)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        print(f"\n📡 Portal: {url}")
        for entry in feed.entries[:3]: 
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if ahora - pub_time < timedelta(minutes=25):
                    print(f"🧐 Analizando: {entry.title}")
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA*\n\n{entry.title}\n\n🔗 [Leer]({entry.link})")
                        print("   🔔 Alerta enviada")
                    time.sleep(5) # Pausa para no saturar la cuota
            except: continue
    except Exception as e:
        print(f"⚠️ Error en {url}: {e}")

print("\n🏁 Fin de guardia.")
