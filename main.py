import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("8675822721:AAH_1ue0TDuiZSNoI4TLaWmrpuGu80WZDiY")

bot = Bot(token="8675822721:AAH_1ue0TDuiZSNoI4TLaWmrpuGu80WZDiY")
dp = Dispatcher()

user_style = {}

styles_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Minimalism"), KeyboardButton(text="Cyberpunk")],
        [KeyboardButton(text="Luxury"), KeyboardButton(text="Neon")],
        [KeyboardButton(text="Futuristic"), KeyboardButton(text="Gaming")],
        [KeyboardButton(text="Retro"), KeyboardButton(text="Tech")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 AI Logo Bot\n\n"
        "/styles — выбрать стиль\n"
        "Просто напиши идею логотипа"
    )

@dp.message(Command("styles"))
async def styles(message: Message):
    await message.answer("🎯 Выбери стиль:", reply_markup=styles_kb)

@dp.message(F.text.in_(["Minimalism","Cyberpunk","Luxury","Neon","Futuristic","Gaming","Retro","Tech"]))
async def set_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(f"✅ Стиль: {message.text}\nТеперь напиши идею логотипа")

@dp.message(F.text)
async def generate(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")

    prompt = f"""
🎨 AI LOGO PROMPT

Style: {style}
Idea: {message.text}

Ultra detailed logo, vector, modern branding,
clean design, high quality, 8k
"""

    await message.answer(prompt)

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
