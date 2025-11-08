import telebot
from flask import Flask, request

TOKEN = "8357510901:AAE1JhJkBMR7cd9Ao0Navp34Xn7qGXoj8hU"
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# --- HANDLER SIMPLE ---
@bot.message_handler(func=lambda m: True)
def responder(msg):
    bot.reply_to(msg, f"✅ Recibí tu mensaje: {msg.text}")

# --- RUTAS DE FLASK ---
@app.route('/')
def home():
    return "Bot Test corriendo en Render"

@app.route(f"/{TOKEN}", methods=["POST"])
def recibir_mensaje():
    update = telebot.types.Update.de_json(request.get_data().decode("UTF-8"))
    bot.process_new_updates([update])
    return "!", 200

@app.route('/healthz')
def health_check():
    return "Bot alive!", 200

# --- CONFIGURAR WEBHOOK ---
if __name__ == "__main__":
    WEBHOOK_URL = f"https://botplatajuanma.onrender.com/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print("Webhook configurado en Render")
