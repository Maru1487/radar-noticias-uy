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

# --- SISTEMA DE SELECCIÓN AUTOMÁTICA ---
# Esto evita el error 404 buscando qué nombre exacto acepta tu cuenta
MODELO_PARA_USAR = None
try:
    print("🔍 Buscando modelos habilitados en tu cuenta...")
    for m in client.models.list():
        # Preferimos la versión 1.5 por estabilidad, pero aceptamos 2.0 si es lo único que hay
        if 'gemini-1.5-flash' in m.name or 'gemini-2.0-flash-lite' in m.name:
            MODELO_PARA_USAR = m.name # Usamos el nombre completo (ej: models/gemini-1.5-flash)
            break
    
    if MODELO_PARA_USAR:
        print(f"✅ Modelo detectado y listo: {MODELO_PARA_USAR}")
    else:
        MODELO_PARA_USAR = 'models/gemini-1.5-flash' # Respaldo final
except Exception as e:
    print(f"❌ No pude listar modelos: {e}. Usaré respaldo.")
    MODELO_PARA_USAR = 'models/gemini-1.5-flash'

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
    try:
        # PAUSA CRÍTICA: Esperamos 20 segundos antes de cada consulta para evitar el error 429 (cuota agotada)
        time.sleep(20)
        response = client.models.generate_content(model=MODELO_PARA_USAR, contents=prompt)
        res = response.text.strip()
        print(f"   🤖 Decisión: {res}")
        return "SI" in res.upper()
    except Exception as e:
        print(f"   ❌ Error en análisis: {e}")
        return False

print(f"🚀 Radar v2.0 Final - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=40)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        print(f"\n📡 Portal: {url}")
        # Analizamos SOLO la noticia más reciente de cada portal para maximizar el éxito con la cuota gratuita
        for entry in feed.entries[:1]: 
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if ahora - pub_time < timedelta(minutes=45):
                    print(f"🧐 Analizando: {entry.title}")
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA*\n\n{entry.title}\n\n🔗 [Leer]({entry.link})")
                        print("   🔔 Alerta enviada")
            except: continue
    except Exception as e:
        print(f"⚠️ Error en {url}: {e}")

print("\n🏁 Guardia completada.")
