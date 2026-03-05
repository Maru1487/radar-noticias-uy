import google.generativeai as genai
import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN DE SEGURIDAD ---
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

# Configuración del motor (Usamos gemini-1.5-flash por estabilidad)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- LAS 8 FUENTES PATRULLADAS (Validadas) ---
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
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def analizar_con_gemini(titular):
    """Criterio de Editor de Cierre Uruguayo."""
    prompt = (
        f"Sos un editor senior uruguayo. Tu tarea es detectar noticias que ROMPAN LA INERCIA en Uruguay. "
        f"\n\nCRITERIOS DE 'SI':"
        f"\n1. Crisis política, renuncias, interpelaciones o escándalos de impacto nacional."
        f"\n2. Reacciones o posturas de autoridades (ej: 'preocupación del equipo económico', 'anuncio de Presidencia')."
        f"\n3. Siniestros fatales o hechos de seguridad (en Uruguay esto SIEMPRE se considera noticia de impacto)."
        f"\n4. Cambios bruscos en servicios o economía (tarifazos, cortes masivos, saltos bruscos del dólar)."
        f"\n\nCRITERIOS DE 'NO' (BLOQUEO ABSOLUTO):"
        f"\n- DEPORTES: Fútbol, resultados, pases o declaraciones de jugadores."
        f"\n- INTERNACIONALES: Noticias ocurridas fuera de Uruguay (salvo impacto directo en el país)."
        f"\n- RUTINA: Clima normal, agenda parlamentaria de trámite, noticias de color."
        f"\n\nTitular: '{titular}'. Responde 'SI' si es impacto o 'NO' si es rutina."
    )
    try:
        res = model.generate_content(prompt).text.strip().upper()
        return "SI" in res
    except:
        return False

print(f"🚀 Radar Profesional (Criterio Editor) - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        for entry in feed.entries[:8]: 
            try:
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                # Analizamos noticias de los últimos 25 minutos
                if ahora - pub_time < timedelta(minutes=25):
                    if analizar_con_gemini(entry.title):
                        enviar_telegram(f"🚨 *ALERTA DE IMPACTO*\n\n{entry.title}\n\n🔗 [Ver noticia]({entry.link})")
                        print(f"✅ Alerta enviada: {entry.title}")
            except:
                continue
            
    except Exception as e:
        print(f"⚠️ Error en {url}: {e}")

print("🏁 Guardia completada.")
