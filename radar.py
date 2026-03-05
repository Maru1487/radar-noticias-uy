import google.generativeai as genai
import feedparser
import requests
import os
import time

# --- CARGA DE LLAVES DESDE GITHUB ---
GEMINI_KEY = os.getenv("GEMINI_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MI_CHAT_ID = os.getenv("MI_CHAT_ID")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# --- FUENTES DE PRUEBA (SOLO DOS) ---
FUENTES = [
    "https://www.elobservador.com.uy/rss/home.xml",
    "https://www.gub.uy/presidencia/rss"
]

# Máscara de navegador para evitar bloqueos
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": MI_CHAT_ID, "text": texto, "parse_mode": "Markdown"})

def analizar(texto):
    prompt = f"Sos un editor uruguayo. ¿Esto es una noticia relevante de hoy? Responde 'SI' o 'NO'. Titular: {texto}"
    try:
        res = model.generate_content(prompt).text.strip()
        return "SI" in res.upper()
    except: return False

print("🔍 Iniciando escaneo de prueba...")
for url in FUENTES:
    try:
        # Leemos el sitio usando la máscara de navegador
        response = requests.get(url, headers=HEADERS, timeout=15)
        feed = feedparser.parse(response.content)
        
        # Tomamos solo la noticia más reciente para la prueba
        if feed.entries:
            entry = feed.entries[0]
            print(f"Leído: {entry.title}")
            # Por ser prueba de vida, mandamos la primera que encuentre siempre
            enviar_telegram(f"✅ *PRUEBA DE LECTURA EXITOSA*\n\nFuente: {url}\nTitular: {entry.title}")
    except Exception as e:
        enviar_telegram(f"❌ *ERROR DE LECTURA*\nFuente: {url}\nError: {str(e)}")

print("Fin de la tarea.")
