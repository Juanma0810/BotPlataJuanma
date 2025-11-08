import telebot
from flask import Flask, request

TOKEN = "8357510901:AAE1JhJkBMR7cd9Ao0Navp34Xn7qGXoj8hU"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- RUTA PRINCIPAL ---
@app.route('/')
def home():
    return "✅ Bot corriendo en Render"

# --- WEBHOOK PARA RECIBIR MENSAJES ---
@app.route(f"/{TOKEN}", methods=["POST"])
def recibir_mensaje():
    json_str = request.get_data().decode("UTF-8")
    update = telebot.types.Update.de_json(json_str)

    # --- PRUEBA DIRECTA: enviar mensaje ---
    chat_id = update.message.chat.id
    bot.send_message(chat_id, "💬 ¡Hola! Tu mensaje fue recibido correctamente ✅")

    # Procesar handlers (si los agregas después)
    bot.process_new_updates([update])
    return "!", 200

# --- HEALTH CHECK ---
@app.route('/healthz')
def health_check():
    return "Bot is alive!", 200

# --- EJECUCIÓN ---
if __name__ == "__main__":
    WEBHOOK_URL = f"https://botplatajuanma.onrender.com/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print("Webhook configurado en:", WEBHOOK_URL)
