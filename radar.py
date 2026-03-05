import google.generativeai as genai
import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN DE LLAVES ---
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- FUENTES DE URUGUAY ---
FUENTES = [
    "https://www.elobservador.com.uy/rss/home.xml",
    "https://www.elpais.com.uy/rss/ultimo-momento",
    "https://www.subrayado.com.uy/rss/ultimo-momento",
    "https://www.montevideo.com.uy/anxml.aspx?1",
    "https://www.gub.uy/presidencia/rss"
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    requests.post(url, json=payload, timeout=10)

def analizar_con_gemini(titular):
    prompt = (
        f"Sos un editor senior de un diario uruguayo. Tu tarea es detectar noticias de ALTO IMPACTO "
        f"(Ruptura de inercia, primicias, crisis política, seguridad grave, anuncios de infraestructura). "
        f"Titular: '{titular}'. Responde ÚNICAMENTE con la palabra 'SI' si es relevante o 'NO' si es rutina."
    )
    try:
        res = model.generate_content(prompt).text.strip().upper()
        return "SI" in res
    except: return False

print(f"🚀 Radar Iniciado - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        for entry in feed.entries[:5]: # Miramos las 5 más nuevas de cada sitio
            # Solo procesamos si la noticia tiene menos de 20 minutos de publicada
            # (Para evitar alertas repetidas en cada corrida de 10 minutos)
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                if ahora - pub_time < timedelta(minutes=20):
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA DE IMPACTO*\n\n{entry.title}\n\n🔗 [Leer más]({entry.link})")
                        print(f"✅ Alerta enviada: {entry.title}")
            except: continue
            
    except Exception as e:
        print(f"Error leyendo {url}: {e}")

print("🏁 Guardia completada.")
