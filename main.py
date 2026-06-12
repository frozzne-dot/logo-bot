import asyncio
import logging
import os
import sys
import io
import urllib.parse
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    sys.exit(1)

# Проверка токена перед запуском
if not BOT_TOKEN.startswith("8675822721:AAH"):
    logger.error("❌ Токен выглядит подозрительно! Убедитесь, что скопировали правильно.")
    sys.exit(1)

logger.info("✅ BOT_TOKEN загружен")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_style = {}

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🎨 Создать логотип")],
        [KeyboardButton(text="🎭 Выбрать стиль")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ],
    resize_keyboard=True
)

style_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Minimalism"), KeyboardButton(text="Abstract")],
        [KeyboardButton(text="Vintage"), KeyboardButton(text="Cyberpunk")],
        [KeyboardButton(text="Eco"), KeyboardButton(text="Luxury")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)

async def generate_logo(prompt: str, style: str) -> bytes:
    full_prompt = f"Professional {style} style logo: {prompt}. Clean vector, white background, no text"
    encoded = urllib.parse.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=30) as response:
            if response.status == 200:
                return await response.read()
            raise Exception(f"Ошибка {response.status}")

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot</b>\n\n"
        "Создаю логотипы бесплатно!\n\n"
        "1️⃣ Выберите стиль\n"
        "2️⃣ Нажмите 'Создать логотип'\n"
        "3️⃣ Опишите идею\n\n"
        "💡 Пример: логотип для кофейни, чашка кофе и медведь",
        reply_markup=main_kb,
        parse_mode="HTML"
    )

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer("🎭 Стили: Minimalism, Abstract, Vintage, Cyberpunk, Eco, Luxury")

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    await message.answer("🎭 Выберите стиль:", reply_markup=style_kb)

@dp.message(F.text == "🔙 Назад")
async def back(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(f"✅ Стиль {message.text} сохранён!", reply_markup=main_kb)

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    await message.answer(f"🎨 Опишите идею\n\nСтиль: {style}")

@dp.message(F.text)
async def handle_message(message: Message):
    if message.text in ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад",
                        "Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]:
        return
    
    if len(message.text.split()) < 3:
        await message.answer("❌ Слишком короткое описание")
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    status = await message.answer(f"🎨 Генерация... ⏱ 10-20 сек")
    
    try:
        img = await generate_logo(message.text, style)
        await status.delete()
        await message.answer_photo(photo=io.BytesIO(img), caption=f"✨ Логотип готов!")
    except Exception as e:
        await status.delete()
        await message.answer(f"❌ Ошибка: {str(e)[:100]}")

async def main():
    try:
        # Проверяем токен через API Telegram
        me = await bot.get_me()
        logger.info(f"✅ Бот подключен: @{me.username}")
        
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.error(f"❌ Ошибка подключения: {e}")
        logger.error("   Проверьте правильность BOT_TOKEN в Railway Variables")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
