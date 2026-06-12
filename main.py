import asyncio
import logging
import os
import sys
import io
import aiohttp
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
    logger.error("❌ BOT_TOKEN не найден! Добавьте переменную в Railway")
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
# РАБОЧАЯ ГЕНЕРАЦИЯ (используем стабильный API)
# ======================

async def generate_logo(prompt: str, style: str) -> bytes:
    """Генерация логотипа через стабильный бесплатный API"""
    
    # Улучшаем промпт
    full_prompt = f"Create a professional {style} style logo: {prompt}. Clean design, vector style, white background, high quality, no text."
    
    # API для генерации изображений
    api_url = "https://api.lemonfox.ai/v1/images/generations"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "prompt": full_prompt,
        "size": "1024x1024",
        "n": 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("data") and data[0].get("url"):
                    image_url = data[0]["url"]
                    async with session.get(image_url) as img_response:
                        if img_response.status == 200:
                            return await img_response.read()
            
            raise Exception(f"Ошибка API: {response.status}")

# ======================
# ЗАПАСНОЙ ВАРИАНТ (если основной API недоступен)
# ======================

async def generate_logo_fallback(prompt: str, style: str) -> bytes:
    """Запасной метод генерации через другой API"""
    
    full_prompt = f"Professional {style} style logo: {prompt}. Clean vector, white background"
    
    # Используем Pollinations с другой моделью
    import urllib.parse
    encoded = urllib.parse.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.read()
            raise Exception(f"Ошибка: {response.status}")

# ======================
# ПРОСТОЙ ЧАТ
# ======================

async def simple_chat(text: str) -> str:
    """Ответы на сообщения"""
    text_lower = text.lower()
    
    if any(w in text_lower for w in ["привет", "здравствуй"]):
        return "👋 Привет! Я бот для создания логотипов. Выбери стиль и нажми 'Создать логотип'!"
    elif any(w in text_lower for w in ["как дела", "как ты"]):
        return "У меня всё отлично! Готов создавать красивые логотипы для тебя! 🎨"
    elif "логотип" in text_lower:
        return "Чтобы создать логотип:\n1. Выбери стиль\n2. Нажми 'Создать логотип'\n3. Подробно опиши идею"
    else:
        return f"Я понял: «{text[:100]}»\n\nНажми 'Создать логотип' и опиши идею, и я сгенерирую профессиональный логотип!"

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot</b>\n\n"
        "Я создаю профессиональные логотипы с помощью искусственного интеллекта!\n\n"
        "✨ <b>Возможности:</b>\n"
        "• 6 стилей на выбор\n"
        "• Высокое качество изображений\n"
        "• Полностью бесплатно\n\n"
        "📖 <b>Как использовать:</b>\n"
        "1️⃣ Выберите стиль (кнопка 'Выбрать стиль')\n"
        "2️⃣ Нажмите 'Создать логотип'\n"
        "3️⃣ Опишите вашу идею\n\n"
        "💡 <b>Пример описания:</b>\n"
        "«логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона»",
        reply_markup=main_kb,
        parse_mode="HTML"
    )
    logger.info(f"User {message.from_user.id} started bot")

@dp.message(F.text == "ℹ️ Помощь")
async def help_command(message: Message):
    await message.answer(
        "📖 <b>Помощь</b>\n\n"
        "🎭 <b>Доступные стили:</b>\n"
        "• Minimalism — минимализм\n"
        "• Abstract — абстракция\n"
        "• Vintage — винтажный\n"
        "• Cyberpunk — киберпанк\n"
        "• Eco — эко-стиль\n"
        "• Luxury — люксовый\n\n"
        "💡 <b>Советы:</b>\n"
        "• Пишите подробные описания\n"
        "• Указывайте цвета\n"
        "• Называйте объекты\n\n"
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
        f"🎨 Теперь нажмите «Создать логотип» и опишите вашу идею.\n\n"
        f"💡 Чем подробнее описание — тем лучше результат!",
        parse_mode="HTML",
        reply_markup=main_kb
    )
    logger.info(f"User {message.from_user.id} set style: {message.text}")

@dp.message(F.text == "🎨 Создать логотип")
async def ask_idea(message: Message):
    style = user_style.get(message.from_user.id, "Minimalism")
    await message.answer(
        f"🎨 <b>Создание логотипа</b>\n\n"
        f"🎭 Выбранный стиль: <b>{style}</b>\n\n"
        f"📝 <b>Опишите вашу идею:</b>\n"
        f"• Что должно быть изображено?\n"
        f"• Какие цвета использовать?\n"
        f"• Для какой сферы логотип?\n\n"
        f"⏱ Генерация займёт 5-15 секунд\n\n"
        f"<b>Пример идеального описания:</b>\n"
        f"«логотип для IT-компании, облако и шестерёнка, синие и белые тона»",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_message(message: Message):
    # Пропускаем команды
    if message.text.startswith('/'):
        return
    
    # Пропускаем кнопки
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад",
               "Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury"]
    if message.text in buttons:
        return
    
    # Проверяем длину
    if len(message.text.split()) < 2:
        await message.answer(
            "❌ <b>Слишком короткое описание</b>\n\n"
            "Пожалуйста, напишите более подробно (минимум 3 слова).\n\n"
            "✅ <b>Пример:</b> «логотип для кофейни с чашкой кофе»",
            parse_mode="HTML"
        )
        return
    
    style = user_style.get(message.from_user.id, "Minimalism")
    
    # Отправляем статус
    status_msg = await message.answer(
        f"🎨 <b>Генерация логотипа...</b>\n\n"
        f"🎭 Стиль: {style}\n"
        f"💡 Идея: {message.text[:100]}\n\n"
        f"⏱ Пожалуйста, подождите 5-15 секунд...",
        parse_mode="HTML"
    )
    
    try:
        # Пробуем основной метод
        try:
            img_bytes = await generate_logo(message.text, style)
        except:
            # Если не работает, используем запасной
            img_bytes = await generate_logo_fallback(message.text, style)
        
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=(
                f"✨ <b>Логотип готов!</b>\n\n"
                f"📝 <b>Описание:</b> {message.text[:200]}\n"
                f"🎭 <b>Стиль:</b> {style}\n\n"
                f"🔄 <b>Хотите ещё?</b> Просто нажмите «Создать логотип»"
            ),
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Логотип создан для {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        error_msg = str(e)
        
        await message.answer(
            f"❌ <b>Не удалось создать логотип</b>\n\n"
            f"🔍 <b>Причина:</b> {error_msg[:150]}\n\n"
            f"💡 <b>Что можно сделать:</b>\n"
            f"• Измените описание (сделайте конкретнее)\n"
            f"• Попробуйте другой стиль\n"
            f"• Напишите на русском подробнее\n"
            f"• Подождите минуту и повторите\n\n"
            f"🔄 Просто отправьте новое описание!",
            parse_mode="HTML"
        )
        
        logger.error(f"❌ Ошибка у {message.from_user.id}: {e}")

# ======================
# ЗАПУСК
# ======================

async def main():
    print("\n" + "=" * 60)
    print("🎨 AI LOGO BOT v2.0")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:10]}... ✅")
    print("🚀 Запуск бота...")
    print("✨ Генерация логотипов через AI")
    print("=" * 60 + "\n")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)
