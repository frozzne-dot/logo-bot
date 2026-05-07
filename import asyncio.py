import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("8675822721:AAH_1ue0TDuiZSNoI4TLaWmrpuGu80WZDiY")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# хранение выбранного стиля (в памяти)
user_style = {}


# --- КНОПКИ СТИЛЕЙ ---
styles_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Minimalism"), KeyboardButton(text="Cyberpunk")],
        [KeyboardButton(text="Luxury"), KeyboardButton(text="Neon")],
        [KeyboardButton(text="Futuristic"), KeyboardButton(text="Gaming")],
        [KeyboardButton(text="Retro"), KeyboardButton(text="Tech")]
    ],
    resize_keyboard=True
)


# --- START ---
@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 AI Logo Bot\n\n"
        "Выбери стиль через /styles\n"
        "И напиши описание логотипа",
    )


# --- STYLES ---
@dp.message(Command("styles"))
async def styles(message: Message):
    await message.answer("🎯 Выбери стиль:", reply_markup=styles_kb)


# --- ВЫБОР СТИЛЯ ---
@dp.message(F.text.in_(["Minimalism", "Cyberpunk", "Luxury", "Neon", "Futuristic", "Gaming", "Retro", "Tech"]))
async def set_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(f"✅ Стиль выбран: {message.text}\nТеперь напиши идею логотипа")


# --- ГЕНЕРАЦИЯ ПРОМПТА ---
@dp.message(F.text)
async def generate(message: Message):
    user_id = message.from_user.id
    text = message.text

    style = user_style.get(user_id, "Minimalism")

    prompt = (
        f"🎨 AI LOGO PROMPT\n\n"
        f"Style: {style}\n"
        f"Idea: {text}\n\n"
        f"Ultra detailed logo design, vector, clean branding, "
        f"high quality, modern, 8k, professional design"
    )

    await message.answer(prompt)


# --- ЗАПУСК ---
async def main():
    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())