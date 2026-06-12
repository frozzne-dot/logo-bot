import asyncio
import logging
import os
import sys
import io
import aiohttp
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# ======================
# НАСТРОЙКА
# ======================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден!")
    sys.exit(1)

logger.info("✅ BOT_TOKEN загружен")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
user_style = {}

# ======================
# КЛАВИАТУРЫ
# ======================

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

# ======================
# ГЕНЕРАЦИЯ ЧЕРЕЗ HUGGING FACE (БЕСПЛАТНО)
# ======================

async def generate_logo(prompt: str, style: str) -> bytes:
    """Генерация логотипа через Hugging Face FLUX модель"""
    
    full_prompt = f"Professional {style} style logo: {prompt}. Clean vector, white background, no text"
    
    # Hugging Face Inference API - бесплатно
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"inputs": full_prompt},
            timeout=aiohttp.ClientTimeout(total=60)
        ) as response:
            if response.status == 200:
                return await response.read()
            elif response.status == 503:
                raise Exception("Модель загружается, попробуйте через 5 секунд")
            else:
                raise Exception(f"Ошибка {response.status}")

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 <b>AI Logo Bot</b>\n\n"
        "Создаю логотипы через нейросеть FLUX (Hugging Face)!\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выбери стиль\n"
        "2. Нажми 'Создать логотип'\n"
        "3. Опиши идею\n\n"
        "💡 <b>Пример:</b> логотип для кофейни с чашкой кофе",
        reply_markup=main_kb,
        parse_mode="HTML"
    )

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "📖 <b>Инструкция</b>\n\n"
        "• Выбери стиль (Minimalism, Luxury и др.)\n"
        "• Нажми 'Создать логотип'\n"
        "• Подробно опиши идею (цвета, объекты, сфера)\n\n"
        "✅ Хороший пример:\n"
        "логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона\n\n"
        "❌ Плохой пример:\n"
        "сделай красивый логотип",
        parse_mode="HTML"
    )

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    current = user_style.get(message.from_user.id)
    text = f"\n\nТекущий стиль: <b>{current}</b>" if current else ""
    await message.answer(f"🎭 <b>Выберите стиль:</b>{text}", reply_markup=style_kb, parse_mode="HTML")

@dp.message(F.text == "🔙 Назад")
async def back(message: Message):
    await message.answer("🏠 Главное меню", reply_markup=main_kb)

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(
        f"✅ Стиль <b>{message.text}</b> сохранён!\n\nТеперь нажми 'Создать логотип' и опиши идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    await message.answer(
        f"🎨 <b>Опишите идею логотипа</b>\n\n"
        f"🎭 Стиль: <b>{style}</b>\n\n"
        f"📝 Напишите подробно: что изобразить, какие цвета, для какой сферы\n\n"
        f"⏱ Генерация: 10-20 секунд\n\n"
        f"<b>Пример:</b> логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_message(message: Message):
    if message.text.startswith('/'):
        return
    
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад",
               "Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]
    if message.text in buttons:
        return
    
    if len(message.text.split()) < 3:
        await message.answer("❌ Слишком короткое описание. Напишите подробнее (3+ слов).", parse_mode="HTML")
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    status = await message.answer(f"🎨 Генерация логотипа...\n\nСтиль: {style}\n⏱ Подождите 10-20 секунд", parse_mode="HTML")
    
    try:
        img_bytes = await generate_logo(message.text, style)
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status.delete()
        await message.answer_photo(
            photo=photo,
            caption=f"✨ <b>Логотип готов!</b>\n\n📝 {message.text[:150]}\n🎭 Стиль: {style}",
            parse_mode="HTML"
        )
        logger.info(f"✅ Logo for {message.from_user.id}")
        
    except Exception as e:
        await status.delete()
        error = str(e)
        if "503" in error:
            await message.answer("⏳ Модель загружается, попробуйте ещё раз через 10 секунд", parse_mode="HTML")
        else:
            await message.answer(f"❌ Ошибка: {error[:100]}\n\nПопробуйте другое описание.", parse_mode="HTML")
        logger.error(f"Error: {e}")

# ======================
# ЗАПУСК
# ======================

async def main():
    print("\n" + "=" * 50)
    print("🤖 LOGO BOT (Hugging Face FLUX)")
    print("=" * 50)
    print(f"📌 Bot Token: {BOT_TOKEN[:10]}...")
    print("🚀 Бот запущен!")
    print("=" * 50 + "\n")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
