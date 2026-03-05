from google.genai import Client
import feedparser
import requests
import os
import time
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN DE SEGURIDAD ---
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

client = Client(api_key=GEMINI_KEY)

# Usamos gemini-1.5-flash por ser el modelo con cuota más estable
CANDIDATO_PRINCIPAL = 'gemini-1.5-flash'

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
    try: 
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"   ⚠️ Error enviando a Telegram: {e}")

def analizar_con_gemini(titular):
    prompt = (
        f"Sos un editor senior uruguayo. Tu tarea es detectar noticias que ROMPAN LA INERCIA (crisis, seguridad, anuncios país). "
        f"Titular: '{titular}'. Responde 'SI' si es un hecho disruptivo o 'NO' si es rutina. EXPLICA brevemente."
    )
    
    try:
        print(f"   🔎 Consultando a {CANDIDATO_PRINCIPAL}...")
        response = client.models.generate_content(model=CANDIDATO_PRINCIPAL, contents=prompt)
        res = response.text.strip()
        print(f"   ✅ RESPUESTA: {res}")
        return "SI" in res.upper()
    except Exception as e:
        print(f"   ⚠️ Falló la consulta a la IA: {str(e)[:100]}...")
        return False

print(f"🚀 Iniciando Patrullaje de Rescate - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        print(f"\n📡 Portal: {url}")
        for entry in feed.entries[:2]: 
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if ahora - pub_time < timedelta(minutes=25):
                    print(f"🧐 Evaluando titular: {entry.title}")
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA DE IMPACTO*\n\n{entry.title}\n\n🔗 [Leer noticia]({entry.link})")
                        print(f"   🔔 ALERTA ENVIADA A TELEGRAM")
                    
                    # PAUSA DE SEGURIDAD: 12 segundos para no superar los límites gratuitos
                    time.sleep(12) 
            except Exception:
                continue
    except Exception as e:
        print(f"⚠️ Error conectando con {url}: {e}")

print("\n🏁 Guardia completada correctamente.")
