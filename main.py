
import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

TOKEN = "8533834925:AAE85r5P7AeXq9BoizEcfQXAxrk77EdVAwI"

conn = sqlite3.connect("logos.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT,
    name TEXT,
    data TEXT
)
""")
conn.commit()

styles = ["Minimal", "Luxury", "Tech", "Retro", "Cyberpunk", "Eco", "Corporate", "3D", "Flat", "Glassmorphism"]
symbols = ["Lion","Wolf","Eagle","Phoenix","Dragon","Crown","Shield","Bolt","Mountain","Cube","Infinity","Gear","Rocket","Leaf","Fire","Water","Star"]
fonts = ["Montserrat","Poppins","Roboto","Oswald","Inter","Futura","Lato","Bebas Neue"]
slogans = ["Built for Leaders","Design with meaning","Future starts here","Power of simplicity","Stand out","Premium identity"]

def hex_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def palette():
    return f"{hex_color()} + {hex_color()}"

niches = {
    "it": ["Tech", "Minimal", "Cyberpunk"],
    "coffee": ["Eco", "Retro", "Warm"],
    "car": ["Aggressive", "Metal", "Sport"],
    "finance": ["Corporate", "Luxury", "Minimal"],
    "game": ["Cyberpunk", "Neon", "Dark"],
}

def detect_niche(text):
    t = text.lower()
    for k in niches:
        if k in t:
            return k
    return "it"

def score():
    return {
        "Memorability": random.randint(3,5),
        "Simplicity": random.randint(3,5),
        "Luxury": random.randint(2,5),
        "Versatility": random.randint(3,5),
        "Modernity": random.randint(3,5)
    }

def render_score(sc):
    return "\\n".join([f"{k}: {'⭐'*v}{'☆'*(5-v)}" for k,v in sc.items()])

def generate(name):
    niche = detect_niche(name)

    text = f"LOGO PRO BOT\\nName: {name}\\nNiche: {niche}\\n\\n"

    text += "CORE IDEA\\n"
    text += f"Style: {random.choice(styles)}\\n"
    text += f"Palette: {palette()}\\n"
    text += f"Symbol: {random.choice(symbols)}\\n"
    text += f"Font: {random.choice(fonts)}\\n\\n"

    text += "10 CONCEPTS\\n"
    for i in range(10):
        text += f"{i+1}) {random.choice(styles)} | {palette()} | {random.choice(symbols)} | {random.choice(fonts)}\\n"

    text += "\\nSCORE\\n"
    sc = score()
    text += render_score(sc)

    text += f"\\nSlogan: {random.choice(slogans)}\\n"
    return text

def save(user, name, data):
    cur.execute("INSERT INTO projects(user,name,data) VALUES(?,?,?)", (user,name,data))
    conn.commit()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("New Logo", callback_data="new")],
                [InlineKeyboardButton("Projects", callback_data="list")]]
    await update.message.reply_text("LOGO BOT PRO", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "new":
        await q.message.reply_text("Send name")
        context.user_data["mode"] = "gen"

    if q.data == "list":
        cur.execute("SELECT name FROM projects")
        rows = cur.fetchall()
        await q.message.reply_text("\\n".join([r[0] for r in rows]) if rows else "Empty")

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    user = str(update.message.from_user.id)

    if context.user_data.get("mode") == "gen":
        result = generate(text)
        save(user, text, result)

        for i in range(0,len(result),4000):
            await update.message.reply_text(result[i:i+4000])

        context.user_data["mode"] = None

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

app.run_polling()
