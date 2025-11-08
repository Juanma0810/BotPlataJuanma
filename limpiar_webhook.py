import telebot

TOKEN = "8357510901:AAE1JhJkBMR7cd9Ao0Navp34Xn7qGXoj8hU"  # tu token
bot = telebot.TeleBot(TOKEN)

# Remueve cualquier webhook existente
bot.remove_webhook()
print("✅ Webhook eliminado correctamente")
