import requests
import os

# Traemos las llaves y les quitamos espacios invisibles (.strip())
TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
CHAT_ID = os.getenv("MY_CHAT_ID", "").strip()

def test_telegram(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": msg}
    res = requests.post(url, json=payload)
    return res.status_code, res.text

# Probamos con Google para ver si hay internet libre
URL_TEST = "https://www.google.com"

print("🕵️ MODO FORENSE V3 ACTIVADO")
try:
    r = requests.get(URL_TEST, timeout=10)
    print(f"Status Google: {r.status_code}") # Debería ser 200
    
    # Intentamos el envío y capturamos la respuesta completa de Telegram
    status_t, respuesta = test_telegram("🚀 PRUEBA V3: Si llega esto, el caño está limpio.")
    print(f"Status Telegram: {status_t}")
    print(f"Respuesta de Telegram: {respuesta}") # Esto nos dirá el error exacto
    
except Exception as e:
    print(f"Error de conexión: {e}")

print("Fin del análisis.")
