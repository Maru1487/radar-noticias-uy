import requests
import os

# Traemos las llaves EXACTAMENTE como están en tu captura
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("MY_CHAT_ID") # Corregido a 'MY' con Y

def test_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    res = requests.post(url, json={"chat_id": CHAT_ID, "text": msg})
    return res.status_code

# Probamos con Presidencia para asegurar un status 200
URL_TEST = "https://www.gub.uy/presidencia/rss"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}

print("🕵️ MODO FORENSE V2 ACTIVADO")
try:
    r = requests.get(URL_TEST, headers=HEADERS, timeout=15)
    print(f"Status Presidencia: {r.status_code}")
    
    # Intentamos mandar el reporte al Telegram
    status_t = test_telegram(f"📡 PRUEBA EXITOSA\n\nStatus Presidencia: {r.status_code}\n\n¡Al fin! El radar ya tiene conexión total.")
    print(f"Status envío Telegram: {status_t}")
    
except Exception as e:
    print(f"Error: {e}")

print("Fin del análisis.")
