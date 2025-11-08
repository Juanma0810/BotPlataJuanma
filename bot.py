import telebot
import pandas as pd
from datetime import datetime
from flask import Flask, request
import os
import matplotlib.pyplot as plt
import io

# --- CONFIGURACIÓN ---
TOKEN = "8357510901:AAE1JhJkBMR7cd9Ao0Navp34Xn7qGXoj8hU"
bot = telebot.TeleBot(TOKEN)

# --- HANDLER DE PRUEBA PARA DEBUG ---
@bot.message_handler(func=lambda m: True)
def test_responder(msg):
    print("Intentando responder a:", msg.text)  # log para ver en Render
    bot.reply_to(msg, "Recibido tu mensaje ✅")

ARCHIVO = "movimientos.xlsx"

# Si no existe el archivo, crear estructura inicial
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

@bot.message_handler(commands=["resumen"])
def resumen(msg):
    if len(df) == 0:
        bot.reply_to(msg, "Aún no tienes movimientos registrados 📭")
        return

    mes_actual = datetime.now().strftime("%Y-%m")
    df_mes = df[df["Fecha"].str.startswith(mes_actual)]

    if len(df_mes) == 0:
        bot.reply_to(msg, "No tienes movimientos este mes 📅")
        return

    ingresos = df_mes[df_mes["Tipo"] == "Ingreso"]["Monto"].sum()
    gastos = abs(df_mes[df_mes["Tipo"] == "Gasto"]["Monto"].sum())
    ahorro = ingresos - gastos

    respuesta = (
        f"📊 *Resumen del mes {datetime.now().strftime('%B')}*\n\n"
        f"💵 Ingresos: ${ingresos:,.0f}\n"
        f"💸 Gastos: ${gastos:,.0f}\n"
        f"💰 Ahorro: ${ahorro:,.0f}\n\n"
        f"Último saldo: ${df['Saldo'].iloc[-1]:,.0f}"
    )
    bot.reply_to(msg, respuesta, parse_mode="Markdown")

@bot.message_handler(commands=["grafica"])
def enviar_grafica(msg):
    try:
        if len(df) == 0:
            bot.reply_to(msg, "Aún no tienes datos registrados 📭")
            return

        df["Fecha"] = pd.to_datetime(df["Fecha"])
        mes_actual = datetime.now().month
        df_mes = df[df["Fecha"].dt.month == mes_actual]

        if len(df_mes) == 0:
            bot.reply_to(msg, "No hay movimientos en este mes 📅")
            return

        ingresos = df_mes[df_mes["Tipo"] == "Ingreso"]["Monto"].sum()
        gastos = abs(df_mes[df_mes["Tipo"] == "Gasto"]["Monto"].sum())

        etiquetas = ["Ingresos", "Gastos"]
        valores = [ingresos, gastos]
        colores = ["#4CAF50", "#E53935"]

        fig, ax = plt.subplots()
        ax.pie(valores, labels=etiquetas, autopct="%1.1f%%", colors=colores, startangle=90)
        ax.axis("equal")
        plt.title(f"Distribución de Ingresos y Gastos - {datetime.now().strftime('%B')}")

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close(fig)

        bot.send_photo(msg.chat.id, buffer)
    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error al generar la gráfica: {e}")

#@bot.message_handler(func=lambda message: True)
#def responder_mensaje(msg):
    #texto = msg.text.lower()
    #if "hola" in texto or "buenas" in texto:
       # respuesta = (
            #"👋 ¡Hola Juanma! Aquí tienes las opciones disponibles:\n\n"
           # "💵 *Registrar ingreso:* `/ingreso [monto] [descripción]`\n"
           # "💸 *Registrar gasto:* `/gasto [monto] [descripción]`\n"
            #"📊 *Ver saldo actual:* `/saldo`\n"
            #"📅 *Resumen del mes:* `/resumen`\n"
            #"📈 *Gráfica del mes:* `/grafica`\n\n"
           # "💬 Ejemplo: `/ingreso 50000 plata abuelos`"
       # )
     #   bot.reply_to(msg, respuesta, parse_mode="Markdown")
   # else:
      #  bot.reply_to(msg, "🤖 No reconozco ese comando. Escribe *Hola* para ver las opciones disponibles.", parse_mode="Markdown")

# --- FLASK PARA RENDER (USANDO WEBHOOK) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot MiPlataJuanma corriendo en Render"

@app.route(f"/{TOKEN}", methods=["POST"])
def recibir_mensaje():
    json_str = request.get_data().decode("UTF-8")
    print("Recibido POST de Telegram:", json_str)  # <--- AGREGAR ESTA LÍNEA
    update = telebot.types.Update.de_json(json_str)
    print("Update parseado:", update)  # <--- AGREGAR ESTA LÍNEA
    bot.process_new_updates([update])
    return "!", 200

# --- NUEVA RUTA PARA HEALTH CHECK ---
@app.route('/healthz')
def health_check():
    return "Bot is alive!", 200

# --- EJECUCIÓN ---
if __name__ == "__main__":
    WEBHOOK_URL = f"https://botplatajuanma.onrender.com/{TOKEN}"
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    #"port = int(os.environ.get("PORT", 10000))
    #app.run(host="0.0.0.0", port=port)
