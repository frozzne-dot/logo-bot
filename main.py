import asyncio
import logging
import os
import sys
import io
import aiohttp
import json
import base64
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
# ГЕНЕРАЦИЯ ЧЕРЕЗ BING IMAGE CREATOR (БЕСПЛАТНО, БЕЗ API КЛЮЧА)
# ======================

async def generate_logo_bing(prompt: str, style: str) -> bytes:
    """Генерация логотипа через Bing Image Creator (бесплатно!)"""
    
    full_prompt = f"Professional {style} style logo design: {prompt}. Clean vector graphics, high quality, suitable for branding, white background, no text, no watermark"
    
    # Используем бесплатный API от FreeGPT
    api_url = "https://api.freegpt.one/v1/images/generations"
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    payload = {
        "prompt": full_prompt,
        "n": 1,
        "size": "1024x1024"
    }
    
    async with aiohttp.ClientSession() as session:
        for attempt in range(3):
            try:
                async with session.post(api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("data") and len(data["data"]) > 0:
                            image_url = data["data"][0].get("url")
                            if image_url:
                                # Скачиваем изображение
                                async with session.get(image_url) as img_response:
                                    if img_response.status == 200:
                                        return await img_response.read()
                    elif response.status == 429:
                        await asyncio.sleep(2)
                        continue
                    else:
                        error_text = await response.text()
                        logger.warning(f"Attempt {attempt + 1} failed: {response.status}")
                        await asyncio.sleep(1)
            except asyncio.TimeoutError:
                logger.warning(f"Attempt {attempt + 1} timeout")
                await asyncio.sleep(1)
                continue
        
        raise Exception("Не удалось сгенерировать изображение после нескольких попыток")

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🤖 <b>AI Logo Bot</b>\n\n"
        "Создаю профессиональные логотипы через Bing Image Creator!\n\n"
        "✨ <b>Особенности:</b>\n"
        "• Полностью бесплатно\n"
        "• 6 стилей на выбор\n"
        "• Высокое качество\n"
        "• Без рекламы\n\n"
        "📖 <b>Как пользоваться:</b>\n"
        "1. Выбери стиль\n"
        "2. Нажми 'Создать логотип'\n"
        "3. Опиши идею подробно\n\n"
        "💡 <b>Пример:</b> логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started")

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "📖 <b>Инструкция</b>\n\n"
        "• <b>Выбрать стиль</b> — установи стиль логотипа\n"
        "• <b>Создать логотип</b> — начни генерацию\n\n"
        "<b>Доступные стили:</b>\n"
        "• Minimalism — минимализм\n"
        "• Abstract — абстракция\n"
        "• Vintage — винтажный\n"
        "• Cyberpunk — киберпанк\n"
        "• Eco — эко-стиль\n"
        "• Luxury — люксовый\n\n"
        "<b>Совет:</b> Чем подробнее описание — тем лучше результат!\n"
        "Указывай объекты, цвета и сферу применения.",
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
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    await message.answer(
        f"🎨 <b>Опишите идею логотипа</b>\n\n"
        f"🎭 Стиль: <b>{style}</b>\n\n"
        f"📝 Напишите подробно:\n"
        f"• Что изобразить?\n"
        f"• Какие цвета?\n"
        f"• Для какой сферы?\n\n"
        f"⏱ Генерация: 10-20 секунд\n\n"
        f"<b>Пример:</b>\n"
        f"логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона",
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
        await message.answer(
            "❌ <b>Слишком короткое описание</b>\n\n"
            "Напишите подробнее (минимум 3 слова).",
            parse_mode="HTML"
        )
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:80]}\n\n"
        f"⏱ Подождите 10-20 секунд...",
        parse_mode="HTML"
    )
    
    try:
        img_bytes = await generate_logo_bing(message.text, style)
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=(
                f"✨ <b>Логотип готов!</b>\n\n"
                f"📝 {message.text[:150]}\n"
                f"🎭 Стиль: {style}\n\n"
                f"🔄 Нажми 'Создать логотип' для новой генерации"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Logo generated for user {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        error_str = str(e)
        
        await message.answer(
            f"❌ <b>Ошибка генерации</b>\n\n"
            f"<code>{error_str[:150]}</code>\n\n"
            f"💡 <b>Советы:</b>\n"
            f"• Попробуйте другое описание\n"
            f"• Используйте английские слова\n"
            f"• Подождите минуту и повторите",
            parse_mode="HTML"
        )
        
        logger.error(f"❌ Generation error: {e}")

# ======================
# ЗАПУСК
# ======================

async def main():
    print("\n" + "=" * 60)
    print("🤖 AI LOGO BOT")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:15]}... OK")
    print("🚀 Бот запускается...")
    print("🎨 Бесплатная генерация через Bing Image Creator")
    print("=" * 60 + "\n")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Webhook cleared")
        logger.info("Bot is ready! Starting polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
