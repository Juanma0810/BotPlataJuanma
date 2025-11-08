import telebot
import pandas as pd
from datetime import datetime
from flask import Flask
import threading
import os
import matplotlib.pyplot as plt
import io

# --- CONFIGURACIÓN ---
TOKEN = "8357510901:AAE1JhJkBMR7cd9Ao0Navp34Xn7qGXoj8hU"
bot = telebot.TeleBot(TOKEN)

ARCHIVO = "movimientos.xlsx"

# Crear archivo si no existe
try:
    df = pd.read_excel(ARCHIVO)
except FileNotFoundError:
    df = pd.DataFrame(columns=["Fecha", "Tipo", "Descripción", "Monto", "Saldo"])
    df.to_excel(ARCHIVO, index=False)

# --- FUNCIONES ---
def registrar_movimiento(tipo, descripcion, monto):
    global df
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    monto = float(monto)
    saldo = df["Saldo"].iloc[-1] + monto if len(df) > 0 else monto
    nuevo = pd.DataFrame([[fecha, tipo, descripcion, monto, saldo]], columns=df.columns)
    df = pd.concat([df, nuevo], ignore_index=True)
    df.to_excel(ARCHIVO, index=False)
    return saldo

# --- COMANDOS ---
@bot.message_handler(commands=["start"])
def bienvenida(msg):
    bot.reply_to(msg, "👋 ¡Hola Juanma! Soy tu bot de control de plata 💰\n\nUsa:\n💵 /ingreso [monto] [descripción]\n💸 /gasto [monto] [descripción]\n📊 /saldo para ver tu saldo actual.")

@bot.message_handler(commands=["ingreso"])
def ingreso(msg):
    try:
        _, monto, *desc = msg.text.split()
        desc = " ".join(desc)
        saldo = registrar_movimiento("Ingreso", desc, monto)
        bot.reply_to(msg, f"✅ Ingreso registrado: +${monto}\nNuevo saldo: ${saldo:,.0f}")
    except:
        bot.reply_to(msg, "❗ Usa el formato: /ingreso 50000 trabajo")

@bot.message_handler(commands=["gasto"])
def gasto(msg):
    try:
        _, monto, *desc = msg.text.split()
        desc = " ".join(desc)
        saldo = registrar_movimiento("Gasto", desc, -float(monto))
        bot.reply_to(msg, f"💸 Gasto registrado: -${monto}\nNuevo saldo: ${saldo:,.0f}")
    except:
        bot.reply_to(msg, "❗ Usa el formato: /gasto 20000 gasolina")

@bot.message_handler(commands=["saldo"])
def saldo(msg):
    if len(df) == 0:
        bot.reply_to(msg, "No tienes registros aún 💬")
    else:
        bot.reply_to(msg, f"📊 Tu saldo actual es: ${df['Saldo'].iloc[-1]:,.0f}")

# --- RESPUESTA A MENSAJES NORMALES ---
@bot.message_handler(func=lambda message: True)
def responder_mensaje(msg):
    texto = msg.text.lower()
    if "hola" in texto or "buenas" in texto:
        respuesta = (
            "👋 ¡Hola Juanma! Aquí tienes las opciones disponibles:\n\n"
            "💵 *Registrar ingreso:* `/ingreso [monto] [descripción]`\n"
            "💸 *Registrar gasto:* `/gasto [monto] [descripción]`\n"
            "📊 *Ver saldo actual:* `/saldo`\n"
            "📅 *Resumen del mes:* `/resumen`\n"
            "📈 *Gráfica del mes:* `/grafica`\n"
            "📆 *Historial mensual:* `/historial`\n\n"
            "💬 Ejemplo: `/ingreso 50000 plata abuelos`"
        )
        bot.reply_to(msg, respuesta, parse_mode="Markdown")
    else:
        bot.reply_to(msg, "🤖 No reconozco ese comando. Escribe *Hola* para ver las opciones disponibles.", parse_mode="Markdown")

# --- SERVIDOR FLASK SOLO PARA HEALTH CHECK ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot funcionando correctamente ✅"

@app.route('/healthz')
def health_check():
    return "Bot is alive!", 200

# --- EJECUCIÓN ---
def iniciar_bot():
    print("🤖 Bot corriendo con polling...")
    bot.polling(none_stop=True, interval=0)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    print(f"🌐 Servidor Flask corriendo en el puerto {port}")
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=iniciar_bot).start()
    run_flask()
