import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI

# ======================
# ENV (Railway safe)
# ======================

TOKEN = os.getenv("BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# ⚠️ НЕ ПАДАЕМ, просто лог
if not TOKEN:
    print("❌ BOT_TOKEN не найден в Railway Variables")
if not OPENAI_KEY:
    print("❌ OPENAI_API_KEY не найден в Railway Variables")

if not TOKEN or not OPENAI_KEY:
    print("⛔ Бот не запущен: нет ENV переменных")
    exit()

bot = Bot(token=TOKEN)
dp = Dispatcher()
client = OpenAI(api_key=OPENAI_KEY)

# ======================
# DATA
# ======================
user_style = {}

# ======================
# KEYBOARDS
# ======================

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎨 Styles"), KeyboardButton(text="✨ Generate Logo")]
    ],
    resize_keyboard=True
)

styles_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Minimalism"), KeyboardButton(text="Cyberpunk")],
        [KeyboardButton(text="Luxury"), KeyboardButton(text="Neon")],
        [KeyboardButton(text="Futuristic"), KeyboardButton(text="Gaming")],
        [KeyboardButton(text="Retro"), KeyboardButton(text="Tech")]
    ],
    resize_keyboard=True
)

# ======================
# START
# ======================
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 AI Logo Bot (Railway)\n\nВыбери действие:",
        reply_markup=main_kb
    )

# ======================
# STYLES
# ======================
@dp.message(F.text == "🎨 Styles")
async def styles(message: Message):
    await message.answer("🎯 Выбери стиль:", reply_markup=styles_kb)

# ======================
# SET STYLE
# ======================
@dp.message(F.text.in_([
    "Minimalism","Cyberpunk","Luxury","Neon",
    "Futuristic","Gaming","Retro","Tech"
]))
async def set_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(f"✅ Стиль: {message.text}")

# ======================
# ASK IDEA
# ======================
@dp.message(F.text == "✨ Generate Logo")
async def ask_idea(message: Message):
    await message.answer("💡 Напиши идею логотипа")

# ======================
# GENERATE LOGO
# ======================
@dp.message(F.text)
async def generate(message: Message):
    try:
        style = user_style.get(message.from_user.id, "Minimalism")

        prompt = (
            f"Modern professional logo, style {style}, "
            f"idea: {message.text}, "
            "clean vector logo, minimal, high quality, 8k"
        )

        await message.answer("🎨 Генерация логотипа...")

        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        image_url = result.data[0].url

        await message.answer_photo(
            photo=image_url,
            caption=f"🎨 Готово!\nStyle: {style}"
        )

    except Exception as e:
        await message.answer("⚠️ Ошибка генерации, попробуй ещё раз")
        print("ERROR:", e)

# ======================
# RUN BOT (Railway safe)
# ======================
async def main():
    print("🚀 Bot started on Railway")

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print("FATAL ERROR:", e)

if __name__ == "__main__":
    asyncio.run(main())
