import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from openai import OpenAI

# ======================
# ENV (Render SAFE)
# ======================

TOKEN = os.getenv("8675822721:AAH_1ue0TDuiZSNoI4TLaWmrpuGu80WZDiY")
OPENAI_KEY = os.getenv("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")

if not TOKEN:
    print("8675822721:AAH_1ue0TDuiZSNoI4TLaWmrpuGu80WZDiY")
    exit()

if not OPENAI_KEY:
    print("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")
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
        "🎨 AI Logo Bot Pro\n\nВыбери действие:",
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
# IDEA INPUT
# ======================
@dp.message(F.text == "✨ Generate Logo")
async def ask_idea(message: Message):
    await message.answer("💡 Напиши идею логотипа")

# ======================
# GENERATE IMAGE
# ======================
@dp.message(F.text)
async def generate(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")

    prompt = (
        f"Modern logo, style {style}, idea: {message.text}, "
        "clean vector branding, high quality, minimal, 8k"
    )

    await message.answer("🎨 Генерация...")

    try:
        result = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            size="1024x1024"
        )

        image_url = result.data[0].url

        await message.answer_photo(
            photo=image_url,
            caption=f"🎨 Style: {style}"
        )

    except Exception as e:
        await message.answer(f"❌ Ошибка:\n{e}")

# ======================
# START BOT
# ======================
async def main():
    print("🚀 Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
