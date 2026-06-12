import asyncio
import logging
import os
import sys
import io
import aiohttp
import urllib.parse
import random
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
# ГЕНЕРАЦИЯ ИЗОБРАЖЕНИЙ (рабочий метод)
# ======================

async def generate_logo(prompt: str, style: str) -> bytes:
    """Генерация логотипа через бесплатный API"""
    
    # Промпт для лучшего результата
    full_prompt = f"Professional {style} style logo: {prompt}. Minimalist, clean vector, white background, no text, high quality"
    
    # Кодируем промпт для URL
    encoded = urllib.parse.quote(full_prompt)
    
    # Используем разные сервисы для надежности
    services = [
        f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true",
        f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&model=flux",
        f"https://pollinations.ai/prompt/{encoded}?width=1024&height=1024"
    ]
    
    async with aiohttp.ClientSession() as session:
        for url in services:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        data = await response.read()
                        if len(data) > 5000:  # Проверка что это реальное изображение
                            return data
            except Exception as e:
                logger.warning(f"Service failed: {e}")
                continue
    
    raise Exception("Все сервисы генерации временно недоступны")

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot</b>\n\n"
        "Я создаю профессиональные логотипы бесплатно!\n\n"
        "✨ <b>Возможности:</b>\n"
        "• 6 стилей на выбор\n"
        "• Высокое качество\n"
        "• Полностью бесплатно\n\n"
        "📖 <b>Как использовать:</b>\n"
        "1️⃣ Выберите стиль\n"
        "2️⃣ Нажмите 'Создать логотип'\n"
        "3️⃣ Опишите идею\n\n"
        "💡 <b>Пример:</b>\n"
        "логотип для кофейни, чашка кофе и медведь, коричневые тона",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started")

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "📖 <b>Помощь</b>\n\n"
        "🎭 <b>Стили:</b>\n"
        "• Minimalism — минимализм\n"
        "• Abstract — абстракция\n"
        "• Vintage — винтажный\n"
        "• Cyberpunk — киберпанк\n"
        "• Eco — эко-стиль\n"
        "• Luxury — люксовый\n\n"
        "💡 <b>Совет:</b> Чем подробнее описание, тем лучше результат!\n\n"
        "⏱ Время генерации: 5-15 секунд",
        parse_mode="HTML"
    )

@dp.message(F.text == "🎭 Выбрать стиль")
async def choose_style(message: Message):
    current = user_style.get(message.from_user.id)
    text = f"\n\n✅ Текущий стиль: <b>{current}</b>" if current else ""
    await message.answer(f"🎭 <b>Выберите стиль:</b>{text}", reply_markup=style_kb, parse_mode="HTML")

@dp.message(F.text == "🔙 Назад")
async def back_to_menu(message: Message):
    await message.answer("🏠 <b>Главное меню</b>", reply_markup=main_kb, parse_mode="HTML")

@dp.message(F.text.in_(["Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]))
async def save_style(message: Message):
    user_style[message.from_user.id] = message.text
    await message.answer(
        f"✅ <b>Стиль «{message.text}» сохранён!</b>\n\n"
        f"🎨 Теперь нажмите «Создать логотип» и опишите вашу идею.",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    await message.answer(
        f"🎨 <b>Создание логотипа</b>\n\n"
        f"🎭 Стиль: <b>{style}</b>\n\n"
        f"📝 <b>Опишите идею:</b>\n"
        f"• Что изобразить?\n"
        f"• Какие цвета?\n"
        f"• Для какой сферы?\n\n"
        f"⏱ Генерация: 10-20 секунд\n\n"
        f"<b>Пример:</b>\n"
        f"«логотип для IT-компании, облако и шестерёнка, синие тона»",
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
            "Напишите подробнее (минимум 3 слова).\n\n"
            "✅ <b>Пример:</b> «логотип для кофейни с чашкой кофе»",
            parse_mode="HTML"
        )
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 {message.text[:80]}\n\n"
        f"⏱ Подождите 10-20 секунд...",
        parse_mode="HTML"
    )
    
    try:
        img_bytes = await generate_logo(message.text, style)
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=f"✨ <b>Логотип готов!</b>\n\n📝 {message.text[:150]}\n🎭 Стиль: {style}\n\n🔄 Нажмите «Создать логотип» для новой генерации",
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Логотип создан для {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        
        await message.answer(
            f"❌ <b>Не удалось создать логотип</b>\n\n"
            f"🔍 {str(e)[:150]}\n\n"
            f"💡 <b>Советы:</b>\n"
            f"• Измените описание\n"
            f"• Попробуйте другой стиль\n"
            f"• Подождите минуту и повторите\n\n"
            f"🔄 Просто отправьте новое описание!",
            parse_mode="HTML"
        )
        
        logger.error(f"❌ Ошибка: {e}")

# ======================
# ЗАПУСК (без конфликтов)
# ======================

async def main():
    print("\n" + "=" * 60)
    print("🎨 AI LOGO BOT v4.0")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:10]}... ✅")
    print("🚀 Запуск бота...")
    print("=" * 60 + "\n")
    
    try:
        # Принудительная очистка
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запуск с пропуском старых обновлений
        await dp.start_polling(
            bot,
            skip_updates=True,
            allowed_updates=["message", "callback_query"]
        )
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Фатальная ошибка: {e}")
        sys.exit(1)
