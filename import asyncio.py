import random
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler

TOKEN = "8533834925:AAE85r5P7AeXq9BoizEcfQXAxrk77EdVAwI"

# =========================
# DATABASE (SQLite)
# =========================

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

# =========================
# БАЗА ДАННЫХ
# =========================

styles = ["Minimal", "Luxury", "Tech", "Retro", "Cyberpunk", "Eco", "Corporate", "3D", "Flat", "Glassmorphism"]

symbols = ["Lion", "Wolf", "Eagle", "Phoenix", "Dragon", "Crown", "Shield", "Bolt", "Mountain", "Cube",
           "Circle", "Infinity", "Gear", "Rocket", "Leaf", "Fire", "Water", "Star"]

fonts = ["Montserrat", "Poppins", "Roboto", "Oswald", "Inter", "Futura", "Lato", "Bebas Neue"]

slogans = [
    "Built for Leaders",
    "Design with meaning",
    "Future starts here",
    "Power of simplicity",
    "Stand out",
    "Premium identity"
]

# =========================
# SMART COLOR SYSTEM
# =========================

def hex_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

def palette():
    return f"{hex_color()} + {hex_color()}"

# =========================
# SCENARIOS
# =========================

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
    return random.choice(list(niches.keys()))

# =========================
# SCORING ENGINE (PRO)
# =========================

def score():
    return {
        "Memorability": random.randint(3, 5),
        "Simplicity": random.randint(3, 5),
        "Luxury feel": random.randint(2, 5),
        "Versatility": random.randint(3, 5),
        "Modernity": random.randint(3, 5)
    }

def render_score(sc):
    return "\n".join([f"{k}: {'⭐'*v}{'☆'*(5-v)}" for k, v in sc.items()])

# =========================
# LOGIC ENGINE
# =========================

def generate(name):

    niche = detect_niche(name)

    result = f"""🎨 LOGO DESIGN PRO SYSTEM

Name: {name}
Niche: {niche}

💡 CORE IDEA
Style: {random.choice(styles)}
Palette: {palette()}
Symbol: {random.choice(symbols)}
Font: {random.choice(fonts)}

🔥 CONCEPTS
"""

    concepts = []
    for i in range(10):
        c = {
            "style": random.choice(styles),
            "palette": palette(),
            "symbol": random.choice(symbols),
            "font": random.choice(fonts)
        }
        concepts.append(c)

        result += f"""
{i+1})
Style: {c['style']}
Colors: {c['palette']}
Symbol: {c['symbol']}
Font: {c['font']}
"""

    result += "\n📊 SCORE\n"
    sc = score()
    result += render_score(sc)

    result += f"\n\n💬 Slogan: {random.choice(slogans)}\n"

    return result, concepts

# =========================
# SAVE PROJECT
# =========================

def save(user, name, data):
    cur.execute("INSERT INTO projects (user, name, data) VALUES (?, ?, ?)", (user, name, data))
    conn.commit()

# =========================
# TELEGRAM UI
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("🎨 Новый логотип", callback_data="new")],
        [InlineKeyboardButton("📂 Мои проекты", callback_data="list")]
    ]

    await update.message.reply_text(
        "🚀 LOGO DESIGN PRO BOT",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.data == "new":
        await q.message.reply_text("✍️ Введите название бренда или нишу")
        context.user_data["mode"] = "gen"

    elif q.data == "list":
        cur.execute("SELECT name FROM projects")
        rows = cur.fetchall()

        text = "📂 ПРОЕКТЫ:\n\n"
        for r in rows:
            text += f"• {r[0]}\n"

        await q.message.reply_text(text)

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text
    user = str(update.message.from_user.id)

    if context.user_data.get("mode") == "gen":

        result, concepts = generate(text)

        save(user, text, result)

        for i in range(0, len(result), 4000):
            await update.message.reply_text(result[i:i+4000])

        context.user_data["mode"] = None

    else:
        await update.message.reply_text("Нажми /start")

# =========================
# RUN BOT
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

print("PRO BOT RUNNING...")
app.run_polling()
