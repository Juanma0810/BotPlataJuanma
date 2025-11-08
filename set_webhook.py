import telebot

# --- CONFIGURACIÓN ---
TOKEN = "8357510901:AAE1JhJkBMR7cd9Ao0Navp34Xn7qGXoj8hU"  # tu token de Telegram
WEBHOOK_URL = f"https://botplatajuanma.onrender.com/{TOKEN}"  # URL pública de Render + token
bot = telebot.TeleBot(TOKEN)

# --- ELIMINAR WEBHOOK ANTIGUO ---
bot.remove_webhook()

# --- CONFIGURAR NUEVO WEBHOOK ---
bot.set_webhook(url=WEBHOOK_URL)

print("✅ Webhook configurado para Render correctamente")
