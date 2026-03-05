import google.generativeai as genai
import feedparser
import requests
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Usamos .strip() para limpiar cualquier espacio invisible en tus Secrets de GitHub
GEMINI_KEY = os.getenv("GEMINI_KEY", "").strip()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

# Configuración del cerebro (Gemini)
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- LAS 8 FUENTES PATRULLADAS ---
# Lista actualizada y validada según tus pruebas manuales
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

# Máscara de navegador para evitar bloqueos de seguridad
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

def enviar_telegram(texto):
    """Envía la alerta al bot de Telegram configurado."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": texto, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def analizar_con_gemini(titular):
    """Usa IA para decidir si la noticia es de alto impacto para Uruguay."""
    prompt = (
        f"Sos un editor senior uruguayo. ¿Este titular es una RUPTURA DE INERCIA informativa? "
        f"(Primicias, seguridad, crisis política, interpelaciones o grandes anuncios país). "
        f"Titular: '{titular}'. Responde 'SI' si es impacto o 'NO' si es rutina."
    )
    try:
        res = model.generate_content(prompt).text.strip().upper()
        return "SI" in res
    except:
        return False

print(f"🚀 Iniciando Radar Profesional - {datetime.now()}")

for url in FUENTES:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(r.content)
        ahora = datetime.now(timezone.utc)
        
        # Analizamos las 8 noticias más recientes de cada medio
        for entry in feed.entries[:8]: 
            try:
                # Extraemos la hora de publicación
                pub_time = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                
                # FILTRO DE TIEMPO: Solo noticias de los últimos 25 minutos
                if ahora - pub_time < timedelta(minutes=25):
                    if analizar_con_gemini(entry.title):
                        # Si Gemini da el visto bueno, mandamos la alerta
                        enviar_telegram(f"🚨 *ALERTA DE IMPACTO*\n\n{entry.title}\n\n🔗 [Ver noticia]({entry.link})")
                        print(f"✅ Alerta enviada: {entry.title}")
            except:
                continue
            
    except Exception as e:
        print(f"⚠️ Error leyendo {url}: {e}")

print("🏁 Guardia completada. Entrando en modo espera (10 min).")
