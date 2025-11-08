import telebot
import pandas as pd
from datetime import datetime
from flask import Flask
import threading
import os

# --- CONFIGURACIÓN ---
TOKEN = "8357510901:AAE1JhJkBMR7cd9Ao0Navp34Xn7qGXoj8hU"
bot = telebot.TeleBot(TOKEN)

# Archivo Excel donde se guardarán los movimientos
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

    # Tomar el mes y año actuales
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

import matplotlib.pyplot as plt
import io

@bot.message_handler(commands=["grafica"])
def enviar_grafica(msg):
    try:
        if len(df) == 0:
            bot.reply_to(msg, "Aún no tienes datos registrados 📭")
            return

        # Convertir columna de fecha a tipo datetime
        df["Fecha"] = pd.to_datetime(df["Fecha"])

        # Filtrar por mes actual
        mes_actual = datetime.now().month
        df_mes = df[df["Fecha"].dt.month == mes_actual]

        if len(df_mes) == 0:
            bot.reply_to(msg, "No hay movimientos en este mes 📅")
            return

        # Calcular totales
        ingresos = df_mes[df_mes["Tipo"] == "Ingreso"]["Monto"].sum()
        gastos = abs(df_mes[df_mes["Tipo"] == "Gasto"]["Monto"].sum())

        # Crear la gráfica de pastel
        etiquetas = ["Ingresos", "Gastos"]
        valores = [ingresos, gastos]
        colores = ["#4CAF50", "#E53935"]

        fig, ax = plt.subplots()
        ax.pie(valores, labels=etiquetas, autopct="%1.1f%%", colors=colores, startangle=90)
        ax.axis("equal")
        plt.title(f"Distribución de Ingresos y Gastos - {datetime.now().strftime('%B')}")

        # Guardar la imagen en memoria y enviarla al chat
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close(fig)

        bot.send_photo(msg.chat.id, buffer)
    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error al generar la gráfica: {e}")

@bot.message_handler(commands=["historial"])
def grafica_historial(msg):
    try:
        if len(df) == 0:
            bot.reply_to(msg, "Aún no tienes movimientos registrados 📭")
            return

        # Convertir la columna 'Fecha' a tipo datetime
        df["Fecha"] = pd.to_datetime(df["Fecha"])

        # Crear columna 'Mes-Año' para agrupar
        df["Mes"] = df["Fecha"].dt.strftime("%Y-%m")

        # Agrupar ingresos y gastos por mes
        resumen = df.groupby(["Mes", "Tipo"])["Monto"].sum().unstack(fill_value=0)
        resumen["Gasto"] = resumen.get("Gasto", 0).abs()  # valores positivos
        resumen = resumen.sort_index()

        # Crear gráfica de barras
        fig, ax = plt.subplots(figsize=(8, 4))
        resumen[["Ingreso", "Gasto"]].plot(kind="bar", ax=ax)
        plt.title("Histórico mensual de ingresos y gastos")
        plt.xlabel("Mes")
        plt.ylabel("Monto ($)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Guardar en memoria y enviar al chat
        buffer = io.BytesIO()
        plt.savefig(buffer, format="png")
        buffer.seek(0)
        plt.close(fig)

        bot.send_photo(msg.chat.id, buffer)
    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error al generar la gráfica: {e}")

@bot.message_handler(func=lambda message: True)
def responder_mensaje(msg):
    texto = msg.text.lower()

    if "hola" in texto or "buenas" in texto or "Menu" in texto:
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

# --- EJECUCIÓN ---
def iniciar_bot():
    print("🤖 Bot corriendo...")
    bot.polling(none_stop=True, interval=0)

# --- SERVIDOR FLASK PARA RENDER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot funcionando correctamente ✅"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    threading.Thread(target=iniciar_bot).start()
    threading.Thread(target=run_flask).start()