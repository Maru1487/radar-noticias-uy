import google.generativeai as genai
import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN ---
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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
    # Prompt ajustado para que nos dé el "Por qué" en el log
    prompt = (
        f"Sos un editor senior uruguayo. ¿Este titular ROMPE LA INERCIA? (Crisis, seguridad, anuncios país). "
        f"Titular: '{titular}'. Responde 'SI' o 'NO' y EXPLICA brevemente tu razonamiento periodístico."
    )
    try:
        res = model.generate_content(prompt).text.strip()
        # Imprimimos la respuesta completa de la IA en el log de GitHub
        print(f"   🤖 Decisión IA: {res}")
        return "SI" in res.upper()
    except: return False

print(f"🚀 Iniciando patrullaje transparente - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        print(f"\n📡 Portal: {url}") # Para saber qué sitio está leyendo
        for entry in feed.entries[:8]: 
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                # Solo analizamos si es una noticia "fresca" (últimos 25 min)
                if ahora - pub_time < timedelta(minutes=25):
                    print(f"🧐 Evaluando: {entry.title}")
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA DE IMPACTO*\n\n{entry.title}\n\n🔗 [Leer]({entry.link})")
                        print(f"   ✅ ALERTA ENVIADA")
                else:
                    # Esto te confirma que el bot vio la noticia pero la ignoró por ser antigua
                    pass 
            except: continue
            
    except Exception as e:
        print(f"⚠️ Error en {url}: {e}")

print("\n🏁 Guardia completada.")
