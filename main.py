import asyncio
import logging
import os
import sys
import io
import aiohttp
import signal
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
AGNES_API_KEY = os.getenv("AGNES_API_KEY")

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN не найден! Добавьте переменную в Railway")
    sys.exit(1)

if not AGNES_API_KEY:
    logger.warning("⚠️ AGNES_API_KEY не найден, будет использован fallback метод")
else:
    logger.info("✅ AGNES_API_KEY загружен")

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
        [KeyboardButton(text="💬 Чат с AI")],
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
# ГЕНЕРАЦИЯ ЛОГОТИПА
# ======================

async def generate_logo_agnes(prompt: str, style: str) -> bytes:
    """Генерация логотипа через Agnes AI"""
    
    full_prompt = f"Professional {style} style logo design: {prompt}. Clean vector graphics, high quality, suitable for branding, white background, no text."
    
    api_url = "https://apihub.agnes-ai.com/v1/images/generations"
    
    headers = {
        "Authorization": f"Bearer {AGNES_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "agnes-image-2.1-flash",
        "prompt": full_prompt,
        "n": 1,
        "size": "1024x1024"
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status == 200:
                data = await response.json()
                if data.get('data') and len(data['data']) > 0 and data['data'][0].get('url'):
                    image_url = data['data'][0]['url']
                    async with session.get(image_url) as img_response:
                        if img_response.status == 200:
                            return await img_response.read()
            raise Exception(f"Agnes AI API error: {response.status}")

async def generate_logo_fallback(prompt: str, style: str) -> bytes:
    """Запасной метод генерации"""
    import urllib.parse
    full_prompt = f"Professional {style} style logo: {prompt}, clean vector, white background"
    encoded = urllib.parse.quote(full_prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
            if response.status == 200:
                return await response.read()
            raise Exception(f"Fallback error: {response.status}")

async def generate_logo(prompt: str, style: str) -> bytes:
    """Основная функция генерации"""
    if AGNES_API_KEY:
        try:
            return await generate_logo_agnes(prompt, style)
        except Exception as e:
            logger.warning(f"Agnes AI failed, using fallback: {e}")
            return await generate_logo_fallback(prompt, style)
    else:
        return await generate_logo_fallback(prompt, style)

# ======================
# ЧАТ
# ======================

async def simple_chat(message_text: str) -> str:
    """Простой чат-бот"""
    text_lower = message_text.lower()
    
    if any(w in text_lower for w in ["привет", "здравствуй", "hi"]):
        return "👋 Привет! Я бот для создания логотипов. Выбери стиль и нажми 'Создать логотип'!"
    elif any(w in text_lower for w in ["как дела", "как ты"]):
        return "У меня всё отлично! Готов создавать красивые логотипы для тебя! 🎨"
    elif any(w in text_lower for w in ["логотип", "создай", "сделай"]):
        return "Чтобы создать логотип:\n1. Выбери стиль через кнопку 'Выбрать стиль'\n2. Нажми 'Создать логотип'\n3. Подробно опиши идею (цвета, объекты, сферу)"
    elif any(w in text_lower for w in ["спасибо", "thanks"]):
        return "Пожалуйста! Рад помочь 😊"
    else:
        return f"Я понял: «{message_text[:100]}»\n\nНажми 'Создать логотип' и опиши идею, и я сгенерирую профессиональный логотип!"

# ======================
# ОБРАБОТЧИКИ
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎨 <b>AI Logo Bot</b>\n\n"
        "Я создаю профессиональные логотипы с помощью нейросети!\n\n"
        "✨ <b>Возможности:</b>\n"
        "• 6 стилей на выбор\n"
        "• Высокое качество изображений\n"
        "• Полностью бесплатно\n\n"
        "📖 <b>Как использовать:</b>\n"
        "1️⃣ Выберите стиль (кнопка 'Выбрать стиль')\n"
        "2️⃣ Нажмите 'Создать логотип'\n"
        "3️⃣ Опишите вашу идею\n\n"
        "💡 <b>Пример:</b>\n"
        "«логотип для кофейни, чашка кофе и силуэт медведя, коричневые тона»",
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

@dp.message(F.text == "💬 Чат с AI")
async def chat_mode(message: Message):
    await message.answer(
        "💬 <b>Режим чата</b>\n\n"
        "Просто напиши сообщение, и я отвечу.\n\n"
        "Чтобы вернуться к логотипам — нажми '🎨 Создать логотип'",
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
        f"⏱ Генерация: 5-15 секунд\n\n"
        f"<b>Пример:</b>\n"
        f"«логотип для IT-компании, облако и шестерёнка, синие тона»",
        parse_mode="HTML"
    )

@dp.message(F.text)
async def handle_message(message: Message):
    if message.text.startswith('/'):
        return
    
    buttons = ["🎨 Создать логотип", "🎭 Выбрать стиль", "ℹ️ Помощь", "🔙 Назад",
               "Minimalism", "Abstract", "Vintage", "Cyberpunk", "Eco", "Luxury", "💬 Чат с AI"]
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
        f"⏱ Подождите 5-15 секунд...",
        parse_mode="HTML"
    )
    
    try:
        img_bytes = await generate_logo(message.text, style)
        photo = io.BytesIO(img_bytes)
        photo.name = "logo.png"
        
        await status_msg.delete()
        
        await message.answer_photo(
            photo=photo,
            caption=f"✨ <b>Логотип готов!</b>\n\n📝 {message.text[:150]}\n🎭 Стиль: {style}",
            parse_mode="HTML"
        )
        
        logger.info(f"✅ Логотип создан для {message.from_user.id}")
        
    except Exception as e:
        await status_msg.delete()
        
        await message.answer(
            f"❌ <b>Не удалось создать логотип</b>\n\n"
            f"🔍 {str(e)[:150]}\n\n"
            f"💡 Попробуйте другое описание или подождите минуту.",
            parse_mode="HTML"
        )
        
        logger.error(f"❌ Ошибка: {e}")

# ======================
# ПРАВИЛЬНЫЙ ЗАПУСК (без конфликтов)
# ======================

async def on_startup():
    """Действия при запуске"""
    logger.info("Бот запускается...")

async def on_shutdown():
    """Действия при остановке"""
    logger.info("Бот останавливается...")
    await bot.session.close()

async def main():
    print("\n" + "=" * 60)
    print("🎨 AI LOGO BOT v3.0")
    print("=" * 60)
    print(f"📌 Bot Token: {BOT_TOKEN[:10]}... ✅")
    print("🚀 Запуск бота...")
    print("=" * 60 + "\n")
    
    try:
        # ВАЖНО: удаляем вебхук и сбрасываем обновления
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Дополнительная очистка: получаем и пропускаем все старые обновления
        updates = await bot.get_updates(offset=-1, timeout=1)
        if updates:
            last_id = updates[-1].update_id
            await bot.get_updates(offset=last_id + 1)
            logger.info(f"Очищено {len(updates)} старых обновлений")
        
        # Запускаем с обработкой сигналов
        await dp.start_polling(
            bot,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            handle_signals=True,
            skip_updates=True
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
